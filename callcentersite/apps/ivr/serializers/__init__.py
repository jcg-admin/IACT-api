"""
IVR Serializers.

Serializer activo:
    TblTempPruebaIvrSerializer — consume tbl_temp_prueba_ivr (MariaDB)

CNST-003: READ-ONLY (datos legacy de MariaDB ivr_legacy)
"""

# =============================================================================
# DEUDA TÉCNICA — PENDIENTE
# =============================================================================
# Fecha de eliminación: 2026-03-21
# Los serializers de CallLog fueron desactivados junto con el modelo.
# Reactivar cuando el schema real de ivr_legacy esté provisionado.
# Ver: documentos/planes/PLAN_IVR_SIMPLIFICACION_20260321.md
# =============================================================================
#
# from .calllog_serializers import (
#     CallLogSerializer,
#     CallLogListSerializer,
#     CallLogStatsSerializer,
# )

from .temp_prueba_serializer import TblTempPruebaIvrSerializer

__all__ = [
    'TblTempPruebaIvrSerializer',
]
