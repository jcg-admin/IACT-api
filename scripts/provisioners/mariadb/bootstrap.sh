#!/bin/bash
# IACT API - MariaDB Bootstrap
# Version: 0.1.1
# Adapted from IACT DevBox bootstrap.sh:
#   - /vagrant/ paths → PROJECT_ROOT/scripts/
#   - Variables from environment or config/db.conf (not Vagrantfile)
#
# Usage:
#   MARIADB_VERSION=11.4 DB_NAME=ivr_legacy ... bash scripts/provisioners/mariadb/bootstrap.sh
#   Or: source scripts/config/db.conf && bash scripts/provisioners/mariadb/bootstrap.sh
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

# Load config file if present (optional override)
CONFIG_FILE="${PROJECT_ROOT}/scripts/config/mariadb.conf"
if [[ -f "$CONFIG_FILE" ]]; then
    # shellcheck disable=SC1090
    source "$CONFIG_FILE"
fi

init_log "mariadb_bootstrap"

# =============================================================================
# PROVISIONING STEPS
# =============================================================================
mariadb_system() {
    init_log "mariadb_system"
    step_system
}

mariadb_install() {
    init_log "mariadb_install"
    source "${PROVISIONER_DIR}/install.sh"
    main
}

mariadb_setup() {
    init_log "mariadb_setup"
    source "${PROVISIONER_DIR}/setup.sh"
    main
}

# =============================================================================
# MAIN
# =============================================================================
# Validate required variables
require_vars MARIADB_VERSION DB_NAME DB_CHARSET DB_COLLATION \
             DB_USER DB_PASSWORD DB_ROOT_PASSWORD \
             MARIADB_HOST MARIADB_PORT

step_header "MariaDB" "MariaDB ${MARIADB_VERSION} Database Server"

steps=(
    "mariadb_system"
    "mariadb_install"
    "mariadb_setup"
)

if ! run_all "${steps[@]}"; then
    log_error "MariaDB provisioning failed"
    exit 1
fi

show_results "MariaDB ${MARIADB_VERSION}" \
    "IP:       ${MARIADB_HOST}" \
    "Port:     ${MARIADB_PORT}" \
    "Database: ${DB_NAME}" \
    "Charset:  ${DB_CHARSET}" \
    "Status:   Running"

show_connection_info \
    "MariaDB" \
    "${MARIADB_HOST}" \
    "${MARIADB_PORT}" \
    "${DB_NAME}" \
    "${DB_USER}"

log_success "MariaDB provisioning completed successfully"
