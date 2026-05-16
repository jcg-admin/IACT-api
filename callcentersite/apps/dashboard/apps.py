"""
Configuración de la app Dashboard.

Esta app proporciona dashboards personalizables para visualización
de métricas del call center.
"""

from django.apps import AppConfig


class DashboardConfig(AppConfig):
    """
    Configuración de la aplicación Dashboard.

    Proporciona:
    - Dashboards personalizables por usuario
    - Widgets configurables (8 tipos)
    - Filtros guardados
    - Preferencias de usuario
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.dashboard'
    verbose_name = 'Dashboard'

    def ready(self):
        import apps.dashboard.schema  # noqa: F401
        """
        Importar signals cuando la app esté lista.
        """
        # Import signals to register them
        try:
            from apps.dashboard import signals  # noqa: F401
        except ImportError:
            pass
