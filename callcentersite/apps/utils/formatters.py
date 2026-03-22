"""
Formatters para apps/utils/.

CLEAN_CODE v3.0.1: Funciones auto-documentadas.
SOLID: SRP (Single Responsibility), DRY (Don't Repeat Yourself).
"""

import re
from decimal import Decimal
from typing import Optional


# ============================================================================
# PHONE FORMATTING
# ============================================================================

def format_phone_cl(phone: str, with_country_code: bool = False) -> str:
    """
    Formatea teléfono chileno.
    
    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID SRP: Solo formatea, no valida.
    
    Args:
        phone: Teléfono
        with_country_code: Incluir +56
    
    Returns:
        str: Teléfono formateado
    
    Examples:
        >>> format_phone_cl('912345678')
        '9 1234 5678'
        >>> format_phone_cl('912345678', with_country_code=True)
        '+56 9 1234 5678'
    """
    # DRY: Usar helper de validators
    from apps.utils.validators import _clean_phone_number
    clean = _clean_phone_number(phone)
    
    if len(clean) == 9:  # Móvil
        formatted = f"{clean[0]} {clean[1:5]} {clean[5:]}"
    elif len(clean) == 8:  # Fijo
        formatted = f"{clean[0:2]} {clean[2:6]} {clean[6:]}"
    else:
        return phone  # Retornar sin cambios si formato desconocido
    
    if with_country_code:
        formatted = f"+56 {formatted}"
    
    return formatted


# ============================================================================
# RUT FORMATTING
# ============================================================================

def format_rut(rut: str) -> str:
    """
    Formatea RUT chileno.
    
    CLEAN_CODE v3.0.1: Nombre que revela intención.
    SOLID SRP: Solo formatea.
    
    Args:
        rut: RUT
    
    Returns:
        str: RUT formateado (12.345.678-9)
    
    Examples:
        >>> format_rut('123456789')
        '12.345.678-9'
        >>> format_rut('12345678K')
        '12.345.678-K'
    """
    # DRY: Usar helper de validators
    from apps.utils.validators import _clean_rut
    clean = _clean_rut(rut)
    
    if len(clean) < 2:
        return rut  # Retornar sin cambios
    
    # Separar cuerpo y DV
    body = clean[:-1]
    dv = clean[-1]
    
    # Formatear cuerpo con puntos
    formatted_body = _format_number_with_dots(body)
    
    return f"{formatted_body}-{dv}"


def _format_number_with_dots(number: str) -> str:
    """
    Formatea número con puntos de miles.
    
    SOLID SRP: Solo formatea.
    DRY: Reutilizable.
    
    Args:
        number: Número como string
    
    Returns:
        str: Número con puntos
    
    Examples:
        >>> _format_number_with_dots('12345678')
        '12.345.678'
    """
    # Insertar puntos cada 3 dígitos desde la derecha
    reversed_num = number[::-1]
    groups = [reversed_num[i:i+3] for i in range(0, len(reversed_num), 3)]
    formatted = '.'.join(groups)
    return formatted[::-1]


# ============================================================================
# CURRENCY FORMATTING
# ============================================================================

def format_currency(
    amount: float,
    currency: str = 'CLP',
    decimals: int = 0
) -> str:
    """
    Formatea monto como moneda.
    
    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID SRP: Solo formatea moneda.
    
    Args:
        amount: Monto
        currency: Moneda ('CLP', 'USD', 'EUR')
        decimals: Decimales a mostrar
    
    Returns:
        str: Monto formateado
    
    Examples:
        >>> format_currency(1234567)
        '$1.234.567'
        >>> format_currency(1234.56, currency='USD', decimals=2)
        'USD 1,234.56'
    """
    if currency == 'CLP':
        # Formato chileno: $1.234.567
        formatted_number = _format_number_cl(amount, decimals)
        return f"${formatted_number}"
    
    elif currency in ['USD', 'EUR']:
        # Formato internacional: USD 1,234.56
        formatted_number = _format_number_intl(amount, decimals)
        return f"{currency} {formatted_number}"
    
    else:
        # Formato genérico
        return f"{currency} {amount:,.{decimals}f}"


def _format_number_cl(number: float, decimals: int = 0) -> str:
    """
    Formatea número estilo chileno.
    
    SOLID SRP: Solo formatea.
    DRY: Reutilizable.
    
    Args:
        number: Número
        decimals: Decimales
    
    Returns:
        str: Número formateado (1.234.567,89)
    """
    # Redondear
    rounded = round(number, decimals)
    
    # Separar parte entera y decimal
    if decimals > 0:
        formatted = f"{rounded:,.{decimals}f}"
        # Cambiar , por punto y . por coma (estilo chileno)
        formatted = formatted.replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.')
    else:
        formatted = f"{int(rounded):,}".replace(',', '.')
    
    return formatted


def _format_number_intl(number: float, decimals: int = 2) -> str:
    """
    Formatea número estilo internacional.
    
    SOLID SRP: Solo formatea.
    
    Args:
        number: Número
        decimals: Decimales
    
    Returns:
        str: Número formateado (1,234.56)
    """
    return f"{number:,.{decimals}f}"


# ============================================================================
# PERCENTAGE FORMATTING
# ============================================================================

def format_percentage(
    value: float,
    decimals: int = 2,
    include_symbol: bool = True
) -> str:
    """
    Formatea porcentaje.
    
    CLEAN_CODE v3.0.1: Nombre que revela intención.
    SOLID SRP: Solo formatea porcentajes.
    
    Args:
        value: Valor (0.1234 = 12.34%)
        decimals: Decimales
        include_symbol: Incluir símbolo %
    
    Returns:
        str: Porcentaje formateado
    
    Examples:
        >>> format_percentage(0.1234)
        '12.34%'
        >>> format_percentage(0.5, decimals=1)
        '50.0%'
    """
    percentage = value * 100
    formatted = f"{percentage:.{decimals}f}"
    
    if include_symbol:
        return f"{formatted}%"
    
    return formatted


# ============================================================================
# SERVICE 800 FORMATTING
# ============================================================================

def format_service_800(service: str) -> str:
    """
    Formatea número servicio 800.
    
    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID SRP: Solo formatea.
    
    Args:
        service: Número 800
    
    Returns:
        str: Número formateado (800-123-4567)
    
    Examples:
        >>> format_service_800('8001234567')
        '800-123-4567'
    """
    # Limpiar
    clean = service.replace('-', '').replace(' ', '')
    
    if len(clean) == 10 and clean.startswith('800'):
        return f"{clean[0:3]}-{clean[3:6]}-{clean[6:]}"
    
    return service  # Retornar sin cambios


def format_number(number: float, decimals: int = 0) -> str:
    """
    Formatea un número con separador de miles.

    Args:
        number: Número a formatear
        decimals: Cantidad de decimales (default 0)

    Returns:
        str: Número formateado, ej. '1.000.000' o '1.234,56'

    Example:
        >>> format_number(1000000)
        '1.000.000'
        >>> format_number(1234.56, decimals=2)
        '1.234,56'
    """
    if decimals > 0:
        formatted = f'{number:,.{decimals}f}'
    else:
        formatted = f'{int(round(number)):,}'
    # Convertir separadores al estilo chileno (puntos para miles, coma para decimales)
    formatted = formatted.replace(',', '.')
    if decimals > 0:
        parts = formatted.rsplit('.', 1)
        formatted = parts[0] + ',' + parts[1] if len(parts) == 2 else formatted
    return formatted


def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """
    Trunca texto a una longitud máxima.

    Args:
        text: Texto a truncar
        max_length: Longitud máxima (default 100)
        suffix: Sufijo al truncar (default '...')

    Returns:
        str: Texto truncado con sufijo si supera max_length

    Example:
        >>> truncate_text('Hello world', max_length=5)
        'Hello...'
        >>> truncate_text('Hi', max_length=10)
        'Hi'
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + suffix


# ============================================================================
# DATE/TIME FORMATTING
# ============================================================================

def format_file_size(size_bytes: int) -> str:
    """
    Formatea tamaño de archivo.
    
    CLEAN_CODE v3.0.1: Nombre auto-documentado.
    SOLID SRP: Solo formatea tamaños.
    
    Args:
        size_bytes: Tamaño en bytes
    
    Returns:
        str: Tamaño formateado
    
    Examples:
        >>> format_file_size(1024)
        '1.0 KB'
        >>> format_file_size(1048576)
        '1.0 MB'
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    
    return f"{size_bytes:.1f} PB"


# ============================================================================
# RESUMEN FORMATTERS
# 
# Total: 8 funciones públicas + 3 helpers privados
# 
# Funciones Públicas:
#   [SUCCESS] format_phone_cl()
#   [SUCCESS] format_rut()
#   [SUCCESS] format_currency()
#   [SUCCESS] format_percentage()
#   [SUCCESS] format_service_800()
#   [SUCCESS] format_file_size()
# 
# Helpers Privados (DRY):
#   [SUCCESS] _format_number_with_dots()
#   [SUCCESS] _format_number_cl()
#   [SUCCESS] _format_number_intl()
# 
# Principios SOLID Aplicados:
#   [SUCCESS] SRP: Cada función una responsabilidad
#   [SUCCESS] DRY: Helpers privados reutilizables
#   [SUCCESS] Clean Naming: Nombres descriptivos
#   [SUCCESS] Type Hints: Todas las funciones
#   [SUCCESS] OCP: Extensible (currency puede agregar más tipos)
# ============================================================================
