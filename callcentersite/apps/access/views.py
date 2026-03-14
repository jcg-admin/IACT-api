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
