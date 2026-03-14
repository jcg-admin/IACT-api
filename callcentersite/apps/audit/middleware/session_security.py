from django.utils.deprecation import MiddlewareMixin
from apps.audit.models import AuditLog
from apps.utils import get_client_ip, get_user_agent, should_exclude_path


class SessionSecurityMiddleware(MiddlewareMixin):
    """
    Middleware de seguridad de sesion.
    
    - Registra todas las peticiones API en auditoria
    - Captura IP y User-Agent usando utilidades compartidas
    - Excluye paths admin/static/schema
    
    Refactorizado para usar apps.core.utils.request:
    - get_client_ip()
    - get_user_agent()
    - should_exclude_path()
    """
    
    EXCLUDED_PATHS = [
        '/admin/jsi18n/',
        '/api/schema/',
        '/__debug__/',
    ]
    
    def process_request(self, request):
        """
        Procesar peticion entrante.
        
        Registra en auditoria si:
        - Usuario autenticado
        - Path NO excluido
        - Metodo relevante (GET, POST, PUT, DELETE, PATCH)
        """
        # Verificar si path debe ser excluido (usa utility compartida)
        if should_exclude_path(request.path, self.EXCLUDED_PATHS):
            return None
        
        # Solo registrar si hay usuario autenticado
        if not request.user or not request.user.is_authenticated:
            return None
        
        # Capturar contexto (usa utilities compartidas)
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)
        
        # Registrar en auditoria
        try:
            AuditLog.record(
                user=request.user,
                action='API_REQUEST',
                resource=request.path,
                result='SUCCESS',
                ip_address=ip_address,
                user_agent=user_agent,
                details={
                    'method': request.method,
                    'path': request.path,
                }
            )
        except Exception:
            # No fallar si auditoria falla
            pass
        
        return None
