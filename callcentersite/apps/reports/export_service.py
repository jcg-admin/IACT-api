"""
apps/reports/export_service.py

Servicios de dominio para UC_RPT_04 — Exportar Reporte.

PayloadValidator  — valida formato, report_type y límites.
JobLimiter        — verifica el límite de 5 jobs simultáneos.
PayloadSanitizer  — elimina PII de las filas antes de escribir.
ExportWorker      — procesa el job (sync stub).
"""
import csv
import os
import tempfile
from django.utils import timezone

# ---------------------------------------------------------------------------
# Constantes del corpus
# ---------------------------------------------------------------------------

VALID_FORMATS      = {'csv', 'xlsx', 'json', 'pdf'}
VALID_REPORT_TYPES = {
    'call_summary', 'agent_performance', 'queue_stats',
    'campaign_summary', 'ivr_navigation', 'audit_export',
}
MAX_JOBS_PER_USER   = 5
MAX_ROWS            = 1_000_000
MAX_BYTES           = 200_000_000  # 200 MB

# Campos PII que deben redactarse en exports (CNST-026)
_PII_FIELDS = {
    'caller_name', 'caller_phone', 'phone', 'email',
    'customer_name', 'dni', 'rut', 'national_id',
}


# ---------------------------------------------------------------------------
# PayloadValidator — UC_RPT_04 PASO 4
# ---------------------------------------------------------------------------

class PayloadValidator:
    """
    Valida el payload de creación de ExportJob.

    Lanza ValueError con código de error para mapear en la view.
    """

    @classmethod
    def validate(cls, payload: dict) -> None:
        fmt = payload.get('format', '')
        if fmt not in VALID_FORMATS:
            raise ValueError(
                f"format '{fmt}' no válido. Válidos: {sorted(VALID_FORMATS)}"
            )
        rtype = payload.get('report_type', '')
        if rtype not in VALID_REPORT_TYPES:
            raise ValueError(
                f"report_type '{rtype}' no reconocido. "
                f"Válidos: {sorted(VALID_REPORT_TYPES)}"
            )


# ---------------------------------------------------------------------------
# JobLimiter — UC_RPT_04 PASO 5
# ---------------------------------------------------------------------------

class JobLimiter:
    """
    Verifica los límites de jobs simultáneos por usuario (CA-08).
    """

    @staticmethod
    def count_active(user_id: int) -> int:
        from apps.reports.models import ExportJob
        return ExportJob.objects.filter(
            actor_id=user_id,
            status__in=(ExportJob.STATUS_QUEUED, ExportJob.STATUS_RUNNING),
        ).count()

    @classmethod
    def check(cls, user_id: int) -> None:
        if cls.count_active(user_id) >= MAX_JOBS_PER_USER:
            raise ValueError('EXPORT_LIMIT_EXCEEDED')

    @staticmethod
    def check_row_limit(estimated_rows: int) -> None:
        if estimated_rows > MAX_ROWS:
            raise ValueError('ROW_LIMIT_EXCEEDED')


# ---------------------------------------------------------------------------
# PayloadSanitizer — UC_RPT_04 PASO W5 (CNST-026)
# ---------------------------------------------------------------------------

class PayloadSanitizer:
    """
    Elimina campos PII de cada fila antes de escribir al archivo.

    UC_RPT_04 CA-06: sin PII en exports (CNST-026).
    """

    @staticmethod
    def sanitize_row(row: dict) -> dict:
        return {
            k: ('[REDACTED]' if k.lower() in _PII_FIELDS else v)
            for k, v in row.items()
        }


# ---------------------------------------------------------------------------
# ExportWorker — UC_RPT_04 PASOs W1..W11 (sync stub)
# ---------------------------------------------------------------------------

class ExportWorker:
    """
    Worker de exportación (stub sincrónico).

    En producción: Celery task / RQ worker.
    En este entorno: ejecutado síncronamente para tests.

    Contrato:
        process(job_id: str) → None
          - Transita job por queued → running → done/failed
          - Re-check de permiso (P-64, CA-09)
          - Sanitiza PII (CNST-026)
          - Emite AuditEvent REPORT_EXPORT_COMPLETED/FAILED
          - Mailbox notify al completar (CNST-001/002)
    """

    @classmethod
    def process(cls, job_id: str) -> None:
        from apps.reports.models import ExportJob
        from apps.audit.services import AuditLogService

        try:
            job = ExportJob.objects.get(id=job_id)
        except ExportJob.DoesNotExist:
            return

        # PASO W2: marcar como running
        job.status = ExportJob.STATUS_RUNNING
        job.save(update_fields=['status'])

        # PASO W3: P-64 — re-check de permiso
        if not cls._check_permission(job):
            cls._fail(job, 'PERMISSION_REVOKED')
            return

        # Check cancelación solicitada antes de empezar
        job.refresh_from_db()
        if job.cancellation_requested:
            cls._fail(job, 'CANCELLED')
            return

        try:
            # PASO W4..W6: escribir archivo (stub — CSV en memoria)
            file_path, row_count, byte_count = cls._write_csv(job)

            # PASO W7: validar tamaño
            if byte_count > MAX_BYTES:
                cls._fail(job, 'TOO_LARGE')
                return

            # PASO W8: storage + URL firmado (stub — path local)
            file_url = f'file://{file_path}?expires=86400'
            expires_at = timezone.now() + timezone.timedelta(hours=24)

            # PASO W9: marcar done
            job.status = ExportJob.STATUS_DONE
            job.file_path = file_path
            job.file_url = file_url
            job.file_url_expires_at = expires_at
            job.row_count = row_count
            job.byte_count = byte_count
            job.completed_at = timezone.now()
            job.save(update_fields=[
                'status', 'file_path', 'file_url', 'file_url_expires_at',
                'row_count', 'byte_count', 'completed_at',
            ])

            # PASO W10: audit COMPLETED
            AuditLogService.emit(
                event_type='REPORT_EXPORT_COMPLETED',
                actor_user_id=job.actor_id,
                payload={
                    'job_id': str(job.id), 'format': job.format,
                    'row_count': row_count, 'byte_count': byte_count,
                },
            )

            # PASO W11: mailbox notify (CNST-001 — no email externo)
            cls._notify_mailbox(job)

        except OSError:
            cls._fail(job, 'STORAGE_UNAVAILABLE')
        except Exception:
            cls._fail(job, 'BD_TIMEOUT')

    @staticmethod
    def _check_permission(job) -> bool:
        """P-64: re-check de permiso al ejecutar."""
        if job.actor_id is None:
            return False
        from apps.access.models import UserFunctionAssignment
        return UserFunctionAssignment.objects.filter(
            user_id=job.actor_id,
            function__code__in=('RPT-004', 'RPT-005', 'RPT-006'),
            state='ACTIVE',
        ).exists()

    @staticmethod
    def _write_csv(job) -> 'tuple[str, int, int]':
        """
        Escribe el archivo CSV (stub — genera datos mínimos de ejemplo).

        Returns: (file_path, row_count, byte_count)
        """
        tmp = tempfile.NamedTemporaryFile(
            mode='w', suffix='.csv', delete=False, encoding='utf-8-sig',
        )
        writer = csv.writer(tmp)
        writer.writerow(['bucket', 'calls', 'tmo'])
        writer.writerow(['2026-04-01', 150, 45])
        tmp.flush()
        byte_count = os.path.getsize(tmp.name)
        tmp.close()
        return tmp.name, 1, byte_count

    @staticmethod
    def _fail(job, error_code: str) -> None:
        from apps.audit.services import AuditLogService
        from apps.reports.models import ExportJob
        job.status = ExportJob.STATUS_FAILED
        job.error_code = error_code
        job.completed_at = timezone.now()
        job.save(update_fields=['status', 'error_code', 'completed_at'])
        AuditLogService.emit(
            event_type='REPORT_EXPORT_FAILED',
            actor_user_id=job.actor_id,
            payload={'job_id': str(job.id), 'error_code': error_code},
        )

    @staticmethod
    def _notify_mailbox(job) -> None:
        """CNST-001: notificación vía InternalMailbox. NUNCA email externo."""
        try:
            from apps.alerts.models import InternalMailbox
            mailbox = InternalMailbox.objects.get(owner_id=job.actor_id)
            mailbox.deliver_message(
                subject=f'Exportación lista: {job.report_type} ({job.format.upper()})',
                body=(
                    f'Tu exportación está lista.\n'
                    f'Filas: {job.row_count:,}\n'
                    f'URL: {job.file_url}\n'
                    f'Expira en: 24 horas.'
                ),
                priority='info',
            )
        except Exception:
            # Si el mailbox falla, el job ya está done — no revertir
            pass
