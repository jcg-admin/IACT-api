"""
apps/audit/audit_query_service.py

AuditFilterValidator  — UC_PERM_10: valida filtros de consulta de auditoría.
CursorEncoder         — UC_PERM_10: codifica/decodifica cursores de paginación.
AuditResponseSanitizer — UC_PERM_10: trunca payload y elimina PII residual.
"""
import base64
import json
from datetime import datetime

MAX_RANGE_DAYS = 90
MAX_PAGE_SIZE  = 200


class AuditFilterValidator:
    @classmethod
    def validate(cls, date_from: datetime, date_to: datetime,
                 page_size: int = 50) -> None:
        if date_to <= date_from:
            raise ValueError('date_from debe ser anterior a date_to.')
        if (date_to - date_from).days > MAX_RANGE_DAYS:
            raise ValueError(
                f'Rango máximo {MAX_RANGE_DAYS} días para consulta online (CA-08). '
                'Use export para rangos mayores.'
            )
        if page_size > MAX_PAGE_SIZE:
            raise ValueError(f'page_size máximo: {MAX_PAGE_SIZE}.')


class CursorEncoder:
    @staticmethod
    def encode(data: dict, filters_hash: str = '') -> str:
        payload = {'data': data, 'fh': filters_hash}
        return base64.urlsafe_b64encode(
            json.dumps(payload).encode()
        ).decode()

    @staticmethod
    def decode(cursor: str, expected_filters_hash: str = '') -> dict:
        try:
            payload = json.loads(base64.urlsafe_b64decode(cursor.encode()))
        except Exception as e:
            raise ValueError('CURSOR_INVALID: cursor malformado.') from e
        if expected_filters_hash and payload.get('fh') != expected_filters_hash:
            raise ValueError('CURSOR_INVALID: filtros distintos al cursor.')
        return payload['data']


class AuditResponseSanitizer:
    MAX_PAYLOAD_SNIPPET = 500

    @classmethod
    def sanitize_event(cls, event: dict) -> dict:
        """Trunca el payload a snippet y elimina PII residual."""
        result = dict(event)
        details = result.get('details') or result.get('payload') or {}
        if details:
            snippet = str(details)[:cls.MAX_PAYLOAD_SNIPPET]
            result['details'] = snippet + ('…' if len(str(details)) > cls.MAX_PAYLOAD_SNIPPET else '')
        return result
