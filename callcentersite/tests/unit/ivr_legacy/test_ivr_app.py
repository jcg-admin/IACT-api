"""
Tests app ivr_legacy.
"""
# =============================================================================
# DEUDA TÉCNICA — PENDIENTE
# =============================================================================
# Fecha de eliminación: 2026-03-21
# Motivo: Test de import 'ivr_legacy' apuntaba a un módulo inexistente.
#         El app se llama 'ivr' (apps.ivr), no 'ivr_legacy'.
#         Reactivar / corregir cuando se requieran tests de la app.
# Ver: documentos/planes/PLAN_IVR_SIMPLIFICACION_20260321.md
# =============================================================================
#
# def test_ivr_legacy_app_importable():
#     from apps import ivr_legacy    # ERROR: no existe apps.ivr_legacy
#     assert ivr_legacy is not None
#
# def test_ivr_models_importable():
#     from apps.ivr import models
#     assert hasattr(models, '__file__')
