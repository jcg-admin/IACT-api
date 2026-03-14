from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class PipelineConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.pipeline'
    verbose_name = 'ETL Pipeline'
    
    def ready(self):
        """
        Iniciar scheduler ETL cuando Django inicia.
        
        CNST-004: ETL programado cada 12 horas.
        """
        # Solo iniciar en procesos principales
        # (evitar en migraciones, makemigrations, etc)
        import sys
        
        # Lista de comandos donde NO iniciar scheduler
        skip_commands = [
            'makemigrations',
            'migrate',
            'test',
            'shell',
            'createsuperuser',
        ]
        
        # Detectar si es un comando a evitar
        if len(sys.argv) > 1 and sys.argv[1] in skip_commands:
            logger.info(f"Comando {sys.argv[1]} detectado, "
                       f"NO iniciando scheduler")
            return
        
        # Iniciar scheduler
        logger.info("Iniciando ETLScheduler desde apps.py ready()...")
        from apps.pipeline.scheduler import ETLScheduler
        ETLScheduler.start()

