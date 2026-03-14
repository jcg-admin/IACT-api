#!/bin/bash
# IACT API - System Preparation
# Version: 0.1.1
# Adapted from IACT DevBox:
#   - /vagrant/ paths removed; uses PROJECT_ROOT
#   - timedatectl fallback works without systemd
#   - Can run standalone (main) or sourced by provisioners
set -euo pipefail

# =============================================================================
# INITIALIZATION
# =============================================================================
UTILS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${UTILS_DIR}/../.." && pwd)"
export PROJECT_ROOT

# shellcheck disable=SC1091
source "${UTILS_DIR}/core.sh"
# shellcheck disable=SC1091
source "${UTILS_DIR}/logging.sh"

# =============================================================================
# SYSTEM UPDATE
# =============================================================================
update_system() {
    log_info "Updating package lists"
    export DEBIAN_FRONTEND=noninteractive

    local apt_opts=(
        -o Acquire::http::Timeout=300
        -o Acquire::https::Timeout=300
        -o Acquire::Retries=3
    )

    retry 3 apt-get update "${apt_opts[@]}" -qq || {
        log_error "Failed to update package lists"
        return 1
    }
    log_success "Package lists updated"
}

# Available but not called by default — use manually if needed
upgrade_system() {
    log_info "Upgrading system packages"
    export DEBIAN_FRONTEND=noninteractive
    apt-get upgrade -y -qq || {
        log_error "Failed to upgrade packages"
        return 1
    }
    log_success "System packages upgraded"
}

# =============================================================================
# ESSENTIAL PACKAGES
# =============================================================================
install_essentials() {
    log_info "Installing essential packages"

    local packages=(
        curl
        wget
        git
        vim
        nano
        htop
        net-tools
        iproute2
        dnsutils
        iputils-ping
        ca-certificates
        gnupg
        lsb-release
        software-properties-common
        apt-transport-https
    )

    export DEBIAN_FRONTEND=noninteractive
    for package in "${packages[@]}"; do
        if ! is_package_installed "$package"; then
            log_info "Installing: ${package}"
            apt-get install -y -qq "$package" 2>/dev/null || \
                log_warn "Failed to install: ${package}"
        fi
    done

    log_success "Essential packages installed"
}

# =============================================================================
# TIMEZONE CONFIGURATION
# Adapted: fallback when timedatectl not available (no systemd)
# =============================================================================
configure_timezone() {
    local timezone=${1:-UTC}
    log_info "Configuring timezone: ${timezone}"

    if [[ -f /etc/timezone ]] && [[ "$(cat /etc/timezone)" == "$timezone" ]]; then
        log_info "Timezone already set to: ${timezone}"
        return 0
    fi

    # Try timedatectl first (works with systemd), fall back to manual
    if timedatectl set-timezone "$timezone" 2>/dev/null; then
        log_success "Timezone configured via timedatectl: ${timezone}"
    else
        echo "$timezone" > /etc/timezone
        ln -sf "/usr/share/zoneinfo/${timezone}" /etc/localtime 2>/dev/null || true
        log_success "Timezone configured manually: ${timezone}"
    fi
}

# =============================================================================
# LOCALE CONFIGURATION
# =============================================================================
configure_locale() {
    local locale=${1:-en_US.UTF-8}
    log_info "Configuring locale: ${locale}"

    is_package_installed "locales" || apt-get install -y -qq locales 2>/dev/null

    locale-gen "$locale" 2>/dev/null || true

    update-locale LANG="$locale" 2>/dev/null || {
        echo "LANG=${locale}" > /etc/default/locale
    }

    log_success "Locale configured: ${locale}"
}

# =============================================================================
# CLEANUP
# =============================================================================
cleanup_system() {
    log_info "Cleaning up system"
    apt-get autoremove -y -qq 2>/dev/null || true
    apt-get autoclean  -y -qq 2>/dev/null || true
    apt-get clean      -y -qq 2>/dev/null || true
    log_success "System cleaned up"
}

# =============================================================================
# MAIN
# =============================================================================
main() {
    log_header "SYSTEM PREPARATION"
    start_timer

    validate_root || {
        log_fatal "This script must be run as root"
        return 1
    }

    local steps=(
        update_system
        install_essentials
        configure_timezone
        configure_locale
        cleanup_system
    )

    # Use run_all if provisioning.sh is loaded, otherwise loop manually
    if declare -f run_all &>/dev/null; then
        run_all "${steps[@]}" || {
            log_error "System preparation failed"
            return 1
        }
    else
        for step in "${steps[@]}"; do
            "$step" || { log_error "Step failed: ${step}"; return 1; }
        done
    fi

    log_success "System preparation completed in $(show_elapsed)"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
