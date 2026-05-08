"""
Signals para apps/users/.

Auto-creación de Profile y Settings.
CNST-037: Profile/Settings se crean con User.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.contrib.auth import get_user_model

try:
    from apps.users.models import UserProfile, UserSettings, SessionHistory
except ImportError:
    UserProfile = UserSettings = SessionHistory = None
from apps.utils.helpers import get_client_ip  # <- USAR apps/utils/

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Auto-crear UserProfile al crear User.
    UserProfile puede no estar implementado aún (UserProfile = None).
    """
    if created and UserProfile is not None:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Guardar profile cuando se guarda user."""
    if hasattr(instance, 'profile'):
        instance.profile.save()


@receiver(post_save, sender=User)
def create_user_settings(sender, instance, created, **kwargs):
    """Auto-crear UserSettings al crear User."""
    if created and UserSettings is not None:
        UserSettings.objects.create(user=instance)


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """
    Log sesión al hacer login.
    
    CNST-039: Session auditing.
    USAR: apps.utils.helpers.get_client_ip()
    """
    ip_address = get_client_ip(request)  # <- USAR helper de apps/utils/
    user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]
    
    if SessionHistory is not None:
        SessionHistory.objects.create(
            user=user,
            ip_address=ip_address,
            user_agent=user_agent
        )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log logout."""
    if user and user.is_authenticated:
        from django.utils import timezone
        
        if SessionHistory is not None:
            SessionHistory.objects.filter(
                user=user,
                is_active=True
            ).update(
                logout_at=timezone.now(),
                is_active=False
            )
