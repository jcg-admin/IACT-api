#!/bin/bash
# IACT API - PostgreSQL Installation
# Version: 0.1.0
# Adapted: no systemctl (service command), no sudo -u postgres (run as root)
# Note: main() called by bootstrap.sh, not auto-executed
set -euo pipefail

PROVISIONER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${PROVISIONER_DIR}/../../.." && pwd)"
export PROJECT_ROOT

source "${PROJECT_ROOT}/scripts/utils/core.sh"
source "${PROJECT_ROOT}/scripts/utils/logging.sh"
source "${PROJECT_ROOT}/scripts/utils/database.sh"
source "${PROJECT_ROOT}/scripts/utils/network.sh"
source "${PROJECT_ROOT}/scripts/utils/validation.sh"

# =============================================================================
# MAIN
# =============================================================================
main() {
    log_header "PostgreSQL Installation"

    validate_root || { log_fatal "Must be run as root"; return 1; }
    require_vars POSTGRES_VERSION POSTGRES_PASSWORD

    ensure_dir "${PROJECT_ROOT}/scripts/logs" || return 1

    add_postgres_repository  || { log_error "Failed to add repository"; return 1; }
    install_postgres          || { log_error "Failed to install PostgreSQL"; return 1; }
    configure_postgres        || { log_error "Failed to configure PostgreSQL"; return 1; }

    log_success "PostgreSQL installation completed"
}

# =============================================================================
# ADD REPOSITORY
# =============================================================================
add_postgres_repository() {
    log_info "Adding PostgreSQL ${POSTGRES_VERSION} repository"

    install_package gnupg            || return 1
    install_package apt-transport-https || return 1

    local codename; codename=$(get_os_codename)
    local keyring="/usr/share/keyrings/postgresql-archive-keyring.gpg"

    log_info "Importing PostgreSQL GPG key"
    curl -fsSL "https://www.postgresql.org/media/keys/ACCC4CF8.asc" \
        | gpg --dearmor -o "$keyring" 2>/dev/null || {
        log_error "Failed to import GPG key"
        return 1
    }

    cat > /etc/apt/sources.list.d/pgdg.list <<EOF
# PostgreSQL ${POSTGRES_VERSION} repository
deb [signed-by=${keyring}] https://apt.postgresql.org/pub/repos/apt ${codename}-pgdg main
EOF

    apt-get update -qq || { log_error "Failed to update package index"; return 1; }
    log_success "PostgreSQL repository added"
}

# =============================================================================
# INSTALL
# =============================================================================
install_postgres() {
    log_info "Installing PostgreSQL ${POSTGRES_VERSION}"
    export DEBIAN_FRONTEND=noninteractive

    install_package "postgresql-${POSTGRES_VERSION}" || {
        log_error "Failed to install postgresql-${POSTGRES_VERSION}"
        return 1
    }
    install_package "postgresql-client-${POSTGRES_VERSION}" || {
        log_error "Failed to install postgresql-client-${POSTGRES_VERSION}"
        return 1
    }

    enable_service postgresql || log_warn "Could not enable postgresql service (no systemd)"
    start_service  postgresql || { log_error "Failed to start PostgreSQL"; return 1; }

    postgres_wait_ready 30 || { log_error "PostgreSQL did not start in time"; return 1; }

    # Set postgres user password
    log_info "Setting postgres user password"
    psql -U postgres -c "ALTER USER postgres WITH PASSWORD '${POSTGRES_PASSWORD}';" \
        2>/dev/null || {
        log_error "Failed to set postgres password"
        return 1
    }

    log_success "PostgreSQL installed and started"
}

# =============================================================================
# CONFIGURE FOR REMOTE ACCESS
# =============================================================================
configure_postgres() {
    log_info "Configuring PostgreSQL for remote access"

    local pg_conf pg_hba
    pg_conf=$(find /etc/postgresql -name "postgresql.conf" 2>/dev/null | head -1)
    pg_hba=$(find  /etc/postgresql -name "pg_hba.conf"     2>/dev/null | head -1)

    if [[ -z "$pg_conf" ]] || [[ -z "$pg_hba" ]]; then
        log_error "PostgreSQL config files not found"
        return 1
    fi

    backup_file "$pg_conf" || return 1
    backup_file "$pg_hba"  || return 1

    # Allow listening on all interfaces
    sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" "$pg_conf"
    # Ensure listen_addresses is set (in case line was not commented)
    grep -q "^listen_addresses" "$pg_conf" || \
        echo "listen_addresses = '*'" >> "$pg_conf"

    # Allow md5 auth from Vagrant network range
    local ip_range="${POSTGRES_ALLOW_CIDR:-192.168.56.0/24}"
    echo "host    all    all    ${ip_range}    md5" >> "$pg_hba"

    restart_service postgresql || { log_error "Failed to restart PostgreSQL"; return 1; }
    postgres_wait_ready 30     || { log_error "PostgreSQL did not restart in time"; return 1; }

    log_success "PostgreSQL configured for remote access"
}
