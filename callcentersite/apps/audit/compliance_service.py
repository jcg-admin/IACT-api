"""
apps/audit/compliance_service.py

ComplianceTemplateValidator — UC_AUD_04: valida templates.
HMACSigner                  — UC_AUD_04: firma y verifica reportes.
"""
import hmac, hashlib, os

VALID_TEMPLATES = {
    'PRIVILEGED_ACCESS', 'CONFIG_CHANGES',
    'LOGIN_PATTERNS', 'SENSITIVE_DATA_ACCESS',
}
_SECRET = os.environ.get('COMPLIANCE_HMAC_SECRET', 'iact-compliance-dev-secret').encode()


class ComplianceTemplateValidator:
    @staticmethod
    def validate(template: str) -> None:
        if template not in VALID_TEMPLATES:
            raise ValueError(
                f"template '{template}' inválido. Válidos: {sorted(VALID_TEMPLATES)}"
            )


class HMACSigner:
    @staticmethod
    def sign(payload: bytes) -> str:
        return hmac.new(_SECRET, payload, hashlib.sha256).hexdigest()

    @staticmethod
    def verify(payload: bytes, signature: str) -> bool:
        expected = HMACSigner.sign(payload)
        return hmac.compare_digest(expected, signature)
