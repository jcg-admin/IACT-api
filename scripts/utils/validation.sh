#!/bin/bash
# =============================================================================
# validation.sh — Funciones de validacion para scripts IACT API
# =============================================================================
# Provee: validate_root, validate_ubuntu, validate_python_version
#
# Depende de: logging.sh, core.sh
# =============================================================================

# -----------------------------------------------------------------------------
# validate_root
#   Verifica que el script se ejecuta como root (EUID == 0).
#   Retorna 0 si es root, 1 si no.
#
#   Uso:
#     validate_root || { log_fatal "Requiere root"; exit 1; }
# -----------------------------------------------------------------------------
validate_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "Este script debe ejecutarse como root (usa sudo)"
        return 1
    fi
    return 0
}

# -----------------------------------------------------------------------------
# validate_ubuntu <version_prefix>
#   Verifica que el SO sea Ubuntu con el prefijo de version indicado.
#   Ej: validate_ubuntu "24.04"
#   Retorna 0 si coincide, 1 si no.
# -----------------------------------------------------------------------------
validate_ubuntu() {
    local required_prefix="${1:-24.04}"
    local os_release="/etc/os-release"

    if [[ ! -f "$os_release" ]]; then
        log_error "No se encontro ${os_release}"
        return 1
    fi

    local os_id os_version_id
    # shellcheck disable=SC1090
    os_id=$(. "$os_release" && echo "${ID:-}")
    os_version_id=$(. "$os_release" && echo "${VERSION_ID:-}")

    if [[ "${os_id,,}" != "ubuntu" ]]; then
        log_error "SO incompatible: ${os_id} (se requiere Ubuntu)"
        return 1
    fi

    if [[ "${os_version_id}" != "${required_prefix}"* ]]; then
        log_error "Version incompatible: Ubuntu ${os_version_id} (se requiere ${required_prefix}.x)"
        return 1
    fi

    return 0
}

# -----------------------------------------------------------------------------
# validate_python_version <major> <minor_min>
#   Verifica que python3 sea al menos major.minor_min.
#   Ej: validate_python_version 3 11
# -----------------------------------------------------------------------------
validate_python_version() {
    local required_major="${1:-3}"
    local required_minor="${2:-11}"

    if ! command_exists python3; then
        log_error "python3 no encontrado"
        return 1
    fi

    local version major minor
    version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    major=$(echo "$version" | cut -d. -f1)
    minor=$(echo "$version" | cut -d. -f2)

    if (( major < required_major )) || \
       (( major == required_major && minor < required_minor )); then
        log_error "Python ${version} no cumple el minimo requerido: ${required_major}.${required_minor}+"
        return 1
    fi

    return 0
}
