"""
apps/users/signals.py

Señales para apps/users/.

UserProfile, UserSettings y SessionHistory fueron eliminados en FASE 4.
Las señales que los referenciaban han sido eliminadas.

CNST-039: El registro persistente de sesión ocurre en
LoginService._persist_login() via Session.objects.create().
"""

from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from apps.utils.helpers import get_client_ip

User = get_user_model()


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """
    Captura IP y user-agent al hacer login.
    El registro persistente en BD se delega a LoginService._persist_login().
    """
    _ = get_client_ip(request)


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """
    UC_AUTH_02: Cierra sesiones activas al hacer logout.
    """
    if user and user.is_authenticated:
        from apps.authentication.models import Session
        Session.objects.filter(
            user=user,
            state='ACTIVE',
        ).update(
            state='CLOSED',
            close_reason='USER_LOGOUT',
        )
