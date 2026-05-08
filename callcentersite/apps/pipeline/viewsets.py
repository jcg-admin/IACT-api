"""
ViewSets para apps/pipeline/.

Django REST Framework ViewSets para API REST.

Movido desde apps/core/ - FASE 2 PARTE 2.
CLEAN_CODE v3.0.1: Nombres auto-documentados.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import permissions as drf_permissions
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from datetime import date, datetime

from apps.pipeline.models import Center, Service, CallRecord, CallNote

from apps.pipeline.serializers import (
    # Center
    CenterSerializer,
    CenterListSerializer,
    CenterDetailSerializer,
    # Service
    ServiceSerializer,
    ServiceListSerializer,
    ServiceDetailSerializer,
    # CallRecord
    CallRecordSerializer,
    CallRecordListSerializer,
    CallRecordStatsSerializer,
    # CallNote (FASE 0.2)
    CallNoteSerializer,
)
from apps.pipeline.filters import (
    CenterFilter,
    ServiceFilter,
    CallRecordFilter,
)
from apps.pipeline.permissions import (
    CenterOwnershipPolicy,
    ServiceOwnershipPolicy,
    IsActiveUser,
)
from apps.core.permissions import RequiresFunctionPermission
from apps.pipeline.services import (
    CenterService,
    ServiceService,
    CallRecordService,
)

User = get_user_model()


# ============================================================================
# CENTER VIEWSET
# ============================================================================

class CenterViewSet(viewsets.ModelViewSet):
    """
    ViewSet para Center.
    
    Endpoints:
        GET    /centers/          - Listar centros
        POST   /centers/          - Crear centro
        GET    /centers/{id}/     - Detalle centro
        PUT    /centers/{id}/     - Actualizar centro
        PATCH  /centers/{id}/     - Actualizar parcial
        DELETE /centers/{id}/     - Eliminar centro (soft delete)
        
        POST   /centers/{id}/deactivate/  - Desactivar centro
        POST   /centers/{id}/activate/    - Activar centro
        GET    /centers/{id}/stats/       - Estadísticas centro
    
    Permissions:
        - IsAuthenticated
        - IsActiveUser
        - CenterOwnershipPolicy (POST/PUT/PATCH/DELETE)
    
    Filters:
        - codigo (exact, icontains)
        - nombre (icontains)
        - activo
        - search
    """
    
    queryset = Center.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CenterFilter
    search_fields = ['nombre', 'codigo', 'descripcion']
    ordering_fields = ['nombre', 'codigo', 'created_at']
    ordering = ['nombre']
    
    permission_classes = [
        drf_permissions.IsAuthenticated,
        IsActiveUser,
        CenterOwnershipPolicy,
    ]
    
    def get_serializer_class(self):
        """
        Retornar serializer según action.
        
        - list: CenterListSerializer (ligero)
        - retrieve: CenterDetailSerializer (nested)
        - default: CenterSerializer
        """
        if self.action == 'list':
            return CenterListSerializer
        elif self.action == 'retrieve':
            return CenterDetailSerializer
        return CenterSerializer
    
    def perform_create(self, serializer):
        """Crear centro usando CenterService."""
        data = serializer.validated_data
        center = CenterService.create_center(data)
        serializer.instance = center
    
    def perform_update(self, serializer):
        """Actualizar centro usando CenterService."""
        center = self.get_object()
        data = serializer.validated_data
        updated_center = CenterService.update_center(center, data)
        serializer.instance = updated_center
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Desactivar centro y todos sus servicios.
        
        POST /centers/{id}/deactivate/
        
        Returns:
            {
                'message': str,
                'services_deactivated': int,
                'user_accesses_affected': int
            }
        """
        center = self.get_object()
        
        if not center.activo:
            return Response(
                {'error': 'Centro ya está inactivo'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result = CenterService.deactivate_center(center, user=request.user)
        
        return Response({
            'message': f"Centro '{center.nombre}' desactivado exitosamente",
            'services_deactivated': result['services_deactivated'],
            'user_accesses_affected': result['user_accesses_affected']
        })
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activar centro.
        
        POST /centers/{id}/activate/
        
        NOTA: Los servicios NO se activan automáticamente.
        """
        center = self.get_object()
        
        if center.activo:
            return Response(
                {'error': 'Centro ya está activo'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        activated = CenterService.activate_center(center)
        serializer = self.get_serializer(activated)
        
        return Response({
            'message': f"Centro '{center.nombre}' activado exitosamente",
            'center': serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """
        Obtener estadísticas del centro.
        
        GET /centers/{id}/stats/
        
        Returns:
            {
                'total_services': int,
                'active_services': int,
                'inactive_services': int,
                'total_users_with_access': int,
                'is_active': bool
            }
        """
        center = self.get_object()
        stats = CenterService.get_center_stats(center)
        
        return Response(stats)


# ============================================================================
# SERVICE VIEWSET
# ============================================================================

class ServiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet para Service.
    
    Endpoints:
        GET    /services/          - Listar servicios
        POST   /services/          - Crear servicio
        GET    /services/{id}/     - Detalle servicio
        PUT    /services/{id}/     - Actualizar servicio
        PATCH  /services/{id}/     - Actualizar parcial
        DELETE /services/{id}/     - Eliminar servicio (soft delete)
        
        POST   /services/{id}/deactivate/       - Desactivar servicio
        POST   /services/{id}/activate/         - Activar servicio
    
    Permissions:
        - IsAuthenticated
        - IsActiveUser
        - ServiceOwnershipPolicy (POST/PUT/PATCH/DELETE)
    
    Filters:
        - numero_800 (exact, icontains)
        - nombre (icontains)
        - center (id)
        - center_codigo
        - activo
        - search
    """
    
    queryset = Service.objects.select_related('center').all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ServiceFilter
    search_fields = ['numero_800', 'nombre', 'descripcion', 'center__nombre']
    ordering_fields = ['numero_800', 'nombre', 'created_at']
    ordering = ['numero_800']
    
    permission_classes = [
        drf_permissions.IsAuthenticated,
        IsActiveUser,
        ServiceOwnershipPolicy,
    ]
    
    def get_serializer_class(self):
        """Retornar serializer según action."""
        if self.action == 'list':
            return ServiceListSerializer
        elif self.action == 'retrieve':
            return ServiceDetailSerializer
        return ServiceSerializer
    
    def perform_create(self, serializer):
        """Crear servicio usando ServiceService."""
        data = serializer.validated_data
        data['center_id'] = data.pop('center').id
        service = ServiceService.create_service(data)
        serializer.instance = service
    
    def perform_update(self, serializer):
        """Actualizar servicio usando ServiceService."""
        service = self.get_object()
        data = serializer.validated_data
        if 'center' in data:
            data['center_id'] = data.pop('center').id
        updated_service = ServiceService.update_service(service, data)
        serializer.instance = updated_service
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Desactivar servicio.
        
        POST /services/{id}/deactivate/
        """
        service = self.get_object()
        
        if not service.activo:
            return Response(
                {'error': 'Servicio ya está inactivo'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        deactivated = ServiceService.deactivate_service(service)
        serializer = self.get_serializer(deactivated)
        
        return Response({
            'message': f"Servicio '{service.numero_800}' desactivado exitosamente",
            'service': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activar servicio.
        
        POST /services/{id}/activate/
        """
        service = self.get_object()
        
        if service.activo:
            return Response(
                {'error': 'Servicio ya está activo'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            activated = ServiceService.activate_service(service)
            serializer = self.get_serializer(activated)
            
            return Response({
                'message': f"Servicio '{service.numero_800}' activado exitosamente",
                'service': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


# ============================================================================
# CALLRECORD VIEWSET
# ============================================================================

class CallRecordViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CallRecord.
    
    Endpoints:
        GET    /call-records/          - Listar registros
        POST   /call-records/          - Crear registro
        GET    /call-records/{id}/     - Detalle registro
        PUT    /call-records/{id}/     - Actualizar registro
        PATCH  /call-records/{id}/     - Actualizar parcial
        DELETE /call-records/{id}/     - Eliminar registro (soft delete)
        
        POST   /call-records/bulk_create/  - Crear múltiples registros
        GET    /call-records/stats/         - Estadísticas agregadas
        GET    /call-records/daily_stats/   - Estadísticas diarias
        GET    /call-records/top_callers/   - Top callers
    
    Permissions:
        - IsAuthenticated
        - IsActiveUser
        - RequiresFunctionPermission (RBAC con MOD_Pipeline)
    
    RBAC (Modelo Granular):
        - Removido: MOD_Calls (módulo incorrecto)
        - Agregado: MOD_Pipeline (módulo correcto)
        - Functions:
            * PIPELINE_CALLREC_VIEW (pipeline.callrecord.view)
            * PIPELINE_CALLREC_CREATE (pipeline.callrecord.create)
            * PIPELINE_CALLREC_EDIT (pipeline.callrecord.edit)
            * PIPELINE_CALLREC_DELETE (pipeline.callrecord.delete)
            * PIPELINE_CALLREC_STATS (pipeline.callrecord.stats)
    
    Filters:
        - fecha (exact, gte, lte, range)
        - year, month
        - telefono (exact, icontains)
        - servicio_800 (exact, icontains)
        - total_llamadas (gte, lte)
        - has_abandoned
        - high_abandonment
    
    QuerySet Filtering:
        Los usuarios con permisos apropiados ven TODOS los registros.
        Superusers ven todos.
    """
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CallRecordFilter
    search_fields = ['telefono', 'servicio_800']
    ordering_fields = ['fecha', 'total_llamadas', 'created_at']
    ordering = ['-fecha', '-created_at']
    
    permission_classes = [
        drf_permissions.IsAuthenticated,
        IsActiveUser,
        RequiresFunctionPermission,  # FASE A DT-002: RBAC puro
    ]
    
    # RBAC v6.0.0: Function map con permisos correctos de PIPELINE
    # CORREGIDO: Cambiado de 'calls.*' a 'pipeline.callrecord.*'
    # para reflejar que CallRecord pertenece a la app Pipeline, no a una app "Calls"
    function_map = {
        'list': 'pipeline.callrecord.view',
        'retrieve': 'pipeline.callrecord.view',
        'create': 'pipeline.callrecord.create',
        'update': 'pipeline.callrecord.edit',
        'partial_update': 'pipeline.callrecord.edit',
        'destroy': 'pipeline.callrecord.delete',
        'bulk_create': 'pipeline.callrecord.create',
        'stats': 'pipeline.callrecord.stats',
        'daily_stats': 'pipeline.callrecord.stats',
        'top_callers': 'pipeline.callrecord.stats',
    }
    
    def get_queryset(self):
        """
        Filtrar queryset según RBAC.
        
        Con RBAC puro:
        - Usuario con permiso apropiado: ve TODOS los registros
        - Superusers: ven todos los registros
        
        NOTA: Filtrado granular por servicio eliminado (UserServiceAccess deprecated)
        """
        # Sistema RBAC: Usuario con permiso ve TODOS los registros
        # Los permisos se validan en permission_classes
        return CallRecord.objects.all()
    
    def get_serializer_class(self):
        """Retornar serializer según action."""
        if self.action == 'list':
            return CallRecordListSerializer
        elif self.action == 'bulk_create':
            return CallRecordBulkCreateSerializer
        elif self.action == 'stats':
            return ServiceStatsSerializer
        elif self.action == 'daily_stats':
            return DailyStatsSerializer
        elif self.action == 'top_callers':
            return TopCallerSerializer
        return CallRecordSerializer
    
    def perform_create(self, serializer):
        """Crear registro usando CallRecordService."""
        data = serializer.validated_data
        record = CallRecordService.create_record(data)
        serializer.instance = record
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """
        Crear múltiples registros en bulk.
        
        POST /call-records/bulk_create/
        Body: {'records': [{...}, {...}, ...]}
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        result = serializer.save()
        
        return Response({
            'message': 'Registros creados exitosamente',
            'created_count': result['created_count'],
            'duplicates_ignored': result['duplicates_ignored']
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Obtener estadísticas agregadas de servicio.
        
        GET /call-records/stats/
        Query params:
            - service_800 (required)
            - start_date (YYYY-MM-DD, required)
            - end_date (YYYY-MM-DD, required)
        """
        service_800 = request.query_params.get('service_800')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not all([service_800, start_date, end_date]):
            return Response(
                {'error': 'service_800, start_date y end_date son requeridos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Formato de fecha inválido. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        stats = CallRecordService.get_service_stats(service_800, start, end)
        serializer = self.get_serializer(stats)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def daily_stats(self, request):
        """
        Obtener estadísticas diarias.
        
        GET /call-records/daily_stats/
        Query params:
            - fecha (YYYY-MM-DD, required)
            - service_800 (optional)
        """
        fecha_str = request.query_params.get('fecha')
        service_800 = request.query_params.get('service_800')
        
        if not fecha_str:
            return Response(
                {'error': 'fecha es requerida'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Formato de fecha inválido. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        stats = CallRecordService.get_daily_stats(fecha, service_800)
        serializer = self.get_serializer(stats)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def top_callers(self, request):
        """
        Obtener top callers.
        
        GET /call-records/top_callers/
        Query params:
            - service_800 (required)
            - start_date (YYYY-MM-DD, required)
            - end_date (YYYY-MM-DD, required)
            - limit (int, optional, default=10)
        """
        service_800 = request.query_params.get('service_800')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        limit = int(request.query_params.get('limit', 10))
        
        if not all([service_800, start_date, end_date]):
            return Response(
                {'error': 'service_800, start_date y end_date son requeridos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Formato de fecha inválido. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        top_callers = CallRecordService.get_top_callers(service_800, start, end, limit)
        serializer = self.get_serializer(top_callers, many=True)
        
        return Response({
            'service_800': service_800,
            'start_date': start_date,
            'end_date': end_date,
            'limit': limit,
            'results': serializer.data
        })


# ============================================================================
# CALLNOTE VIEWSET (FASE 0.2)
# ============================================================================

class CallNoteViewSet(viewsets.ModelViewSet):
    """
    API para gestionar notas de llamadas.
    
    Permite:
    - Crear notas sobre llamadas procesadas (CallRecord)
    - Editar/eliminar propias notas
    - Ver todas las notas de una llamada
    - Filtrar por call_record, user, is_important
    
    Permisos:
    - IsAuthenticated: Usuario debe estar autenticado
    - IsActiveUser: Usuario debe estar activo
    
    FASE 0.2: Sistema de notas para CallRecord.
    
    Examples:
        # Crear nota
        POST /api/v1/pipeline/call-notes/
        {
            "call_record": 123,
            "note": "Cliente reportó problema con facturación",
            "is_important": true
        }
        
        # Listar notas de un CallRecord
        GET /api/v1/pipeline/call-notes/?call_record=123
        
        # Filtrar notas importantes
        GET /api/v1/pipeline/call-notes/?is_important=true
    """
    
    queryset = CallNote.objects.select_related('user', 'call_record').all()
    serializer_class = CallNoteSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['call_record', 'user', 'is_important']
    ordering_fields = ['created_at', 'is_important']
    ordering = ['-created_at']  # Más recientes primero
    
    permission_classes = [
        drf_permissions.IsAuthenticated,
        IsActiveUser,
    ]
    
    def perform_create(self, serializer):
        """
        Al crear, asignar automáticamente el usuario actual.
        
        Args:
            serializer: CallNoteSerializer con datos validados
        """
        serializer.save(user=self.request.user)


# ============================================================================
# TOTAL VIEWSETS: 4 (LIMPIEZA DEUDA TÉCNICA + FASE 0.2)
# 
# ViewSets:
#   - CenterViewSet (ModelViewSet)
#   - ServiceViewSet (ModelViewSet)
#   - CallRecordViewSet (ModelViewSet)
#   - CallNoteViewSet (ModelViewSet) <- FASE 0.2
# 
# ELIMINADO en limpieza deuda técnica:
#   [ERROR] UserServiceAccessViewSet - DEPRECADO
#   [ERROR] ServiceViewSet.grant_access - DEPRECADO
#   [ERROR] ServiceViewSet.bulk_grant_access - DEPRECADO  
#   [ERROR] ServiceViewSet.revoke_access - DEPRECADO
#   [ERROR] ServiceViewSet.users - DEPRECADO
# 
# Control de acceso:
#   [SUCCESS] RBAC puro (Function/UserFunctionAssignment)
#   [SUCCESS] Sin segmentación por servicio específico
#   [SUCCESS] Usuario con permiso -> ve TODOS los servicios
# ============================================================================
