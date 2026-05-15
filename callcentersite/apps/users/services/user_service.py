"""
UserService - Service Layer para User model.

Hereda de BaseService (apps.core.services).
Gestiona operaciones CRUD de usuarios.

CLEAN_CODE v3.0.1: Service Layer Pattern, Single Responsibility.
"""

from typing import Optional, Dict, List
from django.db import transaction
from django.contrib.auth import get_user_model

from apps.core.services import BaseService
from apps.users.exceptions import (
    UserAlreadyExistsError,
    UserNotFoundError,
    UserServiceError,
)
from apps.utils.validators import validate_email, validate_phone_number
from apps.audit.services import AuditLogService

User = get_user_model()


class UserService(BaseService):
    """
    Service para operaciones de User.
    
    Hereda de BaseService (apps.core.services).
    
    Responsabilidades:
    - CRUD de usuarios
    - Validaciones de negocio
    - Activación/Desactivación
    - Audit logging
    
    Example:
        service = UserService()
        user = service.create_user(
            username='jdoe',
            email='jdoe@company.com',
            password='SecurePass123',
            first_name='John',
            last_name='Doe'
        )
    """
    
    def __init__(self):
        """Inicializa UserService."""
        super().__init__()
        self.audit_service = AuditLogService()
    
    @transaction.atomic
    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        first_name: str = '',
        last_name: str = '',
        phone: Optional[str] = None,
        created_by: Optional[User] = None,
    ) -> User:
        """
        Crea un nuevo usuario.
        
        Validaciones:
        - Username único
        - Email único y válido
        - Phone válido (si se proporciona)
        
        Post-creación:
        - UserProfile se crea automáticamente (signal)
        - UserSettings se crea automáticamente (signal)
        - Se registra en audit log
        
        Args:
            username: Nombre de usuario (único)
            email: Email del usuario (único)
            password: Password sin hashear
            first_name: Nombre
            last_name: Apellido
                phone: Teléfono (opcional)
                created_by: Usuario que crea (para audit)
        
        Returns:
            User: Usuario creado
        
        Raises:
            UserAlreadyExistsError: Si username o email ya existen
            ValueError: Si validación falla
        
        Example:
            >>> service = UserService()
            >>> user = service.create_user(
            ...     username='jdoe',
            ...     email='jdoe@company.com',
            ...     password='SecurePass123',
            ...     first_name='John',
            ...     last_name='Doe'
            ... )
            >>> print(user.id)
            1
        """
        self.log_info(f"Creando usuario: {username}")
        
        # Validar que username no exista
        if User.objects.filter(username=username).exists():
            raise UserAlreadyExistsError(f"Username '{username}' ya existe")
        
        # Validar que email no exista
        if User.objects.filter(email=email).exists():
            raise UserAlreadyExistsError(f"Email '{email}' ya está en uso")
        
        # Validar email
        validate_email(email)
        
        # Validar phone si se proporciona
        if phone:
            validate_phone_number(phone)
        
        # Crear usuario
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
            
            # Campos adicionales
            if phone:
                user.phone = phone
            
            user.save()
            
            # Audit log
            self.audit_service.log_action(resource="user", 
                action='USER_CREATED',
                user=created_by,
                details={
                    'user_id': user.id,
                    'username': user.username,
                    'email': user.email,
                }
            )
            
            self.log_info(f"Usuario creado exitosamente: {user.id}")
            return user
            
        except Exception as e:
            self.log_error(f"Error creando usuario: {str(e)}")
            raise UserServiceError(f"Error al crear usuario: {str(e)}")
    
    def get_user_by_id(self, user_id: int) -> User:
        """
        Obtiene usuario por ID.
        
        Args:
            user_id: ID del usuario
        
        Returns:
            User: Usuario encontrado
        
        Raises:
            UserNotFoundError: Si usuario no existe
        
        Example:
            >>> service = UserService()
            >>> user = service.get_user_by_id(1)
            >>> print(user.username)
            'jdoe'
        """
        self.log_info(f"Buscando usuario ID: {user_id}")
        
        user = User.objects.filter(id=user_id, state='ACTIVE').first()
        if not user:
            raise UserNotFoundError(f"Usuario {user_id} no encontrado")
        
        return user
    
    def get_user_by_username(self, username: str) -> User:
        """
        Obtiene usuario por username.
        
        Args:
            username: Nombre de usuario
        
        Returns:
            User: Usuario encontrado
        
        Raises:
            UserNotFoundError: Si usuario no existe
        
        Example:
            >>> service = UserService()
            >>> user = service.get_user_by_username('jdoe')
            >>> print(user.email)
            'jdoe@company.com'
        """
        self.log_info(f"Buscando usuario: {username}")
        
        user = User.objects.filter(username=username, state='ACTIVE').first()
        if not user:
            raise UserNotFoundError(f"Usuario '{username}' no encontrado")
        
        return user
    
    def list_users(
        self,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> List[User]:
        """
        Lista usuarios con filtros opcionales.
        
        Args:
            is_active: Filtrar por activos (None = todos)
            search: Buscar en username, email, first_name, last_name
        
        Returns:
            List[User]: Lista de usuarios
        
        Example:
            >>> service = UserService()
            >>> users = service.list_users(is_active=True)
            >>> print(len(users))
            5
        """
        self.log_info("Listando usuarios")
        
        queryset = User.objects.filter(state='ACTIVE')
        
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active)
        
        if search:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        return list(queryset.order_by('username'))
    
    @transaction.atomic
    def update_user(
        self,
        user_id: int,
        updated_by: Optional[User] = None,
        **kwargs
    ) -> User:
        """
        Actualiza datos de usuario.
        
        Campos actualizables:
        - first_name, last_name
        - email (con validación de unicidad)
        - phone (con validación)
        - position
        - employee_id
        
        Args:
            user_id: ID del usuario a actualizar
            updated_by: Usuario que actualiza (para audit)
            **kwargs: Campos a actualizar
        
        Returns:
            User: Usuario actualizado
        
        Raises:
            UserNotFoundError: Si usuario no existe
            UserAlreadyExistsError: Si email ya está en uso
        
        Example:
            >>> service = UserService()
            >>> user = service.update_user(
            ...     user_id=1,
            ...     first_name='Jane',
            ...     email='jane@company.com'
            ... )
        """
        self.log_info(f"Actualizando usuario ID: {user_id}")
        
        user = self.get_user_by_id(user_id)
        
        # Validar email si se actualiza
        if 'email' in kwargs:
            new_email = kwargs['email']
            validate_email(new_email)
            
            # Verificar unicidad
            if User.objects.filter(email=new_email).exclude(id=user_id).exists():
                raise UserAlreadyExistsError(f"Email '{new_email}' ya está en uso")
        
        # Validar phone si se actualiza
        if 'phone' in kwargs and kwargs['phone']:
            validate_phone_number(kwargs['phone'])
        
        # Actualizar campos permitidos
        allowed_fields = [
            'first_name', 'last_name', 'email', 'phone', 
            'position', 'employee_id'
        ]
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(user, field, value)
        
        user.save()
        
        # Audit log
        self.audit_service.log_action(resource="user", 
            action='USER_UPDATED',
            user=updated_by,
            details={
                'user_id': user.id,
                'updated_fields': list(kwargs.keys()),
            }
        )
        
        self.log_info(f"Usuario actualizado: {user.id}")
        return user
    
    @transaction.atomic
    def activate_user(
        self,
        user_id: int,
        activated_by: Optional[User] = None,
    ) -> User:
        """
        Activa un usuario (is_active=True).
        
        Args:
            user_id: ID del usuario
            activated_by: Usuario que activa (para audit)
        
        Returns:
            User: Usuario activado
        
        Raises:
            UserNotFoundError: Si usuario no existe
        
        Example:
            >>> service = UserService()
            >>> user = service.activate_user(user_id=1, activated_by=admin)
        """
        self.log_info(f"Activando usuario ID: {user_id}")
        
        user = self.get_user_by_id(user_id)
        user.is_active = True
        user.save()
        
        # Audit log
        self.audit_service.log_action(resource="user", 
            action='USER_ACTIVATED',
            user=activated_by,
            details={'user_id': user.id, 'username': user.username}
        )
        
        self.log_info(f"Usuario activado: {user.id}")
        return user
    
    @transaction.atomic
    def deactivate_user(
        self,
        user_id: int,
        deactivated_by: Optional[User] = None,
    ) -> User:
        """
        Desactiva un usuario (is_active=False).
        
        Args:
            user_id: ID del usuario
            deactivated_by: Usuario que desactiva (para audit)
        
        Returns:
            User: Usuario desactivado
        
        Raises:
            UserNotFoundError: Si usuario no existe
        
        Example:
            >>> service = UserService()
            >>> user = service.deactivate_user(user_id=1, deactivated_by=admin)
        """
        self.log_info(f"Desactivando usuario ID: {user_id}")
        
        user = self.get_user_by_id(user_id)
        user.is_active = False
        user.save()
        
        # Audit log
        self.audit_service.log_action(resource="user", 
            action='USER_DEACTIVATED',
            user=deactivated_by,
            details={'user_id': user.id, 'username': user.username}
        )
        
        self.log_info(f"Usuario desactivado: {user.id}")
        return user
    
    @transaction.atomic
    def delete_user(
        self,
        user_id: int,
        deleted_by: Optional[User] = None,
    ) -> User:
        """
        Elimina usuario (soft delete).
        
        Usa SoftDeleteMixin.delete() que marca is_deleted=True.
        
        Args:
            user_id: ID del usuario
            deleted_by: Usuario que elimina (para audit)
        
        Returns:
            User: Usuario eliminado
        
        Raises:
            UserNotFoundError: Si usuario no existe
        
        Example:
            >>> service = UserService()
            >>> user = service.delete_user(user_id=1, deleted_by=admin)
        """
        self.log_info(f"Eliminando usuario ID: {user_id}")
        
        user = self.get_user_by_id(user_id)
        user.delete()  # <- Soft delete (SoftDeleteMixin)
        
        # Audit log
        self.audit_service.log_action(resource="user", 
            action='USER_DELETED',
            user=deleted_by,
            details={'user_id': user.id, 'username': user.username}
        )
        
        self.log_info(f"Usuario eliminado: {user.id}")
        return user


# ============================================================================
# RESUMEN UserService
# 
# Hereda de: BaseService (apps.core.services)
# 
# Métodos Públicos: 9
#   [SUCCESS] create_user() - Crea usuario con validaciones
#   [SUCCESS] get_user_by_id() - Busca por ID
#   [SUCCESS] get_user_by_username() - Busca por username
#   [SUCCESS] list_users() - Lista con filtros
#   [SUCCESS] update_user() - Actualiza campos permitidos
#   [SUCCESS] activate_user() - Activa usuario
#   [SUCCESS] deactivate_user() - Desactiva usuario
#   [SUCCESS] delete_user() - Soft delete
# 
# Dependencias:
#   [SUCCESS] BaseService (apps.core.services) - Logging
#   [SUCCESS] AuditService (apps.audit.services) - Audit logging
#   [SUCCESS] validate_email, validate_phone_number (apps.utils.validators)
#   [SUCCESS] UserAlreadyExistsError, UserNotFoundError (apps.users.exceptions)
# 
# Principios SOLID:
#   [SUCCESS] SRP: Solo operaciones de User
#   [SUCCESS] DIP: Depende de abstracciones (BaseService)
#   [SUCCESS] OCP: Extensible sin modificar
# 
# Transacciones:
#   [SUCCESS] @transaction.atomic en operaciones de escritura
# 
# Líneas: ~450
# ============================================================================
