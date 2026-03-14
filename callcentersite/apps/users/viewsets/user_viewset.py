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
    UserListSerializer,
    # UserDetailSerializer,  # TODO: No existe - usando UserSerializer temporalmente
)
from apps.users.filters import UserFilter

# [SUCCESS] BEST PRACTICE: Use get_user_model() instead of direct import
# https://docs.djangoproject.com/en/stable/topics/auth/customizing/#referencing-the-user-model
User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de usuarios.
    
    Endpoints:
    - GET /api/users/ - Listar usuarios (requires: users.view)
    - POST /api/users/ - Crear usuario (requires: users.create)
    - GET /api/users/{id}/ - Detalle usuario (requires: users.view)
    - PUT /api/users/{id}/ - Actualizar usuario (requires: users.edit)
    - PATCH /api/users/{id}/ - Actualizar parcial (requires: users.edit)
    - DELETE /api/users/{id}/ - Soft delete (requires: users.delete)
    - POST /api/users/{id}/activate/ - Activar (requires: users.edit)
    - POST /api/users/{id}/deactivate/ - Desactivar (requires: users.edit)
    
    Permissions:
    - RequiresFunctionPermission: Verifica function_map
    - function_map: Mapea actions a namespaces Django
    
    RBAC:
    - Usa función has_function() del User model
    - Permisos granulares: users.view, users.create, users.edit, users.delete
    """
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, RequiresFunctionPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = UserFilter
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['username', 'email', 'date_joined']
    ordering = ['-date_joined']
    
    function_map = {
        'list': 'users.view',           # <- Namespace Django
        'retrieve': 'users.view',       # <- Namespace Django
        'create': 'users.create',       # <- Namespace Django
        'update': 'users.edit',         # <- Namespace Django
        'partial_update': 'users.edit', # <- Namespace Django
        'destroy': 'users.delete',      # <- Namespace Django
        'activate': 'users.edit',       # <- Namespace Django
        'deactivate': 'users.edit',     # <- Namespace Django
    }
    
    def get_serializer_class(self):
        """Retornar serializer según action."""
        if self.action == 'list':
            return UserListSerializer
        elif self.action == 'retrieve':
            return UserSerializer  # TODO: Debería ser UserDetailSerializer cuando exista
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
