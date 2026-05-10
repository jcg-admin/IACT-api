#!/bin/bash
# =============================================================================
# db_setup.sh — PostgreSQL: crea base de datos y usuario para Django
# =============================================================================
# IDEMPOTENTE: se puede ejecutar N veces sin efectos adversos.
#   · Si el usuario ya existe     → actualiza la contraseña
#   · Si la base ya existe        → salta la creación
#   · Si los privilegios ya están → los vuelve a aplicar (GRANT es idempotente)
#
# NO instala PostgreSQL ni modifica el sistema operativo.
# Requiere que PostgreSQL esté corriendo y acceso como root (sudo).
#
# Uso:
#   sudo bash scripts/provisioners/postgres/db_setup.sh
#
# Variables leídas desde .env (raíz del proyecto):
#   DB_NAME      — nombre de la base de datos   (default: iact_analytics)
#   DB_USER      — usuario Django                (default: django_user)
#   DB_PASSWORD  — contraseña del usuario        (default: django_pass)
#   DB_HOST      — host PostgreSQL               (default: 127.0.0.1)
#   DB_PORT      — puerto PostgreSQL             (default: 5432)
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

DB_NAME="${DB_NAME:-iact_analytics}"
DB_USER="${DB_USER:-django_user}"
DB_PASSWORD="${DB_PASSWORD:-django_pass}"
DB_HOST="${DB_HOST:-127.0.0.1}"
DB_PORT="${DB_PORT:-5432}"

TOTAL_STEPS=5

# =============================================================================
# HELPERS — ejecutan SQL como superusuario postgres (peer auth)
# =============================================================================
pg_super() {
    sudo -u postgres psql -v ON_ERROR_STOP=1 "$@" 2>&1
}

pg_super_quiet() {
    sudo -u postgres psql -v ON_ERROR_STOP=1 -tAq "$@" 2>/dev/null
}

# =============================================================================
# PASO 1 — Prerequisitos
# =============================================================================
check_prerequisites() {
    log_step 1 $TOTAL_STEPS "Verificando prerequisitos"

    [[ $EUID -ne 0 ]] && log_fatal "Ejecuta con sudo" && exit 1

    command -v psql &>/dev/null \
        || { log_fatal "psql no encontrado. Instala postgresql-client."; exit 1; }

    # Verificar que el cluster está activo
    if ! sudo -u postgres pg_isready -h "$DB_HOST" -p "$DB_PORT" -q 2>/dev/null; then
        log_fatal "PostgreSQL no responde en ${DB_HOST}:${DB_PORT}"
        log_error "Inicia el servicio: sudo pg_ctlcluster 16 main start"
        exit 1
    fi

    log_success "PostgreSQL activo en ${DB_HOST}:${DB_PORT}"
}

# =============================================================================
# PASO 2 — Crear / actualizar usuario
# =============================================================================
create_user() {
    log_step 2 $TOTAL_STEPS "Usuario: ${DB_USER}"

    local exists
    exists=$(pg_super_quiet -c \
        "SELECT 1 FROM pg_roles WHERE rolname = '${DB_USER}';" || echo "")

    if [[ "$exists" == "1" ]]; then
        # Idempotente: actualizar contraseña por si cambió en .env
        pg_super -c "ALTER USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';" > /dev/null
        log_info "Usuario ya existe — contraseña sincronizada"
    else
        pg_super -c "CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';" > /dev/null
        log_success "Usuario ${DB_USER} creado"
    fi
}

# =============================================================================
# PASO 3 — Crear base de datos
# =============================================================================
create_database() {
    log_step 3 $TOTAL_STEPS "Base de datos: ${DB_NAME}"

    local exists
    exists=$(pg_super_quiet -c \
        "SELECT 1 FROM pg_database WHERE datname = '${DB_NAME}';" || echo "")

    if [[ "$exists" == "1" ]]; then
        log_info "Base de datos ya existe — sin cambios"
    else
        pg_super -c \
            "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER} ENCODING 'UTF8';" > /dev/null
        log_success "Base de datos ${DB_NAME} creada"
    fi
}

# =============================================================================
# PASO 4 — Otorgar privilegios (GRANT es idempotente en PostgreSQL)
# =============================================================================
grant_privileges() {
    log_step 4 $TOTAL_STEPS "Privilegios: ${DB_USER} sobre ${DB_NAME}"

    pg_super -d "$DB_NAME" <<SQL > /dev/null
GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};
GRANT ALL ON SCHEMA public TO ${DB_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES    TO ${DB_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ${DB_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO ${DB_USER};
-- Necesario para que pytest cree/destruya test_iact_analytics
ALTER ROLE ${DB_USER} CREATEDB;
SQL

    log_success "Privilegios aplicados (incluye CREATEDB para tests)"
}

# =============================================================================
# PASO 5 — Verificar conexión con las credenciales de Django
# =============================================================================
verify_connection() {
    log_step 5 $TOTAL_STEPS "Verificando conexión con credenciales Django"

    local result
    result=$(PGPASSWORD="$DB_PASSWORD" \
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -tAq -c "SELECT current_database() || '@' || current_user;" 2>&1) || {
        log_error "No se pudo conectar como ${DB_USER}"
        log_error "$result"
        exit 1
    }

    log_success "Conexión OK: ${result}"
}

# =============================================================================
# MAIN
# =============================================================================
log_header "PostgreSQL DB Setup — IACT"

echo "  Base de datos : ${DB_NAME}"
echo "  Usuario       : ${DB_USER}"
echo "  Host          : ${DB_HOST}:${DB_PORT}"
echo ""

check_prerequisites
create_user
create_database
grant_privileges
verify_connection

echo ""
log_success "Setup completado. Listo para: python manage.py migrate"
