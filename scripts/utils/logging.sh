#!/bin/bash
# IACT API - Logging Utilities
# Version: 0.1.1
# Adapted from IACT DevBox: removed /vagrant/ paths, uses PROJECT_ROOT
set -euo pipefail

# =============================================================================
# PROJECT ROOT (resolved relative to this file)
# =============================================================================
UTILS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${UTILS_DIR}/../.." && pwd)"

# =============================================================================
# LOG LEVELS
# =============================================================================
LOG_LEVEL_DEBUG=0
LOG_LEVEL_INFO=1
LOG_LEVEL_SUCCESS=2
LOG_LEVEL_WARN=3
LOG_LEVEL_ERROR=4
LOG_LEVEL_FATAL=5

CURRENT_LOG_LEVEL=${LOG_LEVEL:-$LOG_LEVEL_INFO}

# =============================================================================
# COLORS (respects NO_COLOR)
# =============================================================================
if [[ -n "${NO_COLOR:-}" ]] || [[ "${TERM:-}" == "dumb" ]]; then
    COLOR_RESET=""
    COLOR_DEBUG=""
    COLOR_INFO=""
    COLOR_SUCCESS=""
    COLOR_WARN=""
    COLOR_ERROR=""
    COLOR_FATAL=""
else
    COLOR_RESET="\033[0m"
    COLOR_DEBUG="\033[0;36m"
    COLOR_INFO="\033[0;34m"
    COLOR_SUCCESS="\033[0;32m"
    COLOR_WARN="\033[0;33m"
    COLOR_ERROR="\033[0;31m"
    COLOR_FATAL="\033[1;31m"
fi

# =============================================================================
# LOG FILE
# =============================================================================
LOG_FILE="${LOG_FILE:-}"
LOG_TO_FILE=${LOG_TO_FILE:-false}

set_log_file() {
    local file=$1
    LOG_FILE="$file"
    LOG_TO_FILE=true
    mkdir -p "$(dirname "$file")"
}

init_log() {
    local script_name=$1
    # Adapted: use PROJECT_ROOT/scripts/logs instead of /vagrant/logs
    local log_dir="${2:-${PROJECT_ROOT}/scripts/logs}"
    set_log_file "${log_dir}/${script_name}.log"
    {
        echo "=================================================================="
        echo "Log iniciado: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "Script: ${script_name}"
        echo "Host: $(hostname)"
        echo "User: $(whoami)"
        echo "=================================================================="
        echo ""
    } >> "$LOG_FILE"
}

# =============================================================================
# CORE LOGGING
# =============================================================================
log_message() {
    local level=$1
    local prefix=$2
    local color=$3
    local message=$4

    [[ $level -lt $CURRENT_LOG_LEVEL ]] && return 0

    local timestamp
    timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    local formatted="${timestamp} [${prefix}] ${message}"

    if [[ -n "$color" ]]; then
        echo -e "${color}${formatted}${COLOR_RESET}"
    else
        echo "$formatted"
    fi

    if [[ "$LOG_TO_FILE" == "true" ]] && [[ -n "$LOG_FILE" ]]; then
        echo "$formatted" >> "$LOG_FILE"
    fi
}

log_debug()   { log_message "$LOG_LEVEL_DEBUG"   "DEBUG  " "$COLOR_DEBUG"   "$1"; }
log_info()    { log_message "$LOG_LEVEL_INFO"    "INFO   " "$COLOR_INFO"    "$1"; }
log_success() { log_message "$LOG_LEVEL_SUCCESS" "SUCCESS" "$COLOR_SUCCESS" "$1"; }
log_warn()    { log_message "$LOG_LEVEL_WARN"    "WARN   " "$COLOR_WARN"    "$1"; }
log_error()   { log_message "$LOG_LEVEL_ERROR"   "ERROR  " "$COLOR_ERROR"   "$1"; }
log_fatal()   { log_message "$LOG_LEVEL_FATAL"   "FATAL  " "$COLOR_FATAL"   "$1"; }

log_step() {
    local current=$1 total=$2 message=$3
    local timestamp; timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    local formatted="${timestamp} [STEP ${current}/${total}] ${message}"
    echo -e "${COLOR_INFO}${formatted}${COLOR_RESET}"
    if [[ "$LOG_TO_FILE" == "true" ]] && [[ -n "$LOG_FILE" ]]; then
        echo "$formatted" >> "$LOG_FILE"
    fi
}

log_header() {
    local message=$1
    local width=${2:-60}
    local line; line=$(printf '=%.0s' $(seq 1 "$width"))
    echo ""
    echo -e "${COLOR_INFO}${line}${COLOR_RESET}"
    echo -e "${COLOR_INFO}  ${message}${COLOR_RESET}"
    echo -e "${COLOR_INFO}${line}${COLOR_RESET}"
    echo ""
    if [[ "$LOG_TO_FILE" == "true" ]] && [[ -n "$LOG_FILE" ]]; then
        { echo ""; echo "$line"; echo "  $message"; echo "$line"; echo ""; } >> "$LOG_FILE"
    fi
}

log_separator() {
    local width=${1:-60} char=${2:--}
    local line; line=$(printf -- "${char}%.0s" $(seq 1 "$width"))
    echo "$line"
    if [[ "$LOG_TO_FILE" == "true" ]] && [[ -n "$LOG_FILE" ]]; then
        echo "$line" >> "$LOG_FILE"
    fi
}

log_command() {
    local cmd=("$@")
    log_debug "Executing: ${cmd[*]}"
    local output exit_code=0
    output=$("${cmd[@]}" 2>&1) || exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        log_error "Command failed (exit ${exit_code}): ${output}"
    fi
    return $exit_code
}

show_progress() {
    local current=$1 total=$2 width=${3:-50}
    local percent=$((current * 100 / total))
    local filled=$((current * width / total))
    local empty=$((width - filled))
    local bar; bar=$(printf "#%.0s" $(seq 1 "$filled"))
    bar+=$(printf -- "-%.0s" $(seq 1 "$empty"))
    printf "\r[%s] %3d%%" "$bar" "$percent"
    [[ $current -eq $total ]] && echo ""
}

declare -g START_TIME
start_timer() { START_TIME=$(date +%s); }
show_elapsed() {
    local elapsed=$(( $(date +%s) - START_TIME ))
    local m=$((elapsed / 60)) s=$((elapsed % 60))
    [[ $m -gt 0 ]] && echo "${m}m ${s}s" || echo "${s}s"
}

# =============================================================================
# EXPORTS
# =============================================================================
export PROJECT_ROOT
export -f log_message
export -f log_debug log_info log_success log_warn log_error log_fatal
export -f log_step log_header log_separator log_command
export -f show_progress start_timer show_elapsed
export -f set_log_file init_log
