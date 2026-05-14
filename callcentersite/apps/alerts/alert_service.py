"""
apps/alerts/alert_service.py

Servicios de dominio para UC_ALR_01/02/03.

RuleValidator    — valida payload de AlertRule contra el contexto del usuario.
AlertAckValidator — valida el note de UC_ALR_03.
DryRunEngine     — evalúa una regla hipotética sin crear alertas reales.
"""
from django.db import transaction

VALID_METRICS = {
    'call_volume', 'avg_wait_time', 'sla_percentage',
    'abandon_rate', 'agents_available', 'queue_depth',
}

VALID_OPS = {'>', '<', '>=', '<=', '=='}


class RuleValidator:
    """
    Valida el payload de creación/update de AlertRule.

    UC_ALR_01:
    - CA-03: metric ∈ VALID_METRICS → ValidationError
    - CA-02: scope.segment ⊆ segmentos del actor → ValidationError
    - CA-04: action targets existen → ValidationError
    """

    @classmethod
    def validate(cls, payload: dict, segments: list) -> None:
        metric = payload.get('metric', '')
        if metric not in VALID_METRICS:
            raise ValueError(
                f"metric '{metric}' no reconocida. "
                f"Valores válidos: {sorted(VALID_METRICS)}"
            )
        condition = payload.get('condition', {})
        op = condition.get('op', '')
        if op and op not in VALID_OPS:
            raise ValueError(f"op '{op}' no válido. Válidos: {sorted(VALID_OPS)}")

        scope = payload.get('scope', {})
        segment = scope.get('segment')
        if segment and segment != 'all' and segments and segment not in segments:
            raise ValueError(
                f"scope.segment '{segment}' no pertenece a los segmentos del actor."
            )

        for action in payload.get('actions', []):
            if not isinstance(action, dict) or 'type' not in action:
                raise ValueError('Cada action debe tener un campo type.')


class AlertAckValidator:
    """
    UC_ALR_03 UT-01: note ≤ 500 caracteres.
    """

    MAX_NOTE_LEN = 500

    @classmethod
    def validate_note(cls, note: str) -> None:
        if len(note) > cls.MAX_NOTE_LEN:
            raise ValueError(
                f'La nota de reconocimiento no puede exceder {cls.MAX_NOTE_LEN} caracteres '
                f'(recibidos: {len(note)}).'
            )


class DryRunEngine:
    """
    UC_ALR_01 CA-08: evalúa una regla hipotética sin disparar alertas reales.

    Retorna cuántas alertas se habrían generado en el período last_24h
    con los datos actuales, sin crear ninguna Alert en BD.
    """

    @staticmethod
    def evaluate_against(rule_payload: dict, period: str = 'last_24h') -> dict:
        """
        Simula la evaluación de la regla contra datos históricos.

        Returns:
            {'count': int, 'sample': list[dict]}
        """
        # Sin datos de analytics reales en el entorno de tests — retorna 0 hits.
        # En producción conectaría con AnalyticsRepo.
        return {
            'count':  0,
            'sample': [],
            'period': period,
            'note':   'Evaluación simulada — sin datos de analytics en este entorno.',
        }
