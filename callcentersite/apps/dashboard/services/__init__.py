"""
Services para la app Dashboard.

Services:
- DashboardService: Gestión de dashboards
- WidgetService: Generación de datos para widgets
- FilterService: Aplicación de filtros

FASE 2: Implementación de services.
"""

from apps.dashboard.services.dashboard_service import DashboardService
from apps.dashboard.services.widget_service import WidgetService
from apps.dashboard.services.filter_service import FilterService

__all__ = [
    'DashboardService',
    'WidgetService',
    'FilterService',
]
