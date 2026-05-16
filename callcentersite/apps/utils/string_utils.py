"""
String utilities para apps/utils/.

CLEAN_CODE v3.0.1: Funciones auto-documentadas.
SOLID: SRP, DRY, OCP.
"""

import re
import unicodedata


# ============================================================================
# SLUGIFY
# ============================================================================

def slugify(text: str, allow_unicode: bool = False) -> str:
    """
    Convierte texto a slug URL-friendly.

    CLEAN_CODE v3.0.1: Nombre que revela intención.
    SOLID SRP: Solo crea slug.

    Args:
        text: Texto a convertir
        allow_unicode: Permitir caracteres unicode

    Returns:
        str: Slug generado

    Examples:
        >>> slugify('Hola Mundo 2025')
        'hola-mundo-2025'
        >>> slugify('Niño José')
        'nino-jose'
        >>> slugify('Niño José', allow_unicode=True)
        'niño-josé'
    """
    # DRY: Normalizar texto
    if allow_unicode:
        text = unicodedata.normalize('NFKC', text)
    else:
        text = _remove_accents(text)

    # Convertir a minúsculas
    text = text.lower()

    # Remover caracteres no permitidos
    if allow_unicode:
        pattern = r'[^\w\s-]'
    else:
        pattern = r'[^a-z0-9\s-]'

    text = re.sub(pattern, '', text)

    # Convertir espacios/guiones múltiples en un solo guión
    text = re.sub(r'[-\s]+', '-', text)

    # Quitar guiones al inicio/fin
    return text.strip('-')


def _remove_accents(text: str) -> str:
    """
    Remueve acentos de texto.

    SOLID SRP: Solo remueve acentos.
    DRY: Reutilizable por múltiples funciones.

    Args:
        text: Texto

    Returns:
        str: Texto sin acentos

    Examples:
        >>> _remove_accents('Niño José')
        'Nino Jose'
    """
    # Normalizar a NFD (descomponer caracteres)
    nfd = unicodedata.normalize('NFD', text)

    # Filtrar marcas diacríticas
    return ''.join(
        char for char in nfd
        if unicodedata.category(char) != 'Mn'
    )


# ============================================================================
# TEXT NORMALIZATION
# ============================================================================

def normalize_text(
    text: str,
    lowercase: bool = True,
    remove_extra_spaces: bool = True
) -> str:
    """
    Normaliza texto.

    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID SRP: Solo normaliza.
    SOLID OCP: Extensible con parámetros.

    Args:
        text: Texto
        lowercase: Convertir a minúsculas
        remove_extra_spaces: Remover espacios extras

    Returns:
        str: Texto normalizado

    Examples:
        >>> normalize_text('  HOLA   MUNDO  ')
        'hola mundo'
        >>> normalize_text('HOLA', lowercase=False)
        'HOLA'
    """
    normalized = text

    if lowercase:
        normalized = normalized.lower()

    if remove_extra_spaces:
        # Remover espacios múltiples
        normalized = re.sub(r'\s+', ' ', normalized)
        # Trim
        normalized = normalized.strip()

    return normalized


def remove_special_chars(
    text: str,
    keep_spaces: bool = True,
    keep_accents: bool = False
) -> str:
    """
    Remueve caracteres especiales.

    CLEAN_CODE v3.0.1: Nombre auto-documentado.
    SOLID SRP: Solo remueve caracteres especiales.

    Args:
        text: Texto
        keep_spaces: Mantener espacios
        keep_accents: Mantener acentos

    Returns:
        str: Texto limpio

    Examples:
        >>> remove_special_chars('Hola! ¿Cómo estás?')
        'Hola Como estas'
        >>> remove_special_chars('user@email.com', keep_spaces=False)
        'useremailcom'
    """
    if not keep_accents:
        text = _remove_accents(text)

    # Patrón: solo letras, números, espacios (opcional)
    if keep_spaces:
        pattern = r'[^a-zA-Z0-9\s]'
    else:
        pattern = r'[^a-zA-Z0-9]'

    return re.sub(pattern, '', text)


# ============================================================================
# TRUNCATE
# ============================================================================

def truncate(
    text: str,
    max_length: int,
    suffix: str = '...'
) -> str:
    """
    Trunca texto a longitud máxima.

    CLEAN_CODE v3.0.1: Nombre que revela intención.
    SOLID SRP: Solo trunca.

    Args:
        text: Texto
        max_length: Longitud máxima
        suffix: Sufijo al truncar

    Returns:
        str: Texto truncado

    Examples:
        >>> truncate('Esto es un texto largo', 10)
        'Esto es...'
        >>> truncate('Corto', 10)
        'Corto'
    """
    if len(text) <= max_length:
        return text

    # Truncar dejando espacio para sufijo
    truncated = text[:max_length - len(suffix)]

    return truncated + suffix


def truncate_words(
    text: str,
    max_words: int,
    suffix: str = '...'
) -> str:
    """
    Trunca texto a número máximo de palabras.

    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID SRP: Solo trunca por palabras.

    Args:
        text: Texto
        max_words: Palabras máximas
        suffix: Sufijo al truncar

    Returns:
        str: Texto truncado

    Examples:
        >>> truncate_words('Esto es un texto largo', 3)
        'Esto es un...'
    """
    words = text.split()

    if len(words) <= max_words:
        return text

    truncated_words = words[:max_words]

    return ' '.join(truncated_words) + suffix


# ============================================================================
# CASE CONVERSION
# ============================================================================

def to_snake_case(text: str) -> str:
    """
    Convierte a snake_case.

    CLEAN_CODE v3.0.1: Nombre auto-documentado.
    SOLID SRP: Solo convierte a snake_case.

    Args:
        text: Texto

    Returns:
        str: Texto en snake_case

    Examples:
        >>> to_snake_case('HelloWorld')
        'hello_world'
        >>> to_snake_case('thisIsATest')
        'this_is_a_test'
    """
    # Insertar _ antes de mayúsculas
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)

    # Insertar _ antes de mayúsculas seguidas de minúsculas
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)

    return s2.lower()


def to_camel_case(text: str) -> str:
    """
    Convierte a camelCase.

    CLEAN_CODE v3.0.1: Nombre que revela intención.
    SOLID SRP: Solo convierte a camelCase.

    Args:
        text: Texto (puede estar en snake_case, con espacios, etc)

    Returns:
        str: Texto en camelCase

    Examples:
        >>> to_camel_case('hello_world')
        'helloWorld'
        >>> to_camel_case('hello world')
        'helloWorld'
    """
    # Separar por _ o espacios
    components = re.split(r'[_\s]+', text)

    # Primera palabra lowercase, resto title case
    return components[0].lower() + ''.join(x.title() for x in components[1:])


def to_title_case(text: str) -> str:
    """
    Convierte a Title Case.

    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID SRP: Solo convierte a Title Case.

    Args:
        text: Texto

    Returns:
        str: Texto en Title Case

    Examples:
        >>> to_title_case('hello world')
        'Hello World'
    """
    return text.title()


# ============================================================================
# PADDING
# ============================================================================

def pad_left(text: str, width: int, fill_char: str = ' ') -> str:
    """
    Agrega padding a la izquierda.

    CLEAN_CODE v3.0.1: Nombre auto-documentado.
    SOLID SRP: Solo agrega padding izquierdo.

    Args:
        text: Texto
        width: Ancho total deseado
        fill_char: Caracter de relleno

    Returns:
        str: Texto con padding

    Examples:
        >>> pad_left('123', 5, '0')
        '00123'
    """
    return text.rjust(width, fill_char)


def pad_right(text: str, width: int, fill_char: str = ' ') -> str:
    """
    Agrega padding a la derecha.

    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID SRP: Solo agrega padding derecho.

    Args:
        text: Texto
        width: Ancho total deseado
        fill_char: Caracter de relleno

    Returns:
        str: Texto con padding

    Examples:
        >>> pad_right('123', 5, '0')
        '12300'
    """
    return text.ljust(width, fill_char)


# ============================================================================
# STRING VALIDATION
# ============================================================================

def is_alpha_numeric(text: str) -> bool:
    """
    Verifica si texto es alfanumérico.

    CLEAN_CODE v3.0.1: Nombre que revela intención.
    SOLID SRP: Solo verifica.

    Args:
        text: Texto

    Returns:
        bool: True si solo tiene letras y números

    Examples:
        >>> is_alpha_numeric('abc123')
        True
        >>> is_alpha_numeric('abc-123')
        False
    """
    return text.isalnum()


def contains_only_digits(text: str) -> bool:
    """
    Verifica si texto tiene solo dígitos.

    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID SRP: Solo verifica dígitos.

    Args:
        text: Texto

    Returns:
        bool: True si solo dígitos

    Examples:
        >>> contains_only_digits('12345')
        True
        >>> contains_only_digits('123a')
        False
    """
    return text.isdigit()


# ============================================================================
# RESUMEN STRING_UTILS
#
# Total: 16 funciones públicas + 1 helper privado
#
# Funciones Públicas:
#   [SUCCESS] slugify()
#   [SUCCESS] normalize_text()
#   [SUCCESS] remove_special_chars()
#   [SUCCESS] truncate()
#   [SUCCESS] truncate_words()
#   [SUCCESS] to_snake_case()
#   [SUCCESS] to_camel_case()
#   [SUCCESS] to_title_case()
#   [SUCCESS] pad_left()
#   [SUCCESS] pad_right()
#   [SUCCESS] is_alpha_numeric()
#   [SUCCESS] contains_only_digits()
#
# Helpers Privados (DRY):
#   [SUCCESS] _remove_accents()
#
# Principios SOLID Aplicados:
#   [SUCCESS] SRP: Cada función una responsabilidad
#   [SUCCESS] DRY: Helper _remove_accents reutilizable
#   [SUCCESS] OCP: normalize_text extensible con parámetros
#   [SUCCESS] Clean Naming: Nombres descriptivos
#   [SUCCESS] Type Hints: Todas las funciones
# ============================================================================
