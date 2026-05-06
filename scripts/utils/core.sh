#!/bin/bash
# =============================================================================
# core.sh — Funciones utilitarias core para scripts IACT API
# =============================================================================
# Provee: command_exists, require_command, exists_file, exists_dir
#
# Depende de: logging.sh (debe sourciarse antes)
#
# Uso:
#   source "${PROJECT_ROOT}/scripts/utils/logging.sh"
#   source "${PROJECT_ROOT}/scripts/utils/core.sh"
# =============================================================================

# -----------------------------------------------------------------------------
# command_exists <comando>
#   Retorna 0 si el comando existe en el PATH, 1 si no.
#
#   Uso:
#     if command_exists psql; then ...
# -----------------------------------------------------------------------------
command_exists() {
    command -v "$1" &>/dev/null
}

# -----------------------------------------------------------------------------
# require_command <comando>
#   Igual que command_exists pero imprime un warning si no existe.
#   Retorna 1 si el comando no existe.
#
#   Uso:
#     require_command python3 || { log_fatal "..."; exit 1; }
# -----------------------------------------------------------------------------
require_command() {
    local cmd="$1"
    if ! command_exists "$cmd"; then
        log_warn "Comando no encontrado: ${cmd}"
        return 1
    fi
    return 0
}

# -----------------------------------------------------------------------------
# exists_file <ruta>
#   Retorna 0 si el archivo existe y es un archivo regular.
# -----------------------------------------------------------------------------
exists_file() {
    [[ -f "$1" ]]
}

# -----------------------------------------------------------------------------
# exists_dir <ruta>
#   Retorna 0 si el directorio existe.
# -----------------------------------------------------------------------------
exists_dir() {
    [[ -d "$1" ]]
}
