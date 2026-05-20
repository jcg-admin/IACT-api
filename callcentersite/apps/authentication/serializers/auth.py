"""
Serializers para autenticación.

CLEAN_CODE v3.0.1: Nombres descriptivos.
SOLID SRP: Cada serializer una responsabilidad.
"""

import re

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model

from apps.authentication.constants import PASSWORD_MIN_LENGTH, PASSWORD_MAX_LENGTH

User = get_user_model()

# FR-001.01: formato canonico de username
# - Min 3, Max 50 caracteres
# - Alfanumericos + underscore + punto
# - No inicia con numero, no espacios
USERNAME_REGEX = re.compile(r'^[A-Za-z_][A-Za-z0-9_.]{2,49}$')


class LoginSerializer(serializers.Serializer):
    """
    Serializer para login (UC_AUTH_01).

    SOLID SRP: Solo validación de credenciales de login.
    FR-001.01 conforme: valida formato username antes de credenciales.

    Fields:
    - username: Username (required, 3-50 chars, alfanum + _ + .)
    - password: Password (required)
    """

    username = serializers.CharField(
        required=True,
        min_length=3,
        max_length=50,
        help_text='Username del usuario (3-50 chars, alfanum + _ + .)'
    )

    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text='Contraseña del usuario'
    )

    def validate_username(self, value):
        """
        FR-001.01: valida formato username antes de DB query.

        Mensajes deliberadamente genericos para no revelar
        existencia de usuarios (CNST-005 nota seguridad).
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Username invalido")

        value = value.strip()
        if not USERNAME_REGEX.match(value):
            raise serializers.ValidationError("Username invalido")

        return value

    def validate_password(self, value):
        """
        Valida password.

        SOLID SRP: Solo validación de password.
        """
        if not value:
            raise serializers.ValidationError("Password no puede estar vacío")

        return value


class LogoutSerializer(serializers.Serializer):
    """
    Serializer para logout.

    SOLID SRP: Solo logout (sin campos).

    No requiere campos adicionales, usa request.user.
    """
    pass


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer para cambio de contraseña.

    SOLID SRP: Solo cambio de password.

    Fields:
    - current_password: Password actual (required)
    - new_password: Password nueva (required)
    - confirm_password: Confirmación (required)
    """

    current_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text='Contraseña actual'
    )

    new_password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=PASSWORD_MIN_LENGTH,
        max_length=PASSWORD_MAX_LENGTH,
        style={'input_type': 'password'},
        help_text='Nueva contraseña'
    )

    confirm_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text='Confirmar nueva contraseña'
    )

    def validate(self, attrs):
        """
        Valida que las contraseñas coincidan.

        SOLID SRP: Solo validación de coincidencia.
        """
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')

        if new_password != confirm_password:
            raise serializers.ValidationError({
                'confirm_password': 'Las contraseñas no coinciden'
            })

        return attrs


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """JWT con claims custom (username, email)."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['email'] = user.email
        return token
