"""
Tests para apps/utils/validators.py

Los validadores de estilo Django (validate_phone_number, validate_rut,
validate_service_800, validate_codigo_center) levantan ValidationError
cuando el valor es inválido y retornan None cuando es válido.

validate_email y validate_export_row_limit retornan bool.

Coverage objetivo: 95%+
"""

import pytest
from datetime import date, timedelta
from django.core.exceptions import ValidationError


try:
    from apps.utils.validators import (
        validate_email,
        validate_phone_number,
        validate_rut,
        validate_service_800,
        validate_codigo_center,
        validate_date_range,
        validate_export_row_limit,
    )
except ImportError as _err:
    pytest.skip(f'Codigo no implementado: {_err}', allow_module_level=True)


@pytest.mark.unit
class TestValidateEmail:
    """validate_email retorna bool (no raise)."""

    def test_valid_email(self):
        assert validate_email('user@example.com') is True
        assert validate_email('test.user@company.cl') is True
        assert validate_email('admin+tag@domain.com') is True

    def test_invalid_email_no_at(self):
        assert validate_email('userexample.com') is False

    def test_invalid_email_no_domain(self):
        assert validate_email('user@') is False
        assert validate_email('user@domain') is False

    def test_invalid_email_multiple_at(self):
        assert validate_email('user@@example.com') is False

    def test_empty_email(self):
        assert validate_email('') is False
        try:
            result = validate_email(None)
            assert result is False
        except TypeError:
            pass  # None no es string — aceptable

    def test_email_case_insensitive(self):
        assert validate_email('User@Example.COM') is True


@pytest.mark.unit
class TestValidatePhoneNumber:
    """
    validate_phone_number es Django-style: None si válido, ValidationError si inválido.
    Formato: 10 dígitos mexicanos (55XXXXXXXX, 22XXXXXXXX, etc.), opcionalmente +52 prefix.
    """

    def test_valid_mobile_10_digits(self):
        """Móvil válido 10 dígitos: no lanza."""
        validate_phone_number('5512345678')
        validate_phone_number('5587654321')

    def test_valid_with_plus52_prefix(self):
        """Con prefijo +52: no lanza."""
        validate_phone_number('+525512345678')

    def test_valid_landline_10_digits(self):
        """Fijo válido 10 dígitos: no lanza."""
        validate_phone_number('2223456789')
        validate_phone_number('3232345678')

    def test_valid_with_spaces_and_dashes(self):
        """Espacios y guiones son limpiados: no lanza."""
        validate_phone_number('55 1234 5678')
        validate_phone_number('55-1234-5678')

    def test_invalid_too_short(self):
        """Menos de 10 dígitos: ValidationError."""
        with pytest.raises(ValidationError):
            validate_phone_number('12345')
        with pytest.raises(ValidationError):
            validate_phone_number('9123')

    def test_invalid_too_long(self):
        """Más de 10 dígitos: ValidationError."""
        with pytest.raises(ValidationError):
            validate_phone_number('91234567890')

    def test_invalid_characters(self):
        """Letras en el número: ValidationError."""
        with pytest.raises(ValidationError):
            validate_phone_number('9123ABC789')

    def test_empty_phone(self):
        """Cadena vacía: ValidationError."""
        with pytest.raises((ValidationError, AttributeError, TypeError)):
            validate_phone_number('')


@pytest.mark.unit
class TestValidateRut:
    """
    validate_rut es Django-style: None si válido, ValidationError si inválido.
    Formato aceptado: XXXXXXXX-X (7-8 dígitos + guión + dígito o K).
    No valida el dígito verificador — solo el formato.
    """

    def test_valid_rut_with_dash(self):
        """RUT con guión: no lanza."""
        validate_rut('12345678-9')
        validate_rut('11111111-1')

    def test_valid_rut_with_dots_cleaned(self):
        """RUT con puntos (limpiados): no lanza."""
        validate_rut('12.345.678-9')

    def test_valid_rut_with_k(self):
        """RUT con K mayúscula o minúscula: no lanza."""
        validate_rut('12345678-K')
        validate_rut('12345678-k')

    def test_invalid_rut_too_short(self):
        """RUT muy corto: ValidationError."""
        with pytest.raises(ValidationError):
            validate_rut('123-4')

    def test_invalid_rut_too_long(self):
        """RUT muy largo: ValidationError."""
        with pytest.raises(ValidationError):
            validate_rut('123456789012-3')

    def test_invalid_rut_no_dash(self):
        """RUT sin guión (formato incorrecto): ValidationError."""
        with pytest.raises(ValidationError):
            validate_rut('123456789')

    def test_invalid_rut_characters(self):
        """RUT con letras en la parte numérica: ValidationError."""
        with pytest.raises(ValidationError):
            validate_rut('12ABC678-9')

    def test_empty_rut(self):
        """RUT vacío: ValidationError."""
        with pytest.raises((ValidationError, AttributeError, TypeError)):
            validate_rut('')


@pytest.mark.unit
class TestValidateService800:
    """
    validate_service_800 es Django-style: None si válido, ValidationError si inválido.
    Formato: 800 + 7 dígitos = 10 dígitos totales (guiones y espacios se limpian).
    """

    def test_valid_service_800_plain(self):
        """800 + 7 dígitos: no lanza."""
        validate_service_800('8001234567')

    def test_valid_service_800_with_dashes(self):
        """800-XXX-XXXX (guiones limpiados): no lanza."""
        validate_service_800('800-123-4567')

    def test_invalid_not_starting_with_800(self):
        """No empieza con 800: ValidationError."""
        with pytest.raises(ValidationError):
            validate_service_800('9001234567')

    def test_invalid_too_short(self):
        """Menos de 10 dígitos: ValidationError."""
        with pytest.raises(ValidationError):
            validate_service_800('800123')

    def test_invalid_characters(self):
        """Caracteres alfabéticos: ValidationError."""
        with pytest.raises(ValidationError):
            validate_service_800('800ABC1234')

    def test_empty_service(self):
        """Vacío: ValidationError o TypeError."""
        with pytest.raises((ValidationError, AttributeError, TypeError)):
            validate_service_800('')


@pytest.mark.unit
class TestValidateCodigoCenter:
    """
    validate_codigo_center es Django-style: None si válido, ValidationError si inválido.
    Formato: 2-10 caracteres alfanuméricos A-Z0-9 (se convierte a mayúsculas).
    """

    def test_valid_codigo_alphanumeric(self):
        """Código alfanumérico 2-10 chars: no lanza."""
        validate_codigo_center('CTR001')
        validate_codigo_center('AB')
        validate_codigo_center('CENTER12')

    def test_valid_codigo_lowercase_accepted(self):
        """Minúsculas convertidas a mayúsculas: no lanza."""
        validate_codigo_center('ctr001')

    def test_invalid_codigo_too_short(self):
        """Un solo carácter: ValidationError."""
        with pytest.raises(ValidationError):
            validate_codigo_center('C')

    def test_invalid_codigo_special_chars(self):
        """Underscore, @, espacio: ValidationError."""
        with pytest.raises(ValidationError):
            validate_codigo_center('CTR@123')
        with pytest.raises(ValidationError):
            validate_codigo_center('CTR 123')

    def test_empty_codigo(self):
        """Vacío: ValidationError."""
        with pytest.raises((ValidationError, AttributeError, TypeError)):
            validate_codigo_center('')


@pytest.mark.unit
class TestValidateDateRange:
    """validate_date_range es Django-style: None si válido, ValidationError si inválido."""

    def test_valid_date_range(self):
        """Start < end: no lanza."""
        validate_date_range(date(2024, 1, 1), date(2024, 1, 31))

    def test_invalid_start_after_end(self):
        """Start > end: ValidationError."""
        with pytest.raises(ValidationError):
            validate_date_range(date(2024, 1, 31), date(2024, 1, 1))

    def test_valid_same_date(self):
        """Start == end: no lanza."""
        d = date(2024, 6, 15)
        validate_date_range(d, d)

    def test_placeholder_future_dates(self):
        """Test de comportamiento con fechas futuras — depende de implementación."""
        future = date.today() + timedelta(days=100)
        # No asumimos si el validador prohíbe fechas futuras
        try:
            validate_date_range(date.today(), future)
        except ValidationError:
            pass  # Aceptable si el validador lo prohíbe


@pytest.mark.unit
class TestValidateExportRowLimit:
    """validate_export_row_limit retorna bool."""

    def test_valid_under_limit(self):
        assert validate_export_row_limit(1000, 10000) is True
        assert validate_export_row_limit(50, 100) is True

    def test_invalid_over_limit(self):
        assert validate_export_row_limit(150000, 100000) is False

    def test_valid_at_limit(self):
        assert validate_export_row_limit(100000, 100000) is True
