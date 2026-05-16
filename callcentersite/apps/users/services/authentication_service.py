"""
AuthenticationService - Service Layer para autenticación.

Hereda de BaseService (apps.core.services).
Gestiona login, logout y cambio de password.

CLEAN_CODE v3.0.1: Service Layer Pattern, Single Responsibility.
"""

from typing import Optional
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.db import transaction

from apps.core.services import BaseService
from apps.users.exceptions import (
    InvalidCredentialsError,
    UserInactiveError,
    PasswordValidationError,
)
from apps.audit.services import AuditLogService

User = get_user_model()


class AuthenticationService(BaseService):
    """
    Service para autenticación de usuarios.
    
    Hereda de BaseService (apps.core.services).
    
    Responsabilidades:
    - Login (autenticación)
    - Logout
    - Cambio de password
    - Validación de password
    
    Note:
        SessionHistory se crea automáticamente vía signals:
        - user_logged_in -> log_user_login (apps.users.signals)
        - user_logged_out -> log_user_logout (apps.users.signals)
    
    Example:
        service = AuthenticationService()
        user = service.login(
            request=request,
            username='jdoe',
            password='SecurePass123'
        )
    """
    
    def __init__(self):
        """Inicializa AuthenticationService."""
        super().__init__()
        self.audit_service = AuditLogService()
    
    def login(
        self,
        request,
        username: str,
        password: str,
    ) -> User:
        """
        Autentica usuario y crea sesión.
        
        Proceso:
        1. Valida credenciales con Django authenticate()
        2. Verifica que usuario esté activo
        3. Crea sesión con Django login()
        4. Signal crea SessionHistory automáticamente
        5. Registra en audit log
        
        Args:
            request: HttpRequest (necesario para login())
            username: Username del usuario
            password: Password sin hashear
        
        Returns:
            User: Usuario autenticado
        
        Raises:
            InvalidCredentialsError: Si credenciales son incorrectas
            UserInactiveError: Si usuario está inactivo
        
        Example:
            >>> service = AuthenticationService()
            >>> user = service.login(
            ...     request=request,
            ...     username='jdoe',
            ...     password='SecurePass123'
            ... )
            >>> print(user.username)
            'jdoe'
        """
        self.log_info(f"Intento de login: {username}")
        
        # Autenticar con Django
        user = authenticate(request, username=username, password=password)
        
        if user is None:
            self.log_warning(f"Login fallido: {username}")
            raise InvalidCredentialsError("Username o password incorrectos")
        
        # Verificar que esté activo
        if not user.is_active:
            self.log_warning(f"Login rechazado (inactivo): {username}")
            raise UserInactiveError(f"Usuario '{username}' está inactivo")
        
        # Crear sesión
        login(request, user)
        
        # Audit log
        self.audit_service.log_action(resource="user", 
            action='USER_LOGIN',
            user=user,
            details={'username': user.username}
        )
        
        self.log_info(f"Login exitoso: {username}")
        return user
    
    def logout(self, request, user: Optional[User] = None) -> None:
        """
        Cierra sesión de usuario.
        
        Proceso:
        1. Cierra sesión con Django logout()
        2. Signal actualiza SessionHistory automáticamente
        3. Registra en audit log
        
        Args:
            request: HttpRequest
            user: Usuario (opcional, se obtiene de request.user)
        
        Example:
            >>> service = AuthenticationService()
            >>> service.logout(request=request)
        """
        if user is None:
            user = getattr(request, 'user', None)
        
        if user and user.is_authenticated:
            self.log_info(f"Logout: {user.username}")
            
            # Audit log
            self.audit_service.log_action(resource="user", 
                action='USER_LOGOUT',
                user=user,
                details={'username': user.username}
            )
            
            # Cerrar sesión
            logout(request)
            
            self.log_info(f"Logout exitoso: {user.username}")
        else:
            self.log_warning("Logout sin usuario autenticado")
    
    @transaction.atomic
    def change_password(
        self,
        user: User,
        old_password: str,
        new_password: str,
    ) -> User:
        """
        Cambia password de usuario.
        
        Validaciones:
        - old_password debe ser correcto
        - new_password debe cumplir requisitos
        - new_password != old_password
        
        Args:
            user: Usuario que cambia password
            old_password: Password actual
            new_password: Nuevo password
        
        Returns:
            User: Usuario con password actualizado
        
        Raises:
            InvalidCredentialsError: Si old_password es incorrecto
            PasswordValidationError: Si new_password no cumple requisitos
        
        Example:
            >>> service = AuthenticationService()
            >>> user = service.change_password(
            ...     user=user,
            ...     old_password='OldPass123',
            ...     new_password='NewPass456'
            ... )
        """
        self.log_info(f"Cambio de password: {user.username}")
        
        # Verificar old_password
        if not user.check_password(old_password):
            self.log_warning(f"Password actual incorrecto: {user.username}")
            raise InvalidCredentialsError("Password actual es incorrecto")
        
        # Validar new_password
        self._validate_password(new_password)
        
        # Verificar que new_password sea diferente
        if old_password == new_password:
            raise PasswordValidationError(
                "El nuevo password debe ser diferente al actual"
            )
        
        # Cambiar password
        user.set_password(new_password)
        user.save()
        
        # Audit log
        self.audit_service.log_action(resource="user", 
            action='PASSWORD_CHANGED',
            user=user,
            details={'username': user.username}
        )
        
        self.log_info(f"Password cambiado exitosamente: {user.username}")
        return user
    
    def _validate_password(self, password: str) -> None:
        """
        Valida requisitos de password.
        
        Requisitos:
        - Mínimo 8 caracteres
        - Al menos una letra
        - Al menos un número
        
        Args:
            password: Password a validar
        
        Raises:
            PasswordValidationError: Si no cumple requisitos
        
        Example:
            >>> service = AuthenticationService()
            >>> service._validate_password('Pass123')  # OK
            >>> service._validate_password('pass')  # PasswordValidationError
        """
        if len(password) < 8:
            raise PasswordValidationError(
                "El password debe tener mínimo 8 caracteres"
            )
        
        if not any(c.isalpha() for c in password):
            raise PasswordValidationError(
                "El password debe contener al menos una letra"
            )
        
        if not any(c.isdigit() for c in password):
            raise PasswordValidationError(
                "El password debe contener al menos un número"
            )
    
    def validate_user_credentials(
        self,
        username: str,
        password: str,
    ) -> bool:
        """
        Valida credenciales sin crear sesión.
        
        Útil para verificar credenciales antes de operaciones sensibles.
        
        Args:
            username: Username del usuario
            password: Password sin hashear
        
        Returns:
            bool: True si credenciales son válidas
        
        Example:
            >>> service = AuthenticationService()
            >>> is_valid = service.validate_user_credentials(
            ...     username='jdoe',
            ...     password='Pass123'
            ... )
            >>> print(is_valid)
            True
        """
        self.log_info(f"Validando credenciales: {username}")
        
        user = User.objects.filter(username=username, is_active=True).first()
        
        if user and user.check_password(password):
            return True
        
        return False


# ============================================================================
# RESUMEN AuthenticationService
# 
# Hereda de: BaseService (apps.core.services)
# 
# Métodos Públicos: 4
#   [SUCCESS] login() - Autentica y crea sesión
#   [SUCCESS] logout() - Cierra sesión
#   [SUCCESS] change_password() - Cambia password con validación
#   [SUCCESS] validate_user_credentials() - Valida sin crear sesión
# 
# Métodos Privados: 1
#   [SUCCESS] _validate_password() - Valida requisitos de password
# 
# Dependencias:
#   [SUCCESS] BaseService (apps.core.services) - Logging
#   [SUCCESS] AuditService (apps.audit.services) - Audit logging
#   [SUCCESS] Django authenticate, login, logout
#   [SUCCESS] Exceptions de apps.users.exceptions
# 
# Integración con Signals:
#   [SUCCESS] user_logged_in -> log_user_login (SessionHistory)
#   [SUCCESS] user_logged_out -> log_user_logout (SessionHistory)
# 
# Validaciones de Password:
#   [SUCCESS] Mínimo 8 caracteres
#   [SUCCESS] Al menos una letra
#   [SUCCESS] Al menos un número
# 
# Principios SOLID:
#   [SUCCESS] SRP: Solo autenticación
#   [SUCCESS] DIP: Depende de BaseService
#   [SUCCESS] Clean Code: Métodos cortos y claros
# 
# Líneas: ~270
# ============================================================================
