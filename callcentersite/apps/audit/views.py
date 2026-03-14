"""
Views para consulta de AuditLog.
"""
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import AuditLog
from .serializers import AuditLogSerializer, AuditLogSummarySerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para AuditLog.
    
    Endpoints:
    - GET /api/v1/audit/logs/ - Listar logs
    - GET /api/v1/audit/logs/{id}/ - Detalle de log
    
    INMUTABLE (CNST-009): Solo permite GET, no POST/PUT/DELETE.
    
    Filtros disponibles:
    - user: ID de usuario
    - action: Tipo de acción (LOGIN, CREATE, etc.)
    - result: SUCCESS o FAILURE
    - timestamp: Rango de fechas
    
    Búsqueda:
    - resource: Buscar en nombre de recurso
    
    Ordenamiento:
    - timestamp (default: -timestamp)
    """
    
    queryset = AuditLog.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user', 'action', 'result']
    search_fields = ['resource', 'details']
    ordering_fields = ['timestamp', 'action']
    ordering = ['-timestamp']
    
    def get_serializer_class(self):
        """
        Usar serializer resumido para list, completo para retrieve.
        """
        if self.action == 'list':
            return AuditLogSummarySerializer
        return AuditLogSerializer
    
    def get_queryset(self):
        """
        Filtrar logs según permisos del usuario.
        
        - Superusuarios ven todos los logs
        - Usuarios normales solo ven sus propios logs
        """
        queryset = super().get_queryset()
        
        # Superusuarios ven todo
        if self.request.user.is_superuser:
            return queryset
        
        # Usuarios normales solo sus logs
        return queryset.filter(user=self.request.user)
