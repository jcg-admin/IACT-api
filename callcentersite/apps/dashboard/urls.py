"""
URLs para la app Dashboard.

Registra routers DRF para:
- DashboardConfigViewSet
- WidgetConfigViewSet
- SavedFilterViewSet
- UserDashboardPreferenceViewSet

FASE 6: Implementación de URLs REST.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.dashboard.viewsets import (
    DashboardConfigViewSet,
    WidgetConfigViewSet,
    SavedFilterViewSet,
    UserDashboardPreferenceViewSet
)

# Crear router
router = DefaultRouter()

# Registrar ViewSets
router.register(r'dashboards', DashboardConfigViewSet, basename='dashboard')
router.register(r'widgets', WidgetConfigViewSet, basename='widget')
router.register(r'filters', SavedFilterViewSet, basename='filter')
router.register(r'preferences', UserDashboardPreferenceViewSet, basename='preference')

# URLs
app_name = 'dashboard'

urlpatterns = [
    # Router REST API
    path('', include(router.urls)),
]
