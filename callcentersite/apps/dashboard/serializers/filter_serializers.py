"""
Serializers para Saved Filter.

Responsabilidad: Serialización de filtros guardados.

Serializers:
- SavedFilterSerializer: Serializer básico de filtro
- SavedFilterListSerializer: Para listados de filtros

Principios aplicados:
- SRP: Responsabilidad única (filtros)
- Clean Code: Validaciones con FilterService
- Integration: Uso de FilterService para validaciones
"""

from rest_framework import serializers
from apps.dashboard.models import SavedFilter
from apps.dashboard.services import FilterService


class SavedFilterSerializer(serializers.ModelSerializer):
    """
    Serializer básico para SavedFilter.
    """
    
    user_username = serializers.CharField(
        source='user.username',
        read_only=True
    )
    
    filter_type_display = serializers.CharField(
        source='get_filter_type_display',
        read_only=True
    )
    
    class Meta:
        model = SavedFilter
        fields = [
            'id',
            'user',
            'user_username',
            'filter_name',
            'filter_type',
            'filter_type_display',
            'filter_config',
            'is_public',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def validate_filter_config(self, value):
        """Validar filter_config usando FilterService."""
        if not isinstance(value, dict):
            raise serializers.ValidationError(
                "filter_config debe ser un objeto JSON (dict)"
            )
        
        # Usar FilterService para validar
        try:
            FilterService.validate_filter_config(value)
        except Exception as e:
            raise serializers.ValidationError(str(e))
        
        return value


class SavedFilterListSerializer(serializers.ModelSerializer):
    """
    Serializer para listado de filtros.
    
    Campos resumidos sin filter_config completo.
    """
    
    user_username = serializers.CharField(
        source='user.username',
        read_only=True
    )
    
    filter_type_display = serializers.CharField(
        source='get_filter_type_display',
        read_only=True
    )
    
    class Meta:
        model = SavedFilter
        fields = [
            'id',
            'user',
            'user_username',
            'filter_name',
            'filter_type',
            'filter_type_display',
            'is_public',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
