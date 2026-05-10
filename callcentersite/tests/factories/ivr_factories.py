"""
Factories para apps/ivr (BD IVR readonly).
"""
# =============================================================================
# DEUDA TÉCNICA — PENDIENTE
# =============================================================================
# Fecha de eliminación: 2026-03-21
# Motivo: Las factories importaban 11 modelos que no existen en el código
#         actual (QuarterlyReport, TransferReport, AbandonedReport, etc.).
#         El único modelo activo es TblTempPruebaIvr, cuyo seed de datos
#         es responsabilidad del script MariaDB (schema_temp_prueba.sh).
#         No se requiere factory para este modelo ya que los datos vienen
#         del provisioner, no de Python.
#         Reactivar cuando:
#           1. Los modelos IVR completos estén implementados
#           2. Se requieran factories para tests de integración
# Ver: documentos/planes/PLAN_IVR_SIMPLIFICACION_20260321.md
# =============================================================================
#
# import factory
# from factory.django import DjangoModelFactory
# from factory import fuzzy
# from datetime import date, datetime, timedelta
# from decimal import Decimal
# from apps.ivr.models import (
#     QuarterlyReport,    # NO EXISTE
#     TransferReport,     # NO EXISTE
#     AbandonedReport,    # NO EXISTE
#     ClientReport,       # NO EXISTE
#     CallRecordQ1,       # NO EXISTE
#     CallRecordQ2,       # NO EXISTE
#     CallRecordQ3,       # NO EXISTE
#     CallRecordQ4,       # NO EXISTE
#     MonthlyStats,       # NO EXISTE
#     HourlyStats,        # NO EXISTE
#     DIDReport,          # NO EXISTE
# )
#
# class QuarterlyReportFactory(DjangoModelFactory): ...
# class TransferReportFactory(DjangoModelFactory): ...
# ... (23 factories desactivadas)
