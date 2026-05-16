"""
Request Logging Middleware.

CNST-031: Auditoría completa de requests HTTP.
CLEAN_CODE v3.0.1: Nombre auto-documentado.
"""

import logging
import time
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class RequestLoggingHandler(MiddlewareMixin):
    """
    Middleware para loggear requests HTTP.

    CNST-031: Auditoría de todos los requests.
    CLEAN_CODE v3.0.1: Nombre que revela intención.

    Loggea:
    - URL, method, user
    - Timestamp inicio/fin
    - Duration
    - Response status code
    - IP del cliente

    Instalación:
        # settings.py
        MIDDLEWARE = [
            ...
            'apps.core.middleware.logging.RequestLoggingHandler',
        ]

    Examples:
        # Logs automáticos:
        [REQUEST] GET /api/reports/ | User: admin | IP: 192.168.1.1 | Status: 200 | Duration: 0.234s
    """

    def process_request(self, request):
        """
        Procesa request (inicio).

        Agrega:
        - start_time: Timestamp inicio
        - client_ip: IP del cliente

        Args:
            request: HttpRequest

        Returns:
            None
        """
        # Timestamp inicio
        request.start_time = time.time()

        # IP del cliente
        from apps.utils.helpers import get_client_ip
        request.client_ip = get_client_ip(request)

        return None

    def process_response(self, request, response):
        """
        Procesa response y loggea.

        Args:
            request: HttpRequest
            response: HttpResponse

        Returns:
            HttpResponse
        """
        # Calcular duration
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
        else:
            duration = 0

        # Usuario
        user = request.user if hasattr(request, 'user') else None
        username = user.username if user and user.is_authenticated else 'anonymous'

        # IP
        client_ip = getattr(request, 'client_ip', 'unknown')

        # Log
        logger.info(
            f"[REQUEST] {request.method} {request.path} | "
            f"User: {username} | "
            f"IP: {client_ip} | "
            f"Status: {response.status_code} | "
            f"Duration: {duration:.3f}s"
        )

        return response


# ============================================================================
# RESUMEN MIDDLEWARE LOGGING
#
# Middleware: RequestLoggingHandler
# Propósito: Auditar todos los requests HTTP
# CNST: CNST-031 (Auditoría completa)
#
# Logs incluyen:
#   [SUCCESS] Method + Path
#   [SUCCESS] Usuario (o anonymous)
#   [SUCCESS] IP del cliente
#   [SUCCESS] Status code
#   [SUCCESS] Duration en segundos
#
# Instalación: Agregar a MIDDLEWARE en settings
# ============================================================================
