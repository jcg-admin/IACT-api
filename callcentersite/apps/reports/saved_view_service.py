"""
apps/reports/saved_view_service.py

SavedViewValidator — UC_RPT_10: valida nombre, columnas y segmento.
"""

VALID_COLUMNS = {
    'call_summary': {'date', 'calls', 'tmo', 'asa', 'abandon_rate', 'service_level'},
    'agent_performance': {'date', 'agent_id', 'calls', 'tmo', 'occupancy'},
    'queue_stats': {'date', 'queue_id', 'calls', 'asa', 'service_level'},
}


class SavedViewValidator:
    @staticmethod
    def validate(payload: dict) -> None:
        name = payload.get('name', '')
        if not name or len(name) > 100:
            raise ValueError('name obligatorio y ≤ 100 chars.')
        report_type = payload.get('report_type', '')
        columns = payload.get('columns', [])
        valid_cols = VALID_COLUMNS.get(report_type, set())
        if valid_cols:
            for col in columns:
                if col not in valid_cols:
                    raise ValueError(
                        f"columna '{col}' no válida para report_type '{report_type}'. "
                        f"Válidas: {sorted(valid_cols)}"
                    )
