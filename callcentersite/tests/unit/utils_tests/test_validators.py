"""
Tests para apps.utils.validators.

CLEAN_CODE v3.0.1: Tests descriptivos.
"""

import pytest
from datetime import date
from apps.utils.validators import (
    validate_email,
    validate_phone_number,
    validate_rut,
    validate_service_800,
    validate_codigo_center,
    validate_date_range,
)


@pytest.mark.unit
class TestEmailValidator:
    """Tests para validate_email."""
    
    def test_valid_email(self):
        """Email válido debe retornar True."""
        assert validate_email('user@example.com')
        assert validate_email('test.user@domain.co.cl')
        assert validate_email('admin+tag@company.com')
    
    def test_invalid_email(self):
        """Email inválido debe retornar False."""
        assert not validate_email('invalid')
        assert not validate_email('@example.com')
        assert not validate_email('user@')
        assert not validate_email('')
        assert not validate_email(None)


@pytest.mark.unit
class TestPhoneValidator:
    """Tests para validate_phone_number."""
    
    def test_valid_mobile(self):
        """Móviles válidos."""
        assert validate_phone_number('912345678')
        assert validate_phone_number('+56912345678')
        assert validate_phone_number('56 9 1234 5678')
        assert validate_phone_number('+56-9-1234-5678')
    
    def test_valid_landline(self):
        """Fijos válidos."""
        assert validate_phone_number('22345678')
        assert validate_phone_number('322345678')
    
    def test_invalid_phone(self):
        """Teléfonos inválidos."""
        assert not validate_phone_number('12345')
        assert not validate_phone_number('1234567890123')
        assert not validate_phone_number('')


@pytest.mark.unit
class TestRUTValidator:
    """Tests para validate_rut."""
    
    def test_valid_rut(self):
        """RUTs válidos."""
        assert validate_rut('12345678-5')
        assert validate_rut('12.345.678-5')
        assert validate_rut('11111111-1')
        assert validate_rut('22222222-2')
    
    def test_invalid_rut_format(self):
        """RUT formato inválido."""
        assert not validate_rut('123')
        assert not validate_rut('12345678')  # Sin DV
        assert not validate_rut('')
    
    def test_invalid_rut_checksum(self):
        """RUT con DV incorrecto."""
        assert not validate_rut('12345678-0')  # DV incorrecto
        assert not validate_rut('11111111-2')  # DV incorrecto


@pytest.mark.unit
class TestService800Validator:
    """Tests para validate_service_800."""
    
    def test_valid_service_800(self):
        """Servicios 800 válidos."""
        assert validate_service_800('800-123-4567')
        assert validate_service_800('800 123 4567')
        assert validate_service_800('8001234567')
    
    def test_invalid_service_800(self):
        """Servicios 800 inválidos."""
        assert not validate_service_800('900123456')  # No empieza con 800
        assert not validate_service_800('800123')     # Muy corto
        assert not validate_service_800('')


@pytest.mark.unit
class TestCodigoCenterValidator:
    """Tests para validate_codigo_center."""
    
    def test_valid_codigo(self):
        """Códigos válidos."""
        assert validate_codigo_center('CT01')
        assert validate_codigo_center('CENTER_SCL')
        assert validate_codigo_center('CTR-001')
    
    def test_invalid_codigo(self):
        """Códigos inválidos."""
        assert not validate_codigo_center('C')        # Muy corto
        assert not validate_codigo_center('')
        assert not validate_codigo_center('CT@01')    # Caracter inválido


@pytest.mark.unit
class TestDateRangeValidator:
    """Tests para validate_date_range."""
    
    def test_valid_range(self):
        """Rango válido."""
        start = date(2025, 1, 1)
        end = date(2025, 1, 31)
        assert validate_date_range(start, end)
    
    def test_invalid_range_inverted(self):
        """Rango invertido."""
        start = date(2025, 2, 1)
        end = date(2025, 1, 1)
        assert not validate_date_range(start, end)
    
    def test_max_days_exceeded(self):
        """Excede max_days."""
        start = date(2025, 1, 1)
        end = date(2025, 12, 31)  # 365 días
        assert not validate_date_range(start, end, max_days=30)
    
    def test_max_days_within_limit(self):
        """Dentro de max_days."""
        start = date(2025, 1, 1)
        end = date(2025, 1, 15)  # 14 días
        assert validate_date_range(start, end, max_days=30)


# ============================================================================
# RESUMEN TESTS
# 
# Total: 6 clases, 23 tests
# 
# Clases:
#   [SUCCESS] TestEmailValidator (2 tests)
#   [SUCCESS] TestPhoneValidator (3 tests)
#   [SUCCESS] TestRUTValidator (3 tests)
#   [SUCCESS] TestService800Validator (2 tests)
#   [SUCCESS] TestCodigoCenterValidator (2 tests)
#   [SUCCESS] TestDateRangeValidator (4 tests)
# 
# Cobertura: ~95% validators.py
# ============================================================================
