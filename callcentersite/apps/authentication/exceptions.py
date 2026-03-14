"""
Exceptions para authentication con jerarquía SOLID.

CLEAN_CODE v3.0.1: Nombres auto-documentados.
SOLID OCP: Jerarquía extensible sin modificar base.
SOLID SRP: Cada exception una responsabilidad clara.

Jerarquía:
- IACTBaseException (core)
  - AuthenticationBaseError (base authentication)
    - InvalidCredentialsError
    - AccountLockedError
    - UserInactiveError
    - SessionExpiredError
  - SecurityQuestionError (base security questions)
    - SecurityQuestionsNotConfiguredError
    - InvalidSecurityAnswersError
    - InsufficientSecurityQuestionsError
"""

from typing import Optional, Dict, Any
from rest_framework import status
from rest_framework.exceptions import APIException

from apps.core.exceptions import IACTBaseException


# ============================================================================
# BASE AUTHENTICATION EXCEPTIONS
# ============================================================================

class AuthenticationBaseError(APIException, IACTBaseException):
    """
    Excepción base para errores de autenticación.
    
    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID OCP: Base extensible sin modificación.
    SOLID SRP: Solo errores de autenticación.
    
    Atributos estándar:
    - error_code: Código único del error
    - details: Detalles adicionales (dict)
    - user_message: Mensaje para mostrar al usuario
    - log_message: Mensaje para logs
    
    Métodos:
    - to_dict(): Serializa a diccionario
    - get_user_message(): Mensaje amigable
    - should_log(): Si debe loguearse
    """
    
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = 'Error de autenticación.'
    default_code = 'authentication_error'
    
    # SOLID OCP: Atributos que subclases pueden override
    error_code: str = 'AUTH_ERROR'
    should_notify_user: bool = True
    should_log_error: bool = True
    
    def __init__(
        self,
        detail: Optional[str] = None,
        code: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Inicializa exception.
        
        SOLID SRP: Solo inicialización.
        
        Args:
            detail: Mensaje de detalle
            code: Código de error HTTP
            error_code: Código único del error
            details: Detalles adicionales
        """
        super().__init__(detail, code)
        
        if error_code:
            self.error_code = error_code
        
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serializa a diccionario.
        
        SOLID SRP: Solo serialización.
        
        Returns:
            dict: Exception serializada
        
        Example:
            >>> error = InvalidCredentialsError()
            >>> error.to_dict()
            {
                'error_code': 'INVALID_CREDENTIALS',
                'message': 'Usuario o contraseña inválidos.',
                'details': {},
                'status_code': 401
            }
        """
        return {
            'error_code': self.error_code,
            'message': str(self.detail),
            'details': self.details,
            'status_code': self.status_code
        }
    
    def get_user_message(self) -> str:
        """
        Obtiene mensaje amigable para el usuario.
        
        SOLID SRP: Solo genera mensaje.
        
        Returns:
            str: Mensaje para mostrar al usuario
        """
        if self.should_notify_user:
            return str(self.detail)
        return 'Ha ocurrido un error. Por favor, intenta nuevamente.'
    
    def should_log(self) -> bool:
        """
        Determina si debe loguearse.
        
        SOLID SRP: Solo verifica logging.
        
        Returns:
            bool: True si debe loguearse
        """
        return self.should_log_error


class InvalidCredentialsError(AuthenticationBaseError):
    """
    Usuario o contraseña inválidos.
    
    SOLID OCP: Extiende AuthenticationBaseError sin modificarlo.
    SOLID SRP: Solo credenciales inválidas.
    """
    
    default_detail = 'Usuario o contraseña inválidos.'
    default_code = 'invalid_credentials'
    error_code = 'INVALID_CREDENTIALS'
    should_notify_user = True
    should_log_error = True


class AccountLockedError(AuthenticationBaseError):
    """
    Cuenta bloqueada por intentos fallidos.
    
    CNST-005: 5 intentos -> 15 min lockout.
    """
    
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'Cuenta bloqueada temporalmente por múltiples intentos fallidos.'
    default_code = 'account_locked'
    error_code = 'ACCOUNT_LOCKED'
    should_notify_user = True
    should_log_error = True


class UserInactiveError(AuthenticationBaseError):
    """
    Usuario inactivo.
    
    SOLID SRP: Solo usuario inactivo.
    """
    
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'Usuario inactivo. Contacte al administrador.'
    default_code = 'user_inactive'
    error_code = 'USER_INACTIVE'
    should_notify_user = True
    should_log_error = True


class SessionExpiredError(AuthenticationBaseError):
    """
    Sesión expirada.
    
    SOLID SRP: Solo sesiones expiradas.
    """
    
    default_detail = 'Sesión expirada. Por favor, inicia sesión nuevamente.'
    default_code = 'session_expired'
    error_code = 'SESSION_EXPIRED'
    should_notify_user = True
    should_log_error = False  # No loguear, es esperado


# ============================================================================
# SECURITY QUESTION EXCEPTIONS
# ============================================================================

class SecurityQuestionError(APIException, IACTBaseException):
    """
    Excepción base para errores de preguntas de seguridad.
    
    SOLID OCP: Base extensible.
    SOLID SRP: Solo errores de security questions.
    
    CNST-001: Password reset SIN email, solo preguntas.
    """
    
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Error en preguntas de seguridad.'
    default_code = 'security_question_error'
    error_code = 'SECURITY_QUESTION_ERROR'
    should_notify_user = True
    should_log_error = True
    
    def __init__(
        self,
        detail: Optional[str] = None,
        code: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Inicializa exception."""
        super().__init__(detail, code)
        
        if error_code:
            self.error_code = error_code
        
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa a diccionario."""
        return {
            'error_code': self.error_code,
            'message': str(self.detail),
            'details': self.details,
            'status_code': self.status_code
        }


class SecurityQuestionsNotConfiguredError(SecurityQuestionError):
    """
    Usuario no tiene preguntas de seguridad configuradas.
    
    CNST-001: 5 preguntas obligatorias.
    """
    
    default_detail = 'Debe configurar sus preguntas de seguridad primero.'
    default_code = 'security_questions_not_configured'
    error_code = 'SECURITY_QUESTIONS_NOT_CONFIGURED'


class InvalidSecurityAnswersError(SecurityQuestionError):
    """
    Respuestas de seguridad incorrectas.
    
    SOLID SRP: Solo respuestas incorrectas.
    """
    
    default_detail = 'Las respuestas de seguridad son incorrectas.'
    default_code = 'invalid_security_answers'
    error_code = 'INVALID_SECURITY_ANSWERS'


class InsufficientSecurityQuestionsError(SecurityQuestionError):
    """
    No hay suficientes preguntas de seguridad.
    
    CNST-001: Se requieren exactamente 5 preguntas.
    """
    
    default_detail = 'Se requieren exactamente 5 preguntas de seguridad.'
    default_code = 'insufficient_security_questions'
    error_code = 'INSUFFICIENT_SECURITY_QUESTIONS'


# ============================================================================
# RESUMEN EXCEPTIONS
# 
# Jerarquía SOLID:
#   IACTBaseException (core)
#   == AuthenticationBaseError
#   -   == InvalidCredentialsError
#   -   == AccountLockedError
#   -   == UserInactiveError
#   -   == SessionExpiredError
#   == SecurityQuestionError
#       == SecurityQuestionsNotConfiguredError
#       == InvalidSecurityAnswersError
#       == InsufficientSecurityQuestionsError
# 
# Principios SOLID:
#   [SUCCESS] SRP: Cada exception una responsabilidad
#   [SUCCESS] OCP: Extensible sin modificar base
#   [SUCCESS] LSP: Subclases sustituibles
#   [SUCCESS] ISP: Interface segregation (métodos específicos)
#   [SUCCESS] DIP: Dependen de abstracción (IACTBaseException)
# 
# Features:
#   [SUCCESS] error_code único por exception
#   [SUCCESS] to_dict() para serialización
#   [SUCCESS] get_user_message() para UI
#   [SUCCESS] should_log() para logging
#   [SUCCESS] details dict para contexto adicional
# ============================================================================
