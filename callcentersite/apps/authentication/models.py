"""
Modelos de autenticación usando abstract models de core.

CLEAN_CODE v3.0.1: Nombres auto-documentados.
SOLID SRP: Cada modelo una responsabilidad.

CNST-001: NO email externo, solo preguntas de seguridad.
CNST-005: PBKDF2 password hashing.
CNST-031: Auditoría immutable.

CORRECCIONES v1.0.0:
[SUCCESS] Heredar de TimeStampedModel (NO duplicar created_at, updated_at)
[SUCCESS] Heredar de SoftDeleteMixin donde aplique
[SUCCESS] Heredar de CompleteBaseModel para auditoría completa
[SUCCESS] Usar ActiveRecordQuery
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.core.models import (
    TimeStampedModel,
    SoftDeleteMixin,
    AuditedModel,
    CompleteBaseModel,
    ActiveRecordQuery
)

User = get_user_model()


# ============================================================================
# LOGIN ATTEMPT
# ============================================================================

class LoginAttempt(TimeStampedModel):
    """
    Registro de intento de login (exitoso o fallido).
    
    CLEAN_CODE v3.0.1: Nombre que revela intención.
    SOLID SRP: Solo registra intentos de login.
    
    CNST-031: Auditoría immutable de todos los intentos.
    
    Hereda de TimeStampedModel:
    - created_at: Timestamp del intento (attempted_at en plan original)
    - updated_at: Última actualización
    
    Campos:
    - user: FK a User (null si username no existe)
    - username: Username intentado
    - success: Si fue exitoso
    - ip_address: IP del intento
    - user_agent: User agent del navegador
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='login_attempts',
        db_column='iIdUsuario',
        verbose_name='Usuario',
        help_text='Usuario (null si no existe el username)'
    )
    
    username = models.CharField(
        'Username Intentado',
        max_length=150,
        db_column='cUsername',
        help_text='Username que se intentó usar'
    )
    
    success = models.BooleanField(
        'Exitoso',
        db_column='bExitoso',
        help_text='True si login fue exitoso'
    )
    
    ip_address = models.GenericIPAddressField(
        'IP Address',
        db_column='cIpAddress',
        help_text='IP desde donde se intentó el login'
    )
    
    user_agent = models.CharField(
        'User Agent',
        max_length=255,
        blank=True,
        db_column='cUserAgent',
        help_text='User agent del navegador'
    )
    
    # [SUCCESS] NO CREAR attempted_at - usar created_at de TimeStampedModel
    
    class Meta:
        db_table = 'tbl_intentos_login'
        verbose_name = 'Intento de Login'
        verbose_name_plural = 'Intentos de Login'
        ordering = ['-created_at']  # [SUCCESS] Usar created_at
        indexes = [
            models.Index(fields=['username', '-created_at'], name='idx_login_username'),
            models.Index(fields=['ip_address', '-created_at'], name='idx_login_ip'),
            models.Index(fields=['success', '-created_at'], name='idx_login_success'),
        ]
    
    def __str__(self):
        """String representation."""
        status = 'SUCCESS' if self.success else 'FAILED'
        return f"{self.username} - {status} - {self.created_at}"


# ============================================================================
# SECURITY QUESTION
# ============================================================================

class SecurityQuestion(TimeStampedModel, SoftDeleteMixin):
    """
    Pregunta de seguridad predefinida.
    
    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID SRP: Solo preguntas de seguridad.
    
    CNST-001: Pool de 10 preguntas, usuario responde 5.
    
    Hereda:
    - TimeStampedModel: created_at, updated_at
    - SoftDeleteMixin: is_deleted, deleted_at, delete(), restore()
    
    Campos:
    - question: Texto de la pregunta
    - is_active: Si está disponible
    - order: Orden de presentación
    """
    
    question = models.CharField(
        'Pregunta',
        max_length=255,
        unique=True,
        db_column='cPregunta',
        help_text='Texto de la pregunta de seguridad'
    )
    
    is_active = models.BooleanField(
        'Activa',
        default=True,
        db_column='bActiva',
        help_text='Si la pregunta está disponible para usar'
    )
    
    order = models.IntegerField(
        'Orden',
        default=0,
        db_column='iOrden',
        help_text='Orden de presentación en UI'
    )
    
    # [SUCCESS] NO CREAR created_at - heredado de TimeStampedModel
    # [SUCCESS] NO CREAR is_deleted, deleted_at - heredado de SoftDeleteMixin
    
    objects = ActiveRecordQuery()  # [SUCCESS] Manager con active(), deleted()
    
    class Meta:
        db_table = 'tbl_preguntas_seguridad'
        verbose_name = 'Pregunta de Seguridad'
        verbose_name_plural = 'Preguntas de Seguridad'
        ordering = ['order', 'question']
        indexes = [
            models.Index(fields=['is_active', 'order'], name='idx_secq_active'),
            models.Index(fields=['is_deleted'], name='idx_secq_deleted'),
        ]
    
    def __str__(self):
        """String representation."""
        return self.question


# ============================================================================
# USER SECURITY ANSWER
# ============================================================================

class UserSecurityAnswer(CompleteBaseModel):
    """
    Respuesta de usuario a pregunta de seguridad.
    
    CLEAN_CODE v3.0.1: Nombre auto-documentado.
    SOLID SRP: Solo respuestas de seguridad.
    
    CNST-001: Hash PBKDF2, normalización lowercase.
    
    Hereda CompleteBaseModel:
    - TimeStampedModel: created_at, updated_at
    - SoftDeleteMixin: is_deleted, deleted_at, delete(), restore()
    - AuditedModel: created_by, updated_by
    
    Campos:
    - user: FK a User
    - question: FK a SecurityQuestion
    - answer_hash: Hash PBKDF2 de la respuesta
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='security_answers',
        db_column='iIdUsuario',
        verbose_name='Usuario'
    )
    
    question = models.ForeignKey(
        SecurityQuestion,
        on_delete=models.PROTECT,
        db_column='iIdPregunta',
        verbose_name='Pregunta'
    )
    
    answer_hash = models.CharField(
        'Hash Respuesta',
        max_length=255,
        db_column='cHashRespuesta',
        help_text='Hash PBKDF2 de la respuesta normalizada'
    )
    
    # [SUCCESS] NO CREAR created_at, updated_at - heredados de CompleteBaseModel
    # [SUCCESS] NO CREAR created_by, updated_by - heredados de CompleteBaseModel
    # [SUCCESS] NO CREAR is_deleted, deleted_at - heredados de CompleteBaseModel
    
    objects = ActiveRecordQuery()  # [SUCCESS] Manager
    
    class Meta:
        db_table = 'tbl_respuestas_seguridad'
        verbose_name = 'Respuesta de Seguridad'
        verbose_name_plural = 'Respuestas de Seguridad'
        unique_together = [['user', 'question']]
        indexes = [
            models.Index(fields=['user'], name='idx_secanswer_user'),
            models.Index(fields=['is_deleted'], name='idx_secanswer_deleted'),
        ]
    
    def __str__(self):
        """String representation."""
        return f"{self.user.username} - {self.question.question[:30]}..."
    
    def set_answer(self, answer: str):
        """
        Hashea y guarda la respuesta.
        
        SOLID SRP: Solo hashea respuesta.
        
        Normalización: lowercase + strip
        Hash: PBKDF2 (mismo que passwords)
        
        Args:
            answer: Respuesta en texto plano
        
        Raises:
            ValidationError: Si respuesta vacía
        """
        # Normalizar: lowercase, strip
        normalized = answer.lower().strip()
        
        # Validar que no esté vacía
        if not normalized:
            raise ValidationError("La respuesta no puede estar vacía")
        
        # Hash con PBKDF2
        self.answer_hash = make_password(normalized)
    
    def check_answer(self, answer: str) -> bool:
        """
        Verifica si la respuesta es correcta.
        
        SOLID SRP: Solo verifica respuesta.
        
        Args:
            answer: Respuesta a verificar
        
        Returns:
            bool: True si correcta
        """
        normalized = answer.lower().strip()
        return check_password(normalized, self.answer_hash)


# ============================================================================
# SESSION LOG
# ============================================================================

class SessionLog(CompleteBaseModel):
    """
    Log de sesión de usuario.
    
    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID SRP: Solo logs de sesión.
    
    CNST-031: Auditoría de sesiones.
    CNST-010: Sessions en PostgreSQL.
    
    Hereda CompleteBaseModel:
    - TimeStampedModel: created_at (login_at), updated_at
    - SoftDeleteMixin: is_deleted, deleted_at
    - AuditedModel: created_by, updated_by
    
    Campos:
    - user: FK a User
    - session_key: Django session key
    - ip_address: IP del login
    - user_agent: User agent
    - logout_at: Timestamp de logout (null si activa)
    - is_active: Si la sesión está activa
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='session_logs',
        db_column='iIdUsuario',
        verbose_name='Usuario'
    )
    
    session_key = models.CharField(
        'Session Key',
        max_length=40,
        db_column='cSessionKey',
        help_text='Django session key'
    )
    
    ip_address = models.GenericIPAddressField(
        'IP Address',
        db_column='cIpAddress',
        help_text='IP desde donde se hizo login'
    )
    
    user_agent = models.CharField(
        'User Agent',
        max_length=255,
        blank=True,
        db_column='cUserAgent',
        help_text='User agent del navegador'
    )
    
    # [SUCCESS] login_at = created_at (heredado de TimeStampedModel)
    # [SUCCESS] NO CREAR login_at - usar created_at
    
    logout_at = models.DateTimeField(
        'Logout',
        null=True,
        blank=True,
        db_column='dtLogout',
        help_text='Fecha y hora de logout'
    )
    
    is_active = models.BooleanField(
        'Activa',
        default=True,
        db_column='bActiva',
        help_text='Si la sesión está activa'
    )
    
    # [SUCCESS] NO CREAR created_at, updated_at - heredados
    # [SUCCESS] NO CREAR created_by, updated_by - heredados
    # [SUCCESS] NO CREAR is_deleted, deleted_at - heredados
    
    objects = ActiveRecordQuery()  # [SUCCESS] Manager
    
    class Meta:
        db_table = 'tbl_log_sesiones'
        verbose_name = 'Log de Sesión'
        verbose_name_plural = 'Logs de Sesiones'
        ordering = ['-created_at']  # [SUCCESS] login_at = created_at
        indexes = [
            models.Index(fields=['user', '-created_at'], name='idx_session_user'),
            models.Index(fields=['session_key'], name='idx_session_key'),
            models.Index(fields=['is_active'], name='idx_session_active'),
            models.Index(fields=['is_deleted'], name='idx_session_deleted'),
        ]
    
    def __str__(self):
        """String representation."""
        return f"{self.user.username} - {self.created_at}"  # [SUCCESS] login_at = created_at
    
    @property
    def duration(self):
        """
        Duración de la sesión.
        
        SOLID SRP: Solo calcula duración.
        
        Returns:
            timedelta: Duración o None
        """
        if self.logout_at:
            return self.logout_at - self.created_at  # [SUCCESS] login_at = created_at
        elif self.is_active:
            return timezone.now() - self.created_at  # [SUCCESS]
        return None


# ============================================================================
# LOGIN LOCKOUT
# ============================================================================

class LoginLockout(TimeStampedModel):
    """
    Tracking de bloqueo de cuentas por intentos fallidos.
    
    Reemplaza cache volátil con persistencia en BD.
    CUMPLE: CNST-010 (NO cache/Redis permitido)
    
    CLEAN_CODE v3.0.1: Nombre que revela intención.
    SOLID SRP: Solo gestiona lockout de cuentas.
    
    CNST-010: Persistencia SOLO en PostgreSQL (NO cache).
    
    Hereda de TimeStampedModel:
    - created_at: Primer registro de lockout
    - updated_at: Última actualización (auto)
    
    Attributes:
        username: Username del usuario (único)
        failed_attempts: Contador de intentos fallidos
        locked_until: Timestamp hasta cuando está bloqueado
        last_attempt_at: Último intento registrado
    
    Usage:
        # Verificar bloqueo
        lockout = LoginLockout.objects.get(username='user')
        if lockout.is_locked():
            # Usuario bloqueado
            
        # Registrar intento
        lockout.increment_attempts()
        
        # Bloquear
        lockout.lock(duration_minutes=30)
        
        # Desbloquear
        lockout.unlock()
    """
    
    username = models.CharField(
        max_length=150,
        unique=True,
        db_index=True,
        help_text="Username del usuario"
    )
    
    failed_attempts = models.PositiveIntegerField(
        default=0,
        help_text="Número de intentos fallidos"
    )
    
    locked_until = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Bloqueado hasta este timestamp (None = no bloqueado)"
    )
    
    last_attempt_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp del último intento"
    )
    
    class Meta:
        db_table = 'authentication_login_lockout'
        verbose_name = 'Login Lockout'
        verbose_name_plural = 'Login Lockouts'
        indexes = [
            models.Index(fields=['username', 'locked_until'], name='idx_username_locked'),
            models.Index(fields=['last_attempt_at'], name='idx_last_attempt'),
        ]
        ordering = ['-last_attempt_at']
    
    def __str__(self):
        """String representation."""
        status = "LOCKED" if self.is_locked() else "ACTIVE"
        return f"{self.username} - {self.failed_attempts} attempts ({status})"
    
    def is_locked(self) -> bool:
        """
        Verifica si el usuario aún está bloqueado.
        
        SOLID SRP: Solo verifica estado de bloqueo.
        
        Returns:
            True si locked_until es futuro, False si expiró o no está bloqueado
        """
        if not self.locked_until:
            return False
        
        return timezone.now() < self.locked_until
    
    def increment_attempts(self) -> int:
        """
        Incrementa el contador de intentos fallidos.
        
        SOLID SRP: Solo incrementa contador.
        
        Returns:
            Nuevo número de intentos
        """
        self.failed_attempts += 1
        self.save(update_fields=['failed_attempts', 'last_attempt_at'])
        return self.failed_attempts
    
    def lock(self, duration_minutes: int) -> None:
        """
        Bloquea la cuenta por X minutos.
        
        SOLID SRP: Solo bloquea cuenta.
        
        Args:
            duration_minutes: Duración del bloqueo en minutos
        """
        from datetime import timedelta
        
        self.locked_until = timezone.now() + timedelta(minutes=duration_minutes)
        self.save(update_fields=['locked_until'])
    
    def unlock(self) -> None:
        """
        Desbloquea la cuenta y resetea contador.
        
        SOLID SRP: Solo desbloquea y resetea.
        """
        self.failed_attempts = 0
        self.locked_until = None
        self.save(update_fields=['failed_attempts', 'locked_until', 'last_attempt_at'])
    
    @classmethod
    def cleanup_expired(cls, days: int = 30) -> int:
        """
        Elimina registros antiguos (lockouts expirados hace > X días).
        
        SOLID SRP: Solo limpia registros antiguos.
        
        Args:
            days: Días de antigüedad para eliminar
            
        Returns:
            Número de registros eliminados
        """
        from datetime import timedelta
        
        cutoff = timezone.now() - timedelta(days=days)
        
        # Eliminar registros:
        # - No bloqueados (locked_until=None)
        # - Con último intento > X días atrás
        deleted, _ = cls.objects.filter(
            locked_until__isnull=True,
            last_attempt_at__lt=cutoff
        ).delete()
        
        return deleted


# ============================================================================
# RESUMEN MODELS
# 
# Total: 5 modelos
# 
# Models:
#   [SUCCESS] LoginAttempt (TimeStampedModel)
#   [SUCCESS] SecurityQuestion (TimeStampedModel + SoftDeleteMixin)
#   [SUCCESS] UserSecurityAnswer (CompleteBaseModel)
#   [SUCCESS] SessionLog (CompleteBaseModel)
#   [SUCCESS] LoginLockout (TimeStampedModel) - CNST-010 compliance
# 
# SOLID Compliance:
#   [SUCCESS] SRP: Cada modelo una responsabilidad
#   [SUCCESS] OCP: Extensibles vía abstract models
#   [SUCCESS] DIP: Dependen de abstract models (core)
# 
# Herencia de core:
#   [SUCCESS] TimeStampedModel: created_at, updated_at
#   [SUCCESS] SoftDeleteMixin: is_deleted, deleted_at, delete(), restore()
#   [SUCCESS] CompleteBaseModel: Combina los 3
#   [SUCCESS] ActiveRecordQuery: active(), deleted()
# 
# CNST-010 Compliance:
#   [SUCCESS] LoginLockout usa PostgreSQL (NO cache/Redis)
#   [SUCCESS] Persistencia en BD (sobrevive restart)
#   [SUCCESS] Compatible multi-server
# 
# Campos eliminados (heredados):
#   [ERROR] attempted_at -> created_at
#   [ERROR] login_at -> created_at
#   [ERROR] created_at, updated_at (4 veces)
#   [ERROR] created_by, updated_by (2 veces)
#   [ERROR] is_deleted, deleted_at (2 veces)
# 
# Total líneas eliminadas: ~40 líneas
# ============================================================================
