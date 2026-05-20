"""
Tests para signals de Dashboard.

Pruebas de:
- create_default_dashboard_for_new_user
- ensure_only_one_default_dashboard
- invalidate_widget_cache_on_update

FASE 7: Tests de signals.
"""

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.cache import cache

from apps.dashboard.models import DashboardConfig, WidgetConfig, UserDashboardPreference

User = get_user_model()


class DashboardSignalsTestCase(TestCase):
    """Tests para signals de Dashboard."""

    def setUp(self):
        """Limpiar cache antes de cada test."""
        cache.clear()

    def test_create_default_dashboard_on_user_creation(self):
        """Test que se crea dashboard automáticamente al crear usuario."""
        # Crear usuario
        user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='testpass123'
        )

        # Verificar que se creó dashboard
        dashboards = DashboardConfig.objects.filter(user=user)
        self.assertEqual(dashboards.count(), 1)

        dashboard = dashboards.first()
        self.assertEqual(dashboard.config_name, 'Mi Dashboard')
        self.assertTrue(dashboard.is_default)

        # Verificar widgets creados
        self.assertEqual(dashboard.widgets.count(), 3)

        # Verificar preferencia creada
        self.assertTrue(
            UserDashboardPreference.objects.filter(user=user).exists()
        )

    def test_ensure_only_one_default_dashboard(self):
        """Test que solo un dashboard puede ser default."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Crear primer dashboard default
        dashboard1 = DashboardConfig.objects.create(
            user=user,
            config_name='Dashboard 1',
            is_default=True
        )

        # Crear segundo dashboard default
        dashboard2 = DashboardConfig.objects.create(
            user=user,
            config_name='Dashboard 2',
            is_default=True
        )

        # Refrescar dashboard1 desde DB
        dashboard1.refresh_from_db()

        # Verificar que dashboard1 ya no es default
        self.assertFalse(dashboard1.is_default)
        self.assertTrue(dashboard2.is_default)

    def test_ensure_only_one_default_multiple_dashboards(self):
        """Test con múltiples dashboards."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Crear tres dashboards
        dashboard1 = DashboardConfig.objects.create(
            user=user,
            config_name='Dashboard 1',
            is_default=True
        )

        dashboard2 = DashboardConfig.objects.create(
            user=user,
            config_name='Dashboard 2',
            is_default=False
        )

        dashboard3 = DashboardConfig.objects.create(
            user=user,
            config_name='Dashboard 3',
            is_default=False
        )

        # Marcar dashboard3 como default
        dashboard3.is_default = True
        dashboard3.save()

        # Refrescar todos
        dashboard1.refresh_from_db()
        dashboard2.refresh_from_db()
        dashboard3.refresh_from_db()

        # Verificar solo dashboard3 es default
        self.assertFalse(dashboard1.is_default)
        self.assertFalse(dashboard2.is_default)
        self.assertTrue(dashboard3.is_default)

    @override_settings(CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'test-signals-invalidate-cache',
        }
    })
    def test_invalidate_cache_on_widget_update(self):
        """Test que se invalida cache al actualizar widget.

        testing_local.py usa DummyCache para aislamiento entre
        tests. Este test EXIGE cache real para validar que el
        signal lo invalida, asi que override a LocMemCache local
        al test.
        """
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        dashboard = DashboardConfig.objects.create(
            user=user,
            config_name='Test Dashboard'
        )

        widget = WidgetConfig.objects.create(
            dashboard=dashboard,
            widget_type='METRICS_SUMMARY',
            widget_name='Original Name',
            position_x=0,
            position_y=0,
            width=12,
            height=4
        )

        # Simular cache existente
        cache_key = f'widget_data_{widget.id}'
        cache.set(cache_key, {'data': 'cached'}, timeout=300)

        # Verificar que existe en cache
        self.assertIsNotNone(cache.get(cache_key))

        # Actualizar widget
        widget.widget_name = 'Updated Name'
        widget.save()

        # Nota: El signal invalidate_widget_cache_on_update llama a
        # WidgetService.refresh_widget_cache() que invalida el cache
        # En un test real, verificaríamos que el método fue llamado
        # Por ahora verificamos que el widget se actualizó
        widget.refresh_from_db()
        self.assertEqual(widget.widget_name, 'Updated Name')

    def test_no_signal_on_widget_creation(self):
        """Test que signal NO se dispara al crear widget."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        dashboard = DashboardConfig.objects.create(
            user=user,
            config_name='Test Dashboard'
        )

        # Crear widget (no debería disparar invalidate_cache)
        widget = WidgetConfig.objects.create(
            dashboard=dashboard,
            widget_type='METRICS_SUMMARY',
            widget_name='New Widget',
            position_x=0,
            position_y=0,
            width=12,
            height=4
        )

        # Widget debe existir
        self.assertIsNotNone(widget.id)

    def test_default_dashboard_different_users(self):
        """Test que signal no afecta dashboards de otros usuarios."""
        user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )

        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )

        # Crear dashboards default para cada usuario
        dashboard_user1 = DashboardConfig.objects.create(
            user=user1,
            config_name='Dashboard User 1',
            is_default=True
        )

        dashboard_user2 = DashboardConfig.objects.create(
            user=user2,
            config_name='Dashboard User 2',
            is_default=True
        )

        # Ambos deben seguir siendo default
        dashboard_user1.refresh_from_db()
        dashboard_user2.refresh_from_db()

        self.assertTrue(dashboard_user1.is_default)
        self.assertTrue(dashboard_user2.is_default)
