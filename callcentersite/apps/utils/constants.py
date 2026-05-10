"""Shared constants for the IACT API."""

# Call statuses
CALL_STATUS_PENDING = 'pending'
CALL_STATUS_IN_PROGRESS = 'in_progress'
CALL_STATUS_COMPLETED = 'completed'
CALL_STATUS_ABANDONED = 'abandoned'

CALL_STATUS_CHOICES = [
    (CALL_STATUS_PENDING, 'Pendiente'),
    (CALL_STATUS_IN_PROGRESS, 'En progreso'),
    (CALL_STATUS_COMPLETED, 'Completada'),
    (CALL_STATUS_ABANDONED, 'Abandonada'),
]

# Pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Avatar
AVATAR_UPLOAD_PATH = 'profiles/'
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp']
MAX_AVATAR_SIZE_MB = 2
MAX_AVATAR_SIZE_BYTES = MAX_AVATAR_SIZE_MB * 1024 * 1024

# Alert levels
ALERT_LEVEL_INFO = 'info'
ALERT_LEVEL_WARNING = 'warning'
ALERT_LEVEL_CRITICAL = 'critical'

ALERT_LEVEL_CHOICES = [
    (ALERT_LEVEL_INFO, 'Informativo'),
    (ALERT_LEVEL_WARNING, 'Advertencia'),
    (ALERT_LEVEL_CRITICAL, 'Critico'),
]
