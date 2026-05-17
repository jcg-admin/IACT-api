"""
apps/reports/realtime_view.py

UC_RPT_02 — Ver Métricas en Tiempo Real (STUB).

Fuente: uc-rpt-02/implementacion-tecnica.rst
Función RBAC: RPT-012 (view_realtime_metrics)

STUB: UC_RPT_02 requiere infraestructura SSE/ASGI con pub/sub
(topics: call_state_changes, agent_state_changes, queue_state_snapshots).
El stack actual es Django WSGI sincrónico. Este endpoint retorna 503
con el contrato completo documentado.

Contrato completo en: uc-rpt-02/implementacion-tecnica.rst § 11.2
Prerequisito FASE 3 (2026-05-13):
  Hallazgo H-F3-PRE-004: UC_RPT_02 requiere ASGI — se implementa como stub.
  Hallazgo H-F3-PRE-005: view_realtime_metrics no existía en el catálogo v5.4.0
    → añadida como RPT-012 en create_functions.py.

Cuando se migre a ASGI (uvicorn/daphne):
  1. Implementar StreamGateway con SSE/WS
  2. Implementar StreamSubscriber contra el pub/sub configurado
  3. Implementar ConnectionRegistry (en memoria — no persistente)
  4. Implementar Throttler (1 mensaje / 5s), HeartbeatTimer (30s)
  5. Reemplazar este stub por la implementación real
"""
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access.permissions.function_permissions import HasFunction


@extend_schema(
    summary='UC_RPT_02 — Ver Métricas en Tiempo Real (STUB — requiere ASGI)',
    description=(
        '**STUB**: UC_RPT_02 requiere infraestructura SSE/ASGI con pub/sub '
        '(topics: call_state_changes, agent_state_changes, queue_state_snapshots). '
        'El stack actual es Django WSGI sincrónico. '
        'Retorna 503 hasta que se migre a ASGI server (uvicorn/daphne). '
        '\n\n**Contrato completo:** uc-rpt-02/implementacion-tecnica.rst § 11.2\n\n'
        '**Función RBAC:** RPT-012 view_realtime_metrics'
    ),
    responses={
        503: OpenApiResponse(description='FEATURE_NOT_AVAILABLE — requiere infraestructura ASGI/SSE'),
        403: OpenApiResponse(description='Sin función RPT-012 view_realtime_metrics'),
    },
    tags=['Reportes'],
)
class RealtimeMetricsView(APIView):
    """
    UC_RPT_02 — Ver Métricas en Tiempo Real (STUB).

    GET /api/reports/realtime/

    STUB: retorna 503 hasta que la infraestructura SSE/ASGI esté disponible.
    CNST-010: permission_classes explícito.
    """

    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'RPT-012'  # view_realtime_metrics

    def get(self, request):
        return Response(
            {
                'error':    'FEATURE_NOT_AVAILABLE',
                'detail':   (
                    'UC_RPT_02 requiere infraestructura SSE/ASGI con pub/sub. '
                    'El servidor actual es Django WSGI sincrónico. '
                    'Disponible cuando se migre a ASGI server (uvicorn/daphne).'
                ),
                'contract': 'uc-rpt-02/implementacion-tecnica.rst § 11.2',
                'function': 'RPT-012 view_realtime_metrics',
                'topics_required': [
                    'call_state_changes',
                    'agent_state_changes',
                    'queue_state_snapshots',
                ],
            },
            status=503,
        )
