"""
Tests para ViewSets de Dashboard.

Pruebas de:
- DashboardConfigViewSet (CRUD + actions)
- WidgetConfigViewSet (CRUD + actions)
- Permisos en ViewSets
- Serializers dinámicos

FASE 7: Tests de viewsets.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.dashboard.models import DashboardConfig, WidgetConfig

User = get_user_model()


class DashboardViewSetTestCase(TestCase):
    """Tests para DashboardConfigViewSet."""

    def setUp(self):
        """Configurar datos de prueba."""
        self.client = APIClient()

        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )

        self.dashboard = DashboardConfig.objects.create(
            user=self.user,
            config_name='Test Dashboard',
            description='Test description',
            is_public=False
        )

        self.public_dashboard = DashboardConfig.objects.create(
            user=self.other_user,
            config_name='Public Dashboard',
            is_public=True
        )

    def test_list_dashboards_authenticated(self):
        """Test listar dashboards autenticado."""
        self.client.force_authenticate(user=self.user)

        response = self.client.get('/api/dashboard/dashboards/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # DRF default pagination devuelve OrderedDict con
        # count/next/previous/results, no list directo.
        self.assertIn('results', response.data)
        self.assertIsInstance(response.data['results'], list)

    def test_list_dashboards_unauthenticated(self):
        """Test listar dashboards sin autenticar."""
        response = self.client.get('/api/dashboard/dashboards/')

        # Debería requerir autenticación
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_own_dashboard(self):
        """Test obtener propio dashboard."""
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            f'/api/dashboard/dashboards/{self.dashboard.id}/'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['config_name'], 'Test Dashboard')

    def test_retrieve_other_private_dashboard(self):
        """Test obtener dashboard privado de otro usuario."""
        self.client.force_authenticate(user=self.other_user)

        response = self.client.get(
            f'/api/dashboard/dashboards/{self.dashboard.id}/'
        )

        # Debería denegar acceso
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_public_dashboard(self):
        """Test obtener dashboard público."""
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            f'/api/dashboard/dashboards/{self.public_dashboard.id}/'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['config_name'], 'Public Dashboard')

    def test_create_dashboard(self):
        """Test crear dashboard."""
        self.client.force_authenticate(user=self.user)

        data = {
            'config_name': 'New Dashboard',
            'description': 'New description',
            'layout_config': {'columns': 12},
            'is_public': False
        }

        # format='json' requerido porque layout_config es dict
        # anidado y multipart (default) no soporta nested data.
        response = self.client.post(
            '/api/dashboard/dashboards/', data, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['config_name'], 'New Dashboard')

        # Verificar que se creó en BD
        self.assertTrue(
            DashboardConfig.objects.filter(
                config_name='New Dashboard',
                user=self.user
            ).exists()
        )

    def test_update_own_dashboard(self):
        """Test actualizar propio dashboard."""
        self.client.force_authenticate(user=self.user)

        data = {
            'config_name': 'Updated Dashboard',
            'description': 'Updated description',
            'layout_config': {'columns': 12},
            'is_public': False
        }

        response = self.client.put(
            f'/api/dashboard/dashboards/{self.dashboard.id}/',
            data, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['config_name'], 'Updated Dashboard')

        # Verificar en BD
        self.dashboard.refresh_from_db()
        self.assertEqual(self.dashboard.config_name, 'Updated Dashboard')

    def test_update_other_dashboard(self):
        """Test actualizar dashboard de otro usuario."""
        self.client.force_authenticate(user=self.other_user)

        data = {
            'config_name': 'Hacked Dashboard',
            'description': 'Should not work',
            'layout_config': {'columns': 12}
        }

        response = self.client.put(
            f'/api/dashboard/dashboards/{self.dashboard.id}/',
            data, format='json'
        )

        # Debería denegar
        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
        )

    def test_delete_own_dashboard(self):
        """Test eliminar propio dashboard."""
        self.client.force_authenticate(user=self.user)

        response = self.client.delete(
            f'/api/dashboard/dashboards/{self.dashboard.id}/'
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verificar soft delete
        self.dashboard.refresh_from_db()
        self.assertIsNotNone(self.dashboard.deleted_at)

    def test_delete_other_dashboard(self):
        """Test eliminar dashboard de otro usuario."""
        self.client.force_authenticate(user=self.other_user)

        response = self.client.delete(
            f'/api/dashboard/dashboards/{self.dashboard.id}/'
        )

        # Debería denegar
        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
        )

    def test_set_default_action(self):
        """Test action set_default."""
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            f'/api/dashboard/dashboards/{self.dashboard.id}/set_default/'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')

        # Verificar en BD
        self.dashboard.refresh_from_db()
        self.assertTrue(self.dashboard.is_default)

    def test_clone_action(self):
        """Test action clone.

        Clona el propio dashboard. Cloning de dashboards de
        otro usuario requiere permiso de view sobre el source +
        permiso de create sobre el target — caso no contemplado
        por IsDashboardOwnerOrReadOnly (denega POST en no
        propios). Una iniciativa futura puede flexibilizar la
        permission del clone action.
        """
        self.client.force_authenticate(user=self.user)

        # Crear widget en el propio dashboard
        WidgetConfig.objects.create(
            dashboard=self.dashboard,
            widget_type='METRICS_SUMMARY',
            widget_name='Test Widget',
            position_x=0,
            position_y=0,
            width=12,
            height=4
        )

        response = self.client.post(
            f'/api/dashboard/dashboards/{self.dashboard.id}/clone/'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'success')

        # Verificar que se clonó
        cloned_dashboard = DashboardConfig.objects.get(
            id=response.data['cloned_dashboard']['id']
        )
        self.assertEqual(cloned_dashboard.user, self.user)
        self.assertEqual(cloned_dashboard.widgets.count(), 1)


class WidgetViewSetTestCase(TestCase):
    """Tests para WidgetConfigViewSet."""

    def setUp(self):
        """Configurar datos de prueba.

        Usuario superuser para que CanCreateWidget (que requiere
        funcion RBAC 'dashboard.widget.create') no bloquee el
        POST de creacion. Tests de RBAC granular se cubren
        aparte; aqui validamos el contrato del viewset.
        """
        self.client = APIClient()

        self.user = User.objects.create_superuser(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.dashboard = DashboardConfig.objects.create(
            user=self.user,
            config_name='Test Dashboard'
        )

        self.widget = WidgetConfig.objects.create(
            dashboard=self.dashboard,
            widget_type='METRICS_SUMMARY',
            widget_name='Test Widget',
            position_x=0,
            position_y=0,
            width=12,
            height=4,
            config_data={}
        )

    def test_list_widgets(self):
        """Test listar widgets."""
        self.client.force_authenticate(user=self.user)

        response = self.client.get('/api/dashboard/widgets/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIsInstance(response.data['results'], list)

    def test_create_widget(self):
        """Test crear widget."""
        self.client.force_authenticate(user=self.user)

        data = {
            'dashboard': self.dashboard.id,
            'widget_type': 'CALLS_CHART',
            'widget_name': 'New Widget',
            'position_x': 0,
            'position_y': 4,
            'width': 6,
            'height': 4,
            'config_data': {}
        }

        # format='json' por config_data dict (incluso vacio).
        response = self.client.post(
            '/api/dashboard/widgets/', data, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['widget_name'], 'New Widget')

    def test_data_action(self):
        """Test action data (obtener datos del widget)."""
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            f'/api/dashboard/widgets/{self.widget.id}/data/'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('widget_id', response.data)
        self.assertIn('data', response.data)

    def test_refresh_cache_action(self):
        """Test action refresh_cache."""
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            f'/api/dashboard/widgets/{self.widget.id}/refresh_cache/'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
