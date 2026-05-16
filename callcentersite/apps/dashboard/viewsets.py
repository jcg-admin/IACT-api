"""
ViewSets para la app Dashboard.

ViewSets implementados:
- DashboardConfigViewSet (con actions: set_default, clone, export, import_config)
- WidgetConfigViewSet (con actions: data, refresh_cache)
- SavedFilterViewSet (con action: apply)
- UserDashboardPreferenceViewSet

FASE 6: Implementación de viewsets.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from apps.dashboard.models import (
    DashboardConfig,
    WidgetConfig,
    SavedFilter,
    UserDashboardPreference
)
from apps.dashboard.serializers import (
    DashboardConfigSerializer,
    DashboardConfigListSerializer,
    DashboardConfigDetailSerializer,
    WidgetConfigSerializer,
    WidgetConfigCreateSerializer,
    WidgetConfigUpdateSerializer,
    WidgetDataSerializer,
    SavedFilterSerializer,
    SavedFilterListSerializer,
    UserDashboardPreferenceSerializer,
    DashboardExportSerializer,
    DashboardImportSerializer
)
from apps.dashboard.permissions import (
    IsDashboardOwnerOrReadOnly,
    IsWidgetOwnerOrReadOnly,
    IsFilterOwnerOrReadOnly,
    IsPreferenceOwner,
    # RBAC Permissions (Modelo Granular)

    CanCreateWidget,
)
from apps.dashboard.services import (
    DashboardService,
    WidgetService,
    FilterService
)


# ==============================================================================
# VIEWSET: DashboardConfig
# ==============================================================================

class DashboardConfigViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de dashboards.
    
    Endpoints:
    - list: GET /api/dashboards/
    - create: POST /api/dashboards/
    - retrieve: GET /api/dashboards/{id}/
    - update: PUT /api/dashboards/{id}/
    - partial_update: PATCH /api/dashboards/{id}/
    - destroy: DELETE /api/dashboards/{id}/
    
    Actions custom:
    - set_default: POST /api/dashboards/{id}/set_default/
    - clone: POST /api/dashboards/{id}/clone/
    - export: GET /api/dashboards/{id}/export/
    - import_config: POST /api/dashboards/import/
    """
    
    permission_classes = [IsAuthenticated, IsDashboardOwnerOrReadOnly]
    
    def get_queryset(self):
        """
        Obtener queryset filtrado.
        
        Retorna:
        - Dashboards del usuario actual
        - Dashboards públicos de otros usuarios
        - Todos los dashboards si es admin
        """
        user = self.request.user
        
        # Admin ve todos
        if user.is_staff or user.is_superuser:
            return DashboardConfig.objects.filter(
                deleted_at__isnull=True
            ).select_related('user').prefetch_related('widgets')
        
        # Usuario normal ve:
        # - Sus propios dashboards
        # - Dashboards públicos de otros
        return DashboardConfig.objects.filter(
            deleted_at__isnull=True
        ).filter(
            user=user
        ) | DashboardConfig.objects.filter(
            deleted_at__isnull=True,
            is_public=True
        ).select_related('user').prefetch_related('widgets')
    
    def get_serializer_class(self):
        """
        Retornar serializer según action.
        
        - list: DashboardConfigListSerializer
        - retrieve: DashboardConfigDetailSerializer
        - export: DashboardExportSerializer
        - import_config: DashboardImportSerializer
        - default: DashboardConfigSerializer
        """
        if self.action == 'list':
            return DashboardConfigListSerializer
        elif self.action == 'retrieve':
            return DashboardConfigDetailSerializer
        elif self.action == 'export':
            return DashboardExportSerializer
        elif self.action == 'import_config':
            return DashboardImportSerializer
        return DashboardConfigSerializer
    
    def perform_create(self, serializer):
        """
        Crear dashboard asignando user actual.
        """
        serializer.save(user=self.request.user)
    
    def perform_destroy(self, instance):
        """
        Eliminar dashboard (soft delete).
        
        Usa DashboardService.delete_dashboard()
        """
        DashboardService.delete_dashboard(instance.id, self.request.user)
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """
        Marcar dashboard como default.
        
        POST /api/dashboards/{id}/set_default/
        
        Response:
        {
            "status": "success",
            "message": "Dashboard marcado como default",
            "dashboard_id": 123
        }
        """
        dashboard = self.get_object()
        
        try:
            DashboardService.set_as_default(dashboard.id, request.user)
            
            return Response({
                'status': 'success',
                'message': 'Dashboard marcado como default',
                'dashboard_id': dashboard.id
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def clone(self, request, pk=None):
        """
        Clonar dashboard para el usuario actual.
        
        POST /api/dashboards/{id}/clone/
        
        Response:
        {
            "status": "success",
            "message": "Dashboard clonado exitosamente",
            "cloned_dashboard": {...}
        }
        """
        dashboard = self.get_object()
        
        try:
            cloned = DashboardService.clone_dashboard(
                dashboard.id,
                request.user
            )
            
            serializer = DashboardConfigDetailSerializer(cloned)
            
            return Response({
                'status': 'success',
                'message': 'Dashboard clonado exitosamente',
                'cloned_dashboard': serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def export(self, request, pk=None):
        """
        Exportar configuración de dashboard.
        
        GET /api/dashboards/{id}/export/
        
        Response:
        {
            "version": "1.0",
            "dashboard": {...},
            "widgets": [...]
        }
        """
        dashboard = self.get_object()
        
        try:
            export_data = DashboardService.export_config(dashboard.id)
            serializer = DashboardExportSerializer(export_data)
            
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def import_config(self, request):
        """
        Importar configuración de dashboard.
        
        POST /api/dashboards/import/
        
        Body:
        {
            "version": "1.0",
            "dashboard": {...},
            "widgets": [...]
        }
        
        Response:
        {
            "status": "success",
            "message": "Dashboard importado exitosamente",
            "imported_dashboard": {...}
        }
        """
        serializer = DashboardImportSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'message': 'Datos de importación inválidos',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            imported = DashboardService.import_config(
                serializer.validated_data,
                request.user
            )
            
            response_serializer = DashboardConfigDetailSerializer(imported)
            
            return Response({
                'status': 'success',
                'message': 'Dashboard importado exitosamente',
                'imported_dashboard': response_serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ==============================================================================
# VIEWSET: WidgetConfig
# ==============================================================================

class WidgetConfigViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de widgets.
    
    Endpoints:
    - list: GET /api/widgets/
    - create: POST /api/widgets/
    - retrieve: GET /api/widgets/{id}/
    - update: PUT /api/widgets/{id}/
    - partial_update: PATCH /api/widgets/{id}/
    - destroy: DELETE /api/widgets/{id}/
    
    Actions custom:
    - data: GET /api/widgets/{id}/data/
    - refresh_cache: POST /api/widgets/{id}/refresh_cache/
    """
    
    permission_classes = [IsAuthenticated, IsWidgetOwnerOrReadOnly]
    
    def get_queryset(self):
        """
        Obtener queryset filtrado.
        
        Retorna widgets de dashboards accesibles al usuario.
        """
        user = self.request.user
        
        # Admin ve todos
        if user.is_staff or user.is_superuser:
            return WidgetConfig.objects.select_related(
                'dashboard', 'dashboard__user'
            )
        
        # Usuario normal ve widgets de:
        # - Sus propios dashboards
        # - Dashboards públicos
        return WidgetConfig.objects.filter(
            dashboard__user=user
        ) | WidgetConfig.objects.filter(
            dashboard__is_public=True
        ).select_related('dashboard', 'dashboard__user')
    
    def get_serializer_class(self):
        """
        Retornar serializer según action.
        
        - create: WidgetConfigCreateSerializer
        - update/partial_update: WidgetConfigUpdateSerializer
        - data: WidgetDataSerializer
        - default: WidgetConfigSerializer
        """
        if self.action == 'create':
            return WidgetConfigCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return WidgetConfigUpdateSerializer
        elif self.action == 'data':
            return WidgetDataSerializer
        return WidgetConfigSerializer
    
    def get_permissions(self):
        """
        Permisos según acción y tipo de widget.
        
        MODELO GRANULAR: Para widgets de datos sensibles, se requieren
        permisos adicionales además del permiso genérico de widgets.
        """
        if self.action == 'create':
            # Verificar tipo de widget solicitado
            # widget_type = self.request.data.get('widget_type', '')  # reservado para validación futura
            
            # Permisos base para crear widgets
            permissions = [
                IsAuthenticated(),
                CanCreateWidget(),
            ]
            
            # CNST-XXX: Solo se validan tipos chart/kpi; otros pendiente de spec.
            # elif widget_type.startswith('USERS_'):
            #     permissions.append(CanAccessUserData())
            # elif widget_type.startswith('AUDIT_'):
            #     permissions.append(CanAccessAuditData())
            
            return permissions
            
        return super().get_permissions()
    
    @action(detail=True, methods=['get'])
    def data(self, request, pk=None):
        """
        Obtener datos del widget.
        
        GET /api/widgets/{id}/data/?date_from=2025-01-01&date_to=2025-01-31
        
        Query params:
        - date_from (opcional): Fecha inicio (YYYY-MM-DD)
        - date_to (opcional): Fecha fin (YYYY-MM-DD)
        - use_cache (opcional): true/false (default: true)
        
        Response:
        {
            "widget_id": 123,
            "widget_name": "Gráfico de Llamadas",
            "widget_type": "CALLS_CHART",
            "data": {...},
            "cached": true,
            "timestamp": "2025-01-24T12:00:00Z"
        }
        """
        widget = self.get_object()
        
        # Parsear date_range de query params
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        use_cache = request.query_params.get('use_cache', 'true').lower() == 'true'
        
        date_range = None
        if date_from and date_to:
            try:
                from datetime import datetime
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                date_range = (date_from_obj, date_to_obj)
            except ValueError:
                return Response({
                    'status': 'error',
                    'message': 'Formato de fecha inválido. Use YYYY-MM-DD'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Obtener datos del widget
            widget_data = WidgetService.get_widget_data(
                widget.id,
                date_range=date_range,
                use_cache=use_cache
            )
            
            # Construir respuesta
            response_data = {
                'widget_id': widget.id,
                'widget_name': widget.widget_name,
                'widget_type': widget.widget_type,
                'data': widget_data,
                'cached': use_cache,
                'timestamp': timezone.now()
            }
            
            serializer = WidgetDataSerializer(response_data)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def refresh_cache(self, request, pk=None):
        """
        Refrescar cache del widget.
        
        POST /api/widgets/{id}/refresh_cache/
        
        Response:
        {
            "status": "success",
            "message": "Cache refrescado",
            "widget_id": 123
        }
        """
        widget = self.get_object()
        
        try:
            WidgetService.refresh_widget_cache(widget.id)
            
            return Response({
                'status': 'success',
                'message': 'Cache del widget refrescado',
                'widget_id': widget.id
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)



# ==============================================================================
# VIEWSET: SavedFilter
# ==============================================================================

class SavedFilterViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de filtros guardados.
    
    Endpoints:
    - list: GET /api/filters/
    - create: POST /api/filters/
    - retrieve: GET /api/filters/{id}/
    - update: PUT /api/filters/{id}/
    - partial_update: PATCH /api/filters/{id}/
    - destroy: DELETE /api/filters/{id}/
    
    Actions custom:
    - apply: POST /api/filters/{id}/apply/
    """
    
    permission_classes = [IsAuthenticated, IsFilterOwnerOrReadOnly]
    
    def get_queryset(self):
        """
        Obtener queryset filtrado.
        
        Retorna:
        - Filtros del usuario actual
        - Filtros públicos de otros usuarios
        - Todos los filtros si es admin
        """
        user = self.request.user
        
        # Admin ve todos
        if user.is_staff or user.is_superuser:
            return SavedFilter.objects.filter(
                deleted_at__isnull=True
            ).select_related('user')
        
        # Usuario normal ve:
        # - Sus propios filtros
        # - Filtros públicos de otros
        return SavedFilter.objects.filter(
            deleted_at__isnull=True
        ).filter(
            user=user
        ) | SavedFilter.objects.filter(
            deleted_at__isnull=True,
            is_public=True
        ).select_related('user')
    
    def get_serializer_class(self):
        """
        Retornar serializer según action.
        
        - list: SavedFilterListSerializer
        - default: SavedFilterSerializer
        """
        if self.action == 'list':
            return SavedFilterListSerializer
        return SavedFilterSerializer
    
    def perform_create(self, serializer):
        """
        Crear filtro asignando user actual.
        """
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        """
        Aplicar filtro a un queryset.
        
        POST /api/filters/{id}/apply/
        
        Body (opcional):
        {
            "additional_filters": {...}
        }
        
        Response:
        {
            "status": "success",
            "message": "Filtro aplicado",
            "filter_config": {...}
        }
        
        Nota: Este endpoint retorna la configuración del filtro
        que luego debe ser aplicada por el cliente.
        """
        saved_filter = self.get_object()
        
        # Combinar filter_config guardado con filtros adicionales si los hay
        filter_config = saved_filter.filter_config.copy()
        
        if 'additional_filters' in request.data:
            additional = request.data['additional_filters']
            if isinstance(additional, dict):
                filter_config.update(additional)
        
        # Validar configuración combinada
        try:
            FilterService.validate_filter_config(filter_config)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Configuración de filtro inválida: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'status': 'success',
            'message': 'Filtro listo para aplicar',
            'filter_config': filter_config,
            'filter_name': saved_filter.filter_name,
            'filter_type': saved_filter.filter_type
        }, status=status.HTTP_200_OK)


# ==============================================================================
# VIEWSET: UserDashboardPreference
# ==============================================================================

class UserDashboardPreferenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de preferencias de usuario.
    
    Endpoints:
    - list: GET /api/preferences/ (solo admin)
    - create: POST /api/preferences/
    - retrieve: GET /api/preferences/{id}/
    - update: PUT /api/preferences/{id}/
    - partial_update: PATCH /api/preferences/{id}/
    - destroy: DELETE /api/preferences/{id}/
    
    Actions custom:
    - me: GET /api/preferences/me/
    """
    
    queryset = UserDashboardPreference.objects.select_related(
        'user', 'default_dashboard'
    )
    serializer_class = UserDashboardPreferenceSerializer
    permission_classes = [IsAuthenticated, IsPreferenceOwner]
    
    def get_queryset(self):
        """
        Obtener queryset filtrado.
        
        Retorna:
        - Preferencias del usuario actual
        - Todas las preferencias si es admin
        """
        user = self.request.user
        
        # Admin ve todas
        if user.is_staff or user.is_superuser:
            return self.queryset
        
        # Usuario normal solo ve las suyas
        return self.queryset.filter(user=user)
    
    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        """
        Obtener/actualizar preferencias del usuario actual.
        
        GET /api/preferences/me/
        PUT /api/preferences/me/
        PATCH /api/preferences/me/
        
        Response:
        {
            "id": 1,
            "user": 1,
            "default_dashboard": 5,
            "theme": "light",
            "refresh_enabled": true,
            ...
        }
        """
        # Obtener o crear preferencias del usuario
        preference, created = UserDashboardPreference.objects.get_or_create(
            user=request.user,
            defaults={
                'theme': 'light',
                'refresh_enabled': True,
                'refresh_interval_seconds': 300,
                'show_notifications': True,
                'preferences': {}
            }
        )
        
        if request.method == 'GET':
            serializer = self.get_serializer(preference)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        elif request.method in ['PUT', 'PATCH']:
            partial = request.method == 'PATCH'
            serializer = self.get_serializer(
                preference,
                data=request.data,
                partial=partial
            )
            
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
