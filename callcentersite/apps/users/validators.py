"""
Validadores para apps/users/.

CLEAN_CODE v3.0.1: Validadores específicos y reutilizables.
SOLID SRP: Cada validador una responsabilidad.

CNST-014: Validaciones estrictas en inputs.

FASE 2 PARTE 2: Solo validators ESPECÍFICOS de users (3 validators).

NOTA: 
- validate_email() y validate_phone_number() están en apps/utils/validators.py
- Aquí solo validators ESPECÍFICOS de users
"""

import re
from django.core.exceptions import ValidationError


def validate_username(value: str) -> None:
    """
    Valida username.
    
    Reglas:
    - Mínimo 3 caracteres
    - Máximo 150 caracteres
    - Solo alfanuméricos, guiones y underscores
    - No puede comenzar con número
    
    Args:
        value: Username a validar
        
    Raises:
        ValidationError: Si username inválido
        
    Example:
        validate_username('john_doe')  # [SUCCESS] OK
        validate_username('123user')   # [ERROR] ValidationError
    """
    if not value:
        raise ValidationError('Username es requerido')
    
    if len(value) < 3:
        raise ValidationError('Username debe tener al menos 3 caracteres')
    
    if len(value) > 150:
        raise ValidationError('Username no puede exceder 150 caracteres')
    
    # Solo alfanuméricos, guiones y underscores
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', value):
        raise ValidationError(
            'Username debe comenzar con letra y solo contener '
            'letras, números, guiones y underscores'
        )


def validate_avatar_file(file) -> None:
    """
    Valida archivo de avatar.
    
    Reglas:
    - Formatos permitidos: jpg, jpeg, png, gif
    - Tamaño máximo: 2MB
    
    Args:
        file: Archivo a validar
        
    Raises:
        ValidationError: Si archivo inválido
        
    Example:
        validate_avatar_file(uploaded_file)
    """
    if not file:
        return  # Avatar es opcional
    
    # Validar extensión
    allowed_extensions = ['jpg', 'jpeg', 'png', 'gif']
    file_extension = file.name.split('.')[-1].lower()
    
    if file_extension not in allowed_extensions:
        raise ValidationError(
            f'Formato de archivo no permitido. '
            f'Formatos aceptados: {", ".join(allowed_extensions)}'
        )
    
    # Validar tamaño (2MB = 2 * 1024 * 1024 bytes)
    max_size = 2 * 1024 * 1024
    if file.size > max_size:
        raise ValidationError(
            f'Archivo demasiado grande. Tamaño máximo: 2MB. '
            f'Tamaño actual: {file.size / (1024 * 1024):.2f}MB'
        )


def validate_password_strength(password: str) -> None:
    """
    Valida fortaleza de contraseña.
    
    Reglas:
    - Mínimo 8 caracteres
    - Al menos una mayúscula
    - Al menos una minúscula
    - Al menos un número
    - Al menos un carácter especial
    
    Args:
        password: Contraseña a validar
        
    Raises:
        ValidationError: Si contraseña débil
        
    Example:
        validate_password_strength('SecurePass123!')  # [SUCCESS] OK
        validate_password_strength('weak')            # [ERROR] ValidationError
    """
    if not password:
        raise ValidationError('Contraseña es requerida')
    
    if len(password) < 8:
        raise ValidationError('Contraseña debe tener al menos 8 caracteres')
    
    if not re.search(r'[A-Z]', password):
        raise ValidationError('Contraseña debe contener al menos una mayúscula')
    
    if not re.search(r'[a-z]', password):
        raise ValidationError('Contraseña debe contener al menos una minúscula')
    
    if not re.search(r'\d', password):
        raise ValidationError('Contraseña debe contener al menos un número')
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValidationError(
            'Contraseña debe contener al menos un carácter especial (!@#$%^&*...)'
        )


# ============================================================================
# RESUMEN VALIDATORS
# 
# Total: 3 validators específicos de users
# 
# Validators:
#   [SUCCESS] validate_username() - Username alfanumérico
#   [SUCCESS] validate_avatar_file() - Imágenes (jpg, png, gif, max 2MB)
#   [SUCCESS] validate_password_strength() - Password fuerte
# 
# ELIMINADO en FASE 2 PARTE 2:
#   [ERROR] validate_employee_id() - Campo removido del modelo User
# 
# NOTA - Validators en otros módulos:
#   📦 apps/utils/validators.py:
#      - validate_email() - Email genérico
#      - validate_phone_number() - Teléfonos México
#      - validate_rut() - RUT chileno (compatibilidad)
#      - validate_service_800() - Números 800
#      - validate_codigo_center() - Códigos de centro
#      - validate_date_range() - Rangos de fechas
# 
#   📦 apps/core/validators.py:
#      - PhoneValidator (clase) - Teléfonos corporativos
#      - EmailValidator (clase) - Emails corporativos
#      - NITValidator (clase) - RUT empresarial
#      - DateRangeValidator (clase) - Rangos de fechas
#      - PositiveIntegerValidator (clase) - Enteros positivos
# 
# Principios aplicados:
#   [SUCCESS] DRY: No duplicar código de core/utils
#   [SUCCESS] SRP: Cada validator una responsabilidad
#   [SUCCESS] CNST-014: Validaciones estrictas
#   [SUCCESS] FASE 2 PARTE 2: Arquitectura limpia
# ============================================================================
