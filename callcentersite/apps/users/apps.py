from django.apps import AppConfig


class UsersConfig(AppConfig):
    def ready(self):
        import apps.users.schema  # noqa: F401

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
    verbose_name = 'Usuarios'
