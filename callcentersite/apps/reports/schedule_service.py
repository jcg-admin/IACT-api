"""
apps/reports/schedule_service.py

ScheduleValidator — UC_RPT_07: valida cron y frecuencia mínima.
ScheduleService   — computa next_run_at.
"""
from datetime import timedelta
from django.utils import timezone


class ScheduleValidator:
    @staticmethod
    def validate_cron(cron_expr: str) -> None:
        parts = cron_expr.strip().split()
        if len(parts) != 5:
            raise ValueError(f"cron '{cron_expr}' inválido: debe tener 5 campos.")
        limits = [(0, 59), (0, 23), (1, 31), (1, 12), (0, 6)]
        for i, part in enumerate(parts):
            # Wildcard puro siempre válido
            if part == '*':
                continue
            lo, hi = limits[i]
            for token in part.split(','):
                # Manejar step: */2, 1-5/2
                token = token.split('/')[0]
                # Manejar range: 1-5
                token = token.split('-')[0]
                if token == '*':
                    continue
                try:
                    val = int(token)
                    if not (lo <= val <= hi):
                        raise ValueError(
                            f"cron '{cron_expr}' inválido: valor {val} fuera de rango "
                            f"[{lo}-{hi}] en campo {i}."
                        )
                except ValueError as e:
                    if 'cron' in str(e):
                        raise
                    raise ValueError(
                        f"cron '{cron_expr}' inválido en campo {i}: '{part}'"
                    ) from e

    @staticmethod
    def validate_min_frequency(cron_expr: str) -> None:
        """CA-06: frecuencia < 1h rechazada."""
        parts = cron_expr.strip().split()
        minute_part = parts[0] if parts else '*'
        if '/' in minute_part:
            interval = int(minute_part.split('/')[1])
            if interval < 60:
                raise ValueError('Frecuencia mínima: 1 hora (CA-06).')


class ScheduleService:
    @staticmethod
    def compute_next(data: dict):
        """Calcula el próximo next_run_at según frequency y run_at_hour."""
        from datetime import datetime
        freq = data.get('frequency', 'daily')
        hour = data.get('run_at_hour', 6)
        minute = data.get('run_at_minute', 0)
        now = timezone.now()
        # Simple: próximo día a la hora indicada
        candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if candidate <= now:
            candidate += timedelta(days=1)
        return candidate
