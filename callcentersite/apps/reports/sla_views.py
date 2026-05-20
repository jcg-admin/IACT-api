"""
apps/reports/sla_views.py

UC_RPT_03 — Ver Reportes Historicos (SLA por trimestre).

Reporte SLA por trimestre via v_sla_distribucion de MariaDB ivr_legacy.

GET /api/reports/ivr/sla/   RPT-019  view_ivr_reports
  ?quarter=Q0N_YY   (opcional — filtra por trimestre)

v_sla_distribucion: PIVOT emulado con SUM(CASE WHEN) que clasifica centros
en FUERA_SLA, RIESGO_SLA, DENTRO_SLA, ACTIVO_HOY, VOLUMEN_MEDIO, BAJO_VOLUMEN.
Una fila por trimestre — no requiere parámetros en la vista.
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

_TAG    = 'Reportes IVR'
_Q_RE   = re.compile(r'^Q0[1-4]_\d{2}$')
_COLS   = [
    'trimestre', 'fuera_sla', 'riesgo_sla', 'dentro_sla', 'activo_hoy',
    'volumen_medio', 'bajo_volumen', 'total_centros',
]


def _row_to_dict(row):
    d = dict(zip(_COLS, row))
    # Convertir Decimal a float para JSON
    for k in _COLS[1:]:
        if d[k] is not None:
            d[k] = float(d[k])
    return d


class SLADistribucionView(APIView):
    """GET /api/reports/ivr/sla/ — SLA por trimestre."""
    serializer_class   = AuditLogSerializer
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'RPT-019'

    @extend_schema(
        operation_id='reports_ivr_sla',
        summary='Reporte SLA de centros de transferencia por trimestre',
        description=(
            'Consulta v_sla_distribucion en ivr_legacy. '
            'Clasifica centros en FUERA_SLA, RIESGO_SLA, DENTRO_SLA, '
            'ACTIVO_HOY, VOLUMEN_MEDIO y BAJO_VOLUMEN por trimestre.'
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
            200: OpenApiResponse(description='Distribución SLA por trimestre'),
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

        sql    = f'SELECT {", ".join(_COLS)} FROM v_sla_distribucion'
        params = []
        if quarter:
            sql   += ' WHERE trimestre = %s'
            params.append(quarter)
        sql += ' ORDER BY trimestre'

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
            'resumen': {
                'trimestres_con_datos': len(rows),
            },
            'trimestres': rows,
        })
