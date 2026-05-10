"""
ProfileService - Service Layer para UserProfile.

Hereda de BaseService (apps.core.services).
Gestiona operaciones de perfil de usuario.

CLEAN_CODE v3.0.1: Service Layer Pattern, Single Responsibility.
"""

from typing import Optional
from django.db import transaction
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import UploadedFile

from apps.core.services import BaseService
try:
    from apps.users.models import UserProfile
except ImportError:
    UserProfile = None
from apps.users.exceptions import UserNotFoundError, UserServiceError
from apps.utils.file_utils import sanitize_filename, calculate_file_hash
from apps.audit.services import AuditLogService

User = get_user_model()


class ProfileService(BaseService):
    """
    Service para operaciones de UserProfile.
    
    Hereda de BaseService (apps.core.services).
    
    Responsabilidades:
    - Actualizar bio, department
    - Upload de avatar
    - Gestión de imagen de perfil
    
    Note:
        UserProfile se crea automáticamente vía signal cuando se crea User.
    
    Example:
        service = ProfileService()
        profile = service.update_profile(
            user_id=1,
            bio='Software Developer',
            department='Engineering'
        )
    """
    
    def __init__(self):
        """Inicializa ProfileService."""
        super().__init__()
        self.audit_service = AuditLogService()
    
    def get_profile(self, user_id: int) -> UserProfile:
        """
        Obtiene perfil de usuario.
        
        Args:
            user_id: ID del usuario
        
        Returns:
            UserProfile: Perfil del usuario
        
        Raises:
            UserNotFoundError: Si usuario no existe
        
        Example:
            >>> service = ProfileService()
            >>> profile = service.get_profile(user_id=1)
            >>> print(profile.bio)
            'Software Developer'
        """
        self.log_info(f"Obteniendo perfil de usuario ID: {user_id}")
        
        try:
            user = User.objects.get(id=user_id, is_deleted=False)
            return user.profile
        except User.DoesNotExist:
            raise UserNotFoundError(f"Usuario {user_id} no encontrado")
    
    @transaction.atomic
    def update_profile(
        self,
        user_id: int,
        bio: Optional[str] = None,
        department: Optional[str] = None,
        updated_by: Optional[User] = None,
    ) -> UserProfile:
        """
        Actualiza perfil de usuario.
        
        Args:
            user_id: ID del usuario
            bio: Biografía (opcional)
            department: Departamento (opcional)
            updated_by: Usuario que actualiza (para audit)
        
        Returns:
            UserProfile: Perfil actualizado
        
        Raises:
            UserNotFoundError: Si usuario no existe
        
        Example:
            >>> service = ProfileService()
            >>> profile = service.update_profile(
            ...     user_id=1,
            ...     bio='Senior Software Developer',
            ...     department='Product Engineering'
            ... )
        """
        self.log_info(f"Actualizando perfil de usuario ID: {user_id}")
        
        profile = self.get_profile(user_id)
        
        if bio is not None:
            profile.bio = bio
        
        if department is not None:
            profile.department = department
        
        profile.save()
        
        # Audit log
        self.audit_service.log_action(resource="user", 
            action='PROFILE_UPDATED',
            user=updated_by,
            details={
                'user_id': user_id,
                'updated_fields': {
                    'bio': bio is not None,
                    'department': department is not None,
                }
            }
        )
        
        self.log_info(f"Perfil actualizado: usuario {user_id}")
        return profile
    
    @transaction.atomic
    def upload_avatar(
        self,
        user_id: int,
        avatar_file: UploadedFile,
        uploaded_by: Optional[User] = None,
    ) -> User:
        """
        Sube avatar de usuario.
        
        Proceso:
        1. Valida formato (jpg, png, gif)
        2. Valida tamaño máximo (2MB)
        3. Sanitiza nombre de archivo
        4. Guarda en user.avatar
        5. Registra en audit log
        
        Args:
            user_id: ID del usuario
            avatar_file: Archivo de imagen
            uploaded_by: Usuario que sube (para audit)
        
        Returns:
            User: Usuario con avatar actualizado
        
        Raises:
            UserNotFoundError: Si usuario no existe
            UserServiceError: Si validación falla
        
        Example:
            >>> service = ProfileService()
            >>> user = service.upload_avatar(
            ...     user_id=1,
            ...     avatar_file=request.FILES['avatar']
            ... )
            >>> print(user.avatar.url)
            '/media/avatars/user_1/profile.jpg'
        """
        self.log_info(f"Subiendo avatar para usuario ID: {user_id}")
        
        try:
            user = User.objects.get(id=user_id, is_deleted=False)
        except User.DoesNotExist:
            raise UserNotFoundError(f"Usuario {user_id} no encontrado")
        
        # Validar formato
        allowed_formats = ['image/jpeg', 'image/png', 'image/gif']
        if avatar_file.content_type not in allowed_formats:
            raise UserServiceError(
                f"Formato no permitido. Use: jpg, png, gif"
            )
        
        # Validar tamaño (2MB máximo)
        max_size = 2 * 1024 * 1024  # 2MB
        if avatar_file.size > max_size:
            raise UserServiceError(
                f"Archivo muy grande. Máximo: 2MB"
            )
        
        # Sanitizar nombre de archivo
        filename = sanitize_filename(avatar_file.name)
        
        # Guardar avatar
        user.avatar.save(filename, avatar_file, save=True)
        
        # Calcular hash (para audit)
        file_hash = calculate_file_hash(avatar_file)
        
        # Audit log
        self.audit_service.log_action(resource="user", 
            action='AVATAR_UPLOADED',
            user=uploaded_by,
            details={
                'user_id': user_id,
                'filename': filename,
                'size': avatar_file.size,
                'hash': file_hash,
            }
        )
        
        self.log_info(f"Avatar subido exitosamente: usuario {user_id}")
        return user
    
    @transaction.atomic
    def remove_avatar(
        self,
        user_id: int,
        removed_by: Optional[User] = None,
    ) -> User:
        """
        Elimina avatar de usuario.
        
        Args:
            user_id: ID del usuario
            removed_by: Usuario que elimina (para audit)
        
        Returns:
            User: Usuario sin avatar
        
        Raises:
            UserNotFoundError: Si usuario no existe
        
        Example:
            >>> service = ProfileService()
            >>> user = service.remove_avatar(user_id=1)
            >>> print(user.avatar)
            None
        """
        self.log_info(f"Eliminando avatar de usuario ID: {user_id}")
        
        try:
            user = User.objects.get(id=user_id, is_deleted=False)
        except User.DoesNotExist:
            raise UserNotFoundError(f"Usuario {user_id} no encontrado")
        
        # Eliminar archivo físico
        if user.avatar:
            user.avatar.delete(save=False)
        
        user.avatar = None
        user.save()
        
        # Audit log
        self.audit_service.log_action(resource="user", 
            action='AVATAR_REMOVED',
            user=removed_by,
            details={'user_id': user_id}
        )
        
        self.log_info(f"Avatar eliminado: usuario {user_id}")
        return user


# ============================================================================
# RESUMEN ProfileService
# 
# Hereda de: BaseService (apps.core.services)
# 
# Métodos Públicos: 4
#   [SUCCESS] get_profile() - Obtiene perfil
#   [SUCCESS] update_profile() - Actualiza bio, department
#   [SUCCESS] upload_avatar() - Sube imagen de perfil
#   [SUCCESS] remove_avatar() - Elimina avatar
# 
# Dependencias:
#   [SUCCESS] BaseService (apps.core.services) - Logging
#   [SUCCESS] AuditService (apps.audit.services) - Audit logging
#   [SUCCESS] sanitize_filename, calculate_file_hash (apps.utils.file_utils)
#   [SUCCESS] UserNotFoundError, UserServiceError (apps.users.exceptions)
# 
# Validaciones de Avatar:
#   [SUCCESS] Formatos permitidos: jpg, png, gif
#   [SUCCESS] Tamaño máximo: 2MB
#   [SUCCESS] Sanitización de nombre de archivo
#   [SUCCESS] Hash calculado para audit
# 
# Integración con Signal:
#   [SUCCESS] UserProfile auto-creado cuando se crea User
# 
# Principios SOLID:
#   [SUCCESS] SRP: Solo operaciones de perfil
#   [SUCCESS] DIP: Depende de BaseService
#   [SUCCESS] Clean Code: Validaciones claras
# 
# Líneas: ~250
# ============================================================================
