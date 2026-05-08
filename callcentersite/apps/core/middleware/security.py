"""
Security Headers Middleware.

CLEAN_CODE v3.0.1: Nombre auto-documentado.
"""

from django.utils.deprecation import MiddlewareMixin


class SecurityHeadersPolicy(MiddlewareMixin):
    """
    Middleware para headers de seguridad.
    
    CLEAN_CODE v3.0.1: Nombre que revela intención.
    
    Agrega headers de seguridad a todas las responses HTTP.
    
    Headers agregados:
    - X-Content-Type-Options: nosniff (evita MIME sniffing)
    - X-Frame-Options: DENY (evita clickjacking)
    - X-XSS-Protection: 1; mode=block (evita XSS)
    - Referrer-Policy: same-origin (protege privacidad)
    
    Instalación:
        # settings.py
        MIDDLEWARE = [
            ...
            'apps.core.middleware.security.SecurityHeadersPolicy',
        ]
    
    Examples:
        # Headers automáticos en todas las responses:
        X-Content-Type-Options: nosniff
        X-Frame-Options: DENY
        X-XSS-Protection: 1; mode=block
        Referrer-Policy: same-origin
    """
    
    def process_response(self, request, response):
        """
        Agrega headers de seguridad.
        
        Args:
            request: HttpRequest
            response: HttpResponse
        
        Returns:
            HttpResponse con headers de seguridad
        """
        # Prevenir MIME sniffing
        response['X-Content-Type-Options'] = 'nosniff'
        
        # Prevenir clickjacking
        response['X-Frame-Options'] = 'DENY'
        
        # Prevenir XSS
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Proteger privacidad de referrer
        response['Referrer-Policy'] = 'same-origin'
        
        return response


# ============================================================================
# RESUMEN MIDDLEWARE SECURITY
# 
# Middleware: SecurityHeadersPolicy
# Propósito: Agregar headers de seguridad HTTP
# 
# Headers:
#   [SUCCESS] X-Content-Type-Options: nosniff
#   [SUCCESS] X-Frame-Options: DENY
#   [SUCCESS] X-XSS-Protection: 1; mode=block
#   [SUCCESS] Referrer-Policy: same-origin
# 
# Instalación: Agregar a MIDDLEWARE en settings
# ============================================================================
