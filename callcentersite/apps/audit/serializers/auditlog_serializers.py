"""
Serializers para AuditLog (Logs de auditoría).

Responsabilidad: Serialización de logs de auditoría (READ-ONLY).

Serializers:
- AuditLogSerializer: Log completo con información de usuario
- AuditLogSummarySerializer: Resumen para listados

Características:
- READ-ONLY: Los logs de auditoría son inmutables
- Campos enriched: username, full_name
- Performance: Versión summary sin campos pesados

Principios aplicados:
- SRP: Responsabilidad única (logs de auditoría)
- Clean Code: Información de usuario enriquecida
- Immutability: Todos los campos son read-only
"""

from rest_framework import serializers
from apps.audit.models import AuditLog
from drf_spectacular.utils import extend_schema_field, OpenApiTypes


class AuditLogSerializer(serializers.ModelSerializer):
    """
    Serializer para AuditLog (readonly).
    
    Muestra información completa del log de auditoría.
    Incluye username, full_name, y todos los detalles del evento.
    
    Los logs de auditoría son inmutables por diseño (no create/update/delete).
    """
    
    user_username = serializers.CharField(
        source='user.username',
        read_only=True,
        allow_null=True
    )
    user_full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = AuditLog
        fields = [
            'id',
            'user',
            'user_username',
            'user_full_name',
            'action',
            'resource',
            'result',
            'timestamp',
            'ip_address',
            'user_agent',
            'details',
        ]
        read_only_fields = fields  # Todos readonly (inmutable)
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_user_full_name(self, obj):
        """
        Obtener nombre completo del usuario.
        
        Returns:
            str: Nombre completo o username si no tiene nombre, None si no hay usuario
        """
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        return None


class AuditLogSummarySerializer(serializers.ModelSerializer):
    """
    Serializer resumido para listados.
    
    Omite detalles pesados como user_agent y details para mejor performance.
    Ideal para listados con muchos registros.
    """
    
    user_username = serializers.CharField(
        source='user.username',
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = AuditLog
        fields = [
            'id',
            'user_username',
            'action',
            'resource',
            'result',
            'timestamp',
            'ip_address',
        ]
        read_only_fields = fields
