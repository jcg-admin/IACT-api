from django.apps import AppConfig


class ReportsConfig(AppConfig):
    def ready(self):
        import apps.reports.schema  # noqa: F401

    """
    App Reports - Generación y exportación reportes.

    CNST-007: Límite 100,000 registros por export.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.reports'
    verbose_name = 'Reports'
