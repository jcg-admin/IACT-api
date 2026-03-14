#!/bin/bash
# IACT API - Bootstrap
# Version: 0.2.0
# Description: Verifica y prepara el entorno de desarrollo local.
#              Adaptado de IACT DevBox bootstrap.sh:
#              - Sin Vagrant: paths usan PROJECT_ROOT
#              - Sin systemctl: service command o TCP check
#              - No instala MariaDB/PostgreSQL — asume VMs Vagrant corriendo
#
# Uso:
#   bash scripts/bootstrap.sh
#
# Variables opcionales:
#   POSTGRES_HOST, POSTGRES_PORT, MARIADB_HOST, MARIADB_PORT
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

LOG_NAME="bootstrap"

# =============================================================================
# STEP FUNCTIONS
# =============================================================================

# Paso 1 - Verificar Python y pip
step_python() {
    log_header "Paso 1/5 — Python"

    require_command python3 || {
        log_fatal "python3 no encontrado. Instalar Python 3.11+"
        return 1
    }

    local version major minor
    version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
    major=$(echo "$version" | cut -d. -f1)
    minor=$(echo "$version" | cut -d. -f2)

    if [[ "$major" -lt 3 ]] || ([[ "$major" -eq 3 ]] && [[ "$minor" -lt 11 ]]); then
        log_fatal "Python ${version} — se requiere 3.11+"
        return 1
    fi

    log_success "Python ${version}"

    require_command pip3 || require_command pip || {
        log_fatal "pip no encontrado"
        return 1
    }
    log_success "pip disponible"

    return 0
}

# Paso 2 - Verificar entorno virtual
step_virtualenv() {
    log_header "Paso 2/5 — Entorno virtual"

    local venv_dir="${PROJECT_ROOT}/venv"

    if exists_dir "$venv_dir"; then
        log_success "Entorno virtual encontrado: ${venv_dir}"
    else
        log_info "Creando entorno virtual en ${venv_dir}"
        python3 -m venv "$venv_dir" || {
            log_error "No se pudo crear el entorno virtual"
            return 1
        }
        log_success "Entorno virtual creado"
    fi

    # Verificar que pip está en el venv
    if exists_file "${venv_dir}/bin/pip"; then
        log_success "pip en venv: $(${venv_dir}/bin/pip --version 2>&1 | head -1)"
    else
        log_error "pip no encontrado en el entorno virtual"
        return 1
    fi

    return 0
}

# Paso 3a - Instalar dependencias del sistema (headers C para drivers Python)
step_system_deps() {
    log_header "Paso 3a/5 — Dependencias del sistema"

    # Requeridas para compilar psycopg2 y mysqlclient desde fuente
    local sys_packages=(
        "libpq-dev"               # headers PostgreSQL → psycopg2
        "default-libmysqlclient-dev" # headers MariaDB/MySQL → mysqlclient
        "python3-dev"             # headers Python C API
        "build-essential"         # gcc, make
        "pkg-config"              # detección de librerías
    )

    # Actualizar índice antes de instalar
    log_info "Actualizando índice de paquetes"
    apt-get update -qq 2>/dev/null || log_warn "apt-get update falló — continuando"

    for pkg in "${sys_packages[@]}"; do
        if is_package_installed "$pkg"; then
            log_success "${pkg} ya instalado"
        else
            log_info "Instalando ${pkg}"
            if apt-get install -y "$pkg" -qq 2>/dev/null; then
                log_success "${pkg} instalado"
            else
                log_error "No se pudo instalar ${pkg}"
                return 1
            fi
        fi
    done

    return 0
}

# Paso 3 - Instalar dependencias Python
step_dependencies() {
    log_header "Paso 3/5 — Dependencias Python"

    local venv_pip="${PROJECT_ROOT}/venv/bin/pip"
    local req_file="${PROJECT_ROOT}/requirements/development.txt"

    if ! exists_file "$req_file"; then
        log_error "No encontrado: ${req_file}"
        return 1
    fi

    log_info "Instalando desde ${req_file}"
    if "$venv_pip" install -r "$req_file" -q; then
        log_success "Dependencias instaladas"
    else
        log_error "Falló la instalación de dependencias"
        return 1
    fi

    # Verificar drivers críticos
    local python="${PROJECT_ROOT}/venv/bin/python3"

    if "$python" -c "import psycopg2" &>/dev/null; then
        log_success "psycopg2 (driver PostgreSQL) disponible"
    else
        log_error "psycopg2 NO disponible — revisar requirements/base.txt"
        return 1
    fi

    if "$python" -c "import MySQLdb" &>/dev/null; then
        log_success "mysqlclient (driver MariaDB) disponible"
    else
        log_error "mysqlclient NO disponible — revisar requirements/base.txt"
        return 1
    fi

    return 0
}

# Paso 4 - Verificar .env
step_env_file() {
    log_header "Paso 4/5 — Archivo .env"

    local env_file="${PROJECT_ROOT}/.env"
    local env_example="${PROJECT_ROOT}/.env.example"

    if exists_file "$env_file"; then
        log_success ".env encontrado"
    elif exists_file "$env_example"; then
        log_info ".env no encontrado — copiando desde .env.example"
        cp "$env_example" "$env_file"
        log_warn ".env copiado — EDITAR antes de ejecutar el proyecto:"
        log_warn "  ${env_file}"
    else
        log_error ".env.example no encontrado en ${PROJECT_ROOT}"
        return 1
    fi

    # Verificar variables críticas
    local missing=0
    for var in SECRET_KEY DATABASE_URL LEGACY_DATABASE_URL SESSION_ENGINE; do
        if grep -q "^${var}=" "$env_file" 2>/dev/null; then
            log_success "  ${var} configurado"
        else
            log_warn "  ${var} NO configurado"
            missing=$((missing + 1))
        fi
    done

    [[ $missing -gt 0 ]] && log_warn "${missing} variable(s) sin configurar en .env"
    return 0
}

# Paso 5 - Verificar conectividad a bases de datos
step_databases() {
    log_header "Paso 5/5 — Conectividad a bases de datos"

    local pg_ok=0 db_ok=0

    # PostgreSQL
    log_info "PostgreSQL → ${POSTGRES_HOST}:${POSTGRES_PORT}"
    if tcp_is_reachable "$POSTGRES_HOST" "$POSTGRES_PORT" 3; then
        log_success "PostgreSQL alcanzable"
        pg_ok=1
    else
        log_warn "PostgreSQL NO alcanzable en ${POSTGRES_HOST}:${POSTGRES_PORT}"
        log_warn "  Verificar: vagrant up (VM de PostgreSQL)"
    fi

    # MariaDB
    log_info "MariaDB → ${MARIADB_HOST}:${MARIADB_PORT}"
    if tcp_is_reachable "$MARIADB_HOST" "$MARIADB_PORT" 3; then
        log_success "MariaDB alcanzable"
        db_ok=1
    else
        log_warn "MariaDB NO alcanzable en ${MARIADB_HOST}:${MARIADB_PORT}"
        log_warn "  Verificar: vagrant up (VM de MariaDB)"
    fi

    # No es error fatal — las DBs pueden estar apagadas intencionalmente
    if [[ $pg_ok -eq 0 ]] || [[ $db_ok -eq 0 ]]; then
        log_warn "Una o más bases de datos no disponibles. El proyecto no arrancará hasta que estén accesibles."
    else
        log_success "Ambas bases de datos alcanzables"
    fi

    return 0
}

# =============================================================================
# MAIN
# =============================================================================
main() {
    start_timer
    init_log "$LOG_NAME"

    echo ""
    log_header "BOOTSTRAP - IACT API v2.2.1"
    log_info "PROJECT_ROOT: ${PROJECT_ROOT}"
    log_separator

    local steps=(
        "step_python"
        "step_virtualenv"
        "step_system_deps"
        "step_dependencies"
        "step_env_file"
        "step_databases"
    )

    local total=${#steps[@]}
    local failed=0

    for i in "${!steps[@]}"; do
        local step="${steps[$i]}"
        log_step "$((i + 1))" "$total" "$step"

        if ! "$step"; then
            log_error "Paso fallido: ${step}"
            failed=$((failed + 1))
            # Pasos 1-4 (python, venv, sys_deps, pip) son bloqueantes
            if [[ $((i + 1)) -le 4 ]]; then
                log_fatal "Paso crítico fallido — abortando bootstrap"
                exit 1
            fi
        fi
    done

    log_separator "=" 60
    log_info "Tiempo total: $(show_elapsed)"
    echo ""

    if [[ $failed -eq 0 ]]; then
        log_success "Bootstrap completado exitosamente."
        echo ""
        log_info "Siguiente paso — activar entorno y ejecutar Django:"
        log_info "  source venv/bin/activate"
        log_info "  cd callcentersite"
        log_info "  python manage.py migrate"
        log_info "  python manage.py runserver"
    else
        log_warn "Bootstrap completado con ${failed} advertencia(s). Revisar log:"
        log_warn "  ${PROJECT_ROOT}/scripts/logs/${LOG_NAME}.log"
    fi

    echo ""
}

main
