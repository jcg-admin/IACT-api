"""
Configuración de app authentication.

CLEAN_CODE v3.0.1: AppConfig auto-documentado.
"""

from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    """
    Configuración de app authentication.

    CLEAN_CODE v3.0.1: Nombre que revela intención.
    SOLID SRP: Solo configuración de app.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.authentication'
    verbose_name = 'Autenticación y Seguridad'

    def ready(self):
        import apps.authentication.schema  # noqa: F401
        """
        Inicialización cuando app está lista.

        SOLID OCP: Extensible sin modificar.
        """
        # Importar signals si se crean en el futuro
        # import apps.authentication.signals  # noqa
        pass
