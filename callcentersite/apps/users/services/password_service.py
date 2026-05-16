"""
PasswordService - Service Layer para gestión de passwords.

Hereda de BaseService (apps.core.services).
Gestiona password reset con tokens.

CLEAN_CODE v3.0.1: Service Layer Pattern, Single Responsibility.
"""

from django.db import transaction
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings

from apps.core.services import BaseService
from apps.users.exceptions import (
    PasswordValidationError,
    UserServiceError,
)
from apps.audit.services import AuditLogService

User = get_user_model()


class PasswordService(BaseService):
    """
    Service para gestión de passwords.

    Hereda de BaseService (apps.core.services).

    Responsabilidades:
    - Password reset (solicitud + confirmación)
    - Generación de tokens
    - Envío de emails
    - Validación de passwords

    Flujo Password Reset:
    1. Usuario solicita reset -> request_password_reset()
    2. Se genera token y se envía email
    3. Usuario recibe email con link + token
    4. Usuario confirma con nuevo password -> reset_password_confirm()

    Example:
        service = PasswordService()
        # Paso 1: Solicitar reset
        service.request_password_reset(email='user@company.com')
        # Paso 2: Confirmar con token
        service.reset_password_confirm(
            uidb64='MQ',
            token='abc123',
            new_password='NewPass123'
        )
    """

    def __init__(self):
        """Inicializa PasswordService."""
        super().__init__()
        self.audit_service = AuditLogService()
        self.token_generator = default_token_generator

    @transaction.atomic
    def request_password_reset(self, email: str) -> bool:
        """
        Solicita reset de password.

        Proceso:
        1. Busca usuario por email
        2. Genera token de reset
        3. Envía email con link
        4. Registra en audit log

        Args:
            email: Email del usuario

        Returns:
            bool: True si se envió email (o no existe usuario)

        Note:
            Por seguridad, siempre retorna True incluso si el email
            no existe, para no revelar si un email está registrado.

        Example:
            >>> service = PasswordService()
            >>> success = service.request_password_reset(
            ...     email='user@company.com'
            ... )
            >>> print(success)
            True
        """
        self.log_info(f"Solicitud de password reset: {email}")

        try:
            user = User.objects.get(email=email, is_active=True, is_deleted=False)
        except User.DoesNotExist:
            # Por seguridad, no revelar que el email no existe
            self.log_warning(f"Password reset solicitado para email inexistente: {email}")
            return True

        # Generar token
        token = self.token_generator.make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

        # Generar link de reset
        reset_link = self._generate_reset_link(uidb64, token)

        # Enviar email
        self._send_reset_email(user, reset_link)

        # Audit log
        self.audit_service.log_action(resource="user",
            action='PASSWORD_RESET_REQUESTED',
            user=user,
            details={'email': email}
        )

        self.log_info(f"Email de password reset enviado: {email}")
        return True

    @transaction.atomic
    def reset_password_confirm(
        self,
        uidb64: str,
        token: str,
        new_password: str,
    ) -> User:
        """
        Confirma reset de password con token.

        Proceso:
        1. Decodifica uidb64 para obtener user_id
        2. Valida token
        3. Valida nuevo password
        4. Actualiza password
        5. Registra en audit log

        Args:
            uidb64: User ID codificado en base64
            token: Token de reset
            new_password: Nuevo password

        Returns:
            User: Usuario con password actualizado

        Raises:
            UserServiceError: Si token es inválido o expiró
            PasswordValidationError: Si password no cumple requisitos

        Example:
            >>> service = PasswordService()
            >>> user = service.reset_password_confirm(
            ...     uidb64='MQ',
            ...     token='abc123',
            ...     new_password='NewPass456'
            ... )
        """
        self.log_info("Confirmando reset de password")

        # Decodificar user_id
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise UserServiceError("Token de reset inválido")

        # Validar token
        if not self.token_generator.check_token(user, token):
            raise UserServiceError("Token de reset inválido o expirado")

        # Validar nuevo password
        self._validate_password(new_password)

        # Actualizar password
        user.set_password(new_password)
        user.save()

        # Audit log
        self.audit_service.log_action(resource="user",
            action='PASSWORD_RESET_CONFIRMED',
            user=user,
            details={'email': user.email}
        )

        self.log_info(f"Password reset confirmado: {user.email}")
        return user

    def validate_reset_token(self, uidb64: str, token: str) -> bool:
        """
        Valida token de reset sin cambiar password.

        Útil para verificar que el link de reset es válido
        antes de mostrar el formulario de nuevo password.

        Args:
            uidb64: User ID codificado en base64
            token: Token de reset

        Returns:
            bool: True si token es válido

        Example:
            >>> service = PasswordService()
            >>> is_valid = service.validate_reset_token(
            ...     uidb64='MQ',
            ...     token='abc123'
            ... )
            >>> print(is_valid)
            True
        """
        self.log_info("Validando token de reset")

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            return self.token_generator.check_token(user, token)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return False

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

    def _generate_reset_link(self, uidb64: str, token: str) -> str:
        """
        Genera link de password reset.

        Args:
            uidb64: User ID codificado
            token: Token de reset

        Returns:
            str: URL completa para reset

        Example:
            >>> link = service._generate_reset_link('MQ', 'abc123')
            >>> print(link)
            'https://example.com/reset-password/MQ/abc123/'
        """
        # BASE_URL se lee de settings.BASE_URL (valor por defecto en config/settings/base.py)
        base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
        return f"{base_url}/api/v1/users/auth/reset-password/{uidb64}/{token}/"

    def _send_reset_email(self, user: User, reset_link: str) -> None:
        """
        Envía email con link de reset.

        Args:
            user: Usuario que solicitó reset
            reset_link: Link de reset

        Note:
            Si EMAIL_BACKEND no está configurado, solo logea.
        """
        subject = "Recuperación de contraseña"
        message = f"""
Hola {user.get_full_name() or user.username},

Has solicitado recuperar tu contraseña.

Por favor, haz clic en el siguiente enlace para crear una nueva contraseña:

{reset_link}

Si no solicitaste este cambio, ignora este email.

Este enlace expirará en 24 horas.

Saludos,
El equipo de Call Center
        """

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            self.log_info(f"Email enviado a: {user.email}")
        except Exception as e:
            self.log_error(f"Error enviando email: {str(e)}")
            # No lanzar excepción para no revelar errores al usuario


# ============================================================================
# RESUMEN PasswordService
#
# Hereda de: BaseService (apps.core.services)
#
# Métodos Públicos: 3
#   [SUCCESS] request_password_reset() - Solicita reset y envía email
#   [SUCCESS] reset_password_confirm() - Confirma con token
#   [SUCCESS] validate_reset_token() - Valida token sin cambiar password
#
# Métodos Privados: 3
#   [SUCCESS] _validate_password() - Valida requisitos
#   [SUCCESS] _generate_reset_link() - Genera URL de reset
#   [SUCCESS] _send_reset_email() - Envía email
#
# Dependencias:
#   [SUCCESS] BaseService (apps.core.services) - Logging
#   [SUCCESS] AuditService (apps.audit.services) - Audit logging
#   [SUCCESS] Django default_token_generator - Tokens seguros
#   [SUCCESS] Django send_mail - Envío de emails
#   [SUCCESS] Exceptions de apps.users.exceptions
#
# Seguridad:
#   [SUCCESS] No revela si email existe
#   [SUCCESS] Tokens con expiración automática
#   [SUCCESS] Validación de password
#   [SUCCESS] Audit logging completo
#
# Flujo:
#   1. request_password_reset(email) -> Genera token + envía email
#   2. Usuario recibe email con link
#   3. reset_password_confirm(uidb64, token, password) -> Actualiza
#
# Principios SOLID:
#   [SUCCESS] SRP: Solo gestión de password reset
#   [SUCCESS] DIP: Depende de BaseService
#   [SUCCESS] Clean Code: Métodos claros y cohesivos
#
# Líneas: ~320
# ============================================================================
