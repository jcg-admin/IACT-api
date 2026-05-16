"""Shared helper functions."""
import hashlib
import os
import secrets
import uuid
from typing import Any, Dict, Iterable, List, TypeVar

from apps.utils.request import is_ajax_request  # noqa: F401 — re-exportado para compatibilidad


def generate_unique_filename(filename: str) -> str:
    """Generate a unique filename using UUID while preserving extension."""
    ext = os.path.splitext(filename)[1].lower()
    return f"{uuid.uuid4().hex}{ext}"


def avatar_upload_path(instance, filename: str) -> str:
    """Return upload path for user avatars."""
    unique_name = generate_unique_filename(filename)
    return f"profiles/{unique_name}"


def get_client_ip(request) -> str:
    """Extract client IP from request, respecting X-Forwarded-For."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    x_real_ip = request.META.get('HTTP_X_REAL_IP')
    if x_real_ip:
        return x_real_ip.strip()
    return request.META.get('REMOTE_ADDR', '')


def hash_sensitive_value(value: str) -> str:
    """Return SHA-256 hash of a sensitive value (for safe logging)."""
    return hashlib.sha256(value.encode()).hexdigest()[:16]


def get_user_agent(request) -> str:
    """Extract User-Agent string from request headers."""
    return request.META.get('HTTP_USER_AGENT', '')


# ---------------------------------------------------------------------------
# UUID y tokens
# ---------------------------------------------------------------------------

def generate_uuid() -> str:
    """Genera un UUID v4 como string."""
    return str(uuid.uuid4())


def generate_short_uuid(length: int = 8) -> str:
    """Genera un UUID corto de `length` caracteres hex."""
    return uuid.uuid4().hex[:length]


def generate_random_token(length: int = 32) -> str:
    """Genera un token seguro de `length` bytes como hex string."""
    return secrets.token_hex(length // 2)


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------

def hash_string(value: str, algorithm: str = 'sha256') -> str:
    """Retorna el hash hex de `value` usando el algoritmo indicado."""
    h = hashlib.new(algorithm)
    h.update(value.encode('utf-8'))
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Estructuras de datos
# ---------------------------------------------------------------------------

T = TypeVar('T')


def safe_get(obj: Dict, *keys, default: Any = None) -> Any:
    """
    Acceso seguro a un diccionario anidado.

    Ejemplo:
        safe_get({'a': {'b': 1}}, 'a', 'b')          -> 1
        safe_get({'a': 1}, 'b', default=0)             -> 0
        safe_get({'a': {'b': 1}}, 'a', 'c', default=0) -> 0
    """
    current = obj
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key, default)
        if current is default:
            return default
    return current


def merge_dicts(*dicts: Dict) -> Dict:
    """Fusiona N diccionarios. Las claves posteriores sobreescriben las anteriores."""
    result: Dict = {}
    for d in dicts:
        result.update(d)
    return result


def chunk_list(lst: List[T], chunk_size: int) -> List[List[T]]:
    """Divide `lst` en sublistas de tamaño `chunk_size`."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def flatten_list(lst: Iterable) -> List:
    """Aplana una lista de un nivel de profundidad."""
    result = []
    for item in lst:
        if isinstance(item, (list, tuple)):
            result.extend(item)
        else:
            result.append(item)
    return result


def unique_list(lst: List[T]) -> List[T]:
    """Elimina duplicados preservando el orden de aparición."""
    seen = set()
    result = []
    for item in lst:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


# ---------------------------------------------------------------------------
# Conversión de tipos
# ---------------------------------------------------------------------------

def str_to_bool(value: Any) -> bool:
    """
    Convierte un valor a bool. Acepta strings ('true', '1', 'yes', 'on').
    Strings no reconocidos retornan False.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in ('true', '1', 'yes', 'on'):
            return True
        return False
    return bool(value)


# ---------------------------------------------------------------------------
# Limpieza de diccionarios
# ---------------------------------------------------------------------------

def remove_none_values(d: Dict) -> Dict:
    """Retorna una copia del diccionario sin las claves con valor None."""
    return {k: v for k, v in d.items() if v is not None}


def remove_empty_strings(d: Dict) -> Dict:
    """Retorna una copia del diccionario sin las claves con valor ''."""
    return {k: v for k, v in d.items() if v != ''}
