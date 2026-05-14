"""
apps/pipeline/pipeline_retry_service.py

PipelineRetryValidator — valida el campo reason de UC_PIP_04.
PipelineRetryIdempotency — rastrea run_ids ya reintentados (CA-05).

UC_PIP_04:
- CA-03: reason ≥ 20 caracteres
- CA-05: doble retry del mismo run_id → 409
"""
from django.core.cache import cache

MIN_REASON_LEN = 20


class PipelineRetryValidator:
    """
    UC_PIP_04 UT-01: reason ≥ 20 caracteres.
    """

    @staticmethod
    def validate_reason(reason: str) -> None:
        if not reason or len(reason) < MIN_REASON_LEN:
            raise ValueError(
                f'reason debe tener al menos {MIN_REASON_LEN} caracteres '
                f'(recibidos: {len(reason) if reason else 0}).'
            )


class PipelineRetryIdempotency:
    """
    CA-05: doble retry del mismo run_id → 409.

    Usa Django cache con TTL de 24h para registrar los run_ids ya reintentados.
    La clave es: pipeline_retry:{run_id}
    """

    _TTL = 86_400  # 24h

    @classmethod
    def _key(cls, run_id: str) -> str:
        return f'pipeline_retry:{run_id}'

    @classmethod
    def is_already_retried(cls, run_id: str) -> bool:
        return bool(cache.get(cls._key(run_id)))

    @classmethod
    def mark_retried(cls, run_id: str, new_run_id: str) -> None:
        cache.set(cls._key(run_id), new_run_id, cls._TTL)
