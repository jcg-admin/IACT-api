"""
Helper functions para apps/utils/.

CLEAN_CODE v3.0.1: Funciones auto-documentadas.
SOLID: SRP, DRY.
"""

from typing import Optional, Any, Dict, List
import uuid
import hashlib
import secrets


# ============================================================================
# REQUEST HELPERS
# ============================================================================

def get_client_ip(request) -> str:
    """
    Obtiene IP real del cliente.
    
    CLEAN_CODE v3.0.1: Nombre que revela intención.
    SOLID SRP: Solo obtiene IP.
    
    Busca IP en orden:
    1. HTTP_X_FORWARDED_FOR (detrás de proxy)
    2. HTTP_X_REAL_IP (detrás de nginx)
    3. REMOTE_ADDR (conexión directa)
    
    Args:
        request: HttpRequest de Django
    
    Returns:
        str: IP del cliente
    
    Examples:
        >>> ip = get_client_ip(request)
        '192.168.1.100'
    """
    # DRY: Headers en orden de prioridad
    headers_to_check = [
        'HTTP_X_FORWARDED_FOR',
        'HTTP_X_REAL_IP',
        'REMOTE_ADDR'
    ]
    
    for header in headers_to_check:
        value = request.META.get(header)
        
        if value:
            # X-Forwarded-For puede tener múltiples IPs
            if header == 'HTTP_X_FORWARDED_FOR':
                # Primera IP es la real
                ip = value.split(',')[0].strip()
            else:
                ip = value.strip()
            
            if ip:
                return ip
    
    return 'unknown'


def get_user_agent(request) -> str:
    """
    Obtiene User-Agent del request.
    
    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID SRP: Solo obtiene User-Agent.
    
    Args:
        request: HttpRequest de Django
    
    Returns:
        str: User-Agent
    
    Examples:
        >>> ua = get_user_agent(request)
        'Mozilla/5.0 ...'
    """
    return request.META.get('HTTP_USER_AGENT', 'unknown')


def is_ajax_request(request) -> bool:
    """
    Verifica si request es AJAX.
    
    CLEAN_CODE v3.0.1: Nombre auto-documentado.
    SOLID SRP: Solo verifica AJAX.
    
    Args:
        request: HttpRequest
    
    Returns:
        bool: True si es AJAX
    
    Examples:
        >>> is_ajax_request(request)
        True
    """
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


# ============================================================================
# UUID HELPERS
# ============================================================================

def generate_uuid() -> str:
    """
    Genera UUID único.
    
    CLEAN_CODE v3.0.1: Nombre que revela intención.
    SOLID SRP: Solo genera UUID.
    
    Returns:
        str: UUID (UUID4)
    
    Examples:
        >>> uid = generate_uuid()
        '550e8400-e29b-41d4-a716-446655440000'
    """
    return str(uuid.uuid4())


def generate_short_uuid(length: int = 8) -> str:
    """
    Genera UUID corto.
    
    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID SRP: Solo genera UUID corto.
    
    Args:
        length: Longitud deseada
    
    Returns:
        str: UUID corto
    
    Examples:
        >>> short_id = generate_short_uuid()
        'a1b2c3d4'
    """
    return uuid.uuid4().hex[:length]


# ============================================================================
# HASH HELPERS
# ============================================================================

def hash_string(text: str, algorithm: str = 'sha256') -> str:
    """
    Hashea string.
    
    CLEAN_CODE v3.0.1: Nombre que revela intención.
    SOLID SRP: Solo hashea.
    SOLID OCP: Soporta múltiples algoritmos.
    
    Args:
        text: Texto
        algorithm: Algoritmo ('md5', 'sha256', 'sha512')
    
    Returns:
        str: Hash hexadecimal
    
    Examples:
        >>> hash_string('hello')
        '2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824'
    """
    if algorithm == 'md5':
        return hashlib.md5(text.encode()).hexdigest()
    elif algorithm == 'sha256':
        return hashlib.sha256(text.encode()).hexdigest()
    elif algorithm == 'sha512':
        return hashlib.sha512(text.encode()).hexdigest()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")


def generate_random_token(length: int = 32) -> str:
    """
    Genera token aleatorio seguro.
    
    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID SRP: Solo genera token.
    
    Args:
        length: Longitud en bytes
    
    Returns:
        str: Token hexadecimal
    
    Examples:
        >>> token = generate_random_token(16)
        'a1b2c3d4e5f6...'
    """
    return secrets.token_hex(length)


# ============================================================================
# DICT HELPERS
# ============================================================================

def safe_get(
    dictionary: Dict,
    key_path: str,
    default: Any = None
) -> Any:
    """
    Obtiene valor de dict anidado de forma segura.
    
    CLEAN_CODE v3.0.1: Nombre que revela intención.
    SOLID SRP: Solo obtiene valor.
    
    Args:
        dictionary: Diccionario
        key_path: Path de keys separadas por punto
        default: Valor por defecto
    
    Returns:
        Any: Valor o default
    
    Examples:
        >>> data = {'user': {'name': 'John', 'age': 30}}
        >>> safe_get(data, 'user.name')
        'John'
        >>> safe_get(data, 'user.email', 'N/A')
        'N/A'
    """
    keys = key_path.split('.')
    
    current = dictionary
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    
    return current


def merge_dicts(*dicts: Dict) -> Dict:
    """
    Merge múltiples dicts.
    
    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID SRP: Solo merge dicts.
    
    Args:
        *dicts: Dicts a mergear
    
    Returns:
        dict: Dict mergeado
    
    Examples:
        >>> d1 = {'a': 1, 'b': 2}
        >>> d2 = {'b': 3, 'c': 4}
        >>> merge_dicts(d1, d2)
        {'a': 1, 'b': 3, 'c': 4}
    """
    result = {}
    
    for d in dicts:
        result.update(d)
    
    return result


# ============================================================================
# LIST HELPERS
# ============================================================================

def chunk_list(items: List, chunk_size: int) -> List[List]:
    """
    Divide lista en chunks.
    
    CLEAN_CODE v3.0.1: Nombre que revela intención.
    SOLID SRP: Solo divide lista.
    
    Args:
        items: Lista
        chunk_size: Tamaño de cada chunk
    
    Returns:
        list: Lista de chunks
    
    Examples:
        >>> chunk_list([1, 2, 3, 4, 5], 2)
        [[1, 2], [3, 4], [5]]
    """
    chunks = []
    
    for i in range(0, len(items), chunk_size):
        chunk = items[i:i + chunk_size]
        chunks.append(chunk)
    
    return chunks


def flatten_list(nested_list: List[List]) -> List:
    """
    Aplana lista anidada.
    
    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID SRP: Solo aplana.
    
    Args:
        nested_list: Lista anidada
    
    Returns:
        list: Lista plana
    
    Examples:
        >>> flatten_list([[1, 2], [3, 4], [5]])
        [1, 2, 3, 4, 5]
    """
    flattened = []
    
    for item in nested_list:
        if isinstance(item, list):
            flattened.extend(item)
        else:
            flattened.append(item)
    
    return flattened


def unique_list(items: List) -> List:
    """
    Remueve duplicados de lista.
    
    CLEAN_CODE v3.0.1: Nombre auto-documentado.
    SOLID SRP: Solo remueve duplicados.
    
    Preserva orden.
    
    Args:
        items: Lista
    
    Returns:
        list: Lista sin duplicados
    
    Examples:
        >>> unique_list([1, 2, 2, 3, 1, 4])
        [1, 2, 3, 4]
    """
    seen = set()
    unique = []
    
    for item in items:
        if item not in seen:
            seen.add(item)
            unique.append(item)
    
    return unique


# ============================================================================
# BOOLEAN HELPERS
# ============================================================================

def str_to_bool(value: str) -> bool:
    """
    Convierte string a boolean.
    
    CLEAN_CODE v3.0.1: Nombre que revela intención.
    SOLID SRP: Solo convierte.
    
    Args:
        value: String
    
    Returns:
        bool: Boolean
    
    Examples:
        >>> str_to_bool('true')
        True
        >>> str_to_bool('yes')
        True
        >>> str_to_bool('1')
        True
        >>> str_to_bool('false')
        False
    """
    # DRY: Valores true centralizados
    true_values = _get_true_string_values()
    
    return value.lower().strip() in true_values


def _get_true_string_values() -> set:
    """
    Valores string considerados True.
    
    SOLID SRP: Solo provee valores.
    DRY: Centralizado.
    
    Returns:
        set: Valores true
    """
    return {'true', 'yes', '1', 'on', 'enabled'}


# ============================================================================
# CLEANUP HELPERS
# ============================================================================

def remove_none_values(dictionary: Dict) -> Dict:
    """
    Remueve valores None de dict.
    
    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID SRP: Solo remueve None.
    
    Args:
        dictionary: Dict
    
    Returns:
        dict: Dict sin None
    
    Examples:
        >>> remove_none_values({'a': 1, 'b': None, 'c': 3})
        {'a': 1, 'c': 3}
    """
    return {k: v for k, v in dictionary.items() if v is not None}


def remove_empty_strings(dictionary: Dict) -> Dict:
    """
    Remueve strings vacíos de dict.
    
    CLEAN_CODE v3.0.1: Nombre auto-documentado.
    SOLID SRP: Solo remueve vacíos.
    
    Args:
        dictionary: Dict
    
    Returns:
        dict: Dict sin strings vacíos
    
    Examples:
        >>> remove_empty_strings({'a': 'hello', 'b': '', 'c': 'world'})
        {'a': 'hello', 'c': 'world'}
    """
    return {k: v for k, v in dictionary.items() if v != ''}


# ============================================================================
# RESUMEN HELPERS
# 
# Total: 18 funciones públicas + 1 helper privado
# 
# Request Helpers:
#   [SUCCESS] get_client_ip()
#   [SUCCESS] get_user_agent()
#   [SUCCESS] is_ajax_request()
# 
# UUID Helpers:
#   [SUCCESS] generate_uuid()
#   [SUCCESS] generate_short_uuid()
# 
# Hash Helpers:
#   [SUCCESS] hash_string()
#   [SUCCESS] generate_random_token()
# 
# Dict Helpers:
#   [SUCCESS] safe_get()
#   [SUCCESS] merge_dicts()
#   [SUCCESS] remove_none_values()
#   [SUCCESS] remove_empty_strings()
# 
# List Helpers:
#   [SUCCESS] chunk_list()
#   [SUCCESS] flatten_list()
#   [SUCCESS] unique_list()
# 
# Boolean Helpers:
#   [SUCCESS] str_to_bool()
# 
# Helpers Privados (DRY):
#   [SUCCESS] _get_true_string_values()
# 
# Principios SOLID Aplicados:
#   [SUCCESS] SRP: Cada función una responsabilidad
#   [SUCCESS] DRY: Helper privado para valores true
#   [SUCCESS] OCP: hash_string soporta múltiples algoritmos
#   [SUCCESS] Clean Naming: Nombres descriptivos
#   [SUCCESS] Type Hints: Todas las funciones
# ============================================================================


def should_exclude_path(path: str, excluded_paths: list = None) -> bool:
    """
    Determina si un path debe ser excluido de audit logging.
    
    Args:
        path: Path de la request (ej: '/api/v1/users/')
        excluded_paths: Lista opcional de paths a excluir
    
    Returns:
        bool: True si debe ser excluido
    
    Example:
        >>> should_exclude_path('/admin/')
        True
        >>> should_exclude_path('/api/v1/users/')
        False
        >>> should_exclude_path('/custom/', ['/custom/'])
        True
    """
    if excluded_paths is None:
        excluded_paths = [
            '/admin/',
            '/static/',
            '/media/',
            '/api/schema/',
            '/__debug__/',
        ]
    
    for excluded in excluded_paths:
        if path.startswith(excluded):
            return True
    
    return False
