"""
Tests para Serializers de apps/users/.

TDD: Tests primero, luego implementación.
"""

import pytest
from django.contrib.auth import get_user_model

from apps.users.serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    UserProfileSerializer,
    UserSettingsSerializer,
    LoginSerializer,
    ChangePasswordSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)

User = get_user_model()


@pytest.mark.django_db
class TestUserProfileSerializer:
    """Tests para UserProfileSerializer."""
    
    def test_serialize_profile(self):
        """Test: Serializar perfil."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='Pass123'
        )
        
        profile = user.profile
        profile.bio = 'Software Developer'
        profile.department = 'Engineering'
        profile.save()
        
        serializer = UserProfileSerializer(profile)
        data = serializer.data
        
        assert data['bio'] == 'Software Developer'
        assert data['department'] == 'Engineering'
        assert 'avatar_url' in data
    
    def test_update_profile(self):
        """Test: Actualizar perfil."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='Pass123'
        )
        
        data = {
            'bio': 'Senior Developer',
            'department': 'Product Engineering'
        }
        
        serializer = UserProfileSerializer(user.profile, data=data, partial=True)
        assert serializer.is_valid()
        
        profile = serializer.save()
        assert profile.bio == 'Senior Developer'


@pytest.mark.django_db
class TestUserSerializer:
    """Tests para UserSerializer."""
    
    def test_serialize_user(self):
        """Test: Serializar usuario completo."""
        user = User.objects.create_user(
            username='jdoe',
            email='jdoe@example.com',
            password='Pass123',
            first_name='John',
            last_name='Doe'
        )
        
        serializer = UserSerializer(user)
        data = serializer.data
        
        assert data['username'] == 'jdoe'
        assert data['email'] == 'jdoe@example.com'
        assert data['full_name'] == 'John Doe'
        assert 'profile' in data
        assert 'settings' in data
        assert 'functions' in data


@pytest.mark.django_db
class TestUserCreateSerializer:
    """Tests para UserCreateSerializer."""
    
    def test_create_user_success(self):
        """Test: Crear usuario exitosamente."""
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'SecurePass123',
            'password_confirm': 'SecurePass123',
            'first_name': 'New',
            'last_name': 'User'
        }
        
        serializer = UserCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        
        user = serializer.save()
        
        assert user.username == 'newuser'
        assert user.check_password('SecurePass123')
    
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
class TestChangePasswordSerializer:
    """Tests para ChangePasswordSerializer."""
    
    def test_change_password_valid(self):
        """Test: Cambio de password válido."""
        data = {
            'old_password': 'OldPass123',
            'new_password': 'NewPass456',
            'new_password_confirm': 'NewPass456'
        }
        
        serializer = ChangePasswordSerializer(data=data)
        assert serializer.is_valid()
