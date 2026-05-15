"""
apps/pipeline/pipeline_event_views.py

UC_PIP_02 extension — Eventos recientes del pipeline via v_eventos_recientes.

GET /api/pipeline/events/   PIP-002  view_pipeline_errors
  ?severity=CRITICA|ALTA|MEDIA|BAJA|INFO
  ?error_type=ETL_FALLO|PARAM_INVALIDO|VALIDACION|...
  ?limit=N  (default 50, max 200)

v_eventos_recientes es un JOIN entre pipeline_event_log y job_execution_log
que enriquece cada evento con el contexto del job que lo originó.
"""
from django.db import connections, OperationalError
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access.permissions.function_permissions import HasFunction
from apps.audit.serializers.auditlog_serializers import AuditLogSerializer

_TAG = 'Pipeline — Eventos'

_VALID_SEVERITIES  = {'CRITICA', 'ALTA', 'MEDIA', 'BAJA', 'INFO'}
_VALID_ERROR_TYPES = {
    'PARAM_INVALIDO', 'ETL_FALLO', 'ETL_PARTIAL',
    'VALIDACION', 'REPORTE_VACIO', 'SISTEMA',
}
_COLUMNS = [
    'id', 'ts', 'error_type', 'severity', 'sp_nombre',
    'sql_state', 'p_quarter', 'p_segmento', 'error_resumen',
    'ejecutado_por', 'job_status', 'job_step', 'job_inicio',
]


def _row_to_dict(row):
    d = dict(zip(_COLUMNS, row))
    for k in ('ts', 'job_inicio'):
        if d.get(k) is not None:
            d[k] = str(d[k])
    return d


class PipelineEventListView(APIView):
    """GET /api/pipeline/events/ — UC_PIP_02."""
    serializer_class   = AuditLogSerializer
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'PIP-002'

    @extend_schema(
        operation_id='pipeline_events_list',
        summary='UC_PIP_02 — Eventos recientes del pipeline (v_eventos_recientes)',
        tags=[_TAG],
        parameters=[
            OpenApiParameter('severity',   str, description='Filtrar por severity'),
            OpenApiParameter('error_type', str, description='Filtrar por tipo de error'),
            OpenApiParameter('limit',      int, description='Máximo de filas (default 50)'),
        ],
        responses={
            200: OpenApiResponse(description='Lista de eventos del pipeline'),
            400: OpenApiResponse(description='Parámetro inválido'),
            503: OpenApiResponse(description='MariaDB no disponible'),
        },
    )
    def get(self, request):
        severity   = request.query_params.get('severity',   '').upper() or None
        error_type = request.query_params.get('error_type', '').upper() or None

        try:
            limit = int(request.query_params.get('limit', 50))
        except ValueError:
            return Response({'error': 'limit debe ser un entero'}, status=400)
        limit = min(max(limit, 1), 200)

        if severity and severity not in _VALID_SEVERITIES:
            return Response(
                {'error': f'severity inválido. Valores: {sorted(_VALID_SEVERITIES)}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if error_type and error_type not in _VALID_ERROR_TYPES:
            return Response(
                {'error': f'error_type inválido. Valores: {sorted(_VALID_ERROR_TYPES)}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sql    = f'SELECT {", ".join(_COLUMNS)} FROM v_eventos_recientes WHERE 1=1'
        params = []
        if severity:
            sql    += ' AND severity = %s'
            params.append(severity)
        if error_type:
            sql    += ' AND error_type = %s'
            params.append(error_type)
        sql += ' ORDER BY ts DESC LIMIT %s'
        params.append(limit)

        try:
            with connections['ivr'].cursor() as cur:
                cur.execute(sql, params)
                rows = [_row_to_dict(r) for r in cur.fetchall()]
        except OperationalError:
            return Response(
                {'error': 'IVR_DB_UNAVAILABLE'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response({
            'total':  len(rows),
            'limit':  limit,
            'events': rows,
        })
