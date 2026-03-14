"""
Serializers para Center (Centro de llamadas).

Responsabilidad: Serialización de centros de llamadas.

Serializers:
- CenterSerializer: Centro con métricas de servicios
- CenterListSerializer: Listado simplificado de centros
- CenterDetailSerializer: Centro con servicios anidados

Principios aplicados:
- SRP: Responsabilidad única (centros)
- Clean Code: Validaciones claras
- Performance: Serializers list/detail separados
"""

from rest_framework import serializers
from apps.pipeline.models import Center


class CenterSerializer(serializers.ModelSerializer):
    """
    Serializer para Center.
    
    Campos adicionales:
        - active_services_count (read-only): Cantidad de servicios activos
        - total_services_count (read-only): Total de servicios
    """
    
    active_services_count = serializers.SerializerMethodField()
    total_services_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Center
        fields = [
            'id',
            'nombre',
            'codigo',
            'descripcion',
            'direccion',
            'activo',
            'active_services_count',
            'total_services_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_active_services_count(self, obj):
        """Cantidad de servicios activos del centro."""
        return obj.get_active_services_count()
    
    def get_total_services_count(self, obj):
        """Total de servicios del centro."""
        return obj.services.count()
    
    def validate_codigo(self, value):
        """Validar que código sea único."""
        instance = self.instance
        
        # Si es update y código no cambió, OK
        if instance and instance.codigo == value:
            return value
        
        # Verificar si ya existe
        if Center.objects.filter(codigo=value).exists():
            raise serializers.ValidationError(
                f"Ya existe un centro con código '{value}'"
            )
        
        return value


class CenterListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listado de centros.
    
    Solo campos esenciales para optimizar queries.
    """
    
    active_services_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Center
        fields = [
            'id',
            'nombre',
            'codigo',
            'activo',
            'active_services_count',
        ]


class CenterDetailSerializer(CenterSerializer):
    """
    Serializer detallado para Center.
    
    Incluye lista de servicios anidados.
    Importa ServiceListSerializer localmente para evitar import circular.
    """
    
    services = serializers.SerializerMethodField()
    
    class Meta(CenterSerializer.Meta):
        fields = CenterSerializer.Meta.fields + ['services']
    
    def get_services(self, obj):
        """
        Lista de servicios del centro.
        
        Importa ServiceListSerializer localmente para evitar circular import.
        """
        from apps.pipeline.serializers.service_serializers import ServiceListSerializer
        services = obj.services.all()[:20]  # Limitar a 20
        return ServiceListSerializer(services, many=True).data
