"""
Tests modelos ivr_legacy.
"""
# =============================================================================
# DEUDA TÉCNICA — PENDIENTE
# =============================================================================
# Fecha de eliminación: 2026-03-21
# Motivo: Tests de CallLog desactivados. El modelo fue reemplazado por
#         TblTempPruebaIvr. Los tests del nuevo modelo están en:
#         tests/unit/ivr_legacy/test_tbl_temp_prueba_ivr.py
#         Reactivar cuando el schema real de ivr_legacy esté provisionado.
# Ver: documentos/planes/PLAN_IVR_SIMPLIFICACION_20260321.md
# =============================================================================
#
# import pytest
# from datetime import date
#
# @pytest.mark.django_db
# class TestCallLogModel:
#     def test_calllog_importable(self):
#         from apps.ivr.models import CallLog
#         assert CallLog is not None
#
#     def test_calllog_model_structure(self):
#         from apps.ivr.models import CallLog
#         assert hasattr(CallLog, 'fecha')
#         assert hasattr(CallLog, 'telefono')
#         assert hasattr(CallLog, 'servicio_800')
#         assert hasattr(CallLog, 'total_llamadas')
#
#     def test_calllog_meta_unmanaged(self):
#         from apps.ivr.models import CallLog
#         assert CallLog._meta.managed is False
#
#     def test_calllog_meta_db_table(self):
#         from apps.ivr.models import CallLog
#         assert CallLog._meta.db_table == 'call_logs'
