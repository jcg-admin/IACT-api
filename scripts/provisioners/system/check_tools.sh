#!/bin/bash
# IACT API - Check Tools
# Version: 0.3.0
# Description: Verifica herramientas del entorno de desarrollo IACT
#
# Uso:
#   bash scripts/provisioners/system/check_tools.sh
#   sudo bash scripts/bootstrap.sh   (llamado automáticamente)
#
# Variables opcionales de entorno:
#   POSTGRES_HOST  (default: 127.0.0.1)
#   POSTGRES_PORT  (default: 5432)
#   MARIADB_HOST   (default: 127.0.0.1)
#   MARIADB_PORT   (default: 3306)
set -euo pipefail

# =============================================================================
# LOAD UTILITIES
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
export PROJECT_ROOT

# shellcheck disable=SC1091
source "${PROJECT_ROOT}/scripts/utils/logging.sh"
# shellcheck disable=SC1091
source "${PROJECT_ROOT}/scripts/utils/core.sh"
# shellcheck disable=SC1091
source "${PROJECT_ROOT}/scripts/utils/network.sh"
# shellcheck disable=SC1091
source "${PROJECT_ROOT}/scripts/utils/database.sh"

# =============================================================================
# AUTO-ACTIVATE VENV
# Si existe venv/ en el proyecto y no está ya activo, lo agrega al PATH.
# Así check_tools funciona igual con o sin `source venv/bin/activate`.
# =============================================================================
VENV_PYTHON="${PROJECT_ROOT}/venv/bin/python3"
if [[ -f "$VENV_PYTHON" ]]; then
    if [[ "${VIRTUAL_ENV:-}" != "${PROJECT_ROOT}/venv" ]]; then
        export PATH="${PROJECT_ROOT}/venv/bin:${PATH}"
    fi
fi

# =============================================================================
# CONFIGURATION — load from .env, fallback to Vagrant defaults
# =============================================================================
ENV_FILE="${PROJECT_ROOT}/.env"
if [[ -f "$ENV_FILE" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +a
fi

POSTGRES_HOST="${DB_HOST:-127.0.0.1}"
POSTGRES_PORT="${DB_PORT:-5432}"
MARIADB_HOST="${IVR_DB_HOST:-127.0.0.1}"
MARIADB_PORT="${IVR_DB_PORT:-3306}"

ERRORS=0
WARNINGS=0
OK_COUNT=0

# =============================================================================
# RESULT HELPERS (wrap log_* with counters)
# =============================================================================
ok() {
    log_success "$1"
    OK_COUNT=$((OK_COUNT + 1))
}

warn() {
    log_warn "$1"
    WARNINGS=$((WARNINGS + 1))
}

fail() {
    log_error "$1"
    ERRORS=$((ERRORS + 1))
}

# =============================================================================
# CHECK FUNCTIONS
# =============================================================================
check_python() {
    log_header "Python (requerido: 3.11+)"

    if ! command_exists python3; then
        fail "python3 NO encontrado"
        return
    fi

    local version major minor
    version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
    major=$(echo "$version" | cut -d. -f1)
    minor=$(echo "$version" | cut -d. -f2)

    if [[ "$major" -gt 3 ]] || ([[ "$major" -eq 3 ]] && [[ "$minor" -ge 11 ]]); then
        ok "Python ${version}"
    else
        fail "Python ${version} — se requiere 3.11+"
    fi

    if command_exists pip3 || command_exists pip; then
        local pip_cmd; pip_cmd=$(command -v pip3 2>/dev/null || command -v pip)
        ok "pip: $($pip_cmd --version 2>&1 | head -1)"
    else
        fail "pip NO encontrado"
    fi

    if python3 -m venv --help &>/dev/null; then
        ok "venv disponible"
    else
        warn "venv NO disponible"
    fi
}

check_python_packages() {
    log_header "Paquetes Python (drivers y core)"

    local pkg import_name version
    # [import_name]="pip package name"
    declare -A packages=(
        ["django"]="django"
        ["rest_framework"]="djangorestframework"
        ["rest_framework_simplejwt"]="djangorestframework-simplejwt"
        ["django_filters"]="django-filter"
        ["drf_spectacular"]="drf-spectacular"
        ["psycopg2"]="psycopg2-binary"
        ["MySQLdb"]="mysqlclient"
        ["apscheduler"]="APScheduler"
        ["boto3"]="boto3"
        ["openpyxl"]="openpyxl"
        ["decouple"]="python-decouple"
        ["pytz"]="pytz"
        ["dateutil"]="python-dateutil"
        ["jwt"]="PyJWT"
        ["sqlparse"]="sqlparse"
        ["tzlocal"]="tzlocal"
        ["yaml"]="PyYAML"
    )

    # Paquetes bloqueantes (ERROR si faltan)
    local critical="psycopg2 MySQLdb django"

    for import_name in "${!packages[@]}"; do
        pkg="${packages[$import_name]}"
        if python3 -c "import $import_name" &>/dev/null; then
            version=$(python3 -c "
import $import_name
v = getattr($import_name, '__version__', None) or getattr($import_name, 'VERSION', None)
print(v or 'instalado')
" 2>/dev/null || echo "instalado")
            ok "${pkg} (${version})"
        else
            if [[ " $critical " == *" $import_name "* ]]; then
                fail "${pkg} NO instalado — pip install ${pkg}"
            else
                warn "${pkg} NO instalado — pip install ${pkg}"
            fi
        fi
    done
}

check_testing_tools() {
    log_header "Herramientas de testing"

    declare -A test_packages=(
        ["pytest"]="pytest"
        ["pytest_django"]="pytest-django"
        ["pytest_cov"]="pytest-cov"
        ["factory"]="factory-boy"
        ["faker"]="faker"
        ["coverage"]="coverage"
    )

    for import_name in "${!test_packages[@]}"; do
        pkg="${test_packages[$import_name]}"
        if python3 -c "import $import_name" &>/dev/null; then
            ok "${pkg}"
        else
            warn "${pkg} NO instalado — pip install ${pkg}"
        fi
    done
}

check_dev_extras() {
    log_header "Herramientas dev (opcionales)"

    declare -A dev_packages=(
        ["debug_toolbar"]="django-debug-toolbar"
        ["django_extensions"]="django-extensions"
        ["IPython"]="ipython"
    )

    for import_name in "${!dev_packages[@]}"; do
        pkg="${dev_packages[$import_name]}"
        if python3 -c "import $import_name" &>/dev/null; then
            ok "${pkg}"
        else
            warn "${pkg} NO instalado — pip install ${pkg}"
        fi
    done
}

check_code_quality() {
    log_header "Calidad de código (desarrollo)"
    local tools=("black" "flake8" "isort" "mypy")
    for tool in "${tools[@]}"; do
        if command_exists "$tool"; then
            ok "${tool}: $($tool --version 2>&1 | head -1)"
        else
            warn "${tool} NO encontrado — pip install ${tool}"
        fi
    done
}

check_system_tools() {
    log_header "Herramientas del sistema"

    local required=("git" "bash" "curl")
    for tool in "${required[@]}"; do
        if command_exists "$tool"; then
            ok "${tool}: $($tool --version 2>&1 | head -1)"
        else
            fail "${tool} NO encontrado"
        fi
    done

    # Herramientas de red
    if command_exists netstat; then
        ok "netstat: $(netstat --version 2>&1 | head -1)"
    else
        warn "netstat NO encontrado — instalar net-tools"
    fi

    if command_exists ss; then
        ok "ss: $(ss --version 2>&1 | head -1)"
    else
        warn "ss NO encontrado — instalar iproute2"
    fi

    # DB clients (opcionales — Django usa drivers Python, no los binarios)
    if command_exists mysqladmin; then
        ok "mysqladmin: $(mysqladmin --version 2>&1 | head -1)"
    else
        warn "mysqladmin NO encontrado — instalar mariadb-client (opcional)"
    fi

    if command_exists psql; then
        ok "psql: $(psql --version 2>&1 | head -1)"
    else
        warn "psql NO encontrado — instalar postgresql-client (opcional)"
    fi

    if command_exists pg_isready; then
        ok "pg_isready disponible"
    else
        warn "pg_isready NO encontrado — instalar postgresql-client"
    fi
}

check_database_connectivity() {
    log_header "Conectividad a bases de datos"

    # --- PostgreSQL (default DB, READ+WRITE) ---
    log_info "PostgreSQL: ${POSTGRES_HOST}:${POSTGRES_PORT}"
    if command_exists pg_isready && pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -q 2>/dev/null; then
        ok "PostgreSQL activo (pg_isready) en ${POSTGRES_HOST}:${POSTGRES_PORT}"
    elif tcp_is_reachable "$POSTGRES_HOST" "$POSTGRES_PORT" 3; then
        ok "PostgreSQL alcanzable via TCP en ${POSTGRES_HOST}:${POSTGRES_PORT}"
    else
        warn "PostgreSQL NO alcanzable en ${POSTGRES_HOST}:${POSTGRES_PORT}"
        warn "  Verifica: sudo pg_ctlcluster 16 main status"
    fi

    log_separator

    # --- MariaDB (ivr_legacy, READ-ONLY CNST-003) ---
    # Intenta socket Unix primero, TCP despues (igual que database.sh)
    log_info "MariaDB: ${MARIADB_HOST}:${MARIADB_PORT} (ivr_legacy, read-only)"
    local mariadb_ok=false

    if command_exists mysqladmin; then
        for sock in /run/mysqld/mysqld.sock /var/run/mysqld/mysqld.sock; do
            if [[ -S "$sock" ]] && mysqladmin --socket="$sock" ping --silent >/dev/null 2>&1; then
                ok "MariaDB activo via socket: ${sock}"
                mariadb_ok=true
                break
            fi
        done
    fi

    if [[ "$mariadb_ok" != "true" ]]; then
        if mariadb_is_running "$MARIADB_HOST" "$MARIADB_PORT"; then
            ok "MariaDB alcanzable via TCP en ${MARIADB_HOST}:${MARIADB_PORT}"
            mariadb_ok=true
        else
            warn "MariaDB NO alcanzable ni via socket ni TCP"
            warn "  Verifica: sudo service mariadb status"
            warn "  O revisa: /var/lib/mysql/mysqld_err.log"
        fi
    fi

    # Verificar conexion Django con credenciales de ivr_legacy (si MariaDB responde)
    if [[ "$mariadb_ok" == "true" ]]; then
        local ivr_db="${IVR_DB_NAME:-ivr_legacy}"
        local ivr_user="${IVR_DB_USER:-django_user}"
        local ivr_pass="${IVR_DB_PASSWORD:-django_pass}"

        for sock in /run/mysqld/mysqld.sock /var/run/mysqld/mysqld.sock; do
            if [[ -S "$sock" ]]; then
                if mysql --socket="$sock" -u "$ivr_user" -p"${ivr_pass}"                    -e "SELECT 1;" "$ivr_db" &>/dev/null; then
                    ok "Conexion Django a ivr_legacy OK (socket): ${ivr_user}@${ivr_db}"
                    return
                fi
            fi
        done

        mysql -h "$MARIADB_HOST" -P "$MARIADB_PORT"             -u "$ivr_user" -p"${ivr_pass}"             -e "SELECT 1;" "$ivr_db" &>/dev/null             && ok "Conexion Django a ivr_legacy OK (TCP): ${ivr_user}@${ivr_db}"             || warn "No se pudo conectar a ivr_legacy como ${ivr_user} — ejecuta mariadb/db_setup.sh"
    fi
}

check_environment_file() {
    log_header "Variables de entorno (.env)"

    local env_file="${PROJECT_ROOT}/.env"

    if exists_file "$env_file"; then
        ok ".env encontrado"
        local required_vars=(
            "SECRET_KEY"
            "DB_HOST" "DB_PORT" "DB_NAME" "DB_USER" "DB_PASSWORD"
            "IVR_DB_HOST" "IVR_DB_PORT" "IVR_DB_NAME" "IVR_DB_USER" "IVR_DB_PASSWORD"
        )
        for var in "${required_vars[@]}"; do
            if grep -q "^${var}=" "$env_file" 2>/dev/null; then
                ok "  ${var} configurado"
            else
                warn "  ${var} NO configurado en .env"
            fi
        done
    else
        warn ".env NO encontrado en ${PROJECT_ROOT}"
    fi
}

check_project_structure() {
    log_header "Estructura del proyecto"

    local callcentersite="${PROJECT_ROOT}/callcentersite"

    if exists_file "${callcentersite}/manage.py"; then
        ok "manage.py encontrado"
    else
        warn "manage.py NO encontrado en callcentersite/"
    fi

    local dirs=(
        "callcentersite/static/icons/menu"
        "callcentersite/static/icons/submenu"
        "callcentersite/static/icons/defaults"
    )
    for dir in "${dirs[@]}"; do
        if exists_dir "${PROJECT_ROOT}/${dir}"; then
            ok "${dir}/"
        else
            warn "${dir}/ NO encontrado"
        fi
    done
}

# =============================================================================
# MAIN
# =============================================================================
main() {
    start_timer

    echo ""
    log_header "CHECK TOOLS - IACT API v0.3.0"

    check_python
    check_python_packages
    check_testing_tools
    check_dev_extras
    check_code_quality
    check_system_tools
    check_database_connectivity
    check_environment_file
    check_project_structure

    # Summary
    log_separator 60 "="
    echo ""
    log_info  "Tiempo total: $(show_elapsed)"
    log_success "OK:           ${OK_COUNT}"
    log_warn  "Advertencias: ${WARNINGS}"
    log_error "Errores:      ${ERRORS}"
    echo ""

    if [[ $ERRORS -eq 0 ]] && [[ $WARNINGS -eq 0 ]]; then
        log_success "Entorno listo para desarrollo."
        exit 0
    elif [[ $ERRORS -eq 0 ]]; then
        log_warn "Entorno funcional con advertencias. Revisar items marcados."
        exit 0
    else
        log_error "Entorno incompleto. Corregir errores antes de continuar."
        echo ""
        log_info "Pasos sugeridos:"
        log_info "  1. sudo bash scripts/bootstrap.sh"
        log_info "  2. source venv/bin/activate"
        log_info "  3. Editar .env con los valores del entorno"
        echo ""
        exit 1
    fi
}

main
