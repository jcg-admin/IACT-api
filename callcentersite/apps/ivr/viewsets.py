"""
ViewSets para apps/ivr - IACT Call Center System.

API REST READ-ONLY para datos legacy de CallLog.

CNST-003: CallLog es READ-ONLY (MariaDB ivr_legacy)
NO permite create, update, delete.
"""
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from apps.core.permissions import RequiresFunctionPermission
from apps.pipeline.permissions import IsActiveUser
from .models import CallLog
from .serializers import CallLogSerializer, CallLogListSerializer


class CallLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API READ-ONLY para CallLog legacy.
    
    Proporciona:
    - list: GET /api/ivr/call-logs/
    - retrieve: GET /api/ivr/call-logs/{id}/
    
    NO proporciona (READ-ONLY):
    - create: POST (prohibido)
    - update: PUT/PATCH (prohibido)
    - destroy: DELETE (prohibido)
    
    Permissions:
    - IsAuthenticated
    - IsActiveUser
    - RequiresFunctionPermission (RBAC con MOD_IVR)
    
    RBAC (Modelo Granular):
    - Functions:
        * IVR_CALLLOG_VIEW (ivr.calllog.view)
        * IVR_CALLLOG_STATS (ivr.calllog.stats)
    
    Filtros:
    - fecha: Filtrar por fecha exacta
    - servicio_800: Filtrar por número 800
    
    Ordenamiento:
    - fecha: Ordenar por fecha (asc/desc)
    - total_llamadas: Ordenar por cantidad de llamadas
    
    CNST-003: Base de datos ivr_legacy (MariaDB READ-ONLY)
    
    Examples:
        # Listar todos (paginado)
        GET /api/ivr/call-logs/
        
        # Filtrar por fecha
        GET /api/ivr/call-logs/?fecha=2025-01-15
        
        # Filtrar por servicio
        GET /api/ivr/call-logs/?servicio_800=800-123-4567
        
        # Ordenar por fecha descendente
        GET /api/ivr/call-logs/?ordering=-fecha
        
        # Obtener un registro específico
        GET /api/ivr/call-logs/123/
    """
    
    queryset = CallLog.objects.all()
    serializer_class = CallLogSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['fecha', 'servicio_800']
    ordering_fields = ['fecha', 'total_llamadas']
    ordering = ['-fecha']  # Por defecto: más recientes primero
    
    # Permisos RBAC
    permission_classes = [
        IsAuthenticated,
        IsActiveUser,
        RequiresFunctionPermission,
    ]
    
    # RBAC v6.0.0: Function map para IVR
    function_map = {
        'list': 'ivr.calllog.view',
        'retrieve': 'ivr.calllog.view',
        # TODO: Agregar endpoint de stats
        # 'stats': 'ivr.calllog.stats',
    }
    
    def get_serializer_class(self):
        """
        Selecciona serializer según la acción.
        
        - list: CallLogListSerializer (simplificado)
        - retrieve: CallLogSerializer (completo con métricas)
        
        Returns:
            Serializer class apropiado
        """
        if self.action == 'list':
            return CallLogListSerializer
        return CallLogSerializer
