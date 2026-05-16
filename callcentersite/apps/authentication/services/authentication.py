"""
Servicio de autenticación de usuarios.

CLEAN_CODE v3.0.1: Nombre descriptivo.
SOLID SRP: Solo autenticación.

CNST-005: Token + Session, PBKDF2.
CNST-031: Auditoría completa.
"""

from typing import Dict
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.utils import timezone
from rest_framework.authtoken.models import Token

from apps.core.services.base_service import BaseService  # [SUCCESS] BaseService
from apps.utils.helpers import get_client_ip, get_user_agent  # [SUCCESS] apps.utils
from apps.authentication.models import LoginAttempt, SessionLog
from apps.authentication.exceptions import (
    InvalidCredentialsError,
    AccountLockedError,
    UserInactiveError
)
from apps.authentication.services.lockout import LockoutService

User = get_user_model()


class AuthenticationService(BaseService):  # [SUCCESS] Hereda de BaseService
    """
    Servicio de autenticación de usuarios.

    SOLID SRP: Solo autenticación.

    Responsabilidades:
    - Login username/password
    - Logout
    - Registro de intentos (CNST-031)
    - Verificación de lockout
    - Gestión de tokens DRF
    - Gestión de sesiones

    CNST-005: PBKDF2 + Token + Session.
    CNST-031: Auditoría de todos los intentos.
    """

    def __init__(self):
        """Initialize service."""
        super().__init__()  # [SUCCESS] Llamar a super
        self.lockout_service = LockoutService()

        self.log_info("AuthenticationService initialized")

    def login_user(
        self,
        request,
        username: str,
        password: str
    ) -> Dict:
        """
        Login de usuario.

        Flujo:
        1. Verificar lockout
        2. Autenticar con Django
        3. Verificar usuario activo
        4. Login Django
        5. Generar token DRF
        6. Registrar intento exitoso
        7. Crear SessionLog
        8. Resetear contador lockout

        Args:
            request: HttpRequest
            username: Username
            password: Password

        Returns:
            Dict con:
            - user: User object
            - token: DRF token key
            - session_key: Django session key
            - first_login: bool

        Raises:
            AccountLockedError: Cuenta bloqueada
            InvalidCredentialsError: Credenciales inválidas
            UserInactiveError: Usuario inactivo
        """
        # [SUCCESS] Usar helpers de apps.utils
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)

        self.log_info(f"Login attempt for '{username}' from {ip_address}")  # [SUCCESS] Logging

        # 1. Verificar lockout
        if self.lockout_service.is_locked(username):
            self._record_attempt(
                username=username,
                success=False,
                ip_address=ip_address,
                user_agent=user_agent
            )

            time_remaining = self.lockout_service.get_lockout_time_remaining(username)
            minutes = int(time_remaining.total_seconds() / 60) if time_remaining else 15

            self.log_error(f"Login blocked for '{username}' - {minutes} minutes remaining")

            raise AccountLockedError(
                detail=f"Cuenta bloqueada. Intenta en {minutes} minutos.",
                details={'locked_minutes': minutes}
            )

        # 2. Autenticar
        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is None:
            # Intento fallido
            self._record_attempt(
                username=username,
                user=None,
                success=False,
                ip_address=ip_address,
                user_agent=user_agent
            )

            # Incrementar contador lockout
            attempts = self.lockout_service.record_failed_attempt(username)
            remaining = self.lockout_service.max_attempts - attempts

            self.log_warning(f"Invalid credentials for '{username}' - {remaining} attempts remaining")

            if remaining > 0:
                raise InvalidCredentialsError(
                    detail=f"Credenciales inválidas. Te quedan {remaining} intentos.",
                    details={'attempts_remaining': remaining}
                )
            else:
                raise AccountLockedError(
                    detail="Cuenta bloqueada por múltiples intentos fallidos."
                )

        # 3. Verificar activo
        if not user.is_active:
            self._record_attempt(
                username=username,
                user=user,
                success=False,
                ip_address=ip_address,
                user_agent=user_agent
            )

            self.log_warning(f"Inactive user '{username}' attempted login")

            raise UserInactiveError(
                detail=f"Usuario '{username}' inactivo. Contacte al administrador."
            )

        # 4. Login Django
        login(request, user)

        # 5. Generar token DRF
        token, created = Token.objects.get_or_create(user=user)

        # 6. Registrar intento exitoso
        self._record_attempt(
            username=username,
            user=user,
            success=True,
            ip_address=ip_address,
            user_agent=user_agent
        )

        # 7. Log de sesión
        self._create_session_log(
            user=user,
            session_key=request.session.session_key,
            ip_address=ip_address,
            user_agent=user_agent
        )

        # 8. Resetear contador lockout
        self.lockout_service.reset_failed_attempts(username)

        # Detectar first login
        first_login = self._is_first_login(user)

        self.log_info(f"Login successful for '{username}' - First login: {first_login}")

        return {
            'user': user,
            'token': token.key,
            'session_key': request.session.session_key,
            'first_login': first_login
        }

    def logout_user(self, request) -> bool:
        """
        Logout de usuario.

        Args:
            request: HttpRequest

        Returns:
            bool: True si logout exitoso
        """
        if not request.user.is_authenticated:
            return False

        username = request.user.username

        # Actualizar SessionLog
        self._update_session_log(
            session_key=request.session.session_key
        )

        # Logout Django
        logout(request)

        self.log_info(f"Logout successful for '{username}'")

        return True

    def _is_first_login(self, user) -> bool:
        """
        Detecta si es el primer login del usuario.

        SOLID SRP: Solo detecta first login.

        Args:
            user: User object

        Returns:
            bool: True si es primer login
        """
        # Contar logins exitosos anteriores
        previous_logins = LoginAttempt.objects.filter(
            user=user,
            success=True
        ).count()

        # Si solo hay 1 (el actual), es el primero
        return previous_logins <= 1

    def _record_attempt(
        self,
        username: str,
        success: bool,
        ip_address: str,
        user_agent: str,
        user=None
    ):
        """
        Registra intento de login (CNST-031).

        SOLID SRP: Solo registra intento.

        Args:
            username: Username intentado
            success: Si fue exitoso
            ip_address: IP
            user_agent: User agent
            user: User object (None si no existe)
        """
        LoginAttempt.objects.create(
            user=user,
            username=username,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent
        )

    def _create_session_log(
        self,
        user,
        session_key: str,
        ip_address: str,
        user_agent: str
    ) -> SessionLog:
        """
        Crea log de sesión.

        SOLID SRP: Solo crea log.

        Args:
            user: User object
            session_key: Django session key
            ip_address: IP
            user_agent: User agent

        Returns:
            SessionLog: Log creado
        """
        return SessionLog.objects.create(
            user=user,
            session_key=session_key,
            ip_address=ip_address,
            user_agent=user_agent,
            is_active=True,
            created_by=user  # [SUCCESS] Auditoría
        )

    def _update_session_log(self, session_key: str):
        """
        Actualiza log al hacer logout.

        SOLID SRP: Solo actualiza log.

        Args:
            session_key: Django session key
        """
        SessionLog.objects.filter(
            session_key=session_key,
            is_active=True
        ).update(
            logout_at=timezone.now(),
            is_active=False
        )
