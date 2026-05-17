"""
Base Service class para IACT.

CLEAN_CODE v3.0.1: Service Layer Pattern.
SOLID: SRP - Cada service una responsabilidad.
"""

import logging

logger = logging.getLogger(__name__)


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
            def generate_report(self, params):
                self.log_info("Generando reporte...")
                # Lógica aquí
                self.log_info("Reporte generado")

    Examples:
        >>> class MiService(BaseService):
        ...     def do_something(self):
        ...         self.log_info("Doing something...")
        ...         return True
    """

    def log_info(self, message: str):
        """
        Log info level con nombre del service.

        Args:
            message: Mensaje a loggear

        Examples:
            >>> service = ReportService()
            >>> service.log_info("Generando reporte trimestral")
            # [ReportService] Generando reporte trimestral
        """
        logger.info(f"[{self.__class__.__name__}] {message}")

    def log_error(self, message: str):
        """
        Log error level con nombre del service.

        Args:
            message: Mensaje de error

        Examples:
            >>> service = ReportService()
            >>> service.log_error("Fallo al generar PDF")
            # [ReportService] Fallo al generar PDF
        """
        logger.error(f"[{self.__class__.__name__}] {message}")

    def log_warning(self, message: str):
        """
        Log warning level con nombre del service.

        Args:
            message: Mensaje de warning
        """
        logger.warning(f"[{self.__class__.__name__}] {message}")

    def log_debug(self, message: str):
        """
        Log debug level con nombre del service.

        Args:
            message: Mensaje de debug
        """
        logger.debug(f"[{self.__class__.__name__}] {message}")
