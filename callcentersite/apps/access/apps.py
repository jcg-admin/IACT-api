import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class AccessConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.access'
    verbose_name = 'Control de Acceso'

    def ready(self) -> None:
        import apps.access.schema  # noqa: F401 — registers SPECTACULAR_TAGS

        from apps.access.scheduler import AccessScheduler
        AccessScheduler.start()
