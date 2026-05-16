"""
apps/access/separation_rule_view.py

SeparationRuleCRUDView — UC_ACC_05: Gestionar Reglas de Separación de Deberes.

Fuente: uc-acc-05/criterios-aceptacion.rst § 9
Endpoints:
  GET  /api/access/separation-rules/             — listar
  POST /api/access/separation-rules/             — crear
  GET  /api/access/separation-rules/{rule_id}/   — detalle
  PATCH /api/access/separation-rules/{rule_id}/  — modificar
  DELETE /api/access/separation-rules/{rule_id}/ — retirar (baja lógica)
Función RBAC: ACC-005 view_separation_rules / ACC-011 update_separation_rule
             ACC-012 disable_separation_rule

Historial de renombres:
  STD_008 FASE 1 (2026-05-13): sod_rule_view.py → separation_rule_view.py
    SoDRuleCreateSerializer  → SeparationRuleCreateSerializer
    SoDRulePatchSerializer   → SeparationRulePatchSerializer
    SoDRuleRetireSerializer  → SeparationRuleRetireSerializer
    SoDRuleListCreateView    → SeparationRuleListCreateView
    SoDRuleDetailView        → SeparationRuleDetailView
  STD_008 FASE 3 (2026-05-13): URL sod-rules/ → separation-rules/
    error codes SOD_RULE_* → SEPARATION_RULE_*
    event types SOD_RULE_* → SEPARATION_RULE_*
    @extend_schema por método — operation_id explícito + request + responses
"""
from django.db import transaction
from drf_spectacular.utils import (
    extend_schema, OpenApiResponse, inline_serializer,
)
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access.permissions.function_permissions import HasFunction

_TAG = 'Control de Acceso'


# ---------------------------------------------------------------------------
# Serializers de request
# ---------------------------------------------------------------------------

class SeparationRuleCreateSerializer(serializers.Serializer):
    code           = serializers.CharField(max_length=20)
    name           = serializers.CharField(max_length=200)
    description    = serializers.CharField(required=False, allow_blank=True, default='')
    function_ids_a = serializers.ListField(child=serializers.IntegerField(), min_length=1)
    function_ids_b = serializers.ListField(child=serializers.IntegerField(), min_length=1)


class SeparationRulePatchSerializer(serializers.Serializer):
    name           = serializers.CharField(required=False)
    description    = serializers.CharField(required=False, allow_blank=True)
    function_ids_a = serializers.ListField(child=serializers.IntegerField(), required=False)
    function_ids_b = serializers.ListField(child=serializers.IntegerField(), required=False)


class SeparationRuleRetireSerializer(serializers.Serializer):
    retire_reason = serializers.CharField(min_length=5)


# ---------------------------------------------------------------------------
# Inline response schemas para drf-spectacular
# ---------------------------------------------------------------------------

def _rule_item_schema():
    return inline_serializer('SeparationRuleItem', fields={
        'id':              serializers.IntegerField(),
        'code':            serializers.CharField(),
        'name':            serializers.CharField(),
        'state':           serializers.CharField(),
        'functions_set_a': serializers.ListField(child=serializers.CharField()),
        'functions_set_b': serializers.ListField(child=serializers.CharField()),
    })


def _rule_list_schema():
    return inline_serializer('SeparationRuleListResponse', fields={
        'count':   serializers.IntegerField(),
        'results': serializers.ListField(child=_rule_item_schema()),
    })


def _rule_create_response_schema():
    return inline_serializer('SeparationRuleCreateResponse', fields={
        'id':                        serializers.IntegerField(),
        'code':                      serializers.CharField(),
        'state':                     serializers.CharField(),
        'existing_violations_count': serializers.IntegerField(),
    })


def _rule_detail_schema():
    return inline_serializer('SeparationRuleDetailResponse', fields={
        'id':              serializers.IntegerField(),
        'code':            serializers.CharField(),
        'name':            serializers.CharField(),
        'state':           serializers.CharField(),
        'description':     serializers.CharField(),
        'functions_set_a': serializers.ListField(child=serializers.CharField()),
        'functions_set_b': serializers.ListField(child=serializers.CharField()),
    })


def _rule_patch_response_schema():
    return inline_serializer('SeparationRulePatchResponse', fields={
        'id':             serializers.IntegerField(),
        'code':           serializers.CharField(),
        'state':          serializers.CharField(),
        'fields_changed': serializers.ListField(child=serializers.CharField()),
    })


def _rule_retire_response_schema():
    return inline_serializer('SeparationRuleRetireResponse', fields={
        'message': serializers.CharField(),
        'state':   serializers.CharField(),
    })


# ---------------------------------------------------------------------------
# UC_ACC_05 — SeparationRuleListCreateView
# ---------------------------------------------------------------------------

class SeparationRuleListCreateView(APIView):
    """
    GET/POST /api/access/separation-rules/

    UC_ACC_05 — Listar y crear reglas de separación de funciones.
    CNST-010: permission_classes gestionado via get_permissions() con HasFunction.
    STD_008 FASE 3: URL separation-rules/ vigente desde 2026-05-13.
    """

    def get_permissions(self):
        self.required_function = 'ACC-005' if self.request.method == 'GET' else 'ACC-011'
        return [IsAuthenticated(), HasFunction()]

    @extend_schema(
        operation_id='separation_rule_list',
        summary='UC_ACC_05 — Listar reglas de separación',
        description=(
            'Retorna todas las reglas registradas en el catálogo.\n\n'
            'ACC-005 `view_separation_rules` requerido.\n\n'
            '**CA-01**: listado ordenado por `code`.'
        ),
        tags=[_TAG],
        responses={200: _rule_list_schema()},
    )
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

    @extend_schema(
        operation_id='separation_rule_create',
        summary='UC_ACC_05 — Crear regla de separación',
        description=(
            'Crea una nueva regla en el catálogo.\n\n'
            'ACC-011 `update_separation_rule` requerido.\n\n'
            '**CA-03**: exitoso → state=ENABLED, AuditEvent SEPARATION_RULE_CREATED.\n'
            '**CA-04**: código duplicado → 409 SEPARATION_RULE_DUPLICATE.\n'
            '**CA-05**: con violaciones → 201 + existing_violations_count > 0.\n'
            '**CA-06**: function inexistente o inactiva → 400 FUNCTION_NOT_FOUND.'
        ),
        tags=[_TAG],
        request=SeparationRuleCreateSerializer,
        responses={
            201: _rule_create_response_schema(),
            400: OpenApiResponse(description='VALIDATION_ERROR | FUNCTION_NOT_FOUND'),
            409: OpenApiResponse(description='SEPARATION_RULE_DUPLICATE'),
        },
    )
    def post(self, request):
        from apps.access.models import SeparationRule, Function, UserFunctionAssignment
        from apps.audit.services import AuditLogService

        ser = SeparationRuleCreateSerializer(data=request.data)
        if not ser.is_valid():
            return Response({'error': 'VALIDATION_ERROR', 'fields': ser.errors}, status=400)

        data = ser.validated_data
        code = data['code'].upper()

        # CA-04: duplicado
        if SeparationRule.objects.filter(code=code).exists():
            existing = SeparationRule.objects.get(code=code)
            return Response(
                {'error': 'SEPARATION_RULE_DUPLICATE', 'existing_rule_id': existing.pk},
                status=409,
            )

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
            violations_qs = UserFunctionAssignment.objects.filter(
                state='ACTIVE', function__code__in=codes_a,
                user__in=UserFunctionAssignment.objects.filter(
                    state='ACTIVE', function__code__in=codes_b
                ).values('user'),
            ).values_list('user_id', flat=True).distinct()
            violations_count = violations_qs.count()

            AuditLogService.emit(
                event_type='SEPARATION_RULE_CREATED',
                actor_user_id=request.user.pk,
                payload={'rule_code': code, 'existing_violations': violations_count},
            )

        return Response({
            'id': rule.pk, 'code': rule.code, 'state': rule.state,
            'existing_violations_count': violations_count,
        }, status=201)


# ---------------------------------------------------------------------------
# UC_ACC_05 — SeparationRuleDetailView
# ---------------------------------------------------------------------------

class SeparationRuleDetailView(APIView):
    """
    GET/PATCH/DELETE /api/access/separation-rules/{rule_id}/

    UC_ACC_05 — Detalle, modificación y retiro de regla de separación.
    CNST-010: permission_classes gestionado via get_permissions() con HasFunction.
    STD_008 FASE 3: URL separation-rules/ vigente desde 2026-05-13.
    """

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

    @extend_schema(
        operation_id='separation_rule_retrieve',
        summary='UC_ACC_05 — Detalle de regla de separación',
        description='Retorna el detalle completo de una regla por su id.\nACC-005 requerido.',
        tags=[_TAG],
        responses={
            200: _rule_detail_schema(),
            404: OpenApiResponse(description='SEPARATION_RULE_NOT_FOUND'),
        },
    )
    def get(self, request, rule_id):
        rule = self._get_rule(rule_id)
        if not rule:
            return Response({'error': 'SEPARATION_RULE_NOT_FOUND'}, status=404)
        return Response({
            'id': rule.pk, 'code': rule.code, 'name': rule.name,
            'state': rule.state, 'description': rule.description,
            'functions_set_a': list(rule.functions_set_a.values_list('code', flat=True)),
            'functions_set_b': list(rule.functions_set_b.values_list('code', flat=True)),
        })

    @extend_schema(
        operation_id='separation_rule_partial_update',
        summary='UC_ACC_05 — Modificar regla de separación',
        description=(
            'PATCH parcial — solo `name` y `description`.\n\n'
            '**CA-08**: `function_ids_a/b` son inmutables → 400 FUNCTION_IDS_IMMUTABLE.\n'
            'ACC-011 requerido.'
        ),
        tags=[_TAG],
        request=SeparationRulePatchSerializer,
        responses={
            200: _rule_patch_response_schema(),
            400: OpenApiResponse(description='VALIDATION_ERROR | FUNCTION_IDS_IMMUTABLE'),
            404: OpenApiResponse(description='SEPARATION_RULE_NOT_FOUND'),
        },
    )
    def patch(self, request, rule_id):
        from apps.audit.services import AuditLogService
        rule = self._get_rule(rule_id)
        if not rule:
            return Response({'error': 'SEPARATION_RULE_NOT_FOUND'}, status=404)

        # CA-08: function_ids inmutables
        if 'function_ids_a' in request.data or 'function_ids_b' in request.data:
            return Response({'error': 'FUNCTION_IDS_IMMUTABLE'}, status=400)

        ser = SeparationRulePatchSerializer(data=request.data, partial=True)
        if not ser.is_valid():
            return Response({'error': 'VALIDATION_ERROR', 'fields': ser.errors}, status=400)

        data = ser.validated_data
        changed = []
        if 'name' in data:
            rule.name = data['name']
            changed.append('name')
        if 'description' in data:
            rule.description = data['description']
            changed.append('description')
        if changed:
            rule.save(update_fields=changed)

        AuditLogService.emit(
            event_type='SEPARATION_RULE_UPDATED',
            actor_user_id=request.user.pk,
            payload={'rule_id': rule_id, 'fields_changed': changed},
        )
        return Response({
            'id': rule.pk, 'code': rule.code,
            'state': rule.state, 'fields_changed': changed,
        })

    @extend_schema(
        operation_id='separation_rule_destroy',
        summary='UC_ACC_05 — Retirar regla de separación',
        description=(
            'Baja lógica: state → DISABLED (BR-009: nunca DELETE).\n\n'
            '`retire_reason` requerido, mínimo 5 caracteres.\n'
            'ACC-012 requerido.'
        ),
        tags=[_TAG],
        request=SeparationRuleRetireSerializer,
        responses={
            200: _rule_retire_response_schema(),
            400: OpenApiResponse(description='VALIDATION_ERROR — retire_reason requerido'),
            404: OpenApiResponse(description='SEPARATION_RULE_NOT_FOUND'),
        },
    )
    def delete(self, request, rule_id):
        from apps.audit.services import AuditLogService
        rule = self._get_rule(rule_id)
        if not rule:
            return Response({'error': 'SEPARATION_RULE_NOT_FOUND'}, status=404)

        ser = SeparationRuleRetireSerializer(data=request.data)
        if not ser.is_valid():
            return Response(
                {'error': 'VALIDATION_ERROR', 'message': 'retire_reason requerido.'},
                status=400,
            )

        with transaction.atomic():
            rule.state = 'DISABLED'
            rule.save(update_fields=['state'])
            AuditLogService.emit(
                event_type='SEPARATION_RULE_DISABLED',
                actor_user_id=request.user.pk,
                payload={
                    'rule_id':      rule_id,
                    'retire_reason': ser.validated_data['retire_reason'],
                },
            )

        return Response({'message': f'Regla {rule.code} desactivada.', 'state': 'DISABLED'})
