"""
Serializers para Service (Servicios).

Responsabilidad: Serialización de servicios de call center.

Serializers:
- ServiceSerializer: Servicio con métricas de usuarios
- ServiceListSerializer: Listado simplificado de servicios
- ServiceDetailSerializer: Servicio con centro anidado

Principios aplicados:
- SRP: Responsabilidad única (servicios)
- Clean Code: Validaciones de número 800 y centro activo
- Performance: Serializers list/detail separados
"""

from rest_framework import serializers
from apps.pipeline.models import Service


class ServiceSerializer(serializers.ModelSerializer):
    """
    Serializer para Service.
    
    Campos adicionales:
        - center_name (read-only): Nombre del centro
        - users_with_access_count (read-only): Cantidad de usuarios con acceso
    """
    
    center_name = serializers.CharField(source='center.nombre', read_only=True)
    users_with_access_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Service
        fields = [
            'id',
            'numero_800',
            'nombre',
            'descripcion',
            'center',
            'center_name',
            'activo',
            'users_with_access_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_users_with_access_count(self, obj):
        """Cantidad de usuarios con acceso al servicio."""
        return obj.get_users_with_access_count()
    
    def validate_numero_800(self, value):
        """Validar que número 800 sea único."""
        instance = self.instance
        
        # Si es update y número no cambió, OK
        if instance and instance.numero_800 == value:
            return value
        
        # Verificar si ya existe
        if Service.objects.filter(numero_800=value).exists():
            raise serializers.ValidationError(
                f"Ya existe un servicio con número '{value}'"
            )
        
        return value
    
    def validate_center(self, value):
        """Validar que centro esté activo."""
        if not value.activo:
            raise serializers.ValidationError(
                f"Centro '{value.nombre}' está inactivo"
            )
        return value


class ServiceListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listado de servicios.
    
    Solo campos esenciales para optimizar queries.
    """
    
    center_name = serializers.CharField(source='center.nombre', read_only=True)
    
    class Meta:
        model = Service
        fields = [
            'id',
            'numero_800',
            'nombre',
            'center_name',
            'activo',
        ]


class ServiceDetailSerializer(ServiceSerializer):
    """
    Serializer detallado para Service.
    
    Incluye información del centro.
    Importa CenterListSerializer localmente para evitar import circular.
    """
    
    center_detail = serializers.SerializerMethodField()
    
    class Meta(ServiceSerializer.Meta):
        fields = ServiceSerializer.Meta.fields + ['center_detail']
    
    def get_center_detail(self, obj):
        """
        Información del centro.
        
        Importa CenterListSerializer localmente para evitar circular import.
        """
        from apps.pipeline.serializers.center_serializers import CenterListSerializer
        return CenterListSerializer(obj.center).data
