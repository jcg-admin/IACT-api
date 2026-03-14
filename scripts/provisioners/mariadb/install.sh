#!/bin/bash
# IACT API - MariaDB Installation
# Version: 0.1.1
# Adapted from IACT DevBox:
#   - /vagrant/ paths → PROJECT_ROOT/scripts/
#   - systemctl → service command (no systemd required)
#   - Note: main() called by bootstrap.sh, not auto-executed
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
    log_header "MariaDB Installation"

    validate_root || { log_fatal "Must be run as root"; return 1; }
    require_vars MARIADB_VERSION DB_ROOT_PASSWORD

    ensure_dir "${PROJECT_ROOT}/scripts/logs" || return 1

    add_mariadb_repository  || { log_error "Failed to add repository"; return 1; }
    install_mariadb          || { log_error "Failed to install MariaDB"; return 1; }
    configure_mariadb        || { log_error "Failed to configure MariaDB"; return 1; }
    secure_mariadb           || { log_error "Failed to secure MariaDB"; return 1; }

    log_success "MariaDB installation completed"
}

# =============================================================================
# ADD REPOSITORY
# =============================================================================
add_mariadb_repository() {
    log_info "Adding MariaDB ${MARIADB_VERSION} repository"

    install_package software-properties-common || return 1
    install_package dirmngr                    || return 1
    install_package apt-transport-https        || return 1

    log_info "Importing MariaDB GPG key"
    curl -fsSL https://mariadb.org/mariadb_release_signing_key.asc \
        | apt-key add - 2>/dev/null || {
        log_error "Failed to import GPG key"
        return 1
    }

    local repo_file="/etc/apt/sources.list.d/mariadb.list"
    local codename; codename=$(get_os_codename)
    cat > "$repo_file" <<EOF
# MariaDB ${MARIADB_VERSION} repository
deb [arch=amd64] http://mirror.mariadb.org/repo/${MARIADB_VERSION}/ubuntu ${codename} main
EOF

    apt-get update -qq || { log_error "Failed to update package index"; return 1; }
    log_success "MariaDB repository added"
}

# =============================================================================
# INSTALL
# =============================================================================
install_mariadb() {
    log_info "Installing MariaDB ${MARIADB_VERSION}"
    export DEBIAN_FRONTEND=noninteractive

    debconf-set-selections <<< "mariadb-server mysql-server/root_password password ${DB_ROOT_PASSWORD}"
    debconf-set-selections <<< "mariadb-server mysql-server/root_password_again password ${DB_ROOT_PASSWORD}"

    install_package mariadb-server || { log_error "Failed to install mariadb-server"; return 1; }
    install_package mariadb-client || { log_error "Failed to install mariadb-client"; return 1; }

    enable_service mariadb || log_warn "Could not enable mariadb service (no systemd)"
    start_service  mariadb || { log_error "Failed to start MariaDB"; return 1; }

    mysql_wait_ready 30 || { log_error "MariaDB did not start in time"; return 1; }
    log_success "MariaDB installed and started"
}

# =============================================================================
# CONFIGURE
# =============================================================================
configure_mariadb() {
    log_info "Configuring MariaDB for remote access"
    local config_file="/etc/mysql/mariadb.conf.d/50-server.cnf"

    validate_file_exists "$config_file" || return 1
    backup_file "$config_file"          || return 1

    if grep -q "^bind-address" "$config_file"; then
        sed -i 's/^bind-address.*/bind-address = 0.0.0.0/' "$config_file"
    else
        sed -i '/^\[mysqld\]/a bind-address = 0.0.0.0' "$config_file"
    fi

    grep -q "bind-address = 0.0.0.0" "$config_file" || {
        log_error "Failed to set bind-address"
        return 1
    }

    restart_service mariadb || { log_error "Failed to restart MariaDB"; return 1; }
    mysql_wait_ready 30     || { log_error "MariaDB did not restart in time"; return 1; }
    log_success "MariaDB configured for remote access"
}

# =============================================================================
# SECURE
# =============================================================================
secure_mariadb() {
    log_info "Securing MariaDB installation"

    mysql -u root -p"${DB_ROOT_PASSWORD}" \
        -e "DELETE FROM mysql.user WHERE User='';" 2>/dev/null || true

    mysql -u root -p"${DB_ROOT_PASSWORD}" \
        -e "DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');" \
        2>/dev/null || true

    mysql -u root -p"${DB_ROOT_PASSWORD}" \
        -e "DROP DATABASE IF EXISTS test;" 2>/dev/null || true

    mysql -u root -p"${DB_ROOT_PASSWORD}" \
        -e "DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';" 2>/dev/null || true

    mysql -u root -p"${DB_ROOT_PASSWORD}" \
        -e "FLUSH PRIVILEGES;" 2>/dev/null || {
        log_error "Failed to flush privileges"
        return 1
    }

    log_success "MariaDB installation secured"
}
