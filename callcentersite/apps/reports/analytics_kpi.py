"""
apps/reports/analytics_kpi.py

Calculadores de KPI para UC_RPT_12..17.
CNST-007: read-only Analytics.
CNST-026: sin PII en responses.
"""
import hashlib
from collections import Counter


class AgentKPICalculator:
    @staticmethod
    def tmo(row: dict):
        answered = row.get('answered_calls', 0)
        return (row.get('sum_handle_time', 0) // answered) if answered else None

    @staticmethod
    def occupancy(row: dict) -> float:
        total = row.get('total_time', 0)
        return round((row.get('busy_time', 0) / total * 100), 2) if total else 0.0


class QueueKPICalculator:
    @staticmethod
    def asa(row: dict):
        answered = row.get('answered', 0)
        return (row.get('sum_wait', 0) // answered) if answered else None

    @staticmethod
    def service_level(row: dict) -> float:
        total = row.get('total_calls', 0)
        return round((row.get('within_threshold', 0) / total * 100), 2) if total else 0.0

    @staticmethod
    def abandon_rate(row: dict) -> float:
        total = row.get('total_calls', 0)
        return round((row.get('abandoned', 0) / total * 100), 2) if total else 0.0


class CampaignKPICalculator:
    @staticmethod
    def conversion_rate(row: dict) -> float:
        total = row.get('total_calls', 0)
        return round((row.get('converted', 0) / total * 100), 2) if total else 0.0


class DistinctClientCounter:
    @staticmethod
    def exact(ids: list) -> int:
        return len(set(ids))

    @staticmethod
    def top_n_anonymized(ids: list, n: int = 10) -> list:
        """CA-05 + CA-06: Top N con sólo prefix del hash (no client_id raw)."""
        counts = Counter(ids)
        return [
            {'id_prefix': hashlib.sha256(cid.encode()).hexdigest()[:8], 'count': cnt}
            for cid, cnt in counts.most_common(n)
        ]
