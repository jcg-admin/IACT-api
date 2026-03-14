#!/bin/bash

# Script para ejecutar tests del Sistema de Navegacion v3.0.0
# Fecha: 2026-01-16

echo "======================================================================"
echo "  TESTS - SISTEMA DE NAVEGACION v3.0.0"
echo "======================================================================"
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Verificar que estamos en el directorio correcto
if [ ! -f "manage.py" ]; then
    echo -e "${RED}[ERROR]${NC} Debe ejecutar este script desde el directorio del proyecto (callcentersite/)"
    exit 1
fi

# Función para ejecutar tests
run_tests() {
    local test_file=$1
    local test_name=$2
    
    echo -e "${BLUE}[EJECUTANDO]${NC} $test_name"
    echo "Archivo: $test_file"
    echo ""
    
    pytest "$test_file" -v --tb=short
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}[EXITO]${NC} $test_name"
    else
        echo -e "${RED}[FALLO]${NC} $test_name"
        return 1
    fi
    
    echo ""
    echo "----------------------------------------------------------------------"
    echo ""
}

# Menú principal
echo "Seleccione una opción:"
echo ""
echo "  1) Ejecutar TODOS los tests"
echo "  2) Tests de MenuBuilder y MenuValidator"
echo "  3) Tests de API Navigation"
echo "  4) Tests de User Model"
echo "  5) Tests de API Avatar"
echo "  6) Tests de API Profile"
echo "  7) Tests con cobertura (coverage)"
echo "  8) Tests rápidos (sin verbose)"
echo "  9) Salir"
echo ""
read -p "Opción: " option

case $option in
    1)
        echo ""
        echo "======================================================================"
        echo "  EJECUTANDO TODOS LOS TESTS"
        echo "======================================================================"
        echo ""
        
        run_tests "tests/unit/core/test_navigation_builders.py" "MenuBuilder y MenuValidator"
        run_tests "tests/unit/core/test_navigation_views.py" "API Navigation"
        run_tests "tests/unit/users/test_user_model.py" "User Model Extendido"
        run_tests "tests/unit/users/test_avatar_api.py" "API Avatar"
        run_tests "tests/unit/users/test_profile_api.py" "API Profile"
        
        echo ""
        echo "======================================================================"
        echo "  RESUMEN"
        echo "======================================================================"
        pytest tests/unit/core/ tests/unit/users/ --tb=no -q
        ;;
    
    2)
        run_tests "tests/unit/core/test_navigation_builders.py" "MenuBuilder y MenuValidator"
        ;;
    
    3)
        run_tests "tests/unit/core/test_navigation_views.py" "API Navigation"
        ;;
    
    4)
        run_tests "tests/unit/users/test_user_model.py" "User Model Extendido"
        ;;
    
    5)
        run_tests "tests/unit/users/test_avatar_api.py" "API Avatar"
        ;;
    
    6)
        run_tests "tests/unit/users/test_profile_api.py" "API Profile"
        ;;
    
    7)
        echo ""
        echo "======================================================================"
        echo "  TESTS CON COBERTURA"
        echo "======================================================================"
        echo ""
        
        pytest tests/unit/core/ tests/unit/users/ \
            --cov=apps.core.navigation \
            --cov=apps.users.models \
            --cov=apps.users.views \
            --cov-report=term-missing \
            --cov-report=html \
            -v
        
        echo ""
        echo -e "${GREEN}[INFO]${NC} Reporte HTML generado en: htmlcov/index.html"
        ;;
    
    8)
        echo ""
        echo "======================================================================"
        echo "  TESTS RAPIDOS"
        echo "======================================================================"
        echo ""
        
        pytest tests/unit/core/ tests/unit/users/ -q --tb=no
        ;;
    
    9)
        echo "Saliendo..."
        exit 0
        ;;
    
    *)
        echo -e "${RED}[ERROR]${NC} Opción inválida"
        exit 1
        ;;
esac

echo ""
echo "======================================================================"
echo "  TESTS COMPLETADOS"
echo "======================================================================"
