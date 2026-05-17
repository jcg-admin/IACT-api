"""
apps/alerts/alert_views.py

Vistas para UC_ALR_01/02/03.

AlertRuleListCreateView  — POST/GET  /api/alerts/rules/
AlertRuleDetailView      — GET/PATCH/DELETE /api/alerts/rules/{id}/
AlertRulePauseView       — POST /api/alerts/rules/{id}/pause/
AlertRuleResumeView      — POST /api/alerts/rules/{id}/resume/
AlertRuleDryRunView      — POST /api/alerts/rules/dry-run/
ActiveAlertsView         — GET /api/alerts/active/
AlertAcknowledgeView     — POST /api/alerts/{id}/acknowledge/
AlertBulkAcknowledgeView — POST /api/alerts/bulk-acknowledge/
"""
from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import (
    extend_schema, extend_schema_view,
)
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access.permissions.function_permissions import HasFunction
from apps.alerts.alert_service import RuleValidator, AlertAckValidator, DryRunEngine
from apps.alerts.models import AlertRule, AlertRuleHistory, Alert
from apps.audit.services import AuditLogService
from apps.alerts.serializers.alert_serializers import AlertConfigurationSerializer


_TAG_ALR = 'Alertas'


# ---------------------------------------------------------------------------
# Serializers de request
# ---------------------------------------------------------------------------

class AlertRuleCreateSerializer(serializers.Serializer):
    name             = serializers.CharField(max_length=200)
    metric           = serializers.CharField(max_length=100)
    scope            = serializers.DictField()
    condition        = serializers.DictField()
    window_minutes   = serializers.IntegerField(min_value=1)
    severity         = serializers.ChoiceField(choices=['info', 'warning', 'error', 'critical'])
    actions          = serializers.ListField(child=serializers.DictField(), default=list)
    cooldown_minutes = serializers.IntegerField(min_value=1, default=60)


class AlertRulePatchSerializer(serializers.Serializer):
    name             = serializers.CharField(required=False)
    condition        = serializers.DictField(required=False)
    window_minutes   = serializers.IntegerField(required=False, min_value=1)
    severity         = serializers.ChoiceField(
        required=False, choices=['info', 'warning', 'error', 'critical'])
    actions          = serializers.ListField(required=False, child=serializers.DictField())
    cooldown_minutes = serializers.IntegerField(required=False, min_value=1)


class AcknowledgeSerializer(serializers.Serializer):
    note = serializers.CharField(default='', allow_blank=True)


def _rule_to_dict(rule: AlertRule) -> dict:
    return {
        'id': str(rule.id), 'name': rule.name, 'metric': rule.metric,
        'scope': rule.scope, 'condition': rule.condition,
        'window_minutes': rule.window_minutes, 'severity': rule.severity,
        'actions': rule.actions, 'cooldown_minutes': rule.cooldown_minutes,
        'status': rule.status, 'version': rule.version,
        'actor': rule.actor_id,
        'created_at': rule.created_at.isoformat() if rule.created_at else None,
    }


def _alert_to_dict(alert: Alert) -> dict:
    return {
        'id': str(alert.id), 'rule_id': str(alert.rule_id),
        'rule_name': alert.rule_name,
        'metric': alert.metric, 'scope': alert.scope,
        'severity': alert.severity, 'state': alert.state,
        'fired_at': alert.fired_at.isoformat(),
        'current_value': alert.current_value, 'threshold': alert.threshold,
        'acknowledged_by': alert.acknowledged_by_id,
        'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
    }


# ---------------------------------------------------------------------------
# UC_ALR_01 — CRUD
# ---------------------------------------------------------------------------

@extend_schema_view(
    get=extend_schema(
        operation_id='alerts_rule_list', summary='UC_ALR_01 — Listar reglas de alerta',
        tags=[_TAG_ALR],
    ),
    post=extend_schema(
        operation_id='alerts_rule_create', summary='UC_ALR_01 — Crear regla de alerta',
        tags=[_TAG_ALR],
    ),
)
class AlertRuleListCreateView(APIView):
    serializer_class = AlertConfigurationSerializer
    """GET/POST /api/alerts/rules/ — UC_ALR_01"""

    def get_permissions(self):
        self.required_function = 'ALR-002' if self.request.method == 'POST' else 'ALR-002'
        return [IsAuthenticated(), HasFunction()]

    def get(self, request):
        qs = AlertRule.objects.filter(actor=request.user).order_by('-created_at')
        return Response({
            'count': qs.count(),
            'results': [_rule_to_dict(r) for r in qs],
        })

    def post(self, request):
        ser = AlertRuleCreateSerializer(data=request.data)
        if not ser.is_valid():
            return Response({'error': 'VALIDATION_ERROR', 'fields': ser.errors}, status=400)

        data = ser.validated_data
        # UC_ALR_01 PASO 4: validar metric, scope, actions
        try:
            segments = ['all']  # En prod: SegmentResolver.for(request.user.id)
            RuleValidator.validate(data, segments=segments)
        except ValueError as e:
            return Response({'error': 'VALIDATION_ERROR', 'detail': str(e)}, status=400)

        with transaction.atomic():
            rule = AlertRule.objects.create(
                actor=request.user,
                name=data['name'], metric=data['metric'],
                scope=data['scope'], condition=data['condition'],
                window_minutes=data['window_minutes'], severity=data['severity'],
                actions=data.get('actions', []),
                cooldown_minutes=data.get('cooldown_minutes', 60),
            )
            # UC_ALR_01 CA-10: audit
            AuditLogService.emit(
                event_type='ALERT_RULE_CREATED',
                actor_user_id=request.user.pk,
                payload={'rule_id': str(rule.id), 'name': rule.name, 'metric': rule.metric},
            )

        return Response(_rule_to_dict(rule), status=201)


@extend_schema_view(
    get=extend_schema(
        operation_id='alerts_rule_retrieve', summary='UC_ALR_01 — Detalle de regla',
        tags=[_TAG_ALR],
    ),
    patch=extend_schema(
        operation_id='alerts_rule_update', summary='UC_ALR_01 — Modificar regla',
        tags=[_TAG_ALR],
    ),
    delete=extend_schema(
        operation_id='alerts_rule_destroy', summary='UC_ALR_01 — Retirar regla (baja lógica)',
        tags=[_TAG_ALR],
    ),
)
class AlertRuleDetailView(APIView):
    serializer_class = AlertConfigurationSerializer
    """GET/PATCH/DELETE /api/alerts/rules/{id}/ — UC_ALR_01"""

    def get_permissions(self):
        self.required_function = 'ALR-002'
        return [IsAuthenticated(), HasFunction()]

    def _get_rule(self, rule_id, user):
        try:
            return AlertRule.objects.get(id=rule_id, actor=user)
        except (AlertRule.DoesNotExist, ValueError):
            return None

    def get(self, request, rule_id):
        rule = self._get_rule(rule_id, request.user)
        if not rule:
            return Response({'error': 'RULE_NOT_FOUND'}, status=404)
        return Response(_rule_to_dict(rule))

    def patch(self, request, rule_id):
        rule = self._get_rule(rule_id, request.user)
        if not rule:
            return Response({'error': 'RULE_NOT_FOUND'}, status=404)

        ser = AlertRulePatchSerializer(data=request.data, partial=True)
        if not ser.is_valid():
            return Response({'error': 'VALIDATION_ERROR', 'fields': ser.errors}, status=400)

        data = ser.validated_data
        # Snapshot antes del cambio para historial
        snapshot = _rule_to_dict(rule)

        with transaction.atomic():
            for field, value in data.items():
                setattr(rule, field, value)
            rule.version += 1
            rule.save()

            AlertRuleHistory.objects.create(
                rule=rule, version=rule.version - 1,
                snapshot=snapshot, changed_by=request.user,
            )
            AuditLogService.emit(
                event_type='ALERT_RULE_UPDATED',
                actor_user_id=request.user.pk,
                payload={'rule_id': str(rule.id), 'version': rule.version,
                         'fields': list(data.keys())},
            )
        return Response(_rule_to_dict(rule))

    def delete(self, request, rule_id):
        """CA-07: BR-009 — baja lógica, no DELETE físico."""
        rule = self._get_rule(rule_id, request.user)
        if not rule:
            return Response({'error': 'RULE_NOT_FOUND'}, status=404)

        with transaction.atomic():
            rule.status = AlertRule.STATUS_PAUSED
            rule.save(update_fields=['status'])
            AuditLogService.emit(
                event_type='ALERT_RULE_DELETED',
                actor_user_id=request.user.pk,
                payload={'rule_id': str(rule.id), 'note': 'BR-009: baja lógica'},
            )
        return Response({'id': str(rule.id), 'status': rule.status})


@extend_schema(tags=[_TAG_ALR])
class AlertRulePauseView(APIView):
    serializer_class = AlertConfigurationSerializer
    """POST /api/alerts/rules/{id}/pause/ — UC_ALR_01 CA-06"""

    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'ALR-004'  # pause_alerts

    def post(self, request, rule_id):
        try:
            rule = AlertRule.objects.get(id=rule_id, actor=request.user)
        except (AlertRule.DoesNotExist, ValueError):
            return Response({'error': 'RULE_NOT_FOUND'}, status=404)
        rule.status = AlertRule.STATUS_PAUSED
        rule.save(update_fields=['status'])
        AuditLogService.emit(
            event_type='ALERT_RULE_PAUSED',
            actor_user_id=request.user.pk,
            payload={'rule_id': str(rule.id)},
        )
        return Response({'id': str(rule.id), 'status': rule.status})


@extend_schema(tags=[_TAG_ALR])
class AlertRuleResumeView(APIView):
    serializer_class = AlertConfigurationSerializer
    """POST /api/alerts/rules/{id}/resume/ — UC_ALR_01 CA-06"""

    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'ALR-004'

    def post(self, request, rule_id):
        try:
            rule = AlertRule.objects.get(id=rule_id, actor=request.user)
        except (AlertRule.DoesNotExist, ValueError):
            return Response({'error': 'RULE_NOT_FOUND'}, status=404)
        rule.status = AlertRule.STATUS_ACTIVE
        rule.save(update_fields=['status'])
        AuditLogService.emit(
            event_type='ALERT_RULE_RESUMED',
            actor_user_id=request.user.pk,
            payload={'rule_id': str(rule.id)},
        )
        return Response({'id': str(rule.id), 'status': rule.status})


@extend_schema(tags=[_TAG_ALR])
class AlertRuleDryRunView(APIView):
    serializer_class = AlertConfigurationSerializer
    """POST /api/alerts/rules/dry-run/ — UC_ALR_01 CA-08"""

    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'ALR-002'

    def post(self, request):
        ser = AlertRuleCreateSerializer(data=request.data)
        if not ser.is_valid():
            return Response({'error': 'VALIDATION_ERROR', 'fields': ser.errors}, status=400)
        data = ser.validated_data
        try:
            RuleValidator.validate(data, segments=['all'])
        except ValueError as e:
            return Response({'error': 'VALIDATION_ERROR', 'detail': str(e)}, status=400)

        # CA-08: NO crea Alert — solo evalúa
        result = DryRunEngine.evaluate_against(data)
        return Response({'dry_run': True, **result})


# ---------------------------------------------------------------------------
# UC_ALR_02 — Ver Alertas Activas
# ---------------------------------------------------------------------------

@extend_schema(tags=[_TAG_ALR])
class ActiveAlertsView(APIView):
    serializer_class = AlertConfigurationSerializer
    """GET /api/alerts/active/ — UC_ALR_02"""

    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'ALR-011'  # view_active_alerts

    def get(self, request):
        severity = request.query_params.get('severity')

        qs = Alert.objects.filter(
            state__in=(Alert.STATE_FIRING, Alert.STATE_ACKNOWLEDGED),
        ).select_related('rule').order_by(
            # CA-06: orden por severity DESC, fired_at DESC
            '-severity', '-fired_at',
        )

        if severity:
            qs = qs.filter(severity=severity)

        # CA-04: filtrar por scope del usuario (scope ⊆ segmentos)
        # En prod: SegmentResolver.for(request.user.id)
        # Por ahora retorna todo lo que el usuario puede ver

        return Response({
            'count': qs.count(),
            'items': [_alert_to_dict(a) for a in qs],
        })


# ---------------------------------------------------------------------------
# UC_ALR_03 — Reconocer Alerta
# ---------------------------------------------------------------------------

@extend_schema(tags=[_TAG_ALR])
class AlertAcknowledgeView(APIView):
    serializer_class = AlertConfigurationSerializer
    """POST /api/alerts/{id}/acknowledge/ — UC_ALR_03"""

    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'ALR-007'  # acknowledge_alert

    def post(self, request, alert_id):
        ser = AcknowledgeSerializer(data=request.data)
        if not ser.is_valid():
            return Response({'error': 'VALIDATION_ERROR', 'fields': ser.errors}, status=400)

        note = ser.validated_data.get('note', '')

        # UT-01: validar note
        try:
            AlertAckValidator.validate_note(note)
        except ValueError as e:
            return Response({'error': 'VALIDATION_ERROR', 'detail': str(e)}, status=400)

        try:
            alert = Alert.objects.get(id=alert_id)
        except (Alert.DoesNotExist, ValueError):
            return Response({'error': 'ALERT_NOT_FOUND'}, status=404)

        # CA-04/05: validar estado
        if alert.state in (Alert.STATE_ACKNOWLEDGED, Alert.STATE_RESOLVED, Alert.STATE_CLOSED):
            return Response(
                {'error': 'INVALID_STATE',
                 'detail': f'Alerta en estado {alert.state} — no se puede reconocer.'},
                status=409,
            )

        # PASO 7: atómico (CA-10)
        with transaction.atomic():
            alert.state             = Alert.STATE_ACKNOWLEDGED
            alert.acknowledged_by   = request.user
            alert.acknowledged_at   = timezone.now()
            alert.acknowledged_note = note
            alert.save(update_fields=[
                'state', 'acknowledged_by', 'acknowledged_at', 'acknowledged_note',
            ])
            AuditLogService.emit(
                event_type='ALERT_ACKNOWLEDGED',
                actor_user_id=request.user.pk,
                payload={
                    'alert_id': str(alert.id),
                    'rule_id': str(alert.rule_id),
                    'note_excerpt': note[:50],
                },
            )

        return Response(_alert_to_dict(alert))


@extend_schema(tags=[_TAG_ALR])
class AlertBulkAcknowledgeView(APIView):
    serializer_class = AlertConfigurationSerializer
    """POST /api/alerts/bulk-acknowledge/ — UC_ALR_03 CA-08"""

    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'ALR-007'

    def post(self, request):
        alert_ids = request.data.get('alert_ids', [])
        note      = request.data.get('note', '')

        if not alert_ids:
            return Response({'error': 'alert_ids requerido.'}, status=400)

        try:
            AlertAckValidator.validate_note(note)
        except ValueError as e:
            return Response({'error': 'VALIDATION_ERROR', 'detail': str(e)}, status=400)

        acked = []
        errors = []
        for aid in alert_ids:
            try:
                alert = Alert.objects.get(id=aid, state=Alert.STATE_FIRING)
                with transaction.atomic():
                    alert.state = Alert.STATE_ACKNOWLEDGED
                    alert.acknowledged_by = request.user
                    alert.acknowledged_at = timezone.now()
                    alert.acknowledged_note = note
                    alert.save(update_fields=[
                        'state', 'acknowledged_by', 'acknowledged_at', 'acknowledged_note',
                    ])
                    AuditLogService.emit(
                        event_type='ALERT_ACKNOWLEDGED',
                        actor_user_id=request.user.pk,
                        payload={'alert_id': str(alert.id), 'bulk': True},
                    )
                acked.append(str(aid))
            except Alert.DoesNotExist:
                errors.append({'id': str(aid), 'error': 'NOT_FOUND_OR_NOT_FIRING'})

        return Response({'acknowledged': acked, 'errors': errors})
