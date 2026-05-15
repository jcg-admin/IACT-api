"""
ViewSet para gestión de usuarios.

FASE 2 PARTE 4: UserViewSet con RBAC.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.contrib.auth import get_user_model

from apps.core.permissions import RequiresFunctionPermission
from apps.users.serializers import (
    UserSerializer,
)
from apps.users.serializers.user_serializer import UserCreateSerializer
# UC_USR_02: serializers canónicos (F1-H-006)
from apps.users.serializers.user_list_serializer import (
    UserListSerializer,
    UserDetailSerializer,
)
from apps.users.filters import UserFilter

# [SUCCESS] BEST PRACTICE: Use get_user_model() instead of direct import
# https://docs.djangoproject.com/en/stable/topics/auth/customizing/#referencing-the-user-model
User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """
    UC_USR_02 — Consultar Usuarios (list + retrieve).
    UC_USR_01 — Crear Usuario (create).
    UC_USR_03 — Modificar Usuario (update / partial_update).

    Endpoints:
    - GET  /api/users/        — list_users    (USR-004)
    - GET  /api/users/{id}/   — view_users    (USR-009)
    - POST /api/users/        — create_users  (USR-001)
    - PUT  /api/users/{id}/   — update_users  (USR-002)
    - PATCH /api/users/{id}/  — update_users  (USR-002)
    - DELETE /api/users/{id}/ — deactivate_users (USR-003, BR-009 baja lógica)
    - POST /api/users/{id}/activate/   — reactivate_users (USR-008)
    - POST /api/users/{id}/deactivate/ — deactivate_users (USR-003)

    CNST-010: permission_classes explícito.
    F1-H-006: function_map ahora usa códigos canónicos v5.4.0.
    F1-H-007: RequiresFunctionPermission usa has_function_by_code().
    """
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, RequiresFunctionPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = UserFilter
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['username', 'email', 'date_joined']
    ordering = ['-date_joined']
    _VALID_ORDERING = frozenset({'username', 'email', 'date_joined', '-username', '-email', '-date_joined'})
    
    # F1-H-006: function_map con códigos canónicos v5.4.0 (antes: namespaces Django legacy)
    # list_users=USR-004, view_users=USR-009, create_users=USR-001, update_users=USR-002

    def list(self, request, *args, **kwargs):
        """CA-11/12: Validar ordering whitelist (UC_USR_02). CA-07: audit selectivo."""
        from rest_framework.response import Response
        from apps.audit.services import AuditLogService
        ordering = request.query_params.get('ordering', '')
        if ordering and ordering not in self._VALID_ORDERING:
            return Response(
                {'error': 'BAD_FILTER', 'detail': f'Ordering inválido: {ordering!r}'},
                status=400,
            )
        response = super().list(request, *args, **kwargs)
        # CA-07: solo auditar si hay filtro user_id (UC_USR_02 P-16 audit selectivo)
        user_id_filter = request.query_params.get('user_id')
        if user_id_filter:
            AuditLogService.emit(
                event_type='USERS_VIEWED_FOR_USER',
                actor_user_id=request.user.pk,
                payload={'target_user_id': user_id_filter},
            )
        # CA-08: listado sin filtro → ZERO USERS_VIEWED_FOR_USER (no emitir)
        return response

    def retrieve(self, request, *args, **kwargs):
        """CA-09: GET /users/{id}/ → USER_DETAIL_VIEWED siempre. CA-10: self_view."""
        from apps.audit.services import AuditLogService
        response = super().retrieve(request, *args, **kwargs)
        target_pk = kwargs.get('pk')
        self_view = str(request.user.pk) == str(target_pk)
        AuditLogService.emit(
            event_type='USER_DETAIL_VIEWED',
            actor_user_id=request.user.pk,
            payload={'target_user_id': target_pk, 'self_view': self_view},
        )
        return response
    # deactivate_users=USR-003 (baja lógica BR-009)
    function_map = {
        'list':           'USR-004',  # list_users
        'retrieve':       'USR-009',  # view_users
        'create':         'USR-001',  # create_users
        'update':         'USR-002',  # update_users
        'partial_update': 'USR-002',  # update_users
        'destroy':        'USR-003',  # deactivate_users (baja lógica BR-009)
        'activate':       'USR-008',  # reactivate_users
        'deactivate':     'USR-003',  # deactivate_users
    }
    
    def get_serializer_class(self):
        """
        UC_USR_02: serializers distintos para list vs retrieve (CA-02 vs CA-03).
        - list: UserListSerializer (email enmascarado, sin PII — CNST-026)
        - retrieve: UserDetailSerializer (email completo, assignments)
        - create: UserCreateSerializer
        """
        if self.action == 'list':
            return UserListSerializer
        if self.action == 'retrieve':
            return UserDetailSerializer
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer
    
    def perform_destroy(self, instance):
        """Soft delete del usuario."""
        instance.delete()  # SoftDeleteMixin
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activar usuario.
        
        POST /api/users/{id}/activate/
        """
        user = self.get_object()
        user.is_active = True
        user.save()
        
        serializer = self.get_serializer(user)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Desactivar usuario.
        
        POST /api/users/{id}/deactivate/
        """
        user = self.get_object()
        user.is_active = False
        user.save()
        
        serializer = self.get_serializer(user)
        return Response(serializer.data)
