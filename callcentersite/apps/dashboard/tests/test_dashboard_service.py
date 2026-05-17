"""
Tests para DashboardService.

Pruebas de:
- create_default_dashboard
- clone_dashboard
- set_as_default
- export_config
- import_config
- delete_dashboard

FASE 7: Tests de services.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.dashboard.models import DashboardConfig, WidgetConfig, UserDashboardPreference
from apps.dashboard.services import DashboardService

User = get_user_model()


class DashboardServiceTestCase(TestCase):
    """Tests para DashboardService."""

    def setUp(self):
        """Configurar datos de prueba."""
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

    def test_create_default_dashboard(self):
        """Test crear dashboard por defecto."""
        dashboard = DashboardService.create_default_dashboard(self.user)

        # Verificar dashboard creado
        self.assertIsNotNone(dashboard)
        self.assertEqual(dashboard.user, self.user)
        self.assertEqual(dashboard.config_name, 'Mi Dashboard')
        self.assertTrue(dashboard.is_default)

        # Verificar widgets creados
        widgets = dashboard.widgets.all()
        self.assertEqual(widgets.count(), 3)

        # Verificar tipos de widgets
        widget_types = [w.widget_type for w in widgets]
        self.assertIn('METRICS_SUMMARY', widget_types)
        self.assertIn('CALLS_CHART', widget_types)
        self.assertIn('TRANSFERS_CHART', widget_types)

        # Verificar preferencia creada
        preference = UserDashboardPreference.objects.get(user=self.user)
        self.assertEqual(preference.default_dashboard, dashboard)

    def test_create_default_dashboard_already_exists(self):
        """Test crear dashboard cuando ya existe uno."""
        # Crear primer dashboard
        DashboardService.create_default_dashboard(self.user)

        # Crear segundo dashboard
        DashboardService.create_default_dashboard(self.user)

        # Ambos deberían existir
        self.assertEqual(
            DashboardConfig.objects.filter(user=self.user).count(),
            2
        )

    def test_clone_dashboard(self):
        """Test clonar dashboard."""
        # Crear dashboard original
        original = DashboardConfig.objects.create(
            user=self.user,
            config_name='Original Dashboard',
            description='Original description',
            is_default=True,
            is_public=False
        )

        # Crear widgets en original
        WidgetConfig.objects.create(
            dashboard=original,
            widget_type='METRICS_SUMMARY',
            widget_name='Summary',
            position_x=0,
            position_y=0,
            width=12,
            height=4
        )

        WidgetConfig.objects.create(
            dashboard=original,
            widget_type='CALLS_CHART',
            widget_name='Calls',
            position_x=0,
            position_y=4,
            width=6,
            height=4
        )

        # Clonar para otro usuario
        cloned = DashboardService.clone_dashboard(original.id, self.other_user)

        # Verificar dashboard clonado
        self.assertIsNotNone(cloned)
        self.assertNotEqual(cloned.id, original.id)
        self.assertEqual(cloned.user, self.other_user)
        self.assertEqual(cloned.config_name, 'Original Dashboard (copia)')
        self.assertFalse(cloned.is_default)
        self.assertFalse(cloned.is_public)

        # Verificar widgets clonados
        self.assertEqual(cloned.widgets.count(), 2)

        # Verificar que los widgets son nuevos objetos
        original_widget_ids = set(original.widgets.values_list('id', flat=True))
        cloned_widget_ids = set(cloned.widgets.values_list('id', flat=True))
        self.assertEqual(len(original_widget_ids.intersection(cloned_widget_ids)), 0)

    def test_set_as_default(self):
        """Test marcar dashboard como default."""
        # Crear dos dashboards
        dashboard1 = DashboardConfig.objects.create(
            user=self.user,
            config_name='Dashboard 1',
            is_default=True
        )

        dashboard2 = DashboardConfig.objects.create(
            user=self.user,
            config_name='Dashboard 2',
            is_default=False
        )

        # Marcar dashboard2 como default
        DashboardService.set_as_default(dashboard2.id, self.user)

        # Refrescar desde DB
        dashboard1.refresh_from_db()
        dashboard2.refresh_from_db()

        # Verificar
        self.assertFalse(dashboard1.is_default)
        self.assertTrue(dashboard2.is_default)

        # Verificar preferencia actualizada
        preference = UserDashboardPreference.objects.get(user=self.user)
        self.assertEqual(preference.default_dashboard, dashboard2)

    def test_export_config(self):
        """Test exportar configuración."""
        # Crear dashboard con widgets
        dashboard = DashboardConfig.objects.create(
            user=self.user,
            config_name='Test Dashboard',
            description='Test description',
            layout_config={'columns': 12, 'rowHeight': 100}
        )

        WidgetConfig.objects.create(
            dashboard=dashboard,
            widget_type='METRICS_SUMMARY',
            widget_name='Summary',
            position_x=0,
            position_y=0,
            width=12,
            height=4,
            config_data={'metrics': ['total_calls']}
        )

        # Exportar
        export_data = DashboardService.export_config(dashboard.id)

        # Verificar estructura
        self.assertIn('version', export_data)
        self.assertIn('dashboard', export_data)
        self.assertIn('widgets', export_data)

        # Verificar contenido dashboard
        dashboard_data = export_data['dashboard']
        self.assertEqual(dashboard_data['config_name'], 'Test Dashboard')
        self.assertEqual(dashboard_data['description'], 'Test description')

        # Verificar widgets
        widgets_data = export_data['widgets']
        self.assertEqual(len(widgets_data), 1)
        self.assertEqual(widgets_data[0]['widget_type'], 'METRICS_SUMMARY')

    def test_import_config(self):
        """Test importar configuración."""
        import_data = {
            'version': '1.0',
            'dashboard': {
                'config_name': 'Imported Dashboard',
                'description': 'Imported description',
                'layout_config': {'columns': 12},
                'is_public': False
            },
            'widgets': [
                {
                    'widget_type': 'METRICS_SUMMARY',
                    'widget_name': 'Summary Widget',
                    'position_x': 0,
                    'position_y': 0,
                    'width': 12,
                    'height': 4,
                    'config_data': {}
                }
            ]
        }

        # Importar
        dashboard = DashboardService.import_config(import_data, self.user)

        # Verificar dashboard
        self.assertIsNotNone(dashboard)
        self.assertEqual(dashboard.user, self.user)
        self.assertEqual(dashboard.config_name, 'Imported Dashboard')
        self.assertEqual(dashboard.description, 'Imported description')

        # Verificar widgets
        self.assertEqual(dashboard.widgets.count(), 1)
        widget = dashboard.widgets.first()
        self.assertEqual(widget.widget_type, 'METRICS_SUMMARY')
        self.assertEqual(widget.widget_name, 'Summary Widget')

    def test_delete_dashboard(self):
        """Test eliminar dashboard (soft delete)."""
        dashboard = DashboardConfig.objects.create(
            user=self.user,
            config_name='To Delete',
            is_default=True
        )

        # Eliminar
        DashboardService.delete_dashboard(dashboard.id, self.user)

        # Refrescar desde DB
        dashboard.refresh_from_db()

        # Verificar soft delete
        self.assertIsNotNone(dashboard.deleted_at)
        self.assertFalse(dashboard.is_default)

    def test_delete_dashboard_unauthorized(self):
        """Test eliminar dashboard sin permisos."""
        dashboard = DashboardConfig.objects.create(
            user=self.user,
            config_name='Protected'
        )

        # Intentar eliminar con otro usuario
        with self.assertRaises(Exception):
            DashboardService.delete_dashboard(dashboard.id, self.other_user)
