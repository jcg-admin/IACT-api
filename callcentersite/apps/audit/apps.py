from django.apps import AppConfig


class AuditConfig(AppConfig):
    def ready(self):
        import apps.audit.schema  # noqa: F401

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.audit'
    verbose_name = 'Audit'
