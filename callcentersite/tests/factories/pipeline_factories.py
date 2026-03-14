"""
Factories para apps/pipeline/ (ETL y APScheduler).

Factory boy para generación de datos test de pipeline ETL.
Basado en análisis ANALISIS_APP_PIPELINE_v3_0_0.md (4 partes).

CNST-013: APScheduler (NO Celery).
CLEAN_CODE v3.0.1: Nombres auto-documentados.
"""

import factory
from factory.django import DjangoModelFactory
from factory import fuzzy
from datetime import datetime, timedelta
from apps.pipeline.models import (
    ETLJob,
    ETLError,
    SchedulerConfig,
    DataQualityCheck,
)
from .user_factory import UserFactory


# ============================================================================
# ETLJOB FACTORIES
# ============================================================================

class ETLJobFactory(DjangoModelFactory):
    """
    Factory para ETLJob (trabajo ETL).
    
    Uso básico:
        job = ETLJobFactory(
            job_name='quarterly_report_etl',
            status='SUCCESS'
        )
    
    Con duración:
        job = ETLJobFactory(
            started_at=datetime.now() - timedelta(minutes=10),
            finished_at=datetime.now()
        )
    """
    
    class Meta:
        model = ETLJob
    
    job_name = factory.Iterator([
        'quarterly_report_etl',
        'transfer_analysis_etl',
        'abandoned_calls_etl',
        'client_activity_etl',
        'monthly_stats_etl',
    ])
    status = factory.Iterator(['PENDING', 'RUNNING', 'SUCCESS', 'FAILED'])
    started_at = factory.Faker('date_time_this_month')
    finished_at = factory.LazyAttribute(
        lambda obj: obj.started_at + timedelta(minutes=5) if obj.status in ['SUCCESS', 'FAILED'] else None
    )
    records_processed = factory.LazyAttribute(
        lambda obj: factory.Faker('pyint', min_value=100, max_value=10000).evaluate(None, None, {'locale': None}) if obj.status == 'SUCCESS' else 0
    )
    records_failed = factory.LazyAttribute(
        lambda obj: 0 if obj.status == 'SUCCESS' else factory.Faker('pyint', min_value=1, max_value=100).evaluate(None, None, {'locale': None})
    )
    error_message = factory.LazyAttribute(
        lambda obj: None if obj.status == 'SUCCESS' else 'ETL failed: Connection timeout'
    )
    execution_time_seconds = factory.LazyAttribute(
        lambda obj: (obj.finished_at - obj.started_at).total_seconds() if obj.finished_at else None
    )
    triggered_by = factory.SubFactory(UserFactory)


class PendingETLJobFactory(ETLJobFactory):
    """Factory para ETL job pendiente."""
    status = 'PENDING'
    finished_at = None
    records_processed = 0
    records_failed = 0
    error_message = None


class RunningETLJobFactory(ETLJobFactory):
    """Factory para ETL job en ejecución."""
    status = 'RUNNING'
    finished_at = None
    records_processed = 0
    records_failed = 0
    error_message = None


class SuccessETLJobFactory(ETLJobFactory):
    """Factory para ETL job exitoso."""
    status = 'SUCCESS'
    finished_at = factory.LazyAttribute(
        lambda obj: obj.started_at + timedelta(minutes=5)
    )
    records_processed = factory.Faker('pyint', min_value=1000, max_value=10000)
    records_failed = 0
    error_message = None


class FailedETLJobFactory(ETLJobFactory):
    """Factory para ETL job fallido."""
    status = 'FAILED'
    finished_at = factory.LazyAttribute(
        lambda obj: obj.started_at + timedelta(minutes=2)
    )
    records_processed = factory.Faker('pyint', min_value=0, max_value=100)
    records_failed = factory.Faker('pyint', min_value=1, max_value=100)
    error_message = factory.Iterator([
        'Connection timeout',
        'Invalid data format',
        'Database error',
        'Permission denied',
    ])


# ============================================================================
# ETLERROR FACTORIES
# ============================================================================

class ETLErrorFactory(DjangoModelFactory):
    """
    Factory para ETLError (error en ETL).
    
    Uso básico:
        error = ETLErrorFactory(
            job=etl_job,
            error_type='VALIDATION_ERROR'
        )
    """
    
    class Meta:
        model = ETLError
    
    job = factory.SubFactory(FailedETLJobFactory)
    error_type = factory.Iterator([
        'VALIDATION_ERROR',
        'CONNECTION_ERROR',
        'DATA_QUALITY_ERROR',
        'PERMISSION_ERROR',
        'TIMEOUT_ERROR',
    ])
    error_message = factory.Faker('sentence', nb_words=10)
    record_data = factory.LazyFunction(lambda: {
        'row': 123,
        'field': 'total_calls',
        'value': 'invalid',
        'expected': 'integer'
    })
    occurred_at = factory.Faker('date_time_this_month')
    stack_trace = factory.Faker('text', max_nb_chars=500)


class ValidationErrorFactory(ETLErrorFactory):
    """Factory para errores de validación."""
    error_type = 'VALIDATION_ERROR'
    error_message = 'Invalid data format'
    record_data = factory.LazyFunction(lambda: {
        'row': 123,
        'field': 'year',
        'value': '202X',
        'expected': 'integer'
    })


class ConnectionErrorFactory(ETLErrorFactory):
    """Factory para errores de conexión."""
    error_type = 'CONNECTION_ERROR'
    error_message = 'Database connection timeout'
    record_data = factory.LazyFunction(lambda: {
        'database': 'ivr_legacy',
        'timeout_seconds': 30
    })


class DataQualityErrorFactory(ETLErrorFactory):
    """Factory para errores de calidad de datos."""
    error_type = 'DATA_QUALITY_ERROR'
    error_message = 'Data quality check failed'
    record_data = factory.LazyFunction(lambda: {
        'check': 'total_calls_positive',
        'actual_value': -100,
        'expected': '> 0'
    })


# ============================================================================
# SCHEDULERCONFIG FACTORIES
# ============================================================================

class SchedulerConfigFactory(DjangoModelFactory):
    """
    Factory para SchedulerConfig (configuración APScheduler).
    
    CNST-013: APScheduler (NO Celery).
    
    Uso básico:
        config = SchedulerConfigFactory(
            job_name='cleanup_sessions',
            cron_expression='0 3 * * *'
        )
    """
    
    class Meta:
        model = SchedulerConfig
        django_get_or_create = ('job_name',)
    
    job_name = factory.Iterator([
        'cleanup_sessions',
        'etl_monitor',
        'health_check',
        'quarterly_report_etl',
    ])
    cron_expression = factory.Iterator([
        '0 3 * * *',      # Diario a las 3 AM
        '0 */6 * * *',    # Cada 6 horas
        '*/5 * * * *',    # Cada 5 minutos
        '0 2 1 */3 *',    # Primer día de cada trimestre a las 2 AM
    ])
    is_active = True
    max_retries = 3
    retry_delay_seconds = 300
    timeout_seconds = 3600
    description = factory.Faker('sentence', nb_words=12)
    created_by = factory.SubFactory(UserFactory)
    last_run_at = factory.Faker('date_time_this_month')
    next_run_at = factory.LazyAttribute(
        lambda obj: obj.last_run_at + timedelta(hours=6) if obj.last_run_at else None
    )


class DailyJobConfigFactory(SchedulerConfigFactory):
    """Factory para job diario (3 AM)."""
    job_name = 'cleanup_sessions'
    cron_expression = '0 3 * * *'


class HourlyJobConfigFactory(SchedulerConfigFactory):
    """Factory para job cada 6 horas."""
    job_name = 'etl_monitor'
    cron_expression = '0 */6 * * *'


class HealthCheckConfigFactory(SchedulerConfigFactory):
    """Factory para health check (cada 5 min)."""
    job_name = 'health_check'
    cron_expression = '*/5 * * * *'


# ============================================================================
# DATAQUALITYCHECK FACTORIES
# ============================================================================

class DataQualityCheckFactory(DjangoModelFactory):
    """
    Factory para DataQualityCheck (validación calidad datos).
    
    Uso básico:
        check = DataQualityCheckFactory(
            job=etl_job,
            check_name='total_calls_positive'
        )
    """
    
    class Meta:
        model = DataQualityCheck
    
    job = factory.SubFactory(SuccessETLJobFactory)
    check_name = factory.Iterator([
        'total_calls_positive',
        'abandonment_rate_range',
        'duration_reasonable',
        'unique_client_count',
    ])
    check_type = factory.Iterator(['VALIDATION', 'RANGE', 'UNIQUENESS', 'COMPLETENESS'])
    passed = True
    expected_value = factory.LazyFunction(lambda: {
        'min': 0,
        'max': 100000
    })
    actual_value = factory.LazyFunction(lambda: {
        'value': 10000
    })
    error_message = factory.LazyAttribute(
        lambda obj: None if obj.passed else 'Check failed'
    )
    checked_at = factory.Faker('date_time_this_month')


class PassedCheckFactory(DataQualityCheckFactory):
    """Factory para check exitoso."""
    passed = True
    error_message = None


class FailedCheckFactory(DataQualityCheckFactory):
    """Factory para check fallido."""
    passed = False
    error_message = 'Data quality check failed'
    actual_value = factory.LazyFunction(lambda: {
        'value': -100  # Valor inválido
    })


# ============================================================================
# HELPER FACTORIES (Complex scenarios)
# ============================================================================

class CompleteETLRunFactory:
    """
    Factory que crea ejecución completa de ETL.
    
    Uso:
        run = CompleteETLRunFactory.create_run(
            job_name='quarterly_report_etl',
            success=True
        )
        # Retorna dict con job, errors, checks
    """
    
    @staticmethod
    def create_run(job_name, success=True):
        """
        Crea ejecución completa de ETL.
        
        Args:
            job_name: Nombre del job
            success: Si fue exitoso
        
        Returns:
            dict: {
                'job': ETLJob,
                'errors': [ETLError, ...],
                'checks': [DataQualityCheck, ...]
            }
        """
        if success:
            job = SuccessETLJobFactory(job_name=job_name)
            errors = []
            checks = [
                PassedCheckFactory(job=job, check_name='total_calls_positive'),
                PassedCheckFactory(job=job, check_name='abandonment_rate_range'),
            ]
        else:
            job = FailedETLJobFactory(job_name=job_name)
            errors = [
                ValidationErrorFactory(job=job),
                DataQualityErrorFactory(job=job),
            ]
            checks = [
                FailedCheckFactory(job=job, check_name='total_calls_positive'),
            ]
        
        return {
            'job': job,
            'errors': errors,
            'checks': checks
        }


class SchedulerHistoryFactory:
    """
    Factory que crea historial de scheduler.
    
    Uso:
        history = SchedulerHistoryFactory.create_history(
            job_name='cleanup_sessions',
            runs=10
        )
        # Retorna lista de ETLJob
    """
    
    @staticmethod
    def create_history(job_name, runs=10):
        """
        Crea historial de ejecuciones.
        
        Args:
            job_name: Nombre del job
            runs: Número de ejecuciones
        
        Returns:
            list: Lista de ETLJob
        """
        jobs = []
        base_date = datetime.now()
        
        for i in range(runs):
            date = base_date - timedelta(days=i)
            
            # 80% éxito, 20% fallos
            if i % 5 == 0:
                job = FailedETLJobFactory(
                    job_name=job_name,
                    started_at=date
                )
            else:
                job = SuccessETLJobFactory(
                    job_name=job_name,
                    started_at=date
                )
            
            jobs.append(job)
        
        return jobs


# ============================================================================
# TOTAL FACTORIES: 18
# 
# ETLJob Factories (5):
#   - ETLJobFactory (base)
#   - PendingETLJobFactory
#   - RunningETLJobFactory
#   - SuccessETLJobFactory
#   - FailedETLJobFactory
# 
# ETLError Factories (4):
#   - ETLErrorFactory (base)
#   - ValidationErrorFactory
#   - ConnectionErrorFactory
#   - DataQualityErrorFactory
# 
# SchedulerConfig Factories (4):
#   - SchedulerConfigFactory (base)
#   - DailyJobConfigFactory
#   - HourlyJobConfigFactory
#   - HealthCheckConfigFactory
# 
# DataQualityCheck Factories (3):
#   - DataQualityCheckFactory (base)
#   - PassedCheckFactory
#   - FailedCheckFactory
# 
# Helper Factories (2):
#   - CompleteETLRunFactory (static)
#   - SchedulerHistoryFactory (static)
# 
# CNST-013: APScheduler (NO Celery) [SUCCESS]
# CLEAN_CODE v3.0.1: Nombres auto-documentados [SUCCESS]
# ============================================================================
