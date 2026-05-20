"""
apps/reports/export_views.py

UC_RPT_04 — Exportar Reporte (patrón Larman async).

ExportView       — POST /api/reports/export/       → 202 + job_id
                   GET  /api/reports/export/       → lista jobs del usuario
ExportDetailView — GET    /api/reports/export/{id}/ → status + progress_pct
                   DELETE /api/reports/export/{id}/ → cancelled / graceful

CNST-010: permission_classes explícito en cada view.
CNST-001: notificación vía InternalMailbox (no email externo).
"""
from drf_spectacular.utils import (
    extend_schema, extend_schema_view, OpenApiResponse,
)
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access.permissions.function_permissions import HasFunction
from apps.audit.services import AuditLogService
from apps.reports.export_service import (
    JobLimiter, PayloadValidator,
)
from apps.reports.models import ExportJob
from apps.reports.serializers.export_serializers import ExportJobSerializer


_TAG = 'Reportes'


# ---------------------------------------------------------------------------
# Serializers de request/response
# ---------------------------------------------------------------------------

class ExportJobCreateSerializer(serializers.Serializer):
    report_type = serializers.CharField(max_length=50)
    format      = serializers.ChoiceField(choices=['csv', 'xlsx', 'json', 'pdf'])
    filters     = serializers.DictField(default=dict)
    period      = serializers.DictField(default=dict)
    group_by    = serializers.ListField(child=serializers.CharField(), default=list)


def _job_to_dict(job: ExportJob) -> dict:
    return {
        'id':                  str(job.id),
        'report_type':         job.report_type,
        'format':              job.format,
        'status':              job.status,
        'progress_pct':        job.progress_pct,
        'file_url':            job.file_url,
        'file_url_expires_at': (
            job.file_url_expires_at.isoformat() if job.file_url_expires_at else None
        ),
        'row_count':           job.row_count,
        'byte_count':          job.byte_count,
        'error_code':          job.error_code,
        'created_at':          job.created_at.isoformat(),
        'completed_at': (
            job.completed_at.isoformat() if job.completed_at else None
        ),
    }


# ---------------------------------------------------------------------------
# ExportView — POST / GET  /api/reports/export/
# ---------------------------------------------------------------------------

@extend_schema_view(
    get=extend_schema(
        operation_id='reports_export_list',
        summary='UC_RPT_04 — Listar jobs de exportación del usuario',
        tags=[_TAG],
    ),
    post=extend_schema(
        operation_id='reports_export_queue',
        summary='UC_RPT_04 — Encolar exportación de reporte',
        description=(
            'Encola el job y retorna 202 + job_id. '
            'CNST-001: notificación vía mailbox interno al completar.'
        ),
        responses={
            202: OpenApiResponse(description='Job encolado — body: {job_id}'),
            400: OpenApiResponse(description='Validación fallida (format/report_type/ROW_LIMIT)'),
            429: OpenApiResponse(description='EXPORT_LIMIT_EXCEEDED — > 5 jobs activos'),
            403: OpenApiResponse(description='Sin RPT-004/005/006'),
        },
        tags=[_TAG],
    ),
)
class ExportView(APIView):
    serializer_class = ExportJobSerializer
    """POST/GET /api/reports/export/ — UC_RPT_04"""

    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'RPT-004'   # export_csv (más permisivo; RPT-005/006 para otros formatos)

    def post(self, request):
        ser = ExportJobCreateSerializer(data=request.data)
        if not ser.is_valid():
            return Response({'error': 'VALIDATION_ERROR', 'fields': ser.errors}, status=400)

        data = ser.validated_data

        # PASO 4: validar payload
        try:
            PayloadValidator.validate(data)
        except ValueError as e:
            code = str(e).split()[0] if str(e).isupper() else 'VALIDATION_ERROR'
            return Response({'error': code, 'detail': str(e)}, status=400)

        # PASO 4: estimación de filas (stub — sin BD Analytics real)
        # En prod: AnalyticsRepo.estimate(data['filters'], data['period'])
        estimated_rows = 0
        try:
            JobLimiter.check_row_limit(estimated_rows)
        except ValueError:
            return Response({'error': 'ROW_LIMIT_EXCEEDED'}, status=400)

        # PASO 5: límite de jobs simultáneos
        try:
            JobLimiter.check(request.user.pk)
        except ValueError:
            return Response({'error': 'EXPORT_LIMIT_EXCEEDED'}, status=429)

        # PASO 6: crear ExportJob
        job = ExportJob.objects.create(
            actor=request.user,
            report_type=data['report_type'],
            format=data['format'],
            filters=data.get('filters', {}),
            period=data.get('period', {}),
            group_by=data.get('group_by', []),
            status=ExportJob.STATUS_QUEUED,
        )

        # PASO 8: audit QUEUED (CNST-025 + FR-035.02)
        xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
        ip_admin = (xff.split(',')[0].strip() if xff
                    else request.META.get('REMOTE_ADDR', '')) or None
        AuditLogService.emit(
            event_type='REPORT_EXPORT_QUEUED',
            actor_user_id=request.user.pk,
            target_entity_type='ExportJob',
            target_entity_id=str(job.id),
            ip_address=ip_admin,
            payload={
                'job_id': str(job.id),
                'report_type': job.report_type,
                'format': job.format,
            },
        )

        # PASO 7: encolar worker (sync en este entorno — en prod: Celery)
        # En producción: ExportWorker.delay(str(job.id))
        # Aquí NO ejecutamos síncronamente para no bloquear el request

        return Response({'job_id': str(job.id)}, status=202)

    def get(self, request):
        """Lista los jobs de exportación del usuario autenticado."""
        qs = ExportJob.objects.filter(actor=request.user).order_by('-created_at')[:20]
        return Response({
            'count': qs.count(),
            'results': [_job_to_dict(j) for j in qs],
        })


# ---------------------------------------------------------------------------
# ExportDetailView — GET / DELETE  /api/reports/export/{id}/
# ---------------------------------------------------------------------------

@extend_schema_view(
    get=extend_schema(
        operation_id='reports_export_retrieve',
        summary='UC_RPT_04 CA-18 — Estado del job de exportación',
        responses={200: OpenApiResponse(description='status, progress_pct, file_url')},
        tags=[_TAG],
    ),
    delete=extend_schema(
        operation_id='reports_export_cancel',
        summary='UC_RPT_04 CA-17 — Cancelar job de exportación',
        responses={
            200: OpenApiResponse(description='Cancelado (queued) o cancellation_requested (running)'),
            409: OpenApiResponse(description='No cancelable en estado actual'),
        },
        tags=[_TAG],
    ),
)
class ExportDetailView(APIView):
    """GET/DELETE /api/reports/export/{id}/ — UC_RPT_04 CA-17/18"""

    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'RPT-004'

    def _get_job(self, job_id, user):
        try:
            return ExportJob.objects.get(id=job_id, actor=user)
        except (ExportJob.DoesNotExist, ValueError):
            return None

    def get(self, request, job_id):
        """CA-18: GET → status + progress_pct"""
        job = self._get_job(job_id, request.user)
        if not job:
            return Response({'error': 'JOB_NOT_FOUND'}, status=404)
        return Response(_job_to_dict(job))

    def delete(self, request, job_id):
        """
        CA-17: Cancelar job.
        - queued → status=cancelled (inmediato)
        - running → cancellation_requested=True (graceful tras batch)
        """
        job = self._get_job(job_id, request.user)
        if not job:
            return Response({'error': 'JOB_NOT_FOUND'}, status=404)

        if job.status == ExportJob.STATUS_QUEUED:
            job.status = ExportJob.STATUS_CANCELLED
            job.save(update_fields=['status'])
            return Response({'id': str(job.id), 'status': job.status})

        if job.status == ExportJob.STATUS_RUNNING:
            job.cancellation_requested = True
            job.save(update_fields=['cancellation_requested'])
            return Response(
                {'id': str(job.id), 'status': job.status,
                 'cancellation_requested': True},
                status=202,
            )

        return Response(
            {'error': 'INVALID_STATE',
             'detail': f'Job en estado {job.status} no puede cancelarse.'},
            status=409,
        )
