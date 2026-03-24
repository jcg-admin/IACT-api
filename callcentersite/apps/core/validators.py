"""
Core validators for the IACT API.
Base-level validators used as model field validators.
"""
import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.utils.validators import (
    validate_file_extension,
    validate_file_size,
    validate_no_special_chars,
    validate_password_strength,
)


# ---------------------------------------------------------------------------
# Re-exports (single import point for consumers)
# ---------------------------------------------------------------------------
__all__ = [
    'validate_file_extension',
    'validate_file_size',
    'validate_no_special_chars',
    'validate_password_strength',
    'validate_module_name',
    'validate_function_code',
    'validate_color_hex',
    'validate_icon_path',
    'validate_json_field',
]


# ---------------------------------------------------------------------------
# Module / navigation validators
# ---------------------------------------------------------------------------

def validate_module_name(value: str) -> None:
    """Module names: 2-100 chars, letters, digits, spaces and hyphens."""
    if not re.match(r'^[\w\s\-]{2,100}$', value, re.UNICODE):
        raise ValidationError(
            _(
                "Nombre de módulo inválido. Use entre 2 y 100 caracteres. "
                "Solo letras, números, espacios y guiones."
            )
        )


def validate_function_code(value: str) -> None:
    """
    Function codes: uppercase letters, digits and underscores.
    Example: 'USERS_LIST', 'REPORTS_EXPORT'
    """
    if not re.match(r'^[A-Z][A-Z0-9_]{1,49}$', value):
        raise ValidationError(
            _(
                "Código de función inválido. Use mayúsculas, números y guiones bajos. "
                "Ej: USERS_LIST"
            )
        )


# ---------------------------------------------------------------------------
# UI / style validators
# ---------------------------------------------------------------------------

def validate_color_hex(value: str) -> None:
    """Validate CSS hex color code (#RGB or #RRGGBB)."""
    if not re.match(r'^#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$', value):
        raise ValidationError(
            _("Color inválido. Use formato hexadecimal: #RGB o #RRGGBB.")
        )


def validate_icon_path(value: str) -> None:
    """Validate icon file path (relative, no directory traversal)."""
    if '..' in value or value.startswith('/'):
        raise ValidationError(
            _("Ruta de icono inválida. No se permiten rutas absolutas ni traversal.")
        )
    if not re.match(r'^[\w\-/]+\.(svg|png|jpg|webp)$', value, re.IGNORECASE):
        raise ValidationError(
            _("Ruta de icono inválida. Solo se permiten archivos SVG, PNG, JPG o WEBP.")
        )


# ---------------------------------------------------------------------------
# Data structure validators
# ---------------------------------------------------------------------------

def validate_json_field(value) -> None:
    """Validate that a value is a JSON-serializable dict or list."""
    import json
    if not isinstance(value, (dict, list)):
        raise ValidationError(
            _("El campo debe ser un objeto JSON válido (dict o list).")
        )
    try:
        json.dumps(value)
    except (TypeError, ValueError):
        raise ValidationError(_("El campo contiene valores no serializables a JSON."))
