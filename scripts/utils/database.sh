#!/bin/bash
# =============================================================================
# database.sh — Funciones de base de datos para scripts IACT API
# =============================================================================
# Provee: pg_is_running, mariadb_is_running, db_start_postgres, db_start_mariadb
#
# Depende de: logging.sh, network.sh
# =============================================================================

# -----------------------------------------------------------------------------
# pg_is_running [host] [puerto]
#   Verifica si PostgreSQL esta aceptando conexiones.
#   Retorna 0 si esta activo, 1 si no.
# -----------------------------------------------------------------------------
pg_is_running() {
    local host="${1:-127.0.0.1}"
    local port="${2:-5432}"

    if command -v pg_isready &>/dev/null; then
        pg_isready -h "$host" -p "$port" -q 2>/dev/null
        return $?
    fi

    tcp_is_reachable "$host" "$port" 3
}

# -----------------------------------------------------------------------------
# mariadb_is_running [host] [puerto]
#   Verifica si MariaDB/MySQL esta aceptando conexiones.
#   Retorna 0 si esta activo, 1 si no.
# -----------------------------------------------------------------------------
mariadb_is_running() {
    local host="${1:-127.0.0.1}"
    local port="${2:-3306}"

    if command -v mysqladmin &>/dev/null; then
        mysqladmin ping --silent --host="$host" --port="$port" 2>/dev/null
        return $?
    fi

    tcp_is_reachable "$host" "$port" 3
}

# -----------------------------------------------------------------------------
# db_start_postgres [cluster_version] [cluster_name]
#   Intenta arrancar PostgreSQL usando pg_ctlcluster o service.
#   Para entornos sin systemd (contenedores).
# -----------------------------------------------------------------------------
db_start_postgres() {
    local version="${1:-16}"
    local cluster="${2:-main}"

    if command -v pg_ctlcluster &>/dev/null; then
        log_info "Arrancando PostgreSQL con pg_ctlcluster ${version} ${cluster}..."
        pg_ctlcluster "$version" "$cluster" start 2>&1 || true
    elif command -v service &>/dev/null; then
        log_info "Arrancando PostgreSQL con service..."
        service postgresql start 2>/dev/null || true
    else
        log_warn "No se encontro pg_ctlcluster ni service para arrancar PostgreSQL"
    fi
}

# -----------------------------------------------------------------------------
# db_start_mariadb
#   Intenta arrancar MariaDB usando mysqld_safe (sin systemd).
#   Limpia archivos stale de socket/PID antes de arrancar.
# -----------------------------------------------------------------------------
db_start_mariadb() {
    log_info "Limpiando archivos stale de MariaDB..."
    rm -f /var/run/mysqld/mysqld.sock /var/run/mysqld/mysqld.pid \
           /run/mysqld/mysqld.sock /run/mysqld/mysqld.pid 2>/dev/null || true

    if command -v mysqld_safe &>/dev/null; then
        log_info "Arrancando MariaDB con mysqld_safe..."
        mysqld_safe --user=mysql --innodb-use-native-aio=0 &>/dev/null &
        sleep 5
    elif command -v service &>/dev/null; then
        service mariadb start 2>/dev/null || true
    else
        log_warn "No se encontro mysqld_safe ni service para arrancar MariaDB"
    fi
}
