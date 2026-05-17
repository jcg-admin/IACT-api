from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class PipelineConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.pipeline'
    verbose_name = 'ETL Pipeline'

    def ready(self) -> None:
        """
        Start background scheduler on Django startup.
        CNST-004: ETL scheduled every 12 hours — no Celery.
        """
        import apps.pipeline.schema  # noqa: F401

        import sys
        skip_commands = (
            'makemigrations', 'migrate', 'sqlmigrate',
            'showmigrations', 'check', 'spectacular', 'shell',
            'collectstatic', 'test', 'createsuperuser',
        )
        if any(cmd in ' '.join(sys.argv) for cmd in skip_commands):
            logger.info("ETLScheduler: NOT started (management command).")
            return

        logger.info("ETLScheduler: starting from PipelineConfig.ready()...")
        from apps.pipeline.scheduler import ETLScheduler
        ETLScheduler.start()
