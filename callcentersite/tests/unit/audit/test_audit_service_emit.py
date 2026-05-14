"""
tests/unit/audit/test_audit_service_emit.py

UC_PERM_09 — Servicio de Auditoría (AuditLogService).
AuditValidator, AuditPIIScanner, AuditSanitizer, emit_batch atómico.
"""
import json
import pytest
from datetime import datetime, timezone

from apps.audit.models import AuditLog, VALID_EVENT_TYPES
from tests.test_data.user_test_data import AdminUserTestData

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