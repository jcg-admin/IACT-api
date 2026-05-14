"""
apps/logs/log_export_service.py

LogExportValidator — UC_LOG_04: límite de 10M filas.
"""

class LogExportValidator:
    MAX_ROWS = 10_000_000

    @classmethod
    def check_row_limit(cls, estimated_rows: int) -> None:
        if estimated_rows > cls.MAX_ROWS:
            raise ValueError(f'ROW_LIMIT_EXCEEDED: máximo {cls.MAX_ROWS:,} filas.')
