"""
Constantes del proyecto.

Centraliza valores constantes usados en múltiples apps.

CLEAN_CODE v3.0.1: Nombres auto-documentados.
"""

# ============================================================================
# RESTRICCIONES DEL PROYECTO (CNST)
# ============================================================================

# CNST-007: Export máximo 100K rows
MAX_EXPORT_ROWS = 100000

# CNST-010: Session cleanup (días)
SESSION_CLEANUP_DAYS = 90


# ============================================================================
# LÍMITES DE SISTEMA
# ============================================================================

# Tamaños de archivo
MAX_FILE_SIZE_MB = 50  # Máximo para uploads
MAX_REPORT_FILE_SIZE_MB = 100  # Máximo para reportes generados

# Paginación
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 1000

# Cache TTL (segundos)
CACHE_TTL_SHORT = 300  # 5 minutos
CACHE_TTL_MEDIUM = 1800  # 30 minutos
CACHE_TTL_LONG = 3600  # 1 hora
CACHE_TTL_DAILY = 86400  # 24 horas


# ============================================================================
# TRIMESTRES
# ============================================================================

QUARTERS = {
    1: 'Q1',
    2: 'Q2',
    3: 'Q3',
    4: 'Q4',
}

QUARTER_MONTHS = {
    1: [1, 2, 3],   # Q1: Enero-Marzo
    2: [4, 5, 6],   # Q2: Abril-Junio
    3: [7, 8, 9],   # Q3: Julio-Septiembre
    4: [10, 11, 12],  # Q4: Octubre-Diciembre
}

# Nombres de trimestres en español
QUARTER_NAMES_ES = {
    1: 'Primer Trimestre',
    2: 'Segundo Trimestre',
    3: 'Tercer Trimestre',
    4: 'Cuarto Trimestre',
}


# ============================================================================
# MESES
# ============================================================================

MONTH_NAMES_ES = {
    1: 'Enero',
    2: 'Febrero',
    3: 'Marzo',
    4: 'Abril',
    5: 'Mayo',
    6: 'Junio',
    7: 'Julio',
    8: 'Agosto',
    9: 'Septiembre',
    10: 'Octubre',
    11: 'Noviembre',
    12: 'Diciembre',
}

MONTH_ABBR_ES = {
    1: 'Ene',
    2: 'Feb',
    3: 'Mar',
    4: 'Abr',
    5: 'May',
    6: 'Jun',
    7: 'Jul',
    8: 'Ago',
    9: 'Sep',
    10: 'Oct',
    11: 'Nov',
    12: 'Dic',
}


# ============================================================================
# FORMATOS
# ============================================================================

# Formatos de fecha
DATE_FORMAT = '%Y-%m-%d'
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
DATETIME_FORMAT_DISPLAY = '%d/%m/%Y %H:%M'
DATE_FORMAT_DISPLAY = '%d/%m/%Y'

# Formatos de export
EXPORT_FORMATS = ['xlsx', 'csv', 'pdf']

# Tipos de reporte
REPORT_TYPES = {
    'quarterly': 'Reporte Trimestral',
    'transfer': 'Reporte de Transferencias',
    'abandoned': 'Reporte de Abandonos',
    'client': 'Reporte por Cliente',
    'custom': 'Reporte Personalizado',
}


# ============================================================================
# STATUS / ESTADOS
# ============================================================================

# Estados de ETL Job
ETL_STATUS_PENDING = 'PENDING'
ETL_STATUS_RUNNING = 'RUNNING'
ETL_STATUS_SUCCESS = 'SUCCESS'
ETL_STATUS_FAILED = 'FAILED'

ETL_STATUS_CHOICES = [
    (ETL_STATUS_PENDING, 'Pendiente'),
    (ETL_STATUS_RUNNING, 'En Ejecución'),
    (ETL_STATUS_SUCCESS, 'Exitoso'),
    (ETL_STATUS_FAILED, 'Fallido'),
]

# Estados de Report Execution
REPORT_STATUS_PENDING = 'PENDING'
REPORT_STATUS_RUNNING = 'RUNNING'
REPORT_STATUS_SUCCESS = 'SUCCESS'
REPORT_STATUS_FAILED = 'FAILED'

REPORT_STATUS_CHOICES = [
    (REPORT_STATUS_PENDING, 'Pendiente'),
    (REPORT_STATUS_RUNNING, 'Generando'),
    (REPORT_STATUS_SUCCESS, 'Completado'),
    (REPORT_STATUS_FAILED, 'Fallido'),
]

# Estados de Alerta
ALERT_SEVERITY_LOW = 'LOW'
ALERT_SEVERITY_MEDIUM = 'MEDIUM'
ALERT_SEVERITY_HIGH = 'HIGH'
ALERT_SEVERITY_CRITICAL = 'CRITICAL'

ALERT_SEVERITY_CHOICES = [
    (ALERT_SEVERITY_LOW, 'Baja'),
    (ALERT_SEVERITY_MEDIUM, 'Media'),
    (ALERT_SEVERITY_HIGH, 'Alta'),
    (ALERT_SEVERITY_CRITICAL, 'Crítica'),
]


# ============================================================================
# RANGOS Y UMBRALES
# ============================================================================

# Umbral de abandono (15%)
ABANDONMENT_THRESHOLD = 0.15

# Umbral de tiempo de espera (segundos)
WAIT_TIME_THRESHOLD_SECONDS = 120

# Rango de años válidos
MIN_YEAR = 2000
MAX_YEAR = 2100

# Rango de horas (0-23)
MIN_HOUR = 0
MAX_HOUR = 23


# ============================================================================
# TIMEZONE
# ============================================================================

# Timezone del proyecto
DEFAULT_TIMEZONE = 'America/Santiago'


# ============================================================================
# PERMISOS / RBAC
# ============================================================================

# Tipos de función en RBAC
FUNCTION_TYPE_CREATE = 'CREATE'
FUNCTION_TYPE_VIEW = 'VIEW'
FUNCTION_TYPE_EDIT = 'EDIT'
FUNCTION_TYPE_DELETE = 'DELETE'

FUNCTION_TYPE_CHOICES = [
    (FUNCTION_TYPE_CREATE, 'Crear'),
    (FUNCTION_TYPE_VIEW, 'Ver'),
    (FUNCTION_TYPE_EDIT, 'Editar'),
    (FUNCTION_TYPE_DELETE, 'Eliminar'),
]


# ============================================================================
# AUDIT LOG
# ============================================================================

# Acciones de auditoría
AUDIT_ACTION_CREATE = 'CREATE'
AUDIT_ACTION_UPDATE = 'UPDATE'
AUDIT_ACTION_DELETE = 'DELETE'
AUDIT_ACTION_VIEW = 'VIEW'
AUDIT_ACTION_EXPORT = 'EXPORT'
AUDIT_ACTION_LOGIN = 'LOGIN'
AUDIT_ACTION_LOGOUT = 'LOGOUT'
AUDIT_ACTION_ACCESS_DENIED = 'ACCESS_DENIED'

AUDIT_ACTION_CHOICES = [
    (AUDIT_ACTION_CREATE, 'Crear'),
    (AUDIT_ACTION_UPDATE, 'Actualizar'),
    (AUDIT_ACTION_DELETE, 'Eliminar'),
    (AUDIT_ACTION_VIEW, 'Ver'),
    (AUDIT_ACTION_EXPORT, 'Exportar'),
    (AUDIT_ACTION_LOGIN, 'Inicio de Sesión'),
    (AUDIT_ACTION_LOGOUT, 'Cierre de Sesión'),
    (AUDIT_ACTION_ACCESS_DENIED, 'Acceso Denegado'),
]


# ============================================================================
# CACHE KEYS (prefijos)
# ============================================================================

CACHE_KEY_USER_SERVICES = 'user_services_{user_id}'
CACHE_KEY_USER_FUNCTIONS = 'user_functions_{user_id}'
CACHE_KEY_QUARTERLY_REPORT = 'quarterly_report_{year}_{quarter}'
CACHE_KEY_DASHBOARD_DATA = 'dashboard_data_{user_id}'


# ============================================================================
# SCHEDULER (APScheduler)
# ============================================================================

# CNST-013: APScheduler (NO Celery)

# Job IDs
SCHEDULER_JOB_CLEANUP_SESSIONS = 'cleanup_sessions'
SCHEDULER_JOB_ETL_MONITOR = 'etl_monitor'
SCHEDULER_JOB_HEALTH_CHECK = 'health_check'
SCHEDULER_JOB_QUARTERLY_ETL = 'quarterly_report_etl'

# Intervalos (segundos)
SCHEDULER_INTERVAL_HEALTH_CHECK = 300  # 5 minutos
SCHEDULER_INTERVAL_ETL_MONITOR = 21600  # 6 horas


# ============================================================================
# ERROR MESSAGES
# ============================================================================

ERROR_MSG_UNAUTHORIZED = 'No tiene permisos para realizar esta acción.'
ERROR_MSG_NOT_FOUND = 'Recurso no encontrado.'
ERROR_MSG_INVALID_DATA = 'Datos inválidos.'
ERROR_MSG_EXPORT_LIMIT = f'Export limitado a {MAX_EXPORT_ROWS:,} filas.'
ERROR_MSG_SERVICE_ACCESS_DENIED = 'No tiene acceso a este servicio.'


# ============================================================================
# SUCCESS MESSAGES
# ============================================================================

SUCCESS_MSG_CREATED = 'Creado exitosamente.'
SUCCESS_MSG_UPDATED = 'Actualizado exitosamente.'
SUCCESS_MSG_DELETED = 'Eliminado exitosamente.'
SUCCESS_MSG_EXPORT_STARTED = 'Export iniciado. Recibirá notificación al completar.'


# ============================================================================
# TOTAL CONSTANTES: 100+
# 
# Categorías:
#   - Restricciones CNST (2)
#   - Límites del Sistema (8)
#   - Trimestres (3 dicts)
#   - Meses (2 dicts)
#   - Formatos (5)
#   - Status/Estados (15 choices)
#   - Rangos/Umbrales (6)
#   - Timezone (1)
#   - RBAC (4 types)
#   - Audit (8 actions)
#   - Cache Keys (4 templates)
#   - Scheduler (6 configs)
#   - Mensajes (9)
# 
# CLEAN_CODE v3.0.1: Nombres auto-documentados [SUCCESS]
# CNST-007: MAX_EXPORT_ROWS [SUCCESS]
# CNST-010: SESSION_CLEANUP_DAYS [SUCCESS]
# CNST-013: Scheduler configs [SUCCESS]
# ============================================================================
