#!/bin/bash
# IACT API - Provisioning Framework
# Version: 0.1.4
# Adapted from IACT DevBox:
#   - /vagrant/ detection removed; uses git root or script-relative PROJECT_ROOT
#   - vars.conf dependency removed (v0.1.3+); config from env vars or config/
#   - Idempotency markers moved to scripts/.iact/ (was /var/lib/iact-devbox/)
#   - load_utils path: scripts/utils/ (was utils/)
set -euo pipefail

# =============================================================================
# ENVIRONMENT INITIALIZATION
# =============================================================================
init_env() {
    [[ -n "${PROJECT_ROOT:-}" ]] && return 0

    # Try git root first
    local git_root
    git_root=$(git rev-parse --show-toplevel 2>/dev/null || echo "")
    if [[ -n "$git_root" ]]; then
        export PROJECT_ROOT="$git_root"
        return 0
    fi

    # Fallback: resolve from this file's location (scripts/utils/ → project root)
    export PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
}

load_utils() {
    init_env
    # Adapted: scripts/utils/ instead of /vagrant/utils/
    local utils_dir="${PROJECT_ROOT}/scripts/utils"

    if [[ ! -d "$utils_dir" ]]; then
        echo "[ERROR] Utils directory not found: ${utils_dir}"
        return 1
    fi

    # Source in dependency order
    # shellcheck disable=SC1090
    source "${utils_dir}/core.sh"
    # shellcheck disable=SC1090
    source "${utils_dir}/logging.sh"
    # shellcheck disable=SC1090
    source "${utils_dir}/network.sh"
    # shellcheck disable=SC1090
    source "${utils_dir}/database.sh"
    # shellcheck disable=SC1090
    source "${utils_dir}/validation.sh"

    export UTILS_LOADED=true
}

init_all() {
    init_env
    load_utils
}

# =============================================================================
# VALIDATION HELPERS
# =============================================================================
validate() {
    validate_var "$@"
}

# =============================================================================
# STEP EXECUTION
# =============================================================================
run_step() {
    local step_name=$1
    local step_func=$2
    log_info "Running step: ${step_name}"
    if "$step_func"; then
        log_success "Step completed: ${step_name}"
        return 0
    else
        log_error "Step failed: ${step_name}"
        return 1
    fi
}

run_all() {
    local -a steps=("$@")
    local failed=0
    local total=${#steps[@]}
    local current=0

    for step in "${steps[@]}"; do
        current=$((current + 1))
        log_step "$current" "$total" "Executing: ${step}"
        if ! "$step"; then
            log_error "Failed: ${step}"
            failed=$((failed + 1))
        fi
    done

    if [[ $failed -eq 0 ]]; then
        log_success "All steps completed successfully"
        return 0
    else
        log_error "Failed steps: ${failed}/${total}"
        return 1
    fi
}

# =============================================================================
# STANDARD PROVISIONING STEPS
# =============================================================================
step_header() {
    local vm_name=$1
    local vm_description=${2:-""}
    log_header "PROVISIONING: ${vm_name}"
    if [[ -n "$vm_description" ]]; then
        echo "$vm_description"
        echo ""
    fi
    echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "Host:      $(hostname)"
    echo "User:      $(whoami)"
    echo ""
    log_separator
}

step_system() {
    # Adapted: scripts/utils/system.sh instead of /vagrant/utils/system.sh
    local system_script="${PROJECT_ROOT}/scripts/utils/system.sh"
    if [[ ! -f "$system_script" ]]; then
        log_error "System script not found: ${system_script}"
        return 1
    fi
    log_info "Running system preparation"
    bash "$system_script" || {
        log_error "System preparation failed"
        return 1
    }
    log_success "System preparation completed"
}

step_install() {
    local install_script=${1:-}
    if [[ -z "$install_script" ]]; then
        log_error "Install script path required"
        return 1
    fi
    if [[ ! -f "$install_script" ]]; then
        log_error "Install script not found: ${install_script}"
        return 1
    fi
    log_info "Running installation: ${install_script}"
    bash "$install_script" || {
        log_error "Installation failed: ${install_script}"
        return 1
    }
    log_success "Installation completed"
}

step_setup() {
    local setup_script=${1:-}
    if [[ -z "$setup_script" ]]; then
        log_error "Setup script path required"
        return 1
    fi
    if [[ ! -f "$setup_script" ]]; then
        log_error "Setup script not found: ${setup_script}"
        return 1
    fi
    log_info "Running setup: ${setup_script}"
    bash "$setup_script" || {
        log_error "Setup failed: ${setup_script}"
        return 1
    }
    log_success "Setup completed"
}

# =============================================================================
# RESULTS DISPLAY
# =============================================================================
show_results() {
    local vm_name=$1
    shift
    local -a info=("$@")
    log_header "PROVISIONING COMPLETE: ${vm_name}"
    for line in "${info[@]}"; do
        echo "$line"
    done
    echo ""
    log_separator
}

show_connection_info() {
    local service=$1
    local host=$2
    local port=$3
    local database=${4:-}
    local username=${5:-}
    log_header "CONNECTION INFORMATION"
    echo "Service:  ${service}"
    echo "Host:     ${host}"
    echo "Port:     ${port}"
    [[ -n "$database" ]] && echo "Database: ${database}"
    [[ -n "$username" ]] && echo "Username: ${username}"
    echo ""
    log_separator
}

# =============================================================================
# ERROR HANDLING
# =============================================================================
handle_error() {
    local exit_code=$1
    local message=${2:-"An error occurred"}
    log_error "$message"
    log_error "Exit code: ${exit_code}"
    return "$exit_code"
}

ensure_success() {
    local cmd=("$@")
    if ! "${cmd[@]}"; then
        local exit_code=$?
        handle_error "$exit_code" "Command failed: ${cmd[*]}"
        return "$exit_code"
    fi
}

# =============================================================================
# IDEMPOTENCY HELPERS
# Adapted: marker files in scripts/.iact/ (was /var/lib/iact-devbox/)
# =============================================================================
_iact_marker_dir() {
    echo "${PROJECT_ROOT}/scripts/.iact"
}

needs_install() {
    local service=$1
    local required_version=${2:-}
    command_exists "$service" || return 0   # needs install
    [[ -z "$required_version" ]] && return 1  # already installed
    return 1
}

mark_installed() {
    local service=$1
    local version=$2
    local marker_dir; marker_dir=$(_iact_marker_dir)
    mkdir -p "$marker_dir"
    echo "$version" > "${marker_dir}/${service}.installed"
}

is_installed() {
    local service=$1
    local marker_dir; marker_dir=$(_iact_marker_dir)
    [[ -f "${marker_dir}/${service}.installed" ]]
}

get_installed_version() {
    local service=$1
    local marker_dir; marker_dir=$(_iact_marker_dir)
    local marker="${marker_dir}/${service}.installed"
    [[ -f "$marker" ]] && cat "$marker"
}

# =============================================================================
# EXPORTS
# =============================================================================
export -f init_env load_utils init_all
export -f validate
export -f run_step run_all
export -f step_header step_system step_install step_setup
export -f show_results show_connection_info
export -f handle_error ensure_success
export -f needs_install mark_installed is_installed get_installed_version
