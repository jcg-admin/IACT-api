#!/bin/bash
# =============================================================================
# network.sh — Funciones de red para scripts IACT API
# =============================================================================
# Provee: tcp_is_reachable, wait_for_port
#
# Depende de: logging.sh
# =============================================================================

# -----------------------------------------------------------------------------
# tcp_is_reachable <host> <puerto> [timeout_segundos]
#   Intenta conectar via TCP. Retorna 0 si el puerto esta abierto, 1 si no.
#   Usa /dev/tcp de bash o nc si esta disponible.
#
#   Uso:
#     if tcp_is_reachable 127.0.0.1 5432 3; then ...
# -----------------------------------------------------------------------------
tcp_is_reachable() {
    local host="$1"
    local port="$2"
    local timeout="${3:-5}"

    if command -v nc &>/dev/null; then
        nc -z -w "$timeout" "$host" "$port" &>/dev/null
        return $?
    fi

    # Fallback con /dev/tcp (built-in de bash)
    (
        exec 3<>/dev/tcp/"$host"/"$port"
    ) &>/dev/null
    return $?
}

# -----------------------------------------------------------------------------
# wait_for_port <host> <puerto> [intentos] [segundos_entre_intentos]
#   Espera hasta que el puerto este disponible o se agoten los intentos.
#   Retorna 0 si el puerto abrio, 1 si se agoto el tiempo.
#
#   Uso:
#     wait_for_port 127.0.0.1 5432 10 2
# -----------------------------------------------------------------------------
wait_for_port() {
    local host="$1"
    local port="$2"
    local attempts="${3:-10}"
    local sleep_secs="${4:-2}"

    local i=0
    while (( i < attempts )); do
        if tcp_is_reachable "$host" "$port" 2; then
            return 0
        fi
        i=$(( i + 1 ))
        log_info "Esperando ${host}:${port} ... intento ${i}/${attempts}"
        sleep "$sleep_secs"
    done

    log_error "Puerto ${host}:${port} no disponible despues de ${attempts} intentos"
    return 1
}

# -----------------------------------------------------------------------------
# wait_for_port <host> <puerto> [intentos] [segundos_espera]
#   Espera hasta que el puerto este disponible.
#   Reintenta <intentos> veces con <segundos_espera> entre cada intento.
#   Retorna 0 si el puerto respondio, 1 si no respondio en el plazo.
#
#   Util para esperar que un servicio externo este listo antes de continuar.
#
#   Uso:
#     wait_for_port 127.0.0.1 5432 10 2 || { log_fatal "PostgreSQL no responde"; exit 1; }
# -----------------------------------------------------------------------------
wait_for_port() {
    local host="$1" port="$2" attempts="${3:-10}" sleep_secs="${4:-2}"
    local i=0
    while (( i < attempts )); do
        tcp_is_reachable "$host" "$port" 2 && return 0
        i=$(( i + 1 ))
        log_info "Esperando ${host}:${port} ... intento ${i}/${attempts}"
        sleep "$sleep_secs"
    done
    log_error "Puerto ${host}:${port} no disponible despues de ${attempts} intentos"
    return 1
}
