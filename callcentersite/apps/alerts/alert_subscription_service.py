"""
apps/alerts/alert_subscription_service.py

SubscriptionValidator — UC_ALR_05: valida severity y detecta duplicados.
"""
VALID_SEVERITIES = {'info', 'warning', 'error', 'critical'}


class SubscriptionValidator:
    @staticmethod
    def validate(payload: dict) -> None:
        sev = payload.get('severity_filter', '')
        if sev and sev not in VALID_SEVERITIES:
            raise ValueError(f"severity_filter '{sev}' inválido. Válidos: {sorted(VALID_SEVERITIES)}")

    @staticmethod
    def check_duplicate(user_id: int, rule_id: int) -> None:
        from apps.alerts.models import AlertSubscription
        if AlertSubscription.objects.filter(
            user_id=user_id, rule_id=rule_id, state='active'
        ).exists():
            raise ValueError('duplicada: ya existe una suscripción activa para esta regla.')
