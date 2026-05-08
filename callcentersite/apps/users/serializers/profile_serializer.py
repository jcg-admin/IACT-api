"""
Serializers para UserProfile y UserSettings.

CLEAN_CODE v3.0.1: Serializers separados por responsabilidad.
SOLID SRP: Cada serializer un propósito específico.

FASE 2 PARTE 4: Serializers de apps/users/
"""

from rest_framework import serializers

try:
    from apps.users.models import UserProfile, UserSettings
except ImportError:
    UserProfile = UserSettings = None
from apps.users.validators import validate_avatar_size as validate_avatar_file


class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializer para UserProfile.
    
    Perfil extendido del usuario.
    
    Fields:
    - bio: Biografía (opcional)
    - department: Departamento (choices)
    - avatar_url: URL del avatar (computed, read-only)
    
    Example:
        profile = UserProfile.objects.get(user_id=1)
        serializer = ProfileSerializer(profile)
        data = serializer.data
        # {'bio': '...', 'department': 'IT', 'avatar_url': '/media/...'}
    """
    
    avatar_url = serializers.CharField(
        read_only=True,
        help_text='URL del avatar o default'
    )
    
    class Meta:
        model = UserProfile
        fields = [
            'bio',
            'department',
            'avatar_url',
        ]
    
    def update(self, instance, validated_data):
        """
        Actualizar profile.
        
        Delega a ProfileService para lógica de negocio.
        
        Args:
            instance: Profile existente
            validated_data: Datos validados
            
        Returns:
            UserProfile: Profile actualizado
        """
        from apps.users.services.profile_service import ProfileService
        
        profile = ProfileService().update_profile(
            user_id=instance.user.id,
            **validated_data
        )
        
        return profile


class UserSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer para UserSettings.
    
    FASE 2 PARTE 2: Solo preferencias personales.
    
    Fields:
    - language: Idioma de interfaz (es, en)
    - notifications_enabled: Habilitar alertas internas
    
    NO incluye (son config del sistema):
    - theme: Configuración del sistema
    - timezone: America/Mexico_City (config del sistema)
    - email_notifications: Sistema de alertas
    
    Example:
        settings = UserSettings.objects.get(user_id=1)
        serializer = UserSettingsSerializer(settings)
        data = serializer.data
        # {'language': 'es', 'notifications_enabled': True}
    """
    
    class Meta:
        model = UserSettings
        fields = [
            'language',
            'notifications_enabled',
        ]
    
    def update(self, instance, validated_data):
        """
        Actualizar settings.
        
        Args:
            instance: Settings existentes
            validated_data: Datos validados
            
        Returns:
            UserSettings: Settings actualizados
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance


class AvatarUploadSerializer(serializers.Serializer):
    """
    Serializer para subir avatar.
    
    Validación y delegación a ProfileService.
    
    Fields:
    - avatar: Archivo de imagen (ImageField)
    
    Validations:
    - Formatos: jpg, jpeg, png, gif
    - Tamaño máximo: 2MB
    
    Example:
        data = {'avatar': uploaded_file}
        serializer = AvatarUploadSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save(user=request.user)
    """
    
    avatar = serializers.ImageField(
        required=True,
        help_text='Archivo de imagen (jpg, png, gif, max 2MB)'
    )
    
    def validate_avatar(self, value):
        """
        Validar archivo de avatar.
        
        Args:
            value: Archivo subido
            
        Returns:
            File: Archivo validado
            
        Raises:
            ValidationError: Si archivo inválido
        """
        try:
            validate_avatar_file(value)
        except Exception as e:
            raise serializers.ValidationError(str(e))
        
        return value
    
    def update(self, instance, validated_data):
        """
        Subir avatar.
        
        Delega a ProfileService para lógica de negocio.
        
        Args:
            instance: User
            validated_data: Datos validados con avatar
            
        Returns:
            User: Usuario con avatar actualizado
        """
        from apps.users.services.profile_service import ProfileService
        
        user = ProfileService().upload_avatar(
            user=instance,
            avatar_file=validated_data['avatar']
        )
        
        return user
    
    def create(self, validated_data):
        """
        No permitir create, solo update.
        
        Raises:
            NotImplementedError: Siempre
        """
        raise NotImplementedError('Use update() con user existente')


# ============================================================================
# RESUMEN PROFILE SERIALIZERS
#
# Total: 3 serializers
#
# Serializers:
#   [SUCCESS] ProfileSerializer - UserProfile (bio, department)
#   [SUCCESS] UserSettingsSerializer - Preferencias (language, notifications)
#   [SUCCESS] AvatarUploadSerializer - Subir avatar
#
# FASE 2 PARTE 2 aplicada:
#   [SUCCESS] UserSettings solo language y notifications_enabled
#   [ERROR] NO theme, timezone, email_notifications
#
# Responsabilidades:
#   [SUCCESS] Validación de datos
#   [SUCCESS] Delegación a ProfileService
#
# Principios:
#   [SUCCESS] SRP: Cada serializer un propósito
#   [SUCCESS] DRY: Delegar a services
#   [SUCCESS] Clean Code: Nombres auto-documentados
# ============================================================================
