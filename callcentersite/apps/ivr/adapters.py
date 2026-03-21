"""
Adapters para IVR Legacy.

CNST-003: Acceso READ-ONLY a MariaDB legacy.
"""
# =============================================================================
# DEUDA TÉCNICA — PENDIENTE
# =============================================================================
# Fecha de eliminación: 2026-03-21
# Motivo: IVRAdapter desactivado. La tabla call_logs no existe en ivr_legacy.
#         El schema real de ivr_legacy es responsabilidad de los scripts
#         MariaDB, no de Django.
#         Reactivar cuando:
#           1. scripts/provisioners/mariadb/schema.sh esté implementado
#           2. La tabla call_logs exista en ivr_legacy (producción)
#           3. El pipeline ETL requiera datos reales de IVR
# Ver: documentos/planes/PLAN_IVR_SIMPLIFICACION_20260321.md
# =============================================================================
#
# from datetime import date
# from typing import List, Dict
# from .models import CallLog
#
#
# class IVRAdapter:
#     """
#     Adapter para acceder a IVR legacy DB.
#
#     CNST-003:
#     - Acceso READ-ONLY a ivr_legacy DB
#     - Usuario ivr_readonly (SOLO SELECT)
#     - Database Router enforza READ-ONLY
#     """
#
#     def get_calls(self, fecha_inicio: date, fecha_fin: date) -> List[Dict]:
#         calls = []
#         try:
#             queryset = CallLog.objects.using('ivr').filter(
#                 fecha__gte=fecha_inicio,
#                 fecha__lte=fecha_fin
#             ).order_by('fecha', 'telefono')
#             for call in queryset:
#                 calls.append({
#                     'fecha': call.fecha,
#                     'telefono': call.telefono,
#                     'servicio_800': call.servicio_800,
#                     'total_llamadas': call.total_llamadas,
#                     'llamadas_contestadas': call.llamadas_contestadas,
#                     'llamadas_abandonadas': call.llamadas_abandonadas,
#                 })
#         except Exception:
#             pass
#         return calls
