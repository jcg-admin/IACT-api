"""
Tests para API de perfil de usuario.
Versión integrada utilizando fixtures de users.py y conftest.py.
"""

import pytest
from django.urls import reverse
from rest_framework import status
from unittest.mock import patch
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
class TestProfileAPI:
    """
    Cubre: GET /api/v1/users/profile/ y PUT /api/v1/users/profile/update/
    """

    # --- TESTS DE OBTENCIÓN (GET) ---

    def test_get_profile_requires_authentication(self, api_client):
        """Verifica que el perfil no es accesible sin token JWT."""
        url = reverse('users:user-profile')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_profile_success(self, api_client, user_with_profile):
        """
        Verifica que se retornan todos los campos del CustomUser.
        Usa la fixture 'user_with_profile' que ya tiene phone, position, etc.
        """
        api_client.force_authenticate(user=user_with_profile)
        url = reverse('users:user-profile')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data['username'] == user_with_profile.username
        assert data['email'] == user_with_profile.email
        # Campos personalizados de tu modelo CustomUser
        assert data['phone'] == user_with_profile.phone
        assert data['position'] == user_with_profile.position
        assert data['employee_id'] == user_with_profile.employee_id

    # --- TESTS DE ACTUALIZACIÓN (PUT) ---

    def test_update_profile_success(self, api_client, user_with_profile):
        """Verifica la actualización parcial de campos del perfil."""
        api_client.force_authenticate(user=user_with_profile)
        url = reverse('users:update-profile')
        
        update_data = {
            'first_name': 'Carlos',
            'last_name': 'Díaz',
            'position': 'Senior Developer'
        }
        
        response = api_client.put(url, update_data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['profile']['first_name'] == 'Carlos'
        assert response.data['profile']['position'] == 'Senior Developer'
        
        # Verificar persistencia en DB
        user_with_profile.refresh_from_db()
        assert user_with_profile.first_name == 'Carlos'

    def test_update_profile_readonly_fields(self, api_client, user_with_profile):
        """
        Verifica que campos sensibles como 'employee_id' no se puedan 
        editar si el serializador los marca como read-only.
        """
        api_client.force_authenticate(user=user_with_profile)
        url = reverse('users:update-profile')
        
        original_id = user_with_profile.employee_id
        response = api_client.put(url, {'employee_id': 'HACK-999'}, format='json')
        
        user_with_profile.refresh_from_db()
        # El ID no debería cambiar si tu lógica de negocio lo prohíbe
        assert user_with_profile.employee_id == original_id

    def test_update_profile_handles_error(self, api_client, user_with_profile):
        """Test manejo de error interno (500) al fallar el guardado."""
        api_client.force_authenticate(user=user_with_profile)
        
        with patch.object(User, 'save', side_effect=Exception('Error de Base de Datos')):
            url = reverse('users:update-profile')
            response = api_client.put(url, {'first_name': 'Error'}, format='json')
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert 'error' in response.data

@pytest.mark.django_db
class TestProfileURLsIntegration:
    """Verifica la consistencia de las rutas de perfil."""
    
    def test_profile_urls_resolve_correctly(self):
        assert reverse('users:user-profile') == '/api/v1/users/profile/'
        assert reverse('users:update-profile') == '/api/v1/users/profile/update/'