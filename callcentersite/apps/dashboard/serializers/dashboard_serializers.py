"""
Serializers para Dashboard Config.

Responsabilidad: Serialización de configuraciones de dashboards.

Serializers:
- DashboardConfigSerializer: Serializer básico de dashboard
- DashboardConfigListSerializer: Para listados
- DashboardConfigDetailSerializer: Con widgets anidados
- DashboardExportSerializer: Para exportación
- DashboardImportSerializer: Para importación

Principios aplicados:
- SRP: Responsabilidad única (dashboards)
- Clean Code: Nombres descriptivos
- Validation: Validaciones robustas
"""

from rest_framework import serializers
from apps.dashboard.models import DashboardConfig, WidgetConfig


class DashboardConfigSerializer(serializers.ModelSerializer):
    """
    Serializer básico para DashboardConfig.
    
    Usado para creación y actualización.
    """
    
    user_username = serializers.CharField(
        source='user.username',
        read_only=True
    )
    
    class Meta:
        model = DashboardConfig
        fields = [
            'id',
            'user',
            'user_username',
            'config_name',
            'description',
            'layout_config',
            'is_default',
            'is_public',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def validate_layout_config(self, value):
        """Validar que layout_config sea dict."""
        if not isinstance(value, dict):
            raise serializers.ValidationError(
                "layout_config debe ser un objeto JSON (dict)"
            )
        return value


class DashboardConfigListSerializer(serializers.ModelSerializer):
    """
    Serializer para listado de dashboards.
    
    Incluye campos resumidos + conteo de widgets.
    """
    
    user_username = serializers.CharField(
        source='user.username',
        read_only=True
    )
    
    widget_count = serializers.SerializerMethodField()
    
    class Meta:
        model = DashboardConfig
        fields = [
            'id',
            'user',
            'user_username',
            'config_name',
            'description',
            'is_default',
            'is_public',
            'widget_count',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_widget_count(self, obj):
        """Contar widgets del dashboard."""
        return obj.widgets.count()


class DashboardConfigDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detallado para dashboard.
    
    Incluye widgets anidados.
    Importa WidgetConfigSerializer localmente para evitar import circular.
    """
    
    user_username = serializers.CharField(
        source='user.username',
        read_only=True
    )
    
    widgets = serializers.SerializerMethodField()
    
    class Meta:
        model = DashboardConfig
        fields = [
            'id',
            'user',
            'user_username',
            'config_name',
            'description',
            'layout_config',
            'is_default',
            'is_public',
            'widgets',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_widgets(self, obj):
        """Serializar widgets anidados."""
        from apps.dashboard.serializers.widget_serializers import WidgetConfigSerializer
        widgets = obj.widgets.all()
        return WidgetConfigSerializer(widgets, many=True).data


class DashboardExportSerializer(serializers.Serializer):
    """
    Serializer para exportación de dashboards.
    
    Genera estructura JSON para exportar.
    """
    
    version = serializers.CharField(read_only=True)
    dashboard = serializers.DictField(read_only=True)
    widgets = serializers.ListField(
        child=serializers.DictField(),
        read_only=True
    )
    
    def to_representation(self, instance):
        """
        Serializar dashboard para exportación.
        
        instance debe ser resultado de DashboardService.export_config()
        """
        return {
            'version': instance.get('version', '1.0'),
            'dashboard': instance.get('dashboard', {}),
            'widgets': instance.get('widgets', [])
        }


class DashboardImportSerializer(serializers.Serializer):
    """
    Serializer para importación de dashboards.
    
    Valida estructura JSON antes de importar.
    """
    
    version = serializers.CharField(required=False, default='1.0')
    dashboard = serializers.DictField(required=True)
    widgets = serializers.ListField(
        child=serializers.DictField(),
        required=True
    )
    
    def validate_dashboard(self, value):
        """Validar estructura de dashboard."""
        required_fields = ['config_name']
        
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(
                    f"Campo requerido en dashboard: {field}"
                )
        
        # Validar layout_config si existe
        if 'layout_config' in value and not isinstance(value['layout_config'], dict):
            raise serializers.ValidationError(
                "layout_config debe ser un objeto JSON"
            )
        
        return value
    
    def validate_widgets(self, value):
        """Validar estructura de widgets."""
        if not isinstance(value, list):
            raise serializers.ValidationError(
                "widgets debe ser una lista"
            )
        
        required_fields = ['widget_type', 'widget_name']
        
        for idx, widget in enumerate(value):
            for field in required_fields:
                if field not in widget:
                    raise serializers.ValidationError(
                        f"Widget {idx}: Campo requerido: {field}"
                    )
            
            # Validar widget_type
            valid_types = [choice[0] for choice in WidgetConfig.WIDGET_TYPES]
            if widget['widget_type'] not in valid_types:
                raise serializers.ValidationError(
                    f"Widget {idx}: widget_type inválido: {widget['widget_type']}"
                )
            
            # Validar config_data si existe
            if 'config_data' in widget and not isinstance(widget['config_data'], dict):
                raise serializers.ValidationError(
                    f"Widget {idx}: config_data debe ser un objeto JSON"
                )
        
        return value
    
    def validate(self, attrs):
        """Validación general."""
        # Verificar que no haya más de 20 widgets (límite razonable)
        if len(attrs['widgets']) > 20:
            raise serializers.ValidationError({
                'widgets': 'Máximo 20 widgets permitidos por dashboard'
            })
        
        return attrs
    
    def create(self, validated_data):
        """
        Crear dashboard desde datos importados.
        
        No usado directamente, el ViewSet usará DashboardService.import_config()
        """
        raise NotImplementedError(
            "Usar DashboardService.import_config() para importar"
        )
