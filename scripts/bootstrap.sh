#!/bin/bash
# =============================================================================
# bootstrap.sh — IACT API: Entrypoint de provisioning
# =============================================================================
# Version: 1.0.0
# Description: Orquesta la instalación y configuración completa del entorno
#              IACT API en Ubuntu 24.04.x LTS desde cero (idempotente).
#
# Uso:
#   sudo bash scripts/bootstrap.sh
#
# Requisito: Ubuntu 24.04.x LTS
#            El script verifica el SO antes de ejecutar cualquier otra cosa.
#
# Flujo:
#   Fase 1 — SO          : Verificar Ubuntu 24.04.x LTS             [FATAL]
#   Fase 2 — Paquetes    : Instalar dependencias del sistema        [FATAL]
#   Fase 3 — Python      : Entorno virtual + dependencias pip       [FATAL]
#   Fase 4 — Bases datos : PostgreSQL (iact_analytics) +            [WARN]
#                          MariaDB    (ivr_legacy, read-only)
#   Fase 5 — Apache      : Configurar virtual host IACT             [WARN]
#   Fase 6 — Verificación: check_tools — resumen del entorno        [INFO]
# =============================================================================
set -euo pipefail

# =============================================================================
# PATHS
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
export PROJECT_ROOT

PROVISIONERS_DIR="${SCRIPT_DIR}/provisioners"
SYSTEM_DIR="${PROVISIONERS_DIR}/system"
POSTGRES_DIR="${PROVISIONERS_DIR}/postgres"
MARIADB_DIR="${PROVISIONERS_DIR}/mariadb"
APACHE_DIR="${SCRIPT_DIR}/apache"

source "${SCRIPT_DIR}/utils/logging.sh"
source "${SCRIPT_DIR}/utils/core.sh"

LOG_NAME="bootstrap"
init_log "$LOG_NAME"

# =============================================================================
# FASE 1 — Sistema Operativo
# Bloquea TODA la ejecución si no es Ubuntu 24.04.x
# =============================================================================
phase_os() {
    log_header "Fase 1/6 — Sistema operativo"
    bash "${SYSTEM_DIR}/check_os.sh" || {
        echo ""
        log_fatal "SO incompatible. Bootstrap abortado."
        exit 1
    }
}

# =============================================================================
# FASE 2 — Paquetes del sistema
# net-tools, iproute2, python3-dev, libpq-dev, default-libmysqlclient-dev ...
# =============================================================================
phase_system_packages() {
    log_header "Fase 2/6 — Paquetes del sistema"

    [[ $EUID -ne 0 ]] && {
        log_fatal "Las fases 2–5 requieren root. Usa: sudo bash scripts/bootstrap.sh"
        exit 1
    }

    bash "${SYSTEM_DIR}/install_packages.sh" || {
        log_fatal "Instalación de paquetes falló — bootstrap abortado"
        exit 1
    }
}

# =============================================================================
# FASE 3 — Entorno Python
# Virtual env + pip install -r requirements/development.txt
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
    if exists_dir "$venv_dir"; then
        log_info "venv ya existe: ${venv_dir}"
    else
        log_info "Creando entorno virtual en ${venv_dir}"
        python3 -m venv "$venv_dir" || { log_fatal "No se pudo crear el venv"; exit 1; }
        log_success "venv creado"
    fi

    # --- pip install ---
    local venv_pip="${venv_dir}/bin/pip"
    local req_file="${PROJECT_ROOT}/requirements/development.txt"

    validate_file_exists "$req_file" || { log_fatal "requirements/development.txt no encontrado"; exit 1; }

    log_info "pip install -r ${req_file}"
    "$venv_pip" install -r "$req_file" -q || { log_fatal "pip install falló"; exit 1; }
    log_success "Dependencias Python instaladas"

    # --- Verificar drivers críticos ---
    local python="${venv_dir}/bin/python3"
    "$python" -c "import psycopg2"  2>/dev/null \
        && log_success "psycopg2 OK" \
        || { log_fatal "psycopg2 NO disponible — revisa libpq-dev"; exit 1; }

    "$python" -c "import MySQLdb" 2>/dev/null \
        && log_success "mysqlclient OK" \
        || { log_fatal "mysqlclient NO disponible — revisa default-libmysqlclient-dev"; exit 1; }
}

# =============================================================================
# FASE 4 — Bases de datos (provisioning local)
# Idempotente: crea BD/usuario solo si no existen
# =============================================================================
phase_databases() {
    log_header "Fase 4/6 — Bases de datos"

    local failed=0

    # PostgreSQL — iact_analytics (READ+WRITE)
    log_info "PostgreSQL: iact_analytics"
    if bash "${POSTGRES_DIR}/db_setup.sh"; then
        log_success "PostgreSQL OK"
    else
        log_warn "PostgreSQL setup falló — verifica que el servicio esté activo"
        failed=$((failed + 1))
    fi

    echo ""

    # MariaDB — ivr_legacy (READ-ONLY, CNST-003)
    log_info "MariaDB: ivr_legacy (read-only)"
    if bash "${MARIADB_DIR}/db_setup.sh"; then
        log_success "MariaDB OK"
    else
        log_warn "MariaDB setup falló — verifica que el servicio esté activo"
        failed=$((failed + 1))
    fi

    if [[ $failed -gt 0 ]]; then
        log_warn "Fase 4 completada con ${failed} advertencia(s) — continúa el bootstrap"
    else
        log_success "Fase 4 completada — ambas bases de datos listas"
    fi

    return 0   # No es fatal: las DBs pueden estar en otro servidor
}

# =============================================================================
# FASE 5 — Apache
# =============================================================================
phase_apache() {
    log_header "Fase 5/6 — Apache"

    local apache_setup="${APACHE_DIR}/setup_apache.sh"
    if [[ ! -f "$apache_setup" ]]; then
        log_warn "setup_apache.sh no encontrado — omitiendo fase Apache"
        return 0
    fi

    if bash "$apache_setup"; then
        log_success "Apache configurado"
    else
        log_warn "Apache setup falló — verifica ${apache_setup}"
    fi
    return 0
}

# =============================================================================
# FASE 6 — Verificación final (check_tools)
# =============================================================================
phase_verify() {
    log_header "Fase 6/6 — Verificación del entorno"
    log_info "Ejecutando check_tools..."
    echo ""

    # check_tools puede salir con 1 (errores) pero no queremos que falle bootstrap
    bash "${SYSTEM_DIR}/check_tools.sh" || {
        log_warn "check_tools reportó errores — revisa la salida anterior"
    }
}

# =============================================================================
# MAIN
# =============================================================================
main() {
    start_timer

    echo ""
    log_separator 60 "="
    echo "  IACT API — Bootstrap v1.0.0"
    echo "  Ubuntu 24.04.x LTS requerido"
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

    # -------------------------------------------------------------------------
    log_separator 60 "="
    log_info "Tiempo total: $(show_elapsed)"
    log_success "Bootstrap completado."
    echo ""
    log_info "Siguientes pasos:"
    log_info "  source venv/bin/activate"
    log_info "  cp .env.example .env  # si no existe"
    log_info "  cd callcentersite && python manage.py migrate"
    echo ""
}

main
