"""
File utilities para apps/utils/.

CLEAN_CODE v3.0.1: Funciones auto-documentadas.
SOLID: SRP, DRY, OCP.
"""

import os
import mimetypes
from pathlib import Path
from typing import Optional, List


# ============================================================================
# FILE EXTENSION
# ============================================================================

def get_file_extension(filename: str) -> str:
    """
    Obtiene extensión de archivo.
    
    CLEAN_CODE v3.0.1: Nombre que revela intención.
    SOLID SRP: Solo obtiene extensión.
    
    Args:
        filename: Nombre archivo
    
    Returns:
        str: Extensión (sin punto, lowercase)
    
    Examples:
        >>> get_file_extension('document.pdf')
        'pdf'
        >>> get_file_extension('image.PNG')
        'png'
    """
    _, ext = os.path.splitext(filename)
    return ext.lower().lstrip('.')


def change_file_extension(filename: str, new_extension: str) -> str:
    """
    Cambia extensión de archivo.
    
    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID SRP: Solo cambia extensión.
    
    Args:
        filename: Nombre archivo
        new_extension: Nueva extensión
    
    Returns:
        str: Nombre con nueva extensión
    
    Examples:
        >>> change_file_extension('document.txt', 'pdf')
        'document.pdf'
    """
    base = os.path.splitext(filename)[0]
    new_ext = new_extension.lstrip('.')
    return f"{base}.{new_ext}"


# ============================================================================
# FILE SIZE
# ============================================================================

def get_file_size_bytes(filepath: str) -> int:
    """
    Obtiene tamaño de archivo en bytes.
    
    CLEAN_CODE v3.0.1: Nombre auto-documentado.
    SOLID SRP: Solo obtiene tamaño.
    
    Args:
        filepath: Ruta archivo
    
    Returns:
        int: Tamaño en bytes
    
    Examples:
        >>> get_file_size_bytes('/tmp/file.txt')
        1024
    """
    return os.path.getsize(filepath)


def format_file_size(size_bytes: int, precision: int = 1) -> str:
    """
    Formatea tamaño de archivo.
    
    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID SRP: Solo formatea.
    DRY: Reutiliza de formatters (pero aquí también para file_utils)
    
    Args:
        size_bytes: Tamaño en bytes
        precision: Decimales
    
    Returns:
        str: Tamaño formateado
    
    Examples:
        >>> format_file_size(1024)
        '1.0 KB'
        >>> format_file_size(1048576, precision=2)
        '1.00 MB'
    """
    # DRY: Helper privado
    return _format_bytes(size_bytes, precision)


def _format_bytes(size_bytes: int, precision: int = 1) -> str:
    """
    Formatea bytes.
    
    SOLID SRP: Solo formatea bytes.
    DRY: Reutilizable.
    
    Args:
        size_bytes: Bytes
        precision: Decimales
    
    Returns:
        str: Formateado
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.{precision}f} {unit}"
        size_bytes /= 1024.0
    
    return f"{size_bytes:.{precision}f} PB"


# ============================================================================
# FILE TYPE VALIDATION
# ============================================================================

def validate_file_type(
    filename: str,
    allowed_extensions: List[str]
) -> bool:
    """
    Valida tipo de archivo por extensión.
    
    CLEAN_CODE v3.0.1: Nombre que revela intención.
    SOLID SRP: Solo valida extensión.
    
    Args:
        filename: Nombre archivo
        allowed_extensions: Extensiones permitidas
    
    Returns:
        bool: True si válido
    
    Examples:
        >>> validate_file_type('doc.pdf', ['pdf', 'docx'])
        True
        >>> validate_file_type('image.jpg', ['pdf'])
        False
    """
    ext = get_file_extension(filename)
    
    # Normalizar allowed_extensions
    normalized_allowed = [e.lower().lstrip('.') for e in allowed_extensions]
    
    return ext in normalized_allowed


def is_image_file(filename: str) -> bool:
    """
    Verifica si es archivo de imagen.
    
    CLEAN_CODE v3.0.1: Nombre auto-documentado.
    SOLID SRP: Solo verifica si es imagen.
    
    Args:
        filename: Nombre archivo
    
    Returns:
        bool: True si es imagen
    
    Examples:
        >>> is_image_file('photo.jpg')
        True
        >>> is_image_file('document.pdf')
        False
    """
    # DRY: Extensiones centralizadas
    image_extensions = _get_image_extensions()
    
    return validate_file_type(filename, image_extensions)


def is_document_file(filename: str) -> bool:
    """
    Verifica si es archivo de documento.
    
    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID SRP: Solo verifica documento.
    
    Args:
        filename: Nombre archivo
    
    Returns:
        bool: True si es documento
    
    Examples:
        >>> is_document_file('report.pdf')
        True
        >>> is_document_file('image.jpg')
        False
    """
    # DRY: Extensiones centralizadas
    document_extensions = _get_document_extensions()
    
    return validate_file_type(filename, document_extensions)


def _get_image_extensions() -> List[str]:
    """
    Extensiones de imagen.
    
    SOLID SRP: Solo provee lista.
    DRY: Centralizado.
    SOLID OCP: Fácil agregar más.
    
    Returns:
        list: Extensiones
    """
    return ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg']


def _get_document_extensions() -> List[str]:
    """
    Extensiones de documento.
    
    SOLID SRP: Solo provee lista.
    DRY: Centralizado.
    
    Returns:
        list: Extensiones
    """
    return ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'csv']


# ============================================================================
# MIME TYPE
# ============================================================================

def get_mime_type(filename: str) -> Optional[str]:
    """
    Obtiene MIME type de archivo.
    
    CLEAN_CODE v3.0.1: Nombre que revela intención.
    SOLID SRP: Solo obtiene MIME type.
    
    Args:
        filename: Nombre archivo
    
    Returns:
        str: MIME type o None
    
    Examples:
        >>> get_mime_type('document.pdf')
        'application/pdf'
        >>> get_mime_type('image.png')
        'image/png'
    """
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type


# ============================================================================
# FILENAME SANITIZATION
# ============================================================================

def sanitize_filename(filename: str, replace_spaces: bool = True) -> str:
    """
    Sanitiza nombre de archivo.
    
    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID SRP: Solo sanitiza.
    
    Remueve caracteres peligrosos/inválidos.
    
    Args:
        filename: Nombre archivo
        replace_spaces: Reemplazar espacios con guiones
    
    Returns:
        str: Nombre sanitizado
    
    Examples:
        >>> sanitize_filename('My Document!.pdf')
        'My-Document.pdf'
        >>> sanitize_filename('file/name?.txt')
        'filename.txt'
    """
    # Separar nombre y extensión
    name, ext = os.path.splitext(filename)
    
    # Remover caracteres peligrosos
    safe_name = _remove_unsafe_chars(name)
    
    # Reemplazar espacios
    if replace_spaces:
        safe_name = safe_name.replace(' ', '-')
    
    # Remover guiones/puntos múltiples
    safe_name = _clean_multiple_chars(safe_name, ['-', '.', '_'])
    
    # Trim guiones al inicio/fin
    safe_name = safe_name.strip('-._')
    
    return f"{safe_name}{ext.lower()}"


def _remove_unsafe_chars(text: str) -> str:
    """
    Remueve caracteres inseguros.
    
    SOLID SRP: Solo remueve.
    DRY: Reutilizable.
    
    Args:
        text: Texto
    
    Returns:
        str: Texto seguro
    """
    import re
    # Permitir: letras, números, espacios, guiones, puntos, underscores
    return re.sub(r'[^a-zA-Z0-9\s\-\._]', '', text)


def _clean_multiple_chars(text: str, chars: List[str]) -> str:
    """
    Limpia caracteres múltiples.
    
    SOLID SRP: Solo limpia repetidos.
    DRY: Reutilizable.
    
    Args:
        text: Texto
        chars: Caracteres a limpiar
    
    Returns:
        str: Texto limpio
    """
    import re
    for char in chars:
        pattern = re.escape(char) + r'+'
        text = re.sub(pattern, char, text)
    
    return text


# ============================================================================
# PATH UTILITIES
# ============================================================================

def ensure_directory_exists(directory: str) -> None:
    """
    Asegura que directorio existe.
    
    CLEAN_CODE v3.0.1: Nombre que revela intención.
    SOLID SRP: Solo crea directorio.
    
    Args:
        directory: Ruta directorio
    
    Examples:
        >>> ensure_directory_exists('/tmp/mydir')
    """
    Path(directory).mkdir(parents=True, exist_ok=True)


def get_unique_filename(directory: str, filename: str) -> str:
    """
    Genera nombre único de archivo.
    
    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID SRP: Solo genera nombre único.
    
    Si archivo existe, agrega contador (1), (2), etc.
    
    Args:
        directory: Directorio
        filename: Nombre archivo
    
    Returns:
        str: Nombre único
    
    Examples:
        >>> get_unique_filename('/tmp', 'file.txt')
        'file.txt'  # Si no existe
        >>> get_unique_filename('/tmp', 'file.txt')
        'file (1).txt'  # Si existe
    """
    filepath = os.path.join(directory, filename)
    
    if not os.path.exists(filepath):
        return filename
    
    # Separar nombre y extensión
    name, ext = os.path.splitext(filename)
    
    # Buscar contador disponible
    counter = 1
    while True:
        new_filename = f"{name} ({counter}){ext}"
        new_filepath = os.path.join(directory, new_filename)
        
        if not os.path.exists(new_filepath):
            return new_filename
        
        counter += 1
        
        # Seguridad: limitar búsqueda
        if counter > 1000:
            raise ValueError("Cannot find unique filename")


# ============================================================================
# RESUMEN FILE_UTILS
# 
# Total: 12 funciones públicas + 5 helpers privados
# 
# Funciones Públicas:
#   [SUCCESS] get_file_extension()
#   [SUCCESS] change_file_extension()
#   [SUCCESS] get_file_size_bytes()
#   [SUCCESS] format_file_size()
#   [SUCCESS] validate_file_type()
#   [SUCCESS] is_image_file()
#   [SUCCESS] is_document_file()
#   [SUCCESS] get_mime_type()
#   [SUCCESS] sanitize_filename()
#   [SUCCESS] ensure_directory_exists()
#   [SUCCESS] get_unique_filename()
# 
# Helpers Privados (DRY):
#   [SUCCESS] _format_bytes()
#   [SUCCESS] _get_image_extensions()
#   [SUCCESS] _get_document_extensions()
#   [SUCCESS] _remove_unsafe_chars()
#   [SUCCESS] _clean_multiple_chars()
# 
# Principios SOLID Aplicados:
#   [SUCCESS] SRP: Cada función una responsabilidad
#   [SUCCESS] DRY: Helpers privados reutilizables
#   [SUCCESS] OCP: Extensiones centralizadas, fácil agregar más
#   [SUCCESS] Clean Naming: Nombres descriptivos
#   [SUCCESS] Type Hints: Todas las funciones
# ============================================================================


def calculate_file_hash(file) -> str:
    """
    Calcula hash SHA256 de un archivo.
    
    Args:
        file: UploadedFile o archivo similar
    
    Returns:
        str: Hash SHA256 en hexadecimal
    
    Example:
        >>> from django.core.files.uploadedfile import SimpleUploadedFile
        >>> file = SimpleUploadedFile("test.txt", b"content")
        >>> hash_val = calculate_file_hash(file)
        >>> print(len(hash_val))
        64
    """
    import hashlib
    
    # Reset file pointer
    file.seek(0)
    
    # Calculate hash
    sha256 = hashlib.sha256()
    for chunk in file.chunks():
        sha256.update(chunk)
    
    # Reset file pointer again
    file.seek(0)
    
    return sha256.hexdigest()
