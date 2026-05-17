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
    Códigos de función RBAC — formato canónico v5.4.0.

    Formato: MOD-NNN
    - MOD: 2-4 letras mayúsculas (prefijo de módulo)
    - NNN: 3 dígitos (secuencia 001..999)

    Ejemplos válidos: AUTH-001, USR-009, ACC-012, LOG-007, RPT-011
    Ejemplos inválidos: USR_VIEW (legacy v6.0.0), reports.view (namespace)

    Fuente: arquitectura-tecnica/rbac/modelo-rbac-iact.rst v5.4.0
    CNST-033: vocabulario unificado RBAC — inglés, sin namespaces Django.
    """
    if not re.match(r'^[A-Z]{2,4}-\d{3}$', value):
        raise ValidationError(
            _(
                "Código de función inválido: %(value)s. "
                "Use formato MOD-NNN (ej: AUTH-001, RPT-011). "
                "Fuente: modelo-rbac-iact.rst v5.4.0."
            ),
            params={'value': value},
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
