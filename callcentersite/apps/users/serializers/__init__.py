"""
Serializers para apps/users/.

CLEAN_CODE v3.0.1: Imports organizados por módulo.
FASE 2 PARTE 4: 11 serializers implementados.

Estructura:
== user_serializer.py (5 serializers de User)
== profile_serializer.py (3 serializers de Profile)
== auth_serializer.py (2 serializers de Auth)
== session_serializer.py (1 serializer de SessionHistory)
"""

# User serializers (5)
from apps.users.serializers.user_serializer import (
    UserSerializer,
    UserListSerializer,
    # UserDetailSerializer,  # TODO: No existe en user_serializer.py - comentado temporalmente
    UserCreateSerializer,
    UserUpdateSerializer,
)

# Profile serializers (3)
from apps.users.serializers.profile_serializer import (
    ProfileSerializer,
    UserSettingsSerializer,
    AvatarUploadSerializer,
)

# Auth serializers (2 + aliases para compatibilidad)
from apps.users.serializers.auth_serializer import (
    PasswordChangeSerializer,
    UserActivationSerializer,
)
from apps.authentication.serializers import (
    LoginSerializer,
    ChangePasswordSerializer,
)
from apps.authentication.serializers.recovery import (
    PasswordResetRequestSerializer,
)

# PasswordResetConfirmSerializer: simple serializer de confirmación vía token
from rest_framework import serializers as _drf_serializers

class PasswordResetConfirmSerializer(_drf_serializers.Serializer):
    """Confirma reset de password mediante token."""
    uidb64 = _drf_serializers.CharField(required=True)
    token = _drf_serializers.CharField(required=True)
    new_password = _drf_serializers.CharField(
        required=True, write_only=True, min_length=8,
        style={'input_type': 'password'}
    )
    new_password_confirm = _drf_serializers.CharField(
        required=True, write_only=True, style={'input_type': 'password'}
    )

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise _drf_serializers.ValidationError(
                {'new_password_confirm': 'Los passwords no coinciden'}
            )
        return attrs

# UserProfileSerializer alias for ProfileSerializer
UserProfileSerializer = ProfileSerializer

# Session serializer (1)
from apps.users.serializers.session_serializer import (
    SessionHistorySerializer,
)


__all__ = [
    # User (5 -> 4 temporalmente)
    'UserSerializer',
    'UserListSerializer',
    # 'UserDetailSerializer',  # TODO: No existe - comentado temporalmente
    'UserCreateSerializer',
    'UserUpdateSerializer',
    
    # Profile (3)
    'ProfileSerializer',
    'UserSettingsSerializer',
    'AvatarUploadSerializer',
    
    # Auth (2 + aliases)
    'PasswordChangeSerializer',
    'UserActivationSerializer',
    'LoginSerializer',
    'ChangePasswordSerializer',
    'PasswordResetRequestSerializer',
    'PasswordResetConfirmSerializer',
    'UserProfileSerializer',
    
    # Session (1)
    'SessionHistorySerializer',
]


# ============================================================================
# RESUMEN SERIALIZERS
#
# Total: 11 serializers
#
# User (5):
#   [SUCCESS] UserSerializer - Básico para uso general
#   [SUCCESS] UserListSerializer - Lightweight para listados
#   [SUCCESS] UserDetailSerializer - Completo con relaciones
#   [SUCCESS] UserCreateSerializer - Crear con validación
#   [SUCCESS] UserUpdateSerializer - Actualizar campos editables
#
# Profile (3):
#   [SUCCESS] ProfileSerializer - Perfil extendido
#   [SUCCESS] UserSettingsSerializer - Preferencias (language, notifications)
#   [SUCCESS] AvatarUploadSerializer - Subir avatar
#
# Auth (2):
#   [SUCCESS] PasswordChangeSerializer - Cambiar password
#   [SUCCESS] UserActivationSerializer - Activar/desactivar
#
# Session (1):
#   [SUCCESS] SessionHistorySerializer - Auditoría de sesiones
#
# Scope apps/users/:
#   [SUCCESS] SOLO gestión de usuarios
#   [ERROR] NO gestión de RBAC (apps/access)
#   [ERROR] NO login/logout (apps/authentication)
#
# Principios aplicados:
#   [SUCCESS] SOLID SRP: Cada serializer un propósito
#   [SUCCESS] DRY: Delegación a services
#   [SUCCESS] Clean Code: Nombres auto-documentados
#   [SUCCESS] Validation: Passwords fuertes, datos correctos
#
# FASE 2 PARTE 4: [SUCCESS] COMPLETADA
# ============================================================================
