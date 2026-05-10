#!/bin/bash
# =============================================================================
# utils/database.sh — Funciones de base de datos para IACT-api
# =============================================================================
# Versión: 2.0.0 — Delegación a IACT-db
#
# A partir de esta versión, la lógica de arranque y detección de BDs
# vive en IACT-db/utils/database.sh (v1.1.0).
#
# Este archivo provee únicamente las funciones que bootstrap.sh y
# check_tools.sh necesitan localmente:
#   · Detección de MariaDB/PostgreSQL (sin arranque)
#   · db_start_mariadb / try_start_service (compatibilidad con bootstrap.sh)
#
# Para la infraestructura completa de BD (crear BDs, usuarios, privilegios,
# sembrar datos) usar IACT-db directamente.
#
# Historial:
#   v1.x — Lógica completa de BD en IACT-api (archivada en scripts/archive/)
#   v2.0.0 — Funciones de arranque/detección, setup delegado a IACT-db
# =============================================================================

set -euo pipefail

# Rutas de socket conocidas de MariaDB/MySQL en Ubuntu/Debian
_MYSQL_SOCKETS=(
    "/run/mysqld/mysqld.sock"
    "/var/run/mysqld/mysqld.sock"
    "/tmp/mysql.sock"
)

_MYSQL_PID_FILE="/run/mysqld/mysqld.pid"

# =============================================================================
# DETECCIÓN — MariaDB
# =============================================================================

# mariadb_is_running [host] [port]
#   Verifica si MariaDB responde. Orden: socket Unix → TCP.
mariadb_is_running() {
    local host="${1:-127.0.0.1}" port="${2:-3306}"

    if command -v mysqladmin &>/dev/null; then
        for sock in "${_MYSQL_SOCKETS[@]}"; do
            if [[ -S "$sock" ]] && \
               mysqladmin --socket="$sock" ping --silent >/dev/null 2>&1; then
                return 0
            fi
        done
        if mysqladmin ping --silent --host="$host" --port="$port" \
           >/dev/null 2>&1; then
            return 0
        fi
    fi

    can_reach_port "$host" "$port" 3 2>/dev/null || return 1
}

# Alias usado en bootstrap.sh y check_tools.sh
mysql_is_running() { mariadb_is_running "$@"; }

# mysql_cleanup_stale — limpia PID/sock huérfanos
mysql_cleanup_stale() {
    if [[ -f "$_MYSQL_PID_FILE" ]]; then
        local pid
        pid=$(cat "$_MYSQL_PID_FILE" 2>/dev/null || echo "")
        if [[ -n "$pid" ]] && ! kill -0 "$pid" 2>/dev/null; then
            log_warn "PID stale detectado: $_MYSQL_PID_FILE (PID $pid no existe)"
            rm -f "$_MYSQL_PID_FILE"
        fi
    fi

    for sock in "${_MYSQL_SOCKETS[@]}"; do
        if [[ -S "$sock" ]] && \
           ! mysqladmin --socket="$sock" ping --silent >/dev/null 2>&1; then
            log_warn "Socket stale detectado: $sock"
            rm -f "$sock"
        fi
    done

    log_info "  --  Limpiados archivos stale"
}

# mysql_wait_ready [timeout]
mysql_wait_ready() {
    local timeout="${1:-30}" elapsed=0
    log_info "  --  Esperando a que MySQL este listo (timeout: ${timeout}s)..."

    while ! mariadb_is_running; do
        if [[ $elapsed -ge $timeout ]]; then
            log_error "MySQL no respondió en ${timeout}s"
            return 1
        fi
        sleep 2
        (( elapsed += 2 ))
        log_info "  --    ... ${elapsed}s / ${timeout}s"
    done

    log_success "  OK  MySQL listo (${elapsed}s)"
}

# =============================================================================
# ARRANQUE — MariaDB
# =============================================================================

_mysql_start_systemd() {
    command -v service &>/dev/null || return 1
    service mysql   start 2>/dev/null && return 0
    service mariadb start 2>/dev/null && return 0
    return 1
}

_mysql_start_direct() {
    local daemon
    if   command -v mariadbd &>/dev/null; then daemon="mariadbd"
    elif command -v mysqld   &>/dev/null; then daemon="/usr/sbin/mariadbd"
    else
        log_error "No se encontró mariadbd ni mysqld"
        return 1
    fi

    log_info "  --  Arrancando $daemon directamente (sin systemd)..."

    mkdir -p /run/mysqld
    chown mysql:mysql /run/mysqld 2>/dev/null || true

    nohup su -s /bin/bash mysql -c \
        "$daemon \
         --datadir=/var/lib/mysql \
         --socket=/run/mysqld/mysqld.sock \
         --pid-file=$_MYSQL_PID_FILE \
         --log-error=/var/log/mysql/error.log \
         --bind-address=127.0.0.1 \
         --port=3306" \
        >/tmp/mariadbd_startup.log 2>&1 &
}

# mysql_start — arranca MariaDB si no está corriendo
mysql_start() {
    if mariadb_is_running; then
        log_success "MySQL ya está corriendo"
        return 0
    fi

    log_warn "MySQL no responde. Iniciando procedimiento de arranque..."
    mysql_cleanup_stale

    if _mysql_start_systemd; then
        mysql_wait_ready 30 && return 0
    fi

    log_info "  --  service no disponible — intentando arranque directo"
    _mysql_start_direct
    mysql_wait_ready 30
}

# Alias usado en bootstrap.sh
db_start_mariadb() { mysql_start "$@"; }

# =============================================================================
# DETECCIÓN — PostgreSQL
# =============================================================================

pg_is_running() {
    local host="${1:-127.0.0.1}" port="${2:-5432}"

    if command -v pg_isready &>/dev/null; then
        pg_isready -h "$host" -p "$port" -q 2>/dev/null
        return $?
    fi

    can_reach_port "$host" "$port" 3 2>/dev/null || return 1
}

postgres_is_running() { pg_is_running "$@"; }

# =============================================================================
# EXPORTS
# =============================================================================

export -f mariadb_is_running mysql_is_running
export -f mysql_cleanup_stale mysql_wait_ready
export -f mysql_start db_start_mariadb
export -f pg_is_running postgres_is_running
