#!/bin/bash
# =============================================================================
# logging.sh — Funciones de logging para scripts IACT API
# =============================================================================
# Provee: log_header, log_step, log_success, log_info, log_warn,
#         log_fatal, log_error, log_separator, start_timer, show_elapsed,
#         init_log
#
# Uso:
#   source "${PROJECT_ROOT}/scripts/utils/logging.sh"
# =============================================================================

# Colores (desactivados si no es terminal interactiva)
if [[ -t 1 ]]; then
    _CLR_RESET="\033[0m"
    _CLR_GREEN="\033[0;32m"
    _CLR_YELLOW="\033[0;33m"
    _CLR_RED="\033[0;31m"
    _CLR_CYAN="\033[0;36m"
    _CLR_BOLD="\033[1m"
else
    _CLR_RESET=""
    _CLR_GREEN=""
    _CLR_YELLOW=""
    _CLR_RED=""
    _CLR_CYAN=""
    _CLR_BOLD=""
fi

# Timestamp de inicio (para show_elapsed)
_TIMER_START=""

# Archivo de log activo (para init_log)
_LOG_FILE=""

# -----------------------------------------------------------------------------
# init_log <nombre>
#   Inicializa el archivo de log en PROJECT_ROOT/logs/<nombre>.log
#   Crea el directorio si no existe.
# -----------------------------------------------------------------------------
init_log() {
    local name="${1:-bootstrap}"
    local log_dir="${PROJECT_ROOT:-$(pwd)}/logs"
    mkdir -p "$log_dir"
    _LOG_FILE="${log_dir}/${name}.log"
    echo "=== $(date '+%Y-%m-%d %H:%M:%S') — Inicio de sesion ===" >> "$_LOG_FILE"
}

# Escribe en archivo de log si esta inicializado
_write_log() {
    if [[ -n "$_LOG_FILE" ]]; then
        echo "$(date '+%H:%M:%S') $*" >> "$_LOG_FILE"
    fi
}

# -----------------------------------------------------------------------------
# log_header <texto>
#   Imprime una cabecera destacada.
# -----------------------------------------------------------------------------
log_header() {
    echo ""
    echo -e "${_CLR_BOLD}${_CLR_CYAN}>>> $*${_CLR_RESET}"
    echo ""
    _write_log "HEADER $*"
}

# -----------------------------------------------------------------------------
# log_step <paso_actual> <total_pasos> <descripcion>
#   Imprime el numero de paso actual.
# -----------------------------------------------------------------------------
log_step() {
    local current="$1"
    local total="$2"
    shift 2
    echo -e "${_CLR_BOLD}[${current}/${total}]${_CLR_RESET} $*"
    _write_log "STEP [${current}/${total}] $*"
}

# -----------------------------------------------------------------------------
# log_success <texto>
# -----------------------------------------------------------------------------
log_success() {
    echo -e "${_CLR_GREEN}  OK${_CLR_RESET}  $*"
    _write_log "OK   $*"
}

# -----------------------------------------------------------------------------
# log_info <texto>
# -----------------------------------------------------------------------------
log_info() {
    echo -e "  --  $*"
    _write_log "INFO $*"
}

# -----------------------------------------------------------------------------
# log_warn <texto>
# -----------------------------------------------------------------------------
log_warn() {
    echo -e "${_CLR_YELLOW}WARN${_CLR_RESET}  $*"
    _write_log "WARN $*"
}

# -----------------------------------------------------------------------------
# log_error <texto>
# -----------------------------------------------------------------------------
log_error() {
    echo -e "${_CLR_RED}ERR ${_CLR_RESET}  $*" >&2
    _write_log "ERR  $*"
}

# -----------------------------------------------------------------------------
# log_fatal <texto>
#   Error critico — imprime en rojo y en stderr.
# -----------------------------------------------------------------------------
log_fatal() {
    echo -e "${_CLR_BOLD}${_CLR_RED}FATAL${_CLR_RESET}  $*" >&2
    _write_log "FATAL $*"
}

# -----------------------------------------------------------------------------
# log_separator <largo> <caracter>
#   Imprime una linea separadora. Ej: log_separator 60 "="
# -----------------------------------------------------------------------------
log_separator() {
    local len="${1:-60}"
    local char="${2:--}"
    local line
    line=$(printf '%*s' "$len" '' | tr ' ' "$char")
    echo "$line"
    _write_log "$line"
}

# -----------------------------------------------------------------------------
# start_timer
#   Registra el momento de inicio para show_elapsed.
# -----------------------------------------------------------------------------
start_timer() {
    _TIMER_START=$(date +%s)
}

# -----------------------------------------------------------------------------
# show_elapsed
#   Imprime el tiempo transcurrido desde start_timer.
# -----------------------------------------------------------------------------
show_elapsed() {
    if [[ -z "$_TIMER_START" ]]; then
        echo "0s"
        return
    fi
    local end
    end=$(date +%s)
    local elapsed=$(( end - _TIMER_START ))
    if (( elapsed < 60 )); then
        echo "${elapsed}s"
    else
        echo "$(( elapsed / 60 ))m $(( elapsed % 60 ))s"
    fi
}
