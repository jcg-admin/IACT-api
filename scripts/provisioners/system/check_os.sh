#!/bin/bash
# =============================================================================
# check_os.sh — Verifica que el SO sea Ubuntu 24.04.x LTS
# =============================================================================
# IDEMPOTENTE: solo lectura, sin efectos secundarios.
# FATAL: si el SO no es Ubuntu 24.04.x, imprime el error y sale con código 1.
#
# Uso:
#   bash scripts/provisioners/system/check_os.sh
#   # o invocado por bootstrap.sh
#
# Salida:
#   0 — Ubuntu 24.04.x LTS confirmado
#   1 — SO incompatible o no se puede determinar
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

source "${PROJECT_ROOT}/scripts/utils/logging.sh"

REQUIRED_ID="ubuntu"
REQUIRED_VERSION_PREFIX="24.04"

# =============================================================================
# LEER /etc/os-release
# =============================================================================
check_os() {
    log_header "Verificación del sistema operativo"

    local os_release="/etc/os-release"
    if [[ ! -f "$os_release" ]]; then
        log_fatal "No se encontró ${os_release} — sistema operativo desconocido"
        echo ""
        log_error "Este proyecto requiere: Ubuntu ${REQUIRED_VERSION_PREFIX}.x LTS"
        exit 1
    fi

    # Leer variables del archivo
    local os_id="" os_version_id="" os_pretty_name="" os_version_codename=""
    # shellcheck disable=SC1090
    source "$os_release"

    os_id="${ID:-}"
    os_version_id="${VERSION_ID:-}"
    os_pretty_name="${PRETTY_NAME:-}"
    os_version_codename="${VERSION_CODENAME:-}"

    log_info "Sistema detectado: ${os_pretty_name}"
    log_info "  ID            : ${os_id}"
    log_info "  VERSION_ID    : ${os_version_id}"
    log_info "  Codename      : ${os_version_codename}"
    echo ""

    # -------------------------------------------------------------------------
    # Verificar distro
    # -------------------------------------------------------------------------
    if [[ "${os_id,,}" != "$REQUIRED_ID" ]]; then
        log_fatal "Distribución no compatible: '${os_id}'"
        echo ""
        log_error "  Requerido : Ubuntu ${REQUIRED_VERSION_PREFIX}.x LTS"
        log_error "  Detectado : ${os_pretty_name}"
        echo ""
        log_error "No se puede continuar. Instala Ubuntu ${REQUIRED_VERSION_PREFIX}.x LTS y vuelve a ejecutar:"
        log_error "  sudo bash scripts/bootstrap.sh"
        exit 1
    fi

    # -------------------------------------------------------------------------
    # Verificar versión — acepta 24.04, 24.04.1, 24.04.2, 24.04.3, ...
    # -------------------------------------------------------------------------
    if [[ "${os_version_id}" != "${REQUIRED_VERSION_PREFIX}"* ]]; then
        log_fatal "Versión de Ubuntu no compatible: ${os_version_id}"
        echo ""
        log_error "  Requerido : Ubuntu ${REQUIRED_VERSION_PREFIX}.x LTS"
        log_error "  Detectado : Ubuntu ${os_version_id} (${os_pretty_name})"
        echo ""
        log_error "No se puede continuar. Instala Ubuntu ${REQUIRED_VERSION_PREFIX}.x LTS y vuelve a ejecutar:"
        log_error "  sudo bash scripts/bootstrap.sh"
        exit 1
    fi

    log_success "Sistema operativo compatible: ${os_pretty_name}"
}

# =============================================================================
# MAIN
# =============================================================================
check_os
