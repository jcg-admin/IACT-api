from django.apps import AppConfig


class IvrConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.ivr'

    def ready(self):
        import apps.ivr.schema  # noqa: F401
