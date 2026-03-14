"""
Serializers para SessionHistory.

CLEAN_CODE v3.0.1: Serializers separados por responsabilidad.
SOLID SRP: Cada serializer un propósito específico.

FASE 2 PARTE 4: Serializers de apps/users/
"""

from rest_framework import serializers

from apps.users.models import SessionHistory


class SessionHistorySerializer(serializers.ModelSerializer):
    """
    Serializer para SessionHistory.
    
    Auditoría de sesiones de usuario.
    Read-only (la creación es automática vía signals).
    
    Fields:
    - id: ID de sesión
    - username: Username del usuario (nested)
    - login_at: Fecha/hora de login
    - logout_at: Fecha/hora de logout (null si activa)
    - ip_address: IP del cliente
    - user_agent: User agent del navegador
    - is_active: Si la sesión está activa
    
    Example:
        sessions = SessionHistory.objects.filter(user=user)
        serializer = SessionHistorySerializer(sessions, many=True)
        data = serializer.data
        # [
        #   {
        #     'id': 1,
        #     'username': 'jdoe',
        #     'login_at': '2026-01-21T10:30:00Z',
        #     'logout_at': '2026-01-21T12:00:00Z',
        #     'ip_address': '192.168.1.100',
        #     'user_agent': 'Mozilla/5.0...',
        #     'is_active': False
        #   },
        #   ...
        # ]
    """
    
    username = serializers.CharField(
        source='user.username',
        read_only=True,
        help_text='Username del usuario'
    )
    
    full_name = serializers.CharField(
        source='user.get_full_name',
        read_only=True,
        help_text='Nombre completo del usuario'
    )
    
    duration = serializers.SerializerMethodField(
        help_text='Duración de la sesión en minutos (null si activa)'
    )
    
    class Meta:
        model = SessionHistory
        # CLEAN CODE: Explicit is better than implicit (PEP 20)
        fields = (
            'id',
            'username',
            'full_name',
            'login_at',
            'logout_at',
            'duration',
            'ip_address',
            'user_agent',
            'is_active',
        )
        # Session history is read-only (created by signals)
        read_only_fields = fields
    
    def get_duration(self, obj):
        """
        Calcula duración de la sesión.
        
        Args:
            obj: SessionHistory instance
            
        Returns:
            int: Duración en minutos, None si sesión activa
        """
        if obj.is_active or not obj.logout_at:
            return None
        
        delta = obj.logout_at - obj.login_at
        return int(delta.total_seconds() / 60)


# ============================================================================
# RESUMEN SESSION SERIALIZER
#
# Total: 1 serializer
#
# Serializer:
#   [SUCCESS] SessionHistorySerializer - Auditoría de sesiones
#
# Características:
#   [SUCCESS] Read-only (creación automática vía signals)
#   [SUCCESS] Campos nested (username, full_name)
#   [SUCCESS] Campos computed (duration)
#   [SUCCESS] Información de auditoría completa
#
# Uso:
#   - Ver sesiones del usuario
#   - Auditoría de accesos
#   - Historial de logins
#
# Principios:
#   [SUCCESS] SRP: Solo serialización de sesiones
#   [SUCCESS] Read-only: No modificar historial
#   [SUCCESS] Clean Code: Nombres auto-documentados
# ============================================================================
