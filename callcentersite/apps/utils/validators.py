"""
Shared validators for the IACT API.
Used across multiple apps.
"""
import os
import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


# ---------------------------------------------------------------------------
# String validators
# ---------------------------------------------------------------------------

def validate_no_special_chars(value: str) -> None:
    """Allow only alphanumeric, spaces, hyphens and underscores."""
    if not re.match(r'^[\w\s\-]+$', value, re.UNICODE):
        raise ValidationError(
            _("El valor '%(value)s' contiene caracteres no permitidos."),
            params={'value': value},
        )


def validate_alphanumeric(value: str) -> None:
    """Allow only alphanumeric characters."""
    if not re.match(r'^[a-zA-Z0-9]+$', value):
        raise ValidationError(
            _("Solo se permiten letras y números."),
        )


def validate_phone_number(value: str) -> None:
    """Validate Mexican phone number format (10 digits, optionally +52 prefix)."""
    cleaned = re.sub(r'[\s\-\(\)]', '', value)
    if re.match(r'^\+52', cleaned):
        cleaned = cleaned[3:]
    if not re.match(r'^\d{10}$', cleaned):
        raise ValidationError(
            _("Formato de teléfono inválido. Use 10 dígitos (ej: 5512345678)."),
        )


def validate_username(value: str) -> None:
    """
    Username: 3-50 chars, starts with letter, allows letters/digits/underscores/dots/hyphens.
    """
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9._\-]{2,49}$', value):
        raise ValidationError(
            _(
                "El nombre de usuario debe tener entre 3 y 50 caracteres, "
                "comenzar con una letra, y solo contener letras, números, "
                "puntos, guiones o guiones bajos."
            )
        )


# ---------------------------------------------------------------------------
# Password validators
# ---------------------------------------------------------------------------

def validate_password_strength(value: str) -> None:
    """
    Password must have:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """
    errors = []

    if len(value) < 8:
        errors.append(_("Mínimo 8 caracteres."))

    if not re.search(r'[A-Z]', value):
        errors.append(_("Al menos una letra mayúscula."))

    if not re.search(r'[a-z]', value):
        errors.append(_("Al menos una letra minúscula."))

    if not re.search(r'\d', value):
        errors.append(_("Al menos un número."))

    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-]', value):
        errors.append(_("Al menos un carácter especial (!@#$%^&*...)."))

    if errors:
        raise ValidationError(errors)


# ---------------------------------------------------------------------------
# Date validators
# ---------------------------------------------------------------------------

def validate_date_range(start_date, end_date) -> None:
    """Validate that start_date is before end_date."""
    if start_date and end_date and start_date > end_date:
        raise ValidationError(
            _("La fecha de inicio debe ser anterior a la fecha de fin.")
        )


def validate_not_future_date(value) -> None:
    """Validate that a date is not in the future."""
    from django.utils import timezone
    if value > timezone.now().date():
        raise ValidationError(
            _("La fecha no puede ser futura.")
        )


# ---------------------------------------------------------------------------
# File validators
# ---------------------------------------------------------------------------

def validate_file_extension(value, allowed_extensions=None) -> None:
    """Validate file extension against an allowed list."""
    if allowed_extensions is None:
        allowed_extensions = getattr(settings, 'ALLOWED_IMAGE_EXTENSIONS', ['.jpg', '.jpeg', '.png', '.webp'])

    ext = os.path.splitext(value.name)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(
            _("Extensión '%(ext)s' no permitida. Use: %(allowed)s."),
            params={
                'ext': ext,
                'allowed': ', '.join(allowed_extensions),
            },
        )


def validate_file_size(value, max_size=None) -> None:
    """Validate that a file does not exceed the maximum allowed size."""
    if max_size is None:
        max_size = getattr(settings, 'MAX_AVATAR_SIZE', 2 * 1024 * 1024)  # 2 MB

    if value.size > max_size:
        max_mb = max_size / (1024 * 1024)
        raise ValidationError(
            _("El archivo es demasiado grande. Tamaño máximo: %(max)s MB."),
            params={'max': f'{max_mb:.1f}'},
        )


# ---------------------------------------------------------------------------
# Numeric validators
# ---------------------------------------------------------------------------

def validate_positive_integer(value: int) -> None:
    """Validate that value is a positive integer (> 0)."""
    if value <= 0:
        raise ValidationError(_("El valor debe ser un entero positivo mayor a cero."))


def validate_percentage(value) -> None:
    """Validate that a value is between 0 and 100."""
    if not (0 <= value <= 100):
        raise ValidationError(_("El porcentaje debe estar entre 0 y 100."))
