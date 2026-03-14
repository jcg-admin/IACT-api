#!/bin/bash

# Script de verificacion de implementacion del Sistema de Navegacion v3.0.0
# Fecha: 2026-01-16

echo "======================================================================"
echo "  VERIFICACION DE IMPLEMENTACION - SISTEMA DE NAVEGACION v3.0.0"
echo "======================================================================"
echo ""

ERRORS=0
WARNINGS=0

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Funciones auxiliares
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}[OK]${NC} $1"
        return 0
    else
        echo -e "${RED}[ERROR]${NC} Archivo no encontrado: $1"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}[OK]${NC} $1"
        return 0
    else
        echo -e "${YELLOW}[WARN]${NC} Directorio no encontrado: $1"
        WARNINGS=$((WARNINGS + 1))
        return 1
    fi
}

echo "1. VERIFICANDO MANAGEMENT COMMAND"
echo "-------------------------------------------------------------------"
check_file "apps/core/management/__init__.py"
check_file "apps/core/management/commands/__init__.py"
check_file "apps/core/management/commands/create_modules.py"
echo ""

echo "2. VERIFICANDO NAVIGATION SYSTEM"
echo "-------------------------------------------------------------------"
check_file "apps/core/navigation/__init__.py"
check_file "apps/core/navigation/builders.py"
check_file "apps/core/navigation/views.py"
check_file "apps/core/navigation/urls.py"
echo ""

echo "3. VERIFICANDO MODELO USER"
echo "-------------------------------------------------------------------"
check_file "apps/users/models.py"
if [ -f "apps/users/models.py.backup" ]; then
    echo -e "${GREEN}[OK]${NC} Backup creado: apps/users/models.py.backup"
fi

# Verificar que el modelo tenga los campos nuevos
if grep -q "avatar" apps/users/models.py; then
    echo -e "${GREEN}[OK]${NC} Campo 'avatar' encontrado en User model"
else
    echo -e "${RED}[ERROR]${NC} Campo 'avatar' NO encontrado en User model"
    ERRORS=$((ERRORS + 1))
fi

if grep -q "get_avatar_url" apps/users/models.py; then
    echo -e "${GREEN}[OK]${NC} Metodo 'get_avatar_url()' encontrado"
else
    echo -e "${RED}[ERROR]${NC} Metodo 'get_avatar_url()' NO encontrado"
    ERRORS=$((ERRORS + 1))
fi

if grep -q "get_functions" apps/users/models.py; then
    echo -e "${GREEN}[OK]${NC} Metodo 'get_functions()' encontrado"
else
    echo -e "${RED}[ERROR]${NC} Metodo 'get_functions()' NO encontrado"
    ERRORS=$((ERRORS + 1))
fi
echo ""

echo "4. VERIFICANDO VISTAS DE AVATAR"
echo "-------------------------------------------------------------------"
check_file "apps/users/views.py"

if grep -q "upload_avatar_view" apps/users/views.py; then
    echo -e "${GREEN}[OK]${NC} Vista 'upload_avatar_view' encontrada"
else
    echo -e "${RED}[ERROR]${NC} Vista 'upload_avatar_view' NO encontrada"
    ERRORS=$((ERRORS + 1))
fi

if grep -q "delete_avatar_view" apps/users/views.py; then
    echo -e "${GREEN}[OK]${NC} Vista 'delete_avatar_view' encontrada"
else
    echo -e "${RED}[ERROR]${NC} Vista 'delete_avatar_view' NO encontrada"
    ERRORS=$((ERRORS + 1))
fi

if grep -q "get_user_profile_view" apps/users/views.py; then
    echo -e "${GREEN}[OK]${NC} Vista 'get_user_profile_view' encontrada"
else
    echo -e "${RED}[ERROR]${NC} Vista 'get_user_profile_view' NO encontrada"
    ERRORS=$((ERRORS + 1))
fi
echo ""

echo "5. VERIFICANDO URLs"
echo "-------------------------------------------------------------------"
check_file "config/urls.py"

if grep -q "apps.core.navigation.urls" config/urls.py; then
    echo -e "${GREEN}[OK]${NC} URLs de navegacion agregadas"
else
    echo -e "${RED}[ERROR]${NC} URLs de navegacion NO agregadas"
    ERRORS=$((ERRORS + 1))
fi

check_file "apps/users/urls.py"

if grep -q "upload-avatar" apps/users/urls.py; then
    echo -e "${GREEN}[OK]${NC} URLs de avatar agregadas"
else
    echo -e "${RED}[ERROR]${NC} URLs de avatar NO agregadas"
    ERRORS=$((ERRORS + 1))
fi
echo ""

echo "6. VERIFICANDO ESTRUCTURA DE DIRECTORIOS"
echo "-------------------------------------------------------------------"
check_dir "static/icons"
check_dir "static/icons/menu"
check_dir "static/icons/submenu"
check_dir "static/icons/defaults"
check_dir "media/profiles"
check_dir "modules"
echo ""

echo "7. VERIFICANDO CONFIGURACION"
echo "-------------------------------------------------------------------"
check_file "config/settings/base.py"

if grep -q "ALLOWED_IMAGE_EXTENSIONS" config/settings/base.py; then
    echo -e "${GREEN}[OK]${NC} ALLOWED_IMAGE_EXTENSIONS configurado"
else
    echo -e "${YELLOW}[WARN]${NC} ALLOWED_IMAGE_EXTENSIONS NO configurado"
    WARNINGS=$((WARNINGS + 1))
fi

if grep -q "MAX_AVATAR_SIZE" config/settings/base.py; then
    echo -e "${GREEN}[OK]${NC} MAX_AVATAR_SIZE configurado"
else
    echo -e "${YELLOW}[WARN]${NC} MAX_AVATAR_SIZE NO configurado"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

echo "8. VERIFICANDO .gitkeep"
echo "-------------------------------------------------------------------"
check_file "static/icons/menu/.gitkeep"
check_file "static/icons/submenu/.gitkeep"
check_file "static/icons/defaults/.gitkeep"
check_file "media/profiles/.gitkeep"
echo ""

echo "======================================================================"
echo "  RESUMEN DE VERIFICACION"
echo "======================================================================"
echo -e "Errores:      ${RED}${ERRORS}${NC}"
echo -e "Advertencias: ${YELLOW}${WARNINGS}${NC}"
echo ""

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}[EXITO]${NC} Implementacion completada correctamente"
    echo ""
    echo "SIGUIENTES PASOS:"
    echo "1. Crear migraciones: python manage.py makemigrations users"
    echo "2. Aplicar migraciones: python manage.py migrate"
    echo "3. Generar modulos: python manage.py create_modules --verbose"
    echo "4. Poblar iconos en static/icons/"
    echo "5. Crear metadata de navegacion en apps/{app}/navigation/"
    echo ""
    exit 0
else
    echo -e "${RED}[FALLO]${NC} Se encontraron errores en la implementacion"
    echo "Por favor revisa los errores arriba y corrige antes de continuar"
    echo ""
    exit 1
fi
