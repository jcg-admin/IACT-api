"""Test rápido Fase 1 - User model"""
import pytest
import uuid
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_create_user_with_profile_and_settings():
    """
    Crear usuario verifica campos básicos del modelo User.

    UserProfile y UserSettings fueron eliminados en FASE 4.
    La funcionalidad de perfil está integrada en User (avatar, first_name, last_name).
    La configuración se gestiona via /api/users/settings/ (cache-backed).
    """
    u = uuid.uuid4().hex[:6]
    user = User.objects.create_user(
        username=f'testuser_{u}',
        email=f'test_{u}@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User',
    )

    assert user.id is not None
    assert user.username == f'testuser_{u}'
    assert user.email == f'test_{u}@example.com'
    assert user.get_full_name() == 'Test User'
    assert user.is_active is True

    # Perfil integrado: campo avatar disponible directamente en User
    assert hasattr(user, 'avatar')

    # Métodos RBAC disponibles
    assert callable(getattr(user, 'get_functions', None))
    assert callable(getattr(user, 'has_function_by_code', None))
    assert callable(getattr(user, 'has_any_function', None))
    assert callable(getattr(user, 'has_all_functions', None))
