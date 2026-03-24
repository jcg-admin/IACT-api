#!/bin/bash
# =============================================================================
# db_setup.sh — MariaDB: crea base de datos y usuario para Django (READ-ONLY)
# =============================================================================
# IDEMPOTENTE: se puede ejecutar N veces sin efectos adversos.
#   · Si la base ya existe    → salta la creación
#   · Si el usuario ya existe → actualiza la contraseña
#   · Los GRANT se re-aplican siempre (GRANT es idempotente en MySQL/MariaDB)
#
# CNST-003: ivr_legacy es READ-ONLY para Django (solo SELECT).
# NO instala MariaDB ni modifica el sistema operativo.
# Requiere que MariaDB esté corriendo y acceso como root (sudo mysql).
#
# Uso:
#   sudo bash scripts/provisioners/mariadb/db_setup.sh
#
# Variables leídas desde .env (raíz del proyecto):
#   IVR_DB_NAME      — nombre de la base de datos   (default: ivr_legacy)
#   IVR_DB_USER      — usuario Django                (default: django_user)
#   IVR_DB_PASSWORD  — contraseña del usuario        (default: django_pass)
#   IVR_DB_HOST      — host MariaDB                  (default: 127.0.0.1)
#   IVR_DB_PORT      — puerto MariaDB                (default: 3306)
#   DB_CHARSET       — charset de la base            (default: utf8mb4)
#   DB_COLLATION     — collation de la base          (default: utf8mb4_unicode_ci)
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

source "${PROJECT_ROOT}/scripts/utils/logging.sh"

# =============================================================================
# CONFIGURACIÓN — leída desde .env, con defaults
# =============================================================================
ENV_FILE="${PROJECT_ROOT}/.env"
if [[ -f "$ENV_FILE" ]]; then
    set -a; source "$ENV_FILE"; set +a
fi

DB_NAME="${IVR_DB_NAME:-ivr_legacy}"
DB_USER="${IVR_DB_USER:-django_user}"
DB_PASSWORD="${IVR_DB_PASSWORD:-django_pass}"
DB_HOST="${IVR_DB_HOST:-127.0.0.1}"
DB_PORT="${IVR_DB_PORT:-3306}"
DB_CHARSET="${DB_CHARSET:-utf8mb4}"
DB_COLLATION="${DB_COLLATION:-utf8mb4_unicode_ci}"

TOTAL_STEPS=5

# =============================================================================
# HELPERS — ejecutan SQL como root via unix socket (sin contraseña)
# =============================================================================
my_root() {
    sudo mysql --batch "$@" 2>&1
}

my_root_silent() {
    sudo mysql --batch --silent --skip-column-names "$@" 2>/dev/null
}

# =============================================================================
# PASO 1 — Prerequisitos
# =============================================================================
check_prerequisites() {
    log_step 1 $TOTAL_STEPS "Verificando prerequisitos"

    [[ $EUID -ne 0 ]] && log_fatal "Ejecuta con sudo" && exit 1

    command -v mysql &>/dev/null \
        || { log_fatal "mysql client no encontrado."; exit 1; }

    # Verificar acceso root via socket
    if ! my_root_silent -e "SELECT 1;" > /dev/null; then
        log_fatal "No hay acceso root a MariaDB via socket unix"
        log_error "Verifica que MariaDB esté corriendo: sudo service mariadb status"
        exit 1
    fi

    log_success "MariaDB accesible en ${DB_HOST}:${DB_PORT}"
}

# =============================================================================
# PASO 2 — Crear base de datos
# =============================================================================
create_database() {
    log_step 2 $TOTAL_STEPS "Base de datos: ${DB_NAME}"

    local exists
    exists=$(my_root_silent -e \
        "SELECT COUNT(*) FROM information_schema.SCHEMATA
         WHERE SCHEMA_NAME = '${DB_NAME}';" || echo "0")

    if [[ "$exists" -gt 0 ]]; then
        log_info "Base de datos ya existe — sin cambios"
    else
        my_root -e \
            "CREATE DATABASE \`${DB_NAME}\`
             CHARACTER SET ${DB_CHARSET}
             COLLATE ${DB_COLLATION};" > /dev/null
        log_success "Base de datos ${DB_NAME} creada (${DB_CHARSET}/${DB_COLLATION})"
    fi
}

# =============================================================================
# PASO 3 — Crear / actualizar usuario
# =============================================================================
create_user() {
    log_step 3 $TOTAL_STEPS "Usuario: ${DB_USER}"

    for host in "%" "localhost"; do
        local exists
        exists=$(my_root_silent -e \
            "SELECT COUNT(*) FROM mysql.user
             WHERE User = '${DB_USER}' AND Host = '${host}';" || echo "0")

        if [[ "$exists" -gt 0 ]]; then
            # Idempotente: actualizar contraseña por si cambió en .env
            my_root -e \
                "ALTER USER '${DB_USER}'@'${host}'
                 IDENTIFIED BY '${DB_PASSWORD}';" > /dev/null
            log_info "Usuario ${DB_USER}@${host} ya existe — contraseña sincronizada"
        else
            my_root -e \
                "CREATE USER '${DB_USER}'@'${host}'
                 IDENTIFIED BY '${DB_PASSWORD}';" > /dev/null
            log_success "Usuario ${DB_USER}@${host} creado"
        fi
    done
}

# =============================================================================
# PASO 4 — Otorgar privilegios READ-ONLY (CNST-003)
# GRANT es idempotente en MariaDB — re-aplicar no genera error
# =============================================================================
grant_privileges() {
    log_step 4 $TOTAL_STEPS "Privilegios READ-ONLY: ${DB_USER} sobre ${DB_NAME}"

    for host in "%" "localhost"; do
        my_root -e \
            "GRANT SELECT ON \`${DB_NAME}\`.* TO '${DB_USER}'@'${host}';" > /dev/null
    done

    my_root -e "FLUSH PRIVILEGES;" > /dev/null
    log_success "Privilegios SELECT aplicados (READ-ONLY — CNST-003)"
}

# =============================================================================
# PASO 5 — Verificar conexión con las credenciales de Django
# =============================================================================
verify_connection() {
    log_step 5 $TOTAL_STEPS "Verificando conexión con credenciales Django"

    local result
    result=$(mysql -h "$DB_HOST" -P "$DB_PORT" \
        -u "$DB_USER" -p"${DB_PASSWORD}" \
        --batch --silent --skip-column-names \
        -e "SELECT CONCAT(DATABASE(), '@', USER());" \
        "$DB_NAME" 2>&1) || {
        log_error "No se pudo conectar como ${DB_USER}"
        log_error "$result"
        exit 1
    }

    log_success "Conexión OK: ${result}"

    # Verificar que NO tiene permisos de escritura (seguridad CNST-003)
    local can_write
    can_write=$(mysql -h "$DB_HOST" -P "$DB_PORT" \
        -u "$DB_USER" -p"${DB_PASSWORD}" \
        --batch --silent --skip-column-names \
        -e "SELECT COUNT(*) FROM information_schema.USER_PRIVILEGES
            WHERE GRANTEE LIKE \"'${DB_USER}'%\"
            AND PRIVILEGE_TYPE IN ('INSERT','UPDATE','DELETE','DROP');" \
        2>/dev/null || echo "0")

    if [[ "$can_write" -eq 0 ]]; then
        log_success "Verificado: usuario es READ-ONLY (CNST-003)"
    else
        log_warn "El usuario tiene privilegios de escritura — revisa CNST-003"
    fi
}

# =============================================================================
# MAIN
# =============================================================================
log_header "MariaDB DB Setup — IACT (ivr_legacy READ-ONLY)"

echo "  Base de datos : ${DB_NAME}"
echo "  Usuario       : ${DB_USER}"
echo "  Host          : ${DB_HOST}:${DB_PORT}"
echo "  Charset       : ${DB_CHARSET} / ${DB_COLLATION}"
echo "  Permisos      : SELECT (READ-ONLY)"
echo ""

check_prerequisites
create_database
create_user
grant_privileges
verify_connection

echo ""
log_success "Setup completado. Base ${DB_NAME} lista para Django (READ-ONLY)."
