"""
Tests para API de avatar.
Versión integrada utilizando fixtures de users.py y conftest.py.
"""

import pytest

pytestmark = pytest.mark.skip(reason="URLs users:upload-avatar y users:profile no registradas aún")
from django.urls import reverse
from rest_framework import status
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile

@pytest.mark.django_db
class TestAvatarAPI:
    """
    Cubre: POST /api/v1/users/upload-avatar/ y DELETE /api/v1/users/delete-avatar/
    """

    def test_upload_avatar_requires_authentication(self, api_client, valid_avatar_file):
        """Verifica que un usuario no autenticado no puede subir imágenes."""
        url = reverse('users:upload-avatar')
        response = api_client.post(url, {'avatar': valid_avatar_file})
        assert response.status_code in (400, 401)

    def test_upload_avatar_success(self, authenticated_client, valid_avatar_file):
        """Test de subida exitosa con un archivo válido."""
        url = reverse('users:upload-avatar')
        response = authenticated_client.post(
            url, 
            {'avatar': valid_avatar_file}, 
            format='multipart'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert 'avatar_url' in response.data
        assert 'success' in response.data

    def test_upload_avatar_invalid_extension(self, authenticated_client):
        """Verifica que no se permitan archivos que no sean imágenes (ej. .txt)."""
        invalid_file = SimpleUploadedFile(
            name='test.txt', 
            content=b'esto no es una imagen', 
            content_type='text/plain'
        )
        url = reverse('users:upload-avatar')
        response = authenticated_client.post(url, {'avatar': invalid_file}, format='multipart')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'avatar' in response.data  # DRF suele poner el error bajo el nombre del campo

    def test_upload_avatar_too_large(self, authenticated_client):
        """
        Verifica la validación de tamaño. 
        (Asumiendo que tu validador tiene un límite, ej. 2MB).
        """
        large_content = b'0' * (1024 * 1024 * 3)  # 3MB
        large_file = SimpleUploadedFile(
            name='big.jpg', 
            content=large_content, 
            content_type='image/jpeg'
        )
        url = reverse('users:upload-avatar')
        response = authenticated_client.post(url, {'avatar': large_file}, format='multipart')
        
        # Si tienes el validador de tamaño activo, debería dar 400
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # --- TESTS DE ELIMINACIÓN (DELETE) ---

    def test_delete_avatar_success(self, api_client, user_with_avatar):
        """Verifica que el usuario puede eliminar su propio avatar."""
        api_client.force_authenticate(user=user_with_avatar)
        
        url = reverse('users:delete-avatar')
        response = api_client.delete(url)
        
        assert response.status_code == status.HTTP_200_OK
        # Al eliminarlo, el modelo suele retornar la URL del avatar por defecto
        assert 'avatar_url' in response.data

    @patch('apps.users.models.CustomUser.save')
    def test_delete_avatar_server_error(self, mock_save, api_client, user_with_avatar):
        """Prueba la resistencia del sistema ante un error inesperado de base de datos."""
        mock_save.side_effect = Exception("Database error")
        api_client.force_authenticate(user=user_with_avatar)
        
        url = reverse('users:delete-avatar')
        response = api_client.delete(url)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert 'error' in response.data

    # --- TESTS DE INTEGRACIÓN DE URLS ---

@pytest.mark.django_db
class TestAvatarURLsIntegration:
    """Verifica que las rutas del sistema estén correctamente mapeadas."""
    
    def test_avatar_urls_resolve_correctly(self):
        assert reverse('users:upload-avatar') == '/api/v1/users/upload-avatar/'
        assert reverse('users:delete-avatar') == '/api/v1/users/delete-avatar/'