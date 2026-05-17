"""
Serializers para Sistema de Alertas.

Responsabilidad: Serialización de configuraciones y suscripciones de alertas.

Serializers:
- AlertConfigurationSerializer: Configuración de alerta
- AlertSubscriptionSerializer: Suscripción a alerta
- AlertSubscriptionCreateSerializer: Creación simplificada de suscripción

Principios aplicados:
- SRP: Responsabilidad única (alertas)
- Clean Code: Validaciones de condiciones
- Service Layer: Uso de SubscriptionService para lógica de negocio
"""

from rest_framework import serializers
from apps.alerts.models import AlertConfiguration, AlertSubscription
from drf_spectacular.utils import extend_schema_field, OpenApiTypes


class AlertConfigurationSerializer(serializers.ModelSerializer):
    """
    Serializer para configuración de alertas.

    Incluye validación de estructura de condición y conteo de suscriptores.

    Estructura de condición:
    {
        "metric": "call_volume" | "avg_wait_time" | "sla_percentage",
        "operator": ">" | "<" | ">=" | "<=" | "==",
        "value": number,
        "period": "30m" | "1h" | "6h" | "12h" | "1d"
    }
    """

    subscriber_count = serializers.SerializerMethodField()

    class Meta:
        model = AlertConfiguration
        fields = [
            'id',
            'name',
            'description',
            'condition',
            'priority',
            'is_active',
            'last_evaluated_at',
            'last_triggered_at',
            'subscriber_count',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'last_evaluated_at', 'last_triggered_at', 'created_at', 'updated_at']

    @extend_schema_field(OpenApiTypes.INT)
    def get_subscriber_count(self, obj):
        """Contar suscriptores activos."""
        return obj.subscriptions.filter(is_active=True, deleted_at__isnull=True).count()

    def validate_condition(self, value):
        """
        Validar estructura de condition.

        Valida que tenga los campos requeridos y valores válidos.
        """
        required_keys = ['metric', 'operator', 'value', 'period']

        for key in required_keys:
            if key not in value:
                raise serializers.ValidationError(
                    f"Campo '{key}' es requerido en condition"
                )

        # Validar metric
        valid_metrics = ['call_volume', 'avg_wait_time', 'sla_percentage']
        if value['metric'] not in valid_metrics:
            raise serializers.ValidationError(
                f"metric debe ser uno de: {', '.join(valid_metrics)}"
            )

        # Validar operator
        valid_operators = ['>', '<', '>=', '<=', '==']
        if value['operator'] not in valid_operators:
            raise serializers.ValidationError(
                f"operator debe ser uno de: {', '.join(valid_operators)}"
            )

        # Validar period
        valid_periods = ['30m', '1h', '6h', '12h', '1d']
        if value['period'] not in valid_periods:
            raise serializers.ValidationError(
                f"period debe ser uno de: {', '.join(valid_periods)}"
            )

        return value


class AlertSubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer para suscripción a alertas.

    Permite ver y gestionar suscripciones del usuario.
    """

    user = serializers.SerializerMethodField()
    alert_configuration_name = serializers.CharField(
        source='alert_configuration.name',
        read_only=True
    )

    class Meta:
        model = AlertSubscription
        fields = [
            'id',
            'user',
            'alert_configuration',
            'alert_configuration_name',
            'is_active',
            'subscribed_at'
        ]
        read_only_fields = ['id', 'user', 'subscribed_at']

    @extend_schema_field(OpenApiTypes.STR)
    def get_user(self, obj):
        """
        Serializar información básica del usuario.

        Importa localmente para evitar circular imports.
        """
        from apps.alerts.serializers.message_serializers import UserBasicSerializer
        return UserBasicSerializer(obj.user).data

    def create(self, validated_data):
        """
        Crear suscripción usando SubscriptionService.

        El usuario se obtiene automáticamente del request.user.
        """
        from apps.alerts.services import SubscriptionService

        user = self.context['request'].user
        alert_configuration = validated_data['alert_configuration']

        subscription = SubscriptionService.subscribe(
            user=user,
            alert_configuration=alert_configuration
        )

        return subscription


class AlertSubscriptionCreateSerializer(serializers.Serializer):
    """
    Serializer simple para crear suscripción.

    Solo requiere el ID de la configuración de alerta.
    El usuario se obtiene del request.user.
    """

    alert_configuration_id = serializers.IntegerField()

    def validate_alert_configuration_id(self, value):
        """Validar que la configuración existe y no está eliminada."""
        try:
            AlertConfiguration.objects.get(id=value, deleted_at__isnull=True)
        except AlertConfiguration.DoesNotExist:
            raise serializers.ValidationError('Configuración de alerta no encontrada')
        return value

    def create(self, validated_data):
        """
        Crear suscripción usando SubscriptionService.

        El usuario se obtiene automáticamente del request.user.
        """
        from apps.alerts.services import SubscriptionService

        user = self.context['request'].user
        alert_configuration = AlertConfiguration.objects.get(
            id=validated_data['alert_configuration_id']
        )

        subscription = SubscriptionService.subscribe(
            user=user,
            alert_configuration=alert_configuration
        )

        return subscription
