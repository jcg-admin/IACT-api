"""
User-specific validators for the IACT API.
Validates avatars, passwords and user fields.
"""
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.utils.validators import (
    validate_file_extension,
    validate_file_size,
    validate_password_strength,
    validate_phone_number,
    validate_username,
)


# ---------------------------------------------------------------------------
# Avatar validators (composed from utils)
# ---------------------------------------------------------------------------

def validate_avatar(image_file) -> None:
    """
    Full validation for avatar uploads.
    Checks extension and size in one call.
    """
    validate_file_extension(image_file)
    validate_file_size(image_file)


def validate_avatar_extension(image_file) -> None:
    """Validate only the avatar file extension."""
    validate_file_extension(image_file)


def validate_avatar_size(image_file) -> None:
    """Validate only the avatar file size."""
    validate_file_size(image_file)


# ---------------------------------------------------------------------------
# Password change validators
# ---------------------------------------------------------------------------

def validate_new_password(value: str, user=None) -> None:
    """
    Validate a new password:
    - Must meet strength requirements.
    - Must not be the same as the current password (if user is provided).
    """
    validate_password_strength(value)

    if user and user.pk and user.check_password(value):
        raise ValidationError(
            _("La nueva contraseña no puede ser igual a la contraseña actual.")
        )


def validate_password_confirmation(password: str, confirmation: str) -> None:
    """Validate that password and confirmation match."""
    if password != confirmation:
        raise ValidationError(_("Las contraseñas no coinciden."))


# ---------------------------------------------------------------------------
# User field validators (re-exports for use in serializers)
# ---------------------------------------------------------------------------

def validate_user_username(value: str) -> None:
    """Validate username for a user."""
    validate_username(value)


def validate_user_phone(value: str) -> None:
    """Validate phone number for a user."""
    if value:
        validate_phone_number(value)


# ---------------------------------------------------------------------------
# Profile validators
# ---------------------------------------------------------------------------

def validate_employee_id(value: str) -> None:
    """
    Employee ID: 3-20 alphanumeric characters.
    Example: 'EMP001', 'AGT12345'
    """
    import re
    if not re.match(r'^[A-Za-z0-9\-]{3,20}$', value):
        raise ValidationError(
            _("ID de empleado inválido. Use entre 3 y 20 caracteres alfanuméricos.")
        )
