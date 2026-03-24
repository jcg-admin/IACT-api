#!/bin/bash

# Script de verificacion de herramientas requeridas - IACT Call Center System
# Compliance: CNST v2.2.1
# Date: 2026-03-14

echo "======================================================================"
echo "  CHECK TOOLS - IACT Call Center System"
echo "  Verifying required tools and dependencies"
echo "======================================================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

check_ok() {
    echo -e "${GREEN}[OK]${NC}   $1"
}

check_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    WARNINGS=$((WARNINGS + 1))
}

check_err() {
    echo -e "${RED}[FAIL]${NC} $1"
    ERRORS=$((ERRORS + 1))
}

check_version() {
    local name="$1"
    local cmd="$2"
    local version_flag="$3"
    local min_version="$4"

    if ! command -v "$cmd" &>/dev/null; then
        check_err "$name not found (required: $min_version+)"
        return 1
    fi
    local version
    version=$($cmd $version_flag 2>&1 | head -1)
    check_ok "$name found: $version"
    return 0
}

# ----------------------------------------------------------------------
echo -e "${BLUE}1. RUNTIME${NC}"
echo "----------------------------------------------------------------------"

# Python 3.11+
if command -v python3 &>/dev/null; then
    PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
    PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
    if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 11 ]; then
        check_ok "Python $PY_VER (>= 3.11 required)"
    else
        check_err "Python $PY_VER found, but >= 3.11 required"
    fi
else
    check_err "Python 3 not found"
fi

# pip
if command -v pip3 &>/dev/null; then
    PIP_VER=$(pip3 --version 2>&1 | awk '{print $2}')
    check_ok "pip $PIP_VER"
elif command -v pip &>/dev/null; then
    PIP_VER=$(pip --version 2>&1 | awk '{print $2}')
    check_ok "pip $PIP_VER"
else
    check_err "pip not found"
fi

echo ""

# ----------------------------------------------------------------------
echo -e "${BLUE}2. DATABASES${NC}"
echo "----------------------------------------------------------------------"

# PostgreSQL client (psql) - primary DB
if command -v psql &>/dev/null; then
    PSQL_VER=$(psql --version 2>&1)
    check_ok "$PSQL_VER"
else
    check_err "psql (PostgreSQL client) not found - required for iact_analytics"
fi

# MariaDB/MySQL client - ivr_legacy READ-ONLY
if command -v mysql &>/dev/null; then
    MYSQL_VER=$(mysql --version 2>&1)
    check_ok "$MYSQL_VER"
elif command -v mariadb &>/dev/null; then
    MARIADB_VER=$(mariadb --version 2>&1)
    check_ok "$MARIADB_VER"
else
    check_warn "mysql/mariadb client not found - required for ivr_legacy (READ-ONLY)"
fi

echo ""

# ----------------------------------------------------------------------
echo -e "${BLUE}3. VERSION CONTROL${NC}"
echo "----------------------------------------------------------------------"

check_version "Git" "git" "--version" "2.0"

echo ""

# ----------------------------------------------------------------------
echo -e "${BLUE}4. WEB SERVER${NC}"
echo "----------------------------------------------------------------------"

if command -v apache2 &>/dev/null; then
    APACHE_VER=$(apache2 -v 2>&1 | head -1)
    check_ok "$APACHE_VER"
elif command -v httpd &>/dev/null; then
    HTTPD_VER=$(httpd -v 2>&1 | head -1)
    check_ok "$HTTPD_VER"
else
    check_warn "Apache 2.4 not found (required for production deployment)"
fi

echo ""

# ----------------------------------------------------------------------
echo -e "${BLUE}5. PYTHON PACKAGES (requirements/base.txt)${NC}"
echo "----------------------------------------------------------------------"

REQUIRED_PACKAGES=(
    "Django"
    "djangorestframework"
    "django-filter"
    "drf-spectacular"
    "djangorestframework-simplejwt"
    "psycopg2-binary"
    "mysqlclient"
    "APScheduler"
    "boto3"
    "openpyxl"
    "pytz"
    "python-dateutil"
    "python-decouple"
)

PIP_CMD=""
if command -v pip3 &>/dev/null; then
    PIP_CMD="pip3"
elif command -v pip &>/dev/null; then
    PIP_CMD="pip"
fi

if [ -n "$PIP_CMD" ]; then
    INSTALLED_PKGS=$($PIP_CMD list --format=columns 2>/dev/null)
    for pkg in "${REQUIRED_PACKAGES[@]}"; do
        # Case-insensitive, handle both hyphen and underscore
        pkg_key=$(echo "$pkg" | tr '[:upper:]' '[:lower:]' | tr '-' '_')
        if echo "$INSTALLED_PKGS" | awk '{print tolower($1)}' | tr '-' '_' | grep -q "^${pkg_key}$"; then
            version=$(echo "$INSTALLED_PKGS" | awk 'tolower($1) == "'$pkg_key'" || tolower($1) == "'$(echo $pkg_key | tr '_' '-')'" {print $2}' | head -1)
            check_ok "$pkg $version"
        else
            check_warn "$pkg not installed (run: pip install -r requirements/base.txt)"
        fi
    done
else
    check_err "pip not available - cannot check Python packages"
fi

echo ""

# ----------------------------------------------------------------------
echo -e "${BLUE}6. TESTING TOOLS${NC}"
echo "----------------------------------------------------------------------"

if command -v pytest &>/dev/null; then
    PYTEST_VER=$(pytest --version 2>&1 | head -1)
    check_ok "$PYTEST_VER"
else
    check_warn "pytest not found (install: pip install -r requirements/testing.txt)"
fi

echo ""

# ----------------------------------------------------------------------
echo "======================================================================"
echo "  SUMMARY"
echo "======================================================================"
echo -e "  Errors:   ${RED}${ERRORS}${NC}"
echo -e "  Warnings: ${YELLOW}${WARNINGS}${NC}"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}[PASS]${NC} All required tools are available."
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}[PASS with warnings]${NC} Core tools present. Install missing optional tools for full functionality."
else
    echo -e "${RED}[FAIL]${NC} Missing required tools. Please install them before proceeding."
    echo ""
    echo "  Quick install:"
    echo "    pip install -r requirements/development.txt"
fi

echo ""
exit $ERRORS
