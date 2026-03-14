#!/bin/bash
# IACT API - Check Tools
# Version: 0.2.0
# Description: Verifica herramientas del entorno de desarrollo IACT
#
# Uso:
#   bash scripts/check_tools.sh
#
# Variables opcionales de entorno:
#   POSTGRES_HOST  (default: 192.168.56.11)
#   POSTGRES_PORT  (default: 5432)
#   MARIADB_HOST   (default: 192.168.56.10)
#   MARIADB_PORT   (default: 3306)
set -euo pipefail

# =============================================================================
# LOAD UTILITIES
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/utils/logging.sh"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/utils/core.sh"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/utils/database.sh"

# =============================================================================
# CONFIGURATION
# =============================================================================
POSTGRES_HOST="${POSTGRES_HOST:-192.168.56.11}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
MARIADB_HOST="${MARIADB_HOST:-192.168.56.10}"
MARIADB_PORT="${MARIADB_PORT:-3306}"

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
    declare -A packages=(
        ["django"]="django"
        ["rest_framework"]="djangorestframework"
        ["rest_framework_simplejwt"]="djangorestframework-simplejwt"
        ["django_filters"]="django-filter"
        ["drf_spectacular"]="drf-spectacular"
        ["psycopg2"]="psycopg2"
        ["MySQLdb"]="mysqlclient"
        ["apscheduler"]="APScheduler"
        ["boto3"]="boto3"
        ["openpyxl"]="openpyxl"
        ["decouple"]="python-decouple"
        ["pytz"]="pytz"
        ["dateutil"]="python-dateutil"
    )

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
            # psycopg2 y mysqlclient son bloqueantes — error en vez de warn
            if [[ "$import_name" == "psycopg2" ]] || [[ "$import_name" == "MySQLdb" ]] || \
               [[ "$import_name" == "django" ]]; then
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
    log_header "Conectividad a bases de datos (via TCP)"
    log_info "PostgreSQL: ${POSTGRES_HOST}:${POSTGRES_PORT}"
    log_info "MariaDB:    ${MARIADB_HOST}:${MARIADB_PORT}"
    log_separator

    # PostgreSQL TCP
    if tcp_is_reachable "$POSTGRES_HOST" "$POSTGRES_PORT" 3; then
        ok "PostgreSQL alcanzable en ${POSTGRES_HOST}:${POSTGRES_PORT}"
    else
        warn "PostgreSQL NO alcanzable en ${POSTGRES_HOST}:${POSTGRES_PORT} — ejecutar: vagrant up"
    fi

    # MariaDB TCP
    if tcp_is_reachable "$MARIADB_HOST" "$MARIADB_PORT" 3; then
        ok "MariaDB alcanzable en ${MARIADB_HOST}:${MARIADB_PORT}"
    else
        warn "MariaDB NO alcanzable en ${MARIADB_HOST}:${MARIADB_PORT} — ejecutar: vagrant up"
    fi
}

check_environment_file() {
    log_header "Variables de entorno (.env)"

    local env_file="${PROJECT_ROOT}/.env"
    local env_example="${PROJECT_ROOT}/.env.example"

    if exists_file "$env_file"; then
        ok ".env encontrado"
        local required_vars=("SECRET_KEY" "DEBUG" "ALLOWED_HOSTS" "DATABASE_URL" "LEGACY_DATABASE_URL" "SESSION_ENGINE")
        for var in "${required_vars[@]}"; do
            if grep -q "^${var}=" "$env_file" 2>/dev/null; then
                ok "  ${var} configurado"
            else
                warn "  ${var} NO configurado en .env"
            fi
        done
    elif exists_file "$env_example"; then
        warn ".env NO encontrado — copiar: cp .env.example .env"
    else
        warn ".env y .env.example NO encontrados"
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
    log_header "CHECK TOOLS - IACT API v2.2.1"

    check_python
    check_python_packages
    check_testing_tools
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
        log_info "  1. python3 -m venv venv && source venv/bin/activate"
        log_info "  2. pip install -r requirements/development.txt"
        log_info "  3. cp .env.example .env  (y editar valores)"
        log_info "  4. vagrant up            (para levantar las DBs)"
        echo ""
        exit 1
    fi
}

main
