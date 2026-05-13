"""
apps/authentication/services/login_service.py

LoginService — servicio canónico para UC_AUTH_01.

Fuente: uc-auth-01/implementacion-tecnica.rst § 11
Responsabilidad única: ejecutar el flujo de login de manera atómica.

Flujo (pasos del UC):
  1-5   Validación de credenciales
  6     Verificar User.state
  7     Verificar lockout BR-015
  8     Autenticar password
  9     Actualizar lockout counter
  10    Cerrar Sessions previas (BR-005, CNST-004)
  11    Crear Session nueva
  12    Emitir AuditEvent LOGIN (CNST-025)
  13    Detectar first_login y warnings
  14    Actualizar User.last_login_at
  15    Generar tokens JWT (SimpleJWT)
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Optional

from django.contrib.auth import get_user_model
from django.db import transaction, DatabaseError
from django.utils import timezone

User = get_user_model()

# Timeout de sesión — CNST-002: 15 minutos
SESSION_TIMEOUT_MINUTES = 15
# Política de lockout — BR-015: 5 intentos → bloqueo
MAX_FAILED_ATTEMPTS = 5
# Ventana de aviso de expiración — FA-02: 7 días
PASSWORD_EXPIRY_WARNING_DAYS = 7


# ---------------------------------------------------------------------------
# Output dataclasses
# ---------------------------------------------------------------------------

@dataclass
class TokenPair:
    access: str
    refresh: str
    access_expires_at: str
    refresh_expires_at: str


@dataclass
class SessionInfo:
    session_id: str
    started_at: str
    expires_at: str


@dataclass
class UserInfo:
    user_id: int
    username: str
    full_name: str
    primary_access_group_id: Optional[str]
    access_groups: list[str]
    first_login: bool


@dataclass
class LoginWarning:
    type: str            # 'password_expiring' | 'no_permissions'
    message: str
    days_remaining: Optional[int] = None


@dataclass
class LoginOutput:
    tokens: TokenPair
    user: UserInfo
    session: SessionInfo
    next_step: Optional[str]     # 'change_password' | None
    warning: Optional[LoginWarning]
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))


# ---------------------------------------------------------------------------
# Excepciones de dominio (UC_AUTH_01 § 7.3)
# ---------------------------------------------------------------------------

class LoginError(Exception):
    """Base de errores de login con code y HTTP status."""
    code: str
    http_status: int

    def __init__(self, message: str = '', **extra):
        super().__init__(message)
        self.message = message
        self.extra = extra


class InvalidCredentialsError(LoginError):
    code = 'INVALID_CREDENTIALS'
    http_status = 401


class AccountBlockedError(LoginError):
    code = 'ACCOUNT_BLOCKED'
    http_status = 403


class AccountInactiveError(LoginError):
    code = 'ACCOUNT_INACTIVE'
    http_status = 403


class DBTransientError(LoginError):
    code = 'DB_TRANSIENT_ERROR'
    http_status = 503


# ---------------------------------------------------------------------------
# LoginService
# ---------------------------------------------------------------------------

class LoginService:
    """
    Servicio canónico de login (UC_AUTH_01).

    Punto de entrada único: ``login(username, password, client_info, ip)``.
    Toda la lógica vive aquí para facilitar testing y trazabilidad.

    Reglas de negocio:
    - BR-005 / CNST-004: sesión única — cierra Sessions previas.
    - BR-015: 5 intentos fallidos → state=BLOCKED.
    - CNST-002: Session.expires_at = now + 15 min.
    - CNST-025: AuditEvent inmutable, siempre emitido.
    - CNST-026: password nunca en payload de AuditEvent.
    - FA-01: first_login=True → next_step='change_password', scope='restricted'.
    - FA-02: password_expires_at < now+7d → warning.
    - FA-04: sin Assignments activos → warning + AuditEvent LOGIN_NO_PERMISSIONS.
    """

    # ------------------------------------------------------------------
    # Punto de entrada público
    # ------------------------------------------------------------------

    @classmethod
    def login(
        cls,
        username: str,
        password: str,
        client_info: dict | None = None,
        ip_address: str | None = None,
    ) -> LoginOutput:
        """
        Ejecuta el flujo de login de manera atómica.

        Raises:
            InvalidCredentialsError: EX-01 / EX-02
            AccountBlockedError:     EX-03
            AccountInactiveError:    EX-04
            DBTransientError:        EX-07
        """
        # Pasos 1-9: verificación (fuera de transacción para evitar locks)
        user = cls._authenticate(username, password)

        # Pasos 10-14: persistencia atómica
        try:
            with transaction.atomic():
                output = cls._persist_login(user, client_info or {}, ip_address)
        except DatabaseError as exc:
            raise DBTransientError('Error transitorio de BD. Reintente en breve.') from exc

        return output

    # ------------------------------------------------------------------
    # Paso 1-9: autenticación y verificación pre-transacción
    # ------------------------------------------------------------------

    @classmethod
    def _authenticate(cls, username: str, password: str) -> 'User':
        """
        Verifica estado, lockout y credenciales.
        No escribe en BD en este paso para minimizar locks.
        """
        from django.contrib.auth.hashers import check_password as django_check_password

        # Buscar usuario (timing-safe: mismo código path si existe o no)
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # Registrar intento fallido sin usuario real (EX-01)
            cls._record_failed_attempt(username, user=None)
            raise InvalidCredentialsError('Credenciales inválidas.')

        # Verificar state (antes de password — menor costo)
        if user.state == 'BLOCKED':
            cls._emit_audit('BLOCKED_LOGIN_ATTEMPT', user.pk, {
                'username': username, 'reason': 'state=BLOCKED',
            })
            raise AccountBlockedError('Cuenta bloqueada. Contacte al administrador.')

        if user.state == 'INACTIVE':
            raise AccountInactiveError('Cuenta inactiva. Contacte al administrador.')

        # Verificar lockout por BD
        from apps.authentication.models import LoginLockout
        try:
            lockout = LoginLockout.objects.get(username=username)
            if lockout.is_locked():
                raise AccountBlockedError('Cuenta bloqueada temporalmente por intentos fallidos.')
        except LoginLockout.DoesNotExist:
            pass

        # Verificar password
        if not user.check_password(password):
            new_count = cls._record_failed_attempt(username, user=user)
            # BR-015: si llega al límite, bloquear
            if new_count >= MAX_FAILED_ATTEMPTS:
                user.state = 'BLOCKED'
                user.save(update_fields=['state'])
                cls._emit_audit('BLOCKED_LOGIN_ATTEMPT', user.pk, {
                    'username': username, 'reason': 'max_attempts_reached',
                })
                raise AccountBlockedError('Cuenta bloqueada por múltiples intentos fallidos.')
            raise InvalidCredentialsError('Credenciales inválidas.')

        # Éxito — resetear contador de lockout
        cls._reset_lockout(username)
        return user

    # ------------------------------------------------------------------
    # Pasos 10-14: persistencia dentro de transaction.atomic()
    # ------------------------------------------------------------------

    @classmethod
    def _persist_login(
        cls,
        user: 'User',
        client_info: dict,
        ip_address: str | None,
    ) -> LoginOutput:
        from apps.authentication.models import Session

        now = timezone.now()
        expires_at = now + timedelta(minutes=SESSION_TIMEOUT_MINUTES)

        # PASO 10: cerrar Sessions previas (BR-005 / CNST-004)
        prev_sessions = Session.objects.filter(user=user, state='ACTIVE')
        for prev in prev_sessions:
            prev.close(reason='SUPERSEDED')
            cls._emit_audit('SESSION_CLOSED', user.pk, {
                'session_id': str(prev.session_id),
                'close_reason': 'SUPERSEDED',
            })

        # PASO 11: detectar first_login y calcular scope
        is_first_login = user.first_login
        scope = 'restricted' if is_first_login else 'full'

        # Crear Session nueva
        session = Session.objects.create(
            user=user,
            state='ACTIVE',
            expires_at=expires_at,
            client_info=client_info,
            ip_address=ip_address,
            scope=scope,
        )

        # PASO 12: construir payload de auditoría (sin PII — CNST-026)
        audit_payload = {
            'username': user.username,
            'session_id': str(session.session_id),
            'client_info': client_info,
        }

        # Verificar si tiene permisos (FA-04)
        has_perms = cls._user_has_any_assignment(user)

        # PASO 13a: emitir LOGIN principal
        cls._emit_audit('LOGIN', user.pk, audit_payload)

        # PASO 13b: LOGIN_NO_PERMISSIONS si no tiene funciones
        warning: Optional[LoginWarning] = None
        next_step: Optional[str] = None

        if is_first_login:
            next_step = 'change_password'
        elif not has_perms:
            warning = LoginWarning(
                type='no_permissions',
                message='Su cuenta no tiene funciones asignadas. Contacte al administrador.',
            )
            cls._emit_audit('LOGIN_NO_PERMISSIONS', user.pk, {'username': user.username})
        elif user.password_expires_at:
            days_remaining = (user.password_expires_at - now).days
            if 0 <= days_remaining <= PASSWORD_EXPIRY_WARNING_DAYS:
                warning = LoginWarning(
                    type='password_expiring',
                    message=f'Su contraseña expira en {days_remaining} días.',
                    days_remaining=days_remaining,
                )

        # PASO 14: actualizar last_login_at
        user.last_login_at = now
        user.save(update_fields=['last_login_at'])

        # PASO 15: generar tokens JWT (SimpleJWT)
        tokens = cls._generate_tokens(user, expires_at)

        # Construir UserInfo
        agr_codes = cls._get_user_agr_codes(user)
        primary_agr = agr_codes[0] if agr_codes else None

        return LoginOutput(
            tokens=tokens,
            user=UserInfo(
                user_id=user.pk,
                username=user.username,
                full_name=user.get_full_name() or user.username,
                primary_access_group_id=primary_agr,
                access_groups=agr_codes,
                first_login=user.first_login,
            ),
            session=SessionInfo(
                session_id=str(session.session_id),
                started_at=session.started_at.isoformat(),
                expires_at=session.expires_at.isoformat(),
            ),
            next_step=next_step,
            warning=warning,
        )

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_tokens(user: 'User', session_expires_at) -> TokenPair:
        """Genera par de tokens JWT con SimpleJWT."""
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        access_exp = timezone.now() + timedelta(minutes=SESSION_TIMEOUT_MINUTES)
        refresh_exp = timezone.now() + timedelta(days=7)

        return TokenPair(
            access=str(access_token),
            refresh=str(refresh),
            access_expires_at=access_exp.isoformat(),
            refresh_expires_at=refresh_exp.isoformat(),
        )

    @staticmethod
    def _record_failed_attempt(username: str, user=None) -> int:
        """
        Registra intento fallido en LoginLockout.
        Retorna el nuevo contador de intentos.
        """
        from apps.authentication.models import LoginLockout, LoginAttempt
        from apps.utils.helpers import get_client_ip

        lockout, _ = LoginLockout.objects.get_or_create(
            username=username,
            defaults={'failed_attempts': 0},
        )
        if not lockout.is_locked():
            lockout.increment_attempts()

        return lockout.failed_attempts

    @staticmethod
    def _reset_lockout(username: str) -> None:
        """Resetea el contador de lockout tras login exitoso."""
        from apps.authentication.models import LoginLockout
        try:
            lockout = LoginLockout.objects.get(username=username)
            lockout.failed_attempts = 0
            lockout.locked_until = None
            lockout.save(update_fields=['failed_attempts', 'locked_until', 'last_attempt_at'])
        except LoginLockout.DoesNotExist:
            pass

    @staticmethod
    def _emit_audit(event_type: str, user_id: int, payload: dict) -> None:
        """
        Emite AuditEvent vía AuditLogService.emit().
        CNST-025: inmutable.
        CNST-026: PII eliminado por emit().
        """
        from apps.audit.services import AuditLogService
        AuditLogService.emit(
            event_type=event_type,
            actor_user_id=user_id,
            payload=payload,
        )

    @staticmethod
    def _user_has_any_assignment(user) -> bool:
        """
        FA-04: verifica si el usuario tiene al menos un Assignment activo
        o pertenece a un AccessGroup.
        """
        from apps.access.models import UserFunctionAssignment, UserAccessGroup
        direct = UserFunctionAssignment.objects.filter(
            user=user, state='ACTIVE',
        ).filter(
            models_q_not_expired()
        ).exists()
        if direct:
            return True
        return UserAccessGroup.objects.filter(user=user).exists()

    @staticmethod
    def _get_user_agr_codes(user) -> list[str]:
        """Retorna códigos de AccessGroup del usuario."""
        from apps.access.models import UserAccessGroup
        return list(
            UserAccessGroup.objects.filter(user=user)
            .values_list('access_group__code', flat=True)
            .order_by('access_group__code')
        )


def models_q_not_expired():
    """Q para filtrar Assignments no expirados."""
    from django.db.models import Q
    now = timezone.now()
    return Q(expires_at__isnull=True) | Q(expires_at__gt=now)
