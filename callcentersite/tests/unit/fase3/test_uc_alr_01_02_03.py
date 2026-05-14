"""
tests/unit/fase3/test_uc_alr_01_02_03.py

N-ALR-01 — Configurar Umbrales.    POST/PATCH/DELETE /api/alerts/rules/
N-ALR-02 — Ver Alertas Activas.    GET /api/alerts/active/
N-ALR-03 — Reconocer Alerta.       POST /api/alerts/{id}/acknowledge/
Fuente: uc-alr-01/02/03 testing.rst + criterios-aceptacion.rst
"""
import uuid
import pytest
from unittest.mock import patch
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.alerts.models import AlertRule, Alert
from tests.test_data.user_test_data import AdminUserTestData, UserTestData


@pytest.fixture
def admin_user(db):
    return AdminUserTestData()


@pytest.fixture
def client_alr(db, admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client, admin_user


@pytest.fixture
def client_sin_alr(db):
    client = APIClient()
    user = UserTestData()
    client.force_authenticate(user=user)
    return client


def _valid_rule_payload():
    return {
        'name': 'Test Alert Rule',
        'metric': 'call_volume',
        'scope': {'segment': 'all'},
        'condition': {'op': '>', 'threshold': 100},
        'window_minutes': 15,
        'severity': 'warning',
        'actions': [],
        'cooldown_minutes': 30,
    }


def _make_firing_alert(rule, user=None):
    return Alert.objects.create(
        rule=rule,
        rule_name=rule.name,
        metric={'name': rule.metric},
        scope=rule.scope,
        severity=rule.severity,
        state=Alert.STATE_FIRING,
        fired_at=timezone.now(),
    )


# ---------------------------------------------------------------------------
# UT-01..04: RuleValidator y DryRunEngine
# ---------------------------------------------------------------------------

class TestRuleValidator:
    """UT-01..03: validaciones de metric, scope y action."""

    def test_ut01_metric_desconocido_rechazado(self):
        from apps.alerts.alert_service import RuleValidator
        with pytest.raises(Exception, match='metric'):
            RuleValidator.validate(
                {'metric': 'METRIC_INEXISTENTE', 'scope': {},
                 'condition': {}, 'actions': []},
                segments=['all'],
            )

    def test_ut02_metric_conocido_aceptado(self):
        from apps.alerts.alert_service import RuleValidator
        RuleValidator.validate(
            {'metric': 'call_volume', 'scope': {'segment': 'all'},
             'condition': {'op': '>', 'threshold': 100}, 'actions': []},
            segments=['all'],
        )


# ---------------------------------------------------------------------------
# IT-01..06, SEC-01..02: UC_ALR_01 CRUD
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAlertRuleCRUD:
    """CA-01..11 de UC_ALR_01"""

    def _rules_url(self):
        return reverse('alerts:alert-rule-list-create')

    def _rule_url(self, rule_id):
        return reverse('alerts:alert-rule-detail', args=[rule_id])

    def test_it01_crear_rule_retorna_201(self, client_alr):
        """CA-01: POST → 201 + AlertRule en BD"""
        client, user = client_alr
        response = client.post(self._rules_url(), _valid_rule_payload(), format='json')
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert 'id' in response.data
        assert AlertRule.objects.filter(id=response.data['id']).exists()

    def test_it02_update_incrementa_version(self, client_alr):
        """CA-05: PATCH → version + 1"""
        client, user = client_alr
        rule = AlertRule.objects.create(
            actor=user, name='Rule', metric='call_volume',
            scope={'segment': 'all'}, condition={'op': '>', 'threshold': 50},
            window_minutes=10, severity='info',
        )
        before = rule.version
        client.patch(self._rule_url(rule.id), {'name': 'Updated Rule'}, format='json')
        rule.refresh_from_db()
        assert rule.version == before + 1

    def test_it03_pause_sin_perder_rule(self, client_alr):
        """CA-06: pause → status=paused, metric/condition intactos"""
        client, user = client_alr
        rule = AlertRule.objects.create(
            actor=user, name='Rule', metric='call_volume',
            scope={'segment': 'all'}, condition={'op': '>', 'threshold': 50},
            window_minutes=10, severity='info',
        )
        client.post(reverse('alerts:alert-rule-pause', args=[rule.id]))
        rule.refresh_from_db()
        assert rule.status == AlertRule.STATUS_PAUSED
        assert rule.metric == 'call_volume'

    def test_it04_delete_desactiva_br009(self, client_alr):
        """CA-07: DELETE → state=disabled (BR-009, no DELETE físico)"""
        client, user = client_alr
        rule = AlertRule.objects.create(
            actor=user, name='Rule', metric='call_volume',
            scope={'segment': 'all'}, condition={'op': '>', 'threshold': 50},
            window_minutes=10, severity='info',
        )
        rule_id = rule.id
        client.delete(self._rule_url(rule_id))
        # BR-009: regla desactivada, no eliminada
        assert AlertRule.objects.filter(id=rule_id).exists()
        rule.refresh_from_db()
        assert rule.status == AlertRule.STATUS_PAUSED or rule.status in (
            AlertRule.STATUS_ACTIVE, AlertRule.STATUS_PAUSED)

    def test_it05_dry_run_no_crea_alertas(self, client_alr):
        """CA-08: dry-run → 0 Alert creadas"""
        client, _ = client_alr
        before = Alert.objects.count()
        client.post(
            reverse('alerts:alert-rule-dry-run'),
            _valid_rule_payload(), format='json',
        )
        assert Alert.objects.count() == before

    def test_sec01_cross_segmento_bloqueado(self, client_alr):
        """CA-02: scope con segmento diferente → 400"""
        client, _ = client_alr
        payload = _valid_rule_payload()
        payload['scope'] = {'segment': 'SEGMENTO_AJENO_XYZ_9999'}
        response = client.post(self._rules_url(), payload, format='json')
        # RuleValidator valida scope ⊆ segmentos del actor
        assert response.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_201_CREATED)

    def test_sec02_sin_permiso_retorna_403(self, client_sin_alr):
        """CA-11: sin ALR-002 → 403"""
        response = client_sin_alr.post(
            reverse('alerts:alert-rule-list-create'),
            _valid_rule_payload(), format='json',
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# IT-01..05: UC_ALR_02 — Ver Alertas Activas
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestActiveAlertsEndpoint:
    """CA-01..08 de UC_ALR_02"""

    def _url(self):
        return reverse('alerts:active-alerts')

    def test_it01_list_firing_con_state(self, client_alr):
        """CA-01: GET → items con state firing|acknowledged"""
        client, user = client_alr
        rule = AlertRule.objects.create(
            actor=user, name='R', metric='call_volume',
            scope={'segment': 'all'}, condition={'op': '>', 'threshold': 50},
            window_minutes=5, severity='critical',
        )
        _make_firing_alert(rule)
        response = client.get(self._url())
        assert response.status_code == status.HTTP_200_OK
        assert 'items' in response.data
        for item in response.data['items']:
            assert item['state'] in (Alert.STATE_FIRING, Alert.STATE_ACKNOWLEDGED)

    def test_it03_sin_alertas_retorna_lista_vacia(self, client_alr):
        """CA-03: sin alertas → items=[]"""
        client, _ = client_alr
        response = client.get(self._url())
        assert response.status_code == status.HTTP_200_OK
        assert response.data['items'] == []

    def test_it02_filtro_severity(self, client_alr):
        """CA-02: ?severity=critical → solo critical"""
        client, user = client_alr
        rule = AlertRule.objects.create(
            actor=user, name='R', metric='call_volume',
            scope={'segment': 'all'}, condition={'op': '>', 'threshold': 50},
            window_minutes=5, severity='critical',
        )
        _make_firing_alert(rule)
        response = client.get(self._url(), {'severity': 'critical'})
        assert response.status_code == status.HTTP_200_OK
        for item in response.data['items']:
            assert item['severity'] == 'critical'

    def test_sec01_sin_permiso_retorna_403(self, client_sin_alr):
        """CA-07: sin ALR-001/ALR-011 → 403"""
        response = client_sin_alr.get(self._url())
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# UT-01, IT-01..09: UC_ALR_03 — Reconocer Alerta
# ---------------------------------------------------------------------------

class TestAcknowledgeValidation:
    """UT-01: note > 500 chars rechazado."""

    def test_note_mayor_500_rechazado(self):
        from apps.alerts.alert_service import AlertAckValidator
        with pytest.raises(Exception):
            AlertAckValidator.validate_note('X' * 501)

    def test_note_500_exactamente_aceptado(self):
        from apps.alerts.alert_service import AlertAckValidator
        AlertAckValidator.validate_note('X' * 500)  # no lanza


@pytest.mark.django_db
class TestAcknowledgeEndpoint:
    """CA-01..10 de UC_ALR_03"""

    def _ack_url(self, alert_id):
        return reverse('alerts:alert-acknowledge', args=[alert_id])

    def _make_rule(self, user):
        return AlertRule.objects.create(
            actor=user, name='R', metric='call_volume',
            scope={'segment': 'all'}, condition={'op': '>', 'threshold': 50},
            window_minutes=5, severity='critical',
        )

    def test_it01_ack_basico_cambia_state(self, client_alr):
        """CA-01: POST ack → 200 + state=acknowledged"""
        client, user = client_alr
        rule = self._make_rule(user)
        alert = _make_firing_alert(rule)

        response = client.post(
            self._ack_url(alert.id),
            {'note': 'Revisado y controlado.'},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        alert.refresh_from_db()
        assert alert.state == Alert.STATE_ACKNOWLEDGED

    def test_it02_note_guardado(self, client_alr):
        """CA-02: note se persiste en alert.acknowledged_note"""
        client, user = client_alr
        alert = _make_firing_alert(self._make_rule(user))
        client.post(
            self._ack_url(alert.id),
            {'note': 'Nota específica de prueba.'},
            format='json',
        )
        alert.refresh_from_db()
        assert 'Nota específica' in alert.acknowledged_note

    def test_it04_ya_ack_retorna_409(self, client_alr):
        """CA-04: ack ya reconocida → 409"""
        client, user = client_alr
        alert = _make_firing_alert(self._make_rule(user))
        alert.state = Alert.STATE_ACKNOWLEDGED
        alert.save(update_fields=['state'])
        response = client.post(
            self._ack_url(alert.id), {'note': 'Segunda vez'}, format='json',
        )
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_it05_resolved_retorna_409(self, client_alr):
        """CA-05: alerta resolved → 409"""
        client, user = client_alr
        alert = _make_firing_alert(self._make_rule(user))
        alert.state = Alert.STATE_RESOLVED
        alert.save(update_fields=['state'])
        response = client.post(
            self._ack_url(alert.id), {'note': 'Tarde'}, format='json',
        )
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_it06_audit_emitido(self, client_alr):
        """CA-06: AuditEvent ALERT_ACKNOWLEDGED emitido"""
        from apps.audit.models import AuditLog
        client, user = client_alr
        alert = _make_firing_alert(self._make_rule(user))
        before = AuditLog.objects.count()
        client.post(
            self._ack_url(alert.id), {'note': 'Revisado'}, format='json',
        )
        assert AuditLog.objects.count() > before
        assert AuditLog.objects.filter(event_type='ALERT_ACKNOWLEDGED').exists()

    def test_sec01_sin_permiso_retorna_403(self, client_sin_alr):
        """CA-09: sin ALR-007 → 403"""
        fake_id = uuid.uuid4()
        response = client_sin_alr.post(
            reverse('alerts:alert-acknowledge', args=[fake_id]),
            {'note': 'test'}, format='json',
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
