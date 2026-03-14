"""
Validators (clases) para IACT.

CLEAN_CODE v3.0.1: Nombres auto-documentados.
NOTA: Funciones de validación van en apps/utils/validators.py
"""

import re
from django.core.exceptions import ValidationError as DjangoValidationError


class PhoneValidator:
    """
    Validador de números telefónicos.
    
    CLEAN_CODE v3.0.1: Nombre que revela intención.
    
    Valida formato de teléfonos chilenos.
    
    Formatos aceptados:
    - +56912345678
    - 912345678
    - +56 9 1234 5678
    - 9 1234 5678
    
    Uso:
        validator = PhoneValidator()
        validator('912345678')  # OK
        validator('123')  # ValidationError
    """
    
    message = 'Formato de teléfono inválido'
    code = 'invalid_phone'
    
    def __call__(self, value):
        """Valida el teléfono."""
        # Limpiar (quitar espacios, +, -)
        cleaned = re.sub(r'[\s\-\+]', '', str(value))
        
        # Validar formato chileno
        # Debe ser: 56912345678 o 912345678
        if not re.match(r'^(56)?9\d{8}$', cleaned):
            raise DjangoValidationError(
                self.message,
                code=self.code
            )


class EmailValidator:
    """
    Validador de emails corporativos.
    
    CLEAN_CODE v3.0.1: Nombre descriptivo.
    
    Valida que email sea de dominio corporativo.
    
    Uso:
        validator = EmailValidator(allowed_domains=['empresa.cl'])
        validator('user@empresa.cl')  # OK
        validator('user@gmail.com')  # ValidationError
    """
    
    message = 'Email debe ser de dominio corporativo'
    code = 'invalid_email_domain'
    
    def __init__(self, allowed_domains=None):
        """
        Inicializa validador.
        
        Args:
            allowed_domains: Lista dominios permitidos
        """
        self.allowed_domains = allowed_domains or []
    
    def __call__(self, value):
        """Valida el email."""
        if not self.allowed_domains:
            return  # Sin restricción
        
        # Extraer dominio
        if '@' not in value:
            raise DjangoValidationError(
                'Email inválido',
                code='invalid_email'
            )
        
        domain = value.split('@')[1].lower()
        
        # Validar dominio
        if domain not in self.allowed_domains:
            raise DjangoValidationError(
                f'Email debe ser de dominio: {", ".join(self.allowed_domains)}',
                code=self.code
            )


class NITValidator:
    """
    Validador de NIT (RUT empresarial).
    
    CLEAN_CODE v3.0.1: Nombre auto-documentado.
    
    Valida formato y dígito verificador de NIT chileno.
    
    Formato: 12.345.678-9
    
    Uso:
        validator = NITValidator()
        validator('76.123.456-7')  # OK
        validator('12345')  # ValidationError
    """
    
    message = 'NIT inválido'
    code = 'invalid_nit'
    
    def __call__(self, value):
        """Valida el NIT."""
        # Limpiar (quitar puntos y guión)
        cleaned = str(value).replace('.', '').replace('-', '')
        
        # Validar largo (8 o 9 dígitos + verificador)
        if len(cleaned) < 8 or len(cleaned) > 9:
            raise DjangoValidationError(
                self.message,
                code=self.code
            )
        
        # Separar cuerpo y verificador
        cuerpo = cleaned[:-1]
        verificador = cleaned[-1].upper()
        
        # Validar que cuerpo sea numérico
        if not cuerpo.isdigit():
            raise DjangoValidationError(
                self.message,
                code=self.code
            )
        
        # Calcular dígito verificador
        suma = 0
        multiplo = 2
        
        for digit in reversed(cuerpo):
            suma += int(digit) * multiplo
            multiplo += 1
            if multiplo == 8:
                multiplo = 2
        
        resto = suma % 11
        dv_calculado = 11 - resto
        
        if dv_calculado == 11:
            dv_calculado = '0'
        elif dv_calculado == 10:
            dv_calculado = 'K'
        else:
            dv_calculado = str(dv_calculado)
        
        # Validar
        if verificador != dv_calculado:
            raise DjangoValidationError(
                f'Dígito verificador incorrecto. Esperado: {dv_calculado}',
                code=self.code
            )


class DateRangeValidator:
    """
    Validador de rangos de fechas.
    
    CLEAN_CODE v3.0.1: Nombre descriptivo.
    
    Valida que fecha esté dentro de rango permitido.
    
    Uso:
        from datetime import date
        
        validator = DateRangeValidator(
            min_date=date(2024, 1, 1),
            max_date=date(2024, 12, 31)
        )
        validator(date(2024, 6, 15))  # OK
        validator(date(2025, 1, 1))  # ValidationError
    """
    
    message = 'Fecha fuera de rango permitido'
    code = 'invalid_date_range'
    
    def __init__(self, min_date=None, max_date=None):
        """
        Inicializa validador.
        
        Args:
            min_date: Fecha mínima (inclusive)
            max_date: Fecha máxima (inclusive)
        """
        self.min_date = min_date
        self.max_date = max_date
    
    def __call__(self, value):
        """Valida la fecha."""
        if self.min_date and value < self.min_date:
            raise DjangoValidationError(
                f'Fecha no puede ser anterior a {self.min_date}',
                code=self.code
            )
        
        if self.max_date and value > self.max_date:
            raise DjangoValidationError(
                f'Fecha no puede ser posterior a {self.max_date}',
                code=self.code
            )


class PositiveIntegerValidator:
    """
    Validador de enteros positivos.
    
    CLEAN_CODE v3.0.1: Nombre auto-documentado.
    
    Valida que valor sea entero positivo (> 0).
    
    Uso:
        validator = PositiveIntegerValidator()
        validator(10)  # OK
        validator(0)  # ValidationError
        validator(-5)  # ValidationError
    """
    
    message = 'Valor debe ser un entero positivo'
    code = 'invalid_positive_integer'
    
    def __call__(self, value):
        """Valida el entero."""
        try:
            int_value = int(value)
        except (TypeError, ValueError):
            raise DjangoValidationError(
                'Valor debe ser numérico',
                code='invalid_numeric'
            )
        
        if int_value <= 0:
            raise DjangoValidationError(
                self.message,
                code=self.code
            )


# ============================================================================
# RESUMEN VALIDATORS
# 
# Total: 5 validators (clases)
# 
# Validators:
#   [SUCCESS] PhoneValidator (teléfonos chilenos)
#   [SUCCESS] EmailValidator (emails corporativos)
#   [SUCCESS] NITValidator (RUT empresarial)
#   [SUCCESS] DateRangeValidator (rangos de fechas)
#   [SUCCESS] PositiveIntegerValidator (enteros positivos)
# 
# CLEAN_CODE v3.0.1:
#   [SUCCESS] Nombres auto-documentados
#   [SUCCESS] Docstrings Google Style
#   [SUCCESS] Ejemplos de uso
#   [SUCCESS] Callable classes (pattern validator)
# 
# NOTA: 
#   Funciones de validación simples van en apps/utils/validators.py
#   Estas son CLASES para casos más complejos
# ============================================================================
