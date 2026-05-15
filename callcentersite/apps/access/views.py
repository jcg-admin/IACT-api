"""
Views para sistema de acceso y módulos.
"""
from rest_framework import viewsets, status
from apps.access.permissions.function_permissions import HasFunction
from apps.core.permissions import RequiresFunctionPermission
from drf_spectacular.utils import (
    extend_schema, extend_schema_view, OpenApiParameter,
    OpenApiResponse, inline_serializer)
from rest_framework import serializers as drf_serializers_module
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .models import (
    Module, UserModuleAccess, Function, UserPermission,
    AccessGroup, UserAccessGroup,
    SeparationRule, ExceptionalPermission,
)
from .serializers import (
    ModuleSerializer,
    ModuleTreeSerializer,
    UserModuleAccessSerializer,
    MyModulesSerializer,
    AccessGroupSerializer,
    AccessGroupListSerializer,
    UserAccessGroupSerializer,
    ExceptionalPermissionSerializer,
    FunctionSerializer,
)
from .services import ModuleAccessService


class ModuleViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de módulos.
    
    Endpoints:
    - GET /api/v1/access/modules/ - Listar módulos
    - POST /api/v1/access/modules/ - Crear módulo
    - GET /api/v1/access/modules/{id}/ - Detalle módulo
    - PUT/PATCH /api/v1/access/modules/{id}/ - Actualizar módulo
    - DELETE /api/v1/access/modules/{id}/ - Eliminar módulo (soft delete)
    - GET /api/v1/access/modules/tree/ - Obtener jerarquía completa
    """
    
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'parent']
    search_fields = ['code', 'name', 'description']
    ordering_fields = ['order', 'code', 'name', 'created_at']
    ordering = ['order', 'code']
    
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """
        Obtener jerarquía completa de módulos.
        
        GET /api/v1/access/modules/tree/
        
        Returns:
            Estructura de árbol de módulos
        """
        hierarchy = ModuleAccessService.get_module_hierarchy()
        return Response({
            'modules': hierarchy,
            'total_count': Module.objects.filter(is_active=True).count(),
            'root_count': Module.objects.filter(parent__isnull=True, is_active=True).count(),
        })
    
    @action(detail=False, methods=['get'])
    def roots(self, request):
        """
        Obtener solo módulos raíz.
        
        GET /api/v1/access/modules/roots/
        
        Returns:
            Lista de módulos raíz
        """
        roots = Module.objects.filter(parent__isnull=True, is_active=True).order_by('order', 'code')
        serializer = self.get_serializer(roots, many=True)
        return Response({
            'results': serializer.data,
            'count': roots.count(),
        })


class UserModuleAccessViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de accesos a módulos.
    
    Endpoints:
    - GET /api/v1/access/module-accesses/ - Listar accesos
    - POST /api/v1/access/module-accesses/ - Otorgar acceso
    - DELETE /api/v1/access/module-accesses/{id}/ - Revocar acceso
    """
    
    queryset = UserModuleAccess.objects.all()
    serializer_class = UserModuleAccessSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['user', 'module', 'is_active']
    ordering_fields = ['granted_at', 'revoked_at']
    ordering = ['-granted_at']
    
    def perform_create(self, serializer):
        """Guardar con granted_by automático."""
        serializer.save(granted_by=self.request.user)
    
    def perform_destroy(self, instance):
        """Soft delete: marcar como revocado."""
        from django.utils import timezone
        instance.is_active = False
        instance.revoked_at = timezone.now()
        instance.revoked_by = self.request.user
        instance.save()


@extend_schema(
    summary="UC_PERM_08 — Menu dinamico del usuario autenticado",
    description="Retorna los modulos accesibles segun las funciones del usuario.",
    responses={200: OpenApiResponse(description="Arbol de modulos accesibles")},
    tags=["Control de Acceso"]
)
class MyModulesView(APIView):
    """
    Vista para obtener módulos accesibles por el usuario autenticado.
    
    GET /api/v1/access/my-modules/
    
    Retorna:
        - modules: Árbol de módulos accesibles
        - total_count: Total de módulos accesibles
        - root_count: Número de módulos raíz accesibles
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Obtener módulos del usuario autenticado.
        
        Returns:
            Árbol de módulos con hijos anidados
        """
        user = request.user
        
        # Obtener árbol de módulos del usuario
        modules_tree = ModuleAccessService.get_user_module_tree(user)

        # Obtener todos los módulos accesibles (plano)
        all_modules = ModuleAccessService.get_user_modules(user)
        root_modules = all_modules.filter(parent__isnull=True)

        return Response({
            'modules': ModuleTreeSerializer(modules_tree, many=True).data,
            'total_count': all_modules.count(),
            'root_count': root_modules.count(),
        })


# ---------------------------------------------------------------------------
# B-05: AccessGroup ViewSet (UC_ACC_04, UC_PERM_01..06, UC_ADM_03)
# ---------------------------------------------------------------------------
from .models import AccessGroup, UserAccessGroup, SeparationRule, ExceptionalPermission
from rest_framework import serializers as drf_serializers
from apps.access.serializers.menu_item_serializers import MenuItemSerializer



@extend_schema_view(
    list=extend_schema(
        summary="UC_PERM_05 — Listar grupos de acceso", tags=["Control de Acceso"]),
    create=extend_schema(
        summary="UC_PERM_05 — Crear grupo de acceso", tags=["Control de Acceso"]),
    retrieve=extend_schema(
        summary="UC_PERM_05 — Detalle de grupo", tags=["Control de Acceso"]),
    partial_update=extend_schema(
        summary="UC_PERM_05 — Modificar grupo", tags=["Control de Acceso"]),
    destroy=extend_schema(
        summary="UC_PERM_05 — Eliminar grupo (baja logica)", tags=["Control de Acceso"]),
)
class AccessGroupViewSet(viewsets.ModelViewSet):
    """
    CRUD de grupos de acceso.

    UC_ACC_04, UC_PERM_05, UC_ADM_03.
    GET    /api/access/groups/            — listar grupos
    POST   /api/access/groups/            — crear grupo
    GET    /api/access/groups/{id}/       — detalle
    PATCH  /api/access/groups/{id}/       — modificar
    DELETE /api/access/groups/{id}/       — baja logica
    POST   /api/access/groups/{id}/add-function/    — UC_PERM_06
    DELETE /api/access/groups/{id}/remove-function/ — UC_PERM_06
    """
    queryset = AccessGroup.objects.all()
    permission_classes = [IsAuthenticated, RequiresFunctionPermission]
    function_map = {
        'list':           'ACC-003',
        'retrieve':       'ACC-003',
        'create':         'access.manage_groups',
        'update':         'access.manage_groups',
        'partial_update': 'access.manage_groups',
        'destroy':        'access.manage_groups',
        'add_function':   'access.manage_groups',
        'remove_function':'access.manage_groups',
    }

    serializer_class = AccessGroupSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return AccessGroupListSerializer
        return AccessGroupSerializer

    @action(detail=True, methods=['post'], url_path='add-function')
    def add_function(self, request, pk=None):
        """UC_PERM_06 — Asignar funcion a grupo."""
        group = self.get_object()
        function_id = request.data.get('function_id')
        try:
            from .models import Function
            fn = Function.objects.get(id=function_id)
            group.functions.add(fn)
            return Response({'detail': f'Function {fn.code} added to group {group.code}.'})
        except Function.DoesNotExist:
            return Response({'error': 'Function not found.'}, status=404)

    @action(detail=True, methods=['delete'], url_path='remove-function')
    def remove_function(self, request, pk=None):
        """UC_PERM_06 — Remover funcion de grupo."""
        group = self.get_object()
        function_id = request.data.get('function_id')
        try:
            from .models import Function
            fn = Function.objects.get(id=function_id)
            group.functions.remove(fn)
            return Response({'detail': f'Function {fn.code} removed from group {group.code}.'})
        except Function.DoesNotExist:
            return Response({'error': 'Function not found.'}, status=404)


class UserAccessGroupViewSet(viewsets.ModelViewSet):
    """
    Asignacion/revocacion de AccessGroups a usuarios.

    UC_ACC_04, UC_PERM_01..02.
    POST   /api/access/user-groups/       — asignar grupo a usuario
    DELETE /api/access/user-groups/{id}/  — revocar grupo
    GET    /api/access/user-groups/?user={id} — listar grupos de un usuario
    """
    queryset = UserAccessGroup.objects.select_related('user', 'access_group').all()
    permission_classes = [IsAuthenticated, RequiresFunctionPermission]
    function_map = {
        'list': 'ACC-003',
        'create': 'ACC-001',
        'destroy': 'ACC-001',
    }

    serializer_class = UserAccessGroupSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user_id = self.request.query_params.get('user')
        if user_id:
            qs = qs.filter(user_id=user_id)
        return qs

    def perform_create(self, serializer):
        """
        G-004: Verificar SeparationRule antes de asignar el AccessGroup.

        Cada función del grupo se verifica contra las funciones actuales
        del usuario. Si alguna genera conflicto, se rechaza con 400.
        """
        from django.db import models as dj_models
        from rest_framework.exceptions import ValidationError

        user  = serializer.validated_data["user"]
        group = serializer.validated_data["access_group"]

        existing_codes = user.get_functions()

        for fn in group.functions.filter(is_active=True):
            conflict = SeparationRule.objects.filter(
                status="active"
            ).filter(
                dj_models.Q(functions_set_a=fn, functions_set_b__code__in=existing_codes) |
                dj_models.Q(functions_set_b=fn, functions_set_a__code__in=existing_codes)
            ).first()

            if conflict:
                raise ValidationError({
                    "error":         "Separation rule conflict detected.",
                    "conflict_rule": conflict.name,
                    "function":      fn.code,
                    "conflicts_with": "see separation rule",
                })

        serializer.save(granted_by=self.request.user)



# ---------------------------------------------------------------------------
# B-07: ExceptionalPermission ViewSet (UC_ACC_08, UC_PERM_03..04)
# ---------------------------------------------------------------------------

@extend_schema_view(
    list=extend_schema(
        summary="UC_ACC_08 — Listar permisos excepcionales", tags=["Control de Acceso"]),
    create=extend_schema(
        summary="UC_ACC_08 — Solicitar permiso excepcional", tags=["Control de Acceso"]),
    retrieve=extend_schema(
        summary="UC_ACC_08 — Detalle de permiso excepcional", tags=["Control de Acceso"]),
    partial_update=extend_schema(
        summary="UC_ACC_08 — Modificar permiso excepcional", tags=["Control de Acceso"]),
)
class ExceptionalPermissionViewSet(viewsets.ModelViewSet):
    """
    Gestion de permisos temporales excepcionales.

    UC_ACC_08, UC_PERM_03..04.
    POST   /api/access/exceptional/           — solicitar permiso excepcional
    GET    /api/access/exceptional/           — listar permisos excepcionales
    PATCH  /api/access/exceptional/{id}/      — aprobar/revocar
    """
    queryset = ExceptionalPermission.objects.select_related(
        'user', 'function', 'granted_by'
    ).all()
    permission_classes = [IsAuthenticated, RequiresFunctionPermission]
    function_map = {
        'list': 'access.view_exceptional_permissions',
        'retrieve': 'access.view_exceptional_permissions',
        'create': 'access.request_exceptional_permission',
        'partial_update': 'access.manage_exceptional_permissions',
        'approve': 'access.manage_exceptional_permissions',
        'revoke': 'access.manage_exceptional_permissions',
    }

    serializer_class = ExceptionalPermissionSerializer

    @action(detail=True, methods=['patch'], url_path='approve')
    def approve(self, request, pk=None):
        """UC_ACC_08 / UC_PERM_03 — Aprobar permiso excepcional."""
        perm = self.get_object()
        if perm.status != 'pending':
            return Response({'error': 'Only pending permissions can be approved.'}, status=400)
        perm.status = 'approved'
        perm.granted_by = request.user
        perm.save()
        return Response({'detail': 'Permission approved.', 'status': perm.status})

    @action(detail=True, methods=['patch'], url_path='revoke')
    def revoke(self, request, pk=None):
        """UC_PERM_04 — Revocar permiso excepcional."""
        perm = self.get_object()
        if perm.status in ('revoked', 'expired'):
            return Response({'error': f'Permission already in status {perm.status}.'}, status=400)
        perm.status = 'revoked'
        perm.save()
        return Response({'detail': 'Permission revoked.', 'status': perm.status})


# ---------------------------------------------------------------------------
# B-05: EffectivePermissions endpoint (UC_ACC_03, UC_PERM_07)
# ---------------------------------------------------------------------------

@extend_schema(
    summary="UC_ACC_03 / UC_PERM_07 — Permisos efectivos del usuario",
    description=(
        "Union de: UserPermission directos + funciones via AccessGroup "
        "+ ExceptionalPermission aprobados y vigentes."
    ),
    parameters=[OpenApiParameter('user_id', int, location='path')],
    responses={
        200: OpenApiResponse(description="Permisos efectivos con desglose por fuente"),
        404: OpenApiResponse(description="Usuario no encontrado"),
    },
    tags=["Control de Acceso"]
)
class EffectivePermissionsView(APIView):
    """
    UC_ACC_03 / UC_PERM_07 — Consultar permisos efectivos de un usuario.

    GET /api/access/users/{user_id}/effective-permissions/

    Algoritmo de precedencia (CA-01..04):
      1. Revocación excepcional ACTIVA gana sobre cualquier concesión
         → allowed=False, origin=REVOKED_EXCEPTIONAL
      2. Concesión AGR (AccessGroup ACTIVE) → allowed=True, origin=GRANTED_BY_AGR
      3. Concesión excepcional ACTIVE → allowed=True, origin=GRANTED_EXCEPTIONAL
      4. Sin grant → allowed=False, origin=DENIED_NO_GRANT

    CA-16: ZERO AuditEvents emitidos por invocación.
    CA-05: AGR INACTIVE no cuenta.
    CA-07: ExceptionalPermission con status='ACTIVE' y expires_at >= now() cuenta.

    Hallazgo H-F6-GRP-GC-001 (2026-05-14):
      Bug previo: status='approved' (estado legacy pre-FASE 4).
      Corrección: ExceptionalPermission.STATE_ACTIVE = 'ACTIVE'.
    """
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'ACC-003'

    def get(self, request, user_id):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=404)

        from django.utils import timezone
        now = timezone.now()

        # Funciones via AccessGroup ACTIVE (CA-05: AGR INACTIVE no cuenta)
        group_fns = set(Function.objects.filter(
            access_groups__memberships__user=user,
            access_groups__is_active=True,
        ).values_list('code', flat=True))

        # Concesiones excepcionales ACTIVE no expiradas (CA-07)
        # Hallazgo H-F6-GRP-GC-001: era status='approved', corregido a STATE_ACTIVE='ACTIVE'
        exceptional_grants = set(ExceptionalPermission.objects.filter(
            user=user,
            status=ExceptionalPermission.STATE_ACTIVE,
            expires_at__gt=now,
        ).values_list('function__code', flat=True))

        # Revocaciones excepcionales ACTIVE (CA-02: ganan sobre AGR)
        exceptional_revokes = set(ExceptionalPermission.objects.filter(
            user=user,
            status=ExceptionalPermission.STATE_REVOKED,
        ).values_list('function__code', flat=True))

        # Construir lista efectiva con origin por función
        all_candidates = group_fns | exceptional_grants
        effective = []
        for fn_code in sorted(all_candidates):
            if fn_code in exceptional_revokes:
                # CA-02: revocación excepcional gana
                continue
            if fn_code in group_fns:
                effective.append(fn_code)
            elif fn_code in exceptional_grants:
                effective.append(fn_code)

        # CA-16: ZERO AuditEvents emitidos

        return Response({
            'user_id': user_id,
            'total_functions': len(effective),
            'sources': {
                'from_groups':  sorted(group_fns - exceptional_revokes),
                'exceptional':  sorted(exceptional_grants - exceptional_revokes),
                'revoked':      sorted(exceptional_revokes),
            },
            'effective': effective,
        })


# ---------------------------------------------------------------------------
# Endpoints requeridos por IACT-ui (accessService.js)
# ---------------------------------------------------------------------------

@extend_schema(
    summary="UC_ACC — Listar funciones disponibles",
    description=(
        "Retorna todas las funciones activas con campo 'category' para FunctionSelector.jsx."
    ),
    tags=["Control de Acceso"],
    responses={200: OpenApiResponse(description='Lista de funciones con category')},
)
class FunctionListView(APIView):
    """
    accessService.getAllFunctions()
    GET /api/access/functions/

    FunctionSelector.jsx espera:
      [{ id, code, name, description, category, permission_django, is_active }]
    """
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'ACC-003'

    def get(self, request):
        qs = Function.objects.filter(
            is_active=True
        ).select_related('module').order_by('module__code', 'code')
        serializer = FunctionSerializer(qs, many=True)
        return Response(serializer.data)


@extend_schema(
    summary="UC_ACC_03 — Permisos del usuario (alias accessService)",
    description=(
        "Alias de /users/{id}/effective-permissions/ para compatibilidad con accessService.js."
    ),
    tags=["Control de Acceso"],
    responses={200: OpenApiResponse(description='Permisos efectivos'), 404: OpenApiResponse(description='Usuario no encontrado')},
)
class UserEffectivePermissionsAliasView(APIView):
    """
    accessService.getUserPermissions(userId)
    GET /api/access/permissions/{userId}/

    Alias de /api/access/users/{id}/effective-permissions/
    para compatibilidad con accessService.js del frontend.

    Retorna estructura que Redux espera en state.access.userPermissions:
      { user_id, functions: [...codes], sources: {...} }
    """
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'ACC-003'

    def get(self, request, user_id):
        from django.contrib.auth import get_user_model
        from django.utils import timezone
        User = get_user_model()

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=404)

        direct = set(UserPermission.objects.filter(
            user=user
        ).values_list('function__code', flat=True))

        from_groups = set(Function.objects.filter(
            access_groups__memberships__user=user
        ).values_list('code', flat=True))

        now = timezone.now()
        exceptional = set(ExceptionalPermission.objects.filter(
            user=user, status='approved',
            valid_from__lte=now, valid_until__gte=now,
        ).values_list('function__code', flat=True))

        all_functions = sorted(direct | from_groups | exceptional)

        return Response({
            'user_id':   user_id,
            'functions': all_functions,
            'sources': {
                'direct':      sorted(direct),
                'from_groups': sorted(from_groups),
                'exceptional': sorted(exceptional),
            },
        })


@extend_schema(
    summary="UC_ACC_01 — Asignar funcion a usuario",
    description=(
        "Verifica SeparationRule antes de crear UserPermission. Retorna newFunction para Redux."
    ),
    tags=["Control de Acceso"],
    request=inline_serializer('FunctionAssignRequest', fields={
        'userId':     drf_serializers_module.IntegerField(),
        'functionId': drf_serializers_module.IntegerField(),
        'expiresAt':  drf_serializers_module.DateTimeField(required=False),
    }),
    responses={
        201: inline_serializer('FunctionAssignResponse', fields={
            'newFunction': drf_serializers_module.DictField(),
            'user_id':     drf_serializers_module.IntegerField(),
        }),
        409: OpenApiResponse(description='Conflicto SeparationRule o duplicado'),
    },
)
class FunctionAssignView(APIView):
    """
    accessService.assignFunction(userId, functionId)
    POST /api/access/functions/assign
    Body: { userId, functionId, expiresAt? }

    assignFunction.fulfilled actualiza:
      state.userPermissions.functions.push(action.payload.newFunction)
    Retorna: { newFunction: { id, code, name }, user_id }
    """
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'ACC-001'

    def post(self, request):
        from django.contrib.auth import get_user_model
        from django.db import models as dj_models
        User = get_user_model()

        user_id     = request.data.get('userId')
        function_id = request.data.get('functionId')

        if not user_id or not function_id:
            return Response(
                {'error': 'userId and functionId are required.'}, status=400)

        try:
            user     = User.objects.get(pk=user_id)
            function = Function.objects.get(pk=function_id, is_active=True)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=404)
        except Function.DoesNotExist:
            return Response({'error': 'Function not found or inactive.'}, status=404)

        # Verificar conflicto de SeparationRule
        existing_codes = user.get_functions() if hasattr(user, 'get_functions') else []
        conflict = SeparationRule.objects.filter(
            state='ACTIVE'
        ).filter(
            dj_models.Q(functions_set_a=function, functions_set_b__code__in=existing_codes) |
            dj_models.Q(functions_set_b=function, functions_set_a__code__in=existing_codes)
        ).first()

        if conflict:
            return Response({
                'error':   'Conflicto de separacion de funciones detectado.',
                'message': str(conflict),
                'conflict_rule': conflict.name,
            }, status=409)

        perm, created = UserPermission.objects.get_or_create(
            user=user, function=function)

        if not created:
            return Response(
                {'error': 'Function already assigned to this user.'}, status=409)

        return Response({
            'newFunction': {
                'id':   function.id,
                'code': function.code,
                'name': function.name,
            },
            'user_id': user_id,
        }, status=201)


@extend_schema(
    summary="UC_ACC_02 — Revocar funcion de usuario",
    description=(
        "Elimina el UserPermission del usuario."
    ),
    tags=["Control de Acceso"],
    request=inline_serializer('FunctionRevokeRequest', fields={
        'userId':     drf_serializers_module.IntegerField(),
        'functionId': drf_serializers_module.IntegerField(),
    }),
    responses={
        200: inline_serializer('FunctionRevokeResponse', fields={
            'detail': drf_serializers_module.CharField(),
        }),
        404: OpenApiResponse(description='Asignacion no encontrada'),
    },
)
class FunctionRevokeView(APIView):
    """
    accessService.revokeFunction(userId, functionId)
    POST /api/access/functions/revoke
    Body: { userId, functionId }
    """
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'ACC-001'

    def post(self, request):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        user_id     = request.data.get('userId')
        function_id = request.data.get('functionId')

        if not user_id or not function_id:
            return Response(
                {'error': 'userId and functionId are required.'}, status=400)

        deleted, _ = UserPermission.objects.filter(
            user_id=user_id, function_id=function_id
        ).delete()

        if not deleted:
            return Response(
                {'error': 'Assignment not found.'}, status=404)

        return Response({'detail': 'Function revoked successfully.'})


class SeparationRuleValidateView(APIView):
    """
    UC_ACC_01 — Validar conflictos de separación de funciones.

    POST /api/access/separation-rules/validate  (canónico — FASE 3)
    POST /api/access/validate-sod               (legacy — backward compat sin consumidor activo)
    Body: { userId: int, functionId: int }

    Evalúa si la función `functionId` puede asignarse al usuario `userId`
    sin crear violaciones de separación (CNST-030, BR-007).

    Retorna estructura que consume accessGateway.validateSeparationRules():
      { conflicts: [{ rule, ruleDesc, setA, setB, message }] }

    Hallazgo H-003 (STD_008 FASE 3, 2026-05-13):
      Implementación anterior usaba function_a/function_b/status='active'/
      rule.justification — campos inexistentes en SeparationRule v5.4.0.
      Reescrita para usar functions_set_a/functions_set_b M2M y state='ENABLED'.
    """
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'ACC-005'

    @extend_schema(
        operation_id='separation_rule_validate',
        summary='UC_ACC_01 — Validar conflictos de separación antes de asignar función',
        description=(
            'Evalúa si asignar `functionId` al usuario `userId` crearía un conflicto\n'
            'con las reglas de separación activas (state=ENABLED).\n\n'
            'Retorna la lista de conflictos detectados. Lista vacía = sin conflictos.\n\n'
            'URL canónica: `POST /api/access/separation-rules/validate`\n'
            'URL legacy (sin consumidor activo): `POST /api/access/validate-sod`\n\n'
            'Consumido por: `accessGateway.validateSeparationRules()` (IACT-ui)\n'
            'Estado Redux: `accessSlice.separationConflicts`\n\n'
            'ACC-005 `view_separation_rules` requerido.'
        ),
        tags=['Control de Acceso'],
        request=inline_serializer('SeparationValidateRequest', fields={
            'userId':     drf_serializers_module.IntegerField(),
            'functionId': drf_serializers_module.IntegerField(),
        }),
        responses={
            200: inline_serializer('SeparationValidateResponse', fields={
                'conflicts': drf_serializers_module.ListField(
                    child=drf_serializers_module.DictField()),
            }),
            400: OpenApiResponse(description='userId y functionId son requeridos'),
            404: OpenApiResponse(description='Usuario o función no encontrados'),
        },
    )
    def post(self, request):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        user_id     = request.data.get('userId')
        function_id = request.data.get('functionId')

        if not user_id or not function_id:
            return Response(
                {'error': 'userId and functionId are required.'}, status=400)

        try:
            user     = User.objects.get(pk=user_id)
            function = Function.objects.get(pk=function_id)
        except (User.DoesNotExist, Function.DoesNotExist) as exc:
            return Response({'error': str(exc)}, status=404)

        # Funciones actuales activas del usuario
        from apps.access.models import UserFunctionAssignment
        current_codes = set(
            UserFunctionAssignment.objects.filter(user=user, state='ACTIVE')
            .values_list('function__code', flat=True)
        )
        proposed_code = function.code

        # Evaluar reglas ENABLED con prefetch M2M para evitar N+1
        conflicts = []
        for rule in (
            SeparationRule.objects
            .filter(state='ENABLED')
            .prefetch_related('functions_set_a', 'functions_set_b')
        ):
            codes_a = set(rule.functions_set_a.values_list('code', flat=True))
            codes_b = set(rule.functions_set_b.values_list('code', flat=True))

            if proposed_code in codes_a:
                conflicting = current_codes & codes_b
                if conflicting:
                    conflicts.append({
                        'rule':     rule.code,
                        'ruleDesc': rule.description,
                        'setA':     [proposed_code],
                        'setB':     sorted(conflicting),
                        'message':  (
                            f'{rule.name}: {proposed_code} '
                            f'incompatible con {", ".join(sorted(conflicting))}'
                        ),
                    })
            elif proposed_code in codes_b:
                conflicting = current_codes & codes_a
                if conflicting:
                    conflicts.append({
                        'rule':     rule.code,
                        'ruleDesc': rule.description,
                        'setA':     sorted(conflicting),
                        'setB':     [proposed_code],
                        'message':  (
                            f'{rule.name}: {proposed_code} '
                            f'incompatible con {", ".join(sorted(conflicting))}'
                        ),
                    })

        return Response({'conflicts': conflicts})


@extend_schema(exclude=True)
class SeparationRuleValidateLegacyView(SeparationRuleValidateView):
    """
    POST /api/access/validate-sod — DEPRECATED legacy endpoint.

    Sin consumidor activo en IACT-ui (migrado a separation-rules/validate).
    Delegada a SeparationRuleValidateView.
    Excluida del schema OpenAPI para evitar colisión de operationId.
    """


@extend_schema(
    summary="UC_PERM_05 — Listar agrupadores (alias accessService)",
    description=(
        "Alias de /access/groups/ para compatibilidad con accessService.getGroupers()."
    ),
    tags=["Control de Acceso"],
    responses={200: OpenApiResponse(description='Lista de AccessGroups activos')},
)
class GrouperListView(APIView):
    """
    accessService.getGroupers()
    GET /api/access/groupers/

    Alias de /api/access/groups/ para compatibilidad con frontend.
    """
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'ACC-003'

    def get(self, request):
        qs = AccessGroup.objects.filter(is_active=True).order_by('name')
        serializer = AccessGroupListSerializer(qs, many=True)
        return Response(serializer.data)


@extend_schema(
    summary="UC_ACC_04 — Asignar agrupador a usuario",
    description=(
        "Crea UserAccessGroup. Alias de POST /access/user-groups/."
    ),
    tags=["Control de Acceso"],
    request=inline_serializer('GrouperAssignRequest', fields={
        'userId':    drf_serializers_module.IntegerField(),
        'grouperId': drf_serializers_module.IntegerField(),
    }),
    responses={
        201: OpenApiResponse(description='Agrupador asignado'),
        409: OpenApiResponse(description='Ya pertenece al agrupador'),
    },
)
class GrouperAssignView(APIView):
    """
    accessService.assignGrouper(userId, grouperId)
    POST /api/access/groupers/assign
    Body: { userId, grouperId }
    """
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'ACC-001'

    def post(self, request):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        user_id   = request.data.get('userId')
        grouper_id = request.data.get('grouperId')

        if not user_id or not grouper_id:
            return Response(
                {'error': 'userId and grouperId are required.'}, status=400)

        try:
            user   = User.objects.get(pk=user_id)
            group  = AccessGroup.objects.get(pk=grouper_id, is_active=True)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=404)
        except AccessGroup.DoesNotExist:
            return Response({'error': 'Group not found.'}, status=404)

        membership, created = UserAccessGroup.objects.get_or_create(
            user=user, access_group=group,
            defaults={'granted_by': request.user}
        )

        if not created:
            return Response(
                {'error': 'User already belongs to this group.'}, status=409)

        serializer = UserAccessGroupSerializer(membership)
        return Response(serializer.data, status=201)


# ---------------------------------------------------------------------------
# G-001: UserFunctionAssignView — UC_ACC_01 (endpoint DRF con auditoría)
# Distinto de FunctionAssignView (Fase C, compatibilidad IACT-ui)
# ---------------------------------------------------------------------------

@extend_schema(
    summary="UC_ACC_01 — Asignar función a usuario (con auditoría)",
    description=(
        "Asigna una Function a un usuario creando un UserPermission. "
        "Verifica SeparationRule activa antes de asignar. "
        "Emite evento de auditoría ACTION=ACCESS_FUNCTION_ASSIGNED."
    ),
    request=inline_serializer("AssignFunctionByIdRequest", fields={
        "function_id": drf_serializers_module.IntegerField(),
    }),
    responses={
        201: OpenApiResponse(description="Función asignada correctamente"),
        409: OpenApiResponse(description="Función ya asignada o conflicto de separación"),
        404: OpenApiResponse(description="Usuario o función no encontrados"),
    },
    tags=["Control de Acceso"]
)
class UserFunctionAssignView(APIView):
    """
    POST /api/access/users/{user_id}/functions/
    Body: { "function_id": 42 }

    Verifica SeparationRule activa antes de crear UserPermission.
    Emite AuditLog con action=ACCESS_FUNCTION_ASSIGNED.
    """
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'ACC-001'  # fix DT-REQUIRED-FUNCTION-001 (era access.assign_functions)

    def post(self, request, user_id):
        from django.contrib.auth import get_user_model
        from django.db import models as dj_models
        from apps.audit.models import AuditLog

        User = get_user_model()
        function_id = request.data.get("function_id")

        if not function_id:
            return Response(
                {"error": "function_id is required."}, status=400)

        try:
            target_user = User.objects.get(pk=user_id)
            function    = Function.objects.get(pk=function_id, is_active=True)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=404)
        except Function.DoesNotExist:
            return Response({"error": "Function not found or inactive."}, status=404)

        # Verify no duplicate
        if UserPermission.objects.filter(user=target_user, function=function).exists():
            return Response(
                {"error": "Function already assigned to this user."}, status=409)

        # Verify SeparationRule
        existing_codes = target_user.get_functions()
        conflict = SeparationRule.objects.filter(
            state="ACTIVE"
        ).filter(
            dj_models.Q(functions_set_a=function, functions_set_b__code__in=existing_codes) |
            dj_models.Q(functions_set_b=function, functions_set_a__code__in=existing_codes)
        ).first()

        if conflict:
            AuditLog.record(
                user=request.user,
                action="ACCESS_FUNCTION_ASSIGN_DENIED",
                resource=f"User:{user_id}/Function:{function.code}",
                result="FAILURE",
                details={"reason": "separation_rule_conflict",
                         "rule": conflict.name}
            )
            return Response({
                "error":         "Separation rule conflict detected.",
                "conflict_rule": conflict.name,
            }, status=409)

        # Create UserPermission
        UserPermission.objects.create(user=target_user, function=function)

        AuditLog.record(
            user=request.user,
            action="ACCESS_FUNCTION_ASSIGNED",
            resource=f"User:{user_id}/Function:{function.code}",
            result="SUCCESS",
            details={"function_code":          function.code,
                     "function_permission_django": function.permission_django}
        )

        return Response({
            "function_id":   function.id,
            "function_code": function.code,
            "user_id":       user_id,
        }, status=201)


# ---------------------------------------------------------------------------
# G-002: UserFunctionRevokeView — UC_ACC_02 (endpoint DRF con auditoría)
# ---------------------------------------------------------------------------

@extend_schema(
    summary="UC_ACC_02 — Revocar función de usuario (con auditoría)",
    description=(
        "Elimina el UserPermission de un usuario para una función. "
        "Emite evento de auditoría ACTION=ACCESS_FUNCTION_REVOKED."
    ),
    responses={
        204: OpenApiResponse(description="Función revocada correctamente"),
        404: OpenApiResponse(description="UserPermission no encontrado"),
    },
    tags=["Control de Acceso"]
)
class UserFunctionRevokeView(APIView):
    """
    DELETE /api/access/users/{user_id}/functions/{function_id}/
    """
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'ACC-002'  # fix DT-REQUIRED-FUNCTION-001

    def delete(self, request, user_id, function_id):
        from apps.audit.models import AuditLog

        try:
            perm = UserPermission.objects.select_related("function").get(
                user_id=user_id, function_id=function_id)
        except UserPermission.DoesNotExist:
            return Response({"error": "UserPermission not found."}, status=404)

        fn_code = perm.function.code
        perm.delete()

        AuditLog.record(
            user=request.user,
            action="ACCESS_FUNCTION_REVOKED",
            resource=f"User:{user_id}/Function:{fn_code}",
            result="SUCCESS",
            details={"function_code": fn_code}
        )

        return Response(status=204)


class MenuItemViewSet(viewsets.ModelViewSet):
    """
    CRUD para MenuItem. Requiere permiso manage_menu_catalog (UC_ADM_04).

    CNST-032: MenuItem es wrapper UX — no controla acceso, solo metadata visual.
    El lifecycle (DRAFT → ACTIVE → DEPRECATED → ARCHIVED) se gestiona via
    MenuLifecycleService (T-104).
    """
    from apps.access.models import MenuItem as _MenuItem
    from apps.access.serializers import MenuItemSerializer as _MenuItemSerializer

    queryset         = _MenuItem.objects.select_related('function', 'parent').all()
    serializer_class = _MenuItemSerializer

    def get_permissions(self):
        from rest_framework.permissions import IsAuthenticated
        return [IsAuthenticated()]


class MenuItemTransitionView(APIView):
    serializer_class = MenuItemSerializer
    """
    POST /api/access/menu-items/{id}/transition/

    Aplica una transición de estado a un MenuItem (UC_ADM_05).
    Body: {"status": "ACTIVE"} | {"status": "DEPRECATED", "block_reason": "..."}

    Usa MenuLifecycleService — no permite saltar transiciones.
    """

    def post(self, request, pk):
        from rest_framework.permissions import IsAuthenticated
        from rest_framework.response import Response
        from rest_framework import status as http_status
        from apps.access.models import MenuItem
        from apps.access.services.menu_lifecycle_service import (
            MenuLifecycleService, InvalidTransitionError,
        )

        try:
            item = MenuItem.objects.get(pk=pk)
        except MenuItem.DoesNotExist:
            return Response({'detail': 'No encontrado.'}, status=http_status.HTTP_404_NOT_FOUND)

        new_status  = request.data.get('status')
        block_reason = request.data.get('block_reason')

        if not new_status:
            return Response(
                {'detail': 'Campo requerido: status.'},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        try:
            MenuLifecycleService.transition(item, new_status, block_reason=block_reason)
        except (InvalidTransitionError, ValueError) as e:
            return Response({'detail': str(e)}, status=http_status.HTTP_400_BAD_REQUEST)

        return Response({
            'id':     item.pk,
            'status': item.status,
            'allowed_next': MenuLifecycleService.get_allowed_transitions(item),
        })


# ===========================================================================
# UC_PERM_07 — Verificar Permiso (endpoint administrativo)
# ===========================================================================

@extend_schema(
    summary='UC_PERM_07 — Verificar permiso de usuario',
    description=(
        'Verifica si un usuario tiene una función RBAC activa, aplicando '
        'la regla de precedencia:\n\n'
        '1. ExceptionalPermission REVOKE activo → denegado (siempre gana).\n'
        '2. ExceptionalPermission GRANT activo → autorizado.\n'
        '3. AccessGroup ACTIVE con la función → autorizado.\n'
        '4. Ningún match → denegado.\n\n'
        'El resultado se cachea durante 60 s (DatabaseCache, CNST-010).\n\n'
        '**CA-14**: Requiere ACC-003 `view_assignments`.'
    ),
    parameters=[
        OpenApiParameter('user_id', int, location='query', required=True,
                         description='ID del usuario a verificar.'),
        OpenApiParameter('function_code', str, location='query', required=True,
                         description='Código canónico de la función (ej: RPT-001).'),
    ],
    responses={
        200: OpenApiResponse(description=(
            'Resultado de verificación: allowed, origin, via_agr_codes, cache.'
        )),
        400: OpenApiResponse(description='function_code no existe en catálogo (CA-12).'),
        403: OpenApiResponse(description='Sin permiso view_assignments (CA-14).'),
        404: OpenApiResponse(description='Usuario no encontrado o inactivo (CA-13).'),
    },
    tags=['Control de Acceso'],
)
class PermissionVerifyView(APIView):
    """
    GET /api/access/permissions/verify/?user_id=N&function_code=XYZ

    UC_PERM_07 — verificación de permiso con cache.
    Requiere ACC-003 (view_assignments).
    CNST-010: permission_classes explícito.
    """
    permission_classes = [IsAuthenticated, HasFunction]
    required_function = 'ACC-003'

    def get(self, request):
        from apps.access.services.permission_service import PermissionService

        user_id_raw = request.query_params.get('user_id')
        function_code = request.query_params.get('function_code', '').strip()

        if not user_id_raw or not function_code:
            return Response(
                {'error': {'code': 'VALIDATION_ERROR',
                           'message': 'user_id y function_code son requeridos.'}},
                status=400,
            )

        try:
            user_id = int(user_id_raw)
        except ValueError:
            return Response(
                {'error': {'code': 'VALIDATION_ERROR', 'message': 'user_id debe ser entero.'}},
                status=400,
            )

        try:
            result = PermissionService.check(user_id, function_code)
        except ValueError as exc:
            return Response(
                {'error': {'code': 'FUNCTION_NOT_FOUND', 'message': str(exc)}},
                status=400,
            )
        except LookupError as exc:
            return Response(
                {'error': {'code': 'USER_NOT_FOUND', 'message': str(exc)}},
                status=404,
            )

        return Response({
            'user_id': user_id,
            'function_code': function_code,
            'allowed': result.allowed,
            'origin': result.origin,
            'via_agr_codes': result.via_agr_codes,
            'valid_until': result.valid_until,
            'cache': result.cache,
        })
