#!/bin/bash
# IACT API - Database Utilities
# Version: 0.1.1
# Adapted from IACT DevBox:
#   - Service checks use TCP port probe (no local DB required)
#   - postgres functions use direct psql (no 'sudo -u postgres' needed as root)
#   - mysql functions use mysqladmin/mysql directly (mariadb-client required)
set -euo pipefail

UTILS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${UTILS_DIR}/logging.sh"
# shellcheck disable=SC1091
source "${UTILS_DIR}/core.sh"

# =============================================================================
# TCP CONNECTIVITY CHECK
# Adapted: primary check — works without local DB service running
# Checks if a host:port is reachable (e.g., Vagrant VM or remote host)
# =============================================================================
tcp_is_reachable() {
    local host=$1
    local port=$2
    local timeout=${3:-3}
    # Use 'timeout' + bash /dev/tcp — respects the timeout without blocking
    timeout "$timeout" bash -c "exec 3<>/dev/tcp/${host}/${port}" 2>/dev/null && return 0 || return 1
}

wait_for_tcp() {
    local host=$1
    local port=$2
    local timeout=${3:-30}
    local elapsed=0
    log_info "Waiting for ${host}:${port} to be reachable..."
    while ! tcp_is_reachable "$host" "$port"; do
        [[ $elapsed -ge $timeout ]] && {
            log_error "${host}:${port} not reachable after ${timeout}s"
            return 1
        }
        sleep 1
        elapsed=$((elapsed + 1))
    done
    log_success "${host}:${port} is reachable"
}

# =============================================================================
# MARIADB/MYSQL OPERATIONS
# Adapted: service check via TCP; no systemctl dependency
# =============================================================================
mysql_is_running() {
    # Check local process first, then TCP
    is_running "mariadbd" || is_running "mysqld" || \
    tcp_is_reachable "${MARIADB_HOST:-127.0.0.1}" "${MARIADB_PORT:-3306}"
}

mysql_wait_ready() {
    local timeout=${1:-30}
    local elapsed=0
    log_info "Waiting for MySQL/MariaDB to be ready..."
    # Adapted: use mysqladmin ping (mariadb-client installed)
    while ! mysqladmin ping --silent \
            -h "${MARIADB_HOST:-127.0.0.1}" \
            -P "${MARIADB_PORT:-3306}" 2>/dev/null; do
        [[ $elapsed -ge $timeout ]] && {
            log_error "MySQL/MariaDB not ready after ${timeout}s"
            return 1
        }
        sleep 1
        elapsed=$((elapsed + 1))
    done
    log_success "MySQL/MariaDB is ready"
}

mysql_execute() {
    local sql=$1
    local user=${2:-root}
    local password=${3:-}
    local host=${4:-${MARIADB_HOST:-127.0.0.1}}
    local port=${5:-${MARIADB_PORT:-3306}}

    if [[ -n "$password" ]]; then
        mysql -h"$host" -P"$port" -u"$user" -p"$password" -e "$sql" 2>/dev/null
    else
        mysql -h"$host" -P"$port" -u"$user" -e "$sql" 2>/dev/null
    fi
}

mysql_database_exists() {
    local database=$1 user=${2:-root} password=${3:-}
    local result
    if [[ -n "$password" ]]; then
        result=$(mysql -h"${MARIADB_HOST:-127.0.0.1}" -P"${MARIADB_PORT:-3306}" \
            -u"$user" -p"$password" \
            -e "SHOW DATABASES LIKE '${database}';" 2>/dev/null | tail -1)
    else
        result=$(mysql -h"${MARIADB_HOST:-127.0.0.1}" -P"${MARIADB_PORT:-3306}" \
            -u"$user" \
            -e "SHOW DATABASES LIKE '${database}';" 2>/dev/null | tail -1)
    fi
    [[ "$result" == "$database" ]]
}

mysql_user_exists() {
    local username=$1 user=${2:-root} password=${3:-}
    local result
    if [[ -n "$password" ]]; then
        result=$(mysql -h"${MARIADB_HOST:-127.0.0.1}" -P"${MARIADB_PORT:-3306}" \
            -u"$user" -p"$password" \
            -e "SELECT User FROM mysql.user WHERE User='${username}';" 2>/dev/null | tail -1)
    else
        result=$(mysql -h"${MARIADB_HOST:-127.0.0.1}" -P"${MARIADB_PORT:-3306}" \
            -u"$user" \
            -e "SELECT User FROM mysql.user WHERE User='${username}';" 2>/dev/null | tail -1)
    fi
    [[ "$result" == "$username" ]]
}

mysql_create_database() {
    local database=$1 charset=${2:-utf8mb4} collation=${3:-utf8mb4_unicode_ci}
    local user=${4:-root} password=${5:-}

    if mysql_database_exists "$database" "$user" "$password"; then
        log_info "Database already exists: ${database}"
        return 0
    fi
    log_info "Creating database: ${database}"
    mysql_execute "CREATE DATABASE \`${database}\` CHARACTER SET ${charset} COLLATE ${collation};" \
        "$user" "$password"
    log_success "Database created: ${database}"
}

mysql_create_user() {
    local username=$1 password=$2 host=${3:-%}
    local admin_user=${4:-root} admin_password=${5:-}

    if mysql_user_exists "$username" "$admin_user" "$admin_password"; then
        log_info "User already exists: ${username}"
        return 0
    fi
    log_info "Creating user: ${username}@${host}"
    mysql_execute "CREATE USER '${username}'@'${host}' IDENTIFIED BY '${password}';" \
        "$admin_user" "$admin_password"
    log_success "User created: ${username}@${host}"
}

mysql_grant_privileges() {
    local database=$1 username=$2 host=${3:-%}
    local user=${4:-root} password=${5:-}

    log_info "Granting privileges on ${database} to ${username}@${host}"
    mysql_execute "GRANT ALL PRIVILEGES ON \`${database}\`.* TO '${username}'@'${host}';" \
        "$user" "$password"
    mysql_execute "FLUSH PRIVILEGES;" "$user" "$password"
    log_success "Privileges granted"
}

# =============================================================================
# POSTGRESQL OPERATIONS
# Adapted: removed 'sudo -u postgres' — running as root, use -U flag directly
# =============================================================================
postgres_is_running() {
    # Check local process first, then TCP
    is_running "postgres" || \
    tcp_is_reachable "${POSTGRES_HOST:-127.0.0.1}" "${POSTGRES_PORT:-5432}"
}

postgres_wait_ready() {
    local timeout=${1:-30}
    local elapsed=0
    log_info "Waiting for PostgreSQL to be ready..."
    # Adapted: use pg_isready if available, else direct psql
    while ! pg_isready \
            -h "${POSTGRES_HOST:-127.0.0.1}" \
            -p "${POSTGRES_PORT:-5432}" \
            -U "${POSTGRES_USER:-postgres}" \
            -q 2>/dev/null; do
        [[ $elapsed -ge $timeout ]] && {
            log_error "PostgreSQL not ready after ${timeout}s"
            return 1
        }
        sleep 1
        elapsed=$((elapsed + 1))
    done
    log_success "PostgreSQL is ready"
}

postgres_execute() {
    local sql=$1
    local database=${2:-postgres}
    local user=${3:-${POSTGRES_USER:-postgres}}
    local host=${4:-${POSTGRES_HOST:-127.0.0.1}}
    local port=${5:-${POSTGRES_PORT:-5432}}
    # Adapted: direct psql with -U flag (no sudo -u postgres needed as root)
    PGPASSWORD="${POSTGRES_PASSWORD:-}" \
        psql -h "$host" -p "$port" -U "$user" -d "$database" -c "$sql" 2>/dev/null
}

postgres_database_exists() {
    local database=$1
    local host=${2:-${POSTGRES_HOST:-127.0.0.1}}
    local port=${3:-${POSTGRES_PORT:-5432}}
    local user=${4:-${POSTGRES_USER:-postgres}}
    local result
    result=$(PGPASSWORD="${POSTGRES_PASSWORD:-}" \
        psql -h "$host" -p "$port" -U "$user" \
        -tAc "SELECT 1 FROM pg_database WHERE datname='${database}';" 2>/dev/null)
    [[ "$result" == "1" ]]
}

postgres_user_exists() {
    local username=$1
    local host=${2:-${POSTGRES_HOST:-127.0.0.1}}
    local port=${3:-${POSTGRES_PORT:-5432}}
    local result
    result=$(PGPASSWORD="${POSTGRES_PASSWORD:-}" \
        psql -h "$host" -p "$port" -U "${POSTGRES_USER:-postgres}" \
        -tAc "SELECT 1 FROM pg_roles WHERE rolname='${username}';" 2>/dev/null)
    [[ "$result" == "1" ]]
}

postgres_create_database() {
    local database=$1 owner=${2:-${POSTGRES_USER:-postgres}} encoding=${3:-UTF8}
    local host=${4:-${POSTGRES_HOST:-127.0.0.1}}
    local port=${5:-${POSTGRES_PORT:-5432}}

    if postgres_database_exists "$database" "$host" "$port"; then
        log_info "Database already exists: ${database}"
        return 0
    fi
    log_info "Creating database: ${database}"
    PGPASSWORD="${POSTGRES_PASSWORD:-}" \
        createdb -h "$host" -p "$port" -U "${POSTGRES_USER:-postgres}" \
        -O "$owner" -E "$encoding" "$database" 2>/dev/null
    log_success "Database created: ${database}"
}

postgres_create_user() {
    local username=$1 password=$2
    local host=${3:-${POSTGRES_HOST:-127.0.0.1}}
    local port=${4:-${POSTGRES_PORT:-5432}}

    if postgres_user_exists "$username" "$host" "$port"; then
        log_info "User already exists: ${username}"
        return 0
    fi
    log_info "Creating user: ${username}"
    PGPASSWORD="${POSTGRES_PASSWORD:-}" \
        psql -h "$host" -p "$port" -U "${POSTGRES_USER:-postgres}" \
        -c "CREATE USER ${username} WITH PASSWORD '${password}';" 2>/dev/null
    log_success "User created: ${username}"
}

postgres_grant_privileges() {
    local database=$1 username=$2
    local host=${3:-${POSTGRES_HOST:-127.0.0.1}}
    local port=${4:-${POSTGRES_PORT:-5432}}

    log_info "Granting privileges on ${database} to ${username}"
    PGPASSWORD="${POSTGRES_PASSWORD:-}" \
        psql -h "$host" -p "$port" -U "${POSTGRES_USER:-postgres}" \
        -c "GRANT ALL PRIVILEGES ON DATABASE ${database} TO ${username};" 2>/dev/null
    log_success "Privileges granted"
}

# =============================================================================
# GENERIC DATABASE OPERATIONS
# =============================================================================
wait_for_database() {
    local db_type=$1 timeout=${2:-30}
    case "$db_type" in
        mysql|mariadb)   mysql_wait_ready "$timeout" ;;
        postgres|postgresql) postgres_wait_ready "$timeout" ;;
        *)
            log_error "Unknown database type: ${db_type}"
            return 1
            ;;
    esac
}

test_db_connection() {
    local db_type=$1 host=$2 port=$3 database=$4 username=$5 password=$6

    log_info "Testing ${db_type} connection to ${host}:${port}/${database}"

    # Step 1: TCP reachability (works even without credentials)
    if ! tcp_is_reachable "$host" "$port"; then
        log_error "Host not reachable: ${host}:${port} — is the environment up?"
        return 1
    fi
    log_success "TCP reachable: ${host}:${port}"

    # Step 2: Authenticated connection
    case "$db_type" in
        mysql|mariadb)
            mysql -h"$host" -P"$port" -u"$username" -p"$password" \
                -e "SELECT 1;" "$database" &>/dev/null
            ;;
        postgres|postgresql)
            PGPASSWORD="$password" \
                psql -h "$host" -p "$port" -U "$username" -d "$database" \
                -c "SELECT 1;" &>/dev/null
            ;;
        *)
            log_error "Unknown database type: ${db_type}"
            return 1
            ;;
    esac

    if [[ $? -eq 0 ]]; then
        log_success "Connection successful: ${db_type}://${username}@${host}:${port}/${database}"
        return 0
    else
        log_error "Authentication failed: ${db_type}://${username}@${host}:${port}/${database}"
        return 1
    fi
}

# =============================================================================
# EXPORTS
# =============================================================================
export -f tcp_is_reachable wait_for_tcp
export -f mysql_is_running mysql_wait_ready mysql_execute
export -f mysql_database_exists mysql_user_exists
export -f mysql_create_database mysql_create_user mysql_grant_privileges
export -f postgres_is_running postgres_wait_ready postgres_execute
export -f postgres_database_exists postgres_user_exists
export -f postgres_create_database postgres_create_user postgres_grant_privileges
export -f wait_for_database test_db_connection
