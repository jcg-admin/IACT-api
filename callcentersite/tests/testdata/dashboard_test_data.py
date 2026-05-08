"""
Factories para apps/dashboard/.

Factory boy para generación de datos test de dashboards.
Basado en análisis ANALISIS_APP_DASHBOARD_v3_0_0.md (5 partes).

NOTA: Esta app aún no está implementada. Estas factories estarán
listas para cuando se implemente.

CLEAN_CODE v3.0.1: Nombres auto-documentados.
"""

import factory
from factory.django import DjangoModelFactory
from factory import fuzzy
from datetime import datetime, timedelta
from decimal import Decimal


# NOTA TEMPORAL: Imports comentados hasta que se implementen los modelos
# from apps.dashboard.models import (
#     DashboardConfig,
#     WidgetConfig,
#     SavedFilter,
#     UserDashboardPreference,
# )
from tests.testdata.user_test_data import UserTestData


# ============================================================================
# DASHBOARDCONFIG FACTORIES
# ============================================================================

class DashboardConfigTestData(DjangoModelFactory):
    """
    Factory para DashboardConfig (configuración de dashboard).
    
    Uso básico:
        config = DashboardConfigTestData(
            user=user,
            config_name='My Dashboard'
        )
    
    Con layout:
        config = DashboardConfigTestData(
            layout_config={
                'widgets': ['calls', 'transfers', 'abandonments'],
                'columns': 3
            }
        )
    """
    
    class Meta:
        # model = DashboardConfig  # Descomentar cuando se implemente
        abstract = True  # Temporal
    
    user = factory.SubFactory(UserTestData)
    config_name = factory.Sequence(lambda n: f'Dashboard {n}')
    description = factory.Faker('sentence', nb_words=12)
    layout_config = factory.LazyFunction(lambda: {
        'columns': 3,
        'widgets': [
            {'type': 'calls', 'position': 0},
            {'type': 'transfers', 'position': 1},
            {'type': 'abandonments', 'position': 2},
        ]
    })
    is_default = False
    is_public = False
    created_at = factory.Faker('date_time_this_month')
    updated_at = factory.LazyAttribute(lambda obj: obj.created_at)


class DefaultDashboardTestData(DashboardConfigTestData):
    """Factory para dashboard por defecto del usuario."""
    config_name = 'Default Dashboard'
    is_default = True


class PublicDashboardTestData(DashboardConfigTestData):
    """Factory para dashboard público (compartido)."""
    config_name = 'Public Dashboard'
    is_public = True


# ============================================================================
# WIDGETCONFIG FACTORIES
# ============================================================================

class WidgetConfigTestData(DjangoModelFactory):
    """
    Factory para WidgetConfig (configuración de widget).
    
    Uso básico:
        widget = WidgetConfigTestData(
            dashboard=dashboard,
            widget_type='CALLS_CHART'
        )
    """
    
    class Meta:
        # model = WidgetConfig  # Descomentar cuando se implemente
        abstract = True  # Temporal
    
    dashboard = factory.SubFactory(DashboardConfigTestData)
    widget_type = factory.Iterator([
        'CALLS_CHART',
        'TRANSFERS_CHART',
        'ABANDONMENTS_CHART',
        'TOP_CLIENTS',
        'METRICS_SUMMARY',
        'HOURLY_STATS',
    ])
    widget_name = factory.LazyAttribute(
        lambda obj: f'{obj.widget_type.replace("_", " ").title()}'
    )
    position_x = 0
    position_y = 0
    width = 6
    height = 4
    config_data = factory.LazyFunction(lambda: {
        'chart_type': 'line',
        'show_legend': True,
        'time_range': 'last_30_days'
    })
    is_visible = True
    refresh_interval_seconds = 300  # 5 minutos
    created_at = factory.Faker('date_time_this_month')


class CallsChartWidgetTestData(WidgetConfigTestData):
    """Factory para widget de gráfico de llamadas."""
    widget_type = 'CALLS_CHART'
    widget_name = 'Calls Chart'
    config_data = factory.LazyFunction(lambda: {
        'chart_type': 'line',
        'metrics': ['total', 'answered', 'abandoned'],
        'time_range': 'last_30_days'
    })


class TransfersChartWidgetTestData(WidgetConfigTestData):
    """Factory para widget de gráfico de transferencias."""
    widget_type = 'TRANSFERS_CHART'
    widget_name = 'Transfers Chart'
    config_data = factory.LazyFunction(lambda: {
        'chart_type': 'bar',
        'group_by': 'menu_option',
        'time_range': 'last_7_days'
    })


class AbandonmentsChartWidgetTestData(WidgetConfigTestData):
    """Factory para widget de gráfico de abandonos."""
    widget_type = 'ABANDONMENTS_CHART'
    widget_name = 'Abandonments Chart'
    config_data = factory.LazyFunction(lambda: {
        'chart_type': 'line',
        'show_rate': True,
        'threshold': 0.15
    })


class TopClientsWidgetTestData(WidgetConfigTestData):
    """Factory para widget de top clientes."""
    widget_type = 'TOP_CLIENTS'
    widget_name = 'Top 5 Clients'
    config_data = factory.LazyFunction(lambda: {
        'limit': 5,
        'sort_by': 'total_calls',
        'time_range': 'current_quarter'
    })


class MetricsSummaryWidgetTestData(WidgetConfigTestData):
    """Factory para widget de resumen de métricas."""
    widget_type = 'METRICS_SUMMARY'
    widget_name = 'Metrics Summary'
    config_data = factory.LazyFunction(lambda: {
        'metrics': [
            'total_calls',
            'abandonment_rate',
            'avg_duration',
            'unique_clients'
        ]
    })


# ============================================================================
# SAVEDFILTER FACTORIES
# ============================================================================

class SavedFilterTestData(DjangoModelFactory):
    """
    Factory para SavedFilter (filtros guardados).
    
    Uso básico:
        filter = SavedFilterTestData(
            user=user,
            filter_name='Q1 2025 Calls'
        )
    """
    
    class Meta:
        # model = SavedFilter  # Descomentar cuando se implemente
        abstract = True  # Temporal
    
    user = factory.SubFactory(UserTestData)
    filter_name = factory.Sequence(lambda n: f'Filter {n}')
    filter_type = factory.Iterator(['CALLS', 'TRANSFERS', 'ABANDONED', 'CLIENTS'])
    filter_config = factory.LazyFunction(lambda: {
        'date_from': '2025-01-01',
        'date_to': '2025-03-31',
        'did': None,
        'client_id': None
    })
    is_public = False
    created_at = factory.Faker('date_time_this_month')


class QuarterlyFilterTestData(SavedFilterTestData):
    """Factory para filtro trimestral."""
    filter_name = 'Q1 2025'
    filter_config = factory.LazyFunction(lambda: {
        'year': 2025,
        'quarter': 1,
        'date_from': '2025-01-01',
        'date_to': '2025-03-31'
    })


class MonthlyFilterTestData(SavedFilterTestData):
    """Factory para filtro mensual."""
    filter_name = factory.LazyAttribute(lambda obj: f'Month Filter {obj.pk}')
    filter_config = factory.LazyFunction(lambda: {
        'year': 2025,
        'month': 1,
        'date_from': '2025-01-01',
        'date_to': '2025-01-31'
    })


# ============================================================================
# USERDASHBOARDPREFERENCE FACTORIES
# ============================================================================

class UserDashboardPreferenceTestData(DjangoModelFactory):
    """
    Factory para UserDashboardPreference (preferencias usuario).
    
    Uso básico:
        pref = UserDashboardPreferenceTestData(
            user=user,
            default_dashboard=dashboard
        )
    """
    
    class Meta:
        # model = UserDashboardPreference  # Descomentar cuando se implemente
        abstract = True  # Temporal
    
    user = factory.SubFactory(UserTestData)
    default_dashboard = factory.SubFactory(DashboardConfigTestData)
    theme = factory.Iterator(['light', 'dark', 'auto'])
    refresh_enabled = True
    refresh_interval_seconds = 300
    show_notifications = True
    preferences = factory.LazyFunction(lambda: {
        'language': 'es',
        'timezone': 'America/Santiago',
        'date_format': 'DD/MM/YYYY'
    })


# ============================================================================
# HELPER FACTORIES (Complex scenarios)
# ============================================================================

class CompleteDashboardTestData:
    """
    Factory que crea dashboard completo con widgets.
    
    Uso:
        dashboard = CompleteDashboardTestData.create_dashboard(
            user=user,
            widgets=['calls', 'transfers', 'abandonments']
        )
        # Retorna dict con config y widgets
    """
    
    @staticmethod
    def create_dashboard(user, widget_types=None):
        """
        Crea dashboard completo con widgets.
        
        Args:
            user: Usuario dueño
            widget_types: Lista de tipos de widgets (opcional)
        
        Returns:
            dict: {
                'config': DashboardConfig,
                'widgets': [WidgetConfig, ...]
            }
        """
        if widget_types is None:
            widget_types = ['CALLS_CHART', 'TRANSFERS_CHART', 'ABANDONMENTS_CHART']
        
        config = DashboardConfigTestData(user=user)
        
        widgets = []
        for i, widget_type in enumerate(widget_types):
            widget = WidgetConfigTestData(
                dashboard=config,
                widget_type=widget_type,
                position_x=i % 3,
                position_y=i // 3
            )
            widgets.append(widget)
        
        return {
            'config': config,
            'widgets': widgets
        }


class UserWithDashboardTestData(UserTestData):
    """
    Factory que crea Usuario con dashboard completo.
    
    Uso:
        user = UserWithDashboardTestData()
        # Usuario con dashboard y 3 widgets automáticamente
    """
    
    @factory.post_generation
    def dashboard(self, create, extracted, **kwargs):
        if not create:
            return
        
        # Crear dashboard por defecto
        config = DefaultDashboardTestData(user=self)
        
        # Crear 3 widgets estándar
        CallsChartWidgetTestData(dashboard=config, position_x=0, position_y=0)
        TransfersChartWidgetTestData(dashboard=config, position_x=1, position_y=0)
        AbandonmentsChartWidgetTestData(dashboard=config, position_x=2, position_y=0)


# ============================================================================
# TOTAL FACTORIES: 17
# 
# DashboardConfig Factories (3):
#   - DashboardConfigTestData
#   - DefaultDashboardTestData
#   - PublicDashboardTestData
# 
# WidgetConfig Factories (6):
#   - WidgetConfigTestData
#   - CallsChartWidgetTestData
#   - TransfersChartWidgetTestData
#   - AbandonmentsChartWidgetTestData
#   - TopClientsWidgetTestData
#   - MetricsSummaryWidgetTestData
# 
# SavedFilter Factories (3):
#   - SavedFilterTestData
#   - QuarterlyFilterTestData
#   - MonthlyFilterTestData
# 
# UserDashboardPreference Factories (1):
#   - UserDashboardPreferenceTestData
# 
# Helper Factories (2):
#   - CompleteDashboardTestData (static)
#   - UserWithDashboardTestData
# 
# NOTA: Todas las factories están marcadas como abstract=True temporalmente.
# Cambiar a model=X cuando se implementen los modelos en apps/dashboard/.
# 
# CLEAN_CODE v3.0.1: Nombres auto-documentados [SUCCESS]
# ============================================================================
