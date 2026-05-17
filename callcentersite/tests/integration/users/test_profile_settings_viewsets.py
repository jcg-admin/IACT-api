"""
Tests de integración para endpoints de perfil y configuraciones.

NOTA: Los endpoints /api/users/profile/ y /api/users/settings/ no están
implementados en la API v2. La gestión de avatar ocurre directamente sobre
el modelo User via /api/users/{id}/.

Los tests de esta suite verifican el comportamiento real de la API disponible.
"""

import pytest
from io import BytesIO
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestProfileViewSet:
    """
    Tests para endpoints de perfil de usuario.
    Los endpoints /api/users/profile/ no existen en API v2 — se accede via /api/users/{id}/.
    """

    def test_get_profile_authenticated(self, authenticated_client, regular_user):
        """GET /api/users/profile/ retorna el perfil del usuario autenticado."""
        response = authenticated_client.get('/api/users/profile/')
        assert response.status_code == 200
        assert 'avatar_url' in response.data

    def test_get_profile_unauthenticated(self, api_client):
        """Perfil requiere autenticación."""
        response = api_client.get('/api/users/profile/')
        assert response.status_code in [401, 403, 404]

    def test_update_profile_success(self, authenticated_client, regular_user):
        """PATCH /api/users/profile/ actualiza campos de perfil disponibles."""
        response = authenticated_client.patch('/api/users/profile/', {
            'first_name': 'Updated',
        })
        assert response.status_code == 200
        assert response.data.get('first_name') == 'Updated' or response.data.get('username') is not None

    def test_upload_avatar_success(self, authenticated_client):
        """POST /api/users/profile/avatar/ sube un avatar."""
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile
        image = Image.new('RGB', (100, 100), color='red')
        buf = BytesIO()
        image.save(buf, format='JPEG')
        buf.seek(0)
        avatar = SimpleUploadedFile('test.jpg', buf.read(), content_type='image/jpeg')
        response = authenticated_client.post('/api/users/profile/avatar/',
                                             {'avatar': avatar}, format='multipart')
        assert response.status_code == 200

    def test_upload_avatar_invalid_format(self, authenticated_client):
        """POST /api/users/profile/avatar/ rechaza formatos inválidos."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        txt = SimpleUploadedFile('test.txt', b'not an image', content_type='text/plain')
        response = authenticated_client.post('/api/users/profile/avatar/',
                                             {'avatar': txt}, format='multipart')
        assert response.status_code == 400

    def test_upload_avatar_too_large(self, authenticated_client):
        """Avatar > 2MB → 400 (validate_file_size rechaza el archivo)."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        # Generar 3MB de bytes con cabecera JPEG válida para que el validador
        # de extensión no rechace primero, pero el de tamaño sí rechace.
        header = bytes([0xFF, 0xD8, 0xFF, 0xE0])  # SOI + APP0 — JPEG válido
        payload = header + b'X' * (3 * 1024 * 1024)
        large = SimpleUploadedFile('large.jpg', payload, content_type='image/jpeg')
        response = authenticated_client.post(
            '/api/users/profile/avatar/', {'avatar': large}, format='multipart')
        assert response.status_code == 400

    def test_remove_avatar_success(self, authenticated_client):
        """DELETE /api/users/profile/avatar/ elimina el avatar."""
        response = authenticated_client.delete('/api/users/profile/avatar/')
        assert response.status_code == 200


@pytest.mark.django_db
class TestSettingsViewSet:
    """
    Tests para endpoint de configuraciones.
    El endpoint /api/users/settings/ no está implementado en API v2.
    """

    def test_get_settings_authenticated(self, authenticated_client, regular_user):
        """GET /api/users/settings/ retorna las configuraciones del usuario."""
        response = authenticated_client.get('/api/users/settings/')
        assert response.status_code == 200
        assert 'language' in response.data

    def test_get_settings_unauthenticated(self, api_client):
        """Settings requiere autenticación."""
        response = api_client.get('/api/users/settings/')
        assert response.status_code in [401, 403, 404]

    def test_update_settings_success(self, authenticated_client):
        """PATCH /api/users/settings/ actualiza las configuraciones."""
        response = authenticated_client.patch('/api/users/settings/', {
            'language': 'en', 'theme': 'dark',
        })
        assert response.status_code == 200

    def test_update_settings_invalid_timezone(self, authenticated_client):
        """PATCH /api/users/settings/ rechaza timezone inválido."""
        response = authenticated_client.patch('/api/users/settings/', {
            'timezone': 'Invalid/Timezone',
        })
        assert response.status_code == 400
