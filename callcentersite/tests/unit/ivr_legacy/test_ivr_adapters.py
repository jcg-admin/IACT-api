"""
Tests IVRAdapter.
"""
# =============================================================================
# DEUDA TÉCNICA — PENDIENTE
# =============================================================================
# Fecha de eliminación: 2026-03-21
# Motivo: IVRAdapter desactivado (ver adapters.py). La tabla call_logs
#         no existe en ivr_legacy. Estos tests probaban el adapter
#         que accedía a call_logs via QuerySet.
#         Reactivar cuando:
#           1. La tabla call_logs exista en ivr_legacy
#           2. IVRAdapter sea reactivado en apps/ivr/adapters.py
# Ver: documentos/planes/PLAN_IVR_SIMPLIFICACION_20260321.md
# =============================================================================
#
# import pytest
# from datetime import date
# from apps.ivr.adapters import IVRAdapter
#
# class TestIVRAdapter:
#     def test_adapter_instantiation(self):
#         adapter = IVRAdapter()
#         assert adapter is not None
#
#     def test_adapter_has_get_calls_method(self):
#         adapter = IVRAdapter()
#         assert hasattr(adapter, 'get_calls')
#         assert callable(adapter.get_calls)
#
#     def test_get_calls_returns_list(self):
#         adapter = IVRAdapter()
#         fecha = date(2024, 1, 15)
#         result = adapter.get_calls(fecha_inicio=fecha, fecha_fin=fecha)
#         assert isinstance(result, list)
#
#     def test_get_calls_returns_dicts(self):
#         adapter = IVRAdapter()
#         fecha = date(2024, 1, 15)
#         result = adapter.get_calls(fecha_inicio=fecha, fecha_fin=fecha)
#         if len(result) > 0:
#             assert isinstance(result[0], dict)
