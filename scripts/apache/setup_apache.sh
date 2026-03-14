#!/bin/bash

# Apache + mod_wsgi Setup Script for IACT Call Center
# Located in: scripts/apache/setup_apache.sh
# Configures Apache to serve the Django project via mod_wsgi
# Date: 2026-03-14

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../utils/logging.sh"

# ==============================================================================
# PATHS
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# PROJECT_ROOT is exported by logging.sh (points to IACT-api/)
DJANGO_DIR="$PROJECT_ROOT/callcentersite"
VENV_DIR="$PROJECT_ROOT/venv"

DJANGO_SETTINGS_MODULE="config.settings.production"
WSGI_FILE="$DJANGO_DIR/config/wsgi.py"
APACHE_CONF_TPL="$SCRIPT_DIR/iact-apache.conf"
APACHE_SITES_AVAILABLE="/etc/apache2/sites-available"
APACHE_CONF_DEST="$APACHE_SITES_AVAILABLE/iact.conf"

# Static / media (must match production.py)
STATIC_ROOT="${STATIC_ROOT:-/var/www/iact/static}"
MEDIA_ROOT="${MEDIA_ROOT:-/var/www/iact/media}"
LOG_DIR="${LOG_DIR:-/var/log/apache2}"

# ==============================================================================
# CHECKS
# ==============================================================================

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_fatal "Este script debe ejecutarse como root (sudo)"
        exit 1
    fi
}

check_prerequisites() {
    log_step 1 5 "Verificando prerequisitos"

    if [ ! -f "$DJANGO_DIR/manage.py" ]; then
        log_fatal "manage.py no encontrado en $DJANGO_DIR"
        exit 1
    fi

    if [ ! -f "$WSGI_FILE" ]; then
        log_fatal "wsgi.py no encontrado en $WSGI_FILE"
        exit 1
    fi

    if [ ! -d "$VENV_DIR" ]; then
        log_fatal "Virtualenv no encontrado en $VENV_DIR"
        log_error "Crea el virtualenv antes: python -m venv $VENV_DIR"
        exit 1
    fi

    if [ ! -f "$APACHE_CONF_TPL" ]; then
        log_fatal "Plantilla de configuracion no encontrada: $APACHE_CONF_TPL"
        exit 1
    fi

    log_success "Prerequisitos OK"
}

# ==============================================================================
# INSTALLATION
# ==============================================================================

install_apache_modwsgi() {
    log_step 2 5 "Instalando Apache y mod_wsgi"

    if command -v apache2 &>/dev/null; then
        log_info "Apache ya instalado: $(apache2 -v 2>&1 | head -1)"
    else
        log_info "Instalando apache2..."
        apt-get update -q
        apt-get install -y apache2
        log_success "apache2 instalado"
    fi

    # mod_wsgi para Python 3
    if apache2ctl -M 2>/dev/null | grep -q wsgi_module; then
        log_info "mod_wsgi ya activo"
    else
        log_info "Instalando libapache2-mod-wsgi-py3..."
        apt-get install -y libapache2-mod-wsgi-py3
        a2enmod wsgi
        log_success "mod_wsgi instalado y habilitado"
    fi
}

create_directories() {
    log_step 3 5 "Creando directorios de static/media/logs"

    for dir in "$STATIC_ROOT" "$MEDIA_ROOT" "$LOG_DIR"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log_info "Creado: $dir"
        else
            log_info "Ya existe: $dir"
        fi
    done

    # Apache (www-data) necesita acceso de lectura en static y lectura/escritura en media
    chown -R www-data:www-data "$STATIC_ROOT" "$MEDIA_ROOT"
    chmod -R 755 "$STATIC_ROOT"
    chmod -R 755 "$MEDIA_ROOT"

    log_success "Directorios configurados"
}

configure_apache() {
    log_step 4 5 "Instalando configuracion de Apache"

    # Generar conf desde plantilla reemplazando variables
    sed \
        -e "s|{{PROJECT_ROOT}}|$PROJECT_ROOT|g" \
        -e "s|{{DJANGO_DIR}}|$DJANGO_DIR|g" \
        -e "s|{{VENV_DIR}}|$VENV_DIR|g" \
        -e "s|{{WSGI_FILE}}|$WSGI_FILE|g" \
        -e "s|{{STATIC_ROOT}}|$STATIC_ROOT|g" \
        -e "s|{{MEDIA_ROOT}}|$MEDIA_ROOT|g" \
        -e "s|{{LOG_DIR}}|$LOG_DIR|g" \
        -e "s|{{DJANGO_SETTINGS_MODULE}}|$DJANGO_SETTINGS_MODULE|g" \
        "$APACHE_CONF_TPL" > "$APACHE_CONF_DEST"

    log_info "Configuracion generada en: $APACHE_CONF_DEST"

    # Habilitar el sitio y deshabilitar el default
    a2dissite 000-default.conf 2>/dev/null || true
    a2ensite iact.conf

    # Verificar sintaxis
    if apache2ctl configtest 2>&1 | grep -q "Syntax OK"; then
        log_success "Sintaxis Apache OK"
    else
        log_error "Error en la sintaxis de Apache:"
        apache2ctl configtest
        exit 1
    fi
}

collect_static_and_restart() {
    log_step 5 5 "Collectstatic y reinicio de Apache"

    log_info "Ejecutando collectstatic..."
    cd "$DJANGO_DIR"
    DJANGO_SETTINGS_MODULE="$DJANGO_SETTINGS_MODULE" \
        "$VENV_DIR/bin/python" manage.py collectstatic --noinput

    if [ $? -eq 0 ]; then
        log_success "Archivos estaticos recolectados en $STATIC_ROOT"
    else
        log_error "Fallo collectstatic"
        exit 1
    fi

    log_info "Reiniciando Apache..."
    systemctl restart apache2

    if systemctl is-active --quiet apache2; then
        log_success "Apache activo y corriendo"
    else
        log_error "Apache no pudo iniciar. Revisa: journalctl -xe"
        exit 1
    fi
}

# ==============================================================================
# MAIN
# ==============================================================================

log_header "APACHE + MOD_WSGI SETUP - IACT Call Center"

echo "Configuracion:"
echo "  PROJECT_ROOT            : $PROJECT_ROOT"
echo "  DJANGO_DIR              : $DJANGO_DIR"
echo "  VENV_DIR                : $VENV_DIR"
echo "  WSGI_FILE               : $WSGI_FILE"
echo "  DJANGO_SETTINGS_MODULE  : $DJANGO_SETTINGS_MODULE"
echo "  STATIC_ROOT             : $STATIC_ROOT"
echo "  MEDIA_ROOT              : $MEDIA_ROOT"
echo "  Apache conf destino     : $APACHE_CONF_DEST"
echo ""

read -p "Continuar con la instalacion? [yes/no]: " confirm
if [ "$confirm" != "yes" ]; then
    log_warn "Cancelado"
    exit 0
fi

check_root
check_prerequisites
install_apache_modwsgi
create_directories
configure_apache
collect_static_and_restart

log_header "SETUP COMPLETADO"
echo ""
echo "SIGUIENTES PASOS:"
echo "  1. Configura /etc/hosts o DNS apuntando al servidor"
echo "  2. Edita $APACHE_CONF_DEST y ajusta ServerName"
echo "  3. Configura el archivo .env en $DJANGO_DIR con ALLOWED_HOSTS"
echo "  4. Verifica con: bash scripts/apache/check_apache.sh"
echo ""
