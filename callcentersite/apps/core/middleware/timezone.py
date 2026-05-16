"""
User Timezone Middleware.

CLEAN_CODE v3.0.1: Nombre auto-documentado.
CORRECCIÓN v5.1.1: Simplificado a usar configuración global del sistema.
"""

import pytz
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from django.conf import settings


class UserTimezoneHandler(MiddlewareMixin):
    """
    Middleware para timezone del sistema.

    CORRECCIÓN v5.1.1:
    Simplificado a usar configuración global (settings.TIME_ZONE).

    IMPORTANTE:
    UserSettings NO tiene campo timezone (eliminado en FASE 2 PARTE 2).
    Sistema usa timezone global: America/Mexico_City.

    CLEAN_CODE v3.0.1: Nombre que revela intención.

    Activa timezone global del sistema.
    Todas las fechas se muestran en el mismo timezone.

    Timezone: America/Mexico_City (configurado en settings.py)

    Instalación:
        # settings.py
        MIDDLEWARE = [
            ...
            'apps.core.middleware.timezone.UserTimezoneHandler',
        ]

        TIME_ZONE = 'America/Mexico_City'  # <- Configuración global

    Uso:
        # El timezone se activa automáticamente
        # Todas las fechas se muestran en America/Mexico_City

        # En views/templates:
        {{ order.created_at }}  # Se muestra en America/Mexico_City

    Examples:
        # Timezone global: America/Mexico_City
        # created_at: 2025-01-20 10:00 UTC
        # Se muestra: 2025-01-20 04:00 CST

    Note:
        Para timezone por usuario, agregar campo timezone a UserSettings
        y modificar _get_timezone() para leerlo.
    """

    def process_request(self, request):
        """
        Activa timezone del sistema.

        Args:
            request: HttpRequest

        Returns:
            None
        """
        # Obtener timezone de configuración
        tz = self._get_timezone(request.user)

        try:
            timezone.activate(pytz.timezone(tz))
        except pytz.UnknownTimeZoneError:
            # Fallback a Mexico City si timezone inválido
            timezone.activate(pytz.timezone('America/Mexico_City'))

        return None

    def _get_timezone(self, user):
        """
        Obtiene timezone a usar.

        CORRECCIÓN v5.1.1:
        Retorna settings.TIME_ZONE (configuración global).

        # El timezone del usuario se gestiona via SettingsView (cache-backed).
        # Para activar: leer cache key user_settings:{pk} y extraer timezone.
            if user.is_authenticated and hasattr(user, 'settings'):
                return getattr(user.settings, 'timezone', settings.TIME_ZONE)

        Args:
            user: User object (puede ser AnonymousUser)

        Returns:
            str: Timezone (ej: 'America/Mexico_City')
        """
        # Usar configuración global del sistema
        return getattr(settings, 'TIME_ZONE', 'America/Mexico_City')


# ============================================================================
# RESUMEN MIDDLEWARE TIMEZONE
#
# Middleware: UserTimezoneHandler
# Versión: v5.1.1 (Simplificado)
# Propósito: Activar timezone global del sistema automáticamente
#
# Comportamiento:
#   [SUCCESS] Todos los usuarios -> America/Mexico_City (settings.TIME_ZONE)
#   [SUCCESS] Timezone inválido -> fallback a America/Mexico_City
#
# CORRECCIÓN v5.1.1:
#   - UserSettings NO tiene campo timezone (eliminado FASE 2 PARTE 2)
#   - Sistema usa timezone global configurado en settings.py
#
# Benefit:
#   - Todas las fechas se muestran en timezone consistente
#   - No necesita conversión manual en views/templates
#   - Evita AttributeError por user.timezone inexistente
#
# Instalación: Agregar a MIDDLEWARE en settings
# ============================================================================
