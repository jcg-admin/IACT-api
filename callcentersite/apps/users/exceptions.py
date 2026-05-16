"""
Excepciones personalizadas para apps/users/.

Todas heredan de BusinessRuleError (apps.core.exceptions).

CLEAN_CODE v3.0.1: Nombres auto-documentados, Single Responsibility.
"""

from apps.core.exceptions import BusinessRuleError


class UserServiceError(BusinessRuleError):
    """
    Error base para operaciones de User.

    Hereda de BusinessRuleError (apps.core.exceptions).

    Example:
        raise UserServiceError("Error al procesar usuario")
    """
    pass


class UserAlreadyExistsError(UserServiceError):
    """
    Error cuando se intenta crear un usuario que ya existe.

    Se lanza cuando username o email ya están en uso.

    Example:
        if User.objects.filter(username=username).exists():
            raise UserAlreadyExistsError(f"Username '{username}' ya existe")
    """
    pass


class UserNotFoundError(UserServiceError):
    """
    Error cuando no se encuentra un usuario.

    Se lanza cuando se busca un usuario que no existe.

    Example:
        user = User.objects.filter(id=user_id).first()
        if not user:
            raise UserNotFoundError(f"Usuario {user_id} no encontrado")
    """
    pass


class InvalidCredentialsError(UserServiceError):
    """
    Error cuando las credenciales son inválidas.

    Se lanza durante autenticación cuando username/password son incorrectos.

    Example:
        user = authenticate(username=username, password=password)
        if not user:
            raise InvalidCredentialsError("Credenciales inválidas")
    """
    pass


class UserInactiveError(UserServiceError):
    """
    Error cuando se intenta autenticar un usuario inactivo.

    Se lanza cuando el usuario existe pero is_active=False.

    Example:
        if not user.is_active:
            raise UserInactiveError(f"Usuario '{user.username}' está inactivo")
    """
    pass


class PasswordValidationError(UserServiceError):
    """
    Error cuando la validación de password falla.

    Se lanza cuando el password no cumple los requisitos.

    Example:
        if len(password) < 8:
            raise PasswordValidationError("Password debe tener mínimo 8 caracteres")
    """
    pass


# ============================================================================
# RESUMEN EXCEPTIONS
#
# Total Exceptions: 6
#
# Base:
#   [SUCCESS] UserServiceError (BusinessLogicError)
#
# Específicas:
#   [SUCCESS] UserAlreadyExistsError - Username/email duplicado
#   [SUCCESS] UserNotFoundError - Usuario no encontrado
#   [SUCCESS] InvalidCredentialsError - Credenciales incorrectas
#   [SUCCESS] UserInactiveError - Usuario inactivo
#   [SUCCESS] PasswordValidationError - Password inválido
#
# Uso de Arquitectura:
#   [SUCCESS] BusinessLogicError (apps.core.exceptions)
#
# Principios SOLID:
#   [SUCCESS] SRP: Cada excepción una responsabilidad
#   [SUCCESS] Clean Naming: Nombres descriptivos
#   [SUCCESS] Herencia: Jerarquía clara
#
# Líneas: ~110
# ============================================================================
