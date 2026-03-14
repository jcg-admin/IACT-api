"""
Factories para apps/ivr_legacy/ (BD IVR readonly).

Factory boy para generación de datos test de IVR/ETL.
Basado en análisis ANALISIS_APP_IVR_v3_1_0.md (4 partes).

CRÍTICO: En producción usa MariaDB readonly, en tests usa SQLite.
CNST-002: Dual DB (PostgreSQL + MariaDB readonly).
CLEAN_CODE v3.0.1: Nombres auto-documentados.
"""

import factory
from factory.django import DjangoModelFactory
from factory import fuzzy
from datetime import date, datetime, timedelta
from decimal import Decimal
from apps.ivr.models import (
    QuarterlyReport,
    TransferReport,
    AbandonedReport,
    ClientReport,
    CallRecordQ1,
    CallRecordQ2,
    CallRecordQ3,
    CallRecordQ4,
    MonthlyStats,
    HourlyStats,
    DIDReport,
)


# ============================================================================
# QUARTERLY REPORT FACTORIES
# ============================================================================

class QuarterlyReportFactory(DjangoModelFactory):
    """
    Factory para QuarterlyReport (resumen trimestral).
    
    IMPORTANTE: Simula datos de BD IVR (MariaDB en prod, SQLite en tests).
    
    Uso básico:
        report = QuarterlyReportFactory(year=2025, quarter=1)
    
    Batch (4 trimestres):
        reports = [
            QuarterlyReportFactory(year=2025, quarter=q)
            for q in range(1, 5)
        ]
    """
    
    class Meta:
        model = QuarterlyReport
        django_get_or_create = ('year', 'quarter')
    
    year = 2025
    quarter = factory.Iterator([1, 2, 3, 4])
    total_calls = factory.Faker('pyint', min_value=5000, max_value=50000)
    unique_clients = factory.LazyAttribute(
        lambda obj: int(obj.total_calls * 0.6)  # ~60% clientes únicos
    )
    avg_duration_seconds = factory.Faker('pyint', min_value=120, max_value=600)
    total_duration_hours = factory.LazyAttribute(
        lambda obj: Decimal(obj.total_calls * obj.avg_duration_seconds / 3600)
    )
    abandonment_rate = factory.Faker('pyfloat', min_value=0.05, max_value=0.25)


class Q1ReportFactory(QuarterlyReportFactory):
    """Factory para reporte Q1 (Enero-Marzo)."""
    quarter = 1


class Q2ReportFactory(QuarterlyReportFactory):
    """Factory para reporte Q2 (Abril-Junio)."""
    quarter = 2


class Q3ReportFactory(QuarterlyReportFactory):
    """Factory para reporte Q3 (Julio-Septiembre)."""
    quarter = 3


class Q4ReportFactory(QuarterlyReportFactory):
    """Factory para reporte Q4 (Octubre-Diciembre)."""
    quarter = 4


# ============================================================================
# TRANSFER REPORT FACTORIES
# ============================================================================

class TransferReportFactory(DjangoModelFactory):
    """
    Factory para TransferReport (análisis de transferencias).
    
    Uso básico:
        report = TransferReportFactory(
            year=2025,
            quarter=1,
            menu_option='1'
        )
    """
    
    class Meta:
        model = TransferReport
        django_get_or_create = ('year', 'quarter', 'menu_option')
    
    year = 2025
    quarter = factory.Iterator([1, 2, 3, 4])
    menu_option = factory.Iterator(['1', '2', '3', '4', '5', '9', '0'])
    total_transfers = factory.Faker('pyint', min_value=100, max_value=5000)
    avg_wait_time_seconds = factory.Faker('pyint', min_value=10, max_value=180)
    max_wait_time_seconds = factory.LazyAttribute(
        lambda obj: obj.avg_wait_time_seconds * 2
    )
    successful_transfers = factory.LazyAttribute(
        lambda obj: int(obj.total_transfers * 0.9)  # 90% éxito
    )
    failed_transfers = factory.LazyAttribute(
        lambda obj: obj.total_transfers - obj.successful_transfers
    )


# ============================================================================
# ABANDONED REPORT FACTORIES
# ============================================================================

class AbandonedReportFactory(DjangoModelFactory):
    """
    Factory para AbandonedReport (llamadas abandonadas).
    
    Uso básico:
        report = AbandonedReportFactory(
            year=2025,
            quarter=1,
            did='800123456'
        )
    """
    
    class Meta:
        model = AbandonedReport
        django_get_or_create = ('year', 'quarter', 'did')
    
    year = 2025
    quarter = factory.Iterator([1, 2, 3, 4])
    did = factory.Sequence(lambda n: f'80012345{n}')
    total_calls = factory.Faker('pyint', min_value=100, max_value=10000)
    total_abandoned = factory.LazyAttribute(
        lambda obj: int(obj.total_calls * 0.15)  # ~15% abandono
    )
    abandonment_rate = factory.LazyAttribute(
        lambda obj: Decimal(obj.total_abandoned / obj.total_calls if obj.total_calls > 0 else 0)
    )
    avg_abandon_time_seconds = factory.Faker('pyint', min_value=5, max_value=60)


# ============================================================================
# CLIENT REPORT FACTORIES
# ============================================================================

class ClientReportFactory(DjangoModelFactory):
    """
    Factory para ClientReport (actividad por cliente).
    
    Uso básico:
        report = ClientReportFactory(
            year=2025,
            quarter=1,
            client_id='CLIENT_001'
        )
    """
    
    class Meta:
        model = ClientReport
        django_get_or_create = ('year', 'quarter', 'client_id')
    
    year = 2025
    quarter = factory.Iterator([1, 2, 3, 4])
    client_id = factory.Sequence(lambda n: f'CLIENT_{n:05d}')
    total_calls = factory.Faker('pyint', min_value=10, max_value=1000)
    total_duration_seconds = factory.LazyAttribute(
        lambda obj: obj.total_calls * 180  # Promedio 3 min
    )
    avg_duration_seconds = factory.LazyAttribute(
        lambda obj: int(obj.total_duration_seconds / obj.total_calls) if obj.total_calls > 0 else 0
    )
    first_call_date = factory.LazyFunction(lambda: date(2025, 1, 1))
    last_call_date = factory.LazyFunction(lambda: date(2025, 3, 31))


# ============================================================================
# CALL RECORD FACTORIES (por trimestre)
# ============================================================================

class CallRecordQ1Factory(DjangoModelFactory):
    """
    Factory para CallRecordQ1 (llamadas Q1).
    
    Uso básico:
        record = CallRecordQ1Factory(
            fecha=date(2025, 1, 15),
            telefono='800123456'
        )
    """
    
    class Meta:
        model = CallRecordQ1
    
    fecha = factory.LazyFunction(lambda: date(2025, 1, 15))
    telefono = factory.Sequence(lambda n: f'80012{n:05d}')
    duracion_segundos = factory.Faker('pyint', min_value=30, max_value=1800)
    estado = factory.Iterator(['COMPLETED', 'ABANDONED', 'FAILED', 'BUSY'])
    menu_option = factory.Iterator(['1', '2', '3', '4', '5', '0'])
    did = factory.Sequence(lambda n: f'80098765{n}')
    client_id = factory.Sequence(lambda n: f'CLIENT_{n:05d}')


class CallRecordQ2Factory(DjangoModelFactory):
    """Factory para CallRecordQ2 (llamadas Q2)."""
    
    class Meta:
        model = CallRecordQ2
    
    fecha = factory.LazyFunction(lambda: date(2025, 4, 15))
    telefono = factory.Sequence(lambda n: f'80012{n:05d}')
    duracion_segundos = factory.Faker('pyint', min_value=30, max_value=1800)
    estado = factory.Iterator(['COMPLETED', 'ABANDONED', 'FAILED'])
    menu_option = factory.Iterator(['1', '2', '3', '4', '5'])
    did = factory.Sequence(lambda n: f'80098765{n}')


class CallRecordQ3Factory(DjangoModelFactory):
    """Factory para CallRecordQ3 (llamadas Q3)."""
    
    class Meta:
        model = CallRecordQ3
    
    fecha = factory.LazyFunction(lambda: date(2025, 7, 15))
    telefono = factory.Sequence(lambda n: f'80012{n:05d}')
    duracion_segundos = factory.Faker('pyint', min_value=30, max_value=1800)
    estado = factory.Iterator(['COMPLETED', 'ABANDONED', 'FAILED'])


class CallRecordQ4Factory(DjangoModelFactory):
    """Factory para CallRecordQ4 (llamadas Q4)."""
    
    class Meta:
        model = CallRecordQ4
    
    fecha = factory.LazyFunction(lambda: date(2025, 10, 15))
    telefono = factory.Sequence(lambda n: f'80012{n:05d}')
    duracion_segundos = factory.Faker('pyint', min_value=30, max_value=1800)
    estado = factory.Iterator(['COMPLETED', 'ABANDONED', 'FAILED'])


# ============================================================================
# STATS FACTORIES
# ============================================================================

class MonthlyStatsFactory(DjangoModelFactory):
    """
    Factory para MonthlyStats (estadísticas mensuales).
    
    Uso:
        stats = MonthlyStatsFactory(year=2025, month=1)
    """
    
    class Meta:
        model = MonthlyStats
        django_get_or_create = ('year', 'month')
    
    year = 2025
    month = factory.Iterator(range(1, 13))
    total_calls = factory.Faker('pyint', min_value=1000, max_value=20000)
    total_duration_hours = factory.Faker('pyfloat', min_value=100, max_value=5000)
    avg_calls_per_day = factory.LazyAttribute(
        lambda obj: int(obj.total_calls / 30)
    )


class HourlyStatsFactory(DjangoModelFactory):
    """
    Factory para HourlyStats (estadísticas por hora).
    
    Uso:
        stats = HourlyStatsFactory(
            fecha=date(2025, 1, 15),
            hora=9
        )
    """
    
    class Meta:
        model = HourlyStats
        django_get_or_create = ('fecha', 'hora')
    
    fecha = factory.LazyFunction(lambda: date(2025, 1, 15))
    hora = factory.Iterator(range(0, 24))
    total_calls = factory.Faker('pyint', min_value=10, max_value=1000)
    avg_duration_seconds = factory.Faker('pyint', min_value=60, max_value=600)


class DIDReportFactory(DjangoModelFactory):
    """
    Factory para DIDReport (reporte por DID).
    
    Uso:
        report = DIDReportFactory(did='800123456')
    """
    
    class Meta:
        model = DIDReport
        django_get_or_create = ('year', 'quarter', 'did')
    
    year = 2025
    quarter = factory.Iterator([1, 2, 3, 4])
    did = factory.Sequence(lambda n: f'80012345{n}')
    total_calls = factory.Faker('pyint', min_value=100, max_value=10000)
    total_duration_hours = factory.Faker('pyfloat', min_value=10, max_value=1000)


# ============================================================================
# HELPER FACTORIES (Complex scenarios)
# ============================================================================

class CompleteQuarterDataFactory:
    """
    Factory que crea conjunto completo de datos para un trimestre.
    
    Uso:
        data = CompleteQuarterDataFactory.create_quarter(
            year=2025,
            quarter=1
        )
        # Retorna dict con quarterly, transfers, abandoned, clients
    """
    
    @staticmethod
    def create_quarter(year, quarter):
        """
        Crea datos completos de un trimestre.
        
        Args:
            year: Año
            quarter: Trimestre (1-4)
        
        Returns:
            dict: {
                'quarterly': QuarterlyReport,
                'transfers': [TransferReport, ...],
                'abandoned': [AbandonedReport, ...],
                'clients': [ClientReport, ...]
            }
        """
        quarterly = QuarterlyReportFactory(year=year, quarter=quarter)
        
        transfers = [
            TransferReportFactory(year=year, quarter=quarter, menu_option=option)
            for option in ['1', '2', '3', '4', '5']
        ]
        
        abandoned = [
            AbandonedReportFactory(
                year=year,
                quarter=quarter,
                did=f'80012345{i}'
            )
            for i in range(3)
        ]
        
        clients = [
            ClientReportFactory(
                year=year,
                quarter=quarter,
                client_id=f'CLIENT_{i:05d}'
            )
            for i in range(10)
        ]
        
        return {
            'quarterly': quarterly,
            'transfers': transfers,
            'abandoned': abandoned,
            'clients': clients
        }


class YearDataFactory:
    """
    Factory que crea datos completos de un año (4 trimestres).
    
    Uso:
        data = YearDataFactory.create_year(2025)
        # Retorna lista de 4 trimestres completos
    """
    
    @staticmethod
    def create_year(year):
        """
        Crea datos completos de un año.
        
        Args:
            year: Año
        
        Returns:
            list: Lista de 4 trimestres (CompleteQuarterData)
        """
        return [
            CompleteQuarterDataFactory.create_quarter(year, quarter)
            for quarter in range(1, 5)
        ]


# ============================================================================
# TOTAL FACTORIES: 23
# 
# Quarterly Factories (5):
#   - QuarterlyReportFactory (+ Q1, Q2, Q3, Q4)
# 
# Transfer Factories (1):
#   - TransferReportFactory
# 
# Abandoned Factories (1):
#   - AbandonedReportFactory
# 
# Client Factories (1):
#   - ClientReportFactory
# 
# Call Record Factories (4):
#   - CallRecordQ1Factory
#   - CallRecordQ2Factory
#   - CallRecordQ3Factory
#   - CallRecordQ4Factory
# 
# Stats Factories (3):
#   - MonthlyStatsFactory
#   - HourlyStatsFactory
#   - DIDReportFactory
# 
# Helper Factories (2):
#   - CompleteQuarterDataFactory (static)
#   - YearDataFactory (static)
# 
# CNST-002: Dual DB (MariaDB readonly en prod, SQLite en tests) [SUCCESS]
# CLEAN_CODE v3.0.1: Nombres auto-documentados [SUCCESS]
# ============================================================================
