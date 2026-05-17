"""
Constantes para authentication.

CLEAN_CODE v3.0.1: Nombres en UPPER_CASE.
SOLID OCP: Valores configurables centralizados.

CNST-005: Lockout configurado.
CNST-001: Security questions configuradas.
"""

# ============================================================================
# LOGIN & LOCKOUT
# ============================================================================

MAX_LOGIN_ATTEMPTS = 5
"""
Máximo de intentos fallidos antes del bloqueo.

CNST-005: 5 intentos fallidos.
"""

LOCKOUT_DURATION_MINUTES = 15
"""
Duración del bloqueo en minutos.

CNST-005: 15 minutos de bloqueo.
"""

LOCKOUT_WINDOW_MINUTES = 15
"""
Ventana de tiempo para contar intentos fallidos.

Los intentos fuera de esta ventana no se cuentan.
"""

# ============================================================================
# SECURITY QUESTIONS
# ============================================================================

SECURITY_QUESTIONS_REQUIRED = 5
"""
Número de preguntas que el usuario debe responder.

CNST-001: 5 preguntas obligatorias (NO email).
"""

SECURITY_QUESTIONS_POOL_MIN = 10
"""
Mínimo de preguntas en el pool disponible.

Debe haber al menos 10 preguntas activas.
"""

# ============================================================================
# PASSWORD
# ============================================================================

PASSWORD_MIN_LENGTH = 8
"""
Longitud mínima de contraseña.

CNST-005: Mínimo 8 caracteres.
"""

PASSWORD_MAX_LENGTH = 128
"""
Longitud máxima de contraseña.

Django limit: 128 caracteres.
"""

# ============================================================================
# SESSION
# ============================================================================

SESSION_TIMEOUT_SECONDS = 3600
"""
Timeout de sesión en segundos.

Default: 1 hora (3600 segundos).
"""

SESSION_COOKIE_AGE = 3600
"""
Edad de la cookie de sesión en segundos.

Debe coincidir con SESSION_TIMEOUT_SECONDS.
"""

SESSION_SAVE_EVERY_REQUEST = True
"""
Guardar sesión en cada request.

CNST-010: Sessions en PostgreSQL.
"""

# ============================================================================
# AUDIT
# ============================================================================

LOG_FAILED_ATTEMPTS = True
"""
Si se deben loguear intentos fallidos.

CNST-031: Auditoría completa de todos los intentos.
"""

LOG_SUCCESSFUL_LOGINS = True
"""
Si se deben loguear logins exitosos.

CNST-031: Auditoría completa.
"""

LOG_LOGOUTS = True
"""
Si se deben loguear logouts.

CNST-031: Auditoría de sesiones.
"""

# ============================================================================
# CACHE KEYS (OBSOLETO - CNST-010)
# ============================================================================
# NOTA: Estas constantes ya NO se usan.
# LockoutService ahora usa modelo LoginLockout en PostgreSQL.
# Removidas por corrección CNST-010 (NO cache permitido).
# Mantenidas como referencia histórica.

# CACHE_KEY_LOCKOUT = 'auth:lockout:{username}'
# CACHE_KEY_FAILED_ATTEMPTS = 'auth:failed_attempts:{username}'

# ============================================================================
# CNST-010 COMPLIANCE
# ============================================================================
# Sistema de lockout migrado de cache a PostgreSQL:
# - Model: LoginLockout
# - Fields: username, failed_attempts, locked_until
# - Persistente, sobrevive restart
# - Compatible multi-server
