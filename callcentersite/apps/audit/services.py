"""
Service para gestión de logs de auditoría.

Proporciona métodos para registrar acciones en el sistema
manteniendo la inmutabilidad del AuditLog (CNST-009).
"""
from typing import Optional, Dict, Any
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from .models import AuditLog

User = get_user_model()


class AuditLogService:
    """
    Service para crear logs de auditoría.
    
    Maneja la creación de logs con información completa
    del contexto de la petición.
    """
    
    # Constantes de acciones
    LOGIN = 'LOGIN'
    LOGOUT = 'LOGOUT'
    CREATE = 'CREATE'
    UPDATE = 'UPDATE'
    DELETE = 'DELETE'
    VIEW = 'VIEW'
    EXPORT = 'EXPORT'
    IMPORT = 'IMPORT'
    ACCESS_DENIED = 'ACCESS_DENIED'
    ERROR = 'ERROR'
    
    # Resultados
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'
    
    @classmethod
    def log(
        cls,
        user: Optional[User],
        action: str,
        resource: str,
        result: str = SUCCESS,
        request: Optional[HttpRequest] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AuditLog:
        """
        Registrar log de auditoría.
        
        Args:
            user: Usuario que realiza la acción (None para anónimos)
            action: Acción realizada (LOGIN, CREATE, etc.)
            resource: Recurso afectado (ej: 'User:123', 'Report:export')
            result: SUCCESS o FAILURE
            request: HttpRequest para extraer IP y User-Agent
            details: Dict con información adicional
            **kwargs: Campos adicionales del log
            
        Returns:
            AuditLog: Log creado
            
        Examples:
            >>> AuditLogService.log(
            ...     user=request.user,
            ...     action=AuditLogService.CREATE,
            ...     resource='Report:123',
            ...     request=request,
            ...     details={'name': 'Monthly Report'}
            ... )
        """
        # Extraer info del request si está disponible
        ip_address = None
        user_agent = ''
        
        if request:
            from apps.utils import get_client_ip, get_user_agent
            ip_address = get_client_ip(request)
            user_agent = get_user_agent(request)
        
        # Crear log
        return AuditLog.objects.create(
            user=user,
            action=action,
            resource=resource,
            result=result,
            ip_address=ip_address or kwargs.get('ip_address'),
            user_agent=user_agent or kwargs.get('user_agent', ''),
            details=details,
        )
    
    @classmethod
    def log_login(
        cls,
        user: User,
        request: Optional[HttpRequest] = None,
        success: bool = True,
        details: Optional[Dict] = None
    ) -> AuditLog:
        """
        Registrar intento de login.
        
        Args:
            user: Usuario intentando login
            request: HttpRequest
            success: Si login fue exitoso
            details: Info adicional (ej: método de auth)
            
        Returns:
            AuditLog: Log creado
        """
        return cls.log(
            user=user,
            action=cls.LOGIN,
            resource=f'User:{user.id}',
            result=cls.SUCCESS if success else cls.FAILURE,
            request=request,
            details=details,
        )
    
    @classmethod
    def log_logout(
        cls,
        user: User,
        request: Optional[HttpRequest] = None
    ) -> AuditLog:
        """
        Registrar logout.
        
        Args:
            user: Usuario haciendo logout
            request: HttpRequest
            
        Returns:
            AuditLog: Log creado
        """
        return cls.log(
            user=user,
            action=cls.LOGOUT,
            resource=f'User:{user.id}',
            request=request,
        )
    
    @classmethod
    def log_create(
        cls,
        user: User,
        resource_type: str,
        resource_id: Any,
        request: Optional[HttpRequest] = None,
        details: Optional[Dict] = None
    ) -> AuditLog:
        """
        Registrar creación de recurso.
        
        Args:
            user: Usuario que crea
            resource_type: Tipo de recurso (ej: 'Report', 'User')
            resource_id: ID del recurso creado
            request: HttpRequest
            details: Datos adicionales del recurso
            
        Returns:
            AuditLog: Log creado
        """
        return cls.log(
            user=user,
            action=cls.CREATE,
            resource=f'{resource_type}:{resource_id}',
            request=request,
            details=details,
        )
    
    @classmethod
    def log_update(
        cls,
        user: User,
        resource_type: str,
        resource_id: Any,
        request: Optional[HttpRequest] = None,
        details: Optional[Dict] = None
    ) -> AuditLog:
        """
        Registrar actualización de recurso.
        
        Args:
            user: Usuario que actualiza
            resource_type: Tipo de recurso
            resource_id: ID del recurso
            request: HttpRequest
            details: Cambios realizados (ej: {'field': 'old -> new'})
            
        Returns:
            AuditLog: Log creado
        """
        return cls.log(
            user=user,
            action=cls.UPDATE,
            resource=f'{resource_type}:{resource_id}',
            request=request,
            details=details,
        )
    
    @classmethod
    def log_delete(
        cls,
        user: User,
        resource_type: str,
        resource_id: Any,
        request: Optional[HttpRequest] = None,
        details: Optional[Dict] = None
    ) -> AuditLog:
        """
        Registrar eliminación de recurso.
        
        Args:
            user: Usuario que elimina
            resource_type: Tipo de recurso
            resource_id: ID del recurso
            request: HttpRequest
            details: Info del recurso eliminado
            
        Returns:
            AuditLog: Log creado
        """
        return cls.log(
            user=user,
            action=cls.DELETE,
            resource=f'{resource_type}:{resource_id}',
            request=request,
            details=details,
        )
    
    @classmethod
    def log_access_denied(
        cls,
        user: Optional[User],
        resource: str,
        request: Optional[HttpRequest] = None,
        reason: Optional[str] = None
    ) -> AuditLog:
        """
        Registrar intento de acceso denegado.
        
        Args:
            user: Usuario (None si anónimo)
            resource: Recurso al que intentó acceder
            request: HttpRequest
            reason: Razón del rechazo
            
        Returns:
            AuditLog: Log creado
        """
        details = {'reason': reason} if reason else None
        return cls.log(
            user=user,
            action=cls.ACCESS_DENIED,
            resource=resource,
            result=cls.FAILURE,
            request=request,
            details=details,
        )
    
    @classmethod
    def log_export(
        cls,
        user: User,
        resource_type: str,
        request: Optional[HttpRequest] = None,
        details: Optional[Dict] = None
    ) -> AuditLog:
        """
        Registrar exportación de datos.
        
        Args:
            user: Usuario que exporta
            resource_type: Tipo de datos exportados
            request: HttpRequest
            details: Info de la exportación (formato, filtros, etc)
            
        Returns:
            AuditLog: Log creado
        """
        return cls.log(
            user=user,
            action=cls.EXPORT,
            resource=resource_type,
            request=request,
            details=details,
        )


    def log_action(self, action: str, user=None, details: dict = None, resource: str = 'unknown'):
        """
        Wrapper genérico para log().
        
        Mapea action a los métodos específicos de AuditLogService.
        
        Args:
            action: Tipo de acción (USER_CREATED, USER_UPDATED, etc)
            user: Usuario que realiza la acción
            details: Dict con detalles adicionales
            resource: Recurso afectado
        """
        # Por ahora, usar log() genérico
        self.log(
            user=user,
            action=action,
            resource=resource,
            details=details or {},
        )


# ===========================================================================
# emit() — FASE 0 (F0-T5)
# ===========================================================================
# Fuente: UC_PERM_09 CA-01..03, BR-008, BR-010, CNST-025, CNST-026
# modelo-dominio-iact.rst § 4.7 (AuditEvent.record())

    @classmethod
    def emit(
        cls,
        event_type: str,
        actor_user_id: int,
        payload: dict | None = None,
        *,
        target_entity_type: str = '',
        target_entity_id: str = '',
        ip_address: str | None = None,
        user_agent: str = '',
    ) -> 'AuditLog':
        """
        Emite un AuditEvent inmutable — punto de entrada canónico (FASE 1+).

        UC_PERM_09 CA-01: emit básico → AuditEvent persistido + id.
        UC_PERM_09 CA-02: inmutable — save() rechaza UPDATE.
        UC_PERM_09 CA-03: event_type desconocido → AuditValidationError.
        CNST-025: append-only.
        CNST-026: PII eliminado del payload antes de persistir.

        Args:
            event_type: Código canónico del evento (ver VALID_EVENT_TYPES).
            actor_user_id: ID del usuario que actúa.
            payload: Dict con contexto del evento (sin PII).
            target_entity_type: Tipo de entidad afectada (ej: 'User').
            target_entity_id: ID de entidad afectada (ej: '42').
            ip_address: IP del request, si aplica.
            user_agent: User-Agent del request, si aplica.

        Returns:
            AuditLog: Evento persistido con pk asignado.

        Raises:
            AuditValidationError: Si event_type no está en VALID_EVENT_TYPES.
        """
        from apps.audit.models import VALID_EVENT_TYPES, AuditValidationError, _PII_FIELDS, AuditLog
        from django.contrib.auth import get_user_model

        # UC_PERM_09 CA-03: validar event_type
        if event_type not in VALID_EVENT_TYPES:
            raise AuditValidationError(
                f"event_type desconocido: {event_type!r}. "
                f"Valores válidos: {sorted(VALID_EVENT_TYPES)}"
            )

        # CNST-026: eliminar PII del payload
        clean_payload = cls._strip_pii(payload or {})

        # Resolver User (puede ser None si el ID no existe — FK nullable)
        User = get_user_model()
        try:
            user = User.objects.get(pk=actor_user_id)
        except User.DoesNotExist:
            user = None

        # resource = "EntityType:EntityId" — formato canónico
        resource = (
            f"{target_entity_type}:{target_entity_id}"
            if target_entity_type else f"actor:{actor_user_id}"
        )

        return AuditLog.objects.create(
            user=user,
            action=event_type,       # Campo 'action' existente ← mapea a event_type
            resource=resource,
            result='SUCCESS',
            ip_address=ip_address,
            user_agent=user_agent or '',
            details=clean_payload,
        )

    @staticmethod
    def _strip_pii(payload: dict) -> dict:
        """
        CNST-026: Elimina campos PII del payload antes de persistir.

        Elimina recursivamente cualquier clave en _PII_FIELDS.
        Las claves se normalizan a minúsculas para la comparación.

        Args:
            payload: Dict original con potencial PII.

        Returns:
            Dict limpio sin campos PII. PII reemplazado por '[REDACTED]'.
        """
        from apps.audit.models import _PII_FIELDS

        if not isinstance(payload, dict):
            return payload

        clean = {}
        for key, value in payload.items():
            if key.lower() in _PII_FIELDS:
                clean[key] = '[REDACTED]'
            elif isinstance(value, dict):
                clean[key] = AuditLogService._strip_pii(value)
            else:
                clean[key] = value
        return clean
