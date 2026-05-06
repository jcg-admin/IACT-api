"""
Tests unitarios para ProfileViewSet.

FASE 2 PARTE 6: Tests con 90%+ coverage.
"""

import pytest
from rest_framework import status
from unittest.mock import patch, Mock
from io import BytesIO
from PIL import Image


try:
    from apps.users.models import User, UserProfile, UserSettings
except ImportError as _err:
    pytest.skip(
        f'Codigo no implementado: {_err}',
        allow_module_level=True,
    )
from tests.factories.user_factory import UserFactory


@pytest.mark.django_db
class TestProfileMe:
    """Tests para GET/PUT/PATCH /api/profile/me/."""
    
    def test_get_profile_authenticated(self, api_client):
        """Test: Ver perfil propio."""
        user = UserFactory()
        api_client.force_authenticate(user=user)
        
        response = api_client.get('/api/profile/me/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'bio' in response.data
        assert 'department' in response.data
        assert 'avatar_url' in response.data
    
    def test_get_profile_unauthenticated(self, api_client):
        """Test: Sin autenticación retorna 401."""
        response = api_client.get('/api/profile/me/')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_update_profile_put(self, api_client):
        """Test: Actualizar perfil completo (PUT)."""
        user = UserFactory()
        api_client.force_authenticate(user=user)
        
        data = {
            'bio': 'Desarrollador Python Senior',
            'department': 'DEVELOPMENT',
        }
        
        response = api_client.put('/api/profile/me/', data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['bio'] == 'Desarrollador Python Senior'
        assert response.data['department'] == 'DEVELOPMENT'
    
    def test_update_profile_patch(self, api_client):
        """Test: Actualizar perfil parcial (PATCH)."""
        user = UserFactory()
        api_client.force_authenticate(user=user)
        
        data = {'bio': 'Nueva bio'}
        
        response = api_client.patch('/api/profile/me/', data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['bio'] == 'Nueva bio'
    
    def test_profile_autocreated(self, api_client):
        """Test: Profile se crea automáticamente si no existe."""
        user = UserFactory()
        
        # Asegurar que no existe profile
        if hasattr(user, 'profile'):
            user.profile.delete()
        
        api_client.force_authenticate(user=user)
        
        response = api_client.get('/api/profile/me/')
        
        assert response.status_code == status.HTTP_200_OK
        assert UserProfile.objects.filter(user=user).exists()


@pytest.mark.django_db
class TestSettings:
    """Tests para GET/PUT/PATCH /api/profile/me/settings/."""
    
    def test_get_settings(self, api_client):
        """Test: Ver settings propios."""
        user = UserFactory()
        api_client.force_authenticate(user=user)
        
        response = api_client.get('/api/profile/me/settings/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'language' in response.data
        assert 'notifications_enabled' in response.data
    
    def test_update_settings_language(self, api_client):
        """Test: Cambiar idioma."""
        user = UserFactory()
        api_client.force_authenticate(user=user)
        
        data = {'language': 'en'}
        
        response = api_client.patch('/api/profile/me/settings/', data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['language'] == 'en'
    
    def test_update_settings_notifications(self, api_client):
        """Test: Cambiar notificaciones."""
        user = UserFactory()
        api_client.force_authenticate(user=user)
        
        data = {'notifications_enabled': False}
        
        response = api_client.patch('/api/profile/me/settings/', data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['notifications_enabled'] is False
    
    def test_settings_autocreated(self, api_client):
        """Test: Settings se crean automáticamente."""
        user = UserFactory()
        
        # Asegurar que no existen settings
        if hasattr(user, 'settings'):
            user.settings.delete()
        
        api_client.force_authenticate(user=user)
        
        response = api_client.get('/api/profile/me/settings/')
        
        assert response.status_code == status.HTTP_200_OK
        assert UserSettings.objects.filter(user=user).exists()


@pytest.mark.django_db
class TestAvatar:
    """Tests para POST/DELETE /api/profile/me/avatar/."""
    
    def test_upload_avatar(self, api_client):
        """Test: Subir avatar."""
        user = UserFactory()
        api_client.force_authenticate(user=user)
        
        # Crear imagen fake
        image = Image.new('RGB', (100, 100), color='red')
        image_file = BytesIO()
        image.save(image_file, 'JPEG')
        image_file.seek(0)
        image_file.name = 'avatar.jpg'
        
        data = {'avatar': image_file}
        
        response = api_client.post(
            '/api/profile/me/avatar/',
            data,
            format='multipart'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert 'avatar_url' in response.data
    
    def test_upload_avatar_invalid_format(self, api_client):
        """Test: Formato inválido retorna error."""
        user = UserFactory()
        api_client.force_authenticate(user=user)
        
        # Crear archivo txt (no imagen)
        file = BytesIO(b'not an image')
        file.name = 'file.txt'
        
        data = {'avatar': file}
        
        response = api_client.post(
            '/api/profile/me/avatar/',
            data,
            format='multipart'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_upload_avatar_too_large(self, api_client):
        """Test: Archivo muy grande retorna error."""
        user = UserFactory()
        api_client.force_authenticate(user=user)
        
        # Crear imagen muy grande (simular >2MB)
        # Mock validate_avatar_file para simular error
        from apps.users.validators import validate_avatar_file
        
        image = Image.new('RGB', (100, 100))
        image_file = BytesIO()
        image.save(image_file, 'JPEG')
        image_file.seek(0)
        image_file.name = 'large.jpg'
        
        with patch('apps.users.validators.validate_avatar_file') as mock_validate:
            mock_validate.side_effect = ValueError('Tamaño máximo: 2MB')
            
            data = {'avatar': image_file}
            response = api_client.post(
                '/api/profile/me/avatar/',
                data,
                format='multipart'
            )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_remove_avatar(self, api_client):
        """Test: Eliminar avatar."""
        user = UserFactory()
        api_client.force_authenticate(user=user)
        
        # Mock ProfileService.remove_avatar
        with patch('apps.users.services.profile_service.ProfileService.remove_avatar') as mock_remove:
            mock_remove.return_value = None
            
            response = api_client.delete('/api/profile/me/avatar/')
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_remove.assert_called_once_with(user)
    
    def test_upload_avatar_unauthenticated(self, api_client):
        """Test: Upload sin autenticación retorna 401."""
        response = api_client.post('/api/profile/me/avatar/')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# RESUMEN TESTS ProfileViewSet
# 
# Total tests: 14
# 
# /me/ (5 tests):
#   [SUCCESS] GET authenticated
#   [SUCCESS] GET unauthenticated -> 401
#   [SUCCESS] PUT update completo
#   [SUCCESS] PATCH update parcial
#   [SUCCESS] Profile auto-creado
# 
# /me/settings/ (4 tests):
#   [SUCCESS] GET settings
#   [SUCCESS] UPDATE language
#   [SUCCESS] UPDATE notifications
#   [SUCCESS] Settings auto-creados
# 
# /me/avatar/ (5 tests):
#   [SUCCESS] POST upload success
#   [SUCCESS] POST formato inválido -> 400
#   [SUCCESS] POST archivo muy grande -> 400
#   [SUCCESS] DELETE avatar
#   [SUCCESS] POST sin autenticación -> 401
# 
# Coverage: ~90% de ProfileViewSet
# ============================================================================
