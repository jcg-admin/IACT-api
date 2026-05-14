"""
apps/alerts/alert_history_service.py

TimingCalculator — UC_ALR_04: calcula time-to-ack y time-to-resolve.
"""
from datetime import datetime


class TimingCalculator:
    @staticmethod
    def time_to_ack(fired_at: datetime, acked_at) -> 'int | None':
        if acked_at is None:
            return None
        return int((acked_at - fired_at).total_seconds())

    @staticmethod
    def time_to_resolve(fired_at: datetime, resolved_at) -> 'int | None':
        if resolved_at is None:
            return None
        return int((resolved_at - fired_at).total_seconds())
