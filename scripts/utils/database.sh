#!/bin/bash
# =============================================================================
# database.sh — Funciones de base de datos para scripts IACT API
# =============================================================================
# Provee: pg_is_running, mariadb_is_running, db_start_postgres,
#         mariadb_cleanup_stale, mariadb_wait_ready, db_start_mariadb
#
# Depende de: logging.sh, network.sh
#
# Historial:
#   v1.0.0 — Version original. mariadb_is_running solo TCP.
#             db_start_mariadb usaba mysqld_safe (deprecado).
#   v1.1.0 — Actualizaciones desde PracticaYoruba-api:
#             · mariadb_is_running: socket Unix primero, TCP despues.
#             · mariadb_cleanup_stale: limpia pid/sock de procesos muertos.
#             · mariadb_wait_ready: espera activa con polling (sin sleep fijo).
#             · db_start_mariadb: nohup con mariadbd/mysqld directo
#               (reemplaza mysqld_safe deprecado en MariaDB >= 10.4).
#               Flujo completo: check → cleanup → systemd → directo → wait.
# =============================================================================

# Rutas de socket conocidas de MariaDB/MySQL en Ubuntu
_MARIADB_SOCKETS=(
    "/run/mysqld/mysqld.sock"
    "/var/run/mysqld/mysqld.sock"
    "/tmp/mysql.sock"
)

_MARIADB_PID_FILE="/run/mysqld/mysqld.pid"

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
#   Verifica en este orden:
#     1. Unix socket (rapido, funciona en contenedores sin red)
#     2. TCP (host:port)
#   Retorna 0 si esta activo, 1 si no.
# -----------------------------------------------------------------------------
mariadb_is_running() {
    local host="${1:-127.0.0.1}"
    local port="${2:-3306}"

    if command -v mysqladmin &>/dev/null; then
        # 1. Intentar via socket Unix
        for sock in "${_MARIADB_SOCKETS[@]}"; do
            if [[ -S "$sock" ]]; then
                if mysqladmin --socket="$sock" ping --silent >/dev/null 2>&1; then
                    return 0
                fi
            fi
        done
        # 2. Intentar via TCP
        if mysqladmin ping --silent --host="$host" --port="$port" >/dev/null 2>&1; then
            return 0
        fi
    fi

    # 3. Fallback: conectividad TCP sin autenticacion
    tcp_is_reachable "$host" "$port" 3
}

# -----------------------------------------------------------------------------
# mariadb_cleanup_stale
#   Detecta y elimina archivos .pid y .sock que apuntan a procesos muertos.
#   Solo elimina archivos cuyo PID ya no existe en /proc.
#   Ocurre cuando el contenedor se reinicia sin apagar MariaDB limpiamente.
# -----------------------------------------------------------------------------
mariadb_cleanup_stale() {
    local cleaned=0

    for pid_file in /run/mysqld/*.pid; do
        [[ -f "$pid_file" ]] || continue
        local pid
        pid=$(cat "$pid_file" 2>/dev/null) || continue
        if [[ -n "$pid" ]] && ! kill -0 "$pid" 2>/dev/null; then
            log_warn "PID stale detectado: ${pid_file} (PID ${pid} no existe)"
            rm -f "$pid_file"
            cleaned=$(( cleaned + 1 ))
        fi
    done

    for sock in "${_MARIADB_SOCKETS[@]}"; do
        [[ -S "$sock" ]] || continue
        if ! mysqladmin --socket="$sock" ping --silent >/dev/null 2>&1; then
            log_warn "Socket stale detectado: ${sock}"
            rm -f "$sock"
            cleaned=$(( cleaned + 1 ))
        fi
    done

    (( cleaned > 0 )) && log_info "Limpiados ${cleaned} archivos stale" || true
}

# -----------------------------------------------------------------------------
# mariadb_wait_ready [timeout_secs]
#   Espera activamente hasta que mariadb_is_running retorne 0.
#   Retorna 0 si el servidor respondio antes del timeout, 1 si no.
# -----------------------------------------------------------------------------
mariadb_wait_ready() {
    local timeout="${1:-30}" elapsed=0 interval=2

    log_info "Esperando a que MariaDB este listo (timeout: ${timeout}s)..."

    while (( elapsed < timeout )); do
        if mariadb_is_running; then
            log_success "MariaDB listo (${elapsed}s)"
            return 0
        fi
        sleep "$interval"
        elapsed=$(( elapsed + interval ))
        log_info "  ... ${elapsed}s / ${timeout}s"
    done

    log_error "MariaDB no respondio en ${timeout}s"
    log_error "Revisa el log: /var/lib/mysql/mysqld_err.log"
    return 1
}

# -----------------------------------------------------------------------------
# _mariadb_start_systemd
#   Intenta arrancar MariaDB via service/systemctl.
#   Retorna 0 si tuvo exito, 1 si el gestor no esta disponible o fallo.
# -----------------------------------------------------------------------------
_mariadb_start_systemd() {
    command -v service &>/dev/null || return 1
    service mariadb start 2>/dev/null && return 0
    service mysql start 2>/dev/null && return 0
    return 1
}

# -----------------------------------------------------------------------------
# _mariadb_start_direct
#   Arranca mariadbd/mysqld directamente con nohup.
#   Usado como fallback en contenedores sin systemd.
#   Reemplaza mysqld_safe (deprecado en MariaDB >= 10.4).
#   Busca el binario en rutas conocidas de Ubuntu.
# -----------------------------------------------------------------------------
_mariadb_start_direct() {
    local daemon=""
    for bin in /usr/sbin/mariadbd /usr/sbin/mysqld /usr/bin/mariadbd; do
        [[ -x "$bin" ]] && daemon="$bin" && break
    done

    if [[ -z "$daemon" ]]; then
        log_error "No se encontro el daemon de MariaDB/MySQL en rutas conocidas"
        return 1
    fi

    log_info "Arrancando ${daemon} directamente (sin systemd)..."

    nohup su -s /bin/bash mysql -c \
        "${daemon} \
         --datadir=/var/lib/mysql \
         --socket=/run/mysqld/mysqld.sock \
         --pid-file=${_MARIADB_PID_FILE} \
         --log-error=/var/lib/mysql/mysqld_err.log \
         --bind-address=127.0.0.1 \
         --port=3306" \
        > /tmp/mariadbd_startup.log 2>&1 &

    return 0
}

# -----------------------------------------------------------------------------
# db_start_mariadb
#   Punto de entrada principal para arranque de MariaDB.
#   Flujo:
#     1. Si ya corre → retornar 0 inmediatamente
#     2. Limpiar estado stale de sesiones anteriores
#     3. Intentar arranque via systemd/service
#     4. Si falla, intentar arranque directo (contenedores sin systemd)
#     5. Esperar activamente hasta que responda (max 30s)
# -----------------------------------------------------------------------------
db_start_mariadb() {
    if mariadb_is_running; then
        log_success "MariaDB ya esta activo"
        return 0
    fi

    log_info "MariaDB no responde. Iniciando procedimiento de arranque..."

    mariadb_cleanup_stale

    if _mariadb_start_systemd; then
        log_info "Arranque via service solicitado"
    else
        log_info "service no disponible — intentando arranque directo"
        _mariadb_start_direct || {
            log_error "No se pudo iniciar MariaDB"
            return 1
        }
    fi

    mariadb_wait_ready 30
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
