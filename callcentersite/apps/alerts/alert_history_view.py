"""
apps/alerts/alert_history_view.py

UC_ALR_04 — Ver Historial de Alertas.
GET /api/alerts/history/
Función: ALR-006 (view_alert_history)
"""
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access.permissions.function_permissions import HasFunction
from apps.alerts.models import Alert
from apps.alerts.alert_history_service import TimingCalculator

_TAG = 'Alertas'
_MAX_RANGE_DAYS = 365


@extend_schema_view(
    get=extend_schema(
        operation_id='alerts_history',
        summary='UC_ALR_04 — Historial de alertas disparadas',
        responses={
            200: OpenApiResponse(description='{items, summary}'),
            400: OpenApiResponse(description='Range > 1 año → 400'),
            403: OpenApiResponse(description='Sin ALR-006 view_alert_history'),
        },
        tags=[_TAG],
    )
)
class AlertHistoryView(APIView):
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'ALR-006'

    def get(self, request):
        try:
            days = int(request.query_params.get('days', 30))
        except (ValueError, TypeError):
            days = 30

        if days > _MAX_RANGE_DAYS:
            return Response({'error': 'RANGE_TOO_LARGE',
                             'detail': f'Máximo {_MAX_RANGE_DAYS} días.'}, status=400)

        severity = request.query_params.get('severity')
        qs = Alert.objects.all().order_by('-fired_at')
        if severity:
            qs = qs.filter(severity=severity)

        items = []
        for alert in qs[:200]:
            items.append({
                'id':           str(alert.id),
                'rule_name':    alert.rule_name,
                'severity':     alert.severity,
                'state':        alert.state,
                'fired_at':     alert.fired_at.isoformat(),
                'time_to_ack':  TimingCalculator.time_to_ack(
                    alert.fired_at, alert.acknowledged_at),
            })

        top_rules = {}
        for item in items:
            top_rules[item['rule_name']] = top_rules.get(item['rule_name'], 0) + 1
        top_rules_list = sorted(
            [{'rule_name': k, 'count': v} for k, v in top_rules.items()],
            key=lambda x: -x['count'],
        )[:10]

        return Response({
            'items': items,
            'summary': {
                'total': len(items),
                'top_rules': top_rules_list,
            },
        })
