"""
Servicio de bloqueo de cuentas por intentos fallidos.

CLEAN_CODE v3.0.1: Nombre que revela intención.
SOLID SRP: Solo gestión de lockout.

FR-001.02 + BR-015: 5 intentos en 30 min -> 30 minutos de bloqueo.
CNST-010: Usa PostgreSQL (NO cache/Redis).
"""

from typing import Optional
from django.utils import timezone
from django.db import transaction
from datetime import timedelta

from apps.core.services.base_service import BaseService
from apps.authentication.models import LoginLockout
from apps.authentication.constants import (
    MAX_LOGIN_ATTEMPTS,
    LOCKOUT_DURATION_MINUTES,
    LOCKOUT_WINDOW_MINUTES,
)


class LockoutService(BaseService):
    """
    Servicio de bloqueo de cuentas.

    SOLID SRP: Solo gestión de lockout.
    CNST-010: Usa PostgreSQL (NO cache/Redis).

    Responsabilidades:
    - Verificar si cuenta está bloqueada
    - Registrar intentos fallidos
    - Bloquear cuenta automáticamente
    - Desbloquear cuenta manualmente
    - Resetear contador de intentos

    FR-001.02 + BR-015: 5 intentos fallidos en 30 min -> 30 min lockout.
    CNST-010: Persistencia en PostgreSQL (NO cache volátil).
    """

    def __init__(self):
        """
        Initialize service.

        CNST-010: No cache, solo PostgreSQL.
        """
        super().__init__()
        self.max_attempts = MAX_LOGIN_ATTEMPTS
        self.lockout_duration = LOCKOUT_DURATION_MINUTES
        self.window_minutes = LOCKOUT_WINDOW_MINUTES

        self.log_info(
            f"LockoutService initialized: {self.max_attempts} attempts, "
            f"{self.lockout_duration} min lockout (PostgreSQL)"
        )

    def is_locked(self, username: str) -> bool:
        """
        Verifica si la cuenta está bloqueada.

        CNST-010: Consulta PostgreSQL (NO cache).

        Args:
            username: Username a verificar

        Returns:
            bool: True si bloqueada, False si no
        """
        try:
            lockout = LoginLockout.objects.get(username=username)

            is_currently_locked = lockout.is_locked()

            if is_currently_locked:
                self.log_warning(
                    f"Account '{username}' is locked until {lockout.locked_until}"
                )
            else:
                # Si lockout expiró, limpiar
                if lockout.locked_until:
                    lockout.unlock()
                    self.log_info(f"Lockout expired for account '{username}'")

            return is_currently_locked

        except LoginLockout.DoesNotExist:
            # No hay registro, no está bloqueado
            return False

    def get_lockout_time_remaining(self, username: str) -> Optional[timedelta]:
        """
        Obtiene tiempo restante de bloqueo.

        CNST-010: Consulta PostgreSQL (NO cache).

        Args:
            username: Username

        Returns:
            timedelta: Tiempo restante, None si no está bloqueado
        """
        try:
            lockout = LoginLockout.objects.get(username=username)

            if not lockout.locked_until:
                return None

            now = timezone.now()
            if now < lockout.locked_until:
                return lockout.locked_until - now

            return None

        except LoginLockout.DoesNotExist:
            return None

    @transaction.atomic
    def record_failed_attempt(self, username: str) -> int:
        """
        Registra intento fallido y bloquea si alcanza el límite.

        CNST-010: Usa PostgreSQL con transacción (NO cache).

        Args:
            username: Username del intento fallido

        Returns:
            int: Número actual de intentos fallidos
        """
        # Obtener o crear registro de lockout
        lockout, created = LoginLockout.objects.get_or_create(
            username=username,
            defaults={'failed_attempts': 0}
        )

        # Si ya está bloqueado, no incrementar
        if lockout.is_locked():
            self.log_info(f"Account '{username}' already locked, attempt not counted")
            return lockout.failed_attempts

        # Incrementar contador
        attempts = lockout.increment_attempts()

        self.log_warning(f"Failed attempt #{attempts} for account '{username}'")

        # Si alcanzó el máximo, bloquear
        if attempts >= self.max_attempts:
            self._lock_account(username, lockout)
            self.log_warning(
                f"Account '{username}' locked after {attempts} failed attempts"
            )

        return attempts

    def get_failed_attempts_count(self, username: str) -> int:
        """
        Obtiene número de intentos fallidos actuales.

        CNST-010: Consulta PostgreSQL (NO cache).

        Args:
            username: Username

        Returns:
            int: Número de intentos fallidos (0 si no existe o está bloqueado)
        """
        try:
            lockout = LoginLockout.objects.get(username=username)
            # Si está bloqueado, retornar 0 (no contar intentos durante lockout)
            return lockout.failed_attempts if not lockout.is_locked() else 0
        except LoginLockout.DoesNotExist:
            return 0

    def reset_failed_attempts(self, username: str):
        """
        Resetea el contador de intentos fallidos.

        Se llama después de login exitoso.
        CNST-010: Actualiza PostgreSQL (NO cache).

        Args:
            username: Username
        """
        try:
            lockout = LoginLockout.objects.get(username=username)
            lockout.failed_attempts = 0
            lockout.save(update_fields=['failed_attempts', 'last_attempt_at'])

            self.log_info(f"Failed attempts counter reset for '{username}'")
        except LoginLockout.DoesNotExist:
            # No existe, no hay nada que resetear
            pass

    def unlock_account(self, username: str):
        """
        Desbloquea cuenta manualmente.

        CNST-010: Actualiza PostgreSQL (NO cache).

        Args:
            username: Username a desbloquear
        """
        try:
            lockout = LoginLockout.objects.get(username=username)
            lockout.unlock()

            self.log_info(f"Account '{username}' manually unlocked")
        except LoginLockout.DoesNotExist:
            # No existe, crear con valores limpios
            LoginLockout.objects.create(
                username=username,
                failed_attempts=0,
                locked_until=None
            )
            self.log_info(f"Account '{username}' unlock record created")

    def _lock_account(self, username: str, lockout: Optional[LoginLockout] = None):
        """
        Bloquea la cuenta por el tiempo configurado.

        SOLID SRP: Solo bloquea cuenta.
        CNST-010: Actualiza PostgreSQL (NO cache).

        Args:
            username: Username a bloquear
            lockout: Objeto LoginLockout existente (opcional)
        """
        if not lockout:
            try:
                lockout = LoginLockout.objects.get(username=username)
            except LoginLockout.DoesNotExist:
                lockout = LoginLockout.objects.create(
                    username=username,
                    failed_attempts=self.max_attempts
                )

        lockout.lock(duration_minutes=self.lockout_duration)

        self.log_error(
            f"Account '{username}' LOCKED until {lockout.locked_until}"
        )
