# apps/alerts/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.alerts.models import (
    InternalMessage,
    MessageRecipient,
    AlertConfiguration,
    AlertSubscription
)
from apps.alerts.serializers import (
    InternalMessageListSerializer,
    InternalMessageDetailSerializer,
    InternalMessageCreateSerializer,
    InboxMessageSerializer,
    AlertConfigurationSerializer,
    AlertSubscriptionSerializer,
    AlertSubscriptionCreateSerializer
)
from apps.alerts.permissions import (
    MessagePermissions,
    AlertConfigurationPermissions,
    AlertSubscriptionPermissions
)
from apps.alerts.services import MessageService, SubscriptionService


class InternalMessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet para mensajes internos
    
    Endpoints:
    - GET /api/alerts/messages/ - Listar todos (admin)
    - GET /api/alerts/messages/inbox/ - Bandeja de entrada
    - GET /api/alerts/messages/{id}/ - Detalle de mensaje
    - POST /api/alerts/messages/ - Enviar mensaje
    - DELETE /api/alerts/messages/{id}/ - Eliminar mensaje
    - PATCH /api/alerts/messages/{id}/mark-read/ - Marcar como leído
    - PATCH /api/alerts/messages/{id}/archive/ - Archivar
    - PATCH /api/alerts/messages/{id}/unarchive/ - Desarchivar
    """
    
    permission_classes = [MessagePermissions]
    
    def get_queryset(self):
        """QuerySet base"""
        return InternalMessage.objects.filter(
            deleted_at__isnull=True
        ).select_related('sender').prefetch_related('recipients')
    
    def get_serializer_class(self):
        """Seleccionar serializer según acción"""
        if self.action == 'list':
            return InternalMessageListSerializer
        elif self.action == 'create':
            return InternalMessageCreateSerializer
        elif self.action == 'inbox':
            return InboxMessageSerializer
        else:
            return InternalMessageDetailSerializer
    
    @action(detail=False, methods=['get'])
    def inbox(self, request):
        """
        Bandeja de entrada del usuario actual
        
        Query params:
        - unread: true/false (solo no leídos)
        - archived: true/false (incluir archivados)
        - priority: info/warning/error/critical
        """
        unread_only = request.query_params.get('unread', 'false').lower() == 'true'
        archived = request.query_params.get('archived', 'false').lower() == 'true'
        priority = request.query_params.get('priority')
        
        # Obtener inbox usando service
        queryset = MessageService.get_inbox(
            user=request.user,
            unread_only=unread_only,
            archived=archived
        )
        
        # Filtrar por prioridad si se especifica
        if priority and priority in ['info', 'warning', 'error', 'critical']:
            queryset = queryset.filter(message__priority=priority)
        
        # Paginación
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def mark_read(self, request, pk=None):
        """Marcar mensaje como leído"""
        message = self.get_object()
        
        try:
            recipient = MessageService.mark_as_read(
                message=message,
                user=request.user
            )
            return Response({
                'message': 'Mensaje marcado como leído',
                'read_at': recipient.read_at
            })
        except MessageRecipient.DoesNotExist:
            return Response(
                {'error': 'No eres destinatario de este mensaje'},
                status=status.HTTP_403_FORBIDDEN
            )
    
    @action(detail=True, methods=['patch'])
    def archive(self, request, pk=None):
        """Archivar mensaje"""
        message = self.get_object()
        
        try:
            recipient = MessageService.archive_message(
                message=message,
                user=request.user
            )
            return Response({
                'message': 'Mensaje archivado',
                'archived_at': recipient.archived_at
            })
        except MessageRecipient.DoesNotExist:
            return Response(
                {'error': 'No eres destinatario de este mensaje'},
                status=status.HTTP_403_FORBIDDEN
            )
    
    @action(detail=True, methods=['patch'])
    def unarchive(self, request, pk=None):
        """Desarchivar mensaje"""
        message = self.get_object()
        
        try:
            recipient = MessageService.unarchive_message(
                message=message,
                user=request.user
            )
            return Response({
                'message': 'Mensaje desarchivado'
            })
        except MessageRecipient.DoesNotExist:
            return Response(
                {'error': 'No eres destinatario de este mensaje'},
                status=status.HTTP_403_FORBIDDEN
            )


class AlertConfigurationViewSet(viewsets.ModelViewSet):
    """
    ViewSet para configuraciones de alertas
    
    Endpoints:
    - GET /api/alerts/configurations/ - Listar configuraciones
    - POST /api/alerts/configurations/ - Crear configuración
    - GET /api/alerts/configurations/{id}/ - Detalle
    - PATCH /api/alerts/configurations/{id}/ - Actualizar
    - DELETE /api/alerts/configurations/{id}/ - Eliminar (soft delete)
    """
    
    queryset = AlertConfiguration.objects.filter(deleted_at__isnull=True)
    serializer_class = AlertConfigurationSerializer
    permission_classes = [AlertConfigurationPermissions]
    
    def get_queryset(self):
        """Filtrar por active si se especifica"""
        queryset = super().get_queryset()
        
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.order_by('-created_at')


class AlertSubscriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para suscripciones a alertas
    
    Endpoints:
    - GET /api/alerts/subscriptions/ - Mis suscripciones
    - POST /api/alerts/subscriptions/ - Suscribirse
    - DELETE /api/alerts/subscriptions/{id}/ - Desuscribirse
    """
    
    serializer_class = AlertSubscriptionSerializer
    permission_classes = [AlertSubscriptionPermissions]
    http_method_names = ['get', 'post', 'delete']  # No PUT/PATCH
    
    def get_queryset(self):
        """Solo suscripciones del usuario actual"""
        return AlertSubscription.objects.filter(
            user=self.request.user,
            deleted_at__isnull=True
        ).select_related('alert_configuration')
    
    def get_serializer_class(self):
        """Usar serializer simple para create"""
        if self.action == 'create':
            return AlertSubscriptionCreateSerializer
        return AlertSubscriptionSerializer
    
    def destroy(self, request, *args, **kwargs):
        """Desuscribirse"""
        subscription = self.get_object()
        
        # Usar service para desuscribir
        SubscriptionService.unsubscribe(
            user=request.user,
            alert_configuration=subscription.alert_configuration
        )
        
        return Response(
            {'message': 'Desuscrito correctamente'},
            status=status.HTTP_204_NO_CONTENT
        )
