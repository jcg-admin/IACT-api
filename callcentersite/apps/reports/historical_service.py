"""
apps/reports/historical_service.py

Servicios de dominio para UC_RPT_03 — Ver Reportes Históricos.

PeriodResolver      — calcula período actual y período anterior para comparativo.
FilterValidator     — valida parámetros de filtro (range, group_by, page_size).
ComparativeBuilder  — construye el comparativo current vs prior.
ttl_for_period      — TTL adaptativo según el período (PASO 10 del flujo).
HistoricalReportService — servicio principal de UC_RPT_03.
"""
from datetime import datetime, timezone, timedelta


# ---------------------------------------------------------------------------
# PeriodResolver
# ---------------------------------------------------------------------------

_PERIOD_DAYS = {
    'last_24h': 1,
    'last_7d':  7,
    'last_30d': 30,
    'last_90d': 90,
}


class PeriodResolver:
    """
    Calcula el período actual y el período anterior para el comparativo.

    UC_RPT_03 UT-01..02.
    """

    @staticmethod
    def prior(preset: str) -> dict:
        """
        Retorna el período anterior al preset dado.

        'last_30d' → 30 días que terminan 30 días antes de hoy.
        """
        days = _PERIOD_DAYS.get(preset, 30)
        now = datetime.now(timezone.utc)
        end   = now - timedelta(days=days)
        start = end - timedelta(days=days)
        return {'start': start, 'end': end, 'days': days}

    @staticmethod
    def prior_from_range(start: datetime, end: datetime) -> dict:
        """
        Retorna el período anterior de la misma duración que (start, end).

        UT-02: prior_from_range tiene el mismo length que el rango dado.
        """
        duration = end - start
        prior_end   = start
        prior_start = start - duration
        return {'start': prior_start, 'end': prior_end, 'days': duration.days}


# ---------------------------------------------------------------------------
# FilterValidator
# ---------------------------------------------------------------------------

_GROUP_BY_MAX_DAYS = {
    'hour':   7,
    'day':    730,
    'week':   730,
    'month':  730,
}

MAX_RANGE_DAYS  = 730   # 2 años
MAX_PAGE_SIZE   = 200


class FilterValidator:
    """
    UC_RPT_03 UT-05..06: valida filtros de consulta.

    Lanza ValueError con código de error para mapear en la view.
    """

    @classmethod
    def validate(cls, period_days: int = 30,
                 group_by: 'list | None' = None,
                 page_size: int = 50) -> None:
        if period_days > MAX_RANGE_DAYS:
            raise ValueError('RANGE_TOO_LARGE')

        if group_by:
            for dim in group_by:
                max_days = _GROUP_BY_MAX_DAYS.get(dim, MAX_RANGE_DAYS)
                if period_days > max_days:
                    raise ValueError(
                        f'group_by={dim} no compatible con rango de {period_days} días '
                        f'(máx {max_days} días).'
                    )

        if page_size > MAX_PAGE_SIZE:
            raise ValueError(f'page_size máximo es {MAX_PAGE_SIZE}.')


# ---------------------------------------------------------------------------
# ComparativeBuilder
# ---------------------------------------------------------------------------

class ComparativeBuilder:
    """
    UC_RPT_03 UT-03..04: construye el comparativo current vs prior.
    """

    @staticmethod
    def build(current_total: float, prior_total: 'float | None') -> dict:
        if prior_total is None or prior_total == 0:
            return {
                'diff_pct': None,
                'diff_abs': None,
                'insufficient_data': True,
            }
        diff_abs = current_total - prior_total
        diff_pct = (diff_abs / prior_total) * 100
        return {
            'diff_pct': round(diff_pct, 2),
            'diff_abs': diff_abs,
            'insufficient_data': False,
        }


# ---------------------------------------------------------------------------
# TTL adaptativo
# ---------------------------------------------------------------------------

def ttl_for_period(period: str) -> int:
    """
    UC_RPT_03 PASO 10: TTL adaptativo según el período consultado.

    last_24h → 60s, last_7d → 300s, last_30d/90d/custom → 900s
    """
    mapping = {
        'last_24h': 60,
        'last_7d':  300,
        'last_30d': 900,
        'last_90d': 900,
    }
    return mapping.get(period, 900)


# ---------------------------------------------------------------------------
# HistoricalReportService
# ---------------------------------------------------------------------------

class HistoricalReportService:
    """
    UC_RPT_03 — Servicio principal.

    CNST-007: read-only sobre Analytics.
    CNST-008: filtro de segmento aplicado.
    P-62: TTL adaptativo.
    P-63: comparative auto-derived.
    """

    def get(self, filters: dict, period: str, group_by: list,
            page: int, invoker) -> dict:
        """
        Retorna el reporte histórico con buckets y comparativo.

        En este entorno no hay BD Analytics real — retorna datos stub.
        En producción: AnalyticsRepo.aggregate(...) con conexión real.
        """
        # Validar período
        period_days = _PERIOD_DAYS.get(period, 30)
        if 'date_from' in filters and 'date_to' in filters:
            try:
                from_dt = datetime.fromisoformat(filters['date_from'])
                to_dt   = datetime.fromisoformat(filters['date_to'])
                period_days = (to_dt - from_dt).days
            except (ValueError, TypeError):
                raise ValueError('VALIDATION_ERROR')

        FilterValidator.validate(period_days=period_days, group_by=group_by)

        comparative = ComparativeBuilder.build(
            current_total=0, prior_total=None,
        )

        return {
            'period': period,
            'group_by': group_by,
            'filters_applied': filters,
            'buckets': [],
            'pagination': {'page': page, 'page_size': 50, 'has_next': False},
            'comparative': comparative,
            'cache': False,
        }
