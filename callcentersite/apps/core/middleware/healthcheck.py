"""
Health Check Middleware.

CLEAN_CODE v3.0.1: Nombre auto-documentado.
"""

from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse


class HealthCheckHandler(MiddlewareMixin):
    """
    Middleware para health check.

    CLEAN_CODE v3.0.1: Nombre que revela intención.

    Responde a /health/ sin autenticación.
    Útil para load balancers, monitoring, etc.

    Endpoint:
        GET /health/
        -> 200 OK {"status": "healthy"}

    Instalación:
        # settings.py
        MIDDLEWARE = [
            'apps.core.middleware.healthcheck.HealthCheckHandler',  # <- Primero
            ...
        ]

    Uso:
        # Load balancer health check:
        curl http://localhost:8000/health/
        -> {"status": "healthy"}

        # Monitoring:
        if response.status_code == 200:
            service_is_up = True

    Examples:
        >>> import requests
        >>> response = requests.get('http://localhost:8000/health/')
        >>> response.json()
        {'status': 'healthy'}
        >>> response.status_code
        200
    """

    def process_request(self, request):
        """
        Procesa health check.

        Si path es /health/, retorna JSON response inmediatamente.
        Si no, continúa con el request normal.

        Args:
            request: HttpRequest

        Returns:
            JsonResponse si es /health/, None si no
        """
        if request.path == '/health/':
            return JsonResponse({
                'status': 'healthy',
                'service': 'IACT Call Center',
            })

        return None


# ============================================================================
# RESUMEN MIDDLEWARE HEALTHCHECK
#
# Middleware: HealthCheckHandler
# Propósito: Endpoint /health/ para monitoring
#
# Endpoint:
#   GET /health/
#   -> 200 OK {"status": "healthy", "service": "IACT Call Center"}
#
# Características:
#   [SUCCESS] No requiere autenticación
#   [SUCCESS] Response inmediata (no pasa por otros middlewares)
#   [SUCCESS] Ideal para load balancers
#   [SUCCESS] Ideal para monitoring (Prometheus, Datadog, etc)
#
# Instalación: Agregar PRIMERO en MIDDLEWARE (settings)
# ============================================================================
