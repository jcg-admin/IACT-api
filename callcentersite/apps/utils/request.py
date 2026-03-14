"""
Utilidades reutilizables para manejar requests HTTP.

Funciones:
- get_client_ip: Obtener IP real del cliente
- get_user_agent: Obtener User-Agent
- should_exclude_path: Verificar si path debe excluirse
"""
from typing import Optional


def get_client_ip(request) -> str:
    """
    Obtener IP real del cliente considerando proxies.
    
    Busca la IP en el siguiente orden:
    1. HTTP_X_FORWARDED_FOR (si está detrás de proxy)
    2. HTTP_X_REAL_IP (si está detrás de nginx)
    3. REMOTE_ADDR (conexión directa)
    
    Args:
        request: HttpRequest de Django
        
    Returns:
        str: Dirección IP del cliente
        
    Examples:
        >>> ip = get_client_ip(request)
        >>> print(ip)  # "192.168.1.100"
    """
    # Intentar obtener IP de headers de proxy
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # X-Forwarded-For puede contener múltiples IPs separadas por comas
        # La primera es la IP real del cliente
        ip = x_forwarded_for.split(',')[0].strip()
        return ip
    
    # Intentar header alternativo (nginx)
    x_real_ip = request.META.get('HTTP_X_REAL_IP')
    if x_real_ip:
        return x_real_ip.strip()
    
    # Fallback a REMOTE_ADDR (conexión directa)
    remote_addr = request.META.get('REMOTE_ADDR', '')
    return remote_addr.strip()


def get_user_agent(request) -> str:
    """
    Obtener User-Agent del request.
    
    Args:
        request: HttpRequest de Django
        
    Returns:
        str: User-Agent del navegador o cadena vacía si no existe
        
    Examples:
        >>> ua = get_user_agent(request)
        >>> print(ua)  # "Mozilla/5.0 (Windows NT 10.0; Win64; x64)..."
    """
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    return user_agent.strip()


def should_exclude_path(path: str, excluded_paths: Optional[list] = None) -> bool:
    """
    Verificar si un path debe ser excluido del procesamiento.
    
    Paths excluidos por defecto:
    - /admin/ (Django admin)
    - /static/ (archivos estáticos)
    - /media/ (archivos media)
    - /api/health/ (health check)
    - /api/docs/ (documentación API)
    
    Args:
        path: Path del request (ej: "/api/users/")
        excluded_paths: Lista adicional de paths a excluir (opcional)
        
    Returns:
        bool: True si debe excluirse, False si no
        
    Examples:
        >>> should_exclude_path("/admin/users/")
        True
        >>> should_exclude_path("/api/users/")
        False
        >>> should_exclude_path("/custom/", excluded_paths=["/custom/"])
        True
    """
    # Paths excluidos por defecto
    default_excluded = [
        '/admin/',
        '/static/',
        '/media/',
        '/api/health/',
        '/api/docs/',
        '/swagger/',
        '/redoc/',
    ]
    
    # Combinar con paths adicionales
    all_excluded = default_excluded.copy()
    if excluded_paths:
        all_excluded.extend(excluded_paths)
    
    # Verificar si path comienza con alguno de los excluidos
    for excluded_path in all_excluded:
        if path.startswith(excluded_path):
            return True
    
    return False


def is_ajax_request(request) -> bool:
    """
    Verificar si el request es AJAX.
    
    Detecta requests AJAX por:
    1. Header X-Requested-With: XMLHttpRequest (jQuery, axios)
    2. Content-Type: application/json (APIs modernas)
    
    Args:
        request: HttpRequest de Django
        
    Returns:
        bool: True si es AJAX, False si no
        
    Examples:
        >>> is_ajax_request(request)
        True  # Si tiene header X-Requested-With
    """
    # Método tradicional (jQuery)
    if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        return True
    
    # Método moderno (Accept: application/json)
    accept = request.META.get('HTTP_ACCEPT', '')
    if 'application/json' in accept:
        return True
    
    return False


def get_request_info(request) -> dict:
    """
    Obtener información completa del request.
    
    Útil para logging, auditoría, debugging.
    
    Args:
        request: HttpRequest de Django
        
    Returns:
        dict: Diccionario con información del request
        
    Examples:
        >>> info = get_request_info(request)
        >>> print(info['ip'])  # "192.168.1.100"
        >>> print(info['user_agent'])  # "Mozilla/5.0..."
    """
    return {
        'ip': get_client_ip(request),
        'user_agent': get_user_agent(request),
        'path': request.path,
        'method': request.method,
        'is_ajax': is_ajax_request(request),
        'is_secure': request.is_secure(),
        'user': request.user.username if request.user.is_authenticated else 'Anonymous',
    }
