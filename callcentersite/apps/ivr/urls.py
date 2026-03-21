"""
URLs para apps/ivr - IACT Call Center System.

Rutas activas:
    GET /api/ivr/temp-prueba/       — lista tbl_temp_prueba_ivr
    GET /api/ivr/temp-prueba/{id}/  — detalle

CNST-003: API READ-ONLY (MariaDB ivr_legacy)
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import viewsets


router = DefaultRouter()
router.register(r'temp-prueba', viewsets.TblTempPruebaIvrViewSet, basename='temp-prueba-ivr')

# =============================================================================
# DEUDA TÉCNICA — PENDIENTE
# =============================================================================
# Ruta call-logs desactivada junto con CallLogViewSet.
# Reactivar cuando el schema real de ivr_legacy esté provisionado.
# Ver: documentos/planes/PLAN_IVR_SIMPLIFICACION_20260321.md
# =============================================================================
# router.register(r'call-logs', viewsets.CallLogViewSet, basename='calllog')

app_name = 'ivr'

urlpatterns = [
    path('api/', include(router.urls)),
]
