"""
apps/logs/log_export_views.py

UC_LOG_04 — Exportar Logs (async).
POST/GET /api/logs/export/
"""
import uuid
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access.permissions.function_permissions import HasFunction
from apps.audit.services import AuditLogService

_TAG = 'Logs'

VALID_LOG_TYPES = {'application', 'etl', 'infrastructure', 'security'}
VALID_FORMATS   = {'csv', 'json', 'txt'}


class LogExportSerializer(serializers.Serializer):
    log_type        = serializers.ChoiceField(choices=list(VALID_LOG_TYPES))
    date_from       = serializers.DateField()
    date_to         = serializers.DateField()
    format          = serializers.ChoiceField(choices=list(VALID_FORMATS), default='csv')
    include_archive = serializers.BooleanField(default=False)


@extend_schema_view(
    post=extend_schema(
        operation_id='logs_export_queue',
        summary='UC_LOG_04 — Encolar exportación de logs',
        responses={
            202: OpenApiResponse(description='Job encolado — {job_id}'),
            400: OpenApiResponse(description='ROW_LIMIT_EXCEEDED'),
            403: OpenApiResponse(description='Sin LOG-002 export_logs'),
        },
        tags=[_TAG],
    ),
    get=extend_schema(
        operation_id='logs_export_list',
        summary='UC_LOG_04 — Listar jobs de exportación de logs',
        tags=[_TAG],
    ),
)
class LogExportView(APIView):
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'LOG-002'

    def post(self, request):
        ser = LogExportSerializer(data=request.data)
        if not ser.is_valid():
            return Response({'error': 'VALIDATION_ERROR', 'fields': ser.errors}, status=400)

        job_id = str(uuid.uuid4())

        AuditLogService.emit(
            event_type='LOG_EXPORT_QUEUED',
            actor_user_id=request.user.pk,
            payload={
                'job_id':    job_id,
                'log_type':  ser.validated_data['log_type'],
                'date_from': str(ser.validated_data['date_from']),
                'date_to':   str(ser.validated_data['date_to']),
            },
        )

        return Response({'job_id': job_id}, status=202)

    def get(self, request):
        return Response({'count': 0, 'results': []})


@extend_schema(
    operation_id='logs_infra_list',
    summary='UC_LOG_05 — Ver logs de infraestructura',
    tags=[_TAG],
)
class InfraLogView(APIView):
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'LOG-005'   # view_infrastructure_logs

    def get(self, request):
        host = request.query_params.get('host')
        from django.db import connections, OperationalError
        try:
            with connections['ivr'].cursor() as cur:
                if host:
                    cur.execute(
                        "SELECT id, host, message, level, created_at "
                        "FROM infra_logs WHERE host=%s ORDER BY created_at DESC LIMIT 500",
                        (host,),
                    )
                else:
                    cur.execute(
                        "SELECT id, host, message, level, created_at "
                        "FROM infra_logs ORDER BY created_at DESC LIMIT 500"
                    )
                if cur.description:
                    cols = [d[0] for d in cur.description]
                    entries = [dict(zip(cols, row)) for row in cur.fetchall()]
                else:
                    entries = []
        except OperationalError as e:
            return Response({'error': 'SERVICE_UNAVAILABLE', 'detail': str(e)}, status=503)

        return Response({'source': 'infrastructure', 'entries': entries})
