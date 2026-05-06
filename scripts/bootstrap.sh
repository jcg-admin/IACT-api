#!/bin/bash
# =============================================================================
# bootstrap.sh — IACT API: Entrypoint único de provisioning y verificación
# =============================================================================
# Version: 2.0.0
#
# UN SOLO COMANDO para todo:
#   sudo bash scripts/bootstrap.sh
#
# Flags:
#   --skip-update   Omite apt-get update (útil si el índice ya es reciente)
#
# Primera vez : instala y configura todo desde cero
# Veces siguientes: verifica estado de todo (DBs activas, Apache, Python...)
#
# Requisito: Ubuntu 24.04.x LTS
#
# Flujo (todas las fases son idempotentes):
#   Fase 1 — SO          : Verificar Ubuntu 24.04.x LTS             [FATAL]
#   Fase 2 — Paquetes    : Instalar dependencias del sistema        [FATAL]
#   Fase 3 — Python      : Entorno virtual + drivers               [FATAL]
#   Fase 4 — Bases datos : Delega en IACT-db/setup.sh               [WARN]
#                          Requiere IACT_DB_PATH en .env o arg --iact-db
#   Fase 5 — Apache      : Virtual host + mod_wsgi + static         [WARN]
#   Fase 6 — Verificación: Estado completo del entorno              [INFO]
# =============================================================================
set -euo pipefail

# =============================================================================
# ARGUMENTOS
# =============================================================================
SKIP_APT_UPDATE=false
IACT_DB_PATH_ARG=""
for arg in "$@"; do
    case "$arg" in
        --skip-update)  SKIP_APT_UPDATE=true ;;
        --iact-db=*)    IACT_DB_PATH_ARG="${arg#--iact-db=}" ;;
    esac
done
export SKIP_APT_UPDATE

# =============================================================================
# PATHS
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
export PROJECT_ROOT

UTILS_DIR="${SCRIPT_DIR}/utils"
PROVISIONERS_DIR="${SCRIPT_DIR}/provisioners"
SYSTEM_DIR="${PROVISIONERS_DIR}/system"
POSTGRES_DIR="${PROVISIONERS_DIR}/postgres"
MARIADB_DIR="${PROVISIONERS_DIR}/mariadb"

# Ruta a IACT-db (fuente de verdad de infraestructura de BD)
# Prioridad: 1) flag --iact-db=<ruta>  2) .env IACT_DB_PATH  3) default
_resolve_iact_db_path() {
    if [[ -n "${IACT_DB_PATH_ARG:-}" ]]; then
        echo "$IACT_DB_PATH_ARG"
        return
    fi
    local env_file="${PROJECT_ROOT}/.env"
    if [[ -f "$env_file" ]]; then
        local from_env
        from_env=$(grep '^IACT_DB_PATH=' "$env_file" 2>/dev/null | cut -d= -f2- | tr -d '"')
        [[ -n "$from_env" ]] && echo "$from_env" && return
    fi
    # Default: asume que IACT-db está junto a IACT-api
    echo "$(cd "${PROJECT_ROOT}/../IACT-db" 2>/dev/null && pwd || echo "")"
}
APACHE_DIR="${SCRIPT_DIR}/apache"

# =============================================================================
# LOAD UTILS (orden importa: logging primero, luego el resto)
# =============================================================================
# shellcheck disable=SC1091
source "${UTILS_DIR}/logging.sh"
# shellcheck disable=SC1091
source "${UTILS_DIR}/core.sh"
# shellcheck disable=SC1091
source "${UTILS_DIR}/validation.sh"
# shellcheck disable=SC1091
source "${UTILS_DIR}/network.sh"
# shellcheck disable=SC1091
source "${UTILS_DIR}/database.sh"
# shellcheck disable=SC1091
source "${UTILS_DIR}/provisioning.sh"

LOG_NAME="bootstrap"
init_log "$LOG_NAME"

# =============================================================================
# FASE 1 — Sistema Operativo
# Bloquea TODO si no es Ubuntu 24.04.x LTS
# =============================================================================
phase_os() {
    log_header "Fase 1/6 — Sistema operativo"
    bash "${SYSTEM_DIR}/check_os.sh" || {
        echo ""
        log_fatal "SO incompatible — bootstrap abortado"
        exit 1
    }
}

# =============================================================================
# FASE 2 — Paquetes del sistema
# Instala: net-tools, iproute2, python3-dev, libpq-dev, mariadb-client, etc.
# Idempotente: dpkg check antes de instalar
# =============================================================================
phase_system_packages() {
    log_header "Fase 2/6 — Paquetes del sistema"

    validate_root || {
        log_fatal "Las fases de provisioning requieren root."
        log_fatal "Usa: sudo bash scripts/bootstrap.sh"
        exit 1
    }

    bash "${SYSTEM_DIR}/install_packages.sh" || {
        log_fatal "Instalación de paquetes del sistema falló"
        exit 1
    }
}

# =============================================================================
# FASE 3 — Entorno Python
# Crea venv si no existe, instala requirements/development.txt
# Idempotente: venv ya existente = solo re-instala si hay cambios en req
# =============================================================================
phase_python() {
    log_header "Fase 3/6 — Entorno Python"

    # --- Python 3.11+ ---
    require_command python3 || { log_fatal "python3 no encontrado"; exit 1; }

    local version major minor
    version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
    major=$(echo "$version" | cut -d. -f1)
    minor=$(echo "$version" | cut -d. -f2)

    if [[ "$major" -lt 3 ]] || ([[ "$major" -eq 3 ]] && [[ "$minor" -lt 11 ]]); then
        log_fatal "Python ${version} — se requiere 3.11+"
        exit 1
    fi
    log_success "Python ${version}"

    # --- Virtual env ---
    local venv_dir="${PROJECT_ROOT}/venv"
    if exists_dir "$venv_dir" && exists_file "${venv_dir}/bin/pip"; then
        log_success "venv existe: ${venv_dir}"
    else
        log_fatal "venv no encontrado en ${venv_dir}"
        log_fatal "  Crea el entorno manualmente:"
        log_fatal "    python3 -m venv venv"
        log_fatal "    venv/bin/pip install -r requirements/development.txt"
        exit 1
    fi

    # --- Drivers críticos ---
    local python="${venv_dir}/bin/python3"
    "$python" -c "import psycopg2" 2>/dev/null \
        && log_success "psycopg2 OK" \
        || { log_fatal "psycopg2 NO disponible — revisa libpq-dev"; exit 1; }

    "$python" -c "import MySQLdb" 2>/dev/null \
        && log_success "mysqlclient OK" \
        || { log_fatal "mysqlclient NO disponible — revisa default-libmysqlclient-dev"; exit 1; }
}

# =============================================================================
# FASE 4 — Bases de datos
# Arranca y habilita servicios en boot, luego crea BD/usuario si no existen.
# No es FATAL: las DBs pueden estar en otro host o no instaladas localmente.
# =============================================================================

# Intenta arrancar un servicio si está inactivo y lo habilita para boot.
# En entornos con systemd usa systemctl; en contenedores/SysVinit usa `service`.
# Uso: try_start_service <nombre> <comando_check>
try_start_service() {
    local name="$1" check_cmd="$2"
    local has_systemd=false

    systemctl is-system-running &>/dev/null 2>&1 && has_systemd=true

    if eval "$check_cmd" &>/dev/null 2>&1; then
        log_success "${name} ya está activo"
        return 0
    fi

    log_info "${name} inactivo — intentando arrancar..."

    local started=false
    if $has_systemd; then
        if systemctl start "$name" &>/dev/null 2>&1; then
            started=true
            log_success "${name} iniciado (systemctl)"
            systemctl enable "$name" &>/dev/null 2>&1 \
                && log_info "${name} habilitado en arranque (systemctl enable)" \
                || log_warn "${name}: no se pudo habilitar en arranque"
        fi
    fi

    if ! $started; then
        # Fallback SysVinit / contenedor (sin systemd)
        if service "$name" start &>/dev/null 2>&1; then
            started=true
            log_success "${name} iniciado (service — entorno sin systemd)"
            log_info "${name}: systemctl enable no aplica en este entorno"
        fi
    fi

    if ! $started; then
        log_warn "${name}: no se pudo iniciar — puede no estar instalado localmente"
    fi
}

phase_databases() {
    log_header "Fase 4/6 — Bases de datos (via IACT-db)"

    # La infraestructura de BD es responsabilidad exclusiva de IACT-db.
    # Este fase:
    #   1. Arranca los servicios si no están corriendo (MariaDB + PostgreSQL)
    #   2. Delega el setup (BD, usuario, privilegios) en IACT-db/setup.sh
    #
    # Ver: scripts/documents/relacion_con_iact_db.md

    # --- Resolver ruta a IACT-db ---
    local iact_db_path
    iact_db_path="$(_resolve_iact_db_path)"

    if [[ -z "$iact_db_path" || ! -d "$iact_db_path" ]]; then
        log_warn "IACT-db no encontrado en: ${iact_db_path:-<no resuelto>}"
        log_warn "  Opciones:"
        log_warn "    1) sudo bash scripts/bootstrap.sh --iact-db=/ruta/a/IACT-db"
        log_warn "    2) Añadir IACT_DB_PATH=/ruta/a/IACT-db en .env"
        log_warn "  Saltando setup de BD — asegúrate de ejecutar IACT-db/setup.sh"
        return 0
    fi

    log_info "IACT-db: ${iact_db_path}"
    echo ""

    # --- Paso 1: Arrancar servicios ---
    log_info "Arrancando PostgreSQL..."
    try_start_service "postgresql" "pg_isready -h 127.0.0.1 -p 5432 -q"

    log_info "Arrancando MariaDB..."
    if ! db_start_mariadb; then
        log_warn "MariaDB no pudo arrancar automaticamente"
        log_warn "  Verifica: sudo service mariadb status"
    fi

    echo ""

    # --- Paso 2: Delegar setup en IACT-db ---
    local setup_script="${iact_db_path}/setup.sh"

    if [[ ! -f "$setup_script" ]]; then
        log_warn "IACT-db/setup.sh no encontrado: ${setup_script}"
        log_warn "  Verifica la instalación de IACT-db"
        return 0
    fi

    log_info "Ejecutando IACT-db/setup.sh..."
    echo ""

    if bash "$setup_script"; then
        log_success "Fase 4 completa — BD configuradas por IACT-db"
    else
        log_warn "IACT-db/setup.sh reportó errores"
        log_warn "  Ejecuta manualmente: bash ${iact_db_path}/verify.sh"
    fi

    return 0   # Siempre continúa
}

# =============================================================================
# FASE 5 — Apache
# Configura virtual host, permisos, static files, reinicia servicio
# No es FATAL: puede no estar instalado en el entorno
# =============================================================================
phase_apache() {
    log_header "Fase 5/6 — Apache"

    local apache_setup="${APACHE_DIR}/setup_apache.sh"

    if [[ ! -f "$apache_setup" ]]; then
        log_warn "setup_apache.sh no encontrado en ${APACHE_DIR}"
        log_warn "  Omitiendo fase Apache"
        return 0
    fi

    if ! command_exists apache2 && ! command_exists apache2ctl; then
        log_warn "Apache2 no está instalado — omitiendo fase"
        log_warn "  Instalar: sudo apt-get install -y apache2 libapache2-mod-wsgi-py3"
        return 0
    fi

    bash "$apache_setup" && \
        log_success "Apache configurado correctamente" || \
        log_warn "Apache setup tuvo advertencias — revisa ${APACHE_DIR}/setup_apache.sh"

    return 0
}

# =============================================================================
# FASE 6 — Verificación completa del entorno
# Ejecuta check_tools: muestra estado de TODO en una sola vista
# =============================================================================
phase_verify() {
    log_header "Fase 6/6 — Estado completo del entorno"
    echo ""

    # Activar venv temporalmente para que check_tools vea los paquetes Python
    local venv_python="${PROJECT_ROOT}/venv/bin/python3"
    if exists_file "$venv_python"; then
        export PATH="${PROJECT_ROOT}/venv/bin:${PATH}"
        log_info "venv activado para verificación de paquetes Python"
        echo ""
    fi

    bash "${SYSTEM_DIR}/check_tools.sh" || {
        log_warn "check_tools reportó errores — ver salida anterior"
    }
}

# =============================================================================
# MAIN
# =============================================================================
main() {
    start_timer

    echo ""
    log_separator 60 "="
    echo "  IACT API — Bootstrap v2.0.0"
    echo "  sudo bash scripts/bootstrap.sh [--skip-update]"
    [[ "$SKIP_APT_UPDATE" == "true" ]] && echo "  (--skip-update activo: se omite apt-get update)"
    log_separator 60 "="
    echo ""

    phase_os
    echo ""

    phase_system_packages
    echo ""

    phase_python
    echo ""

    phase_databases
    echo ""

    phase_apache
    echo ""

    phase_verify

    log_separator 60 "="
    log_info "Tiempo total: $(show_elapsed)"
    log_success "Bootstrap completado."
    echo ""
    log_info "Siguientes pasos (primera vez):"
    log_info "  source venv/bin/activate"
    log_info "  cp .env.example .env              # ajusta las variables"
    log_info "  bash /ruta/a/IACT-db/setup.sh     # configurar BDs"
    log_info "  cd callcentersite && python manage.py migrate"
    echo ""
    log_info "Para verificar estado en cualquier momento:"
    log_info "  sudo bash scripts/bootstrap.sh"
    echo ""
}

main
