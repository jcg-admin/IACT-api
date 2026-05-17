"""
Context processors para templates Django.

CLEAN_CODE v3.0.1: Nombres auto-documentados.
SOLID SRP: Cada processor una responsabilidad.
"""

from django.conf import settings


def site_settings(request):
    """
    Agrega settings del sitio al context de templates.

    CLEAN_CODE v3.0.1: Nombre que revela intención.
    SOLID SRP: Solo provee site settings.

    Disponible en todos los templates:
    - {{ SITE_NAME }}
    - {{ VERSION }}
    - {{ DEBUG }}

    Instalación:
        # settings.py
        TEMPLATES = [{
            'OPTIONS': {
                'context_processors': [
                    ...
                    'apps.core.context_processors.site_settings',
                ],
            },
        }]

    Args:
        request: HttpRequest

    Returns:
        dict: Variables de contexto

    Examples:
        # En template:
        <h1>{{ SITE_NAME }}</h1>
        <p>Version {{ VERSION }}</p>
    """
    return {
        'SITE_NAME': getattr(settings, 'SITE_NAME', 'IACT Call Center'),
        'VERSION': getattr(settings, 'VERSION', '1.0.0'),
        'DEBUG': settings.DEBUG,
    }


def user_permissions(request):
    """
    Agrega funciones RBAC del usuario al context.

    RBAC v6.0.0: Usa métodos del User model directamente.
    ARQUITECTURA CORRECTA: No depende de apps específicas.

    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID SRP: Solo provee user permissions.
    SOLID DIP: No depende de implementaciones específicas.

    Disponible en templates:
    - {{ user_functions }} (set de namespaces Django)

    Permite verificar permisos en templates:
    {% if 'reports.create' in user_functions %}
        <button>Crear Reporte</button>
    {% endif %}

    Instalación:
        # settings.py
        TEMPLATES = [{
            'OPTIONS': {
                'context_processors': [
                    ...
                    'apps.core.context_processors.user_permissions',
                ],
            },
        }]

    Args:
        request: HttpRequest

    Returns:
        dict: Variables de contexto con user_functions

    Examples:
        # En template:
        {% if 'reports.create' in user_functions %}
            <a href="{% url 'reports:create' %}">Nuevo Reporte</a>
        {% endif %}

        {% if 'users.edit' in user_functions %}
            <button>Editar Usuario</button>
        {% endif %}

    Architecture Note:
        Uses User.get_functions() method instead of AccessService
        to avoid creating a dependency from core -> access.
        This respects the Dependency Inversion Principle (DIP).
    """
    user_functions = []

    if request.user.is_authenticated:
        try:
            # [SUCCESS] CORRECTO: User model tiene get_functions()
            # No depende de apps específicas (DIP compliance)
            user_functions = list(request.user.get_functions())
        except Exception:
            # Si falla, retornar lista vacía
            user_functions = []

    return {
        'user_functions': user_functions,
    }


def request_meta(request):
    """
    Agrega metadata del request al context.

    CLEAN_CODE v3.0.1: Nombre auto-documentado.
    SOLID SRP: Solo provee request metadata.

    Disponible en templates:
    - {{ client_ip }}
    - {{ user_agent }}

    Útil para:
    - Debugging
    - Auditoría
    - Analytics

    Instalación:
        # settings.py
        TEMPLATES = [{
            'OPTIONS': {
                'context_processors': [
                    ...
                    'apps.core.context_processors.request_meta',
                ],
            },
        }]

    Args:
        request: HttpRequest

    Returns:
        dict: Variables de contexto

    Examples:
        # En template:
        <p>Tu IP: {{ client_ip }}</p>
        <p>Browser: {{ user_agent }}</p>
    """
    from apps.utils.helpers import get_client_ip, get_user_agent

    return {
        'client_ip': get_client_ip(request),
        'user_agent': get_user_agent(request),
    }


# ============================================================================
# RESUMEN CONTEXT PROCESSORS
#
# Total: 3 context processors
#
# Processors:
#   [SUCCESS] site_settings() - SITE_NAME, VERSION, DEBUG
#   [SUCCESS] user_permissions() - user_functions (RBAC)
#   [SUCCESS] request_meta() - client_ip, user_agent
#
# Instalación:
#   Agregar a TEMPLATES['OPTIONS']['context_processors'] en settings.py
#
# Uso en Templates:
#   {{ SITE_NAME }}
#   {% if 'reports.create' in user_functions %}...{% endif %}
#   {{ client_ip }}
#
# Principios SOLID:
#   [SUCCESS] SRP: Cada processor una responsabilidad
#   [SUCCESS] Clean Naming: Nombres descriptivos
#   [SUCCESS] Documentation: Docstrings + ejemplos
# ============================================================================
