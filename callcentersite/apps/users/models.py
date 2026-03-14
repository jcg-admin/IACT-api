"""
User model for the IACT API.
Extends AbstractUser with avatar, profile and RBAC support.
"""
import os

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimestampedModel
from apps.utils.helpers import avatar_upload_path


class User(AbstractUser, TimestampedModel):
    """
    Custom user model for IACT.
    Adds avatar, employee data and RBAC helpers.
    """

    # Profile
    avatar = models.ImageField(
        upload_to=avatar_upload_path,
        blank=True,
        null=True,
        verbose_name=_('Avatar'),
        help_text=_('Foto de perfil del usuario (JPG, PNG, WEBP - max 2 MB)'),
    )
    employee_id = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('ID de empleado'),
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Teléfono'),
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Departamento'),
    )

    # Account state
    failed_login_attempts = models.PositiveSmallIntegerField(
        default=0,
        verbose_name=_('Intentos fallidos de login'),
    )
    is_locked = models.BooleanField(
        default=False,
        verbose_name=_('Cuenta bloqueada'),
    )
    locked_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Bloqueado el'),
    )
    must_change_password = models.BooleanField(
        default=False,
        verbose_name=_('Debe cambiar contraseña'),
    )
    last_password_change = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Ultimo cambio de contraseña'),
    )

    class Meta:
        verbose_name = _('Usuario')
        verbose_name_plural = _('Usuarios')
        ordering = ['username']
        db_table = 'users_user'

    def __str__(self):
        return self.get_full_name() or self.username

    # ------------------------------------------------------------------
    # Avatar helpers
    # ------------------------------------------------------------------

    def get_avatar_url(self) -> str:
        """Return the avatar URL, or empty string if not set."""
        if self.avatar:
            return self.avatar.url
        return ''

    def delete_avatar(self) -> bool:
        """Delete the avatar file from storage and clear the field."""
        if not self.avatar:
            return False
        path = self.avatar.path
        self.avatar.delete(save=False)
        self.avatar = None
        self.save(update_fields=['avatar'])
        if os.path.exists(path):
            os.remove(path)
        return True

    # ------------------------------------------------------------------
    # RBAC helpers
    # ------------------------------------------------------------------

    def get_functions(self) -> list[str]:
        """
        Return a list of function codes the user has permission to access.
        Combines direct user permissions and role-based permissions.
        """
        from apps.access.services import get_user_function_codes
        return get_user_function_codes(self)

    def has_function(self, function_code: str) -> bool:
        """Check if user has access to a specific function code."""
        return function_code in self.get_functions()

    def lock_account(self) -> None:
        """Lock the user account."""
        from django.utils import timezone
        self.is_locked = True
        self.locked_at = timezone.now()
        self.save(update_fields=['is_locked', 'locked_at'])

    def unlock_account(self) -> None:
        """Unlock the user account and reset failed attempts."""
        self.is_locked = False
        self.locked_at = None
        self.failed_login_attempts = 0
        self.save(update_fields=['is_locked', 'locked_at', 'failed_login_attempts'])

    def increment_failed_login(self, max_attempts: int = 5) -> None:
        """Increment failed login counter. Lock account if max is reached."""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= max_attempts:
            self.lock_account()
        else:
            self.save(update_fields=['failed_login_attempts'])

    def reset_failed_login(self) -> None:
        """Reset failed login counter on successful login."""
        if self.failed_login_attempts > 0:
            self.failed_login_attempts = 0
            self.save(update_fields=['failed_login_attempts'])
