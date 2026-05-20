"""
apps/pipeline/monitor_weekday_views.py

UC_PIP_01 — Ver Estado Pipeline (monitor weekday view).

Monitor de distribucion de llamadas por dias de semana
via vw_monitor_dias_semana de MariaDB ivr_legacy.

GET /api/pipeline/monitor/weekdays/   PIP-001  view_pipeline_status
  ?quarter=Q0N_YY  (opcional)

vw_monitor_dias_semana:
  Una fila por mes (fecha=YYYYMM) dentro de cada trimestre.
  Columnas: trimestre, fecha, total, habiles, fin_semana,
            error_suma, pct_entre_semana, estado_monitor.
  estado_monitor = 'OK' | 'ALERTA' (ALERTA si error_suma > 0).

Uso operacional:
  Detecta meses donde la suma habiles+fin_semana != total (error_suma > 0).
  Permite verificar la integridad de los datos del ETL antes de reportar.
"""
import re
from django.db import connections, OperationalError
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access.permissions.function_permissions import HasFunction
from apps.audit.serializers.auditlog_serializers import AuditLogSerializer

_TAG  = 'Pipeline — Monitor'
_Q_RE = re.compile(r'^Q0[1-4]_\d{2}$')
_COLS = [
    'trimestre', 'fecha', 'total', 'habiles', 'fin_semana',
    'error_suma', 'pct_entre_semana', 'estado_monitor',
]


def _row_to_dict(row):
    d = dict(zip(_COLS, row))
    for k in ('total', 'habiles', 'fin_semana', 'error_suma', 'pct_entre_semana'):
        if d[k] is not None:
            d[k] = float(d[k])
    return d


class MonitorWeekdayView(APIView):
    """GET /api/pipeline/monitor/weekdays/ — distribución días semana."""
    serializer_class   = AuditLogSerializer
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'PIP-001'

    @extend_schema(
        operation_id='pipeline_monitor_weekdays',
        summary='Monitor de distribución de llamadas por días de semana',
        description=(
            'Consulta vw_monitor_dias_semana en ivr_legacy. '
            'Detecta meses donde habiles+fin_semana != total (error_suma > 0). '
            'estado_monitor=ALERTA indica posible inconsistencia en los datos del ETL.'
        ),
        tags=[_TAG],
        parameters=[
            OpenApiParameter(
                'quarter', str,
                description='Trimestre en formato Q0N_YY (ej: Q02_26)',
                required=False,
            ),
        ],
        responses={
            200: OpenApiResponse(description='Monitor de días de semana por mes'),
            400: OpenApiResponse(description='Formato de quarter inválido'),
            503: OpenApiResponse(description='MariaDB no disponible'),
        },
    )
    def get(self, request):
        quarter = request.query_params.get('quarter', '').strip().upper()

        if quarter and not _Q_RE.match(quarter):
            return Response(
                {'error': 'QUARTER_INVALIDO',
                 'detail': 'Formato esperado: Q01_25, Q02_26, ...'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sql    = f'SELECT {", ".join(_COLS)} FROM vw_monitor_dias_semana'
        params = []
        if quarter:
            sql   += ' WHERE trimestre = %s'
            params.append(quarter)
        sql += ' ORDER BY trimestre, fecha'

        try:
            with connections['ivr'].cursor() as cur:
                cur.execute(sql, params)
                rows = [_row_to_dict(r) for r in cur.fetchall()]
        except OperationalError:
            return Response(
                {'error': 'IVR_DB_UNAVAILABLE'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        alertas = sum(1 for r in rows if r.get('estado_monitor') != 'OK')

        return Response({
            'resumen': {
                'total_filas': len(rows),
                'alertas':     alertas,
            },
            'filas': rows,
        })
