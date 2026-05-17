"""
apps/audit/audit_validator.py

AuditValidator   — UC_PERM_09: validación estructural de eventos.
AuditPIIScanner  — UC_PERM_09: detección de PII en payloads.
AuditPIIDetected — excepción levantada al detectar PII.
AuditSanitizer   — UC_PERM_09: sanitización de valores (hash username, UTC).
"""
import hashlib
import json
import re
from datetime import datetime, timezone

from apps.audit.models import AuditValidationError

MAX_PAYLOAD_BYTES = 16 * 1024  # 16 KB (CA-04)

_EMAIL_RE    = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
_PHONE_RE    = re.compile(r'\b\d{7,15}\b')
_DNI_RE      = re.compile(r'\b\d{7,9}[A-Z]?\b')
_PII_KEYS    = frozenset({'email', 'phone', 'dni', 'rut', 'password', 'passwd',
                          'secret', 'token', 'national_id'})


class AuditPIIDetected(Exception):
    """CA-05: payload contiene PII detectado — emisión bloqueada."""
    pass


class AuditValidator:
    """UC_PERM_09 CA-03/04: validación estructural."""

    @staticmethod
    def validate_event_type(event_type: str) -> None:
        from apps.audit.models import VALID_EVENT_TYPES
        if event_type not in VALID_EVENT_TYPES:
            raise AuditValidationError(
                f"event_type desconocido: {event_type!r}."
            )

    @staticmethod
    def validate_payload_size(payload: dict) -> None:
        serialized = json.dumps(payload, default=str).encode('utf-8')
        if len(serialized) > MAX_PAYLOAD_BYTES:
            raise AuditValidationError(
                f'payload excede {MAX_PAYLOAD_BYTES // 1024} KB '
                f'(recibido: {len(serialized)} bytes) — CA-04.'
            )


class AuditPIIScanner:
    """UC_PERM_09 CA-05/06: detección de PII — bloquea emisión si detecta."""

    @classmethod
    def scan(cls, payload: dict) -> None:
        for key, value in payload.items():
            if key.lower() in _PII_KEYS:
                raise AuditPIIDetected(
                    f"PII detectado en campo '{key}' — CA-05 UC_PERM_09."
                )
            if isinstance(value, str):
                if _EMAIL_RE.search(value):
                    raise AuditPIIDetected(
                        f"Email detectado en campo '{key}' — CA-05."
                    )
            if isinstance(value, dict):
                cls.scan(value)


class AuditSanitizer:
    """UC_PERM_09 CA-06: hashea username, normaliza timestamps a UTC."""

    @staticmethod
    def sanitize(payload: dict) -> dict:
        """Reemplaza 'username' por 'username_hash' (CA-06)."""
        result = {}
        for k, v in payload.items():
            if k.lower() == 'username' and isinstance(v, str):
                result['username_hash'] = hashlib.sha256(v.encode()).hexdigest()[:16]
            else:
                result[k] = v
        return result

    @staticmethod
    def ensure_utc(dt: datetime) -> datetime:
        """CA-15: normaliza timestamps naive a UTC."""
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
