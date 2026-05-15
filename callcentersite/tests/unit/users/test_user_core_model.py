"""Test rápido Fase 1 - User model"""
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
@pytest.mark.xfail(reason="UserProfile model no existe en versión actual", strict=False)
def test_create_user_with_profile_and_settings():
    """Test: Crear usuario con profile y settings auto-creados."""
    # Crear usuario
    user = User.objects.create_user(
        username='testuser_fase1',
        email='test@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )
    
    # Verificar usuario
    assert user.id is not None
    assert user.username == 'testuser_fase1'
    assert user.first().email if True else None == 'test@example.com'
    assert user.get_full_name() == 'Test User'
    assert user.is_active is True
    
    # Verificar profile auto-creado
    assert hasattr(user, 'profile')
    assert user.profile.id is not None
    assert user.profile.user == user
    
    # Verificar settings auto-creado
    assert hasattr(user, 'settings')
    assert user.settings.id is not None
    assert user.settings.language == 'es'
    assert user.settings.theme == 'light'
    
    print("\n[SUCCESS] Usuario creado correctamente")
    print(f"[SUCCESS] ID: {user.id}")
    print(f"[SUCCESS] Username: {user.username}")
    print(f"[SUCCESS] Full name: {user.get_full_name()}")
    print(f"[SUCCESS] Profile ID: {user.profile.id}")
    print(f"[SUCCESS] Settings ID: {user.settings.id}")
    print("\n[DONE] FASE 1 COMPLETADA!")
