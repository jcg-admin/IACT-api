"""
apps/pipeline/status_calculator.py

StatusCalculator — Calcula el status de frescura de un dataset ETL.

UC_PIP_03: status ∈ {fresco, aceptable, vencido, sin_datos}
Thresholds: < 14h → fresco, < 24h → aceptable, >= 24h → vencido.
"""
from datetime import datetime, timezone

_FRESH_HOURS    = 14
_STALE_HOURS    = 24


class StatusCalculator:
    """
    Calcula el status de frescura de un dataset ETL.

    UC_PIP_03 CA-02..04:
      lag < 14h  → 'fresco'
      14h ≤ lag < 24h → 'aceptable'
      lag >= 24h → 'vencido'
      sin carga  → 'sin_datos'
    """

    @staticmethod
    def compute(ultima_carga: 'datetime | None') -> str:
        if ultima_carga is None:
            return 'sin_datos'
        now = datetime.now(timezone.utc)
        if ultima_carga.tzinfo is None:
            ultima_carga = ultima_carga.replace(tzinfo=timezone.utc)
        lag_hours = (now - ultima_carga).total_seconds() / 3600
        if lag_hours < _FRESH_HOURS:
            return 'fresco'
        if lag_hours < _STALE_HOURS:
            return 'aceptable'
        return 'vencido'

    @staticmethod
    def lag_minutes(ultima_carga: 'datetime | None') -> 'int | None':
        if ultima_carga is None:
            return None
        now = datetime.now(timezone.utc)
        if ultima_carga.tzinfo is None:
            ultima_carga = ultima_carga.replace(tzinfo=timezone.utc)
        return int((now - ultima_carga).total_seconds() / 60)
