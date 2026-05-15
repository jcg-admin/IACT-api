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
    
    # Crear funciones usando el catálogo existente o creando con Module
    from apps.access.models import Module
    default_module, _ = Module.objects.get_or_create(
        code='USR', defaults={'name': 'Usuarios', 'order': 99}
    )
    func_view, _ = Function.objects.get_or_create(
        code='USR_VIEW',
        defaults={'name': 'Ver Usuarios', 'module': default_module,
                  'permission_django': 'users.view'}
    )
    func_create, _ = Function.objects.get_or_create(
        code='USR_CREATE',
        defaults={'name': 'Crear Usuarios', 'module': default_module,
                  'permission_django': 'users.create'}
    )
    func_edit, _ = Function.objects.get_or_create(
        code='USR_EDIT',
        defaults={'name': 'Editar Usuarios', 'module': default_module,
                  'permission_django': 'users.edit'}
    )
    
    # Asignar funciones al usuario
    UserPermission.objects.create(
        user=user,
        function=func_view,
    )
    UserPermission.objects.create(
        user=user,
        function=func_create,
    )
    UserPermission.objects.create(
        user=user,
        function=func_edit,
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
#       response = admin_client.get('/api/users/')
#       assert response.status_code == 200
# ============================================================================


# ─── Fix de migraciones para la BD de producción ─────────────────────────────
# Las columnas de access_group.is_active, reports.ExportJob.id (uuid) y
# users.PasswordHistory ya existen en iact_analytics por evolución manual
# del schema anterior a las migraciones correspondientes. Si esas migraciones
# se ejecutan contra iact_analytics, fallan con "column already exists".
#
# Solución: monkey-patch del executor de migraciones que aplica fake SOLO
# cuando la conexión apunta a la BD de producción (iact_analytics).
# La BD de test (test_iact_analytics) se crea limpia desde cero — no tiene
# columnas preexistentes, así que sus migraciones deben ejecutarse normalmente.
#
# Criterio de discriminación: la BD de test siempre comienza con "test_".

import django.db.migrations.executor as _executor_mod
_orig_run_migration = _executor_mod.MigrationExecutor.apply_migration

_FAKE_MIGRATIONS = {
    ('access',      '0007_fase2_access_group_and_function_menu'),
    ('access',      '0008_std008_fase2_related_names'),
    ('access',      '0009_fase4_exceptionalpermisos_canonical'),
    ('reports',     '0004_fase3_exportjob_canonical'),
    ('reports',     '0005_fase4_scheduledreport_canonical'),
    ('reports',     '0006_fase5_savedfilter_savedview_canonical'),
    ('users',       '0002_fase1_user_canonical_fields'),
    ('users',       '0003_fase1_password_history'),
    ('users',       '0004_fase2_user_admin_fields'),
}

def _patched_apply_migration(self, state, migration, fake=False, fake_initial=False):
    key = (migration.app_label, migration.name)
    if key in _FAKE_MIGRATIONS:
        # Solo forzar fake en la BD de producción.
        # En test_iact_analytics las migraciones deben correr para que el
        # schema quede correcto (constraints, nullable, etc.).
        db_name = self.connection.settings_dict.get('NAME', '')
        if not db_name.startswith('test_'):
            fake = True
    return _orig_run_migration(self, state, migration, fake=fake, fake_initial=fake_initial)

_executor_mod.MigrationExecutor.apply_migration = _patched_apply_migration
