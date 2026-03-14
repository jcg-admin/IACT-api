"""
Constants para apps/users/.

CLEAN_CODE v3.0.1: UPPER_SNAKE_CASE.
FASE 2 PARTE 2: Correcciones arquitectónicas
"""

# Password policies (CNST-038)
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
PASSWORD_RESET_TIMEOUT = 86400  # 24 horas
PASSWORD_HISTORY_COUNT = 5  # No reutilizar últimas 5

# Login
MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_DURATION = 900  # 15 minutos
SESSION_TIMEOUT = 3600  # 1 hora

# Avatar
AVATAR_MAX_SIZE_MB = 2  # Reducido de 5 a 2 MB (FASE 2 PARTE 1)
AVATAR_ALLOWED_FORMATS = ['jpg', 'jpeg', 'png', 'gif']
DEFAULT_AVATAR = 'avatars/default.png'

# Email verification
EMAIL_VERIFICATION_TIMEOUT = 86400  # 24 horas

# User status
USER_STATUS_ACTIVE = 'active'
USER_STATUS_INACTIVE = 'inactive'
USER_STATUS_LOCKED = 'locked'
USER_STATUS_PENDING = 'pending'

# ============================================================================
# RBAC PERMISSIONS v6.0.0 (Django Namespaces)
# ============================================================================

# Users permissions
PERM_USERS_VIEW = 'users.view'
PERM_USERS_CREATE = 'users.create'
PERM_USERS_EDIT = 'users.edit'
PERM_USERS_DELETE = 'users.delete'

# Sessions permissions
PERM_SESSIONS_VIEW = 'sessions.view'
PERM_SESSIONS_MANAGE = 'sessions.manage'

# Authentication permissions
PERM_AUTH_LOGIN = 'authentication.login'
PERM_AUTH_LOGOUT = 'authentication.logout'
PERM_AUTH_CHANGE_PASSWORD = 'authentication.change_password'
PERM_AUTH_RECOVER_PASSWORD = 'authentication.recover_password'

# ============================================================================
# DEPRECATED: RBAC Codes (usar namespaces arriba)
# ============================================================================

# Funciones RBAC (referencia legacy - NO USAR)
# DEPRECADO v6.0.0: Usar PERM_* arriba
USR_VIEW = 'USR_VIEW'       # -> PERM_USERS_VIEW
USR_EDIT = 'USR_EDIT'       # -> PERM_USERS_EDIT
USR_DELETE = 'USR_DELETE'   # -> PERM_USERS_DELETE
USR_PERMS = 'USR_PERMS'     # -> PERM_USERS_MANAGE




# ============================================================================
# CHOICES (FASE 2 PARTE 1)
# ============================================================================

USER_STATUS_CHOICES = [
    ('active', 'Activo'),
    ('inactive', 'Inactivo'),
    ('locked', 'Bloqueado'),
    ('pending', 'Pendiente'),
]

DEPARTMENT_CHOICES = [
    ('IT', 'Tecnología (IT)'),
    ('HR', 'Recursos Humanos'),
    ('SALES', 'Ventas'),
    ('MARKETING', 'Marketing'),
    ('FINANCE', 'Finanzas'),
    ('OPERATIONS', 'Operaciones'),
    ('CUSTOMER_SERVICE', 'Servicio al Cliente'),
    ('ADMIN', 'Administración'),
]

POSITION_CHOICES = [
    ('CEO', 'CEO'),
    ('CTO', 'CTO'),
    ('CFO', 'CFO'),
    ('MANAGER', 'Manager'),
    ('SUPERVISOR', 'Supervisor'),
    ('TEAM_LEAD', 'Team Lead'),
    ('SENIOR_DEV', 'Senior Developer'),
    ('DEVELOPER', 'Developer'),
    ('JUNIOR_DEV', 'Junior Developer'),
    ('ANALYST', 'Analyst'),
    ('SPECIALIST', 'Specialist'),
    ('COORDINATOR', 'Coordinator'),
    ('ASSISTANT', 'Assistant'),
    ('INTERN', 'Intern'),
]

# ============================================================================
# NOTAS FASE 2 PARTE 2 - CORRECCIONES ARQUITECTÓNICAS
# ============================================================================

# employee_id: ELIMINADO
# - Campo removido del modelo User
# - No es necesario para el sistema
# - Usar username como identificador principal

# theme y timezone: ELIMINADOS de UserSettings
# - Configuración global del sistema (no por usuario)
# - theme: Configurado en sistema
# - timezone: America/Mexico_City (configuración del sistema)

# email_notifications: ELIMINADO de UserSettings
# - Reemplazado por sistema de alertas internas
# - Usar notifications_enabled en UserSettings

# Control de acceso:
# - SOLO UserFunctionAssignment (funciones atómicas)
# - SOLO UserModuleAccess (módulos jerárquicos)
# - UserServiceAccess: OBSOLETO (marcar para eliminación)
