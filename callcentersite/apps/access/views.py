"""
Views para sistema de acceso y módulos.
"""
from rest_framework import viewsets, status
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
    SeparationRuleSerializer,
    SeparationRuleCheckSerializer,
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
            'modules': modules_tree,
            'total_count': all_modules.count(),
            'root_count': root_modules.count(),
        })


# ---------------------------------------------------------------------------
# B-05: AccessGroup ViewSet (UC_ACC_04, UC_PERM_01..06, UC_ADM_03)
# ---------------------------------------------------------------------------
from .models import AccessGroup, UserAccessGroup, SeparationRule, ExceptionalPermission
from rest_framework import serializers as drf_serializers


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
    permission_classes = [IsAuthenticated]

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
            return Response({'detail': f'Funcion {fn.code} agregada al grupo {group.code}.'})
        except Function.DoesNotExist:
            return Response({'error': 'Funcion no encontrada.'}, status=404)

    @action(detail=True, methods=['delete'], url_path='remove-function')
    def remove_function(self, request, pk=None):
        """UC_PERM_06 — Remover funcion de grupo."""
        group = self.get_object()
        function_id = request.data.get('function_id')
        try:
            from .models import Function
            fn = Function.objects.get(id=function_id)
            group.functions.remove(fn)
            return Response({'detail': f'Funcion {fn.code} removida del grupo {group.code}.'})
        except Function.DoesNotExist:
            return Response({'error': 'Funcion no encontrada.'}, status=404)


class UserAccessGroupViewSet(viewsets.ModelViewSet):
    """
    Asignacion/revocacion de AccessGroups a usuarios.

    UC_ACC_04, UC_PERM_01..02.
    POST   /api/access/user-groups/       — asignar grupo a usuario
    DELETE /api/access/user-groups/{id}/  — revocar grupo
    GET    /api/access/user-groups/?user={id} — listar grupos de un usuario
    """
    queryset = UserAccessGroup.objects.select_related('user', 'access_group').all()
    permission_classes = [IsAuthenticated]

    serializer_class = UserAccessGroupSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user_id = self.request.query_params.get('user')
        if user_id:
            qs = qs.filter(user_id=user_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(granted_by=self.request.user)


# ---------------------------------------------------------------------------
# B-05: SeparationRule ViewSet (UC_ACC_05, UC_ADM_01)
# ---------------------------------------------------------------------------

@extend_schema_view(
    list=extend_schema(
        summary="UC_ACC_05 — Listar reglas de separacion", tags=["Control de Acceso"]),
    create=extend_schema(
        summary="UC_ACC_05 — Crear regla de separacion", tags=["Control de Acceso"]),
    retrieve=extend_schema(
        summary="UC_ACC_05 — Detalle de regla", tags=["Control de Acceso"]),
    partial_update=extend_schema(
        summary="UC_ACC_05 — Modificar regla", tags=["Control de Acceso"]),
    destroy=extend_schema(
        summary="UC_ACC_05 — Eliminar regla", tags=["Control de Acceso"]),
)
class SeparationRuleViewSet(viewsets.ModelViewSet):
    """
    CRUD de reglas de Separacion de Deberes.

    UC_ACC_05, UC_ADM_01.
    GET    /api/access/separation-rules/  — listar reglas
    POST   /api/access/separation-rules/  — crear regla
    GET    /api/access/separation-rules/{id}/  — detalle
    PATCH  /api/access/separation-rules/{id}/ — modificar
    DELETE /api/access/separation-rules/{id}/ — baja logica
    """
    queryset = SeparationRule.objects.select_related('function_a', 'function_b').all()
    permission_classes = [IsAuthenticated]

    serializer_class = SeparationRuleSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'], url_path='check')
    def check_conflict(self, request):
        """
        UC_ACC_05 — Verificar si dos funciones tienen conflicto SoD.
        GET /api/access/separation-rules/check/?function_a=X&function_b=Y
        """
        fa = request.query_params.get('function_a')
        fb = request.query_params.get('function_b')
        conflicto = SeparationRule.objects.filter(
            status='activa'
        ).filter(
            models.Q(function_a_id=fa, function_b_id=fb) |
            models.Q(function_a_id=fb, function_b_id=fa)
        ).first()
        return Response({
            'tiene_conflicto': conflicto is not None,
            'regla': str(conflicto) if conflicto else None,
        })


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
    permission_classes = [IsAuthenticated]

    serializer_class = ExceptionalPermissionSerializer

    @action(detail=True, methods=['patch'], url_path='approve')
    def approve(self, request, pk=None):
        """UC_ACC_08 / UC_PERM_03 — Aprobar permiso excepcional."""
        perm = self.get_object()
        if perm.status != 'pending':
            return Response({'error': 'Solo se pueden aprobar permisos pendientes.'}, status=400)
        perm.status = 'approved'
        perm.granted_by = request.user
        perm.save()
        return Response({'detail': 'Permiso aprobado.', 'status': perm.status})

    @action(detail=True, methods=['patch'], url_path='revoke')
    def revoke(self, request, pk=None):
        """UC_PERM_04 — Revocar permiso excepcional."""
        perm = self.get_object()
        if perm.status in ('revocado', 'expirado'):
            return Response({'error': f'Permiso ya esta en status {perm.status}.'}, status=400)
        perm.status = 'revoked'
        perm.save()
        return Response({'detail': 'Permiso revocado.', 'status': perm.status})


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

    Retorna la union de:
    - UserPermission directos
    - Funciones de los AccessGroup del usuario
    - ExceptionalPermission activos
    Menos cualquier funcion que viole una SeparationRule activa.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        from apps.access.services import get_user_function_codes
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'error': 'Usuario no encontrado.'}, status=404)

        # Funciones directas
        direct = set(UserPermission.objects.filter(
            user=user
        ).values_list('function__code', flat=True))

        # Funciones via AccessGroup
        group_fns = set(Function.objects.filter(
            access_groups__memberships__user=user
        ).values_list('code', flat=True))

        # Funciones excepcionales activas
        from django.utils import timezone
        now = timezone.now()
        exceptional = set(ExceptionalPermission.objects.filter(
            user=user, status='approved',
            valid_from__lte=now, valid_until__gte=now
        ).values_list('function__code', flat=True))

        all_functions = direct | group_fns | exceptional

        return Response({
            'user_id': user_id,
            'total_functions': len(all_functions),
            'sources': {
                'direct':       list(direct),
                'from_groups':  list(group_fns),
                'exceptional':  list(exceptional),
            },
            'effective': sorted(all_functions),
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
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        from django.contrib.auth import get_user_model
        from django.utils import timezone
        User = get_user_model()

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'error': 'Usuario no encontrado.'}, status=404)

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
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from django.contrib.auth import get_user_model
        from django.db import models as dj_models
        User = get_user_model()

        user_id     = request.data.get('userId')
        function_id = request.data.get('functionId')

        if not user_id or not function_id:
            return Response(
                {'error': 'userId y functionId son requeridos.'}, status=400)

        try:
            user     = User.objects.get(pk=user_id)
            function = Function.objects.get(pk=function_id, is_active=True)
        except User.DoesNotExist:
            return Response({'error': 'Usuario no encontrado.'}, status=404)
        except Function.DoesNotExist:
            return Response({'error': 'Funcion no encontrada o inactiva.'}, status=404)

        # Verificar conflicto de SeparationRule
        existing_codes = user.get_functions() if hasattr(user, 'get_functions') else []
        conflict = SeparationRule.objects.filter(
            status='activa'
        ).filter(
            dj_models.Q(function_a=function, function_b__code__in=existing_codes) |
            dj_models.Q(function_b=function, function_a__code__in=existing_codes)
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
                {'error': 'La funcion ya esta asignada al usuario.'}, status=409)

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
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        user_id     = request.data.get('userId')
        function_id = request.data.get('functionId')

        if not user_id or not function_id:
            return Response(
                {'error': 'userId y functionId son requeridos.'}, status=400)

        deleted, _ = UserPermission.objects.filter(
            user_id=user_id, function_id=function_id
        ).delete()

        if not deleted:
            return Response(
                {'error': 'Asignacion no encontrada.'}, status=404)

        return Response({'detail': 'Funcion revocada correctamente.'})


@extend_schema(
    summary="UC_ACC_05 — Validar conflicto de separacion",
    description=(
        "Retorna conflicts[] con la estructura que consume accessSlice.sodConflicts."
    ),
    tags=["Control de Acceso"],
    request=inline_serializer('SeparationValidateRequest', fields={
        'userId':     drf_serializers_module.IntegerField(),
        'functionId': drf_serializers_module.IntegerField(),
    }),
    responses={
        200: inline_serializer('SeparationValidateResponse', fields={
            'conflicts': drf_serializers_module.ListField(
                child=drf_serializers_module.DictField()),
        }),
        404: OpenApiResponse(description='Usuario o funcion no encontrados'),
    },
)
class SeparationRuleValidateView(APIView):
    """
    accessService.validateSoD(userId, functionId)
    POST /api/access/validate-sod
    Body: { userId, functionId }

    NOTA: El nombre del endpoint respeta el contrato del frontend
    (strings opacos de API). El nombre de la clase en Python sigue
    CLEAN_CODE_NAMING_PRINCIPLES (sin acronimos).

    Retorna estructura que consume accessSlice:
      { conflicts: [{ rule, ruleDesc, setA, setB, message }] }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from django.contrib.auth import get_user_model
        from django.db import models as dj_models
        User = get_user_model()

        user_id     = request.data.get('userId')
        function_id = request.data.get('functionId')

        if not user_id or not function_id:
            return Response(
                {'error': 'userId y functionId son requeridos.'}, status=400)

        try:
            user     = User.objects.get(pk=user_id)
            function = Function.objects.get(pk=function_id)
        except (User.DoesNotExist, Function.DoesNotExist) as e:
            return Response({'error': str(e)}, status=404)

        existing_codes = user.get_functions() if hasattr(user, 'get_functions') else []
        rules = SeparationRule.objects.filter(
            status='activa'
        ).filter(
            dj_models.Q(function_a=function) | dj_models.Q(function_b=function)
        ).select_related('function_a', 'function_b')

        conflicts = []
        for rule in rules:
            other_fn = rule.function_b if rule.function_a == function else rule.function_a
            if other_fn.code in existing_codes:
                conflicts.append({
                    'rule':     rule.name,
                    'ruleDesc': rule.justification,
                    'setA':     [function.code],
                    'setB':     [other_fn.code],
                    'message':  f'{rule.name}: {function.code} incompatible con {other_fn.code}',
                })

        return Response({'conflicts': conflicts})


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
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        user_id   = request.data.get('userId')
        grouper_id = request.data.get('grouperId')

        if not user_id or not grouper_id:
            return Response(
                {'error': 'userId y grouperId son requeridos.'}, status=400)

        try:
            user   = User.objects.get(pk=user_id)
            group  = AccessGroup.objects.get(pk=grouper_id, is_active=True)
        except User.DoesNotExist:
            return Response({'error': 'Usuario no encontrado.'}, status=404)
        except AccessGroup.DoesNotExist:
            return Response({'error': 'Agrupador no encontrado.'}, status=404)

        membership, created = UserAccessGroup.objects.get_or_create(
            user=user, access_group=group,
            defaults={'granted_by': request.user}
        )

        if not created:
            return Response(
                {'error': 'El usuario ya pertenece a este agrupador.'}, status=409)

        serializer = UserAccessGroupSerializer(membership)
        return Response(serializer.data, status=201)
