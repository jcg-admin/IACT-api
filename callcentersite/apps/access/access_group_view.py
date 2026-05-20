"""
apps/access/access_group_view.py

AccessGroupCRUDView — UC_PERM_05: Crear y gestionar Grupos de Funciones (AGR custom).

Fuente: uc-perm-05/criterios-aceptacion.rst § 9
Endpoint: /api/access/groups/

Acciones:
  POST   /api/access/groups/           — crear AGR custom (ACC-006)
  PATCH  /api/access/groups/{id}/      — modificar AGR (ACC-006)
  DELETE /api/access/groups/{id}/      — retirar AGR (BR-009 baja lógica) (ACC-006)
  GET    /api/access/groups/           — listar AGRs (ACC-005 view_separation_rules)
  GET    /api/access/groups/{id}/      — detalle AGR (ACC-005)
"""
from django.db import transaction, DatabaseError
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access.permissions.function_permissions import HasFunction
from apps.access.serializers.access_group_serializers import AccessGroupSerializer



# ---------------------------------------------------------------------------
# Serializers
# ---------------------------------------------------------------------------
class AccessGroupCreateSerializer(serializers.Serializer):
    code         = serializers.CharField(max_length=50)
    name         = serializers.CharField(max_length=100)
    description  = serializers.CharField(required=False, allow_blank=True, default='')
    initial_function_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, default=list,
    )


class AccessGroupPatchSerializer(serializers.Serializer):
    name         = serializers.CharField(max_length=100, required=False)
    description  = serializers.CharField(required=False, allow_blank=True)
    code         = serializers.CharField(required=False)  # detectar intento de cambio


class AccessGroupRetireSerializer(serializers.Serializer):
    retire_reason = serializers.CharField(min_length=5)


# ---------------------------------------------------------------------------
# AccessGroupListCreateView — GET / POST
# ---------------------------------------------------------------------------
@extend_schema(
    summary='UC_PERM_05 — Listar / Crear grupos de funciones (AGR)',
    description=(
        'GET: lista todos los AGRs activos (predefinidos + custom). '
        'ACC-005 view_separation_rules.\n\n'
        'POST: crea un AGR custom (is_predefined=False). '
        'ACC-006 create_function_group.\n\n'
        '**CA-01**: AGR creado con is_predefined=False.\n'
        '**CA-02**: code duplicado → 409.\n'
        '**CA-03**: format inválido → 400.\n'
        '**CA-04**: initial_function_ids → AccessGroupFunction delegado.'
    ),
    responses={
        200: OpenApiResponse(description='Lista de AGRs.'),
        201: OpenApiResponse(description='AGR creado.'),
        400: OpenApiResponse(description='Datos inválidos.'),
        409: OpenApiResponse(description='CODE_DUPLICATE.'),
    },
    tags=['Control de Acceso'],
)
@extend_schema_view(
    get=extend_schema(operation_id='access_group_list',
                      summary='UC_PERM_05 — Listar Access Groups',
                      tags=['Control de Acceso']),
)
class AccessGroupListCreateView(APIView):
    serializer_class = AccessGroupSerializer
    """GET/POST /api/access/groups/"""

    def get_permissions(self):
        if self.request.method == 'POST':
            self.required_function = 'ACC-006'
        else:
            self.required_function = 'ACC-005'
        return [IsAuthenticated(), HasFunction()]

    def get(self, request):
        from apps.access.models import AccessGroup
        qs = AccessGroup.objects.filter(is_active=True).order_by('code')
        return Response({
            'count': qs.count(),
            'results': [
                {
                    'id':           agr.pk,
                    'code':         agr.code,
                    'name':         agr.name,
                    'description':  agr.description,
                    'is_predefined': agr.is_predefined,
                    'function_count': agr.functions.count(),
                }
                for agr in qs
            ],
        })

    def post(self, request):
        from apps.access.models import AccessGroup, Function
        from apps.audit.services import AuditLogService
        import re

        ser = AccessGroupCreateSerializer(data=request.data)
        if not ser.is_valid():
            return Response({'error': 'VALIDATION_ERROR', 'fields': ser.errors}, status=400)

        data = ser.validated_data
        code = data['code'].upper()

        # CA-03: validar formato de code
        if not re.match(r'^[A-Z][A-Z0-9_-]{1,49}$', code):
            return Response(
                {'error': 'VALIDATION_ERROR', 'message': 'Code debe ser UPPER_SNAKE_CASE.'},
                status=400,
            )

        # CA-02: code duplicado
        if AccessGroup.objects.filter(code=code).exists():
            return Response({'error': 'CODE_DUPLICATE', 'message': f'El code {code!r} ya existe.'}, status=409)

        try:
            with transaction.atomic():
                agr = AccessGroup.objects.create(
                    code=code,
                    name=data['name'],
                    description=data.get('description', ''),
                    is_predefined=False,
                    is_active=True,
                )
                # CA-04: initial_function_ids
                fn_ids = data.get('initial_function_ids', [])
                if fn_ids:
                    fns = Function.objects.filter(pk__in=fn_ids, is_active=True)
                    agr.functions.set(fns)

                ip_admin = (
                    request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
                    or request.META.get('REMOTE_ADDR', '')
                ) or None
                # FR-016.01: audit canonico de creacion AGR
                AuditLogService.emit(
                    event_type='ACCESS_GROUP_CREATED',
                    actor_user_id=request.user.pk,
                    target_entity_type='AccessGroup',
                    target_entity_id=str(agr.pk),
                    ip_address=ip_admin,
                    payload={
                        'agr_code': code,
                        'agr_id': agr.pk,
                        'function_count': len(fn_ids),
                        'initial_function_ids': fn_ids,
                    },
                )
        except DatabaseError:
            return Response({'error': 'DB_TIMEOUT'}, status=500)

        return Response({
            'id':            agr.pk,
            'code':          agr.code,
            'name':          agr.name,
            'is_predefined': False,
            'function_count': agr.functions.count(),
        }, status=201)


# ---------------------------------------------------------------------------
# AccessGroupDetailView — PATCH / DELETE
# ---------------------------------------------------------------------------
@extend_schema(
    summary='UC_PERM_05 — Modificar o retirar AGR custom',
    description=(
        'PATCH: modifica display_name o description. ACC-006.\n\n'
        'DELETE: retira el AGR (BR-009 baja lógica — is_active=False). ACC-006.\n\n'
        '**CA-05**: PATCH parcial — solo name/description.\n'
        '**CA-06**: code es inmutable → 400 CODE_IMMUTABLE.\n'
        '**CA-07**: predefinido → 400 PREDEFINED_NOT_MUTABLE.\n'
        '**CA-08**: retirar exitoso → is_active=False.'
    ),
    tags=['Control de Acceso'],
)
class AccessGroupDetailView(APIView):
    serializer_class = AccessGroupSerializer
    """PATCH/DELETE /api/access/groups/{agr_id}/"""
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'ACC-006'

    def _get_agr(self, agr_id):
        from apps.access.models import AccessGroup
        try:
            return AccessGroup.objects.get(pk=agr_id)
        except AccessGroup.DoesNotExist:
            return None

    def get(self, request, agr_id):
        agr = self._get_agr(agr_id)
        if not agr:
            return Response({'error': 'ACCESS_GROUP_NOT_FOUND'}, status=404)
        return Response({
            'id': agr.pk, 'code': agr.code, 'name': agr.name,
            'description': agr.description, 'is_predefined': agr.is_predefined,
            'is_active': agr.is_active,
            'function_count': agr.functions.count(),
        })

    def patch(self, request, agr_id):
        from apps.audit.services import AuditLogService
        agr = self._get_agr(agr_id)
        if not agr:
            return Response({'error': 'ACCESS_GROUP_NOT_FOUND'}, status=404)

        # CA-07: predefinido no mutable
        if agr.is_predefined:
            return Response({'error': 'PREDEFINED_NOT_MUTABLE'}, status=400)

        ser = AccessGroupPatchSerializer(data=request.data)
        if not ser.is_valid():
            return Response({'error': 'VALIDATION_ERROR', 'fields': ser.errors}, status=400)

        data = ser.validated_data

        # CA-06: code inmutable
        if 'code' in request.data:
            return Response({'error': 'CODE_IMMUTABLE', 'message': 'El code no puede modificarse.'}, status=400)

        changed = []
        if 'name' in data:
            agr.name = data['name']
            changed.append('name')
        if 'description' in data:
            agr.description = data['description']
            changed.append('description')

        agr.save(update_fields=changed) if changed else None

        ip_admin = (
            request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
            or request.META.get('REMOTE_ADDR', '')
        ) or None
        # FR-016.02: audit canonico de modificacion AGR
        AuditLogService.emit(
            event_type='ACCESS_GROUP_MODIFIED',
            actor_user_id=request.user.pk,
            target_entity_type='AccessGroup',
            target_entity_id=str(agr_id),
            ip_address=ip_admin,
            payload={'agr_id': agr_id, 'fields_changed': changed},
        )
        return Response({'id': agr.pk, 'code': agr.code, 'name': agr.name, 'fields_changed': changed})

    def delete(self, request, agr_id):
        from apps.audit.services import AuditLogService
        agr = self._get_agr(agr_id)
        if not agr:
            return Response({'error': 'ACCESS_GROUP_NOT_FOUND'}, status=404)

        # CA-07: predefinido no mutable
        if agr.is_predefined:
            return Response({'error': 'PREDEFINED_NOT_MUTABLE'}, status=400)

        ser = AccessGroupRetireSerializer(data=request.data)
        if not ser.is_valid():
            return Response({'error': 'VALIDATION_ERROR', 'message': 'retire_reason requerido.'}, status=400)

        with transaction.atomic():
            agr.is_active = False
            agr.retired_at = timezone.now()
            agr.retire_reason = ser.validated_data['retire_reason']
            agr.save(update_fields=['is_active', 'retired_at', 'retire_reason'])

            ip_admin = (
                request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
                or request.META.get('REMOTE_ADDR', '')
            ) or None
            # FR-016.03: audit canonico de retiro AGR
            AuditLogService.emit(
                event_type='ACCESS_GROUP_RETIRED',
                actor_user_id=request.user.pk,
                target_entity_type='AccessGroup',
                target_entity_id=str(agr_id),
                ip_address=ip_admin,
                payload={'agr_id': agr_id, 'retire_reason': ser.validated_data['retire_reason']},
            )

        return Response({'message': f'AGR {agr.code} retirado.', 'retired_at': agr.retired_at.isoformat()})
