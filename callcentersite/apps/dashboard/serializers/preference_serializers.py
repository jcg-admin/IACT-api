"""
Serializers para User Dashboard Preference.

Responsabilidad: Serialización de preferencias de usuario para dashboards.

Serializers:
- UserDashboardPreferenceSerializer: Preferencias de usuario

Principios aplicados:
- SRP: Responsabilidad única (preferencias de usuario)
- Clean Code: Validaciones claras
- Validation: Validar pertenencia de dashboard al usuario
"""

from rest_framework import serializers
from apps.dashboard.models import UserDashboardPreference


class UserDashboardPreferenceSerializer(serializers.ModelSerializer):
    """
    Serializer para UserDashboardPreference.

    Incluye información enriched del dashboard y tema.
    """

    user_username = serializers.CharField(
        source='user.username',
        read_only=True
    )

    default_dashboard_name = serializers.CharField(
        source='default_dashboard.config_name',
        read_only=True,
        allow_null=True
    )

    theme_display = serializers.CharField(
        source='get_theme_display',
        read_only=True
    )

    class Meta:
        model = UserDashboardPreference
        fields = [
            'id',
            'user',
            'user_username',
            'default_dashboard',
            'default_dashboard_name',
            'theme',
            'theme_display',
            'refresh_enabled',
            'refresh_interval_seconds',
            'show_notifications',
            'preferences',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def validate_preferences(self, value):
        """Validar que preferences sea dict."""
        if not isinstance(value, dict):
            raise serializers.ValidationError(
                "preferences debe ser un objeto JSON (dict)"
            )
        return value

    def validate_refresh_interval_seconds(self, value):
        """Validar refresh_interval."""
        if value < 60 or value > 3600:
            raise serializers.ValidationError(
                "El intervalo debe estar entre 60 y 3600 segundos"
            )
        return value

    def validate(self, attrs):
        """Validar que default_dashboard pertenezca al usuario."""
        if 'default_dashboard' in attrs and attrs['default_dashboard']:
            # En creación, user viene del contexto
            user = self.instance.user if self.instance else self.context['request'].user

            if attrs['default_dashboard'].user != user:
                raise serializers.ValidationError({
                    'default_dashboard': 'El dashboard debe pertenecer al mismo usuario'
                })

        return attrs
