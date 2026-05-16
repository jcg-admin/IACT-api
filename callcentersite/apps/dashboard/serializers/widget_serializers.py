"""
Serializers para Widget Config.

Responsabilidad: Serialización de widgets de dashboards.

Serializers:
- WidgetConfigSerializer: Serializer básico de widget
- WidgetConfigCreateSerializer: Para creación de widgets
- WidgetConfigUpdateSerializer: Para actualización de widgets
- WidgetDataSerializer: Para respuestas de datos de widgets

Principios aplicados:
- SRP: Responsabilidad única (widgets)
- Clean Code: Validaciones claras
- DRY: Reutilización de validaciones
"""

from rest_framework import serializers
from apps.dashboard.models import WidgetConfig


class WidgetConfigSerializer(serializers.ModelSerializer):
    """
    Serializer básico para WidgetConfig.

    Incluye todos los campos excepto dashboard (se infiere del contexto).
    """

    widget_type_display = serializers.CharField(
        source='get_widget_type_display',
        read_only=True
    )

    class Meta:
        model = WidgetConfig
        fields = [
            'id',
            'widget_type',
            'widget_type_display',
            'widget_name',
            'position_x',
            'position_y',
            'width',
            'height',
            'config_data',
            'is_visible',
            'refresh_interval_seconds',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_config_data(self, value):
        """Validar que config_data sea dict."""
        if not isinstance(value, dict):
            raise serializers.ValidationError(
                "config_data debe ser un objeto JSON (dict)"
            )
        return value

    def validate(self, attrs):
        """Validar dimensiones y refresh_interval."""
        # Validar width
        if 'width' in attrs:
            if attrs['width'] < 1 or attrs['width'] > 12:
                raise serializers.ValidationError({
                    'width': 'El ancho debe estar entre 1 y 12'
                })

        # Validar height
        if 'height' in attrs:
            if attrs['height'] < 1:
                raise serializers.ValidationError({
                    'height': 'El alto debe ser mayor a 0'
                })

        # Validar refresh_interval
        if 'refresh_interval_seconds' in attrs:
            interval = attrs['refresh_interval_seconds']
            if interval < 60 or interval > 3600:
                raise serializers.ValidationError({
                    'refresh_interval_seconds': 'El intervalo debe estar entre 60 y 3600 segundos'
                })

        return attrs


class WidgetConfigCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para creación de widgets.

    Incluye dashboard en el payload.
    """

    class Meta:
        model = WidgetConfig
        fields = [
            'dashboard',
            'widget_type',
            'widget_name',
            'position_x',
            'position_y',
            'width',
            'height',
            'config_data',
            'is_visible',
            'refresh_interval_seconds'
        ]

    def validate_config_data(self, value):
        """Validar config_data."""
        if not isinstance(value, dict):
            raise serializers.ValidationError(
                "config_data debe ser un objeto JSON (dict)"
            )
        return value

    def validate(self, attrs):
        """Validar dimensiones, ownership y solapamiento."""
        # Validar dimensiones
        if attrs['width'] < 1 or attrs['width'] > 12:
            raise serializers.ValidationError({
                'width': 'El ancho debe estar entre 1 y 12'
            })

        if attrs['height'] < 1:
            raise serializers.ValidationError({
                'height': 'El alto debe ser mayor a 0'
            })

        # Validar refresh_interval
        if 'refresh_interval_seconds' in attrs:
            interval = attrs['refresh_interval_seconds']
            if interval < 60 or interval > 3600:
                raise serializers.ValidationError({
                    'refresh_interval_seconds': 'El intervalo debe estar entre 60 y 3600 segundos'
                })

        # Validar ownership del dashboard
        request = self.context.get('request')
        if request and attrs['dashboard'].user != request.user:
            raise serializers.ValidationError({
                'dashboard': 'No puedes agregar widgets a un dashboard que no te pertenece'
            })

        return attrs


class WidgetConfigUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para actualización de widgets.

    No permite cambiar dashboard.
    """

    class Meta:
        model = WidgetConfig
        fields = [
            'widget_type',
            'widget_name',
            'position_x',
            'position_y',
            'width',
            'height',
            'config_data',
            'is_visible',
            'refresh_interval_seconds'
        ]

    def validate_config_data(self, value):
        """Validar config_data."""
        if not isinstance(value, dict):
            raise serializers.ValidationError(
                "config_data debe ser un objeto JSON (dict)"
            )
        return value

    def validate(self, attrs):
        """Validar dimensiones y refresh_interval."""
        if 'width' in attrs and (attrs['width'] < 1 or attrs['width'] > 12):
            raise serializers.ValidationError({
                'width': 'El ancho debe estar entre 1 y 12'
            })

        if 'height' in attrs and attrs['height'] < 1:
            raise serializers.ValidationError({
                'height': 'El alto debe ser mayor a 0'
            })

        if 'refresh_interval_seconds' in attrs:
            interval = attrs['refresh_interval_seconds']
            if interval < 60 or interval > 3600:
                raise serializers.ValidationError({
                    'refresh_interval_seconds': 'El intervalo debe estar entre 60 y 3600 segundos'
                })

        return attrs


class WidgetDataSerializer(serializers.Serializer):
    """
    Serializer para respuestas de datos de widgets.

    No está vinculado a un modelo.
    Usado para serializar respuestas de WidgetService.get_widget_data().
    """

    widget_id = serializers.IntegerField(read_only=True)
    widget_name = serializers.CharField(read_only=True)
    widget_type = serializers.CharField(read_only=True)
    data = serializers.JSONField(read_only=True)
    cached = serializers.BooleanField(read_only=True, default=False)
    timestamp = serializers.DateTimeField(read_only=True)

    def to_representation(self, instance):
        """
        Personalizar representación.

        instance debería ser un dict con:
        - widget_id
        - widget_name
        - widget_type
        - data (resultado de calculate_*_data)
        - cached
        - timestamp
        """
        return {
            'widget_id': instance.get('widget_id'),
            'widget_name': instance.get('widget_name'),
            'widget_type': instance.get('widget_type'),
            'data': instance.get('data'),
            'cached': instance.get('cached', False),
            'timestamp': instance.get('timestamp')
        }
