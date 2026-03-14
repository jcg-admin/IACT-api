# apps/alerts/scheduler.py

"""
APScheduler configuration for apps/alerts

Cumple CNST-013: Usa APScheduler en lugar de Celery/RabbitMQ

El scheduler se inicia automáticamente en apps.py ready()
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Singleton scheduler
scheduler = None


def start_scheduler():
    """
    Inicia APScheduler para tareas programadas de alertas
    
    Cumple CNST-013: Usa APScheduler en lugar de Celery
    """
    global scheduler
    
    if scheduler is not None:
        logger.warning("APScheduler ya está corriendo")
        return
    
    scheduler = BackgroundScheduler(
        timezone=settings.TIME_ZONE,
        daemon=True,
    )
    
    # Job: Evaluar alertas cada 5 minutos
    from apps.alerts.services.alert_service import AlertService
    
    scheduler.add_job(
        func=AlertService.evaluate_all_active_configs,
        trigger=IntervalTrigger(minutes=5),
        id='evaluate_alert_configs',
        name='Evaluar configuraciones de alertas',
        replace_existing=True,
        max_instances=1,  # Solo una instancia a la vez
    )
    
    scheduler.start()
    logger.info("[OK] APScheduler iniciado: Evaluación de alertas cada 5 minutos (CNST-013 compliant)")


def stop_scheduler():
    """Detener APScheduler al apagar Django"""
    global scheduler
    if scheduler is not None:
        scheduler.shutdown(wait=True)
        scheduler = None
        logger.info("APScheduler detenido")


def get_scheduler():
    """Obtener instancia del scheduler (para debugging)"""
    return scheduler
