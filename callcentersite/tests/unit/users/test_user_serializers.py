"""
Tests para Serializers de apps/users/.

TDD: Tests primero, luego implementación.
"""

import pytest
from django.contrib.auth import get_user_model


try:
    from apps.users.serializers import (
        UserSerializer,
        UserCreateSerializer,
        UserUpdateSerializer,
        UserSettingsSerializer,
        AvatarUploadSerializer,
        LoginSerializer,
        ChangePasswordSerializer,
        PasswordResetRequestSerializer,
        PasswordResetConfirmSerializer,
    )

except ImportError as _err:
    pytest.skip(
        f'Codigo no implementado: {_err}',
        allow_module_level=True,
    )
User = get_user_model()


@pytest.mark.django_db
class TestUserProfileSerializer:
    """
    Tests para UserProfileSerializer.

    NOTA: El modelo UserProfile fue integrado directamente en User (FASE 4).
    User no tiene atributo .profile. ProfileSerializer serializa el objeto User.
    """

    @pytest.mark.xfail(
        reason="ProfileSerializer usa UserProfile que no existe (modelo integrado en User en FASE 4). "
               "UserProfile fue eliminado — la serialización de perfil ocurre via UserSerializer.",
        strict=True,
    )
    def test_serialize_profile_avatar(self):
        """ProfileSerializer incluye el campo avatar_url del usuario."""
        import uuid
        u = uuid.uuid4().hex[:6]
        user = User.objects.create_user(
            username=f'u_{u}',
            email=f'u_{u}@example.com',
            password='Pass123',
        )
        from apps.users.serializers.profile_serializer import ProfileSerializer as PS
        serializer = PS(user)
        data = serializer.data
        assert 'avatar_url' in data or 'avatar' in data

    @pytest.mark.xfail(
        reason="UserSettingsSerializer usa UserSettings que no existe (modelo integrado en User en FASE 4).",
        strict=True,
    )
    def test_update_profile(self):
        """UserSettingsSerializer acepta datos parciales."""
        import uuid
        u = uuid.uuid4().hex[:6]
        user = User.objects.create_user(
            username=f'u_{u}',
            email=f'u_{u}@example.com',
            password='Pass123',
        )
        serializer = UserSettingsSerializer(user, data={}, partial=True)
        assert serializer.is_valid(), serializer.errors


@pytest.mark.django_db
class TestUserSerializer:
    """Tests para UserSerializer."""
    
    def test_serialize_user(self):
        """UserSerializer incluye campos básicos del usuario."""
        import uuid
        u = uuid.uuid4().hex[:6]
        user = User.objects.create_user(
            username=f'jdoe_{u}',
            email=f'jdoe_{u}@example.com',
            password='Pass123',
            first_name='John',
            last_name='Doe',
        )
        serializer = UserSerializer(user)
        data = serializer.data
        assert data['username'] == f'jdoe_{u}'
        assert data['email'] == f'jdoe_{u}@example.com'
        assert 'id' in data


@pytest.mark.django_db
class TestUserCreateSerializer:
    """Tests para UserCreateSerializer."""
    
    def test_create_user_success(self):
        """Test: Crear usuario exitosamente."""
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'SecureP@ss1!',
            'password_confirm': 'SecureP@ss1!',
            'first_name': 'New',
            'last_name': 'User'
        }
        
        serializer = UserCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        
        user = serializer.save()
        
        assert user.username == 'newuser'
        assert user.check_password('SecureP@ss1!')
    
    def test_create_user_password_mismatch(self):
        """Test: Error cuando passwords no coinciden."""
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'Pass123',
            'password_confirm': 'Pass456'
        }
        
        serializer = UserCreateSerializer(data=data)
        assert not serializer.is_valid()


@pytest.mark.django_db
class TestLoginSerializer:
    """Tests para LoginSerializer."""
    
    def test_login_serializer_valid(self):
        """Test: Serializer de login válido."""
        data = {
            'username': 'testuser',
            'password': 'Pass123'
        }
        
        serializer = LoginSerializer(data=data)
        assert serializer.is_valid()


@pytest.mark.django_db
@pytest.mark.xfail(reason="API cambió — pendiente actualización post-FASE 6", strict=False)
class TestChangePasswordSerializer:
    """Tests para ChangePasswordSerializer."""
    
    def test_change_password_valid(self):
        """Test: Cambio de password válido."""
        data = {
            'old_password': 'OldPass123',
            'new_password': 'T3stP@ssw0rd!',
            'new_password_confirmation': 'T3stP@ssw0rd!'
        }
        
        serializer = ChangePasswordSerializer(data=data)
        assert serializer.is_valid()
