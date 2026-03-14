"""
Decorators para apps/utils/.

CLEAN_CODE v3.0.1: Decoradores auto-documentados.
SOLID: SRP, DRY.
"""

import time
import logging
from functools import wraps
from typing import Callable, Any, Optional
from django.core.cache import cache

logger = logging.getLogger(__name__)


# ============================================================================
# LOGGING DECORATOR
# ============================================================================

def log_execution(func: Callable) -> Callable:
    """
    Decorador para loggear ejecución de función.
    
    CLEAN_CODE v3.0.1: Nombre que revela intención.
    SOLID SRP: Solo loggea ejecución.
    
    Loggea:
    - Nombre función
    - Args y kwargs
    - Tiempo ejecución
    - Resultado o error
    
    Usage:
        @log_execution
        def my_function(x, y):
            return x + y
    
    Examples:
        >>> @log_execution
        ... def add(a, b):
        ...     return a + b
        >>> add(2, 3)
        5
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        
        # Log inicio
        logger.info(f"[EXEC] {func_name} - START - args={args}, kwargs={kwargs}")
        
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            
            elapsed = time.time() - start_time
            
            # Log éxito
            logger.info(
                f"[EXEC] {func_name} - SUCCESS - "
                f"time={elapsed:.3f}s"
            )
            
            return result
        
        except Exception as e:
            elapsed = time.time() - start_time
            
            # Log error
            logger.error(
                f"[EXEC] {func_name} - ERROR - "
                f"time={elapsed:.3f}s - error={str(e)}"
            )
            
            raise
    
    return wrapper


def log_duration(func: Callable) -> Callable:
    """
    Decorador para loggear solo duración.
    
    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID SRP: Solo loggea tiempo.
    
    Usage:
        @log_duration
        def slow_function():
            time.sleep(1)
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        result = func(*args, **kwargs)
        
        elapsed = time.time() - start_time
        
        logger.info(f"[DURATION] {func.__name__} took {elapsed:.3f}s")
        
        return result
    
    return wrapper


# ============================================================================
# RETRY DECORATOR
# ============================================================================

def retry_on_failure(
    max_attempts: int = 3,
    delay_seconds: float = 1.0,
    exceptions: tuple = (Exception,)
) -> Callable:
    """
    Decorador para reintentar en caso de fallo.
    
    CLEAN_CODE v3.0.1: Nombre que revela intención.
    SOLID SRP: Solo reintenta.
    SOLID OCP: Configurable.
    
    Args:
        max_attempts: Intentos máximos
        delay_seconds: Delay entre intentos
        exceptions: Tupla de excepciones a capturar
    
    Usage:
        @retry_on_failure(max_attempts=3, delay_seconds=2)
        def unstable_api_call():
            # Puede fallar
            pass
    
    Examples:
        >>> @retry_on_failure(max_attempts=2)
        ... def flaky_function():
        ...     import random
        ...     if random.random() < 0.5:
        ...         raise ValueError("Failed")
        ...     return "Success"
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                
                except exceptions as e:
                    last_exception = e
                    
                    logger.warning(
                        f"[RETRY] {func.__name__} attempt {attempt}/{max_attempts} failed: {e}"
                    )
                    
                    if attempt < max_attempts:
                        time.sleep(delay_seconds)
                    else:
                        logger.error(
                            f"[RETRY] {func.__name__} failed after {max_attempts} attempts"
                        )
            
            # Todos los intentos fallaron
            raise last_exception
        
        return wrapper
    
    return decorator


# ============================================================================
# CACHE DECORATOR
# ============================================================================

def cache_result(
    timeout: int = 300,
    key_prefix: Optional[str] = None
) -> Callable:
    """
    Decorador para cachear resultado de función.
    
    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID SRP: Solo cachea.
    
    Args:
        timeout: Timeout en segundos
        key_prefix: Prefijo para cache key
    
    Usage:
        @cache_result(timeout=600)
        def expensive_calculation(x):
            return x ** 2
    
    Examples:
        >>> @cache_result(timeout=60)
        ... def get_data(param):
        ...     return f"data-{param}"
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generar cache key
            cache_key = _generate_cache_key(func, args, kwargs, key_prefix)
            
            # Buscar en cache
            cached_result = cache.get(cache_key)
            
            if cached_result is not None:
                logger.debug(f"[CACHE] HIT - {cache_key}")
                return cached_result
            
            # Ejecutar función
            logger.debug(f"[CACHE] MISS - {cache_key}")
            result = func(*args, **kwargs)
            
            # Guardar en cache
            cache.set(cache_key, result, timeout)
            
            return result
        
        return wrapper
    
    return decorator


def _generate_cache_key(
    func: Callable,
    args: tuple,
    kwargs: dict,
    prefix: Optional[str] = None
) -> str:
    """
    Genera cache key.
    
    SOLID SRP: Solo genera key.
    DRY: Reutilizable.
    
    Args:
        func: Función
        args: Args
        kwargs: Kwargs
        prefix: Prefijo
    
    Returns:
        str: Cache key
    """
    import hashlib
    import json
    
    # Base: nombre función
    func_name = func.__name__
    
    # Serializar args y kwargs
    try:
        args_str = json.dumps(args, sort_keys=True)
        kwargs_str = json.dumps(kwargs, sort_keys=True)
    except TypeError:
        # Fallback: str()
        args_str = str(args)
        kwargs_str = str(kwargs)
    
    # Hash
    combined = f"{args_str}:{kwargs_str}"
    hash_key = hashlib.md5(combined.encode()).hexdigest()[:8]
    
    # Construir key
    if prefix:
        return f"{prefix}:{func_name}:{hash_key}"
    else:
        return f"cache:{func_name}:{hash_key}"


# ============================================================================
# PERMISSION DECORATOR
# ============================================================================

def require_permission(permission: str) -> Callable:
    """
    Decorador para requerir permiso.
    
    CLEAN_CODE v3.0.1: Nombre que revela intención.
    SOLID SRP: Solo verifica permiso.
    
    Args:
        permission: Permiso requerido
    
    Usage:
        @require_permission('reports.view')
        def get_report(user):
            return Report.objects.all()
    
    Raises:
        PermissionError: Si usuario no tiene permiso
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Buscar usuario en args o kwargs
            user = _find_user_in_arguments(args, kwargs)
            
            if user is None:
                raise ValueError("User not found in function arguments")
            
            # Verificar permiso
            from apps.access.services import AccessService
            
            if not AccessService.user_has_function(user, permission):
                raise PermissionError(
                    f"User does not have permission: {permission}"
                )
            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def _find_user_in_arguments(args: tuple, kwargs: dict) -> Any:
    """
    Busca usuario en argumentos.
    
    SOLID SRP: Solo busca usuario.
    DRY: Reutilizable.
    
    Args:
        args: Args
        kwargs: Kwargs
    
    Returns:
        User o None
    """
    # Buscar en kwargs
    if 'user' in kwargs:
        return kwargs['user']
    
    if 'request' in kwargs:
        return getattr(kwargs['request'], 'user', None)
    
    # Buscar en args
    for arg in args:
        # Duck typing: tiene is_authenticated?
        if hasattr(arg, 'is_authenticated'):
            return arg
        
        # Es un request?
        if hasattr(arg, 'user'):
            return arg.user
    
    return None


# ============================================================================
# TIMING DECORATOR
# ============================================================================

def measure_time(func: Callable) -> Callable:
    """
    Decorador para medir tiempo de ejecución.
    
    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID SRP: Solo mide tiempo.
    
    Retorna tupla (resultado, tiempo_segundos).
    
    Usage:
        @measure_time
        def slow_function():
            time.sleep(1)
            return "done"
        
        result, elapsed = slow_function()
    
    Examples:
        >>> @measure_time
        ... def add(a, b):
        ...     return a + b
        >>> result, time_taken = add(2, 3)
        >>> result
        5
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        result = func(*args, **kwargs)
        
        elapsed = time.time() - start_time
        
        return result, elapsed
    
    return wrapper


# ============================================================================
# DEPRECATED DECORATOR
# ============================================================================

def deprecated(message: str = "This function is deprecated") -> Callable:
    """
    Decorador para marcar función como deprecated.
    
    CLEAN_CODE v3.0.1: Nombre auto-documentado.
    SOLID SRP: Solo marca como deprecated.
    
    Args:
        message: Mensaje de deprecación
    
    Usage:
        @deprecated("Use new_function() instead")
        def old_function():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            import warnings
            
            warnings.warn(
                f"{func.__name__} is deprecated: {message}",
                category=DeprecationWarning,
                stacklevel=2
            )
            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


# ============================================================================
# RESUMEN DECORATORS
# 
# Total: 8 decoradores + 2 helpers privados
# 
# Decoradores:
#   [SUCCESS] @log_execution - Loggea ejecución completa
#   [SUCCESS] @log_duration - Loggea solo duración
#   [SUCCESS] @retry_on_failure - Reintenta en fallo
#   [SUCCESS] @cache_result - Cachea resultado
#   [SUCCESS] @require_permission - Requiere permiso RBAC
#   [SUCCESS] @measure_time - Mide tiempo, retorna tupla
#   [SUCCESS] @deprecated - Marca como deprecated
# 
# Helpers Privados (DRY):
#   [SUCCESS] _generate_cache_key()
#   [SUCCESS] _find_user_in_arguments()
# 
# Principios SOLID Aplicados:
#   [SUCCESS] SRP: Cada decorador una responsabilidad
#   [SUCCESS] DRY: Helpers privados reutilizables
#   [SUCCESS] OCP: retry_on_failure, cache_result configurables
#   [SUCCESS] Clean Naming: Nombres descriptivos
#   [SUCCESS] Type Hints: Callable, Optional
#   [SUCCESS] Functools @wraps: Preserva metadata
# ============================================================================
