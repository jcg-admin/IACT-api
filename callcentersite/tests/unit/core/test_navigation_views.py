"""
Tests para API de navegación.

Cobertura:
- GET /api/navigation/menu/    → navigation_menu_view
- GET /api/navigation/modules/ → navigation_modules_view
- Autenticación requerida en ambos endpoints
- Respuesta JSON desde NavigationMenuAssembler.build_from_modules / build_flat
- El usuario autenticado se pasa a build_from_modules
- Manejo de excepciones del assembler → HTTP 500
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch, Mock


# ============================================================================
# TestNavigationMenuView — GET /api/navigation/menu/
# ============================================================================

@pytest.mark.django_db
class TestNavigationMenuView:
    """Tests para navigation_menu_view."""

    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def authenticated_user(self, django_user_model):
        return django_user_model.objects.create_user(
            username='testuser',
            password='testpass123',
        )

    @pytest.fixture
    def sample_menu(self):
        """Estructura que retorna build_from_modules (campos de _serialize_module)."""
        return [
            {
                'code': 'MOD_REPORTS',
                'name': 'Reportes',
                'url_path': '/reports/',
                'icon': None,
                'order': 1,
                'is_active': True,
                'children': [],
            }
        ]

    def test_requires_authentication(self, api_client):
        """Endpoint requiere autenticación — 401 sin credenciales."""
        response = api_client.get(reverse('navigation:menu'))
        assert response.status_code in (400, 401)

    @patch('apps.core.navigation.views.NavigationMenuAssembler')
    def test_returns_menu_from_build_from_modules(
        self, mock_assembler_class, api_client, authenticated_user, sample_menu
    ):
        """Response contiene la clave 'menu' con el valor de build_from_modules."""
        mock_assembler = Mock()
        mock_assembler.build_from_modules.return_value = sample_menu
        mock_assembler_class.return_value = mock_assembler

        api_client.force_authenticate(user=authenticated_user)
        response = api_client.get(reverse('navigation:menu'))

        assert response.status_code == status.HTTP_200_OK
        assert 'menu' in response.data
        assert response.data['menu'] == sample_menu
        mock_assembler.build_from_modules.assert_called_once()

    @patch('apps.core.navigation.views.NavigationMenuAssembler')
    def test_passes_user_to_build_from_modules(
        self, mock_assembler_class, api_client, authenticated_user
    ):
        """build_from_modules recibe el usuario autenticado como kwarg 'user'."""
        mock_assembler = Mock()
        mock_assembler.build_from_modules.return_value = []
        mock_assembler_class.return_value = mock_assembler

        api_client.force_authenticate(user=authenticated_user)
        api_client.get(reverse('navigation:menu'))

        call_args = mock_assembler.build_from_modules.call_args
        assert call_args is not None
        assert call_args.kwargs.get('user') == authenticated_user

    @patch('apps.core.navigation.views.NavigationMenuAssembler')
    def test_returns_empty_menu(
        self, mock_assembler_class, api_client, authenticated_user
    ):
        """Menú vacío retorna HTTP 200 con lista vacía."""
        mock_assembler = Mock()
        mock_assembler.build_from_modules.return_value = []
        mock_assembler_class.return_value = mock_assembler

        api_client.force_authenticate(user=authenticated_user)
        response = api_client.get(reverse('navigation:menu'))

        assert response.status_code == status.HTTP_200_OK
        assert response.data['menu'] == []

    @patch('apps.core.navigation.views.NavigationMenuAssembler')
    def test_handles_assembler_exception(
        self, mock_assembler_class, api_client, authenticated_user
    ):
        """Excepción en build_from_modules → HTTP 500 con clave 'error'."""
        mock_assembler = Mock()
        mock_assembler.build_from_modules.side_effect = Exception('Error interno')
        mock_assembler_class.return_value = mock_assembler

        api_client.force_authenticate(user=authenticated_user)
        response = api_client.get(reverse('navigation:menu'))

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert 'error' in response.data

    @patch('apps.core.navigation.views.NavigationMenuAssembler')
    def test_response_content_type_is_json(
        self, mock_assembler_class, api_client, authenticated_user, sample_menu
    ):
        """Content-Type de la respuesta es application/json."""
        mock_assembler = Mock()
        mock_assembler.build_from_modules.return_value = sample_menu
        mock_assembler_class.return_value = mock_assembler

        api_client.force_authenticate(user=authenticated_user)
        response = api_client.get(reverse('navigation:menu'))

        assert response.status_code == status.HTTP_200_OK
        assert 'application/json' in response['Content-Type']


# ============================================================================
# TestNavigationModulesView — GET /api/navigation/modules/
# ============================================================================

@pytest.mark.django_db
class TestNavigationModulesView:
    """Tests para navigation_modules_view."""

    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def authenticated_user(self, django_user_model):
        return django_user_model.objects.create_user(
            username='testuser_mod',
            password='testpass123',
        )

    @pytest.fixture
    def sample_flat(self):
        """Lista plana que retorna build_flat."""
        return [
            {
                'code': 'MOD_A',
                'name': 'Módulo A',
                'url_path': '/a/',
                'icon': None,
                'order': 1,
                'is_active': True,
            },
            {
                'code': 'MOD_B',
                'name': 'Módulo B',
                'url_path': '/b/',
                'icon': None,
                'order': 2,
                'is_active': True,
            },
        ]

    def test_requires_authentication(self, api_client):
        """Endpoint requiere autenticación — 401 sin credenciales."""
        response = api_client.get(reverse('navigation:modules'))
        assert response.status_code in (400, 401)

    @patch('apps.core.navigation.views.NavigationMenuAssembler')
    def test_returns_flat_module_list(
        self, mock_assembler_class, api_client, authenticated_user, sample_flat
    ):
        """Response contiene la clave 'modules' con el valor de build_flat."""
        mock_assembler = Mock()
        mock_assembler.build_flat.return_value = sample_flat
        mock_assembler_class.return_value = mock_assembler

        api_client.force_authenticate(user=authenticated_user)
        response = api_client.get(reverse('navigation:modules'))

        assert response.status_code == status.HTTP_200_OK
        assert 'modules' in response.data
        assert response.data['modules'] == sample_flat
        mock_assembler.build_flat.assert_called_once()

    @patch('apps.core.navigation.views.NavigationMenuAssembler')
    def test_handles_assembler_exception(
        self, mock_assembler_class, api_client, authenticated_user
    ):
        """Excepción en build_flat → HTTP 500 con clave 'error'."""
        mock_assembler = Mock()
        mock_assembler.build_flat.side_effect = Exception('DB error')
        mock_assembler_class.return_value = mock_assembler

        api_client.force_authenticate(user=authenticated_user)
        response = api_client.get(reverse('navigation:modules'))

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert 'error' in response.data


# ============================================================================
# TestNavigationURLs — resolución de URLs
# ============================================================================

@pytest.mark.django_db
class TestNavigationURLs:
    """Tests para URLs del sistema de navegación."""

    def test_navigation_app_name(self):
        """app_name del módulo urls es 'navigation'."""
        from apps.core.navigation import urls
        assert urls.app_name == 'navigation'

    def test_menu_url_resolves_to_correct_path(self):
        """navigation:menu resuelve a /api/navigation/menu/."""
        url = reverse('navigation:menu')
        assert url == '/api/navigation/menu/'

    def test_modules_url_resolves_to_correct_path(self):
        """navigation:modules resuelve a /api/navigation/modules/."""
        url = reverse('navigation:modules')
        assert url == '/api/navigation/modules/'
