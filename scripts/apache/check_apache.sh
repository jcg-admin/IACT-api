#!/bin/bash

# Apache + Django Verification Script for IACT Call Center
# Located in: scripts/apache/check_apache.sh
# Verifica que Apache, mod_wsgi y Django esten correctamente configurados
# Date: 2026-03-14

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../utils/logging.sh"

# ==============================================================================
# PATHS
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DJANGO_DIR="$PROJECT_ROOT/callcentersite"
VENV_DIR="$PROJECT_ROOT/venv"
WSGI_FILE="$DJANGO_DIR/config/wsgi.py"
APACHE_CONF="/etc/apache2/sites-enabled/iact.conf"
APACHE_CONF_AVAILABLE="/etc/apache2/sites-available/iact.conf"

STATIC_ROOT="${STATIC_ROOT:-/var/www/iact/static}"
MEDIA_ROOT="${MEDIA_ROOT:-/var/www/iact/media}"

ERRORS=0
WARNINGS=0

# ==============================================================================
# HELPERS
# ==============================================================================

ok()   { echo -e "\033[0;32m[OK]\033[0m      $1"; }
fail() { echo -e "\033[0;31m[ERROR]\033[0m   $1"; ERRORS=$((ERRORS + 1)); }
warn() { echo -e "\033[0;33m[WARN]\033[0m    $1"; WARNINGS=$((WARNINGS + 1)); }
info() { echo -e "\033[0;34m[INFO]\033[0m    $1"; }

section() {
    echo ""
    echo "----------------------------------------------------------------------"
    echo "  $1"
    echo "----------------------------------------------------------------------"
}

# ==============================================================================
# CHECKS
# ==============================================================================

check_apache_installed() {
    section "1. APACHE"

    if command -v apache2 &>/dev/null; then
        version=$(apache2 -v 2>&1 | head -1)
        ok "Apache instalado: $version"
    else
        fail "Apache NO instalado. Ejecuta: scripts/apache/setup_apache.sh"
        return
    fi

    if systemctl is-active --quiet apache2; then
        ok "Apache activo (systemctl status: active)"
    else
        fail "Apache NO esta corriendo. Revisa: journalctl -xe"
    fi

    if apache2ctl configtest 2>&1 | grep -q "Syntax OK"; then
        ok "Sintaxis de configuracion Apache: OK"
    else
        fail "Errores de sintaxis en Apache:"
        apache2ctl configtest 2>&1 | grep -v "^$"
    fi
}

check_modwsgi() {
    section "2. MOD_WSGI"

    if apache2ctl -M 2>/dev/null | grep -q wsgi_module; then
        ok "mod_wsgi habilitado"
    else
        fail "mod_wsgi NO habilitado. Ejecuta: a2enmod wsgi && systemctl restart apache2"
    fi
}

check_apache_conf() {
    section "3. CONFIGURACION IACT"

    if [ -f "$APACHE_CONF_AVAILABLE" ]; then
        ok "Archivo disponible: $APACHE_CONF_AVAILABLE"
    else
        fail "Configuracion no encontrada: $APACHE_CONF_AVAILABLE"
        info "Ejecuta: bash scripts/apache/setup_apache.sh"
    fi

    if [ -f "$APACHE_CONF" ]; then
        ok "Sitio habilitado: $APACHE_CONF"
    else
        warn "Sitio NO habilitado en sites-enabled. Ejecuta: a2ensite iact.conf"
    fi

    # Verificar que apunta al wsgi.py correcto
    if [ -f "$APACHE_CONF_AVAILABLE" ] && grep -q "$WSGI_FILE" "$APACHE_CONF_AVAILABLE"; then
        ok "WSGIScriptAlias apunta a: $WSGI_FILE"
    elif [ -f "$APACHE_CONF_AVAILABLE" ]; then
        warn "WSGIScriptAlias no apunta a $WSGI_FILE - verifica manualmente"
    fi

    # Verificar DJANGO_SETTINGS_MODULE
    if [ -f "$APACHE_CONF_AVAILABLE" ] && grep -q "DJANGO_SETTINGS_MODULE" "$APACHE_CONF_AVAILABLE"; then
        setting=$(grep "DJANGO_SETTINGS_MODULE" "$APACHE_CONF_AVAILABLE" | head -1 | awk '{print $3}')
        ok "DJANGO_SETTINGS_MODULE: $setting"
    else
        warn "DJANGO_SETTINGS_MODULE no encontrado en la configuracion de Apache"
    fi
}

check_project_files() {
    section "4. ARCHIVOS DEL PROYECTO"

    for f in "$DJANGO_DIR/manage.py" "$WSGI_FILE" "$DJANGO_DIR/config/settings/production.py"; do
        if [ -f "$f" ]; then
            ok "$f"
        else
            fail "No encontrado: $f"
        fi
    done

    if [ -d "$VENV_DIR" ]; then
        ok "Virtualenv: $VENV_DIR"
        if [ -f "$VENV_DIR/bin/python" ]; then
            py_version=$("$VENV_DIR/bin/python" --version 2>&1)
            ok "Python en venv: $py_version"
        fi
    else
        fail "Virtualenv NO encontrado: $VENV_DIR"
    fi
}

check_static_media() {
    section "5. STATIC Y MEDIA"

    if [ -d "$STATIC_ROOT" ]; then
        count=$(find "$STATIC_ROOT" -type f 2>/dev/null | wc -l)
        ok "STATIC_ROOT: $STATIC_ROOT ($count archivos)"
        if [ "$count" -eq 0 ]; then
            warn "Sin archivos estaticos. Ejecuta: python manage.py collectstatic"
        fi
    else
        fail "STATIC_ROOT no existe: $STATIC_ROOT"
        info "Ejecuta: bash scripts/apache/setup_apache.sh"
    fi

    if [ -d "$MEDIA_ROOT" ]; then
        ok "MEDIA_ROOT: $MEDIA_ROOT"
    else
        fail "MEDIA_ROOT no existe: $MEDIA_ROOT"
    fi

    # Verificar permisos de www-data
    if [ -d "$STATIC_ROOT" ]; then
        owner=$(stat -c '%U' "$STATIC_ROOT" 2>/dev/null)
        if [ "$owner" = "www-data" ]; then
            ok "Propietario STATIC_ROOT: www-data"
        else
            warn "Propietario STATIC_ROOT es '$owner', deberia ser 'www-data'"
        fi
    fi
}

check_django_check() {
    section "6. DJANGO CHECK (produccion)"

    if [ ! -f "$VENV_DIR/bin/python" ]; then
        warn "Saltando django check: virtualenv no encontrado"
        return
    fi

    cd "$DJANGO_DIR"
    result=$(DJANGO_SETTINGS_MODULE=config.settings.production \
        "$VENV_DIR/bin/python" manage.py check --deploy 2>&1)
    exit_code=$?

    if [ $exit_code -eq 0 ]; then
        ok "django check --deploy: sin errores"
    else
        # Distinguir errores de warnings
        if echo "$result" | grep -q "^SystemCheckError\|ERRORS:"; then
            fail "django check --deploy encontro errores:"
            echo "$result" | grep -E "ERROR|CRITICAL" | head -10
        else
            warn "django check --deploy encontro advertencias:"
            echo "$result" | tail -5
        fi
    fi
}

check_connectivity() {
    section "7. CONECTIVIDAD"

    if command -v curl &>/dev/null; then
        http_code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ 2>/dev/null || echo "000")
        if [ "$http_code" = "200" ] || [ "$http_code" = "301" ] || [ "$http_code" = "302" ]; then
            ok "HTTP localhost responde: $http_code"
        elif [ "$http_code" = "000" ]; then
            warn "No se pudo conectar a http://localhost/ (puede ser normal si Apache no esta en este servidor)"
        else
            warn "HTTP localhost: $http_code (esperado 200/301/302)"
        fi
    else
        info "curl no disponible, saltando test de conectividad"
    fi
}

# ==============================================================================
# MAIN
# ==============================================================================

log_header "VERIFICACION APACHE + DJANGO - IACT Call Center"

check_apache_installed
check_modwsgi
check_apache_conf
check_project_files
check_static_media
check_django_check
check_connectivity

# ==============================================================================
# RESUMEN
# ==============================================================================

echo ""
echo "======================================================================"
echo "  RESUMEN"
echo "======================================================================"
echo -e "  Errores:       \033[0;31m$ERRORS\033[0m"
echo -e "  Advertencias:  \033[0;33m$WARNINGS\033[0m"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "\033[0;32m[OK]\033[0m Apache + Django configurados correctamente"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "\033[0;33m[WARN]\033[0m Configuracion con advertencias menores"
    exit 0
else
    echo -e "\033[0;31m[FALLO]\033[0m Se encontraron $ERRORS error(es). Revisa arriba."
    exit 1
fi
