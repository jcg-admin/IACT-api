"""
Tests unitarios para endpoints de perfil de usuario.

GET/PATCH /api/users/profile/   — implementado en apps/users/profile_view.py.
GET/PATCH /api/users/settings/  — implementado en apps/users/profile_view.py.

UserProfile y UserSettings fueron eliminados en FASE 4.
La funcionalidad de perfil está integrada directamente en User.
"""
import pytest
import uuid
from rest_framework import status
from tests.test_data.user_test_data import UserTestData, AdminUserTestData


@pytest.mark.django_db
class TestProfileMe:
    """Tests para GET/PATCH /api/users/profile/."""

    def test_get_profile_authenticated(self, api_client):
        """Usuario autenticado puede ver su perfil."""
        user = UserTestData()
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/users/profile/')
        assert response.status_code == status.HTTP_200_OK
        assert 'avatar_url' in response.data
        assert 'username' in response.data

    def test_get_profile_unauthenticated(self, api_client):
        """Perfil requiere autenticación."""
        response = api_client.get('/api/users/profile/')
        assert response.status_code in (401, 403)

    def test_update_profile_partial(self, api_client):
        """PATCH actualiza campos editables."""
        u = uuid.uuid4().hex[:6]
        user = UserTestData()
        api_client.force_authenticate(user=user)
        response = api_client.patch(
            '/api/users/profile/', {'first_name': f'Nuevo_{u}'}, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_get_settings_authenticated(self, api_client):
        """Usuario autenticado puede ver sus settings."""
        user = UserTestData()
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/users/settings/')
        assert response.status_code == status.HTTP_200_OK
        assert 'language' in response.data
        assert 'theme' in response.data

    def test_update_settings(self, api_client):
        """PATCH actualiza configuraciones del usuario."""
        user = UserTestData()
        api_client.force_authenticate(user=user)
        response = api_client.patch(
            '/api/users/settings/', {'language': 'en', 'theme': 'dark'}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['language'] == 'en'

    def test_update_settings_invalid_timezone(self, api_client):
        """Timezone inválido retorna 400."""
        user = UserTestData()
        api_client.force_authenticate(user=user)
        response = api_client.patch(
            '/api/users/settings/', {'timezone': 'Invalid/Zone'}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
