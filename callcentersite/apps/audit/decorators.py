"""
Decorators para auditoría automática.

Permite decorar views/viewsets para registrar acciones
automáticamente en AuditLog.
"""
from functools import wraps
from typing import Optional, Callable
from .services import AuditLogService


def audit_log(
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    get_resource_id: Optional[Callable] = None,
):
    """
    Decorator para registrar acciones en AuditLog automáticamente.
    
    Args:
        action: Acción a registrar (CREATE, UPDATE, DELETE, etc.)
                Si None, se infiere del método HTTP
        resource_type: Tipo de recurso (ej: 'Report', 'User')
                       Si None, se usa el nombre de la view
        get_resource_id: Función para extraer ID del recurso
                         (por defecto usa kwargs['pk'])
    
    Usage:
        # En function-based view:
        @audit_log(action='VIEW', resource_type='Report')
        def report_detail(request, pk):
            ...
        
        # En ViewSet method:
        class ReportViewSet(viewsets.ModelViewSet):
            @audit_log()
            def destroy(self, request, *args, **kwargs):
                # Se registrará DELETE automáticamente
                ...
    
    Examples:
        # Auto-detectar acción desde método HTTP
        @audit_log(resource_type='Report')
        def create_report(request):
            # Acción será CREATE (inferida de POST)
            ...
        
        # Especificar acción manualmente
        @audit_log(action='EXPORT', resource_type='Report')
        def export_report(request, pk):
            ...
        
        # Custom resource ID
        @audit_log(
            action='UPDATE',
            resource_type='Setting',
            get_resource_id=lambda view, **kw: kw.get('setting_key')
        )
        def update_setting(request, setting_key):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Detectar si es function-based o class-based view
            if args and hasattr(args[0], 'request'):
                # Class-based view (self, request)
                view_instance = args[0]
                request = view_instance.request
                view_name = view_instance.__class__.__name__
            elif args and hasattr(args[0], 'method'):
                # Function-based view (request, ...)
                request = args[0]
                view_name = func.__name__
            else:
                # Sin request, ejecutar sin auditoría
                return func(*args, **kwargs)
            
            # Ejecutar función original
            response = func(*args, **kwargs)
            
            # Solo auditar si hay usuario autenticado
            if not request.user or not request.user.is_authenticated:
                return response
            
            # Inferir acción si no se especificó
            log_action = action
            if not log_action:
                method = request.method
                action_map = {
                    'POST': AuditLogService.CREATE,
                    'PUT': AuditLogService.UPDATE,
                    'PATCH': AuditLogService.UPDATE,
                    'DELETE': AuditLogService.DELETE,
                    'GET': AuditLogService.VIEW,
                }
                log_action = action_map.get(method, AuditLogService.VIEW)
            
            # Determinar resource_type
            res_type = resource_type or view_name
            
            # Obtener resource_id
            resource_id = None
            if get_resource_id:
                resource_id = get_resource_id(
                    view_instance if hasattr(args[0], 'request') else None,
                    **kwargs
                )
            else:
                # Por defecto usar 'pk' de kwargs
                resource_id = kwargs.get('pk', kwargs.get('id'))
            
            # Construir resource string
            if resource_id:
                resource = f'{res_type}:{resource_id}'
            else:
                resource = res_type
            
            # Determinar resultado (SUCCESS/FAILURE)
            result = AuditLogService.SUCCESS
            if hasattr(response, 'status_code'):
                # Response de DRF o Django
                if response.status_code >= 400:
                    result = AuditLogService.FAILURE
            
            # Registrar en AuditLog
            try:
                AuditLogService.log(
                    user=request.user,
                    action=log_action,
                    resource=resource,
                    result=result,
                    request=request,
                )
            except Exception as e:
                # No fallar si el logging falla
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Error creating audit log: {e}')
            
            return response
        
        return wrapper
    return decorator


def audit_action(action_name: str):
    """
    Decorator simplificado para ViewSet actions.
    
    Registra la acción especificada automáticamente.
    
    Args:
        action_name: Nombre de la acción (CREATE, UPDATE, etc.)
    
    Usage:
        class ReportViewSet(viewsets.ModelViewSet):
            @action(detail=True, methods=['post'])
            @audit_action('EXPORT')
            def export(self, request, pk=None):
                ...
    """
    return audit_log(action=action_name)
