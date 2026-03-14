import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


@pytest.mark.unit
@pytest.mark.django_db
class TestUserViewSet:
    """Tests UserViewSet."""
    
    def test_list_users_requires_authentication(self):
        """Listar usuarios requiere autenticacion (CNST-005)."""
        client = APIClient()
        url = reverse('users:user-list')
        
        response = client.get(url)
        
        assert response.status_code == 401
    
    def test_list_users_authenticated(self):
        """Listar usuarios cuando esta autenticado."""
        user = User.objects.create_user('testuser', password='test123')
        
        # Autenticar con JWT
        refresh = RefreshToken.for_user(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('users:user-list')
        response = client.get(url)
        
        assert response.status_code == 200
        # Respuesta paginada
        assert 'results' in response.data
        assert isinstance(response.data['results'], list)
        assert len(response.data['results']) >= 1
    
    def test_create_user_requires_authentication(self):
        """Crear usuario requiere autenticacion."""
        client = APIClient()
        url = reverse('users:user-list')
        
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123'
        }
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == 401
    
    def test_create_user_authenticated(self):
        """Crear usuario via API autenticado."""
        admin = User.objects.create_user('admin', password='admin123')
        
        refresh = RefreshToken.for_user(admin)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('users:user-list')
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'newpass123'
        }
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert User.objects.filter(username='newuser').exists()
        
        # Verificar password hasheado
        new_user = User.objects.get(username='newuser')
        assert new_user.check_password('newpass123')
    
    def test_retrieve_user(self):
        """Obtener detalle de usuario."""
        user = User.objects.create_user('testuser', password='test123')
        other_user = User.objects.create_user('otheruser')
        
        refresh = RefreshToken.for_user(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('users:user-detail', args=[other_user.id])
        response = client.get(url)
        
        assert response.status_code == 200
        assert response.data['username'] == 'otheruser'
    
    def test_update_user(self):
        """Actualizar usuario."""
        user = User.objects.create_user('testuser', password='test123')
        target = User.objects.create_user('targetuser', email='old@example.com')
        
        refresh = RefreshToken.for_user(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('users:user-detail', args=[target.id])
        data = {
            'username': 'targetuser',
            'email': 'new@example.com',
            'first_name': 'Updated',
            'last_name': 'Name',
        }
        
        response = client.put(url, data, format='json')
        
        assert response.status_code == 200
        target.refresh_from_db()
        assert target.email == 'new@example.com'
    
    def test_delete_user(self):
        """Eliminar usuario."""
        user = User.objects.create_user('testuser', password='test123')
        target = User.objects.create_user('targetuser')
        
        refresh = RefreshToken.for_user(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('users:user-detail', args=[target.id])
        response = client.delete(url)
        
        assert response.status_code == 204
        assert not User.objects.filter(id=target.id).exists()
