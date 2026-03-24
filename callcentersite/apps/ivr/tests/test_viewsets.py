"""
Tests para viewsets de apps/ivr - IACT Call Center System.
"""
# =============================================================================
# DEUDA TÉCNICA — PENDIENTE
# =============================================================================
# Fecha de eliminación: 2026-03-21
# Motivo: Tests de CallLogViewSet desactivados. La tabla call_logs no existe
#         en ivr_legacy y el modelo CallLog fue reemplazado por TblTempPruebaIvr.
#         Reactivar cuando:
#           1. scripts/provisioners/mariadb/schema.sh esté implementado
#           2. La tabla call_logs exista en ivr_legacy con datos reales
#           3. Se requieran tests de integración con MariaDB real
# Ver: documentos/planes/PLAN_IVR_SIMPLIFICACION_20260321.md
# =============================================================================
#
# from datetime import date
# from django.urls import reverse
# from rest_framework import status
# from rest_framework.test import APITestCase
# from django.contrib.auth import get_user_model
# from apps.ivr.models import CallLog
#
# User = get_user_model()
#
#
# class CallLogViewSetTestCase(APITestCase):
#     def setUp(self):
#         self.user = User.objects.create_user(
#             username='testuser', password='testpass123', email='test@example.com'
#         )
#         self.client.force_authenticate(user=self.user)
#         self.calllog1 = CallLog.objects.create(
#             fecha=date(2025, 1, 15), telefono='912345678',
#             servicio_800='800-123-4567', total_llamadas=100,
#             llamadas_contestadas=85, llamadas_abandonadas=15
#         )
#         self.calllog2 = CallLog.objects.create(
#             fecha=date(2025, 1, 16), telefono='987654321',
#             servicio_800='800-987-6543', total_llamadas=50,
#             llamadas_contestadas=40, llamadas_abandonadas=10
#         )
#         self.calllog3 = CallLog.objects.create(
#             fecha=date(2025, 1, 17), telefono='912345678',
#             servicio_800='800-123-4567', total_llamadas=200,
#             llamadas_contestadas=180, llamadas_abandonadas=20
#         )
#
#     def test_list_call_logs(self): ...
#     def test_retrieve_call_log(self): ...
#     def test_filter_by_fecha(self): ...
#     def test_filter_by_servicio_800(self): ...
#     def test_ordering_by_fecha_desc(self): ...
#     def test_readonly_no_create(self): ...
#     def test_readonly_no_update(self): ...
#     def test_readonly_no_delete(self): ...
#     def test_metrics_calculation_zero_division(self): ...
