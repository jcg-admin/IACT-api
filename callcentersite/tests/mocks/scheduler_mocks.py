"""
Mocks para APScheduler (NO Celery).

CONTEXTO: CNST-013 - APScheduler para jobs programados.
Simulamos scheduler sin ejecutar jobs reales.

RESTRICCIONES:
- CNST-013: APScheduler (NO Celery)

CLEAN_CODE v3.0.1: Nombres auto-documentados.
"""

import pytest
from unittest.mock import MagicMock, Mock, patch
from datetime import datetime, timedelta


# ============================================================================
# APSCHEDULER BASE MOCKS
# ============================================================================

@pytest.fixture
def mock_apscheduler(mocker):
    """
    Mock de APScheduler completo.
    
    CNST-013: APScheduler (NO Celery).
    
    Uso:
        def test_scheduler(mock_apscheduler):
            scheduler = setup_scheduler()
            assert scheduler.add_job.called
    
    Métodos mockeados:
        - add_job(func, trigger, **kwargs)
        - remove_job(job_id)
        - start()
        - shutdown()
        - get_jobs()
        - get_job(job_id)
    """
    from apscheduler.schedulers.background import BackgroundScheduler
    
    mock_scheduler = MagicMock(spec=BackgroundScheduler)
    
    # Mock add_job() retorna job fake
    mock_job = MagicMock()
    mock_job.id = 'job_1'
    mock_job.next_run_time = datetime.now() + timedelta(hours=1)
    mock_scheduler.add_job.return_value = mock_job
    
    # Mock remove_job()
    mock_scheduler.remove_job.return_value = None
    
    # Mock start()
    mock_scheduler.start.return_value = None
    mock_scheduler.running = True
    
    # Mock shutdown()
    mock_scheduler.shutdown.return_value = None
    
    # Mock get_jobs()
    mock_scheduler.get_jobs.return_value = [mock_job]
    
    # Mock get_job()
    mock_scheduler.get_job.return_value = mock_job
    
    mocker.patch(
        'apscheduler.schedulers.background.BackgroundScheduler',
        return_value=mock_scheduler
    )
    
    return mock_scheduler


@pytest.fixture
def mock_scheduler_job(mocker):
    """
    Mock de un Job individual de APScheduler.
    
    Uso:
        def test_job(mock_scheduler_job):
            assert mock_scheduler_job.id == 'cleanup_sessions'
    
    Atributos:
        - id
        - name
        - trigger
        - next_run_time
        - func
    """
    mock_job = MagicMock()
    mock_job.id = 'cleanup_sessions'
    mock_job.name = 'Cleanup Sessions'
    mock_job.trigger = 'cron'
    mock_job.next_run_time = datetime.now() + timedelta(hours=24)
    mock_job.func = MagicMock()
    
    return mock_job


# ============================================================================
# TRIGGER MOCKS
# ============================================================================

@pytest.fixture
def mock_cron_trigger(mocker):
    """
    Mock de CronTrigger.
    
    Uso:
        def test_cron(mock_cron_trigger):
            trigger = CronTrigger(hour=3)
            assert trigger is not None
    
    Ejemplo cron: '0 3 * * *' (diario a las 3 AM)
    """
    from apscheduler.triggers.cron import CronTrigger
    
    mock_trigger = MagicMock(spec=CronTrigger)
    mock_trigger.get_next_fire_time.return_value = datetime.now() + timedelta(hours=24)
    
    mocker.patch(
        'apscheduler.triggers.cron.CronTrigger',
        return_value=mock_trigger
    )
    
    return mock_trigger


@pytest.fixture
def mock_interval_trigger(mocker):
    """
    Mock de IntervalTrigger.
    
    Uso:
        def test_interval(mock_interval_trigger):
            trigger = IntervalTrigger(hours=6)
            assert trigger is not None
    
    Ejemplo: Cada 6 horas
    """
    from apscheduler.triggers.interval import IntervalTrigger
    
    mock_trigger = MagicMock(spec=IntervalTrigger)
    mock_trigger.get_next_fire_time.return_value = datetime.now() + timedelta(hours=6)
    
    mocker.patch(
        'apscheduler.triggers.interval.IntervalTrigger',
        return_value=mock_trigger
    )
    
    return mock_trigger


@pytest.fixture
def mock_date_trigger(mocker):
    """
    Mock de DateTrigger (ejecución única).
    
    Uso:
        def test_date(mock_date_trigger):
            trigger = DateTrigger(run_date='2025-01-20 10:00:00')
    """
    from apscheduler.triggers.date import DateTrigger
    
    mock_trigger = MagicMock(spec=DateTrigger)
    mock_trigger.get_next_fire_time.return_value = datetime(2025, 1, 20, 10, 0, 0)
    
    mocker.patch(
        'apscheduler.triggers.date.DateTrigger',
        return_value=mock_trigger
    )
    
    return mock_trigger


# ============================================================================
# JOB EXECUTION MOCKS
# ============================================================================

@pytest.fixture
def mock_job_execution_success(mocker):
    """
    Mock de ejecución exitosa de job.
    
    Uso:
        def test_job_success(mock_job_execution_success):
            job.func()  # Ejecuta sin error
            assert mock_job_execution_success.called
    """
    mock_func = MagicMock()
    mock_func.return_value = {'status': 'SUCCESS'}
    
    return mock_func


@pytest.fixture
def mock_job_execution_failure(mocker):
    """
    Mock de ejecución fallida de job.
    
    Uso:
        def test_job_failure(mock_job_execution_failure):
            with pytest.raises(Exception):
                job.func()
    """
    mock_func = MagicMock()
    mock_func.side_effect = Exception("Job execution failed")
    
    return mock_func


# ============================================================================
# SCHEDULED JOBS MOCKS
# ============================================================================

@pytest.fixture
def mock_cleanup_sessions_job(mocker, mock_apscheduler):
    """
    Mock del job 'cleanup_sessions'.
    
    CNST-010: Cleanup de sesiones BD (diario 3 AM).
    
    Uso:
        def test_cleanup_job(mock_cleanup_sessions_job):
            # Job configurado en scheduler
            assert 'cleanup_sessions' in [j.id for j in scheduler.get_jobs()]
    """
    mock_job = MagicMock()
    mock_job.id = 'cleanup_sessions'
    mock_job.name = 'Cleanup Old Sessions'
    mock_job.trigger = 'cron: hour=3'
    mock_job.next_run_time = datetime.now().replace(hour=3, minute=0) + timedelta(days=1)
    
    # Agregar job al scheduler
    mock_apscheduler.get_job.return_value = mock_job
    
    return mock_job


@pytest.fixture
def mock_etl_monitor_job(mocker, mock_apscheduler):
    """
    Mock del job 'etl_monitor'.
    
    Monitorea ETL jobs (cada 6 horas).
    
    Uso:
        def test_etl_monitor(mock_etl_monitor_job):
            assert mock_etl_monitor_job.trigger == 'interval: hours=6'
    """
    mock_job = MagicMock()
    mock_job.id = 'etl_monitor'
    mock_job.name = 'ETL Monitor'
    mock_job.trigger = 'interval: hours=6'
    mock_job.next_run_time = datetime.now() + timedelta(hours=6)
    
    mock_apscheduler.get_job.return_value = mock_job
    
    return mock_job


@pytest.fixture
def mock_health_check_job(mocker, mock_apscheduler):
    """
    Mock del job 'health_check'.
    
    Health check del sistema (cada 5 min).
    
    Uso:
        def test_health_check(mock_health_check_job):
            assert mock_health_check_job.trigger == 'interval: minutes=5'
    """
    mock_job = MagicMock()
    mock_job.id = 'health_check'
    mock_job.name = 'System Health Check'
    mock_job.trigger = 'interval: minutes=5'
    mock_job.next_run_time = datetime.now() + timedelta(minutes=5)
    
    mock_apscheduler.get_job.return_value = mock_job
    
    return mock_job


@pytest.fixture
def mock_quarterly_report_job(mocker, mock_apscheduler):
    """
    Mock del job 'quarterly_report_etl'.
    
    ETL de reporte trimestral (primer día trimestre, 2 AM).
    
    Uso:
        def test_quarterly_etl(mock_quarterly_report_job):
            assert 'quarterly_report_etl' in mock_quarterly_report_job.id
    """
    mock_job = MagicMock()
    mock_job.id = 'quarterly_report_etl'
    mock_job.name = 'Quarterly Report ETL'
    mock_job.trigger = 'cron: day=1, month=1,4,7,10, hour=2'
    mock_job.next_run_time = datetime(2025, 4, 1, 2, 0, 0)  # Próximo trimestre
    
    mock_apscheduler.get_job.return_value = mock_job
    
    return mock_job


# ============================================================================
# JOB STORE MOCKS
# ============================================================================

@pytest.fixture
def mock_memory_job_store(mocker):
    """
    Mock de MemoryJobStore.
    
    APScheduler usa MemoryJobStore por defecto.
    
    Uso:
        def test_jobstore(mock_memory_job_store):
            jobstore = MemoryJobStore()
            assert jobstore is not None
    """
    from apscheduler.jobstores.memory import MemoryJobStore
    
    mock_jobstore = MagicMock(spec=MemoryJobStore)
    mock_jobstore.get_all_jobs.return_value = []
    mock_jobstore.add_job.return_value = None
    mock_jobstore.remove_job.return_value = None
    
    mocker.patch(
        'apscheduler.jobstores.memory.MemoryJobStore',
        return_value=mock_jobstore
    )
    
    return mock_jobstore


@pytest.fixture
def mock_sqlalchemy_job_store(mocker):
    """
    Mock de SQLAlchemyJobStore (persistencia BD).
    
    Uso:
        def test_sqlalchemy_jobstore(mock_sqlalchemy_job_store):
            jobstore = SQLAlchemyJobStore(url='sqlite:///jobs.db')
    """
    from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
    
    mock_jobstore = MagicMock(spec=SQLAlchemyJobStore)
    mock_jobstore.get_all_jobs.return_value = []
    
    mocker.patch(
        'apscheduler.jobstores.sqlalchemy.SQLAlchemyJobStore',
        return_value=mock_jobstore
    )
    
    return mock_jobstore


# ============================================================================
# SCHEDULER LIFECYCLE MOCKS
# ============================================================================

@pytest.fixture
def mock_scheduler_start(mocker, mock_apscheduler):
    """
    Mock de scheduler.start().
    
    Uso:
        def test_start(mock_scheduler_start):
            scheduler.start()
            assert scheduler.running is True
    """
    mock_apscheduler.start.return_value = None
    mock_apscheduler.running = True
    
    return mock_apscheduler


@pytest.fixture
def mock_scheduler_shutdown(mocker, mock_apscheduler):
    """
    Mock de scheduler.shutdown().
    
    Uso:
        def test_shutdown(mock_scheduler_shutdown):
            scheduler.shutdown()
            assert scheduler.running is False
    """
    mock_apscheduler.shutdown.return_value = None
    mock_apscheduler.running = False
    
    return mock_apscheduler


# ============================================================================
# ERROR HANDLING MOCKS
# ============================================================================

@pytest.fixture
def mock_scheduler_error(mocker):
    """
    Mock de scheduler que lanza error al iniciar.
    
    Uso:
        def test_scheduler_error(mock_scheduler_error):
            with pytest.raises(Exception):
                scheduler.start()
    """
    mock_scheduler = MagicMock()
    mock_scheduler.start.side_effect = Exception("Scheduler start failed")
    
    mocker.patch(
        'apscheduler.schedulers.background.BackgroundScheduler',
        return_value=mock_scheduler
    )
    
    return mock_scheduler


@pytest.fixture
def mock_job_not_found(mocker, mock_apscheduler):
    """
    Mock cuando job no existe.
    
    Uso:
        def test_job_not_found(mock_job_not_found):
            job = scheduler.get_job('invalid_job_id')
            assert job is None
    """
    from apscheduler.jobstores.base import JobLookupError
    
    mock_apscheduler.get_job.side_effect = JobLookupError('invalid_job_id')
    
    return mock_apscheduler


# ============================================================================
# HELPER MOCKS
# ============================================================================

@pytest.fixture
def mock_scheduler_config(mocker):
    """
    Mock de configuración de scheduler.
    
    Uso:
        def test_config(mock_scheduler_config):
            config = get_scheduler_config()
            assert config['timezone'] == 'America/Santiago'
    """
    return {
        'timezone': 'America/Santiago',
        'job_defaults': {
            'coalesce': False,
            'max_instances': 1
        },
        'jobstores': {
            'default': 'MemoryJobStore'
        }
    }


@pytest.fixture
def mock_all_scheduled_jobs(mocker, mock_apscheduler):
    """
    Mock que retorna TODOS los jobs programados.
    
    Uso:
        def test_all_jobs(mock_all_scheduled_jobs):
            jobs = scheduler.get_jobs()
            assert len(jobs) == 4
    """
    jobs = [
        MagicMock(id='cleanup_sessions', name='Cleanup Sessions'),
        MagicMock(id='etl_monitor', name='ETL Monitor'),
        MagicMock(id='health_check', name='Health Check'),
        MagicMock(id='quarterly_report_etl', name='Quarterly ETL'),
    ]
    
    mock_apscheduler.get_jobs.return_value = jobs
    
    return jobs


# ============================================================================
# TOTAL MOCKS: 19
# 
# Base Scheduler Mocks (2):
#   - mock_apscheduler
#   - mock_scheduler_job
# 
# Trigger Mocks (3):
#   - mock_cron_trigger
#   - mock_interval_trigger
#   - mock_date_trigger
# 
# Job Execution Mocks (2):
#   - mock_job_execution_success
#   - mock_job_execution_failure
# 
# Scheduled Jobs Mocks (4):
#   - mock_cleanup_sessions_job
#   - mock_etl_monitor_job
#   - mock_health_check_job
#   - mock_quarterly_report_job
# 
# JobStore Mocks (2):
#   - mock_memory_job_store
#   - mock_sqlalchemy_job_store
# 
# Lifecycle Mocks (2):
#   - mock_scheduler_start
#   - mock_scheduler_shutdown
# 
# Error Mocks (2):
#   - mock_scheduler_error
#   - mock_job_not_found
# 
# Helper Mocks (2):
#   - mock_scheduler_config
#   - mock_all_scheduled_jobs
# 
# CNST-013: APScheduler (NO Celery) [SUCCESS]
# CLEAN_CODE v3.0.1: Nombres auto-documentados [SUCCESS]
# ============================================================================
