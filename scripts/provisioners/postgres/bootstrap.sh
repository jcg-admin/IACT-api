#!/bin/bash
# IACT API - PostgreSQL Bootstrap
# Version: 0.1.0
# Mirrors mariadb/bootstrap.sh structure for PostgreSQL.
#
# Usage:
#   POSTGRES_VERSION=16 DB_NAME=iact_analytics ... bash scripts/provisioners/postgres/bootstrap.sh
#   Or: source scripts/config/postgres.conf && bash scripts/provisioners/postgres/bootstrap.sh
set -euo pipefail

PROVISIONER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${PROVISIONER_DIR}/../../.." && pwd)"
export PROJECT_ROOT

# Load utils
source "${PROJECT_ROOT}/scripts/utils/core.sh"
source "${PROJECT_ROOT}/scripts/utils/logging.sh"
source "${PROJECT_ROOT}/scripts/utils/database.sh"
source "${PROJECT_ROOT}/scripts/utils/network.sh"
source "${PROJECT_ROOT}/scripts/utils/validation.sh"
source "${PROJECT_ROOT}/scripts/utils/provisioning.sh"

# Load config file if present
CONFIG_FILE="${PROJECT_ROOT}/scripts/config/postgres.conf"
if [[ -f "$CONFIG_FILE" ]]; then
    # shellcheck disable=SC1090
    source "$CONFIG_FILE"
fi

init_log "postgres_bootstrap"

# =============================================================================
# PROVISIONING STEPS
# =============================================================================
postgres_system() {
    init_log "postgres_system"
    step_system
}

postgres_install() {
    init_log "postgres_install"
    source "${PROVISIONER_DIR}/install.sh"
    main
}

postgres_setup() {
    init_log "postgres_setup"
    source "${PROVISIONER_DIR}/setup.sh"
    main
}

# =============================================================================
# MAIN
# =============================================================================
require_vars POSTGRES_VERSION DB_NAME DB_USER DB_PASSWORD POSTGRES_PASSWORD \
             POSTGRES_HOST POSTGRES_PORT

step_header "PostgreSQL" "PostgreSQL ${POSTGRES_VERSION} Database Server"

steps=(
    "postgres_system"
    "postgres_install"
    "postgres_setup"
)

if ! run_all "${steps[@]}"; then
    log_error "PostgreSQL provisioning failed"
    exit 1
fi

show_results "PostgreSQL ${POSTGRES_VERSION}" \
    "IP:       ${POSTGRES_HOST}" \
    "Port:     ${POSTGRES_PORT}" \
    "Database: ${DB_NAME}" \
    "Encoding: UTF8" \
    "Status:   Running"

show_connection_info \
    "PostgreSQL" \
    "${POSTGRES_HOST}" \
    "${POSTGRES_PORT}" \
    "${DB_NAME}" \
    "${DB_USER}"

log_success "PostgreSQL provisioning completed successfully"
