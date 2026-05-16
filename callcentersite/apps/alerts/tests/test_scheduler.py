# apps/alerts/tests/test_scheduler.py

from django.test import TestCase
from apps.alerts.scheduler import start_scheduler, stop_scheduler, get_scheduler


class SchedulerTest(TestCase):
    """Tests para APScheduler - CNST-013 compliance"""
    
    def tearDown(self):
        """Detener scheduler después de cada test"""
        stop_scheduler()
    
    def test_start_scheduler(self):
        """Test: Iniciar scheduler"""
        start_scheduler()
        
        scheduler = get_scheduler()
        
        self.assertIsNotNone(scheduler)
        self.assertTrue(scheduler.running)
    
    def test_stop_scheduler(self):
        """Test: Detener scheduler"""
        start_scheduler()
        stop_scheduler()
        
        scheduler = get_scheduler()
        
        self.assertIsNone(scheduler)
    
    def test_scheduler_has_job(self):
        """Test: Scheduler tiene job 'evaluate_alert_configs'"""
        start_scheduler()
        
        scheduler = get_scheduler()
        jobs = scheduler.get_jobs()
        
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].id, 'evaluate_alert_configs')
        self.assertEqual(jobs[0].name, 'Evaluar configuraciones de alertas')
    
    def test_job_trigger_interval(self):
        """Test: Job tiene trigger de 5 minutos"""
        start_scheduler()
        
        scheduler = get_scheduler()
        job = scheduler.get_job('evaluate_alert_configs')
        
        # Verificar que es IntervalTrigger
        self.assertEqual(str(job.trigger), 'interval[0:05:00]')
    
    def test_no_celery_imports(self):
        """Test: ⭐ CNST-013 - NO hay imports de Celery/RabbitMQ/Kafka"""
        import os
        
        # Buscar imports prohibidos en todos los archivos de apps/alerts
        alerts_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__))
        )
        
        # Buscar en archivos .py
        prohibited_imports = [
            'from celery',
            'import celery',
            'from kombu',
            'import kombu',
            'from pika',
            'import pika',
            'from kafka',
            'import kafka',
            'from confluent',
            'import confluent'
        ]
        
        violations = []
        
        # Buscar archivos Python
        for root, dirs, files in os.walk(alerts_path):
            # Ignorar __pycache__
            dirs[:] = [d for d in dirs if d != '__pycache__']
            
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    
                    with open(filepath, 'r') as f:
                        content = f.read()
                        
                        for prohibited in prohibited_imports:
                            if prohibited in content:
                                # Verificar que no es un comentario
                                for line in content.split('\n'):
                                    if prohibited in line and not line.strip().startswith('#'):
                                        violations.append({
                                            'file': filepath,
                                            'import': prohibited,
                                            'line': line.strip()
                                        })
        
        # Assertion: NO debe haber violaciones
        if violations:
            violation_msg = '\n'.join([
                f"  - {v['file']}: {v['import']}"
                for v in violations
            ])
            self.fail(
                f"CNST-013 VIOLADO: Se encontraron imports prohibidos:\n{violation_msg}"
            )
        
        # Si llegamos aquí, no hay violaciones
        self.assertTrue(True, "CNST-013 cumplido: No hay imports de Celery/RabbitMQ/Kafka")


class SchedulerSingletonTest(TestCase):
    """Tests para patrón Singleton del scheduler"""
    
    def tearDown(self):
        """Detener scheduler después de cada test"""
        stop_scheduler()
    
    def test_singleton_pattern(self):
        """Test: Solo una instancia de scheduler"""
        start_scheduler()
        scheduler1 = get_scheduler()
        
        # Intentar iniciar de nuevo
        start_scheduler()
        scheduler2 = get_scheduler()
        
        # Debe ser la misma instancia
        self.assertIs(scheduler1, scheduler2)
    
    def test_scheduler_restarts_after_stop(self):
        """Test: Scheduler puede reiniciarse después de detenerse"""
        # Iniciar
        start_scheduler()
        scheduler1 = get_scheduler()
        self.assertIsNotNone(scheduler1)
        
        # Detener
        stop_scheduler()
        scheduler_after_stop = get_scheduler()
        self.assertIsNone(scheduler_after_stop)
        
        # Reiniciar
        start_scheduler()
        scheduler2 = get_scheduler()
        self.assertIsNotNone(scheduler2)
        
        # Debe ser una nueva instancia
        self.assertIsNot(scheduler1, scheduler2)
