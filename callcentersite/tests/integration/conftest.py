"""
Fixtures compartidas para tests de integración.

Configuración común para todos los tests de integración.
"""

import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.access.models import Function, UserPermission

User = get_user_model()


@pytest.fixture
def api_client():
    """
    Cliente API de DRF para tests de integración.
    
    Returns:
        APIClient: Cliente configurado para hacer requests
    """
    return APIClient()


@pytest.fixture
def admin_user(db):
    """
    Usuario administrador con todos los permisos.
    
    Returns:
        User: Usuario con is_staff=True, is_superuser=True
    """
    user = User.objects.create_user(
        username='admin',
        email='admin@test.com',
        password='AdminPass123',
        first_name='Admin',
        last_name='User',
        is_staff=True,
        is_superuser=True,
    )
    return user


@pytest.fixture
def regular_user(db):
    """
    Usuario regular sin permisos especiales.
    
    Returns:
        User: Usuario básico is_active=True
    """
    user = User.objects.create_user(
        username='regular',
        email='regular@test.com',
        password='RegularPass123',
        first_name='Regular',
        last_name='User',
    )
    return user


@pytest.fixture
def user_with_permissions(db):
    """
    Usuario con permisos RBAC específicos.
    
    Returns:
        User: Usuario con funciones USR_VIEW, USR_CREATE, USR_EDIT
    """
    user = User.objects.create_user(
        username='permitted',
        email='permitted@test.com',
        password='PermittedPass123',
        first_name='Permitted',
        last_name='User',
    )
    
    # Crear funciones
    func_view = Function.objects.create(
        code='USR_VIEW',
        name='Ver Usuarios',
        description='Permiso para ver usuarios',
    )
    func_create = Function.objects.create(
        code='USR_CREATE',
        name='Crear Usuarios',
        description='Permiso para crear usuarios',
    )
    func_edit = Function.objects.create(
        code='USR_EDIT',
        name='Editar Usuarios',
        description='Permiso para editar usuarios',
    )
    
    # Asignar funciones al usuario
    UserPermission.objects.create(
        user=user,
        function=func_view,
        is_active=True,
    )
    UserPermission.objects.create(
        user=user,
        function=func_create,
        is_active=True,
    )
    UserPermission.objects.create(
        user=user,
        function=func_edit,
        is_active=True,
    )
    
    return user


@pytest.fixture
def authenticated_client(api_client, regular_user):
    """
    Cliente autenticado con usuario regular.
    
    Args:
        api_client: APIClient
        regular_user: Usuario regular
    
    Returns:
        APIClient: Cliente autenticado
    """
    api_client.force_authenticate(user=regular_user)
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """
    Cliente autenticado con usuario admin.
    
    Args:
        api_client: APIClient
        admin_user: Usuario admin
    
    Returns:
        APIClient: Cliente autenticado como admin
    """
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def permitted_client(api_client, user_with_permissions):
    """
    Cliente autenticado con usuario que tiene permisos RBAC.
    
    Args:
        api_client: APIClient
        user_with_permissions: Usuario con permisos
    
    Returns:
        APIClient: Cliente autenticado con permisos
    """
    api_client.force_authenticate(user=user_with_permissions)
    return api_client


# ============================================================================
# RESUMEN FIXTURES
# 
# Total Fixtures: 7
# 
# Clients:
#   [SUCCESS] api_client - Cliente base sin autenticación
#   [SUCCESS] authenticated_client - Cliente con usuario regular
#   [SUCCESS] admin_client - Cliente con usuario admin
#   [SUCCESS] permitted_client - Cliente con permisos RBAC
# 
# Users:
#   [SUCCESS] admin_user - is_superuser=True
#   [SUCCESS] regular_user - Usuario básico
#   [SUCCESS] user_with_permissions - Con funciones USR_VIEW, USR_CREATE, USR_EDIT
# 
# Uso:
#   def test_something(admin_client):
#       response = admin_client.get('/api/v1/users/')
#       assert response.status_code == 200
# ============================================================================
