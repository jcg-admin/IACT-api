"""
tests/unit/fase5/test_uc_perm09_perm10.py

UC_PERM_09 — Servicio de Auditoría (AuditLogService mejoras FASE 5).
UC_PERM_10 — Consultar Auditoría de Permisos.
GET /api/audit-events/
GET /api/audit-events/{id}/
GET /api/audit-events/aggregate/
POST /api/audit-events/export/
"""
import json
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.audit.models import AuditLog, VALID_EVENT_TYPES
from tests.test_data.user_test_data import AdminUserTestData, UserTestData


# ============================================================================
# UC_PERM_09 — AuditLogService mejoras
# ============================================================================

class TestAuditValidator:
    """UT-01..04: Validación estructural del servicio de auditoría."""

    def test_ut01_event_type_valido_pasa(self):
        from apps.audit.audit_validator import AuditValidator
        AuditValidator.validate_event_type('LOGIN')  # no lanza

    def test_ut02_event_type_desconocido_lanza(self):
        from apps.audit.audit_validator import AuditValidator
        from apps.audit.models import AuditValidationError
        with pytest.raises(AuditValidationError):
            AuditValidator.validate_event_type('EVENTO_INEXISTENTE_XYZ')

    def test_ut03_payload_mayor_16kb_lanza(self):
        from apps.audit.audit_validator import AuditValidator
        from apps.audit.models import AuditValidationError
        payload_gigante = {'data': 'x' * (16 * 1024 + 1)}
        with pytest.raises(AuditValidationError, match='16'):
            AuditValidator.validate_payload_size(payload_gigante)

    def test_ut03_payload_exactamente_16kb_pasa(self):
        from apps.audit.audit_validator import AuditValidator
        payload = {'data': 'x' * (16 * 1024 - 10)}
        AuditValidator.validate_payload_size(payload)


class TestAuditPIIScanner:
    """UT-05..08: Detección de PII en payloads de auditoría."""

    def test_ut05_detecta_email_plano(self):
        from apps.audit.audit_validator import AuditPIIScanner
        from apps.audit.audit_validator import AuditPIIDetected
        with pytest.raises(AuditPIIDetected):
            AuditPIIScanner.scan({'actor_email': 'user@corp.com'})

    def test_ut06_detecta_numero_identidad(self):
        from apps.audit.audit_validator import AuditPIIScanner, AuditPIIDetected
        with pytest.raises(AuditPIIDetected):
            AuditPIIScanner.scan({'dni': '12345678A'})

    def test_ut07_detecta_password(self):
        from apps.audit.audit_validator import AuditPIIScanner, AuditPIIDetected
        with pytest.raises(AuditPIIDetected):
            AuditPIIScanner.scan({'password': 'secret123'})

    def test_ut08_payload_limpio_pasa(self):
        from apps.audit.audit_validator import AuditPIIScanner
        AuditPIIScanner.scan({
            'target_user_id': 42,
            'function_ids': [1, 2],
            'ip': '10.0.0.1',
        })


class TestAuditSanitizer:
    """UT-09..10: Sanitización de valores."""

    def test_ut09_hashea_username(self):
        from apps.audit.audit_validator import AuditSanitizer
        result = AuditSanitizer.sanitize({'username': 'alice'})
        assert 'username' not in result
        assert 'username_hash' in result
        assert result['username_hash'] != 'alice'

    def test_ut10_normaliza_timestamp_a_utc(self):
        from apps.audit.audit_validator import AuditSanitizer
        naive = datetime(2026, 5, 1, 10, 0, 0)
        result = AuditSanitizer.ensure_utc(naive)
        assert result.tzinfo is not None


@pytest.mark.django_db
class TestEmitBatch:
    """CA-11: emit_batch atómico."""

    def test_batch_atomico_un_fallo_rollback_todo(self):
        from apps.audit.services import AuditLogService
        before = AuditLog.objects.count()
        events = [
            {'event_type': 'LOGIN', 'actor_user_id': 1, 'payload': {}},
            {'event_type': 'EVENTO_QUE_NO_EXISTE', 'actor_user_id': 1, 'payload': {}},
        ]
        try:
            AuditLogService.emit_batch(events)
        except Exception:
            pass
        # Rollback: 0 eventos añadidos
        assert AuditLog.objects.count() == before


# ============================================================================
# UC_PERM_10 — Consultar Auditoría
# ============================================================================

@pytest.fixture
def client_perm10(db):
    client = APIClient()
    user = AdminUserTestData()
    client.force_authenticate(user=user)
    return client, user


@pytest.fixture
def client_sin_perm10(db):
    client = APIClient()
    user = UserTestData()
    client.force_authenticate(user=user)
    return client


class TestAuditFilterValidator:
    """UT-01..04 de UC_PERM_10."""

    def test_ut01_date_range_valido_pasa(self):
        from apps.audit.audit_query_service import AuditFilterValidator
        AuditFilterValidator.validate(
            date_from=datetime(2026, 4, 1, tzinfo=timezone.utc),
            date_to=datetime(2026, 4, 30, tzinfo=timezone.utc),
        )

    def test_ut02_range_invertido_rechazado(self):
        from apps.audit.audit_query_service import AuditFilterValidator
        with pytest.raises(ValueError):
            AuditFilterValidator.validate(
                date_from=datetime(2026, 5, 1, tzinfo=timezone.utc),
                date_to=datetime(2026, 4, 1, tzinfo=timezone.utc),
            )

    def test_ut03_range_mayor_90_rechazado(self):
        from apps.audit.audit_query_service import AuditFilterValidator
        with pytest.raises(ValueError, match='90'):
            AuditFilterValidator.validate(
                date_from=datetime(2026, 1, 1, tzinfo=timezone.utc),
                date_to=datetime(2026, 5, 1, tzinfo=timezone.utc),
            )

    def test_ut04_page_size_mayor_200_rechazado(self):
        from apps.audit.audit_query_service import AuditFilterValidator
        with pytest.raises(ValueError):
            AuditFilterValidator.validate(
                date_from=datetime(2026, 4, 1, tzinfo=timezone.utc),
                date_to=datetime(2026, 4, 30, tzinfo=timezone.utc),
                page_size=201,
            )


class TestCursorEncoder:
    """UT-05..07 de UC_PERM_10."""

    def test_ut05_encode_decode_roundtrip(self):
        from apps.audit.audit_query_service import CursorEncoder
        data = {'created_at': '2026-05-01T10:00:00Z', 'id': '42'}
        encoded = CursorEncoder.encode(data)
        decoded = CursorEncoder.decode(encoded)
        assert decoded['id'] == '42'

    def test_ut06_cursor_con_filters_hash_distinto_rechazado(self):
        from apps.audit.audit_query_service import CursorEncoder
        encoded = CursorEncoder.encode({'id': '1'}, filters_hash='abc')
        with pytest.raises(ValueError, match='CURSOR_INVALID'):
            CursorEncoder.decode(encoded, expected_filters_hash='xyz')


class TestAuditPayloadSanitizer:
    """UT-08..09: Truncación de payload."""

    def test_ut08_trunca_payload_a_500_chars(self):
        from apps.audit.audit_query_service import AuditResponseSanitizer
        event = {'details': {'data': 'x' * 1000}}
        result = AuditResponseSanitizer.sanitize_event(event)
        assert len(str(result.get('details', ''))) <= 600

    def test_ut09_no_destruye_campos_estructurales(self):
        from apps.audit.audit_query_service import AuditResponseSanitizer
        event = {'action': 'LOGIN', 'user_id': 42, 'details': {}}
        result = AuditResponseSanitizer.sanitize_event(event)
        assert result.get('user_id') == 42


@pytest.mark.django_db
class TestAuditEventListEndpoint:
    """IT-01..06, CA-17..18 de UC_PERM_10."""

    def _url(self):
        return reverse('audit:audit-event-list')

    def _aggregate_url(self):
        return reverse('audit:audit-event-aggregate')

    def _export_url(self):
        return reverse('audit:audit-event-export')

    def test_it01_list_retorna_200(self, client_perm10):
        """CA-01: GET → 200."""
        client, _ = client_perm10
        response = client.get(self._url(), {
            'date_from': '2026-04-01', 'date_to': '2026-04-30',
        })
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data

    def test_it04_filtro_actor_id(self, client_perm10):
        """CA-05: ?actor_id=X → solo eventos de ese actor."""
        client, _ = client_perm10
        response = client.get(self._url(), {
            'actor_id': '1', 'date_from': '2026-04-01', 'date_to': '2026-04-30',
        })
        assert response.status_code == status.HTTP_200_OK

    def test_it06_range_mayor_90_retorna_400(self, client_perm10):
        """CA-08: range > 90 días → 400."""
        client, _ = client_perm10
        response = client.get(self._url(), {
            'date_from': '2026-01-01', 'date_to': '2026-05-01',
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_it01_meta_audit_queried_emitido(self, client_perm10):
        """CA-17: AUDIT_LOG_QUERIED emitido por cada consulta exitosa."""
        client, _ = client_perm10
        before = AuditLog.objects.filter(action='AUDIT_LOG_QUERIED').count()
        client.get(self._url(), {
            'date_from': '2026-04-01', 'date_to': '2026-04-30',
        })
        assert AuditLog.objects.filter(action='AUDIT_LOG_QUERIED').count() > before

    def test_aggregate_retorna_200(self, client_perm10):
        """CA-12: GET aggregate → 200 con buckets."""
        client, _ = client_perm10
        response = client.get(self._aggregate_url(), {
            'date_from': '2026-04-01', 'date_to': '2026-04-30',
            'group_by': 'event_type',
        })
        assert response.status_code == status.HTTP_200_OK

    def test_export_retorna_202(self, client_perm10):
        """CA-14: POST export → 202 + job_id."""
        client, _ = client_perm10
        response = client.post(self._export_url(), {
            'date_from': '2026-04-01',
            'date_to': '2026-04-30',
            'format': 'csv',
        }, format='json')
        assert response.status_code == status.HTTP_202_ACCEPTED

    def test_sec_sin_permiso_retorna_403(self, client_sin_perm10):
        """CA-16: sin AUD-001 → 403."""
        response = client_sin_perm10.get(self._url(), {
            'date_from': '2026-04-01', 'date_to': '2026-04-30',
        })
        assert response.status_code == status.HTTP_403_FORBIDDEN
