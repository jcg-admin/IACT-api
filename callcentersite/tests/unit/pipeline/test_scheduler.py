import pytest
from apps.pipeline.scheduler import ETLScheduler


@pytest.mark.unit
class TestETLScheduler:
    """Tests ETLScheduler."""
    
    def test_scheduler_starts(self):
        """Scheduler puede iniciarse."""
        # Limpiar si ya existe
        if ETLScheduler.scheduler is not None:
            ETLScheduler.stop()
        
        ETLScheduler.start()
        
        assert ETLScheduler.scheduler is not None
        
        # Limpiar
        ETLScheduler.stop()
    
    def test_scheduler_stops(self):
        """Scheduler puede detenerse."""
        ETLScheduler.start()
        ETLScheduler.stop()
        
        assert ETLScheduler.scheduler is None
    
    def test_scheduler_has_etl_job(self):
        """Scheduler tiene job ETL registrado."""
        ETLScheduler.start()
        
        jobs = ETLScheduler.scheduler.get_jobs()
        job_ids = [j.id for j in jobs]
        
        assert 'etl_job' in job_ids
        
        # Limpiar
        ETLScheduler.stop()
    
    def test_scheduler_job_cron_02am(self):
        """Job ETL configurado para las 02:00 AM diario (CronTrigger)."""
        ETLScheduler.start()
        
        job = ETLScheduler.scheduler.get_job('etl_job')
        
        assert job is not None
        # CronTrigger, no IntervalTrigger
        assert 'cron' in str(type(job.trigger)).lower()
        # Dispara a las 02:00
        trigger_str = str(job.trigger)
        assert '2' in trigger_str  # hora=2
        
        ETLScheduler.stop()
    
    def test_scheduler_idempotent_start(self):
        """Llamar start() multiples veces es seguro."""
        ETLScheduler.start()
        ETLScheduler.start()
        ETLScheduler.start()
        
        assert ETLScheduler.scheduler is not None
        
        # Limpiar
        ETLScheduler.stop()
