"""
Tests para API de navegacion (user_menu_view).

Cobertura:
- GET /api/v1/navigation/menu/
- Autenticacion requerida
- Respuesta JSON con menu personalizado
- Manejo de errores
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch, Mock


@pytest.mark.django_db
class TestUserMenuView:
    """Tests para endpoint GET /api/v1/navigation/menu/"""
    
    @pytest.fixture
    def api_client(self):
        """Cliente API de DRF."""
        return APIClient()
    
    @pytest.fixture
    def authenticated_user(self, django_user_model):
        """Usuario autenticado."""
        user = django_user_model.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        return user
    
    @pytest.fixture
    def sample_menu(self):
        """Menu de ejemplo."""
        return [
            {
                'id_menu': 5,
                'des_name': 'Reportes',
                'icon': '/static/icons/menu/reports.png',
                'nivel': 1,
                'orden': 50,
                'submenus': [
                    {
                        'id_menu': 501,
                        'des_name': 'Dashboard',
                        'nivel': 2,
                        'orden': 1,
                        'endpoint': {
                            'url': '/api/v1/reports/dashboard/',
                            'method': 'GET'
                        }
                    }
                ]
            }
        ]
    
    def test_menu_endpoint_requires_authentication(self, api_client):
        """Test que endpoint requiere autenticacion."""
        url = reverse('navigation:user-menu')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @patch('apps.core.navigation.views.MenuBuilder')
    def test_menu_endpoint_returns_user_menu(
        self, 
        mock_builder_class, 
        api_client, 
        authenticated_user,
        sample_menu
    ):
        """Test que endpoint retorna menu del usuario."""
        # Mock del MenuBuilder
        mock_builder = Mock()
        mock_builder.build_user_menu.return_value = sample_menu
        mock_builder_class.return_value = mock_builder
        
        # Autenticar
        api_client.force_authenticate(user=authenticated_user)
        
        # Request
        url = reverse('navigation:user-menu')
        response = api_client.get(url)
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        assert 'menu' in response.data
        assert 'user' in response.data
        
        # Verificar menu
        menu_data = response.data['menu']
        assert len(menu_data) == 1
        assert menu_data[0]['id_menu'] == 5
        assert menu_data[0]['des_name'] == 'Reportes'
        
        # Verificar user info
        user_data = response.data['user']
        assert user_data['username'] == 'testuser'
        assert user_data['full_name'] == 'Test User'
    
    @patch('apps.core.navigation.views.MenuBuilder')
    def test_menu_endpoint_empty_menu(
        self, 
        mock_builder_class, 
        api_client, 
        authenticated_user
    ):
        """Test endpoint con menu vacio (sin permisos)."""
        # Mock retorna menu vacio
        mock_builder = Mock()
        mock_builder.build_user_menu.return_value = []
        mock_builder_class.return_value = mock_builder
        
        # Autenticar
        api_client.force_authenticate(user=authenticated_user)
        
        # Request
        url = reverse('navigation:user-menu')
        response = api_client.get(url)
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        assert response.data['menu'] == []
        assert 'user' in response.data
    
    @patch('apps.core.navigation.views.MenuBuilder')
    def test_menu_endpoint_handles_builder_error(
        self, 
        mock_builder_class, 
        api_client, 
        authenticated_user
    ):
        """Test manejo de error en MenuBuilder."""
        # Mock lanza excepcion
        mock_builder = Mock()
        mock_builder.build_user_menu.side_effect = Exception('Error interno')
        mock_builder_class.return_value = mock_builder
        
        # Autenticar
        api_client.force_authenticate(user=authenticated_user)
        
        # Request
        url = reverse('navigation:user-menu')
        response = api_client.get(url)
        
        # Debe retornar error 500
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert 'error' in response.data
    
    @patch('apps.core.navigation.views.MenuBuilder')
    @patch('apps.core.navigation.views.MenuSerializer')
    def test_menu_endpoint_serializes_menu(
        self, 
        mock_serializer_class,
        mock_builder_class, 
        api_client, 
        authenticated_user,
        sample_menu
    ):
        """Test que endpoint serializa menu correctamente."""
        # Mock MenuBuilder
        mock_builder = Mock()
        mock_builder.build_user_menu.return_value = sample_menu
        mock_builder_class.return_value = mock_builder
        
        # Mock MenuSerializer
        mock_serializer = Mock()
        mock_serializer.serialize_menu.return_value = sample_menu[0]
        mock_serializer_class.return_value = mock_serializer
        
        # Autenticar
        api_client.force_authenticate(user=authenticated_user)
        
        # Request
        url = reverse('navigation:user-menu')
        response = api_client.get(url)
        
        # Verificar que se llamo a serialize_menu
        assert response.status_code == status.HTTP_200_OK
        # MenuSerializer.serialize_menu deberia llamarse para cada item
    
    def test_menu_endpoint_url_pattern(self):
        """Test que URL pattern es correcto."""
        url = reverse('navigation:user-menu')
        assert url == '/api/v1/navigation/menu/'
    
    @patch('apps.core.navigation.views.MenuBuilder')
    def test_menu_endpoint_returns_json(
        self, 
        mock_builder_class, 
        api_client, 
        authenticated_user,
        sample_menu
    ):
        """Test que respuesta es JSON."""
        mock_builder = Mock()
        mock_builder.build_user_menu.return_value = sample_menu
        mock_builder_class.return_value = mock_builder
        
        api_client.force_authenticate(user=authenticated_user)
        
        url = reverse('navigation:user-menu')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response['Content-Type'] == 'application/json'
    
    @patch('apps.core.navigation.views.MenuBuilder')
    def test_menu_endpoint_with_complex_user_name(
        self, 
        mock_builder_class, 
        api_client, 
        django_user_model,
        sample_menu
    ):
        """Test con usuario sin first_name/last_name."""
        # Usuario solo con username
        user = django_user_model.objects.create_user(
            username='admin',
            password='pass123'
        )
        
        mock_builder = Mock()
        mock_builder.build_user_menu.return_value = sample_menu
        mock_builder_class.return_value = mock_builder
        
        api_client.force_authenticate(user=user)
        
        url = reverse('navigation:user-menu')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        # full_name deberia ser username si no hay first/last name
        assert response.data['user']['full_name'] == 'admin'


@pytest.mark.django_db
class TestNavigationURLs:
    """Tests para URLs de navegacion."""
    
    def test_navigation_app_name(self):
        """Test que app_name es 'navigation'."""
        from apps.core.navigation import urls
        assert urls.app_name == 'navigation'
    
    def test_menu_url_resolves(self):
        """Test que URL de menu resuelve correctamente."""
        url = reverse('navigation:user-menu')
        assert url is not None
        assert 'menu' in url
