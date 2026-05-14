"""
apps/access/sod_rule_view.py

SoDRuleCRUDView — UC_ACC_05: Gestionar Reglas de Separación de Deberes.

Fuente: uc-acc-05/criterios-aceptacion.rst § 9
Endpoints: /api/access/sod-rules/
Función RBAC: ACC-005 view_separation_rules / ACC-011 update_separation_rule
             ACC-012 disable_separation_rule
"""
from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access.permissions.function_permissions import HasFunction


class SoDRuleCreateSerializer(serializers.Serializer):
    code          = serializers.CharField(max_length=20)
    name          = serializers.CharField(max_length=200)
    description   = serializers.CharField(required=False, allow_blank=True, default='')
    function_ids_a = serializers.ListField(child=serializers.IntegerField(), min_length=1)
    function_ids_b = serializers.ListField(child=serializers.IntegerField(), min_length=1)


class SoDRulePatchSerializer(serializers.Serializer):
    name         = serializers.CharField(required=False)
    description  = serializers.CharField(required=False, allow_blank=True)
    function_ids_a = serializers.ListField(child=serializers.IntegerField(), required=False)
    function_ids_b = serializers.ListField(child=serializers.IntegerField(), required=False)


class SoDRuleRetireSerializer(serializers.Serializer):
    retire_reason = serializers.CharField(min_length=5)


@extend_schema(
    summary='UC_ACC_05 — Listar / Crear reglas SoD',
    description=(
        'GET: lista reglas SoD. ACC-005 view_separation_rules.\n\n'
        'POST: crea nueva regla SoD. ACC-011 update_separation_rule.\n\n'
        '**CA-01**: listado paginado.\n'
        '**CA-03**: crear exitoso → state=ENABLED.\n'
        '**CA-04**: duplicado → 409.\n'
        '**CA-05**: con violaciones existentes → 201 + existing_violations_count.\n'
        '**CA-06**: function no existe → 400.'
    ),
    tags=['Control de Acceso'],
)
class SoDRuleListCreateView(APIView):
    """GET/POST /api/access/sod-rules/"""

    def get_permissions(self):
        self.required_function = 'ACC-005' if self.request.method == 'GET' else 'ACC-011'
        return [IsAuthenticated(), HasFunction()]

    def get(self, request):
        from apps.access.models import SeparationRule
        qs = SeparationRule.objects.all().order_by('code')
        return Response({
            'count': qs.count(),
            'results': [
                {
                    'id': r.pk, 'code': r.code, 'name': r.name,
                    'state': r.state,
                    'functions_set_a': list(r.functions_set_a.values_list('code', flat=True)),
                    'functions_set_b': list(r.functions_set_b.values_list('code', flat=True)),
                }
                for r in qs
            ],
        })

    def post(self, request):
        from apps.access.models import SeparationRule, Function, UserFunctionAssignment
        from apps.audit.services import AuditLogService

        ser = SoDRuleCreateSerializer(data=request.data)
        if not ser.is_valid():
            return Response({'error': 'VALIDATION_ERROR', 'fields': ser.errors}, status=400)

        data = ser.validated_data
        code = data['code'].upper()

        # CA-04: duplicado
        if SeparationRule.objects.filter(code=code).exists():
            existing = SeparationRule.objects.get(code=code)
            return Response({'error': 'SOD_RULE_DUPLICATE', 'existing_rule_id': existing.pk}, status=409)

        # CA-06: functions válidas
        fns_a = list(Function.objects.filter(pk__in=data['function_ids_a'], is_active=True))
        fns_b = list(Function.objects.filter(pk__in=data['function_ids_b'], is_active=True))
        if len(fns_a) < len(data['function_ids_a']) or len(fns_b) < len(data['function_ids_b']):
            return Response({'error': 'FUNCTION_NOT_FOUND'}, status=400)

        with transaction.atomic():
            rule = SeparationRule.objects.create(
                code=code, name=data['name'],
                description=data.get('description', ''),
                state=SeparationRule.STATE_ENABLED,
            )
            rule.functions_set_a.set(fns_a)
            rule.functions_set_b.set(fns_b)

            # CA-05: detectar violaciones existentes
            codes_a = {f.code for f in fns_a}
            codes_b = {f.code for f in fns_b}
            violations = UserFunctionAssignment.objects.filter(
                state='ACTIVE', function__code__in=codes_a,
                user__in=UserFunctionAssignment.objects.filter(
                    state='ACTIVE', function__code__in=codes_b
                ).values('user'),
            ).values_list('user_id', flat=True).distinct()
            violations_count = violations.count()

            AuditLogService.emit(
                event_type='SOD_RULE_CREATED',
                actor_user_id=request.user.pk,
                payload={'rule_code': code, 'existing_violations': violations_count},
            )

        return Response({
            'id': rule.pk, 'code': rule.code, 'state': rule.state,
            'existing_violations_count': violations_count,
        }, status=201)


@extend_schema(
    summary='UC_ACC_05 — Detalle / Modificar / Retirar regla SoD',
    description=(
        '**CA-02**: detalle por id.\n'
        '**CA-07**: PATCH parcial — name/description.\n'
        '**CA-08**: function_ids inmutables → 400.\n'
        '**CA-09**: DELETE (BR-009) → state=DISABLED.'
    ),
    tags=['Control de Acceso'],
)
class SoDRuleDetailView(APIView):
    """GET/PATCH/DELETE /api/access/sod-rules/{rule_id}/"""

    def get_permissions(self):
        if self.request.method == 'GET':
            self.required_function = 'ACC-005'
        elif self.request.method == 'DELETE':
            self.required_function = 'ACC-012'
        else:
            self.required_function = 'ACC-011'
        return [IsAuthenticated(), HasFunction()]

    def _get_rule(self, rule_id):
        from apps.access.models import SeparationRule
        try:
            return SeparationRule.objects.get(pk=rule_id)
        except SeparationRule.DoesNotExist:
            return None

    def get(self, request, rule_id):
        rule = self._get_rule(rule_id)
        if not rule:
            return Response({'error': 'SOD_RULE_NOT_FOUND'}, status=404)
        return Response({
            'id': rule.pk, 'code': rule.code, 'name': rule.name,
            'state': rule.state, 'description': rule.description,
            'functions_set_a': list(rule.functions_set_a.values_list('code', flat=True)),
            'functions_set_b': list(rule.functions_set_b.values_list('code', flat=True)),
        })

    def patch(self, request, rule_id):
        from apps.audit.services import AuditLogService
        rule = self._get_rule(rule_id)
        if not rule:
            return Response({'error': 'SOD_RULE_NOT_FOUND'}, status=404)

        # CA-08: function_ids inmutables
        if 'function_ids_a' in request.data or 'function_ids_b' in request.data:
            return Response({'error': 'FUNCTION_IDS_IMMUTABLE'}, status=400)

        ser = SoDRulePatchSerializer(data=request.data, partial=True)
        if not ser.is_valid():
            return Response({'error': 'VALIDATION_ERROR', 'fields': ser.errors}, status=400)

        data = ser.validated_data
        changed = []
        if 'name' in data:
            rule.name = data['name']; changed.append('name')
        if 'description' in data:
            rule.description = data['description']; changed.append('description')
        if changed:
            rule.save(update_fields=changed)

        AuditLogService.emit(
            event_type='SOD_RULE_UPDATED',
            actor_user_id=request.user.pk,
            payload={'rule_id': rule_id, 'fields_changed': changed},
        )
        return Response({'id': rule.pk, 'code': rule.code, 'state': rule.state, 'fields_changed': changed})

    def delete(self, request, rule_id):
        from apps.audit.services import AuditLogService
        rule = self._get_rule(rule_id)
        if not rule:
            return Response({'error': 'SOD_RULE_NOT_FOUND'}, status=404)

        ser = SoDRuleRetireSerializer(data=request.data)
        if not ser.is_valid():
            return Response({'error': 'VALIDATION_ERROR', 'message': 'retire_reason requerido.'}, status=400)

        with transaction.atomic():
            rule.state = 'DISABLED'
            rule.save(update_fields=['state'])
            AuditLogService.emit(
                event_type='SOD_RULE_DISABLED',
                actor_user_id=request.user.pk,
                payload={'rule_id': rule_id, 'retire_reason': ser.validated_data['retire_reason']},
            )

        return Response({'message': f'Regla {rule.code} desactivada.', 'state': 'DISABLED'})
