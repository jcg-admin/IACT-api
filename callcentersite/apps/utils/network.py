"""
apps/utils/network.py

Utilidades de red: extracción de IP, User-Agent y metadata del request HTTP.

Estas funciones son el punto de entrada canónico para todo el proyecto.
apps.utils.request contiene la implementación base; este módulo la re-exporta
y agrega get_request_metadata con el campo query_string requerido por la capa
de auditoría.
"""
from apps.utils.request import get_client_ip, get_user_agent


__all__ = ['get_client_ip', 'get_user_agent', 'get_request_metadata']


def get_request_metadata(request) -> dict:
    """
    Metadata completo del request HTTP.

    Retorna ip, user_agent, method, path y query_string.
    Usado en auditoría y logging estructurado.

    Returns:
        dict con claves: ip, user_agent, method, path, query_string
    """
    return {
        'ip':           get_client_ip(request),
        'user_agent':   get_user_agent(request),
        'method':       request.method,
        'path':         request.path,
        'query_string': request.META.get('QUERY_STRING', ''),
    }
