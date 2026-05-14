"""
apps/pipeline/pii_scanner.py

PIIScanner — Sanitización de PII en stack traces y mensajes de error.

UC_PIP_02 CA-03: stack_trace_sanitized sin PII.
CNST-026: payloads sin PII detectable.
"""
import re

_EMAIL_RE  = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
_PASS_RE   = re.compile(r"(password|passwd|pwd|secret|token)[\s]*[=:]['\"](.*?)['\"]",
                         re.IGNORECASE)
_PASS_STR  = re.compile(r"(password|passwd|pwd|secret|token)=\S+", re.IGNORECASE)


class PIIScanner:
    """
    Sanitizador de PII para respuestas de UC_PIP_02.

    Elimina emails y credenciales de stack traces antes de retornar al cliente.
    """

    @staticmethod
    def sanitize(text: str) -> str:
        """
        Redacta PII detectable en un string.

        - Emails: reemplazados por [EMAIL-REDACTED]
        - Passwords/secrets en key=value: reemplazados por [REDACTED]
        """
        if not text:
            return text
        result = _EMAIL_RE.sub('[EMAIL-REDACTED]', text)
        result = _PASS_RE.sub(r"\1='[REDACTED]'", result)
        result = _PASS_STR.sub(r'\1=[REDACTED]', result)
        return result

    @classmethod
    def sanitize_error_row(cls, row: dict) -> dict:
        """Aplica sanitize a todos los campos de texto de una fila de error ETL."""
        sanitized = {}
        for k, v in row.items():
            sanitized[k] = cls.sanitize(str(v)) if isinstance(v, str) else v
        return sanitized
