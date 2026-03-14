#!/bin/bash
# IACT API - PostgreSQL Database Setup
# Version: 0.1.0
# Adapted: no sudo -u postgres, using psql -U postgres directly (run as root)
# Note: main() called by bootstrap.sh, not auto-executed
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
    log_header "PostgreSQL Database Setup"

    validate_root || { log_fatal "Must be run as root"; return 1; }
    require_vars DB_NAME DB_USER DB_PASSWORD POSTGRES_PASSWORD

    ensure_dir "${PROJECT_ROOT}/scripts/logs" || return 1

    export POSTGRES_HOST="${POSTGRES_HOST:-127.0.0.1}"
    export POSTGRES_PORT="${POSTGRES_PORT:-5432}"
    export POSTGRES_USER="postgres"
    export POSTGRES_PASSWORD

    verify_postgres_running  || { log_error "PostgreSQL is not running"; return 1; }
    create_pg_user           || { log_error "Failed to create user"; return 1; }
    create_pg_database       || { log_error "Failed to create database"; return 1; }
    grant_pg_privileges      || { log_error "Failed to grant privileges"; return 1; }
    create_schema_version    || { log_error "Failed to create schema_version"; return 1; }

    log_success "PostgreSQL database setup completed"
}

# =============================================================================
# VERIFY RUNNING
# =============================================================================
verify_postgres_running() {
    log_info "Verifying PostgreSQL is running"
    is_service_active "postgresql" || {
        log_error "PostgreSQL service is not active"
        return 1
    }
    postgres_wait_ready 30 || return 1
    log_success "PostgreSQL is running and ready"
}

# =============================================================================
# CREATE USER
# =============================================================================
create_pg_user() {
    log_info "Creating user: ${DB_USER}"
    if postgres_user_exists "$DB_USER"; then
        log_warn "User ${DB_USER} already exists — skipping"
        return 0
    fi
    postgres_create_user "$DB_USER" "$DB_PASSWORD" || return 1
    log_success "User ${DB_USER} created"
}

# =============================================================================
# CREATE DATABASE
# =============================================================================
create_pg_database() {
    log_info "Creating database: ${DB_NAME}"
    if postgres_database_exists "$DB_NAME"; then
        log_warn "Database ${DB_NAME} already exists — skipping"
        return 0
    fi
    postgres_create_database "$DB_NAME" "$DB_USER" "UTF8" || return 1
    log_success "Database ${DB_NAME} created"
}

# =============================================================================
# GRANT PRIVILEGES
# =============================================================================
grant_pg_privileges() {
    log_info "Granting privileges: ${DB_USER} on ${DB_NAME}"
    postgres_grant_privileges "$DB_NAME" "$DB_USER" || return 1

    # Grant schema privileges
    PGPASSWORD="$POSTGRES_PASSWORD" \
    psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U postgres -d "$DB_NAME" <<SQL 2>/dev/null
GRANT ALL ON SCHEMA public TO ${DB_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES    TO ${DB_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ${DB_USER};
SQL

    log_success "Privileges granted"
}

# =============================================================================
# SCHEMA VERSION TABLE
# =============================================================================
create_schema_version() {
    log_info "Creating schema_version table"
    PGPASSWORD="$DB_PASSWORD" \
    psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$DB_USER" -d "$DB_NAME" <<SQL 2>/dev/null
CREATE TABLE IF NOT EXISTS schema_version (
    id          SERIAL PRIMARY KEY,
    version     VARCHAR(50)  NOT NULL,
    description VARCHAR(255),
    applied_at  TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_schema_version ON schema_version(version);
INSERT INTO schema_version (version, description)
VALUES ('1.0.0', 'Initial database schema')
ON CONFLICT DO NOTHING;
SQL

    log_success "schema_version table ready"
}
