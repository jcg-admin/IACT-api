"""
Serializers para autenticación y password.

CLEAN_CODE v3.0.1: Serializers separados por responsabilidad.
SOLID SRP: Cada serializer un propósito específico.

FASE 2 PARTE 4: Serializers de apps/users/
"""

from rest_framework import serializers

from apps.users.validators import validate_password_strength


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer para cambiar password.
    
    Para usuario autenticado que cambia su propia contraseña.
    
    Fields:
    - old_password: Password actual
    - new_password: Nuevo password
    - new_password_confirm: Confirmación de nuevo password
    
    Validations:
    - old_password correcto (verificado en service)
    - new_password != old_password
    - new_password fuerte
    - new_password == new_password_confirm
    
    Example:
        data = {
            'old_password': 'OldPass123!',
            'new_password': 'NewPass456!',
            'new_password_confirm': 'NewPass456!',
        }
        serializer = PasswordChangeSerializer(data=data)
        if serializer.is_valid():
            serializer.save(user=request.user)
    """
    
    old_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text='Password actual'
    )
    
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text='Nuevo password (min 8 chars, mayús/minús/número/especial)'
    )
    
    new_password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text='Confirmación de nuevo password'
    )
    
    def validate(self, data):
        """
        Validar passwords.
        
        Args:
            data: Datos a validar
            
        Returns:
            dict: Datos validados
            
        Raises:
            ValidationError: Si validación falla
        """
        # Validar que nuevo password != viejo password
        if data['new_password'] == data['old_password']:
            raise serializers.ValidationError({
                'new_password': 'El nuevo password debe ser diferente al actual'
            })
        
        # Validar passwords coinciden
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'Las contraseñas no coinciden'
            })
        
        # Validar fortaleza de password
        try:
            validate_password_strength(data['new_password'])
        except Exception as e:
            raise serializers.ValidationError({
                'new_password': str(e)
            })
        
        return data
    
    def save(self, **kwargs):
        """
        Cambiar password.
        
        Delega a PasswordService para lógica de negocio.
        
        Args:
            **kwargs: user (User) requerido
            
        Returns:
            bool: True si cambio exitoso
            
        Raises:
            ValueError: Si user no provisto
        """
        user = kwargs.get('user')
        if not user:
            raise ValueError('Se requiere user en save(user=...)')
        
        from apps.users.services.password_service import PasswordService
        
        # Delegar a PasswordService
        PasswordService().change_password(
            user=user,
            old_password=self.validated_data['old_password'],
            new_password=self.validated_data['new_password']
        )
        
        return True


class UserActivationSerializer(serializers.Serializer):
    """
    Serializer para activar/desactivar usuario.
    
    Para staff que gestiona usuarios.
    
    Fields:
    - is_active: Estado de activación
    - reason: Razón del cambio (opcional)
    
    Example:
        # Desactivar usuario
        data = {
            'is_active': False,
            'reason': 'Usuario reportado por comportamiento inapropiado'
        }
        serializer = UserActivationSerializer(data=data)
        if serializer.is_valid():
            serializer.save(user=user)
    """
    
    is_active = serializers.BooleanField(
        required=True,
        help_text='True para activar, False para desactivar'
    )
    
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='Razón del cambio de estado (opcional)'
    )
    
    def save(self, **kwargs):
        """
        Activar/desactivar usuario.
        
        Delega a UserService para lógica de negocio.
        
        Args:
            **kwargs: user (User) requerido
            
        Returns:
            User: Usuario actualizado
            
        Raises:
            ValueError: Si user no provisto
        """
        user = kwargs.get('user')
        if not user:
            raise ValueError('Se requiere user en save(user=...)')
        
        from apps.users.services.user_service import UserService
        
        is_active = self.validated_data['is_active']
        
        if is_active:
            # Activar usuario
            UserService().activate_user(user.id)
        else:
            # Desactivar usuario
            UserService().deactivate_user(user.id)
        
        # Refrescar user
        user.refresh_from_db()
        return user


# ============================================================================
# RESUMEN AUTH SERIALIZERS
#
# Total: 2 serializers
#
# Serializers:
#   [SUCCESS] PasswordChangeSerializer - Cambiar password
#   [SUCCESS] UserActivationSerializer - Activar/desactivar usuario
#
# Responsabilidades:
#   [SUCCESS] Validación de passwords
#   [SUCCESS] Delegación a services (Password, User)
#
# NO incluye:
#   [ERROR] Login/Logout (apps/authentication)
#   [ERROR] Password reset (apps/authentication)
#
# Principios:
#   [SUCCESS] SRP: Cada serializer un propósito
#   [SUCCESS] DRY: Delegar a services
#   [SUCCESS] Validation: Passwords fuertes
#   [SUCCESS] Clean Code: Nombres auto-documentados
# ============================================================================
