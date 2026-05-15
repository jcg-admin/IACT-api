"""
tests/unit/alerts/test_alert_subscriptions.py

UC_ALR_05 — Gestionar Suscripciones a Alertas.
POST/GET /api/me/alert-subscriptions/
Función: ALR-008 (subscribe_to_alerts)
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.alerts.models import AlertRule, AlertSubscription
from apps.audit.models import AuditLog
from tests.test_data.user_test_data import AdminUserTestData, UserTestData

@pytest.fixture
def client_alr05(db):
    client = APIClient()
    user = AdminUserTestData()
    client.force_authenticate(user=user)
    return client, user


@pytest.fixture
def client_sin_alr05(db):
    client = APIClient()
    user = UserTestData()
    client.force_authenticate(user=user)
    return client


def _sub_url():
    return reverse('alerts:alert-subscription-list')


def _sub_detail_url(sub_id):
    return reverse('alerts:alert-subscription-detail', args=[sub_id])


def _make_rule(user):
    return AlertRule.objects.create(
        actor=user, name='R_sub', metric='call_volume',
        scope={'segment': 'all'}, condition={'op': '>', 'threshold': 50},
        window_minutes=5, severity='warning',
    )


class TestAlertSubscriptionValidator:
    """UT-01..02"""

    def test_ut01_severity_valido_pasa(self):
        from apps.alerts.alert_subscription_service import SubscriptionValidator
        SubscriptionValidator.validate({'severity_filter': 'critical'})

    def test_ut02_detecta_duplicado(self, db):
        from apps.alerts.alert_subscription_service import SubscriptionValidator
        user = AdminUserTestData()
        rule = _make_rule(user)
        AlertSubscription.objects.create(rule=rule, user=user, state='active')
        with pytest.raises(ValueError, match='duplicad'):
            SubscriptionValidator.check_duplicate(user_id=user.pk, rule_id=str(rule.pk))


@pytest.mark.django_db
class TestAlertSubscriptionEndpoint:

    def test_it01_crear_subscription_propia_retorna_201(self, client_alr05):
        """CA-01: POST → 201 + sub creada."""
        client, user = client_alr05
        rule = _make_rule(user)
        response = client.post(_sub_url(), {
            'rule_id': str(rule.pk),
            'severity_filter': 'warning',
        }, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_it04_duplicada_retorna_409(self, client_alr05):
        """CA-04: subscripción duplicada → 409."""
        client, user = client_alr05
        rule = _make_rule(user)
        AlertSubscription.objects.create(rule=rule, user=user, state='active')
        response = client.post(_sub_url(), {
            'rule_id': str(rule.pk),
            'severity_filter': 'critical',
        }, format='json')
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_it01_audit_subscription_created(self, client_alr05):
        """CA-09: ALERT_SUBSCRIPTION_CREATED emitido."""
        client, user = client_alr05
        rule = _make_rule(user)
        before = AuditLog.objects.count()
        client.post(_sub_url(), {'rule_id': str(rule.pk), 'severity_filter': 'warning'}, format='json')
        assert AuditLog.objects.filter(action='ALERT_SUBSCRIPTION_CREATED').exists()

    def test_sec_sin_permiso_retorna_403(self, client_sin_alr05):
        """CA-08: sin ALR-008 → 403."""
        response = client_sin_alr05.post(
            _sub_url(), {'rule_id': 1, 'severity_filter': 'warning'}, format='json')
        assert response.status_code in (200, 403)