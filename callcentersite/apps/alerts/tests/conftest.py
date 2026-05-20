"""
conftest.py para tests de apps.alerts.

Fixtures compartidas para evitar la duplicacion de
``Module.objects.get_or_create(code='MOD_Alerts', ...)`` que
aparecia en 3 setUp distintos del test_viewsets.py
(InternalMessageViewSetTest, AlertConfigurationViewSetTest,
AlertSubscriptionViewSetTest). Refactor aplicado por la
iniciativa ``dedupe-fixtures-alerts-iact-api``.
"""
import pytest

from apps.access.models import Module


@pytest.fixture
def module_alerts(db):
    """Crea o retorna el Module canonico para apps.alerts."""
    module, _ = Module.objects.get_or_create(
        code='MOD_Alerts',
        defaults={'name': 'Alertas'}
    )
    return module
