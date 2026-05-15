"""
apps/reports/analytics_views.py

Vistas de reportes analíticos: UC_RPT_12..17.
Todas leen exclusivamente de MariaDB IVR (CNST-007: read-only Analytics).
"""
from django.db import connections, OperationalError
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access.permissions.function_permissions import HasFunction
from apps.audit.services import AuditLogService
from apps.audit.serializers.auditlog_serializers import AuditLogSerializer
from apps.reports.analytics_kpi import (
    AgentKPICalculator, QueueKPICalculator,
    CampaignKPICalculator, DistinctClientCounter,
)

_TAG = 'Reportes Analíticos'

_PERIOD_PARAM = OpenApiParameter(
    'period', str, enum=['last_24h', 'last_7d', 'last_30d', 'last_90d'],
    description='Período de consulta.', default='last_30d',
)


def _stub_rows(cursor, sql: str, params: tuple = ()) -> list:
    """Ejecuta la query y retorna filas como lista de dicts.

    Captura ProgrammingError cuando la tabla no existe en IVR (H-PROD-010).
    Retorna lista vacía en lugar de propagar la excepción como 500.
    """
    from django.db import ProgrammingError
    try:
        cursor.execute(sql, params)
    except ProgrammingError:
        return []
    if not cursor.description:
        return []
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def _timeout_response():
    return Response({'error': 'SERVICE_UNAVAILABLE'}, status=503)


# ---------------------------------------------------------------------------
# UC_RPT_12 — Agentes
# ---------------------------------------------------------------------------

@extend_schema_view(
    get=extend_schema(
        operation_id='reports_agent_list',
        summary='UC_RPT_12 — Reporte de rendimiento de agentes',
        parameters=[_PERIOD_PARAM],
        responses={200: OpenApiResponse(description='{items, summary}'),
                   503: OpenApiResponse(description='BD timeout')},
        tags=[_TAG],
    )
)
class AgentReportView(APIView):
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'RPT-014'

    def get(self, request):
        try:
            with connections['ivr'].cursor() as cur:
                rows = _stub_rows(cur,
                    "SELECT agent_id, name, answered_calls, sum_handle_time, busy_time, total_time "
                    "FROM agent_performance_summary WHERE 1=1")
        except OperationalError:
            return _timeout_response()

        items = []
        for row in rows:
            row['tmo']       = AgentKPICalculator.tmo(row)
            row['occupancy'] = AgentKPICalculator.occupancy(row)
            # CNST-026: eliminar PII
            for pii_key in ('email', 'phone', 'full_name'):
                row.pop(pii_key, None)
            items.append(row)

        return Response({'items': items, 'summary': {'total_agents': len(items)}})


@extend_schema_view(
    get=extend_schema(
    operation_id='reports_agent_detail',
    summary='UC_RPT_12 — Detalle privilegiado de agente (RPT-015)',
    tags=[_TAG],
)
)
class AgentDetailView(APIView):
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'RPT-015'   # view_agent_detail — función adicional (CA-06)

    def get(self, request, agent_id):
        AuditLogService.emit(
            event_type='AGENT_DETAIL_VIEWED',
            actor_user_id=request.user.pk,
            payload={'agent_id': agent_id},
        )
        try:
            with connections['ivr'].cursor() as cur:
                rows = _stub_rows(cur,
                    "SELECT * FROM agent_performance_detail WHERE agent_id=%s",
                    (agent_id,))
        except OperationalError:
            return _timeout_response()
        if not rows:
            return Response({'error': 'NOT_FOUND'}, status=404)
        return Response(rows[0])


# ---------------------------------------------------------------------------
# UC_RPT_13 — Colas
# ---------------------------------------------------------------------------

@extend_schema_view(
    get=extend_schema(
        operation_id='reports_queue_list',
        summary='UC_RPT_13 — Reporte de colas de atención',
        parameters=[_PERIOD_PARAM],
        tags=[_TAG],
    )
)
class QueueReportView(APIView):
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'RPT-016'

    def get(self, request):
        try:
            with connections['ivr'].cursor() as cur:
                rows = _stub_rows(cur,
                    "SELECT queue_id, name, sum_wait, answered, abandoned, within_threshold, total_calls "
                    "FROM queue_performance_summary WHERE 1=1")
        except OperationalError:
            return _timeout_response()

        items = []
        for row in rows:
            row['asa']           = QueueKPICalculator.asa(row)
            row['service_level'] = QueueKPICalculator.service_level(row)
            row['abandon_rate']  = QueueKPICalculator.abandon_rate(row)
            items.append(row)

        return Response({'items': items, 'summary': {'total_queues': len(items)}})


# ---------------------------------------------------------------------------
# UC_RPT_14 — Campañas
# ---------------------------------------------------------------------------

@extend_schema_view(
    get=extend_schema(
        operation_id='reports_campaign_list',
        summary='UC_RPT_14 — Reporte de campañas',
        parameters=[_PERIOD_PARAM],
        tags=[_TAG],
    )
)
class CampaignReportView(APIView):
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'RPT-017'

    def get(self, request):
        try:
            with connections['ivr'].cursor() as cur:
                rows = _stub_rows(cur,
                    "SELECT campaign_id, name, total_calls, converted "
                    "FROM campaign_summary WHERE 1=1")
        except OperationalError:
            return _timeout_response()

        items = [
            {**row, 'conversion_rate': CampaignKPICalculator.conversion_rate(row)}
            for row in rows
        ]
        return Response({'items': items, 'summary': {'total_campaigns': len(items)}})


# ---------------------------------------------------------------------------
# UC_RPT_15 — Transferencias IVR
# ---------------------------------------------------------------------------

@extend_schema_view(
    get=extend_schema(
        operation_id='reports_transfer_list',
        summary='UC_RPT_15 — Reporte de transferencias IVR',
        parameters=[_PERIOD_PARAM],
        tags=[_TAG],
    )
)
class TransferReportView(APIView):
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'RPT-018'

    def get(self, request):
        try:
            with connections['ivr'].cursor() as cur:
                rows = _stub_rows(cur,
                    "SELECT * FROM ivr_transfer_summary WHERE 1=1")
        except OperationalError:
            return _timeout_response()
        return Response({'items': rows, 'summary': {'total': len(rows)}})


# ---------------------------------------------------------------------------
# UC_RPT_16 — Menús IVR
# ---------------------------------------------------------------------------

@extend_schema_view(
    get=extend_schema(
        operation_id='reports_ivr_menu_list',
        summary='UC_RPT_16 — Reporte de navegación IVR',
        parameters=[_PERIOD_PARAM, OpenApiParameter('ivr_id', int, description='Filtro por IVR.')],
        tags=[_TAG],
    )
)
class IVRMenuReportView(APIView):
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'RPT-019'

    def get(self, request):
        ivr_id = request.query_params.get('ivr_id')
        try:
            with connections['ivr'].cursor() as cur:
                if ivr_id:
                    rows = _stub_rows(cur,
                        "SELECT * FROM ivr_menu_navigation WHERE ivr_id=%s", (ivr_id,))
                else:
                    rows = _stub_rows(cur, "SELECT * FROM ivr_menu_navigation WHERE 1=1")
        except OperationalError:
            return _timeout_response()
        return Response({'items': rows, 'summary': {'sessions': len(rows)}})


# ---------------------------------------------------------------------------
# UC_RPT_17 — Clientes Únicos
# ---------------------------------------------------------------------------

@extend_schema_view(
    get=extend_schema(
        operation_id='reports_unique_clients',
        summary='UC_RPT_17 — Clientes únicos (sin client_id raw)',
        parameters=[_PERIOD_PARAM],
        tags=[_TAG],
    )
)
class UniqueClientsReportView(APIView):
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'RPT-020'

    def get(self, request):
        try:
            with connections['ivr'].cursor() as cur:
                rows = _stub_rows(cur,
                    "SELECT client_hash, call_count FROM unique_clients_summary WHERE 1=1")
        except OperationalError:
            return _timeout_response()

        ids = [r.get('client_hash', '') for r in rows]
        top_n = DistinctClientCounter.top_n_anonymized(ids, n=10)

        return Response({
            'data':         {'distinct_count': DistinctClientCounter.exact(ids)},
            'top_n':        top_n,
            'items':        [],  # CA-06: no client_id raw
            'summary':      {'total': len(rows)},
        })
