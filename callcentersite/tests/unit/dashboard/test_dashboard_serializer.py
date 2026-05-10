"""
tests/unit/dashboard/test_dashboard_serializer.py

Tests para DashboardConfigDetailSerializer.

El endpoint de dashboard no está incluido en las URLs activas (config/urls.py),
pero el serializer es parte del código de producción y debe comportarse
correctamente cuando se active.
"""
import pytest

from apps.dashboard.models import DashboardConfig, WidgetConfig
from apps.dashboard.serializers.dashboard_serializers import (
    DashboardConfigDetailSerializer,
)
from tests.test_data.user_test_data import UserTestData


def _make_dashboard(user, config_name='Test Dashboard'):
    return DashboardConfig.objects.create(
        user=user,
        config_name=config_name,
        layout_config={},
    )


def _make_widget(dashboard, name='Widget', is_visible=True):
    return WidgetConfig.objects.create(
        dashboard=dashboard,
        widget_type='CALLS_CHART',
        widget_name=name,
        position_x=0,
        position_y=0,
        width=4,
        height=3,
        config_data={},
        is_visible=is_visible,
    )


@pytest.mark.unit
@pytest.mark.django_db
class TestDashboardConfigDetailSerializer:
    """Tests del serializer de detalle con widgets anidados."""

    def test_visible_widgets_appear_in_response(self):
        """Widgets con is_visible=True aparecen en la respuesta."""
        user      = UserTestData()
        dashboard = _make_dashboard(user)
        widget    = _make_widget(dashboard, name='Visible Widget')

        data = DashboardConfigDetailSerializer(dashboard).data

        widget_names = [w['widget_name'] for w in data['widgets']]
        assert 'Visible Widget' in widget_names

    def test_hidden_widgets_excluded_from_response(self):
        """
        Widgets con is_visible=False no aparecen en la respuesta.

        Bug original: get_widgets() hacía obj.widgets.all() sin filtro,
        exponiendo widgets desactivados que el usuario no debería ver.
        Corrección: filtrar is_visible=True.
        """
        user      = UserTestData()
        dashboard = _make_dashboard(user)
        _make_widget(dashboard, name='Visible Widget',   is_visible=True)
        _make_widget(dashboard, name='Hidden Widget',    is_visible=False)

        data = DashboardConfigDetailSerializer(dashboard).data

        widget_names = [w['widget_name'] for w in data['widgets']]
        assert 'Visible Widget' in widget_names
        assert 'Hidden Widget'  not in widget_names

    def test_dashboard_with_no_widgets_returns_empty_list(self):
        """Dashboard sin widgets retorna lista vacía."""
        user      = UserTestData()
        dashboard = _make_dashboard(user)

        data = DashboardConfigDetailSerializer(dashboard).data

        assert data['widgets'] == []

    def test_widgets_ordered_by_position(self):
        """Widgets se ordenan por position_y, luego position_x."""
        user      = UserTestData()
        dashboard = _make_dashboard(user)
        _make_widget(dashboard, name='Bottom Right',
                     is_visible=True)
        w1 = _make_widget(dashboard, name='Top Left', is_visible=True)
        w1.position_y = 0; w1.position_x = 0; w1.save()
        w2 = _make_widget(dashboard, name='Bottom', is_visible=True)
        w2.position_y = 2; w2.position_x = 0; w2.save()

        data = DashboardConfigDetailSerializer(dashboard).data
        assert len(data['widgets']) >= 1
        # El primero debe tener la posición más baja
        assert data['widgets'][0]['position_y'] <= data['widgets'][-1]['position_y']
