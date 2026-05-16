"""
Tests para sistema de permissions.

Pruebas de:
- Funciones can_view/edit/delete para Dashboard
- Funciones can_view/edit/delete para Widget
- Funciones can_view/edit para Filter
- Clases DRF BasePermission

FASE 7: Tests de permissions.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory

from apps.dashboard.models import DashboardConfig, WidgetConfig, SavedFilter
from apps.dashboard.permissions import (  # noqa: F401
    can_view_dashboard,
    can_edit_dashboard,
    can_delete_dashboard,
    can_view_widget,
    can_edit_widget,
    can_delete_widget,
    can_view_filter,
    can_edit_filter,
    IsDashboardOwnerOrReadOnly,
    IsWidgetOwnerOrReadOnly,  # noqa: F401
    IsFilterOwnerOrReadOnly  # noqa: F401
)

User = get_user_model()


class DashboardPermissionsTestCase(TestCase):
    """Tests para permisos de Dashboard."""
    
    def setUp(self):
        """Configurar datos de prueba."""
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='testpass123'
        )
        
        self.other = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123'
        )
        
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            is_staff=True
        )
        
        self.private_dashboard = DashboardConfig.objects.create(
            user=self.owner,
            config_name='Private Dashboard',
            is_public=False
        )
        
        self.public_dashboard = DashboardConfig.objects.create(
            user=self.owner,
            config_name='Public Dashboard',
            is_public=True
        )
    
    def test_can_view_dashboard_owner(self):
        """Test que propietario puede ver dashboard privado."""
        self.assertTrue(
            can_view_dashboard(self.owner, self.private_dashboard)
        )
    
    def test_can_view_dashboard_other_private(self):
        """Test que otro usuario NO puede ver dashboard privado."""
        self.assertFalse(
            can_view_dashboard(self.other, self.private_dashboard)
        )
    
    def test_can_view_dashboard_other_public(self):
        """Test que otro usuario puede ver dashboard público."""
        self.assertTrue(
            can_view_dashboard(self.other, self.public_dashboard)
        )
    
    def test_can_view_dashboard_admin(self):
        """Test que admin puede ver cualquier dashboard."""
        self.assertTrue(
            can_view_dashboard(self.admin, self.private_dashboard)
        )
        self.assertTrue(
            can_view_dashboard(self.admin, self.public_dashboard)
        )
    
    def test_can_edit_dashboard_owner(self):
        """Test que propietario puede editar."""
        self.assertTrue(
            can_edit_dashboard(self.owner, self.private_dashboard)
        )
    
    def test_can_edit_dashboard_other(self):
        """Test que otro usuario NO puede editar."""
        self.assertFalse(
            can_edit_dashboard(self.other, self.public_dashboard)
        )
    
    def test_can_edit_dashboard_admin(self):
        """Test que admin puede editar cualquier dashboard."""
        self.assertTrue(
            can_edit_dashboard(self.admin, self.private_dashboard)
        )
    
    def test_can_delete_dashboard_owner(self):
        """Test que propietario puede eliminar."""
        self.assertTrue(
            can_delete_dashboard(self.owner, self.private_dashboard)
        )
    
    def test_can_delete_dashboard_other(self):
        """Test que otro usuario NO puede eliminar."""
        self.assertFalse(
            can_delete_dashboard(self.other, self.private_dashboard)
        )


class WidgetPermissionsTestCase(TestCase):
    """Tests para permisos de Widget."""
    
    def setUp(self):
        """Configurar datos de prueba."""
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='testpass123'
        )
        
        self.other = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123'
        )
        
        self.private_dashboard = DashboardConfig.objects.create(
            user=self.owner,
            config_name='Private',
            is_public=False
        )
        
        self.public_dashboard = DashboardConfig.objects.create(
            user=self.owner,
            config_name='Public',
            is_public=True
        )
        
        self.private_widget = WidgetConfig.objects.create(
            dashboard=self.private_dashboard,
            widget_type='METRICS_SUMMARY',
            widget_name='Private Widget',
            position_x=0,
            position_y=0,
            width=12,
            height=4
        )
        
        self.public_widget = WidgetConfig.objects.create(
            dashboard=self.public_dashboard,
            widget_type='CALLS_CHART',
            widget_name='Public Widget',
            position_x=0,
            position_y=0,
            width=12,
            height=4
        )
    
    def test_can_view_widget_inherits_dashboard(self):
        """Test que permisos de widget heredan de dashboard."""
        # Propietario puede ver widget de dashboard privado
        self.assertTrue(can_view_widget(self.owner, self.private_widget))
        
        # Otro usuario NO puede ver widget de dashboard privado
        self.assertFalse(can_view_widget(self.other, self.private_widget))
        
        # Otro usuario puede ver widget de dashboard público
        self.assertTrue(can_view_widget(self.other, self.public_widget))
    
    def test_can_edit_widget_only_owner(self):
        """Test que solo propietario puede editar widget."""
        # Propietario puede editar
        self.assertTrue(can_edit_widget(self.owner, self.public_widget))
        
        # Otro usuario NO puede editar (aunque dashboard sea público)
        self.assertFalse(can_edit_widget(self.other, self.public_widget))
    
    def test_can_delete_widget_only_owner(self):
        """Test que solo propietario puede eliminar widget."""
        self.assertTrue(can_delete_widget(self.owner, self.private_widget))
        self.assertFalse(can_delete_widget(self.other, self.private_widget))


class FilterPermissionsTestCase(TestCase):
    """Tests para permisos de Filter."""
    
    def setUp(self):
        """Configurar datos de prueba."""
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='testpass123'
        )
        
        self.other = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123'
        )
        
        self.private_filter = SavedFilter.objects.create(
            user=self.owner,
            filter_name='Private Filter',
            filter_type='call',
            filter_config={'call_type': 'inbound'},
            is_public=False
        )
        
        self.public_filter = SavedFilter.objects.create(
            user=self.owner,
            filter_name='Public Filter',
            filter_type='call',
            filter_config={'call_type': 'outbound'},
            is_public=True
        )
    
    def test_can_view_filter_owner(self):
        """Test que propietario puede ver filtro."""
        self.assertTrue(can_view_filter(self.owner, self.private_filter))
    
    def test_can_view_filter_other_private(self):
        """Test que otro usuario NO puede ver filtro privado."""
        self.assertFalse(can_view_filter(self.other, self.private_filter))
    
    def test_can_view_filter_other_public(self):
        """Test que otro usuario puede ver filtro público."""
        self.assertTrue(can_view_filter(self.other, self.public_filter))
    
    def test_can_edit_filter_owner(self):
        """Test que propietario puede editar."""
        self.assertTrue(can_edit_filter(self.owner, self.private_filter))
    
    def test_can_edit_filter_other(self):
        """Test que otro usuario NO puede editar."""
        self.assertFalse(can_edit_filter(self.other, self.public_filter))


class DRFPermissionClassesTestCase(TestCase):
    """Tests para clases de permisos DRF."""
    
    def setUp(self):
        """Configurar datos de prueba."""
        self.factory = APIRequestFactory()
        
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='testpass123'
        )
        
        self.other = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123'
        )
        
        self.dashboard = DashboardConfig.objects.create(
            user=self.owner,
            config_name='Test Dashboard',
            is_public=True
        )
    
    def test_dashboard_owner_or_readonly_get(self):
        """Test IsDashboardOwnerOrReadOnly para GET."""
        permission = IsDashboardOwnerOrReadOnly()
        
        # GET request de otro usuario (público)
        request = self.factory.get('/api/dashboards/1/')
        request.user = self.other
        
        # Debería permitir GET
        self.assertTrue(
            permission.has_object_permission(request, None, self.dashboard)
        )
    
    def test_dashboard_owner_or_readonly_post(self):
        """Test IsDashboardOwnerOrReadOnly para POST."""
        permission = IsDashboardOwnerOrReadOnly()
        
        # POST request de otro usuario
        request = self.factory.post('/api/dashboards/1/')
        request.user = self.other
        
        # NO debería permitir POST
        self.assertFalse(
            permission.has_object_permission(request, None, self.dashboard)
        )
        
        # POST request del propietario
        request.user = self.owner
        
        # Debería permitir POST
        self.assertTrue(
            permission.has_object_permission(request, None, self.dashboard)
        )
