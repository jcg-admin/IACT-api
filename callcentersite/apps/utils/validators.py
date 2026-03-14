"""
Validators para apps/utils/.

CLEAN_CODE v3.0.1: Funciones auto-documentadas.
SOLID: SRP (Single Responsibility), DRY (Don't Repeat Yourself).

IMPORTANTE: 
- Este módulo tiene FUNCIONES de validación simples
- apps/core/validators.py tiene CLASES validadoras complejas
"""

import re
from datetime import datetime, date
from typing import Optional


# ============================================================================
# EMAIL VALIDATION
# ============================================================================

def validate_email(email: str) -> bool:
    """
    Valida formato de email.
    
    CLEAN_CODE v3.0.1: Nombre que revela intención.
    
    Args:
        email: Email a validar
    
    Returns:
        bool: True si válido
    
    Examples:
        >>> validate_email('user@example.com')
        True
        >>> validate_email('invalid.email')
        False
    """
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


# ============================================================================
# PHONE VALIDATION (CHILE)
# ============================================================================

def validate_phone_number(phone: str) -> bool:
    """
    Valida número telefónico chileno.
    
    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID SRP: Solo valida teléfonos chilenos.
    
    Acepta:
    - Móviles: 9 dígitos empezando con 9
    - Fijos: 8 dígitos
    - Con/sin +56
    - Con/sin espacios, guiones
    
    Args:
        phone: Teléfono
    
    Returns:
        bool: True si válido
    
    Examples:
        >>> validate_phone_number('+56 9 1234 5678')
        True
        >>> validate_phone_number('912345678')
        True
        >>> validate_phone_number('12345')
        False
    """
    if not phone:
        return False
    
    # DRY: Helper privado para limpiar
    clean_phone = _clean_phone_number(phone)
    
    # Validar móvil (9 dígitos, empieza con 9)
    if re.match(r'^9\d{8}$', clean_phone):
        return True
    
    # Validar fijo (8 dígitos, empieza con 2-9)
    if re.match(r'^[2-9]\d{7}$', clean_phone):
        return True
    
    return False


def _clean_phone_number(phone: str) -> str:
    """
    Limpia número telefónico.
    
    SOLID SRP: Solo limpia, no valida.
    DRY: Reutilizable por múltiples funciones.
    
    Args:
        phone: Teléfono
    
    Returns:
        str: Teléfono limpio (solo dígitos)
    """
    # Remover espacios, guiones, paréntesis, +
    cleaned = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '').replace('+', '')
    
    # Remover código país si existe (56)
    if cleaned.startswith('56'):
        cleaned = cleaned[2:]
    
    return cleaned


# ============================================================================
# RUT VALIDATION (CHILE)
# ============================================================================

def validate_rut(rut: str) -> bool:
    """
    Valida RUT chileno.
    
    CLEAN_CODE v3.0.1: Nombre que revela intención.
    SOLID SRP: Solo valida RUT, usa helpers para cada paso.
    
    Args:
        rut: RUT - formato: 12345678-9 o 12.345.678-9
    
    Returns:
        bool: True si válido
    
    Examples:
        >>> validate_rut('12.345.678-5')
        True
        >>> validate_rut('12345678-5')
        True
        >>> validate_rut('123')
        False
    """
    if not rut:
        return False
    
    # DRY: Helper para limpiar
    clean_rut = _clean_rut(rut)
    
    # DRY: Helper para validar formato
    if not _has_valid_rut_format(clean_rut):
        return False
    
    # DRY: Helper para validar checksum
    return _validate_rut_checksum(clean_rut)


def _clean_rut(rut: str) -> str:
    """
    Limpia RUT.
    
    SOLID SRP: Solo limpia.
    
    Args:
        rut: RUT
    
    Returns:
        str: RUT limpio
    """
    return rut.replace('.', '').replace('-', '').replace(' ', '').upper()


def _has_valid_rut_format(rut: str) -> bool:
    """
    Valida formato RUT.
    
    SOLID SRP: Solo valida formato, no checksum.
    
    Args:
        rut: RUT limpio
    
    Returns:
        bool: True si formato válido
    """
    return bool(re.match(r'^\d{7,8}[0-9K]$', rut))


def _validate_rut_checksum(rut: str) -> bool:
    """
    Valida dígito verificador RUT.
    
    SOLID SRP: Solo valida checksum.
    
    Args:
        rut: RUT limpio
    
    Returns:
        bool: True si checksum válido
    """
    body = rut[:-1]
    dv = rut[-1]
    
    calculated_dv = _calculate_rut_dv(body)
    
    return calculated_dv == dv


def _calculate_rut_dv(rut_body: str) -> str:
    """
    Calcula dígito verificador RUT.
    
    SOLID SRP: Solo calcula DV.
    DRY: Reutilizable.
    
    Args:
        rut_body: Cuerpo del RUT (sin DV)
    
    Returns:
        str: Dígito verificador calculado
    """
    reversed_digits = map(int, reversed(rut_body))
    factors = [2, 3, 4, 5, 6, 7]
    
    s = sum(d * factors[i % 6] for i, d in enumerate(reversed_digits))
    remainder = 11 - (s % 11)
    
    if remainder == 11:
        return '0'
    elif remainder == 10:
        return 'K'
    else:
        return str(remainder)


# ============================================================================
# SERVICE 800 VALIDATION
# ============================================================================

def validate_service_800(service: str) -> bool:
    """
    Valida número servicio 800.
    
    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID SRP: Solo valida números 800.
    
    Formatos aceptados:
    - 800-XXX-XXXX
    - 800XXXXXXX
    - 800 XXX XXXX
    
    Args:
        service: Número 800
    
    Returns:
        bool: True si válido
    
    Examples:
        >>> validate_service_800('800-123-4567')
        True
        >>> validate_service_800('800123456')
        False
    """
    if not service:
        return False
    
    # Limpiar
    clean_service = service.replace('-', '').replace(' ', '')
    
    # Validar formato: 800 + 7 dígitos = 10 total
    return bool(re.match(r'^800\d{7}$', clean_service))


# ============================================================================
# CODIGO CENTER VALIDATION
# ============================================================================

def validate_codigo_center(codigo: str) -> bool:
    """
    Valida código de centro.
    
    CLEAN_CODE v3.0.1: Nombre que revela intención.
    SOLID SRP: Solo valida códigos de centro.
    
    Formato: 2-20 caracteres alfanuméricos, puede tener guiones/underscores.
    
    Args:
        codigo: Código del centro
    
    Returns:
        bool: True si válido
    
    Examples:
        >>> validate_codigo_center('CT01')
        True
        >>> validate_codigo_center('CENTER_SCL')
        True
        >>> validate_codigo_center('C')
        False
    """
    if not codigo:
        return False
    
    # 2-20 caracteres alfanuméricos + guiones/underscores
    return bool(re.match(r'^[A-Z0-9_-]{2,20}$', codigo, re.IGNORECASE))


# ============================================================================
# DATE RANGE VALIDATION
# ============================================================================

def validate_date_range(
    start_date: date,
    end_date: date,
    max_days: Optional[int] = None
) -> bool:
    """
    Valida rango de fechas.
    
    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID SRP: Solo valida rango.
    
    Args:
        start_date: Fecha inicio
        end_date: Fecha fin
        max_days: Máximo de días permitidos (opcional)
    
    Returns:
        bool: True si válido
    
    Examples:
        >>> from datetime import date
        >>> validate_date_range(date(2025, 1, 1), date(2025, 1, 31))
        True
        >>> validate_date_range(date(2025, 2, 1), date(2025, 1, 1))
        False
    """
    # start_date debe ser <= end_date
    if start_date > end_date:
        return False
    
    # Validar max_days si se especifica
    if max_days:
        delta = (end_date - start_date).days
        if delta > max_days:
            return False
    
    return True


# ============================================================================
# RESUMEN VALIDATORS
# 
# Total: 9 funciones públicas + 5 helpers privados
# 
# Funciones Públicas:
#   [SUCCESS] validate_email()
#   [SUCCESS] validate_phone_number()
#   [SUCCESS] validate_rut()
#   [SUCCESS] validate_service_800()
#   [SUCCESS] validate_codigo_center()
#   [SUCCESS] validate_date_range()
# 
# Helpers Privados (DRY):
#   [SUCCESS] _clean_phone_number()
#   [SUCCESS] _clean_rut()
#   [SUCCESS] _has_valid_rut_format()
#   [SUCCESS] _validate_rut_checksum()
#   [SUCCESS] _calculate_rut_dv()
# 
# Principios SOLID Aplicados:
#   [SUCCESS] SRP: Cada función una responsabilidad
#   [SUCCESS] DRY: Código común en helpers privados
#   [SUCCESS] Clean Naming: Nombres que revelan intención
#   [SUCCESS] Type Hints: Todas las funciones
# ============================================================================


def validate_export_row_limit(row_count: int, max_limit: int = 100000) -> None:
    """
    Valida límite de filas para exportación.
    
    Args:
        row_count: Número de filas a exportar
        max_limit: Límite máximo permitido
    
    Raises:
        ValueError: Si excede el límite
    
    Example:
        >>> validate_export_row_limit(50000)  # OK
        >>> validate_export_row_limit(150000)  # ValueError
    """
    if row_count > max_limit:
        raise ValueError(
            f"La exportación excede el límite permitido. "
            f"Solicitadas: {row_count}, Máximo: {max_limit}"
        )
