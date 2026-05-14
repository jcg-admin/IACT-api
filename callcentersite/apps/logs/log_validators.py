"""
apps/logs/log_validators.py

LogRangeValidator y LogPIIScanner para UC_LOG_01/02.

UC_LOG_01 CA-04: range > 24h rechazado.
UC_LOG_01 CA-05: PII sanitizado antes de retornar.
CNST-026: sin PII en responses.
"""
import re
from datetime import timedelta

_EMAIL_RE = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
_PASS_RE  = re.compile(r"(password|passwd|pwd|secret|token)=\S+", re.IGNORECASE)


class LogRangeValidator:
    """
    UC_LOG_01 EX-03: range > 24h → 400.

    El rango de consulta ad-hoc está limitado a 24 horas.
    Rangos mayores se gestionan via UC_LOG_04 export.
    """

    MAX_HOURS = 24

    @classmethod
    def validate(cls, from_dt, to_dt):
        if to_dt - from_dt > timedelta(hours=cls.MAX_HOURS):
            raise ValueError(
                f'El rango de consulta no puede exceder {cls.MAX_HOURS} horas. '
                'Para rangos mayores use UC_LOG_04 export.'
            )


class LogPIIScanner:
    """
    Sanitizador de PII para log entries.

    UC_LOG_01 CA-05: response sin PII.
    """

    @staticmethod
    def sanitize_text(text: str) -> str:
        if not text:
            return text
        result = _EMAIL_RE.sub('[EMAIL-REDACTED]', text)
        result = _PASS_RE.sub(r'\1=[REDACTED]', result)
        return result

    @classmethod
    def sanitize_entry(cls, entry: dict) -> dict:
        """Sanitiza message y context de un log entry."""
        result = dict(entry)
        if 'message' in result and isinstance(result['message'], str):
            result['message'] = cls.sanitize_text(result['message'])
        if 'context' in result and isinstance(result['context'], dict):
            ctx = {}
            for k, v in result['context'].items():
                if k.lower() in ('password', 'passwd', 'secret', 'token', 'pwd'):
                    ctx[k] = '[REDACTED]'
                elif isinstance(v, str):
                    ctx[k] = cls.sanitize_text(v)
                else:
                    ctx[k] = v
            result['context'] = ctx
        return result
