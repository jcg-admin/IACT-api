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
