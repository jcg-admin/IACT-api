"""
apps/reports/saved_filter_service.py

SavedFilterValidator — UC_RPT_09: valida nombre, segmento y unicidad.
"""

class SavedFilterValidator:
    @staticmethod
    def validate(payload: dict) -> None:
        name = payload.get('name', '')
        if not name or len(name) > 100:
            raise ValueError('name obligatorio y ≤ 100 chars.')

    @staticmethod
    def check_duplicate(user_id: int, name: str) -> None:
        from apps.reports.models import SavedFilter
        if SavedFilter.objects.filter(actor_id=user_id, name=name).exists():
            raise ValueError(f"Nombre duplicado: '{name}' — CA-02.")
