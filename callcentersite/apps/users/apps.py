"""AppConfig para users."""

from django.apps import AppConfig


class UsersConfig(AppConfig):
    """Configuración de app users."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
    verbose_name = 'Usuarios'
    
    def ready(self):
        """Importar signals."""
        import apps.users.signals  # noqa
