#!/bin/bash
# =============================================================================
# provisioning.sh — Funciones de aprovisionamiento para scripts IACT API
# =============================================================================
# Provee: install_apt_packages, check_apt_package, apt_update
#
# Depende de: logging.sh, core.sh, validation.sh
# =============================================================================

# -----------------------------------------------------------------------------
# apt_update
#   Ejecuta apt-get update. Se puede saltar con SKIP_APT_UPDATE=true.
# -----------------------------------------------------------------------------
apt_update() {
    if [[ "${SKIP_APT_UPDATE:-false}" == "true" ]]; then
        log_info "apt-get update omitido (--skip-update activo)"
        return 0
    fi

    log_info "Ejecutando apt-get update..."
    apt-get update -qq 2>&1 | tail -3
}

# -----------------------------------------------------------------------------
# check_apt_package <paquete>
#   Retorna 0 si el paquete esta instalado, 1 si no.
# -----------------------------------------------------------------------------
check_apt_package() {
    dpkg -l "$1" 2>/dev/null | grep -q "^ii"
}

# -----------------------------------------------------------------------------
# install_apt_packages <paquete1> [paquete2 ...]
#   Instala los paquetes que no esten ya instalados.
#   Idempotente: no reinstala los que ya existen.
# -----------------------------------------------------------------------------
install_apt_packages() {
    local to_install=()

    for pkg in "$@"; do
        if check_apt_package "$pkg"; then
            log_info "Ya instalado: ${pkg}"
        else
            to_install+=("$pkg")
        fi
    done

    if (( ${#to_install[@]} == 0 )); then
        log_success "Todos los paquetes ya estaban instalados"
        return 0
    fi

    log_info "Instalando: ${to_install[*]}"
    apt-get install -y --no-install-recommends "${to_install[@]}" 2>&1 | tail -5

    for pkg in "${to_install[@]}"; do
        if check_apt_package "$pkg"; then
            log_success "Instalado: ${pkg}"
        else
            log_warn "No se pudo instalar: ${pkg}"
        fi
    done
}

# -----------------------------------------------------------------------------
# setup_venv <ruta_venv> <ruta_requirements>
#   Crea el entorno virtual si no existe e instala requirements.
# -----------------------------------------------------------------------------
setup_venv() {
    local venv_dir="${1}"
    local requirements="${2}"

    if [[ ! -d "$venv_dir" ]]; then
        log_info "Creando entorno virtual en ${venv_dir}..."
        python3 -m venv "$venv_dir"
        log_success "Entorno virtual creado"
    else
        log_info "Entorno virtual ya existe: ${venv_dir}"
    fi

    if [[ -f "$requirements" ]]; then
        log_info "Instalando dependencias desde ${requirements}..."
        "${venv_dir}/bin/pip" install --quiet --upgrade pip
        "${venv_dir}/bin/pip" install --quiet -r "$requirements"
        log_success "Dependencias instaladas"
    else
        log_warn "No se encontro el archivo de requirements: ${requirements}"
    fi
}
