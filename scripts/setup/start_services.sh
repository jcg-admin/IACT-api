#!/usr/bin/env bash
# =============================================================================
# start_services.sh — Arrancar PostgreSQL y MariaDB para desarrollo local
# =============================================================================
# Uso:
#   bash scripts/setup/start_services.sh
#
# Prerrequisito: IACT-db bootstrap completado al menos una vez.
#   cd /ruta/a/IACT-db && sudo bash bootstrap.sh --no-adminer
#
# Este script NO instala los servicios. Solo los arranca si ya están
# instalados y verifica que responden.
# =============================================================================

set -euo pipefail

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}  OK${NC}  $*"; }
fail() { echo -e "${RED}  FAIL${NC} $*"; }
warn() { echo -e "${YELLOW}  WARN${NC} $*"; }

echo ""
echo "IACT-api — Arranque de servicios de BD"
echo "======================================="
echo ""

# --- PostgreSQL ---
echo "PostgreSQL:"
if pg_isready -h 127.0.0.1 -p 5432 -q 2>/dev/null; then
    ok "PostgreSQL corriendo en 127.0.0.1:5432"
else
    warn "PostgreSQL no responde — intentando arrancar..."
    if command -v pg_ctlcluster &>/dev/null; then
        pg_ctlcluster 16 main start 2>/dev/null \
            && ok "PostgreSQL iniciado" \
            || fail "No se pudo iniciar PostgreSQL"
    elif command -v systemctl &>/dev/null; then
        systemctl start postgresql 2>/dev/null \
            && ok "PostgreSQL iniciado" \
            || fail "No se pudo iniciar PostgreSQL"
    else
        fail "pg_ctlcluster no encontrado. Instalar IACT-db primero:"
        echo "       cd /ruta/a/IACT-db && sudo bash bootstrap.sh --no-adminer"
        exit 1
    fi
fi

# Verificar usuario django_user en PostgreSQL
if pg_isready -h 127.0.0.1 -p 5432 -q 2>/dev/null; then
    if PGPASSWORD=django_pass psql -h 127.0.0.1 -U django_user \
            -d iact_analytics -c "SELECT 1;" &>/dev/null 2>&1; then
        ok "django_user conecta a iact_analytics"
    else
        warn "django_user no puede conectar — ejecutar setup:"
        echo "       cd /ruta/a/IACT-db && sudo bash provisioners/postgres/setup.sh"
    fi
fi

echo ""

# --- MariaDB ---
echo "MariaDB:"
if mysql --socket=/run/mysqld/mysqld.sock \
         -u django_user -pdjango_pass -e "SELECT 1;" &>/dev/null 2>&1; then
    ok "MariaDB corriendo en /run/mysqld/mysqld.sock"
else
    warn "MariaDB no responde — intentando arrancar..."
    if command -v systemctl &>/dev/null && systemctl is-enabled mariadb &>/dev/null; then
        systemctl start mariadb 2>/dev/null \
            && ok "MariaDB iniciado" \
            || fail "No se pudo iniciar MariaDB"
    elif [ -x /usr/sbin/mariadbd ]; then
        # Entorno sandbox: arrancar directamente (mismo patrón que conftest.py)
        warn "Arrancando mariadbd directamente (entorno sandbox)..."
        bash /tmp/mariadb_ensure.sh 2>/dev/null \
            && ok "MariaDB iniciado vía mariadb_ensure.sh" \
            || fail "No se pudo iniciar MariaDB. Revisa /tmp/mdb_startup.log"
    else
        fail "mariadbd no encontrado. Instalar IACT-db primero:"
        echo "       cd /ruta/a/IACT-db && sudo bash bootstrap.sh --no-adminer"
        exit 1
    fi
fi

echo ""

# --- libmysqlclient.so.21 ---
echo "libmysqlclient.so.21:"
if python3 scripts/setup/make_libmysqlclient_stub.py &>/dev/null 2>&1; then
    if /tmp/references/IACT-api/venv/bin/python -c "import MySQLdb" &>/dev/null 2>&1; then
        ok "MySQLdb importa correctamente"
    else
        fail "MySQLdb no importa — ejecutar: sudo python3 scripts/setup/make_libmysqlclient_stub.py"
    fi
fi

echo ""
echo "Verificación final:"
echo ""

# Django check
cd "$(dirname "$0")/../../callcentersite" || exit 1

VENV_PYTHON="$(dirname "$0")/../../venv/bin/python"
if [ -x "$VENV_PYTHON" ]; then
    "$VENV_PYTHON" manage.py check --database default 2>&1 \
        | grep -E "System check|issues" \
        | head -2 \
        && ok "Django check default (PostgreSQL)" \
        || fail "Django check default falló"

    "$VENV_PYTHON" manage.py check --database ivr 2>&1 \
        | grep -E "System check|issues" \
        | head -2 \
        && ok "Django check ivr (MariaDB)" \
        || fail "Django check ivr falló"
else
    warn "venv no encontrado en ../../venv/ — omitiendo Django check"
fi

echo ""
echo "Para correr los tests:"
echo "  venv/bin/pytest tests/unit/ --tb=no -q"
echo "  venv/bin/pytest tests/integration/ --tb=no -q"
echo ""
