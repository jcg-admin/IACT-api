#!/bin/bash
# IACT API - Bootstrap (Entorno de Desarrollo Local)
# Version: 0.3.0
# Description: Verifica y prepara el entorno local de desarrollo.
#              NO instala ni provisionea bases de datos — eso lo hacen
#              los provisioners en scripts/provisioners/{mariadb,postgres}/
#
# Uso:
#   bash scripts/bootstrap.sh
#
# Variables opcionales:
#   POSTGRES_HOST, POSTGRES_PORT, MARIADB_HOST, MARIADB_PORT
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
export PROJECT_ROOT

# Load full utils stack
source "${SCRIPT_DIR}/utils/core.sh"
source "${SCRIPT_DIR}/utils/logging.sh"
source "${SCRIPT_DIR}/utils/network.sh"
source "${SCRIPT_DIR}/utils/database.sh"
source "${SCRIPT_DIR}/utils/validation.sh"
source "${SCRIPT_DIR}/utils/provisioning.sh"

# =============================================================================
# CONFIGURATION
# =============================================================================
POSTGRES_HOST="${POSTGRES_HOST:-192.168.56.11}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
MARIADB_HOST="${MARIADB_HOST:-192.168.56.10}"
MARIADB_PORT="${MARIADB_PORT:-3306}"

LOG_NAME="bootstrap"
init_log "$LOG_NAME"

# =============================================================================
# STEPS
# =============================================================================

step_python() {
    log_header "Paso 1/6 — Python"
    require_command python3 || { log_fatal "python3 no encontrado"; return 1; }

    local version major minor
    version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
    major=$(echo "$version" | cut -d. -f1)
    minor=$(echo "$version" | cut -d. -f2)

    if [[ "$major" -lt 3 ]] || ([[ "$major" -eq 3 ]] && [[ "$minor" -lt 11 ]]); then
        log_fatal "Python ${version} — se requiere 3.11+"
        return 1
    fi
    log_success "Python ${version}"

    require_command pip3 || require_command pip || { log_fatal "pip no encontrado"; return 1; }
    log_success "pip disponible"
}

step_virtualenv() {
    log_header "Paso 2/6 — Entorno virtual"
    local venv_dir="${PROJECT_ROOT}/venv"

    if exists_dir "$venv_dir"; then
        log_success "Entorno virtual encontrado: ${venv_dir}"
    else
        log_info "Creando entorno virtual en ${venv_dir}"
        python3 -m venv "$venv_dir" || { log_error "No se pudo crear el entorno virtual"; return 1; }
        log_success "Entorno virtual creado"
    fi

    exists_file "${venv_dir}/bin/pip" || { log_error "pip no encontrado en venv"; return 1; }
    log_success "pip en venv: $(${venv_dir}/bin/pip --version 2>&1 | head -1)"
}

step_system_deps() {
    log_header "Paso 3/6 — Dependencias del sistema"

    local packages=(
        "libpq-dev"
        "default-libmysqlclient-dev"
        "python3-dev"
        "build-essential"
        "pkg-config"
    )

    log_info "Actualizando índice de paquetes"
    apt-get update -qq 2>/dev/null || log_warn "apt-get update falló — continuando"

    for pkg in "${packages[@]}"; do
        if is_package_installed "$pkg"; then
            log_success "${pkg} ya instalado"
        else
            log_info "Instalando ${pkg}"
            apt-get install -y "$pkg" -qq 2>/dev/null && \
                log_success "${pkg} instalado" || \
                { log_error "No se pudo instalar ${pkg}"; return 1; }
        fi
    done
}

step_dependencies() {
    log_header "Paso 4/6 — Dependencias Python"
    local venv_pip="${PROJECT_ROOT}/venv/bin/pip"
    local req_file="${PROJECT_ROOT}/requirements/development.txt"

    validate_file_exists "$req_file" || return 1

    log_info "Instalando desde ${req_file}"
    "$venv_pip" install -r "$req_file" -q || { log_error "Falló pip install"; return 1; }
    log_success "Dependencias instaladas"

    local python="${PROJECT_ROOT}/venv/bin/python3"
    "$python" -c "import psycopg2"  2>/dev/null && log_success "psycopg2 disponible"  || { log_error "psycopg2 NO disponible"; return 1; }
    "$python" -c "import MySQLdb"   2>/dev/null && log_success "mysqlclient disponible" || { log_error "mysqlclient NO disponible"; return 1; }
}

step_env_file() {
    log_header "Paso 5/6 — Archivo .env"
    local env_file="${PROJECT_ROOT}/.env"
    local env_example="${PROJECT_ROOT}/.env.example"

    if exists_file "$env_file"; then
        log_success ".env encontrado"
    elif exists_file "$env_example"; then
        log_info "Copiando .env.example → .env"
        cp "$env_example" "$env_file"
        log_warn "Editar antes de usar: ${env_file}"
    else
        log_error ".env.example no encontrado en ${PROJECT_ROOT}"
        return 1
    fi

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

step_databases() {
    log_header "Paso 6/6 — Conectividad a bases de datos"
    local pg_ok=0 db_ok=0

    log_info "PostgreSQL → ${POSTGRES_HOST}:${POSTGRES_PORT}"
    if can_reach_port "$POSTGRES_HOST" "$POSTGRES_PORT" 3; then
        log_success "PostgreSQL alcanzable"
        pg_ok=1
    else
        log_warn "PostgreSQL NO alcanzable — verificar: vagrant up"
    fi

    log_info "MariaDB → ${MARIADB_HOST}:${MARIADB_PORT}"
    if can_reach_port "$MARIADB_HOST" "$MARIADB_PORT" 3; then
        log_success "MariaDB alcanzable"
        db_ok=1
    else
        log_warn "MariaDB NO alcanzable — verificar: vagrant up"
    fi

    [[ $pg_ok -eq 1 ]] && [[ $db_ok -eq 1 ]] && \
        log_success "Ambas bases de datos alcanzables" || \
        log_warn "Una o más bases de datos no disponibles"
    return 0
}

# =============================================================================
# MAIN
# =============================================================================
main() {
    start_timer
    step_header "IACT API" "Bootstrap del entorno de desarrollo local"

    local steps=(
        "step_python"
        "step_virtualenv"
        "step_system_deps"
        "step_dependencies"
        "step_env_file"
        "step_databases"
    )

    local total=${#steps[@]} failed=0

    for i in "${!steps[@]}"; do
        local step="${steps[$i]}"
        log_step "$((i + 1))" "$total" "$step"
        if ! "$step"; then
            log_error "Paso fallido: ${step}"
            failed=$((failed + 1))
            # Pasos 1-4 son bloqueantes
            if [[ $((i + 1)) -le 4 ]]; then
                log_fatal "Paso crítico fallido — abortando bootstrap"
                exit 1
            fi
        fi
    done

    log_separator 60 "="
    log_info "Tiempo total: $(show_elapsed)"
    echo ""

    if [[ $failed -eq 0 ]]; then
        log_success "Bootstrap completado exitosamente."
        echo ""
        log_info "Siguiente paso:"
        log_info "  source venv/bin/activate"
        log_info "  cd callcentersite && python manage.py migrate"
    else
        log_warn "Bootstrap completado con ${failed} advertencia(s)."
        log_warn "Log: ${PROJECT_ROOT}/scripts/logs/${LOG_NAME}.log"
    fi
    echo ""
}

main
