"""
Date utilities para apps/utils/.

CLEAN_CODE v3.0.1: Funciones auto-documentadas.
SOLID: SRP, DRY, OCP.
"""

from datetime import datetime, date, timedelta
from typing import Tuple, Optional
import pytz


# ============================================================================
# QUARTER UTILITIES
# ============================================================================

def get_quarter_from_date(dt: date) -> int:
    """
    Obtiene trimestre desde fecha.
    
    CLEAN_CODE v3.0.1: Nombre que revela intención.
    SOLID SRP: Solo calcula trimestre.
    
    Args:
        dt: Fecha
    
    Returns:
        int: Trimestre (1-4)
    
    Examples:
        >>> from datetime import date
        >>> get_quarter_from_date(date(2025, 3, 15))
        1
        >>> get_quarter_from_date(date(2025, 7, 1))
        3
    """
    return (dt.month - 1) // 3 + 1


def get_quarter_date_range(year: int, quarter: int) -> Tuple[date, date]:
    """
    Obtiene rango de fechas de un trimestre.
    
    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID SRP: Solo calcula rango.
    
    Args:
        year: Año
        quarter: Trimestre (1-4)
    
    Returns:
        Tuple[date, date]: (fecha_inicio, fecha_fin)
    
    Raises:
        ValueError: Si quarter no es 1-4
    
    Examples:
        >>> get_quarter_date_range(2025, 1)
        (date(2025, 1, 1), date(2025, 3, 31))
        >>> get_quarter_date_range(2025, 4)
        (date(2025, 10, 1), date(2025, 12, 31))
    """
    if quarter not in [1, 2, 3, 4]:
        raise ValueError("Quarter must be 1-4")
    
    # DRY: Mapeo centralizado
    quarter_months = _get_quarter_months_mapping()
    
    start_month, end_month = quarter_months[quarter]
    
    # Fecha inicio: primer día del mes inicial
    start_date = date(year, start_month, 1)
    
    # Fecha fin: último día del mes final
    end_date = _get_last_day_of_month(year, end_month)
    
    return start_date, end_date


def _get_quarter_months_mapping() -> dict:
    """
    Mapeo trimestre -> meses.
    
    SOLID SRP: Solo provee mapeo.
    DRY: Reutilizable, centralizado.
    
    Returns:
        dict: {trimestre: (mes_inicio, mes_fin)}
    """
    return {
        1: (1, 3),
        2: (4, 6),
        3: (7, 9),
        4: (10, 12)
    }


def _get_last_day_of_month(year: int, month: int) -> date:
    """
    Obtiene último día del mes.
    
    SOLID SRP: Solo calcula último día.
    DRY: Reutilizable.
    
    Args:
        year: Año
        month: Mes
    
    Returns:
        date: Último día del mes
    """
    if month == 12:
        return date(year, 12, 31)
    else:
        # Primer día del siguiente mes - 1 día
        next_month_first = date(year, month + 1, 1)
        return next_month_first - timedelta(days=1)


# ============================================================================
# DATE FORMATTING
# ============================================================================

def format_datetime_cl(dt: datetime, include_time: bool = True) -> str:
    """
    Formatea datetime estilo chileno.
    
    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID SRP: Solo formatea datetime.
    
    Args:
        dt: Datetime
        include_time: Incluir hora
    
    Returns:
        str: Datetime formateado
    
    Examples:
        >>> from datetime import datetime
        >>> dt = datetime(2025, 3, 15, 14, 30, 45)
        >>> format_datetime_cl(dt)
        '15/03/2025 14:30:45'
        >>> format_datetime_cl(dt, include_time=False)
        '15/03/2025'
    """
    if include_time:
        return dt.strftime('%d/%m/%Y %H:%M:%S')
    else:
        return dt.strftime('%d/%m/%Y')


def format_date_cl(dt: date) -> str:
    """
    Formatea date estilo chileno.
    
    CLEAN_CODE v3.0.1: Nombre auto-documentado.
    SOLID SRP: Solo formatea date.
    
    Args:
        dt: Date
    
    Returns:
        str: Date formateado (dd/mm/yyyy)
    
    Examples:
        >>> from datetime import date
        >>> format_date_cl(date(2025, 3, 15))
        '15/03/2025'
    """
    return dt.strftime('%d/%m/%Y')


# ============================================================================
# DATE PARSING
# ============================================================================

def parse_date_flexible(date_str: str) -> Optional[date]:
    """
    Parsea fecha con múltiples formatos.
    
    CLEAN_CODE v3.0.1: Nombre que revela intención.
    SOLID SRP: Solo parsea fechas.
    SOLID OCP: Extensible agregando más formatos.
    
    Soporta:
    - dd/mm/yyyy
    - yyyy-mm-dd
    - dd-mm-yyyy
    - yyyymmdd
    
    Args:
        date_str: String fecha
    
    Returns:
        date: Fecha parseada o None si falla
    
    Examples:
        >>> parse_date_flexible('15/03/2025')
        date(2025, 3, 15)
        >>> parse_date_flexible('2025-03-15')
        date(2025, 3, 15)
        >>> parse_date_flexible('invalid')
        None
    """
    # DRY: Formatos centralizados
    formats = _get_date_formats()
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    
    return None


def _get_date_formats() -> list:
    """
    Formatos de fecha soportados.
    
    SOLID SRP: Solo provee formatos.
    SOLID OCP: Fácil agregar más formatos.
    DRY: Centralizado, reutilizable.
    
    Returns:
        list: Formatos strptime
    """
    return [
        '%d/%m/%Y',      # 15/03/2025
        '%Y-%m-%d',      # 2025-03-15
        '%d-%m-%Y',      # 15-03-2025
        '%Y%m%d',        # 20250315
        '%d/%m/%y',      # 15/03/25
        '%d.%m.%Y',      # 15.03.2025
    ]


# ============================================================================
# DATE CALCULATIONS
# ============================================================================

def get_date_range_days(start_date: date, end_date: date) -> int:
    """
    Calcula días entre fechas.
    
    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID SRP: Solo calcula diferencia.
    
    Args:
        start_date: Fecha inicio
        end_date: Fecha fin
    
    Returns:
        int: Días de diferencia
    
    Examples:
        >>> from datetime import date
        >>> get_date_range_days(date(2025, 1, 1), date(2025, 1, 31))
        30
    """
    return (end_date - start_date).days


def add_business_days(start_date: date, days: int) -> date:
    """
    Suma días hábiles (lunes-viernes).
    
    CLEAN_CODE v3.0.1: Nombre que revela intención.
    SOLID SRP: Solo suma días hábiles.
    
    Args:
        start_date: Fecha inicio
        days: Días hábiles a sumar
    
    Returns:
        date: Fecha resultante
    
    Examples:
        >>> from datetime import date
        >>> add_business_days(date(2025, 3, 14), 1)  # Viernes
        date(2025, 3, 17)  # Lunes siguiente
    """
    current = start_date
    days_added = 0
    
    while days_added < days:
        current += timedelta(days=1)
        # Saltar fines de semana (5=Sábado, 6=Domingo)
        if current.weekday() < 5:
            days_added += 1
    
    return current


def is_business_day(dt: date) -> bool:
    """
    Verifica si es día hábil.
    
    CLEAN_CODE v3.0.1: Nombre auto-documentado.
    SOLID SRP: Solo verifica día hábil.
    
    Args:
        dt: Fecha
    
    Returns:
        bool: True si es lunes-viernes
    
    Examples:
        >>> from datetime import date
        >>> is_business_day(date(2025, 3, 14))  # Viernes
        True
        >>> is_business_day(date(2025, 3, 15))  # Sábado
        False
    """
    return dt.weekday() < 5


# ============================================================================
# TIMEZONE UTILITIES
# ============================================================================

def convert_to_cl_timezone(dt: datetime) -> datetime:
    """
    Convierte datetime a timezone chileno.
    
    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID SRP: Solo convierte timezone.
    
    Args:
        dt: Datetime (puede ser naive o aware)
    
    Returns:
        datetime: Datetime en timezone Chile
    
    Examples:
        >>> from datetime import datetime
        >>> import pytz
        >>> dt_utc = datetime(2025, 3, 15, 12, 0, 0, tzinfo=pytz.UTC)
        >>> convert_to_cl_timezone(dt_utc)
        datetime.datetime(2025, 3, 15, 9, 0, 0, tzinfo=...)
    """
    cl_tz = pytz.timezone('America/Santiago')
    
    # Si es naive, asumimos UTC
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    
    return dt.astimezone(cl_tz)


def get_current_datetime_cl() -> datetime:
    """
    Obtiene datetime actual en timezone Chile.
    
    CLEAN_CODE v3.0.1: Nombre que revela intención.
    SOLID SRP: Solo obtiene datetime actual CL.
    
    Returns:
        datetime: Datetime actual Chile
    
    Examples:
        >>> dt = get_current_datetime_cl()
        >>> dt.tzinfo.zone
        'America/Santiago'
    """
    cl_tz = pytz.timezone('America/Santiago')
    return datetime.now(cl_tz)


# ============================================================================
# DATE RANGE GENERATION
# ============================================================================

def generate_date_range(
    start_date: date,
    end_date: date,
    step_days: int = 1
) -> list:
    """
    Genera lista de fechas en rango.
    
    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID SRP: Solo genera rango.
    
    Args:
        start_date: Fecha inicio
        end_date: Fecha fin
        step_days: Paso en días
    
    Returns:
        list: Lista de fechas
    
    Examples:
        >>> from datetime import date
        >>> dates = generate_date_range(date(2025, 1, 1), date(2025, 1, 5))
        >>> len(dates)
        5
    """
    dates = []
    current = start_date
    
    while current <= end_date:
        dates.append(current)
        current += timedelta(days=step_days)
    
    return dates


# ============================================================================
# RESUMEN DATE_UTILS
# 
# Total: 13 funciones públicas + 3 helpers privados
# 
# Funciones Públicas:
#   [SUCCESS] get_quarter_from_date()
#   [SUCCESS] get_quarter_date_range()
#   [SUCCESS] format_datetime_cl()
#   [SUCCESS] format_date_cl()
#   [SUCCESS] parse_date_flexible()
#   [SUCCESS] get_date_range_days()
#   [SUCCESS] add_business_days()
#   [SUCCESS] is_business_day()
#   [SUCCESS] convert_to_cl_timezone()
#   [SUCCESS] get_current_datetime_cl()
#   [SUCCESS] generate_date_range()
# 
# Helpers Privados (DRY):
#   [SUCCESS] _get_quarter_months_mapping()
#   [SUCCESS] _get_last_day_of_month()
#   [SUCCESS] _get_date_formats()
# 
# Principios SOLID Aplicados:
#   [SUCCESS] SRP: Cada función una responsabilidad
#   [SUCCESS] DRY: Helpers privados centralizados
#   [SUCCESS] OCP: parse_date_flexible extensible
#   [SUCCESS] Clean Naming: Nombres descriptivos
#   [SUCCESS] Type Hints: Todas las funciones
# ============================================================================
