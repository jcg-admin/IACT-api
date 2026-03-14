#!/bin/bash
# =============================================================================
# install_packages.sh — Instala paquetes del sistema necesarios para IACT API
# =============================================================================
# IDEMPOTENTE: verifica con dpkg antes de instalar, no reinstala si ya existe.
# Requiere sudo / root.
#
# Uso:
#   sudo bash scripts/provisioners/system/install_packages.sh
#   # o invocado por bootstrap.sh
#
# Paquetes instalados:
#   Grupo red       : net-tools, iproute2
#   Grupo Python    : python3, python3-dev, python3-venv, python3-pip,
#                     build-essential, pkg-config
#   Grupo PostgreSQL: libpq-dev, postgresql-client
#   Grupo MariaDB   : default-libmysqlclient-dev, mariadb-client
#   Grupo general   : curl, git
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

source "${PROJECT_ROOT}/scripts/utils/logging.sh"

# =============================================================================
# GRUPOS DE PAQUETES
# Nota: algunos paquetes tienen "verificación funcional" como alternativa
# al nombre exacto del paquete dpkg (meta-paquetes con nombre versionado).
#   python3-venv     → existe como python3.X-venv; se verifica con `python3 -m venv`
#   postgresql-client→ existe como postgresql-client-16; se verifica con `psql`
# =============================================================================
declare -A PACKAGE_GROUPS=(
    ["red"]="net-tools iproute2"
    ["python"]="python3 python3-dev python3-pip build-essential pkg-config"
    ["postgresql"]="libpq-dev"
    ["mariadb"]="default-libmysqlclient-dev mariadb-client"
    ["general"]="curl git"
)

# Verificaciones funcionales: si el comando existe, el paquete se considera OK
# Formato: "nombre_descriptivo:comando_check:paquete_a_instalar_si_falla"
FUNCTIONAL_CHECKS=(
    "python3-venv:python3 -m venv --help:python3-venv"
    "postgresql-client:psql --version:postgresql-client"
)

TOTAL_STEPS=5

# =============================================================================
# PASO 1 — Prerequisitos
# =============================================================================
check_prerequisites() {
    log_step 1 $TOTAL_STEPS "Verificando prerequisitos"

    [[ $EUID -ne 0 ]] && {
        log_fatal "Ejecuta con sudo"
        log_error "  sudo bash scripts/provisioners/system/install_packages.sh"
        exit 1
    }

    command -v apt-get &>/dev/null || {
        log_fatal "apt-get no disponible — ¿es Ubuntu/Debian?"
        exit 1
    }

    log_success "Ejecutando como root con apt-get disponible"
}

# =============================================================================
# PASO 2 — Actualizar índice de paquetes
# =============================================================================
update_package_index() {
    log_step 2 $TOTAL_STEPS "Actualizando índice de paquetes apt"

    # Solo actualiza si el índice tiene más de 1 hora de antigüedad
    local apt_lists="/var/lib/apt/lists"
    local update_needed=true

    if [[ -d "$apt_lists" ]]; then
        local age_seconds
        age_seconds=$(find "$apt_lists" -maxdepth 1 -name "*.lz4" -newer /proc/1 2>/dev/null | wc -l || echo "0")
        # Si hay archivos recientes, probablemente no necesitamos actualizar
        local last_update
        last_update=$(stat -c %Y "${apt_lists}" 2>/dev/null || echo "0")
        local now
        now=$(date +%s)
        local age=$(( now - last_update ))
        if [[ $age -lt 3600 ]]; then
            update_needed=false
            log_info "Índice actualizado hace menos de 1 hora — omitiendo apt-get update"
        fi
    fi

    if [[ "$update_needed" == "true" ]]; then
        log_info "Ejecutando apt-get update"
        apt-get update -qq 2>/dev/null || {
            log_warn "apt-get update devolvió errores — continuando de todos modos"
        }
        log_success "Índice actualizado"
    fi
}

# =============================================================================
# HELPERS
# =============================================================================
is_installed() {
    dpkg-query -W -f='${Status}' "$1" 2>/dev/null | grep -q "^install ok installed"
}

install_group() {
    local group_name="$1"
    local packages_str="$2"

    log_info "Grupo [${group_name}]:"
    read -ra packages <<< "$packages_str"

    local to_install=()
    for pkg in "${packages[@]}"; do
        if is_installed "$pkg"; then
            log_info "  ✓ ${pkg} (ya instalado)"
        else
            log_info "  · ${pkg} (pendiente)"
            to_install+=("$pkg")
        fi
    done

    if [[ ${#to_install[@]} -eq 0 ]]; then
        log_success "  Todos los paquetes del grupo ya instalados"
        return 0
    fi

    log_info "  Instalando: ${to_install[*]}"
    if apt-get install -y -qq "${to_install[@]}" 2>/dev/null; then
        for pkg in "${to_install[@]}"; do
            if is_installed "$pkg"; then
                log_success "  ✓ ${pkg} instalado"
            else
                log_error "  ✗ ${pkg} falló (no aparece en dpkg)"
                return 1
            fi
        done
    else
        log_error "  apt-get install falló para el grupo [${group_name}]"
        return 1
    fi
}

# =============================================================================
# PASO 3 — Instalar paquetes de red
# =============================================================================
install_network_packages() {
    log_step 3 $TOTAL_STEPS "Paquetes de red (net-tools, iproute2)"
    install_group "red" "${PACKAGE_GROUPS[red]}" || return 1
    log_success "Paquetes de red listos"
}

# =============================================================================
# HELPER — Verificaciones funcionales (meta-paquetes con nombre versionado)
# Verifica por comando; solo instala si el comando NO está disponible
# =============================================================================
check_functional_packages() {
    log_info "Verificaciones funcionales (meta-paquetes):"

    for entry in "${FUNCTIONAL_CHECKS[@]}"; do
        local label="${entry%%:*}"
        local rest="${entry#*:}"
        local check_cmd="${rest%%:*}"
        local fallback_pkg="${rest##*:}"

        if eval "$check_cmd" &>/dev/null 2>&1; then
            log_info "  ✓ ${label} (funcional)"
        else
            log_info "  · ${label} — intentando instalar ${fallback_pkg}"
            apt-get install -y -qq "$fallback_pkg" 2>/dev/null \
                && log_success "  ✓ ${label} instalado" \
                || log_warn "  ! ${label}: apt-get falló — puede funcionar igual"
        fi
    done
}

# =============================================================================
# PASO 4 — Instalar paquetes Python y DB
# =============================================================================
install_dev_packages() {
    log_step 4 $TOTAL_STEPS "Paquetes Python, PostgreSQL, MariaDB, general"

    local failed=0
    for group in "python" "postgresql" "mariadb" "general"; do
        install_group "$group" "${PACKAGE_GROUPS[$group]}" || {
            log_error "Falló grupo: ${group}"
            failed=$((failed + 1))
        }
        echo ""
    done

    # Meta-paquetes / verificación funcional
    check_functional_packages
    echo ""

    [[ $failed -gt 0 ]] && {
        log_error "${failed} grupo(s) con errores"
        return 1
    }

    log_success "Todos los paquetes de desarrollo instalados"
}

# =============================================================================
# PASO 5 — Verificar herramientas clave post-instalación
# =============================================================================
verify_tools() {
    log_step 5 $TOTAL_STEPS "Verificando herramientas clave"

    local tools=(
        "python3:python3 --version"
        "pip3:pip3 --version"
        "git:git --version"
        "curl:curl --version"
        "psql:psql --version"
        "mysql:mysql --version"
        "netstat:netstat --version"
        "ss:ss --version"
    )

    local failed=0
    for entry in "${tools[@]}"; do
        local name="${entry%%:*}"
        local cmd="${entry##*:}"
        if command -v "$name" &>/dev/null; then
            local ver
            ver=$(eval "$cmd" 2>&1 | head -1)
            log_success "${name}: ${ver}"
        else
            log_warn "${name}: no disponible"
            failed=$((failed + 1))
        fi
    done

    [[ $failed -gt 0 ]] && log_warn "${failed} herramienta(s) no disponibles" \
                        || log_success "Todas las herramientas verificadas"
    return 0   # warnings no son fatales aquí
}

# =============================================================================
# MAIN
# =============================================================================
log_header "System Packages Setup — IACT"

check_prerequisites
update_package_index
install_network_packages
install_dev_packages
verify_tools

echo ""
log_success "Instalación de paquetes del sistema completada."
