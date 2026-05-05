from django.apps import AppConfig


class AccessConfig(AppConfig):
    def ready(self):
        import apps.access.schema  # noqa: F401

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.access'
    verbose_name = 'Control de Acceso'
