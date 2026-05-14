"""
apps/reports/historical_view.py

UC_RPT_03 — Ver Reportes Históricos.
GET /api/reports/historical/
Función: RPT-013 (view_historical_reports)
"""
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access.permissions.function_permissions import HasFunction
from apps.reports.historical_service import (
    HistoricalReportService, FilterValidator,
)


@extend_schema(
    summary='UC_RPT_03 — Ver Reportes Históricos',
    parameters=[
        OpenApiParameter('period', str,
            enum=['last_24h', 'last_7d', 'last_30d', 'last_90d'],
            description='Período predefinido (default: last_30d).'),
        OpenApiParameter('date_from', str, description='Inicio custom (YYYY-MM-DD).'),
        OpenApiParameter('date_to',   str, description='Fin custom (YYYY-MM-DD).'),
        OpenApiParameter('group_by',  str,
            enum=['hour', 'day', 'week', 'month'],
            description='Granularidad de los buckets.'),
        OpenApiParameter('page',      int, default=1),
        OpenApiParameter('page_size', int, default=50, description='Máx 200.'),
    ],
    responses={
        200: OpenApiResponse(description='Reporte con buckets y comparativo'),
        400: OpenApiResponse(description='Parámetros inválidos'),
        403: OpenApiResponse(description='Sin RPT-013 view_historical_reports'),
        503: OpenApiResponse(description='BD Analytics no disponible'),
    },
    tags=['Reportes'],
)
class HistoricalReportView(APIView):
    """
    UC_RPT_03 — Ver Reportes Históricos.

    GET /api/reports/historical/
    CNST-007: read-only sobre Analytics BD.
    CNST-008: filtro de segmento aplicado.
    CNST-010: permission_classes explícito.
    """

    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'RPT-013'  # view_historical_reports

    def get(self, request):
        period   = request.query_params.get('period', 'last_30d')
        group_by_param = request.query_params.get('group_by', 'day')
        group_by = [group_by_param] if group_by_param else ['day']

        try:
            page      = max(1, int(request.query_params.get('page', 1)))
            page_size = min(200, max(1, int(request.query_params.get('page_size', 50))))
        except (ValueError, TypeError):
            page, page_size = 1, 50

        filters = {}
        if request.query_params.get('date_from'):
            filters['date_from'] = request.query_params['date_from']
        if request.query_params.get('date_to'):
            filters['date_to'] = request.query_params['date_to']

        # EX-05/06/07: validar antes de consultar
        try:
            from apps.reports.historical_service import _PERIOD_DAYS
            if 'date_from' in filters and 'date_to' in filters:
                from datetime import datetime
                from_dt = datetime.fromisoformat(filters['date_from'])
                to_dt   = datetime.fromisoformat(filters['date_to'])
                period_days = (to_dt - from_dt).days
            else:
                period_days = _PERIOD_DAYS.get(period, 30)

            FilterValidator.validate(
                period_days=period_days,
                group_by=group_by,
                page_size=page_size,
            )
        except ValueError as e:
            err = str(e)
            code = err if err in ('RANGE_TOO_LARGE',) else 'VALIDATION_ERROR'
            return Response({'error': code, 'detail': err}, status=400)

        try:
            svc    = HistoricalReportService()
            result = svc.get(
                filters=filters, period=period,
                group_by=group_by, page=page,
                invoker=request.user,
            )
        except ValueError as e:
            return Response({'error': 'VALIDATION_ERROR', 'detail': str(e)}, status=400)
        except Exception as e:
            if 'BD_TIMEOUT' in str(e) or 'timeout' in str(e).lower():
                return Response({'error': 'SERVICE_UNAVAILABLE'}, status=503)
            raise

        return Response(result)
