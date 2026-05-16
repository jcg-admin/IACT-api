"""
Base Service classes y Service Access para IACT.

CLEAN_CODE v3.0.1: Service Layer Pattern.
SOLID: SRP - Cada service una responsabilidad.
"""

from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


# ============================================================================
# BASE SERVICE
# ============================================================================

class BaseService:
    """
    Service base para todos los services.

    CLEAN_CODE v3.0.1: Service Layer Pattern.
    SOLID SRP: Solo provee funcionalidad base.

    Provee:
    - Logging automático con nombre del service
    - Exception handling helpers
    - Métodos comunes reutilizables

    Uso:
        class ReportService(BaseService):
            @classmethod
            def generate_report(cls, params):
                cls.log_info("Generando reporte...")
                # Lógica aquí
                cls.log_info("Reporte generado")

    Examples:
        >>> class MiService(BaseService):
        ...     @classmethod
        ...     def do_something(cls):
        ...         cls.log_info("Doing something...")
        ...         return True
    """

    @classmethod
    def log_info(cls, message: str):
        """
        Log info level con nombre del service.

        Args:
            message: Mensaje a loggear

        Examples:
            >>> ReportService.log_info("Generando reporte trimestral")
            # [ReportService] Generando reporte trimestral
        """
        logger.info(f"[{cls.__name__}] {message}")

    @classmethod
    def log_error(cls, message: str):
        """
        Log error level con nombre del service.

        Args:
            message: Mensaje de error

        Examples:
            >>> ReportService.log_error("Fallo al generar PDF")
            # [ReportService] Fallo al generar PDF
        """
        logger.error(f"[{cls.__name__}] {message}")

    @classmethod
    def log_warning(cls, message: str):
        """
        Log warning level con nombre del service.

        Args:
            message: Mensaje de warning
        """
        logger.warning(f"[{cls.__name__}] {message}")

    @classmethod
    def log_debug(cls, message: str):
        """
        Log debug level con nombre del service.

        Args:
            message: Mensaje de debug
        """
        logger.debug(f"[{cls.__name__}] {message}")


# ============================================================================

# ====================================================================================
# REMOVED - FASE A DT-002 (2026-01-21)
# ====================================================================================
#
# ServiceAccessService (eliminado):
#   - get_user_services(): Obtener servicios de usuario
#   - has_service_access(): Verificar acceso
#   - filter_by_user_services(): Filtrar QuerySet
#   - grant_service_access(): Otorgar accesos
#   - revoke_service_access(): Revocar accesos
#   - get_services_summary(): Resumen de servicios
#
# Razón: UserServiceAccess eliminado, reemplazado por RBAC puro
# Reemplazo: Usar RBAC con Functions (CALL_VIEW, SVC_VIEW, etc.)
# ====================================================================================
