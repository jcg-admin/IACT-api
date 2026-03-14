#!/bin/bash
# IACT API - MariaDB Database Setup
# Version: 0.1.1
# Adapted from IACT DevBox:
#   - /vagrant/ paths → PROJECT_ROOT/scripts/
#   - systemctl → service command
#   - Note: main() called by bootstrap.sh, not auto-executed
set -euo pipefail

PROVISIONER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${PROVISIONER_DIR}/../../.." && pwd)"
export PROJECT_ROOT

source "${PROJECT_ROOT}/scripts/utils/core.sh"
source "${PROJECT_ROOT}/scripts/utils/logging.sh"
source "${PROJECT_ROOT}/scripts/utils/database.sh"
source "${PROJECT_ROOT}/scripts/utils/validation.sh"

# =============================================================================
# MAIN
# =============================================================================
main() {
    log_header "MariaDB Database Setup"

    validate_root || { log_fatal "Must be run as root"; return 1; }
    require_vars DB_NAME DB_CHARSET DB_COLLATION DB_USER DB_PASSWORD DB_ROOT_PASSWORD

    ensure_dir "${PROJECT_ROOT}/scripts/logs" || return 1

    verify_mariadb_running   || { log_error "MariaDB is not running"; return 1; }
    create_database          || { log_error "Failed to create database"; return 1; }
    create_database_user     || { log_error "Failed to create user"; return 1; }
    grant_user_privileges    || { log_error "Failed to grant privileges"; return 1; }
    create_schema_version    || { log_error "Failed to create schema_version table"; return 1; }

    log_success "MariaDB database setup completed"
}

# =============================================================================
# VERIFY RUNNING
# =============================================================================
verify_mariadb_running() {
    log_info "Verifying MariaDB is running"
    is_service_active "mariadb" || {
        log_error "MariaDB service is not active"
        return 1
    }
    mysql_wait_ready 30 || return 1
    log_success "MariaDB is running and ready"
}

# =============================================================================
# CREATE DATABASE
# =============================================================================
create_database() {
    log_info "Creating database: ${DB_NAME}"
    if mysql_database_exists "${DB_NAME}" "root" "${DB_ROOT_PASSWORD}"; then
        log_warn "Database ${DB_NAME} already exists — skipping"
        return 0
    fi
    mysql_create_database "${DB_NAME}" "${DB_CHARSET}" "${DB_COLLATION}" \
        "root" "${DB_ROOT_PASSWORD}" || return 1
    log_success "Database ${DB_NAME} created"
}

# =============================================================================
# CREATE USER
# =============================================================================
create_database_user() {
    log_info "Creating user: ${DB_USER}"
    local user_exists
    user_exists=$(mysql -u root -p"${DB_ROOT_PASSWORD}" \
        -sse "SELECT COUNT(*) FROM mysql.user WHERE User='${DB_USER}' AND Host='%';" \
        2>/dev/null || echo "0")

    if [[ "$user_exists" -gt 0 ]]; then
        log_warn "User ${DB_USER} already exists — skipping"
        return 0
    fi
    mysql_create_user "${DB_USER}" "${DB_PASSWORD}" "%" "root" "${DB_ROOT_PASSWORD}" || return 1
    log_success "User ${DB_USER} created"
}

# =============================================================================
# GRANT PRIVILEGES
# =============================================================================
grant_user_privileges() {
    log_info "Granting privileges: ${DB_USER} on ${DB_NAME}"
    mysql_grant_privileges "${DB_NAME}" "${DB_USER}" "%" "root" "${DB_ROOT_PASSWORD}" || return 1
    mysql -u root -p"${DB_ROOT_PASSWORD}" -e "FLUSH PRIVILEGES;" 2>/dev/null || {
        log_error "Failed to flush privileges"
        return 1
    }
    log_success "Privileges granted"
}

# =============================================================================
# SCHEMA VERSION TABLE
# =============================================================================
create_schema_version() {
    log_info "Creating schema_version table"
    local sql="
    CREATE TABLE IF NOT EXISTS schema_version (
        id           INT AUTO_INCREMENT PRIMARY KEY,
        version      VARCHAR(50)  NOT NULL,
        description  VARCHAR(255),
        applied_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_version (version)
    ) ENGINE=InnoDB DEFAULT CHARSET=${DB_CHARSET} COLLATE=${DB_COLLATION};
    "
    mysql -u root -p"${DB_ROOT_PASSWORD}" "${DB_NAME}" -e "${sql}" 2>/dev/null || {
        log_error "Failed to create schema_version table"
        return 1
    }

    local insert_sql="
    INSERT INTO schema_version (version, description)
    VALUES ('1.0.0', 'Initial database schema')
    ON DUPLICATE KEY UPDATE version=version;
    "
    mysql -u root -p"${DB_ROOT_PASSWORD}" "${DB_NAME}" \
        -e "${insert_sql}" 2>/dev/null || \
        log_warn "Initial version record may already exist"

    log_success "schema_version table ready"
}
