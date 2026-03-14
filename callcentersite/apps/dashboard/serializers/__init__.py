"""
Dashboard Serializers - Organización con SRP.

Este paquete organiza los serializers de dashboard aplicando el principio
de Responsabilidad Única (Single Responsibility Principle).

Estructura:
- dashboard_serializers.py: Serialización de configuraciones de dashboards
- widget_serializers.py: Serialización de widgets
- filter_serializers.py: Serialización de filtros guardados
- preference_serializers.py: Serialización de preferencias de usuario

Importaciones centralizadas para mantener compatibilidad:
    from apps.dashboard.serializers import DashboardConfigSerializer
    from apps.dashboard.serializers import WidgetConfigSerializer
    # etc.

Principios aplicados:
- SRP: Cada archivo tiene una responsabilidad única
- DRY: Evitar duplicación de código
- Clean Code: Nombres descriptivos y organización clara
"""

# ====================================================================================
# DASHBOARD SERIALIZERS
# ====================================================================================

from .dashboard_serializers import (
    DashboardConfigSerializer,
    DashboardConfigListSerializer,
    DashboardConfigDetailSerializer,
    DashboardExportSerializer,
    DashboardImportSerializer,
)

# ====================================================================================
# WIDGET SERIALIZERS
# ====================================================================================

from .widget_serializers import (
    WidgetConfigSerializer,
    WidgetConfigCreateSerializer,
    WidgetConfigUpdateSerializer,
    WidgetDataSerializer,
)

# ====================================================================================
# FILTER SERIALIZERS
# ====================================================================================

from .filter_serializers import (
    SavedFilterSerializer,
    SavedFilterListSerializer,
)

# ====================================================================================
# PREFERENCE SERIALIZERS
# ====================================================================================

from .preference_serializers import (
    UserDashboardPreferenceSerializer,
)

# ====================================================================================
# __all__ - Exportaciones públicas
# ====================================================================================

__all__ = [
    # Dashboard serializers
    'DashboardConfigSerializer',
    'DashboardConfigListSerializer',
    'DashboardConfigDetailSerializer',
    'DashboardExportSerializer',
    'DashboardImportSerializer',
    
    # Widget serializers
    'WidgetConfigSerializer',
    'WidgetConfigCreateSerializer',
    'WidgetConfigUpdateSerializer',
    'WidgetDataSerializer',
    
    # Filter serializers
    'SavedFilterSerializer',
    'SavedFilterListSerializer',
    
    # Preference serializers
    'UserDashboardPreferenceSerializer',
]

# ====================================================================================
# RESUMEN
# ====================================================================================
#
# Total Serializers: 12
#
# Dashboards (5):
#   [SUCCESS] DashboardConfigSerializer - Dashboard básico
#   [SUCCESS] DashboardConfigListSerializer - Para listados
#   [SUCCESS] DashboardConfigDetailSerializer - Con widgets anidados
#   [SUCCESS] DashboardExportSerializer - Para exportación
#   [SUCCESS] DashboardImportSerializer - Para importación
#
# Widgets (4):
#   [SUCCESS] WidgetConfigSerializer - Widget básico
#   [SUCCESS] WidgetConfigCreateSerializer - Para creación
#   [SUCCESS] WidgetConfigUpdateSerializer - Para actualización
#   [SUCCESS] WidgetDataSerializer - Para respuestas de datos
#
# Filters (2):
#   [SUCCESS] SavedFilterSerializer - Filtro completo
#   [SUCCESS] SavedFilterListSerializer - Para listados
#
# Preferences (1):
#   [SUCCESS] UserDashboardPreferenceSerializer - Preferencias de usuario
#
# Características:
#   [SUCCESS] SRP aplicado (4 archivos con responsabilidades únicas)
#   [SUCCESS] Validaciones robustas en cada serializer
#   [SUCCESS] Campos enriched (user_username, etc.)
#   [SUCCESS] Integración con FilterService
#   [SUCCESS] Import/Export de dashboards
#   [SUCCESS] Compatibilidad mantenida
#
# ====================================================================================
