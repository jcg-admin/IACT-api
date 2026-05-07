"""
Views para sistema de acceso y módulos.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .models import Module, UserModuleAccess
from .serializers import (
    ModuleSerializer,
    ModuleTreeSerializer,
    UserModuleAccessSerializer,
    MyModulesSerializer,
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

    def get_serializer_class(self):
        from rest_framework import serializers

        class AccessGroupSerializer(serializers.ModelSerializer):
            function_count = serializers.SerializerMethodField()

            class Meta:
                model = AccessGroup
                fields = ['id', 'name', 'code', 'description',
                          'functions', 'function_count']

            def get_function_count(self, obj):
                return obj.functions.count()

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

    def get_serializer_class(self):
        from rest_framework import serializers

        class UserAccessGroupSerializer(serializers.ModelSerializer):
            class Meta:
                model = UserAccessGroup
                fields = ['id', 'user', 'access_group', 'granted_at', 'granted_by']
                read_only_fields = ['granted_at']

        return UserAccessGroupSerializer

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

    def get_serializer_class(self):
        from rest_framework import serializers

        class SeparationRuleSerializer(serializers.ModelSerializer):
            class Meta:
                model = SeparationRule
                fields = ['id', 'name', 'function_a', 'function_b',
                          'justificacion', 'estado', 'creado_por']
                read_only_fields = ['creado_por']

        return SeparationRuleSerializer

    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user)

    @action(detail=False, methods=['get'], url_path='check')
    def check_conflict(self, request):
        """
        UC_ACC_05 — Verificar si dos funciones tienen conflicto SoD.
        GET /api/access/separation-rules/check/?function_a=X&function_b=Y
        """
        fa = request.query_params.get('function_a')
        fb = request.query_params.get('function_b')
        conflicto = SeparationRule.objects.filter(
            estado='activa'
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

class ExceptionalPermissionViewSet(viewsets.ModelViewSet):
    """
    Gestion de permisos temporales excepcionales.

    UC_ACC_08, UC_PERM_03..04.
    POST   /api/access/exceptional/           — solicitar permiso excepcional
    GET    /api/access/exceptional/           — listar permisos excepcionales
    PATCH  /api/access/exceptional/{id}/      — aprobar/revocar
    """
    queryset = ExceptionalPermission.objects.select_related(
        'user', 'function', 'otorgado_por'
    ).all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        from rest_framework import serializers

        class ExceptionalPermissionSerializer(serializers.ModelSerializer):
            class Meta:
                model = ExceptionalPermission
                fields = ['id', 'user', 'function', 'justificacion',
                          'estado', 'valido_desde', 'valido_hasta',
                          'otorgado_por', 'creado_en']
                read_only_fields = ['estado', 'otorgado_por', 'creado_en']

        return ExceptionalPermissionSerializer

    @action(detail=True, methods=['patch'], url_path='approve')
    def approve(self, request, pk=None):
        """UC_ACC_08 / UC_PERM_03 — Aprobar permiso excepcional."""
        perm = self.get_object()
        if perm.estado != 'pendiente':
            return Response({'error': 'Solo se pueden aprobar permisos pendientes.'}, status=400)
        perm.estado = 'aprobado'
        perm.otorgado_por = request.user
        perm.save()
        return Response({'detail': 'Permiso aprobado.', 'estado': perm.estado})

    @action(detail=True, methods=['patch'], url_path='revoke')
    def revoke(self, request, pk=None):
        """UC_PERM_04 — Revocar permiso excepcional."""
        perm = self.get_object()
        if perm.estado in ('revocado', 'expirado'):
            return Response({'error': f'Permiso ya esta en estado {perm.estado}.'}, status=400)
        perm.estado = 'revocado'
        perm.save()
        return Response({'detail': 'Permiso revocado.', 'estado': perm.estado})


# ---------------------------------------------------------------------------
# B-05: EffectivePermissions endpoint (UC_ACC_03, UC_PERM_07)
# ---------------------------------------------------------------------------

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
            user=user, estado='aprobado',
            valido_desde__lte=now, valido_hasta__gte=now
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
