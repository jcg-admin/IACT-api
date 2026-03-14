"""
Filtros para apps/pipeline/.

Django-filter filtros para ViewSets de DRF.

Movido desde apps/core/ - FASE 2 PARTE 2.
CLEAN_CODE v3.0.1: Nombres auto-documentados.
"""

import django_filters
from django.db.models import Q

from apps.pipeline.models import Center, Service, CallRecord


# ============================================================================
# CENTER FILTERS
# ============================================================================

class CenterFilter(django_filters.FilterSet):
    """
    Filtros para Center.
    
    Filtros disponibles:
        - codigo (exact, icontains)
        - nombre (icontains)
        - activo (exact)
        - search (búsqueda en código y nombre)
    """
    
    # Búsqueda por código
    codigo = django_filters.CharFilter(lookup_expr='exact')
    codigo__icontains = django_filters.CharFilter(
        field_name='codigo',
        lookup_expr='icontains'
    )
    
    # Búsqueda por nombre
    nombre__icontains = django_filters.CharFilter(
        field_name='nombre',
        lookup_expr='icontains'
    )
    
    # Búsqueda general
    search = django_filters.CharFilter(method='filter_search')
    
    class Meta:
        model = Center
        fields = {
            'activo': ['exact'],
            'created_at': ['gte', 'lte'],
        }
    
    def filter_search(self, queryset, name, value):
        """
        Búsqueda en código y nombre.
        
        Args:
            queryset: QuerySet a filtrar
            name: Nombre del filtro ('search')
            value: Valor a buscar
        
        Returns:
            QuerySet filtrado
        """
        return queryset.filter(
            Q(codigo__icontains=value) |
            Q(nombre__icontains=value) |
            Q(descripcion__icontains=value)
        )


# ============================================================================
# SERVICE FILTERS
# ============================================================================

class ServiceFilter(django_filters.FilterSet):
    """
    Filtros para Service.
    
    Filtros disponibles:
        - numero_800 (exact, icontains)
        - nombre (icontains)
        - center (exact)
        - center_codigo (exact)
        - activo (exact)
        - search (búsqueda en número y nombre)
    """
    
    # Búsqueda por número 800
    numero_800 = django_filters.CharFilter(lookup_expr='exact')
    numero_800__icontains = django_filters.CharFilter(
        field_name='numero_800',
        lookup_expr='icontains'
    )
    
    # Búsqueda por nombre
    nombre__icontains = django_filters.CharFilter(
        field_name='nombre',
        lookup_expr='icontains'
    )
    
    # Filtro por centro
    center = django_filters.NumberFilter(field_name='center__id')
    center_codigo = django_filters.CharFilter(
        field_name='center__codigo',
        lookup_expr='exact'
    )
    
    # Búsqueda general
    search = django_filters.CharFilter(method='filter_search')
    
    class Meta:
        model = Service
        fields = {
            'activo': ['exact'],
            'created_at': ['gte', 'lte'],
        }
    
    def filter_search(self, queryset, name, value):
        """
        Búsqueda en número 800, nombre y centro.
        """
        return queryset.filter(
            Q(numero_800__icontains=value) |
            Q(nombre__icontains=value) |
            Q(descripcion__icontains=value) |
            Q(center__nombre__icontains=value) |
            Q(center__codigo__icontains=value)
        )


# ============================================================================
# CALLRECORD FILTERS
# ============================================================================

class CallRecordFilter(django_filters.FilterSet):
    """
    Filtros para CallRecord.
    
    Filtros disponibles:
        - fecha (exact, gte, lte, range)
        - telefono (exact, icontains)
        - servicio_800 (exact, icontains)
        - year (año de fecha)
        - month (mes de fecha)
        - has_abandoned (tiene abandonadas)
        - high_abandonment (tasa abandono > threshold)
    """
    
    # Filtros por fecha
    fecha = django_filters.DateFilter(lookup_expr='exact')
    fecha__gte = django_filters.DateFilter(field_name='fecha', lookup_expr='gte')
    fecha__lte = django_filters.DateFilter(field_name='fecha', lookup_expr='lte')
    fecha__range = django_filters.DateFromToRangeFilter(field_name='fecha')
    
    # Filtros por año y mes
    year = django_filters.NumberFilter(field_name='fecha__year')
    month = django_filters.NumberFilter(field_name='fecha__month')
    
    # Filtros por teléfono
    telefono = django_filters.CharFilter(lookup_expr='exact')
    telefono__icontains = django_filters.CharFilter(
        field_name='telefono',
        lookup_expr='icontains'
    )
    
    # Filtros por servicio
    servicio_800 = django_filters.CharFilter(lookup_expr='exact')
    servicio_800__icontains = django_filters.CharFilter(
        field_name='servicio_800',
        lookup_expr='icontains'
    )
    
    # Filtros booleanos
    has_abandoned = django_filters.BooleanFilter(method='filter_has_abandoned')
    high_abandonment = django_filters.BooleanFilter(method='filter_high_abandonment')
    
    # Filtros por cantidad de llamadas
    total_llamadas__gte = django_filters.NumberFilter(
        field_name='total_llamadas',
        lookup_expr='gte'
    )
    total_llamadas__lte = django_filters.NumberFilter(
        field_name='total_llamadas',
        lookup_expr='lte'
    )
    
    class Meta:
        model = CallRecord
        fields = []
    
    def filter_has_abandoned(self, queryset, name, value):
        """
        Filtrar registros con llamadas abandonadas.
        
        Args:
            value (bool): True = con abandonadas, False = sin abandonadas
        """
        if value:
            return queryset.filter(llamadas_abandonadas__gt=0)
        else:
            return queryset.filter(llamadas_abandonadas=0)
    
    def filter_high_abandonment(self, queryset, name, value):
        """
        Filtrar registros con alta tasa de abandono (> 15%).
        
        Args:
            value (bool): True = alta tasa, False = tasa normal
        """
        from django.db.models import F, FloatField
        from django.db.models.functions import Cast
        
        if value:
            # Abandonadas / Total > 0.15
            return queryset.annotate(
                abandonment_rate=Cast(F('llamadas_abandonadas'), FloatField()) / 
                                Cast(F('total_llamadas'), FloatField())
            ).filter(abandonment_rate__gt=0.15)
        else:
            return queryset.annotate(
                abandonment_rate=Cast(F('llamadas_abandonadas'), FloatField()) / 
                                Cast(F('total_llamadas'), FloatField())
            ).filter(abandonment_rate__lte=0.15)


# ============================================================================
# USERSERVICEACCESS FILTERS
# ============================================================================



# ============================================================================
# TOTAL FILTERS: 3 (pipeline only)
# 
# Filters:
#   - CenterFilter (5 filtros + search)
#   - ServiceFilter (7 filtros + search)
#   - CallRecordFilter (14 filtros + métodos custom)
# 
# Características:
#   [SUCCESS] django-filter integration
#   [SUCCESS] Búsqueda general (search)
#   [SUCCESS] Filtros por rango (gte, lte, range)
#   [SUCCESS] Filtros custom (has_abandoned, high_abandonment)
#   [SUCCESS] Filtros relacionados (center, user, service)
#   [SUCCESS] Case-insensitive search (icontains)
#   [SUCCESS] Q objects para búsqueda múltiple
#   [SUCCESS] Docstrings completos
#   [SUCCESS] CLEAN_CODE v3.0.1
# ============================================================================
