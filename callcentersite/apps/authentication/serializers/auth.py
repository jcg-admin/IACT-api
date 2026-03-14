"""
Serializers para autenticación.

CLEAN_CODE v3.0.1: Nombres descriptivos.
SOLID SRP: Cada serializer una responsabilidad.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

from apps.authentication.constants import PASSWORD_MIN_LENGTH, PASSWORD_MAX_LENGTH

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    """
    Serializer para login.
    
    SOLID SRP: Solo validación de credenciales de login.
    
    Fields:
    - username: Username (required)
    - password: Password (required)
    """
    
    username = serializers.CharField(
        required=True,
        max_length=150,
        help_text='Username del usuario'
    )
    
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text='Contraseña del usuario'
    )
    
    def validate_username(self, value):
        """
        Valida username.
        
        SOLID SRP: Solo validación de username.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Username no puede estar vacío")
        
        return value.strip()
    
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
