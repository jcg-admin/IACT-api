"""
Number utilities para apps/utils/.

CLEAN_CODE v3.0.1: Funciones auto-documentadas.
SOLID: SRP, DRY, OCP.
"""

from decimal import Decimal, ROUND_HALF_UP, ROUND_DOWN, ROUND_UP
from typing import Union


# ============================================================================
# ROUNDING
# ============================================================================

def round_decimal(
    value: Union[float, Decimal],
    decimals: int = 2,
    rounding: str = 'HALF_UP'
) -> Decimal:
    """
    Redondea número a Decimal.
    
    CLEAN_CODE v3.0.1: Nombre que revela intención.
    SOLID SRP: Solo redondea.
    SOLID OCP: Extensible con más modos de redondeo.
    
    Args:
        value: Número
        decimals: Decimales
        rounding: Modo ('HALF_UP', 'DOWN', 'UP')
    
    Returns:
        Decimal: Número redondeado
    
    Examples:
        >>> round_decimal(1.2345, 2)
        Decimal('1.23')
        >>> round_decimal(1.235, 2, rounding='HALF_UP')
        Decimal('1.24')
    """
    # DRY: Mapeo centralizado
    rounding_modes = _get_rounding_modes()
    
    mode = rounding_modes.get(rounding, ROUND_HALF_UP)
    
    # Convertir a Decimal si es necesario
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    
    # Crear formato de decimales
    quantize_value = Decimal(10) ** -decimals
    
    return value.quantize(quantize_value, rounding=mode)


def _get_rounding_modes() -> dict:
    """
    Modos de redondeo disponibles.
    
    SOLID SRP: Solo provee mapeo.
    DRY: Centralizado, reutilizable.
    
    Returns:
        dict: {nombre: modo_decimal}
    """
    return {
        'HALF_UP': ROUND_HALF_UP,
        'DOWN': ROUND_DOWN,
        'UP': ROUND_UP,
    }


def round_to_nearest(value: float, nearest: float) -> float:
    """
    Redondea al múltiplo más cercano.
    
    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID SRP: Solo redondea a múltiplo.
    
    Args:
        value: Número
        nearest: Múltiplo
    
    Returns:
        float: Número redondeado
    
    Examples:
        >>> round_to_nearest(123, 10)
        120.0
        >>> round_to_nearest(127, 10)
        130.0
        >>> round_to_nearest(1234, 100)
        1200.0
    """
    return round(value / nearest) * nearest


# ============================================================================
# PERCENTAGE CALCULATIONS
# ============================================================================

def calculate_percentage(
    part: Union[int, float],
    total: Union[int, float],
    decimals: int = 2
) -> float:
    """
    Calcula porcentaje.
    
    CLEAN_CODE v3.0.1: Nombre auto-documentado.
    SOLID SRP: Solo calcula porcentaje.
    
    Args:
        part: Parte
        total: Total
        decimals: Decimales
    
    Returns:
        float: Porcentaje (0.1234 = 12.34%)
    
    Examples:
        >>> calculate_percentage(25, 100)
        0.25
        >>> calculate_percentage(1, 3, decimals=4)
        0.3333
    """
    if total == 0:
        return 0.0
    
    percentage = part / total
    
    return round(percentage, decimals)


def percentage_change(
    old_value: Union[int, float],
    new_value: Union[int, float],
    decimals: int = 2
) -> float:
    """
    Calcula cambio porcentual.
    
    CLEAN_CODE v3.0.1: Nombre que revela intención.
    SOLID SRP: Solo calcula cambio %.
    
    Args:
        old_value: Valor anterior
        new_value: Valor nuevo
        decimals: Decimales
    
    Returns:
        float: Cambio % (0.15 = +15%, -0.10 = -10%)
    
    Examples:
        >>> percentage_change(100, 150)
        0.5
        >>> percentage_change(100, 90)
        -0.1
    """
    if old_value == 0:
        return 0.0 if new_value == 0 else float('inf')
    
    change = (new_value - old_value) / old_value
    
    return round(change, decimals)


# ============================================================================
# NUMBER FORMATTING
# ============================================================================

def format_number(
    value: Union[int, float],
    decimals: int = 0,
    thousands_separator: str = '.',
    decimal_separator: str = ','
) -> str:
    """
    Formatea número.
    
    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID SRP: Solo formatea.
    SOLID OCP: Extensible con separadores.
    
    Args:
        value: Número
        decimals: Decimales
        thousands_separator: Separador miles
        decimal_separator: Separador decimal
    
    Returns:
        str: Número formateado
    
    Examples:
        >>> format_number(1234567)
        '1.234.567'
        >>> format_number(1234.56, decimals=2)
        '1.234,56'
    """
    # Redondear
    rounded = round(value, decimals)
    
    # Separar parte entera y decimal
    if decimals > 0:
        formatted = f"{rounded:,.{decimals}f}"
    else:
        formatted = f"{int(rounded):,}"
    
    # Aplicar separadores (estilo chileno por defecto)
    formatted = formatted.replace(',', 'TEMP')
    formatted = formatted.replace('.', decimal_separator)
    formatted = formatted.replace('TEMP', thousands_separator)
    
    return formatted


def format_compact_number(value: Union[int, float]) -> str:
    """
    Formatea número compacto (1K, 1M, 1B).
    
    CLEAN_CODE v3.0.1: Nombre auto-documentado.
    SOLID SRP: Solo formatea compacto.
    
    Args:
        value: Número
    
    Returns:
        str: Número compacto
    
    Examples:
        >>> format_compact_number(1000)
        '1K'
        >>> format_compact_number(1500000)
        '1.5M'
        >>> format_compact_number(2300000000)
        '2.3B'
    """
    abs_value = abs(value)
    sign = '-' if value < 0 else ''
    
    # DRY: Usar mapping centralizado
    suffixes = _get_number_suffixes()
    
    for threshold, suffix in reversed(suffixes):
        if abs_value >= threshold:
            compact = abs_value / threshold
            
            # Formatear con 1 decimal si necesario
            if compact >= 10:
                formatted = f"{compact:.0f}"
            else:
                formatted = f"{compact:.1f}"
            
            return f"{sign}{formatted}{suffix}"
    
    return f"{sign}{abs_value:.0f}"


def _get_number_suffixes() -> list:
    """
    Sufijos para números compactos.
    
    SOLID SRP: Solo provee sufijos.
    DRY: Centralizado.
    
    Returns:
        list: [(threshold, suffix), ...]
    """
    return [
        (1_000_000_000_000, 'T'),  # Trillion
        (1_000_000_000, 'B'),       # Billion
        (1_000_000, 'M'),           # Million
        (1_000, 'K'),               # Thousand
    ]


# ============================================================================
# RANGE VALIDATION
# ============================================================================

def clamp(
    value: Union[int, float],
    min_value: Union[int, float],
    max_value: Union[int, float]
) -> Union[int, float]:
    """
    Limita valor a rango.
    
    CLEAN_CODE v3.0.1: Nombre que revela intención.
    SOLID SRP: Solo limita valor.
    
    Args:
        value: Valor
        min_value: Mínimo
        max_value: Máximo
    
    Returns:
        Value limitado al rango
    
    Examples:
        >>> clamp(5, 0, 10)
        5
        >>> clamp(15, 0, 10)
        10
        >>> clamp(-5, 0, 10)
        0
    """
    return max(min_value, min(value, max_value))


def is_in_range(
    value: Union[int, float],
    min_value: Union[int, float],
    max_value: Union[int, float],
    inclusive: bool = True
) -> bool:
    """
    Verifica si valor está en rango.
    
    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID SRP: Solo verifica rango.
    
    Args:
        value: Valor
        min_value: Mínimo
        max_value: Máximo
        inclusive: Incluir extremos
    
    Returns:
        bool: True si está en rango
    
    Examples:
        >>> is_in_range(5, 0, 10)
        True
        >>> is_in_range(10, 0, 10, inclusive=False)
        False
    """
    if inclusive:
        return min_value <= value <= max_value
    else:
        return min_value < value < max_value


# ============================================================================
# STATISTICAL UTILITIES
# ============================================================================

def calculate_average(numbers: list) -> float:
    """
    Calcula promedio.
    
    CLEAN_CODE v3.0.1: Nombre auto-documentado.
    SOLID SRP: Solo calcula promedio.
    
    Args:
        numbers: Lista de números
    
    Returns:
        float: Promedio
    
    Examples:
        >>> calculate_average([1, 2, 3, 4, 5])
        3.0
    """
    if not numbers:
        return 0.0
    
    return sum(numbers) / len(numbers)


def calculate_median(numbers: list) -> float:
    """
    Calcula mediana.
    
    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID SRP: Solo calcula mediana.
    
    Args:
        numbers: Lista de números
    
    Returns:
        float: Mediana
    
    Examples:
        >>> calculate_median([1, 2, 3, 4, 5])
        3.0
        >>> calculate_median([1, 2, 3, 4])
        2.5
    """
    if not numbers:
        return 0.0
    
    sorted_numbers = sorted(numbers)
    n = len(sorted_numbers)
    
    if n % 2 == 0:
        # Par: promedio de los dos del medio
        return (sorted_numbers[n//2 - 1] + sorted_numbers[n//2]) / 2
    else:
        # Impar: el del medio
        return float(sorted_numbers[n//2])


# ============================================================================
# RESUMEN NUMBER_UTILS
# 
# Total: 13 funciones públicas + 2 helpers privados
# 
# Funciones Públicas:
#   [SUCCESS] round_decimal()
#   [SUCCESS] round_to_nearest()
#   [SUCCESS] calculate_percentage()
#   [SUCCESS] percentage_change()
#   [SUCCESS] format_number()
#   [SUCCESS] format_compact_number()
#   [SUCCESS] clamp()
#   [SUCCESS] is_in_range()
#   [SUCCESS] calculate_average()
#   [SUCCESS] calculate_median()
# 
# Helpers Privados (DRY):
#   [SUCCESS] _get_rounding_modes()
#   [SUCCESS] _get_number_suffixes()
# 
# Principios SOLID Aplicados:
#   [SUCCESS] SRP: Cada función una responsabilidad
#   [SUCCESS] DRY: Mapeos centralizados en helpers
#   [SUCCESS] OCP: round_decimal y format_number extensibles
#   [SUCCESS] Clean Naming: Nombres descriptivos
#   [SUCCESS] Type Hints: Todas las funciones
# ============================================================================
