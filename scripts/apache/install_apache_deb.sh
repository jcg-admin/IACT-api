#!/bin/bash

# install_apache_deb.sh
# Instala Apache 2.4 + mod_wsgi descargando los .deb directamente desde
# archive.ubuntu.com — funciona aunque sudo no resuelva el hostname local.
#
# Probado en: Ubuntu 24.04 LTS (Noble) amd64
# Uso:        sudo bash scripts/apache/install_apache_deb.sh

set -euo pipefail

# ==============================================================================
# CONFIGURACION
# ==============================================================================

ARCH="amd64"
UBUNTU_POOL="http://archive.ubuntu.com/ubuntu/pool/main"
TMP_DIR="/tmp/iact_apache_debs"
VENV_DIR="${VENV_DIR:-/home/user/IACT-api/venv}"

# Versiones exactas para Ubuntu 24.04 Noble
APR_VER="1.7.2-3.1build2"
APRUTIL_VER="1.6.3-1.1ubuntu7"
LUA_VER="5.4.6-3build2"
APACHE_VER="2.4.58-1ubuntu8.11"
MODWSGI_SRC_VER="5.0.2"
MODWSGI_SRC_URL="https://files.pythonhosted.org/packages/source/m/mod_wsgi/mod_wsgi-${MODWSGI_SRC_VER}.tar.gz"

# ==============================================================================
# COLORES / LOGGING
# ==============================================================================

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'

log_info()    { echo -e "${CYAN}[INFO]${NC}    $*"; }
log_success() { echo -e "${GREEN}[OK]${NC}      $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC}    $*"; }
log_error()   { echo -e "${RED}[ERROR]${NC}   $*" >&2; }
log_step()    { echo -e "\n${BLUE}══ PASO $1/$2 ══${NC} $3"; }

# ==============================================================================
# UTILIDADES
# ==============================================================================

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "Ejecuta con sudo: sudo bash $0"
        exit 1
    fi
}

# Descarga un .deb si no existe ya en TMP_DIR
download_deb() {
    local url="$1"
    local filename
    filename="$(basename "$url")"
    local dest="$TMP_DIR/$filename"

    if [[ -f "$dest" ]]; then
        log_info "Ya descargado: $filename"
        return 0
    fi

    log_info "Descargando $filename ..."
    if ! wget -q --show-progress "$url" -O "$dest"; then
        log_error "Falló la descarga: $url"
        rm -f "$dest"
        exit 1
    fi
    log_success "$filename"
}

# ==============================================================================
# PASO 1 – Verificar conectividad
# ==============================================================================

check_network() {
    log_step 1 5 "Verificando conectividad con archive.ubuntu.com"
    if curl -s --max-time 8 "http://archive.ubuntu.com/ubuntu/" -o /dev/null; then
        log_success "Conexión disponible"
    else
        log_error "No hay acceso a archive.ubuntu.com. Verifica la red."
        exit 1
    fi
}

# ==============================================================================
# PASO 2 – Descargar todos los .deb necesarios
# ==============================================================================

download_packages() {
    log_step 2 5 "Descargando paquetes .deb en $TMP_DIR"
    mkdir -p "$TMP_DIR"

    # --- Apache Runtime (libapr) ---
    download_deb "${UBUNTU_POOL}/a/apr/libapr1t64_${APR_VER}_${ARCH}.deb"
    download_deb "${UBUNTU_POOL}/a/apr-util/libaprutil1t64_${APRUTIL_VER}_${ARCH}.deb"
    download_deb "${UBUNTU_POOL}/a/apr-util/libaprutil1-dbd-sqlite3_${APRUTIL_VER}_${ARCH}.deb"
    download_deb "${UBUNTU_POOL}/a/apr-util/libaprutil1-ldap_${APRUTIL_VER}_${ARCH}.deb"

    # --- Lua (requerido por apache2-bin) ---
    download_deb "${UBUNTU_POOL}/l/lua5.4/liblua5.4-0_${LUA_VER}_${ARCH}.deb"

    # --- Apache2 ---
    download_deb "${UBUNTU_POOL}/a/apache2/apache2-data_${APACHE_VER}_all.deb"
    download_deb "${UBUNTU_POOL}/a/apache2/apache2-utils_${APACHE_VER}_${ARCH}.deb"
    download_deb "${UBUNTU_POOL}/a/apache2/apache2-bin_${APACHE_VER}_${ARCH}.deb"
    download_deb "${UBUNTU_POOL}/a/apache2/apache2_${APACHE_VER}_${ARCH}.deb"
    download_deb "${UBUNTU_POOL}/a/apache2/apache2-dev_${APACHE_VER}_${ARCH}.deb"

    # --- libapr dev (requerido por apache2-dev para compilar mod_wsgi) ---
    download_deb "${UBUNTU_POOL}/a/apr/libapr1-dev_${APR_VER}_${ARCH}.deb"
    download_deb "${UBUNTU_POOL}/a/apr-util/libaprutil1-dev_${APRUTIL_VER}_${ARCH}.deb"

    # --- mod_wsgi fuente ---
    if [[ ! -f "$TMP_DIR/mod_wsgi-${MODWSGI_SRC_VER}.tar.gz" ]]; then
        log_info "Descargando mod_wsgi ${MODWSGI_SRC_VER} (fuente)..."
        wget -q --show-progress "$MODWSGI_SRC_URL" -O "$TMP_DIR/mod_wsgi-${MODWSGI_SRC_VER}.tar.gz"
        log_success "mod_wsgi-${MODWSGI_SRC_VER}.tar.gz"
    else
        log_info "Ya descargado: mod_wsgi-${MODWSGI_SRC_VER}.tar.gz"
    fi

    log_success "Todos los paquetes descargados"
}

# ==============================================================================
# PASO 3 – Instalar .deb en orden de dependencias
# ==============================================================================

install_packages() {
    log_step 3 5 "Instalando paquetes con dpkg"

    # Instalamos libs primero, luego apache, luego dev headers
    dpkg -i --force-confnew \
        "$TMP_DIR/libapr1t64_${APR_VER}_${ARCH}.deb" \
        "$TMP_DIR/libaprutil1t64_${APRUTIL_VER}_${ARCH}.deb" \
        "$TMP_DIR/libaprutil1-dbd-sqlite3_${APRUTIL_VER}_${ARCH}.deb" \
        "$TMP_DIR/libaprutil1-ldap_${APRUTIL_VER}_${ARCH}.deb" \
        "$TMP_DIR/liblua5.4-0_${LUA_VER}_${ARCH}.deb" \
        "$TMP_DIR/apache2-data_${APACHE_VER}_all.deb" \
        "$TMP_DIR/apache2-utils_${APACHE_VER}_${ARCH}.deb" \
        "$TMP_DIR/apache2-bin_${APACHE_VER}_${ARCH}.deb" \
        "$TMP_DIR/apache2_${APACHE_VER}_${ARCH}.deb" 2>&1 || true

    # apache2-dev tiene deps opcionales (debhelper) que no necesitamos para compilar.
    # Instalamos con --force-depends para obtener solo apxs2.
    dpkg -i --force-depends --force-confnew \
        "$TMP_DIR/libapr1-dev_${APR_VER}_${ARCH}.deb" \
        "$TMP_DIR/libaprutil1-dev_${APRUTIL_VER}_${ARCH}.deb" \
        "$TMP_DIR/apache2-dev_${APACHE_VER}_${ARCH}.deb" 2>&1 || true

    if command -v apache2 &>/dev/null; then
        log_success "Apache instalado: $(apache2 -v 2>&1 | head -1)"
    else
        log_error "Apache no se instaló correctamente"
        exit 1
    fi

    if ! command -v apxs2 &>/dev/null; then
        log_error "apxs2 no disponible — apache2-dev no se instaló"
        exit 1
    fi
    log_success "apxs2 disponible: $(which apxs2)"
}

# ==============================================================================
# PASO 4 – Compilar e instalar mod_wsgi desde fuente
# ==============================================================================

install_modwsgi() {
    log_step 4 5 "Compilando mod_wsgi ${MODWSGI_SRC_VER} con Python del venv"

    if [[ ! -d "$VENV_DIR" ]]; then
        log_error "Virtualenv no encontrado en $VENV_DIR"
        log_error "Crea el venv antes: python3 -m venv $VENV_DIR"
        exit 1
    fi

    local python_bin="$VENV_DIR/bin/python"
    local python_ver
    python_ver="$("$python_bin" --version 2>&1)"
    log_info "Usando: $python_bin ($python_ver)"

    # Extraer e instalar
    cd "$TMP_DIR"
    tar xzf "mod_wsgi-${MODWSGI_SRC_VER}.tar.gz"
    cd "mod_wsgi-${MODWSGI_SRC_VER}"

    "$python_bin" setup.py install 2>&1 | grep -E "(Installing|Installed|error|Error)" || true

    # Instalar el .so en el directorio de módulos de Apache
    "$VENV_DIR/bin/mod_wsgi-express" install-module

    local so_path
    so_path=$(find /usr/lib/apache2/modules/ -name "mod_wsgi*.so" | head -1)

    if [[ -n "$so_path" ]]; then
        log_success "mod_wsgi instalado: $so_path"
    else
        log_error "No se encontró mod_wsgi.so en /usr/lib/apache2/modules/"
        exit 1
    fi
}

# ==============================================================================
# PASO 5 – Habilitar mod_wsgi en Apache y verificar
# ==============================================================================

enable_and_verify() {
    log_step 5 5 "Habilitando mod_wsgi y verificando Apache"

    local so_path
    so_path=$(find /usr/lib/apache2/modules/ -name "mod_wsgi*.so" | head -1)
    local so_name
    so_name="$(basename "$so_path")"
    local load_conf="/etc/apache2/mods-available/wsgi.load"
    local wsgi_conf="/etc/apache2/mods-available/wsgi.conf"

    # Crear archivo .load para a2enmod
    if [[ ! -f "$load_conf" ]]; then
        echo "LoadModule wsgi_module /usr/lib/apache2/modules/${so_name}" > "$load_conf"
        log_info "Creado: $load_conf"
    fi

    # Crear archivo .conf con WSGIPythonHome
    if [[ ! -f "$wsgi_conf" ]]; then
        cat > "$wsgi_conf" <<EOF
<IfModule mod_wsgi.c>
    WSGIPythonHome ${VENV_DIR}
</IfModule>
EOF
        log_info "Creado: $wsgi_conf"
    fi

    a2enmod wsgi 2>/dev/null && log_success "mod_wsgi habilitado (a2enmod wsgi)"

    # Verificar sintaxis de configuración
    if apache2ctl configtest 2>&1 | grep -q "Syntax OK"; then
        log_success "Sintaxis de Apache: OK"
    else
        log_warn "Advertencia en configtest (puede ser normal sin VirtualHost configurado):"
        apache2ctl configtest 2>&1 || true
    fi

    echo ""
    echo -e "${GREEN}══════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  INSTALACIÓN COMPLETADA${NC}"
    echo -e "${GREEN}══════════════════════════════════════════════${NC}"
    echo ""
    echo "  Apache:    $(apache2 -v 2>&1 | head -1)"
    echo "  mod_wsgi:  $so_path"
    echo "  Python:    $("$VENV_DIR/bin/python" --version 2>&1)"
    echo ""
    echo "SIGUIENTE PASO:"
    echo "  sudo bash scripts/apache/setup_apache.sh"
    echo ""
}

# ==============================================================================
# MAIN
# ==============================================================================

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║   INSTALACIÓN APACHE + MOD_WSGI VIA .DEB             ║"
echo "║   Ubuntu 24.04 Noble — sin resolución de hostname    ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"

check_root
check_network
download_packages
install_packages
install_modwsgi
enable_and_verify
