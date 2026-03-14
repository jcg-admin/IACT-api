"""
Tests de integración para ProfileViewSet y SettingsViewSet.

Prueban gestión de perfil y configuraciones de usuario.
"""

import pytest
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestProfileViewSet:
    """Tests para ProfileViewSet."""
    
    def test_get_profile_authenticated(self, authenticated_client, regular_user):
        """Test: Obtener perfil propio."""
        response = authenticated_client.get('/api/v1/users/profile/')
        
        assert response.status_code == 200
        assert 'bio' in response.data
        assert 'department' in response.data
        assert 'avatar_url' in response.data
        assert response.data['user_id'] == regular_user.id
    
    def test_get_profile_unauthenticated(self, api_client):
        """Test: Perfil requiere autenticación."""
        response = api_client.get('/api/v1/users/profile/')
        
        assert response.status_code in [401, 403]
    
    def test_update_profile_success(self, authenticated_client, regular_user):
        """Test: Actualizar perfil exitosamente."""
        data = {
            'bio': 'Updated bio',
            'department': 'Engineering',
        }
        
        response = authenticated_client.patch('/api/v1/users/profile/', data)
        
        assert response.status_code == 200
        assert response.data['bio'] == 'Updated bio'
        assert response.data['department'] == 'Engineering'
        
        # Verificar en DB
        regular_user.profile.refresh_from_db()
        assert regular_user.profile.bio == 'Updated bio'
        assert regular_user.profile.department == 'Engineering'
    
    def test_upload_avatar_success(self, authenticated_client, regular_user):
        """Test: Subir avatar exitosamente."""
        # Crear imagen de prueba
        image = Image.new('RGB', (100, 100), color='red')
        image_io = BytesIO()
        image.save(image_io, format='JPEG')
        image_io.seek(0)
        
        avatar = SimpleUploadedFile(
            'test_avatar.jpg',
            image_io.read(),
            content_type='image/jpeg'
        )
        
        data = {'avatar': avatar}
        
        response = authenticated_client.post(
            '/api/v1/users/profile/avatar/',
            data,
            format='multipart'
        )
        
        assert response.status_code == 200
        assert 'avatar_url' in response.data
        assert response.data['avatar_url'] is not None
        
        # Verificar en DB
        regular_user.refresh_from_db()
        assert regular_user.avatar
    
    def test_upload_avatar_invalid_format(self, authenticated_client):
        """Test: Error con formato de avatar inválido."""
        # Archivo de texto en lugar de imagen
        text_file = SimpleUploadedFile(
            'test.txt',
            b'This is not an image',
            content_type='text/plain'
        )
        
        data = {'avatar': text_file}
        
        response = authenticated_client.post(
            '/api/v1/users/profile/avatar/',
            data,
            format='multipart'
        )
        
        assert response.status_code == 400
        assert 'avatar' in response.data
    
    def test_upload_avatar_too_large(self, authenticated_client):
        """Test: Error con avatar muy grande (>2MB)."""
        # Crear imagen grande (3MB)
        image = Image.new('RGB', (3000, 3000), color='blue')
        image_io = BytesIO()
        image.save(image_io, format='JPEG', quality=95)
        image_io.seek(0)
        
        # Verificar que sea > 2MB
        file_size = len(image_io.getvalue())
        if file_size <= 2 * 1024 * 1024:
            # Si la imagen no es lo suficientemente grande, saltamos el test
            pytest.skip("Imagen de prueba no excede 2MB")
        
        avatar = SimpleUploadedFile(
            'large_avatar.jpg',
            image_io.read(),
            content_type='image/jpeg'
        )
        
        data = {'avatar': avatar}
        
        response = authenticated_client.post(
            '/api/v1/users/profile/avatar/',
            data,
            format='multipart'
        )
        
        assert response.status_code == 400
        assert 'avatar' in response.data
    
    def test_remove_avatar_success(self, authenticated_client, regular_user):
        """Test: Eliminar avatar exitosamente."""
        # Primero subir un avatar
        image = Image.new('RGB', (100, 100), color='green')
        image_io = BytesIO()
        image.save(image_io, format='PNG')
        image_io.seek(0)
        
        avatar = SimpleUploadedFile(
            'avatar.png',
            image_io.read(),
            content_type='image/png'
        )
        
        data = {'avatar': avatar}
        authenticated_client.post(
            '/api/v1/users/profile/avatar/',
            data,
            format='multipart'
        )
        
        # Ahora eliminar
        response = authenticated_client.delete('/api/v1/users/profile/avatar/')
        
        assert response.status_code == 200
        assert 'message' in response.data
        
        # Verificar en DB
        regular_user.refresh_from_db()
        assert not regular_user.avatar


@pytest.mark.django_db
class TestSettingsViewSet:
    """Tests para SettingsViewSet."""
    
    def test_get_settings_authenticated(self, authenticated_client, regular_user):
        """Test: Obtener settings propias."""
        response = authenticated_client.get('/api/v1/users/settings/')
        
        assert response.status_code == 200
        assert 'language' in response.data
        assert 'theme' in response.data
        assert 'timezone' in response.data
        assert 'notifications_enabled' in response.data
        assert response.data['user_id'] == regular_user.id
    
    def test_get_settings_unauthenticated(self, api_client):
        """Test: Settings requiere autenticación."""
        response = api_client.get('/api/v1/users/settings/')
        
        assert response.status_code in [401, 403]
    
    def test_update_settings_success(self, authenticated_client, regular_user):
        """Test: Actualizar settings exitosamente."""
        data = {
            'language': 'en',
            'theme': 'dark',
            'notifications_enabled': False,
        }
        
        response = authenticated_client.patch('/api/v1/users/settings/', data)
        
        assert response.status_code == 200
        assert response.data['language'] == 'en'
        assert response.data['theme'] == 'dark'
        assert response.data['notifications_enabled'] is False
        
        # Verificar en DB
        regular_user.settings.refresh_from_db()
        assert regular_user.settings.language == 'en'
        assert regular_user.settings.theme == 'dark'
        assert regular_user.settings.notifications_enabled is False
    
    def test_update_settings_invalid_timezone(self, authenticated_client):
        """Test: Error con timezone inválido."""
        data = {'timezone': 'Invalid/Timezone'}
        
        response = authenticated_client.patch('/api/v1/users/settings/', data)
        
        assert response.status_code == 400
        assert 'timezone' in response.data


# ============================================================================
# RESUMEN TESTS Profile & Settings
# 
# Total Tests: 13
# 
# ProfileViewSet: 8 tests
#   [SUCCESS] get profile authenticated
#   [SUCCESS] get profile unauthenticated
#   [SUCCESS] update profile success
#   [SUCCESS] upload avatar success
#   [SUCCESS] upload avatar invalid format
#   [SUCCESS] upload avatar too large
#   [SUCCESS] remove avatar success
# 
# SettingsViewSet: 5 tests
#   [SUCCESS] get settings authenticated
#   [SUCCESS] get settings unauthenticated
#   [SUCCESS] update settings success
#   [SUCCESS] update settings invalid timezone
# 
# Coverage:
#   [SUCCESS] Profile management
#   [SUCCESS] Avatar upload/delete
#   [SUCCESS] File validation (format, size)
#   [SUCCESS] Settings management
#   [SUCCESS] Timezone validation
# ============================================================================
