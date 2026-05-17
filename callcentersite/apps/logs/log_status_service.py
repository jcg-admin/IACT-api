"""
apps/logs/log_status_service.py

SystemStatusAggregator — UC_LOG_06: agrega status de servicios.
PercentileCalculator   — UC_LOG_07: calcula P50/P95/P99.
"""

class SystemStatusAggregator:
    _PRIORITY = {'red': 3, 'yellow': 2, 'unknown': 1, 'green': 0}

    @classmethod
    def overall(cls, services: list) -> str:
        if not services:
            return 'unknown'
        worst = max(services, key=lambda s: cls._PRIORITY.get(s.get('status', 'unknown'), 1))
        return worst.get('status', 'unknown')


class PercentileCalculator:
    @staticmethod
    def percentile(samples: list, pct: int) -> float:
        if not samples:
            return 0.0
        sorted_s = sorted(samples)
        idx = max(0, int(len(sorted_s) * pct / 100) - 1)
        return float(sorted_s[idx])
