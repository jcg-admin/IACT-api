from django.apps import AppConfig
import sys
import logging

logger = logging.getLogger(__name__)


class AlertsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.alerts'
    verbose_name = 'Sistema de Alertas Internas'
    
    def ready(self):
        import apps.alerts.schema  # noqa: F401
        """
        Inicializar APScheduler cuando Django arranca
        
        IMPORTANTE: Solo en servidor web, NO en shell/migrations
        
        Cumple CNST-013: APScheduler para tareas programadas
        """
        # Verificar si es un comando que debe iniciar scheduler
        # runserver o gunicorn = SÍ
        # makemigrations, migrate, shell = NO
        
        argv = sys.argv
        
        # Detectar runserver
        is_runserver = 'runserver' in argv
        
        # Detectar gunicorn (nombre del proceso)
        is_gunicorn = 'gunicorn' in argv[0] if argv else False
        
        # Detectar comandos que NO deben iniciar scheduler
        skip_commands = [
            'makemigrations',
            'migrate',
            'shell',
            'shell_plus',
            'test',
            'dbshell',
            'createsuperuser',
            'collectstatic',
            'check',
        ]
        is_skip_command = any(cmd in argv for cmd in skip_commands)
        
        # Iniciar scheduler solo si es servidor web
        if (is_runserver or is_gunicorn) and not is_skip_command:
            from apps.alerts.scheduler import start_scheduler
            try:
                start_scheduler()
                logger.info("[OK] Alerts app ready: APScheduler iniciado")
            except Exception as e:
                logger.error(f"[FAIL] Error iniciando APScheduler: {e}")
        else:
            logger.info(f"Alerts app ready: APScheduler NO iniciado (comando: {' '.join(argv)})")
