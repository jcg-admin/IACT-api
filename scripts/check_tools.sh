#!/bin/bash

# ==============================================================================
# CHECK TOOLS - IACT API
# ==============================================================================
# Verifica que todas las herramientas del sistema requeridas para el desarrollo
# y despliegue del sistema IACT estén instaladas y con las versiones correctas.
#
# Uso:
#   bash scripts/check_tools.sh
#
# Requisitos:
#   - Python 3.11+
#   - PostgreSQL 16+ (cliente psql)
#   - MariaDB 11.4+ (cliente mysql)
#   - pip
# ==============================================================================

set -euo pipefail

# ------------------------------------------------------------------------------
# Colores
# ------------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ------------------------------------------------------------------------------
# Contadores
# ------------------------------------------------------------------------------
ERRORS=0
WARNINGS=0
OK_COUNT=0

# ------------------------------------------------------------------------------
# Funciones auxiliares
# ------------------------------------------------------------------------------
ok() {
    echo -e "  ${GREEN}[OK]${NC}   $1"
    OK_COUNT=$((OK_COUNT + 1))
}

warn() {
    echo -e "  ${YELLOW}[WARN]${NC}  $1"
    WARNINGS=$((WARNINGS + 1))
}

error() {
    echo -e "  ${RED}[ERROR]${NC} $1"
    ERRORS=$((ERRORS + 1))
}

section() {
    echo ""
    echo -e "${CYAN}──────────────────────────────────────────────────────${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}──────────────────────────────────────────────────────${NC}"
}

# Verifica que un binario existe
check_binary() {
    local name="$1"
    local cmd="$2"

    if command -v "$cmd" &>/dev/null; then
        local version
        version=$(${3:-"$cmd --version"} 2>&1 | head -1)
        ok "$name encontrado: $version"
        return 0
    else
        error "$name NO encontrado. Instalar: $name"
        return 1
    fi
}

# Verifica versión mínima de Python (major.minor)
check_python_version() {
    local required_major=$1
    local required_minor=$2

    if ! command -v python3 &>/dev/null; then
        error "python3 NO encontrado"
        return 1
    fi

    local version
    version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
    local major minor
    major=$(echo "$version" | cut -d. -f1)
    minor=$(echo "$version" | cut -d. -f2)

    if [ "$major" -gt "$required_major" ] || \
       ([ "$major" -eq "$required_major" ] && [ "$minor" -ge "$required_minor" ]); then
        ok "Python $version (requerido: $required_major.$required_minor+)"
    else
        error "Python $version — se requiere $required_major.$required_minor+"
        return 1
    fi
}

# Verifica que un paquete Python está instalado
check_python_package() {
    local package="$1"
    local import_name="${2:-$1}"

    if python3 -c "import $import_name" &>/dev/null; then
        local version
        version=$(python3 -c "import $import_name; v=getattr($import_name,'__version__',None) or getattr($import_name,'VERSION',None); print(v or 'version desconocida')" 2>/dev/null || echo "instalado")
        ok "$package ($version)"
    else
        warn "$package NO instalado (pip install $package)"
    fi
}

# Verifica versión mínima de PostgreSQL cliente
check_psql_version() {
    local required_major=$1

    if ! command -v psql &>/dev/null; then
        warn "psql (cliente PostgreSQL) NO encontrado — instalar postgresql-client"
        return 0
    fi

    local version
    version=$(psql --version 2>&1 | head -1)
    local major
    major=$(psql --version 2>&1 | grep -oP '\d+' | head -1)

    if [ "$major" -ge "$required_major" ]; then
        ok "psql $version (requerido: $required_major+)"
    else
        warn "psql $version — se recomienda $required_major+"
    fi
}

# Verifica versión de MariaDB/MySQL cliente
check_mysql_version() {
    if command -v mariadb &>/dev/null; then
        local version
        version=$(mariadb --version 2>&1 | head -1)
        ok "mariadb cliente: $version"
    elif command -v mysql &>/dev/null; then
        local version
        version=$(mysql --version 2>&1 | head -1)
        ok "mysql cliente: $version"
    else
        warn "mariadb/mysql cliente NO encontrado — instalar mariadb-client"
    fi
}

# ==============================================================================
# INICIO
# ==============================================================================
echo ""
echo -e "${BLUE}=====================================================================${NC}"
echo -e "${BLUE}  CHECK TOOLS - IACT API v2.2.1${NC}"
echo -e "${BLUE}=====================================================================${NC}"

# ------------------------------------------------------------------------------
# 1. Sistema Operativo
# ------------------------------------------------------------------------------
section "1. SISTEMA OPERATIVO"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    ok "SO: $NAME $VERSION_ID"
else
    ok "SO: $(uname -s) $(uname -r)"
fi

# ------------------------------------------------------------------------------
# 2. Python
# ------------------------------------------------------------------------------
section "2. PYTHON (requerido: 3.11+)"
check_python_version 3 11

if command -v python3 &>/dev/null; then
    PYTHON_PATH=$(command -v python3)
    ok "Ruta: $PYTHON_PATH"
fi

# pip
if command -v pip3 &>/dev/null || command -v pip &>/dev/null; then
    PIP_CMD=$(command -v pip3 2>/dev/null || command -v pip)
    PIP_VERSION=$($PIP_CMD --version 2>&1 | head -1)
    ok "pip: $PIP_VERSION"
else
    error "pip NO encontrado"
fi

# virtualenv / venv
if python3 -m venv --help &>/dev/null; then
    ok "venv (módulo estándar de Python)"
else
    warn "venv NO disponible — verificar instalación de Python"
fi

# ------------------------------------------------------------------------------
# 3. Bases de datos (clientes)
# ------------------------------------------------------------------------------
section "3. CLIENTES DE BASE DE DATOS"
check_psql_version 16
check_mysql_version

# ------------------------------------------------------------------------------
# 4. Paquetes Python del proyecto
# ------------------------------------------------------------------------------
section "4. PAQUETES PYTHON CORE"
check_python_package "Django" "django"
check_python_package "djangorestframework" "rest_framework"
check_python_package "djangorestframework-simplejwt" "rest_framework_simplejwt"
check_python_package "django-filter" "django_filters"
check_python_package "drf-spectacular" "drf_spectacular"
check_python_package "psycopg2" "psycopg2"
check_python_package "mysqlclient" "MySQLdb"
check_python_package "APScheduler" "apscheduler"
check_python_package "boto3" "boto3"
check_python_package "openpyxl" "openpyxl"
check_python_package "python-decouple" "decouple"
check_python_package "pytz" "pytz"
check_python_package "python-dateutil" "dateutil"

# ------------------------------------------------------------------------------
# 5. Herramientas de testing
# ------------------------------------------------------------------------------
section "5. HERRAMIENTAS DE TESTING"
check_python_package "pytest" "pytest"
check_python_package "pytest-django" "pytest_django"
check_python_package "pytest-cov" "pytest_cov"
check_python_package "factory-boy" "factory"
check_python_package "faker" "faker"
check_python_package "coverage" "coverage"

# ------------------------------------------------------------------------------
# 6. Herramientas de calidad de código
# ------------------------------------------------------------------------------
section "6. CALIDAD DE CÓDIGO (desarrollo)"
if command -v black &>/dev/null; then
    ok "black $(black --version 2>&1 | head -1)"
else
    warn "black NO encontrado (pip install black)"
fi

if command -v flake8 &>/dev/null; then
    ok "flake8 $(flake8 --version 2>&1 | head -1)"
else
    warn "flake8 NO encontrado (pip install flake8)"
fi

if command -v isort &>/dev/null; then
    ok "isort $(isort --version 2>&1 | head -1)"
else
    warn "isort NO encontrado (pip install isort)"
fi

if command -v mypy &>/dev/null; then
    ok "mypy $(mypy --version 2>&1 | head -1)"
else
    warn "mypy NO encontrado (pip install mypy)"
fi

# ------------------------------------------------------------------------------
# 7. Herramientas del sistema
# ------------------------------------------------------------------------------
section "7. HERRAMIENTAS DEL SISTEMA"
check_binary "git" "git" "git --version"
check_binary "bash" "bash" "bash --version"
check_binary "curl" "curl" "curl --version"

# Apache (solo en producción)
if command -v apache2 &>/dev/null || command -v httpd &>/dev/null; then
    APACHE_CMD=$(command -v apache2 2>/dev/null || command -v httpd)
    ok "Apache: $($APACHE_CMD -v 2>&1 | head -1)"
else
    warn "Apache NO encontrado (requerido en producción)"
fi

# ------------------------------------------------------------------------------
# 8. Variables de entorno
# ------------------------------------------------------------------------------
section "8. VARIABLES DE ENTORNO (.env)"
if [ -f ".env" ]; then
    ok ".env encontrado"
    # Verificar variables críticas sin exponer valores
    for var in SECRET_KEY DEBUG ALLOWED_HOSTS DATABASE_URL LEGACY_DATABASE_URL SESSION_ENGINE; do
        if grep -q "^${var}=" .env 2>/dev/null; then
            ok "  $var configurado"
        else
            warn "  $var NO configurado en .env"
        fi
    done
elif [ -f ".env.example" ]; then
    warn ".env NO encontrado — copiar .env.example a .env y configurar"
else
    warn ".env y .env.example NO encontrados"
fi

# ------------------------------------------------------------------------------
# 9. Estructura del proyecto
# ------------------------------------------------------------------------------
section "9. ESTRUCTURA DEL PROYECTO"
if [ -f "manage.py" ]; then
    ok "manage.py encontrado (ejecutar desde callcentersite/)"
else
    warn "manage.py NO encontrado — ejecutar desde callcentersite/"
fi

if [ -d "callcentersite" ] || [ -d "apps" ]; then
    ok "Directorio del proyecto encontrado"
else
    warn "Directorio callcentersite/ o apps/ NO encontrado"
fi

# ==============================================================================
# RESUMEN
# ==============================================================================
echo ""
echo -e "${BLUE}=====================================================================${NC}"
echo -e "${BLUE}  RESUMEN${NC}"
echo -e "${BLUE}=====================================================================${NC}"
echo -e "  ${GREEN}OK:${NC}           $OK_COUNT"
echo -e "  ${YELLOW}Advertencias:${NC} $WARNINGS"
echo -e "  ${RED}Errores:${NC}      $ERRORS"
echo ""

if [ "$ERRORS" -eq 0 ] && [ "$WARNINGS" -eq 0 ]; then
    echo -e "  ${GREEN}[LISTO]${NC} Todas las herramientas están instaladas correctamente."
    echo ""
    exit 0
elif [ "$ERRORS" -eq 0 ]; then
    echo -e "  ${YELLOW}[ADVERTENCIA]${NC} Hay advertencias. Revisar herramientas opcionales."
    echo ""
    exit 0
else
    echo -e "  ${RED}[INCOMPLETO]${NC} Faltan herramientas requeridas. Revisar errores arriba."
    echo ""
    echo "  PASOS SUGERIDOS:"
    echo "    1. Instalar herramientas faltantes"
    echo "    2. Crear entorno virtual: python3 -m venv venv"
    echo "    3. Activar entorno:       source venv/bin/activate"
    echo "    4. Instalar dependencias: pip install -r requirements/development.txt"
    echo "    5. Ejecutar de nuevo:     bash scripts/check_tools.sh"
    echo ""
    exit 1
fi
