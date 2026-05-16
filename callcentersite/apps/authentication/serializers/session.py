"""
Serializers para sesiones.

CLEAN_CODE v3.0.1: Nombres descriptivos.
SOLID SRP: Cada serializer una responsabilidad.
"""

from rest_framework import serializers

from apps.authentication.models import SessionLog
from drf_spectacular.utils import extend_schema_field, OpenApiTypes


class SessionLogSerializer(serializers.ModelSerializer):
    """
    Serializer básico para SessionLog.

    SOLID SRP: Solo representación básica de sesión.

    Read-only para listar sesiones.
    """

    username = serializers.CharField(
        source='user.username',
        read_only=True
    )

    # [SUCCESS] login_at = created_at (heredado de TimeStampedModel)
    login_at = serializers.DateTimeField(
        source='created_at',
        read_only=True
    )

    duration_seconds = serializers.SerializerMethodField()

    class Meta:
        model = SessionLog
        fields = [
            'id',
            'username',
            'session_key',
            'ip_address',
            'user_agent',
            'login_at',  # [SUCCESS] created_at
            'logout_at',
            'is_active',
            'duration_seconds'
        ]
        read_only_fields = fields

    @extend_schema_field(OpenApiTypes.INT)
    def get_duration_seconds(self, obj):
        """
        Calcula duración en segundos.

        SOLID SRP: Solo cálculo de duración.
        """
        duration = obj.duration  # [SUCCESS] Property del modelo

        if duration:
            return int(duration.total_seconds())

        return None


class SessionLogDetailSerializer(SessionLogSerializer):
    """
    Serializer detallado para SessionLog.

    SOLID SRP: Solo representación detallada.

    Incluye campos de auditoría.
    """

    created_by_username = serializers.CharField(
        source='created_by.username',
        read_only=True,
        allow_null=True
    )

    class Meta(SessionLogSerializer.Meta):
        fields = SessionLogSerializer.Meta.fields + [
            'created_at',  # [SUCCESS] Timestamp
            'updated_at',  # [SUCCESS] Timestamp
            'created_by_username',  # [SUCCESS] Auditoría
        ]
        read_only_fields = fields
