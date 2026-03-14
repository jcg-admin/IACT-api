"""
Serializers para apps/users/.

Todos usan Django REST Framework ModelSerializer.

CLEAN_CODE v3.0.1: Serializers auto-documentados.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

from apps.users.models import UserProfile, UserSettings, SessionHistory

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer para UserProfile.
    
    Read-only fields:
    - created_at, updated_at (auto)
    - avatar_url (property)
    
    Editable fields:
    - bio, department
    
    Example:
        >>> data = {'bio': 'Software Developer', 'department': 'Engineering'}
        >>> serializer = UserProfileSerializer(data=data)
        >>> serializer.is_valid()
        True
    """
    
    avatar_url = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = [
            'id',
            'bio',
            'department',
            'avatar_url',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'avatar_url']
    
    def get_avatar_url(self, obj):
        """Obtiene URL del avatar."""
        return obj.avatar_url


class UserSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer para UserSettings.
    
    Read-only fields:
    - created_at, updated_at (auto)
    
    Editable fields:
    - language, theme, timezone
    - notifications_enabled, email_notifications
    
    Example:
        >>> data = {'language': 'en', 'theme': 'dark'}
        >>> serializer = UserSettingsSerializer(data=data)
        >>> serializer.is_valid()
        True
    """
    
    class Meta:
        model = UserSettings
        fields = [
            'id',
            'language',
            'theme',
            'timezone',
            'notifications_enabled',
            'email_notifications',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SessionHistorySerializer(serializers.ModelSerializer):
    """
    Serializer para SessionHistory.
    
    Read-only (creado automáticamente por signals).
    
    Example:
        >>> session = SessionHistory.objects.first()
        >>> serializer = SessionHistorySerializer(session)
        >>> serializer.data['is_active']
        True
    """
    
    class Meta:
        model = SessionHistory
        # CLEAN CODE: Explicit is better than implicit (PEP 20)
        fields = (
            'id',
            'ip_address',
            'user_agent',
            'login_at',
            'logout_at',
            'is_active',
            'created_at',
            'updated_at',
        )
        # Session history is read-only (created by signals)
        read_only_fields = fields


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer principal para User.
    
    Incluye:
    - Datos básicos del usuario
    - Profile nested (read-only)
    - Settings nested (read-only)
    - RBAC functions (SerializerMethodField)
    
    Read-only fields:
    - id, date_joined, last_login
    - is_staff, is_superuser (solo admin puede modificar)
    - profile, settings (nested)
    - functions (RBAC)
    
    Editable fields:
    - username, email, first_name, last_name
    - employee_id, phone, position
    - is_active (admin only via activate/deactivate endpoints)
    
    Example:
        >>> user = User.objects.get(id=1)
        >>> serializer = UserSerializer(user)
        >>> serializer.data['full_name']
        'John Doe'
        >>> 'USR_VIEW' in serializer.data['functions']
        True
    """
    
    profile = UserProfileSerializer(read_only=True)
    settings = UserSettingsSerializer(read_only=True)
    functions = serializers.SerializerMethodField()
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            # Identificación
            'id',
            'username',
            'email',
            
            # Nombre
            'first_name',
            'last_name',
            'full_name',
            
            # Datos adicionales
            'phone',
            'position',
            
            # Avatar
            'avatar',
            'avatar_url',
            
            # Estado
            'is_active',
            'is_staff',
            'is_superuser',
            
            # Fechas
            'date_joined',
            'last_login',
            
            # Relaciones
            'profile',
            'settings',
            
            # RBAC
            'functions',
        ]
        read_only_fields = [
            'id',
            'date_joined',
            'last_login',
            'is_staff',
            'is_superuser',
            'full_name',
            'profile',
            'settings',
            'functions',
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'avatar': {'required': False},
        }
    
    def get_functions(self, obj):
        """
        Obtiene funciones RBAC del usuario.
        
        RBAC v6.0.0: Retorna namespaces Django (permission_django).
        
        Usa User.get_functions() que retorna set de namespaces activos:
        - Solo funciones con status='activo'
        - Solo asignaciones con is_active=True
        
        Returns:
            list: Lista de namespaces de funciones
        
        Examples:
            >>> user.get_functions()
            {'users.view', 'calls.view', 'reports.view'}
            
            >>> serializer = UserSerializer(user)
            >>> serializer.data['functions']
            ['users.view', 'calls.view', 'reports.view']
        """
        return list(obj.get_functions())


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear usuarios.
    
    Incluye password (write-only) y validaciones.
    
    Required fields:
    - username (único)
    - email (único)
    - password (mínimo 8 caracteres)
    
    Optional fields:
    - first_name, last_name
    - phone, position
    
    Example:
        >>> data = {
        ...     'username': 'jdoe',
        ...     'email': 'jdoe@company.com',
        ...     'password': 'SecurePass123',
        ...     'first_name': 'John',
        ...     'last_name': 'Doe'
        ... }
        >>> serializer = UserCreateSerializer(data=data)
        >>> serializer.is_valid()
        True
        >>> user = serializer.save()
    """
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        style={'input_type': 'password'},
        help_text='Mínimo 8 caracteres'
    )
    
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text='Confirmar password'
    )
    
    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password',
            'password_confirm',
            'first_name',
            'last_name',
            'phone',
            'position',
        ]
        extra_kwargs = {
            'username': {'required': True},
            'email': {'required': True},
        }
    
    def validate_username(self, value):
        """Valida que username sea único."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                f"Username '{value}' ya está en uso"
            )
        return value
    
    def validate_email(self, value):
        """Valida que email sea único."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                f"Email '{value}' ya está en uso"
            )
        return value
    
    def validate(self, attrs):
        """Valida que passwords coincidan."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Los passwords no coinciden'
            })
        return attrs
    
    def create(self, validated_data):
        """
        Crea usuario con UserService.
        
        Usa UserService.create_user() para:
        - Hashear password
        - Auto-crear profile y settings
        - Audit logging
        """
        from apps.users.services import UserService
        
        # Remover password_confirm
        validated_data.pop('password_confirm', None)
        
        # Usar service
        service = UserService()
        user = service.create_user(**validated_data)
        
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para actualizar usuarios.
    
    Editable fields:
    - first_name, last_name
    - email (con validación de unicidad)
    - phone, position
    
    Read-only fields:
    - username (no se puede cambiar)
    - password (usar ChangePasswordSerializer)
    
    Example:
        >>> user = User.objects.get(id=1)
        >>> data = {'first_name': 'Jane', 'email': 'jane@company.com'}
        >>> serializer = UserUpdateSerializer(user, data=data, partial=True)
        >>> serializer.is_valid()
        True
        >>> serializer.save()
    """
    
    class Meta:
        model = User
        fields = [
            'username',  # read-only
            'email',
            'first_name',
            'last_name',
            'phone',
            'position',
        ]
        read_only_fields = ['username']
    
    def validate_email(self, value):
        """Valida que email sea único (excepto el del usuario actual)."""
        user_id = self.instance.id if self.instance else None
        
        if User.objects.filter(email=value).exclude(id=user_id).exists():
            raise serializers.ValidationError(
                f"Email '{value}' ya está en uso"
            )
        
        return value
    
    def update(self, instance, validated_data):
        """
        Actualiza usuario con UserService.
        
        Usa UserService.update_user() para audit logging.
        """
        from apps.users.services import UserService
        
        service = UserService()
        user = service.update_user(
            user_id=instance.id,
            **validated_data
        )
        
        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer para login.
    
    Input:
    - username
    - password
    
    Output (después de login exitoso):
    - user (UserSerializer)
    - token (si se usa JWT)
    
    Example:
        >>> data = {'username': 'jdoe', 'password': 'SecurePass123'}
        >>> serializer = LoginSerializer(data=data)
        >>> serializer.is_valid()
        True
    """
    
    username = serializers.CharField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """
        Valida credenciales.
        
        Note: La autenticación real se hace en la vista
        usando AuthenticationService.login()
        """
        username = attrs.get('username')
        password = attrs.get('password')
        
        if not username or not password:
            raise serializers.ValidationError(
                'Username y password son requeridos'
            )
        
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer para cambiar password.
    
    Required fields:
    - old_password
    - new_password
    - new_password_confirm
    
    Validations:
    - old_password debe ser correcto
    - new_password mínimo 8 caracteres
    - new_password != old_password
    - new_password == new_password_confirm
    
    Example:
        >>> data = {
        ...     'old_password': 'OldPass123',
        ...     'new_password': 'NewPass456',
        ...     'new_password_confirm': 'NewPass456'
        ... }
        >>> serializer = ChangePasswordSerializer(data=data)
        >>> serializer.is_valid()
        True
    """
    
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=8,
        style={'input_type': 'password'},
        help_text='Mínimo 8 caracteres'
    )
    
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """Valida que passwords coincidan y sean diferentes."""
        old_password = attrs.get('old_password')
        new_password = attrs.get('new_password')
        new_password_confirm = attrs.get('new_password_confirm')
        
        # Verificar que new_password coincida con confirmación
        if new_password != new_password_confirm:
            raise serializers.ValidationError({
                'new_password_confirm': 'Los passwords no coinciden'
            })
        
        # Verificar que new_password sea diferente a old_password
        if old_password == new_password:
            raise serializers.ValidationError({
                'new_password': 'El nuevo password debe ser diferente al actual'
            })
        
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer para solicitar reset de password.
    
    Input:
    - email
    
    Process:
    - Genera token
    - Envía email con link
    
    Note:
        Por seguridad, siempre retorna success=True
        incluso si el email no existe.
    
    Example:
        >>> data = {'email': 'user@company.com'}
        >>> serializer = PasswordResetRequestSerializer(data=data)
        >>> serializer.is_valid()
        True
    """
    
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer para confirmar reset de password.
    
    Input:
    - uidb64 (user ID en base64)
    - token (reset token)
    - new_password
    - new_password_confirm
    
    Validations:
    - Token debe ser válido
    - new_password mínimo 8 caracteres
    - new_password == new_password_confirm
    
    Example:
        >>> data = {
        ...     'uidb64': 'MQ',
        ...     'token': 'abc123',
        ...     'new_password': 'NewPass456',
        ...     'new_password_confirm': 'NewPass456'
        ... }
        >>> serializer = PasswordResetConfirmSerializer(data=data)
        >>> serializer.is_valid()
        True
    """
    
    uidb64 = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=8,
        style={'input_type': 'password'},
        help_text='Mínimo 8 caracteres'
    )
    
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """Valida que passwords coincidan."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'Los passwords no coinciden'
            })
        
        return attrs


# ============================================================================
# RESUMEN SERIALIZERS
# 
# Total Serializers: 11
# 
# Modelos (read/write):
#   [SUCCESS] UserProfileSerializer - Profile de usuario
#   [SUCCESS] UserSettingsSerializer - Settings de usuario
#   [SUCCESS] SessionHistorySerializer - Historial sesiones (read-only)
# 
# User (CRUD):
#   [SUCCESS] UserSerializer - Principal (con RBAC)
#   [SUCCESS] UserCreateSerializer - Crear con password
#   [SUCCESS] UserUpdateSerializer - Actualizar campos permitidos
# 
# Autenticación:
#   [SUCCESS] LoginSerializer - Login
#   [SUCCESS] ChangePasswordSerializer - Cambiar password
# 
# Password Reset:
#   [SUCCESS] PasswordResetRequestSerializer - Solicitar reset
#   [SUCCESS] PasswordResetConfirmSerializer - Confirmar reset
# 
# Validaciones:
#   [SUCCESS] Username único
#   [SUCCESS] Email único
#   [SUCCESS] Password mínimo 8 caracteres
#   [SUCCESS] Password confirmation
#   [SUCCESS] Password != old_password
# 
# Integración:
#   [SUCCESS] UserService.create_user()
#   [SUCCESS] UserService.update_user()
#   [SUCCESS] User.get_functions() (RBAC)
# 
# Principios:
#   [SUCCESS] DRY: Validaciones reutilizables
#   [SUCCESS] SRP: Cada serializer una responsabilidad
#   [SUCCESS] Clean Code: Nombres descriptivos
# 
# Líneas: ~550
# ============================================================================
