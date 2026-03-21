"""
ViewSets para apps/ivr - IACT Call Center System.

API REST READ-ONLY para tbl_temp_prueba_ivr (MariaDB ivr_legacy).

CNST-003: Solo GET permitido — NO create, update, delete.
Schema creado por scripts/provisioners/mariadb/schema_temp_prueba.sh
"""
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import TblTempPruebaIvr
from .serializers import TblTempPruebaIvrSerializer


# =============================================================================
# DEUDA TÉCNICA — PENDIENTE
# =============================================================================
# Fecha de eliminación: 2026-03-21
# CallLogViewSet desactivado junto con el modelo CallLog.
# Reactivar cuando el schema real de ivr_legacy esté provisionado.
# Ver: documentos/planes/PLAN_IVR_SIMPLIFICACION_20260321.md
# =============================================================================
#
# class CallLogViewSet(viewsets.ReadOnlyModelViewSet):
#     queryset         = CallLog.objects.all()
#     serializer_class = CallLogSerializer
#     ...


class TblTempPruebaIvrViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API READ-ONLY para tbl_temp_prueba_ivr.

    Endpoints:
        GET /api/ivr/temp-prueba/        — lista paginada de 3000 registros
        GET /api/ivr/temp-prueba/{id}/   — detalle de un registro

    NO permite (READ-ONLY, CNST-003):
        POST, PUT, PATCH, DELETE

    Permisos:
        IsAuthenticated
    """

    queryset         = TblTempPruebaIvr.objects.using('ivr').all()
    serializer_class = TblTempPruebaIvrSerializer
    permission_classes = [IsAuthenticated]
