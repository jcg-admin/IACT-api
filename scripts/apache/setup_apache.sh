#!/bin/bash

# setup_apache.sh — Configura Apache + mod_wsgi para IACT Call Center
#
# ESTRATEGIA DE ARCHIVOS:
#   Conf (git)           : scripts/apache/iact-apache.conf     (valores de desarrollo, en git)
#   Symlink Apache       : /etc/apache2/sites-available/iact.conf -> scripts/apache/iact-apache.conf
#   Habilitado por a2ensite: /etc/apache2/sites-enabled/iact.conf -> ../sites-available/iact.conf
#
# Para cambiar rutas o settings: edita las directivas Define en iact-apache.conf
#
# IDEMPOTENTE: se puede ejecutar múltiples veces sin efectos adversos.
# PREREQUISITO: sudo bash scripts/apache/install_apache_deb.sh
#
# Uso: sudo bash scripts/apache/setup_apache.sh

set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../utils/logging.sh"

# ==============================================================================
# RUTAS
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# PROJECT_ROOT viene de logging.sh (apunta a IACT-api/)
DJANGO_DIR="$PROJECT_ROOT/callcentersite"
VENV_DIR="$PROJECT_ROOT/venv"

DJANGO_SETTINGS_MODULE="config.settings.production"
WSGI_FILE="$DJANGO_DIR/config/wsgi.py"

# Conf: archivo en el repo con valores de desarrollo (en git)
# El symlink de Apache apunta directamente a este archivo.
# Para producción: edita las variables Define al inicio de iact-apache.conf
APACHE_CONF_SRC="$SCRIPT_DIR/iact-apache.conf"

# Destino en Apache — symlink al archivo del repo
APACHE_SITES_AVAILABLE="/etc/apache2/sites-available"
APACHE_CONF_LINK="$APACHE_SITES_AVAILABLE/iact.conf"

STATIC_ROOT="${STATIC_ROOT:-/var/www/iact/static}"
MEDIA_ROOT="${MEDIA_ROOT:-/var/www/iact/media}"
LOG_DIR="${LOG_DIR:-/var/log/apache2}"

TOTAL_STEPS=5

# ==============================================================================
# HELPERS
# ==============================================================================

# Reinicia Apache de forma compatible con entornos con y sin systemd
restart_apache() {
    if command -v systemctl &>/dev/null && systemctl is-system-running &>/dev/null 2>&1; then
        systemctl restart apache2
        systemctl is-active --quiet apache2 && log_success "Apache reiniciado (systemctl)" || return 1
    elif command -v service &>/dev/null; then
        service apache2 restart
        log_success "Apache reiniciado (service)"
    else
        apache2ctl graceful
        log_success "Apache reiniciado (apache2ctl graceful)"
    fi
}

apache_is_running() {
    if command -v systemctl &>/dev/null && systemctl is-system-running &>/dev/null 2>&1; then
        systemctl is-active --quiet apache2
    else
        # En contenedores: verificar proceso activo
        pgrep -x apache2 &>/dev/null
    fi
}

# ==============================================================================
# PASO 1 — Prerequisitos
# ==============================================================================

check_prerequisites() {
    log_step 1 $TOTAL_STEPS "Verificando prerequisitos"

    local ok=true

    [[ $EUID -ne 0 ]] && log_fatal "Ejecuta con sudo" && exit 1

    command -v apache2 &>/dev/null \
        && log_info "Apache: $(apache2 -v 2>&1 | head -1)" \
        || { log_fatal "Apache no instalado. Ejecuta primero: sudo bash scripts/apache/install_apache_deb.sh"; exit 1; }

    apache2ctl -M 2>/dev/null | grep -q wsgi_module \
        && log_info "mod_wsgi: habilitado" \
        || { log_fatal "mod_wsgi no activo. Ejecuta: sudo bash scripts/apache/install_apache_deb.sh"; exit 1; }

    [[ -f "$DJANGO_DIR/manage.py" ]]  || { log_fatal "manage.py no encontrado en $DJANGO_DIR"; ok=false; }
    [[ -f "$WSGI_FILE" ]]             || { log_fatal "wsgi.py no encontrado en $WSGI_FILE"; ok=false; }
    [[ -d "$VENV_DIR" ]]              || { log_fatal "Virtualenv no encontrado en $VENV_DIR"; ok=false; }
    [[ -f "$APACHE_CONF_SRC" ]]        || { log_fatal "Conf no encontrado: $APACHE_CONF_SRC"; ok=false; }

    $ok || exit 1
    log_success "Prerequisitos OK"
}

# ==============================================================================
# PASO 2 — Generar conf y crear symlink en sites-available
# ==============================================================================

configure_virtualhost() {
    log_step 2 $TOTAL_STEPS "Configurando VirtualHost (symlink al repo)"

    # Crear/actualizar symlink en sites-available apuntando al archivo del repo.
    # Si ya existe y apunta al lugar correcto → sin cambios (idempotente).
    # Si es un archivo real o apunta a otro lugar → reemplazar.
    local needs_link=false

    if [[ -L "$APACHE_CONF_LINK" ]]; then
        current_target="$(readlink -f "$APACHE_CONF_LINK" 2>/dev/null || echo '')"
        if [[ "$current_target" == "$APACHE_CONF_SRC" ]]; then
            log_info "Symlink ya correcto: $APACHE_CONF_LINK -> $APACHE_CONF_SRC"
        else
            log_warn "Symlink apunta a '$current_target', actualizando..."
            rm "$APACHE_CONF_LINK"
            needs_link=true
        fi
    elif [[ -f "$APACHE_CONF_LINK" ]]; then
        log_warn "Existe archivo real en $APACHE_CONF_LINK, reemplazando con symlink..."
        rm "$APACHE_CONF_LINK"
        needs_link=true
    else
        needs_link=true
    fi

    if $needs_link; then
        ln -s "$APACHE_CONF_SRC" "$APACHE_CONF_LINK"
        log_success "Symlink creado: $APACHE_CONF_LINK -> $APACHE_CONF_SRC"
    fi

    # 2c. Deshabilitar default, habilitar iact
    a2dissite 000-default.conf &>/dev/null || true
    a2ensite iact.conf &>/dev/null && log_success "Sitio habilitado: iact.conf"

    # 2d. Módulos necesarios
    a2enmod headers &>/dev/null && log_info "Módulo headers habilitado"

    # 2e. Verificar sintaxis
    if apache2ctl configtest 2>&1 | grep -q "Syntax OK"; then
        log_success "Sintaxis Apache: OK"
    else
        log_error "Error de sintaxis:"
        apache2ctl configtest 2>&1
        exit 1
    fi
}

# ==============================================================================
# PASO 3 — Directorios static/media/logs
# ==============================================================================

create_directories() {
    log_step 3 $TOTAL_STEPS "Creando directorios static / media / logs"

    for dir in "$STATIC_ROOT" "$MEDIA_ROOT" "$LOG_DIR"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            log_info "Creado: $dir"
        else
            log_info "Ya existe: $dir"
        fi
    done

    chown -R www-data:www-data "$STATIC_ROOT" "$MEDIA_ROOT"
    chmod -R 755 "$STATIC_ROOT" "$MEDIA_ROOT"
    log_success "Permisos configurados (www-data)"
}

# ==============================================================================
# PASO 4 — collectstatic
# ==============================================================================

collect_static() {
    log_step 4 $TOTAL_STEPS "Ejecutando collectstatic"

    cd "$DJANGO_DIR"
    DJANGO_SETTINGS_MODULE="$DJANGO_SETTINGS_MODULE" \
        "$VENV_DIR/bin/python" manage.py collectstatic --noinput

    local count
    count=$(find "$STATIC_ROOT" -type f 2>/dev/null | wc -l)
    log_success "Archivos estáticos recolectados: $count archivos en $STATIC_ROOT"
}

# ==============================================================================
# PASO 5 — Arrancar / recargar Apache
# ==============================================================================

start_apache() {
    log_step 5 $TOTAL_STEPS "Iniciando / recargando Apache"

    if apache_is_running; then
        restart_apache || { log_error "No se pudo reiniciar Apache. Revisa: apache2ctl configtest"; exit 1; }
    else
        if command -v systemctl &>/dev/null && systemctl is-system-running &>/dev/null 2>&1; then
            systemctl start apache2
        elif command -v service &>/dev/null; then
            service apache2 start
        else
            apache2ctl start
        fi
        log_success "Apache iniciado"
    fi
}

# ==============================================================================
# MAIN
# ==============================================================================

log_header "SETUP APACHE + DJANGO — IACT Call Center"

echo "Rutas configuradas:"
echo "  PROJECT_ROOT        : $PROJECT_ROOT"
echo "  DJANGO_DIR          : $DJANGO_DIR"
echo "  VENV_DIR            : $VENV_DIR"
echo "  WSGI_FILE           : $WSGI_FILE"
echo "  SETTINGS MODULE     : $DJANGO_SETTINGS_MODULE"
echo "  STATIC_ROOT         : $STATIC_ROOT"
echo "  MEDIA_ROOT          : $MEDIA_ROOT"
echo ""
echo "Archivos Apache:"
echo "  Conf (git)          : $APACHE_CONF_SRC"
echo "  Symlink Apache      : $APACHE_CONF_LINK -> $APACHE_CONF_SRC"
echo ""

read -rp "Continuar? [yes/no]: " confirm
[[ "$confirm" != "yes" ]] && log_warn "Cancelado" && exit 0

check_prerequisites
configure_virtualhost
create_directories
collect_static
start_apache

log_header "SETUP COMPLETADO"
echo ""
echo "  Sitio activo en  : http://$(hostname -I | awk '{print $1}' 2>/dev/null || echo 'localhost')"
echo "  Conf (git)       : $APACHE_CONF_SRC"
echo "  Symlink Apache   : $APACHE_CONF_LINK"
echo ""
echo "Próximos pasos:"
echo "  1. Ajusta las rutas Define en $APACHE_CONF_SRC y re-ejecuta si cambia el servidor"
echo "  2. Configura ALLOWED_HOSTS en $DJANGO_DIR/.env"
echo "  3. Verifica: sudo bash scripts/apache/check_apache.sh"
echo ""
