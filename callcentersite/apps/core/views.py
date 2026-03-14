"""
Views core - IACT Call Center System.

Django REST Framework ViewSets.

CNST-005: Throttling configurado en settings.
"""
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import CallRecord, Center, Service
from .serializers import (
    CallRecordSerializer,
    CenterSerializer,
    ServiceSerializer,
)


class CallRecordViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para CallRecord (READ-ONLY).
    
    GET /api/v1/calls/ - Lista registros
    GET /api/v1/calls/{id}/ - Detalle
    
    CNST-005: Paginacion y throttling configurados en settings.
    """
    
    queryset = CallRecord.objects.all()
    serializer_class = CallRecordSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    
    filterset_fields = {
        'fecha': ['exact', 'gte', 'lte'],
        'telefono': ['exact', 'icontains'],
        'servicio_800': ['exact'],
    }
    
    search_fields = ['telefono', 'servicio_800']
    ordering_fields = ['fecha', 'total_llamadas', 'created_at']
    ordering = ['-fecha']


class CenterViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para Center (READ-ONLY)."""
    
    queryset = Center.objects.filter(activo=True)
    serializer_class = CenterSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'codigo']
    ordering = ['nombre']


class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para Service (READ-ONLY)."""
    
    queryset = Service.objects.filter(activo=True).select_related('center')
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    
    filterset_fields = {
        'center': ['exact'],
        'numero_800': ['exact'],
    }
    
    search_fields = ['numero_800', 'nombre']
    ordering = ['numero_800']
