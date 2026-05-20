"""
apps/alerts/alert_subscription_views.py

UC_ALR_05 — Gestionar Suscripciones.
POST/GET /api/me/alert-subscriptions/
DELETE   /api/me/alert-subscriptions/{id}/
"""
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access.permissions.function_permissions import HasFunction
from apps.alerts.alert_subscription_service import SubscriptionValidator
from apps.alerts.models import AlertSubscription, AlertRule
from apps.audit.services import AuditLogService
from apps.alerts.serializers.alert_serializers import AlertSubscriptionSerializer


_TAG = 'Alertas'


class SubCreateSerializer(serializers.Serializer):
    rule_id          = serializers.UUIDField()
    severity_filter  = serializers.CharField(default='warning')
    muted            = serializers.BooleanField(default=False)


@extend_schema_view(
    get=extend_schema(
        operation_id='alerts_subscription_list',
        summary='UC_ALR_05 — Listar suscripciones propias',
        tags=[_TAG],
    ),
    post=extend_schema(
        operation_id='alerts_subscription_create',
        summary='UC_ALR_05 — Crear suscripción a alerta',
        responses={
            201: OpenApiResponse(description='Suscripción creada'),
            409: OpenApiResponse(description='DUPLICATE_SUBSCRIPTION'),
        },
        tags=[_TAG],
    ),
)
class AlertSubscriptionListView(APIView):
    serializer_class = AlertSubscriptionSerializer
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'ALR-008'

    def get(self, request):
        qs = AlertSubscription.objects.filter(user=request.user).order_by('-created_at')
        return Response({
            'count': qs.count(),
            'results': [
                {'id': s.pk, 'rule_id': s.rule_id, 'state': s.state}
                for s in qs
            ],
        })

    def post(self, request):
        ser = SubCreateSerializer(data=request.data)
        if not ser.is_valid():
            return Response({'error': 'VALIDATION_ERROR', 'fields': ser.errors}, status=400)

        data = ser.validated_data
        try:
            SubscriptionValidator.validate(data)
            SubscriptionValidator.check_duplicate(request.user.pk, data['rule_id'])
        except ValueError as e:
            code = 'DUPLICATE_SUBSCRIPTION' if 'duplicad' in str(e) else 'VALIDATION_ERROR'
            http_st = 409 if code == 'DUPLICATE_SUBSCRIPTION' else 400
            return Response({'error': code, 'detail': str(e)}, status=http_st)

        try:
            rule = AlertRule.objects.get(pk=data['rule_id'])
        except AlertRule.DoesNotExist:
            return Response({'error': 'RULE_NOT_FOUND'}, status=404)

        sub = AlertSubscription.objects.create(
            user=request.user,
            rule=rule,
            state='active',
        )
        xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
        ip_admin = (xff.split(',')[0].strip() if xff
                    else request.META.get('REMOTE_ADDR', '')) or None
        AuditLogService.emit(
            event_type='ALERT_SUBSCRIPTION_CREATED',
            actor_user_id=request.user.pk,
            target_entity_type='AlertSubscription',
            target_entity_id=str(sub.pk),
            ip_address=ip_admin,
            payload={'subscription_id': str(sub.pk), 'rule_id': str(rule.pk)},
        )
        return Response({'id': str(sub.pk), 'rule_id': str(sub.rule_id), 'state': sub.state}, status=201)


@extend_schema_view(
    delete=extend_schema(
        operation_id='alerts_subscription_delete',
        summary='UC_ALR_05 — Cancelar suscripción',
        tags=[_TAG],
    ),
)
class AlertSubscriptionDetailView(APIView):
    serializer_class = AlertSubscriptionSerializer
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'ALR-009'

    def delete(self, request, sub_id):
        try:
            sub = AlertSubscription.objects.get(pk=sub_id, user=request.user)
        except AlertSubscription.DoesNotExist:
            return Response({'error': 'NOT_FOUND'}, status=404)
        sub.state = 'cancelled'
        sub.save(update_fields=['state'])
        xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
        ip_admin = (xff.split(',')[0].strip() if xff
                    else request.META.get('REMOTE_ADDR', '')) or None
        AuditLogService.emit(
            event_type='ALERT_SUBSCRIPTION_CANCELLED',
            actor_user_id=request.user.pk,
            target_entity_type='AlertSubscription',
            target_entity_id=str(sub.pk),
            ip_address=ip_admin,
            payload={'subscription_id': str(sub.pk)},
        )
        return Response({'id': sub.pk, 'state': sub.state})
