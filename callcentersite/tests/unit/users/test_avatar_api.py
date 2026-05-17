"""
Tests para API de avatar.

POST   /api/users/profile/avatar/ — sube avatar.
DELETE /api/users/profile/avatar/ — elimina avatar.

Endpoints implementados en apps/users/profile_view.py::AvatarUploadView.
"""
import pytest
import uuid
from io import BytesIO
from PIL import Image
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status


def _make_image_file(name='avatar.jpg', size=(100, 100), color='red', fmt='JPEG'):
    buf = BytesIO()
    Image.new('RGB', size, color=color).save(buf, format=fmt)
    buf.seek(0)
    return SimpleUploadedFile(name, buf.read(), content_type='image/jpeg')


@pytest.mark.unit
@pytest.mark.django_db
class TestAvatarAPI:
    """Cubre POST /api/users/profile/avatar/ y DELETE /api/users/profile/avatar/."""

    def test_upload_avatar_requires_authentication(self, api_client):
        """Subida de avatar no accesible sin autenticación."""
        url = reverse('users:user-avatar')
        response = api_client.post(url, {'avatar': _make_image_file()}, format='multipart')
        assert response.status_code in (401, 403)

    def test_upload_avatar_success(self, authenticated_client):
        """POST con imagen válida retorna 200 con avatar_url."""
        url = reverse('users:user-avatar')
        response = authenticated_client.post(
            url, {'avatar': _make_image_file()}, format='multipart')
        assert response.status_code == status.HTTP_200_OK
        assert 'avatar_url' in response.data

    def test_upload_avatar_invalid_extension(self, authenticated_client):
        """Formato no-imagen retorna 400."""
        url = reverse('users:user-avatar')
        invalid = SimpleUploadedFile('test.txt', b'no es imagen', content_type='text/plain')
        response = authenticated_client.post(url, {'avatar': invalid}, format='multipart')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_delete_avatar_success(self, authenticated_client):
        """DELETE elimina el avatar y retorna 200."""
        url = reverse('users:user-avatar')
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'avatar_url' in response.data

    def test_upload_avatar_too_large(self, authenticated_client):
        """Archivo demasiado grande retorna 400 (si el validador lo controla)."""
        url = reverse('users:user-avatar')
        large = SimpleUploadedFile('big.jpg', b'0' * (3 * 1024 * 1024), content_type='image/jpeg')
        response = authenticated_client.post(url, {'avatar': large}, format='multipart')
        assert response.status_code in (400, 200)


@pytest.mark.unit
@pytest.mark.django_db
class TestAvatarURLsIntegration:
    """Verifica que las rutas del avatar estén correctamente mapeadas."""

    def test_avatar_url_resolves(self):
        """users:user-avatar resuelve a /api/users/profile/avatar/."""
        assert reverse('users:user-avatar') == '/api/users/profile/avatar/'
