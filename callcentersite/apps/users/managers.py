"""
Custom User Manager para apps/users/.

CNST-037: Custom User Model
SOLID SRP: Solo creación y gestión de usuarios
"""

from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ValidationError
from apps.users.validators import validate_username


class CustomUserManager(BaseUserManager):
    """
    Manager personalizado para modelo User.
    
    Hereda de BaseUserManager (Django).
    
    SOLID SRP: Solo creación de usuarios.
    CNST-037: Custom User Model.
    
    Methods:
        - create_user(): Crear usuario normal
        - create_superuser(): Crear superusuario
        - active(): QuerySet de usuarios activos
        
    Example:
        # Crear usuario normal
        user = User.objects.create_user(
            username='jdoe',
            email='jdoe@company.com',
            password='SecurePass123'
        )
        
        # Crear superusuario
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@company.com',
            password='AdminPass123'
        )
        
        # Obtener usuarios activos
        active_users = User.objects.active()
    """
    
    def create_user(self, username, email, password=None, **extra_fields):
        """
        Crea y guarda usuario normal.
        
        SOLID SRP: Solo crea usuario.
        CNST-014: Validaciones estrictas.
        
        Args:
            username: Username único
            email: Email único
            password: Contraseña (plain text, será hasheada)
            **extra_fields: Campos adicionales
            
        Returns:
            User: Usuario creado
            
        Raises:
            ValidationError: Si datos inválidos
            
        Example:
            user = User.objects.create_user(
                username='jdoe',
                email='jdoe@company.com',
                password='SecurePass123',
                first_name='John',
                last_name='Doe'
            )
        """
        # Validar username
        if not username:
            raise ValidationError('Username es requerido')
        
        validate_username(username)
        

        
        # Establecer defaults
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_active', True)
        
        # Crear usuario
        user = self.model(
            username=username,
            email=email,
            **extra_fields
        )
        
        # Hashear password
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        
        user.save(using=self._db)
        
        return user
    
    def create_superuser(self, username, email, password=None, **extra_fields):
        """
        Crea y guarda superusuario.
        
        SOLID SRP: Solo crea superusuario.
        
        Args:
            username: Username único
            email: Email único
            password: Contraseña (requerida)
            **extra_fields: Campos adicionales
            
        Returns:
            User: Superusuario creado
            
        Raises:
            ValidationError: Si password no proporcionada
            
        Example:
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@company.com',
                password='AdminPass123'
            )
        """
        # Validar password requerida
        if not password:
            raise ValidationError('Superusuario requiere contraseña')
        
        # Forzar flags de superusuario
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        # Validar que flags sean True
        if extra_fields.get('is_staff') is not True:
            raise ValidationError('Superusuario debe tener is_staff=True')
        
        if extra_fields.get('is_superuser') is not True:
            raise ValidationError('Superusuario debe tener is_superuser=True')
        
        return self.create_user(username, email, password, **extra_fields)
    
    def active(self):
        """
        Retorna QuerySet de usuarios activos (no soft-deleted).
        
        SOLID SRP: Solo filtra activos.
        
        Returns:
            QuerySet: Usuarios con is_deleted=False
            
        Example:
            active_users = User.objects.active()
            count = User.objects.active().count()
        """
        return self.filter(is_deleted=False)
    
    def deleted(self):
        """
        Retorna QuerySet de usuarios soft-deleted.
        
        SOLID SRP: Solo filtra eliminados.
        
        Returns:
            QuerySet: Usuarios con is_deleted=True
            
        Example:
            deleted_users = User.objects.deleted()
        """
        return self.filter(is_deleted=True)
    
    def by_employee_id(self, employee_id: str):
        """
        Busca usuario por employee_id.
        
        Args:
            employee_id: ID de empleado
            
        Returns:
            User: Usuario encontrado o None
            
        Example:
            user = User.objects.by_employee_id('EMP-0001')
        """
        try:
            return self.get(employee_id=employee_id)
        except self.model.DoesNotExist:
            return None
    
    def by_email(self, email: str):
        """
        Busca usuario por email.
        
        Args:
            email: Email del usuario
            
        Returns:
            User: Usuario encontrado o None
            
        Example:
            user = User.objects.by_email('jdoe@company.com')
        """
        try:
            return self.get(email=email)
        except self.model.DoesNotExist:
            return None
