#!/bin/bash
# IACT API - Core Utilities
# Version: 0.1.1
# Adapted from IACT DevBox:
#   - systemctl replaced with 'service' command (no systemd required)
#   - /vagrant/ paths replaced with PROJECT_ROOT
set -euo pipefail

# =============================================================================
# FILE SYSTEM OPERATIONS
# =============================================================================
exists_dir()    { [[ -d "$1" ]]; }
exists_file()   { [[ -f "$1" ]]; }
is_executable() { [[ -x "$1" ]]; }
is_readable()   { [[ -r "$1" ]]; }
is_writable()   { [[ -w "$1" ]]; }

# =============================================================================
# DIRECTORY MANAGEMENT
# =============================================================================
ensure_dir() {
    local dir=$1
    [[ -d "$dir" ]] && return 0
    mkdir -p "$dir" || return 1
}

remove_dir() {
    local dir=$1
    [[ ! -d "$dir" ]] && return 0
    rm -rf "$dir" || return 1
}

# =============================================================================
# FILE MANAGEMENT
# =============================================================================
ensure_file() {
    local file=$1
    [[ -f "$file" ]] && return 0
    touch "$file" || return 1
}

remove_file() {
    local file=$1
    [[ ! -f "$file" ]] && return 0
    rm -f "$file" || return 1
}

backup_file() {
    local file=$1
    [[ ! -f "$file" ]] && return 1
    local backup="${file}.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$file" "$backup" || return 1
}

# =============================================================================
# PERMISSIONS
# =============================================================================
make_exec()     { [[ -x "$1" ]] && return 0; chmod +x "$1" || return 1; }
make_readable() { [[ -r "$1" ]] && return 0; chmod +r "$1" || return 1; }
set_perms()     { chmod "$2" "$1" || return 1; }
set_owner()     { chown "$2" "$1" || return 1; }

# =============================================================================
# PATH OPERATIONS
# =============================================================================
get_abs_path() {
    cd "$(dirname "$1")" && pwd -P
}

get_script_dir() {
    local source="${BASH_SOURCE[0]}"
    while [[ -h "$source" ]]; do
        local dir; dir="$(cd -P "$(dirname "$source")" && pwd)"
        source="$(readlink "$source")"
        [[ $source != /* ]] && source="$dir/$source"
    done
    cd -P "$(dirname "$source")" && pwd
}

# =============================================================================
# STRING OPERATIONS
# =============================================================================
trim()        { echo "$1" | xargs; }
lower()       { echo "$1" | tr '[:upper:]' '[:lower:]'; }
upper()       { echo "$1" | tr '[:lower:]' '[:upper:]'; }
contains()    { [[ "$1" == *"$2"* ]]; }
starts_with() { [[ "$1" == "$2"* ]]; }
ends_with()   { [[ "$1" == *"$2" ]]; }

# =============================================================================
# PROCESS OPERATIONS
# =============================================================================
is_running() {
    pgrep -x "$1" &>/dev/null
}

wait_for_process() {
    local process=$1 timeout=${2:-30} elapsed=0
    while ! is_running "$process"; do
        [[ $elapsed -ge $timeout ]] && return 1
        sleep 1
        ((elapsed++))
    done
    return 0
}

kill_process() {
    local process=$1 signal=${2:-TERM}
    pkill -"$signal" "$process" 2>/dev/null || true
}

# =============================================================================
# SERVICE OPERATIONS
# Adapted: use 'service' command instead of 'systemctl' (no systemd required)
# =============================================================================
is_service_active() {
    local service=$1
    # Try systemctl first, fall back to service command
    if command -v systemctl &>/dev/null && systemctl is-active --quiet "$service" 2>/dev/null; then
        return 0
    fi
    service "$service" status &>/dev/null
}

is_service_enabled() {
    local service=$1
    if command -v systemctl &>/dev/null; then
        systemctl is-enabled --quiet "$service" 2>/dev/null
        return $?
    fi
    # Without systemd, check if init script exists and is linked
    [[ -f "/etc/init.d/$service" ]]
}

start_service() {
    local service=$1
    if command -v systemctl &>/dev/null && pidof systemd &>/dev/null; then
        systemctl start "$service" || return 1
    else
        service "$service" start || return 1
    fi
}

stop_service() {
    local service=$1
    if command -v systemctl &>/dev/null && pidof systemd &>/dev/null; then
        systemctl stop "$service" || return 1
    else
        service "$service" stop || return 1
    fi
}

restart_service() {
    local service=$1
    if command -v systemctl &>/dev/null && pidof systemd &>/dev/null; then
        systemctl restart "$service" || return 1
    else
        service "$service" restart || return 1
    fi
}

enable_service() {
    local service=$1
    if command -v systemctl &>/dev/null && pidof systemd &>/dev/null; then
        systemctl enable "$service" || return 1
    else
        # Without systemd: update-rc.d is the equivalent
        update-rc.d "$service" defaults 2>/dev/null || true
    fi
}

# =============================================================================
# COMMAND AVAILABILITY
# =============================================================================
command_exists() {
    command -v "$1" &>/dev/null
}

require_command() {
    local cmd=$1
    command_exists "$cmd" || {
        echo "[ERROR] Required command not found: ${cmd}"
        return 1
    }
}

# =============================================================================
# VARIABLE VALIDATION
# =============================================================================
require_vars() {
    local missing=0
    for var in "$@"; do
        if [[ -z "${!var:-}" ]]; then
            echo "[ERROR] Required variable not set: ${var}"
            missing=1
        fi
    done
    [[ $missing -eq 0 ]] || return 1
}

# =============================================================================
# PACKAGE OPERATIONS
# =============================================================================
is_package_installed() {
    dpkg -l "$1" 2>/dev/null | grep -q "^ii"
}

install_package() {
    local package=$1
    is_package_installed "$package" && return 0
    apt-get install -y "$package" || return 1
}

remove_package() {
    local package=$1
    is_package_installed "$package" || return 0
    apt-get remove -y "$package" || return 1
}

# =============================================================================
# SYSTEM INFO
# =============================================================================
get_os_version() {
    lsb_release -rs 2>/dev/null || grep VERSION_ID /etc/os-release | cut -d'"' -f2
}

get_os_codename() {
    lsb_release -cs 2>/dev/null || grep VERSION_CODENAME /etc/os-release | cut -d'=' -f2
}

get_cpu_count()     { nproc; }
get_total_memory()  { free -m | awk '/^Mem:/{print $2}'; }

# =============================================================================
# RETRY LOGIC
# =============================================================================
retry() {
    local max_attempts=$1; shift
    local cmd=("$@")
    local attempt=1
    while [[ $attempt -le $max_attempts ]]; do
        if "${cmd[@]}"; then
            return 0
        fi
        echo "[WARN] Command failed (attempt ${attempt}/${max_attempts})"
        ((attempt++))
        [[ $attempt -le $max_attempts ]] && sleep 2
    done
    return 1
}

# =============================================================================
# EXPORTS
# =============================================================================
export -f exists_dir exists_file is_executable is_readable is_writable
export -f ensure_dir remove_dir
export -f ensure_file remove_file backup_file
export -f make_exec make_readable set_perms set_owner
export -f get_abs_path get_script_dir
export -f trim lower upper contains starts_with ends_with
export -f is_running wait_for_process kill_process
export -f is_service_active is_service_enabled
export -f start_service stop_service restart_service enable_service
export -f command_exists require_command require_vars
export -f is_package_installed install_package remove_package
export -f get_os_version get_os_codename get_cpu_count get_total_memory
export -f retry
