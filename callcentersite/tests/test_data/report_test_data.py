"""
Factories para apps/reports/.

Factory boy para generación de datos test de reportes.
Basado en análisis ANALISIS_APP_REPORTS_v3_0_0.md (5 partes).

CNST-007: Export máximo 100K rows.
CLEAN_CODE v3.0.1: Nombres auto-documentados.
"""

import factory
from factory.django import DjangoModelFactory
from factory import fuzzy
from datetime import datetime, timedelta
from decimal import Decimal
from apps.reports.models import (
    Report,
    ReportExecution,
    ReportTemplate,
    ReportSchedule,
    ReportCache,
)
from .user_test_data import UserTestData


# ============================================================================
# REPORT FACTORIES
# ============================================================================

class ReportTestData(DjangoModelFactory):
    """
    Factory para Report (reporte generado).
    
    Uso básico:
        report = ReportTestData(
            report_type='quarterly',
            generated_by=user
        )
    
    Con parámetros:
        report = ReportTestData(
            report_type='quarterly',
            parameters={'year': 2025, 'quarter': 1}
        )
    """
    
    class Meta:
        model = Report
    
    report_type = factory.Iterator([
        'quarterly',
        'transfers',
        'abandoned',
        'clients',
        'custom'
    ])
    report_name = factory.Faker('sentence', nb_words=4)
    generated_by = factory.SubFactory(UserTestData)
    file_format = factory.Iterator(['xlsx', 'csv', 'pdf'])
    file_url = factory.Faker('url')
    file_size_bytes = factory.Faker('pyint', min_value=10240, max_value=10485760)  # 10KB - 10MB
    row_count = factory.Faker('pyint', min_value=100, max_value=50000)  # Bajo CNST-007 (100K)
    parameters = factory.LazyFunction(lambda: {
        'year': 2025,
        'quarter': 1,
        'filters': {}
    })
    generation_time_seconds = factory.Faker('pyfloat', min_value=0.5, max_value=60.0)
    is_cached = False
    created_at = factory.Faker('date_time_this_month')


class QuarterlyReportTestData(ReportTestData):
    """Factory para reporte trimestral."""
    report_type = 'quarterly'
    report_name = factory.LazyAttribute(
        lambda obj: f"Reporte Trimestral Q{obj.parameters.get('quarter', 1)} {obj.parameters.get('year', 2025)}"
    )
    file_format = 'xlsx'


class TransferReportTestData(ReportTestData):
    """Factory para reporte de transferencias."""
    report_type = 'transfers'
    report_name = 'Análisis de Transferencias'
    file_format = 'xlsx'


class AbandonedReportTestData(ReportTestData):
    """Factory para reporte de abandonos."""
    report_type = 'abandoned'
    report_name = 'Reporte de Llamadas Abandonadas'
    file_format = 'xlsx'


class ClientReportTestData(ReportTestData):
    """Factory para reporte de clientes."""
    report_type = 'clients'
    report_name = 'Actividad por Cliente'
    file_format = 'csv'


class CustomReportTestData(ReportTestData):
    """Factory para reporte custom."""
    report_type = 'custom'
    report_name = 'Reporte Personalizado'
    file_format = factory.Iterator(['xlsx', 'csv', 'pdf'])


# ============================================================================
# REPORTEXECUTION FACTORIES
# ============================================================================

class ReportExecutionTestData(DjangoModelFactory):
    """
    Factory para ReportExecution (ejecución de reporte).
    
    Uso básico:
        execution = ReportExecutionTestData(
            report=report,
            execution_status='SUCCESS'
        )
    """
    
    class Meta:
        model = ReportExecution
    
    report = factory.SubFactory(ReportTestData)
    execution_status = factory.Iterator(['PENDING', 'RUNNING', 'SUCCESS', 'FAILED'])
    started_at = factory.Faker('date_time_this_month')
    finished_at = factory.LazyAttribute(
        lambda obj: obj.started_at + timedelta(seconds=10) if obj.execution_status in ['SUCCESS', 'FAILED'] else None
    )
    error_message = factory.LazyAttribute(
        lambda obj: None if obj.execution_status == 'SUCCESS' else 'Generation failed'
    )
    execution_time_seconds = factory.LazyAttribute(
        lambda obj: (obj.finished_at - obj.started_at).total_seconds() if obj.finished_at else None
    )


class PendingExecutionTestData(ReportExecutionTestData):
    """Factory para ejecución pendiente."""
    execution_status = 'PENDING'
    finished_at = None
    error_message = None


class RunningExecutionTestData(ReportExecutionTestData):
    """Factory para ejecución en curso."""
    execution_status = 'RUNNING'
    finished_at = None
    error_message = None


class SuccessExecutionTestData(ReportExecutionTestData):
    """Factory para ejecución exitosa."""
    execution_status = 'SUCCESS'
    finished_at = factory.LazyAttribute(
        lambda obj: obj.started_at + timedelta(seconds=10)
    )
    error_message = None


class FailedExecutionTestData(ReportExecutionTestData):
    """Factory para ejecución fallida."""
    execution_status = 'FAILED'
    finished_at = factory.LazyAttribute(
        lambda obj: obj.started_at + timedelta(seconds=5)
    )
    error_message = factory.Iterator([
        'Data not available',
        'Export limit exceeded',
        'Permission denied',
        'Timeout',
    ])


# ============================================================================
# REPORTTEMPLATE FACTORIES
# ============================================================================

class ReportTemplateTestData(DjangoModelFactory):
    """
    Factory para ReportTemplate (plantilla de reporte).
    
    Uso básico:
        template = ReportTemplateTestData(
            template_name='Quarterly Summary',
            report_type='quarterly'
        )
    """
    
    class Meta:
        model = ReportTemplate
        django_get_or_create = ('template_name',)
    
    template_name = factory.Sequence(lambda n: f'Template {n}')
    report_type = factory.Iterator(['quarterly', 'transfers', 'abandoned', 'clients'])
    description = factory.Faker('sentence', nb_words=15)
    default_parameters = factory.LazyFunction(lambda: {
        'year': 2025,
        'quarter': 1,
        'format': 'xlsx'
    })
    sql_query = factory.Faker('text', max_nb_chars=500)
    columns = factory.LazyFunction(lambda: [
        {'name': 'year', 'type': 'integer'},
        {'name': 'quarter', 'type': 'integer'},
        {'name': 'total_calls', 'type': 'integer'},
    ])
    is_active = True
    created_by = factory.SubFactory(UserTestData)


class QuarterlyTemplateTestData(ReportTemplateTestData):
    """Factory para template trimestral."""
    template_name = 'Quarterly Summary Template'
    report_type = 'quarterly'
    default_parameters = factory.LazyFunction(lambda: {
        'year': 2025,
        'quarter': 1,
        'format': 'xlsx',
        'include_charts': True
    })


class TransferTemplateTestData(ReportTemplateTestData):
    """Factory para template de transferencias."""
    template_name = 'Transfer Analysis Template'
    report_type = 'transfers'


# ============================================================================
# REPORTSCHEDULE FACTORIES
# ============================================================================

class ReportScheduleTestData(DjangoModelFactory):
    """
    Factory para ReportSchedule (programación de reportes).
    
    Uso básico:
        schedule = ReportScheduleTestData(
            template=template,
            cron_expression='0 2 1 */3 *'  # Primer día trimestre
        )
    """
    
    class Meta:
        model = ReportSchedule
    
    template = factory.SubFactory(ReportTemplateTestData)
    schedule_name = factory.Sequence(lambda n: f'Schedule {n}')
    cron_expression = factory.Iterator([
        '0 2 1 */3 *',    # Primer día trimestre a las 2 AM
        '0 3 * * 1',      # Lunes a las 3 AM
        '0 2 1 * *',      # Primer día mes a las 2 AM
    ])
    is_active = True
    recipients = factory.LazyFunction(lambda: [
        'manager@example.com',
        'analyst@example.com'
    ])
    created_by = factory.SubFactory(UserTestData)
    last_run_at = factory.Faker('date_time_this_month')
    next_run_at = factory.LazyAttribute(
        lambda obj: obj.last_run_at + timedelta(days=7) if obj.last_run_at else None
    )


class QuarterlyScheduleTestData(ReportScheduleTestData):
    """Factory para schedule trimestral."""
    schedule_name = 'Quarterly Report Schedule'
    cron_expression = '0 2 1 */3 *'  # Primer día de cada trimestre


class WeeklyScheduleTestData(ReportScheduleTestData):
    """Factory para schedule semanal."""
    schedule_name = 'Weekly Report Schedule'
    cron_expression = '0 3 * * 1'  # Lunes a las 3 AM


# ============================================================================
# REPORTCACHE FACTORIES
# ============================================================================

class ReportCacheTestData(DjangoModelFactory):
    """
    Factory para ReportCache (cache de reportes).
    
    Uso básico:
        cache = ReportCacheTestData(
            cache_key='quarterly_2025_Q1',
            report=report
        )
    """
    
    class Meta:
        model = ReportCache
        django_get_or_create = ('cache_key',)
    
    cache_key = factory.Sequence(lambda n: f'cache_key_{n}')
    report = factory.SubFactory(ReportTestData)
    parameters = factory.LazyFunction(lambda: {
        'year': 2025,
        'quarter': 1
    })
    cached_data = factory.LazyFunction(lambda: {
        'rows': [
            {'year': 2025, 'quarter': 1, 'total_calls': 10000}
        ]
    })
    cached_at = factory.Faker('date_time_this_month')
    expires_at = factory.LazyAttribute(
        lambda obj: obj.cached_at + timedelta(hours=24)
    )
    hit_count = factory.Faker('pyint', min_value=0, max_value=100)
    is_valid = True


# ============================================================================
# HELPER FACTORIES (Complex scenarios)
# ============================================================================

class CompleteReportTestData:
    """
    Factory que crea reporte completo con ejecución.
    
    Uso:
        data = CompleteReportTestData.create_report(
            report_type='quarterly',
            user=user,
            success=True
        )
        # Retorna dict con report y execution
    """
    
    @staticmethod
    def create_report(report_type, user, success=True):
        """
        Crea reporte completo.
        
        Args:
            report_type: Tipo de reporte
            user: Usuario generador
            success: Si fue exitoso
        
        Returns:
            dict: {
                'report': Report,
                'execution': ReportExecution
            }
        """
        report = ReportTestData(
            report_type=report_type,
            generated_by=user
        )
        
        if success:
            execution = SuccessExecutionTestData(report=report)
        else:
            execution = FailedExecutionTestData(report=report)
        
        return {
            'report': report,
            'execution': execution
        }


class TemplateWithScheduleTestData:
    """
    Factory que crea template con schedule.
    
    Uso:
        data = TemplateWithScheduleTestData.create(
            report_type='quarterly',
            user=user
        )
        # Retorna dict con template y schedule
    """
    
    @staticmethod
    def create(report_type, user):
        """
        Crea template con schedule.
        
        Args:
            report_type: Tipo de reporte
            user: Usuario creador
        
        Returns:
            dict: {
                'template': ReportTemplate,
                'schedule': ReportSchedule
            }
        """
        template = ReportTemplateTestData(
            report_type=report_type,
            created_by=user
        )
        
        schedule = ReportScheduleTestData(
            template=template,
            created_by=user
        )
        
        return {
            'template': template,
            'schedule': schedule
        }


# ============================================================================
# TOTAL FACTORIES: 19
# 
# Report Factories (6):
#   - ReportTestData (base)
#   - QuarterlyReportTestData
#   - TransferReportTestData
#   - AbandonedReportTestData
#   - ClientReportTestData
#   - CustomReportTestData
# 
# ReportExecution Factories (5):
#   - ReportExecutionTestData (base)
#   - PendingExecutionTestData
#   - RunningExecutionTestData
#   - SuccessExecutionTestData
#   - FailedExecutionTestData
# 
# ReportTemplate Factories (3):
#   - ReportTemplateTestData (base)
#   - QuarterlyTemplateTestData
#   - TransferTemplateTestData
# 
# ReportSchedule Factories (3):
#   - ReportScheduleTestData (base)
#   - QuarterlyScheduleTestData
#   - WeeklyScheduleTestData
# 
# ReportCache Factories (1):
#   - ReportCacheTestData
# 
# Helper Factories (2):
#   - CompleteReportTestData (static)
#   - TemplateWithScheduleTestData (static)
# 
# CNST-007: Export máximo 100K rows [SUCCESS]
# CLEAN_CODE v3.0.1: Nombres auto-documentados [SUCCESS]
# ============================================================================
