# apps/alerts/models.py

from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from apps.core.models import SoftDeleteMixin

User = get_user_model()


# ============================================================================
# CONSTANTES
# ============================================================================

PRIORITY_CHOICES = [
    ('info', 'Informativa'),
    ('warning', 'Advertencia'),
    ('error', 'Error'),
    ('critical', 'Crítica'),
]


# ============================================================================
# MODELOS
# ============================================================================

class InternalMessage(SoftDeleteMixin, models.Model):
    """
    Mensaje interno entre usuarios del sistema
    
    Cumple:
    - CNST-001: Solo mensajería interna (NO email)
    - CNST-024: Máximo 50 destinatarios
    
    Relaciones:
    - sender: Usuario que envía (User)
    - recipients: Usuarios que reciben (User) - many-to-many through MessageRecipient
    """
    sender = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='sent_messages',
        verbose_name='Remitente'
    )
    subject = models.CharField(
        max_length=200,
        verbose_name='Asunto'
    )
    body = models.TextField(
        verbose_name='Contenido'
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='info',
        verbose_name='Prioridad'
    )
    
    # Many-to-many con usuarios a través de MessageRecipient
    recipients = models.ManyToManyField(
        User,
        through='MessageRecipient',
        related_name='received_messages',
        verbose_name='Destinatarios'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    
    class Meta:
        db_table = 'alerts_internal_message'
        ordering = ['-created_at']
        verbose_name = 'Mensaje Interno'
        verbose_name_plural = 'Mensajes Internos'
        indexes = [
            models.Index(fields=['-created_at'], name='idx_msg_created'),
            models.Index(fields=['sender', '-created_at'], name='idx_msg_sender'),
            models.Index(fields=['priority'], name='idx_msg_priority'),
        ]
    
    def __str__(self):
        return f"{self.subject} (de {self.sender.username})"
    
    def clean(self):
        """Validar CNST-024: máximo 50 destinatarios"""
        super().clean()
        if self.pk and self.recipients.count() > 50:
            raise ValidationError(
                'Máximo 50 destinatarios permitidos (CNST-024)'
            )


class MessageRecipient(models.Model):
    """
    Relación mensaje-destinatario con estado de lectura
    
    Permite:
    - Estado individual por destinatario (read_at, archived_at)
    - Tracking de lectura
    - Archivo individual
    """
    message = models.ForeignKey(
        InternalMessage,
        on_delete=models.CASCADE,
        related_name='message_recipients',
        verbose_name='Mensaje'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='message_receipts',
        verbose_name='Usuario'
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de lectura'
    )
    archived_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de archivo'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de recepción'
    )
    
    class Meta:
        db_table = 'alerts_message_recipient'
        unique_together = ('message', 'user')
        verbose_name = 'Destinatario de Mensaje'
        verbose_name_plural = 'Destinatarios de Mensajes'
        indexes = [
            models.Index(fields=['user', 'read_at'], name='idx_rcpt_user_read'),
            models.Index(fields=['user', 'archived_at'], name='idx_rcpt_user_arch'),
        ]
    
    def __str__(self):
        return f"{self.message.subject} -> {self.user.username}"
    
    @property
    def is_read(self):
        """Indica si el mensaje ha sido leído"""
        return self.read_at is not None
    
    @property
    def is_archived(self):
        """Indica si el mensaje ha sido archivado"""
        return self.archived_at is not None


class AlertConfiguration(SoftDeleteMixin, models.Model):
    """
    Configuración de alertas automáticas
    
    Evaluadas por APScheduler (CNST-013 compliant)
    
    Estructura de condition (JSONField):
    {
        "metric": "call_volume | avg_wait_time | sla_percentage",
        "operator": "> | < | >= | <= | ==",
        "value": 100,
        "period": "1h | 30m | 1d",
        "aggregation": "count | avg | sum | max | min"
    }
    """
    name = models.CharField(
        max_length=100,
        verbose_name='Nombre'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descripción'
    )
    condition = models.JSONField(
        verbose_name='Condición',
        help_text='Condición en formato JSON'
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='info',
        verbose_name='Prioridad'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activa'
    )
    
    # Tracking de evaluación (para APScheduler)
    last_evaluated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Última evaluación'
    )
    last_triggered_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Último disparo'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Fecha de actualización'
    )
    
    class Meta:
        db_table = 'alerts_alert_configuration'
        ordering = ['-created_at']
        verbose_name = 'Configuración de Alerta'
        verbose_name_plural = 'Configuraciones de Alertas'
        indexes = [
            models.Index(fields=['is_active'], name='idx_alert_active'),
            models.Index(fields=['-created_at'], name='idx_alert_created'),
        ]
    
    def __str__(self):
        status = "[OK]" if self.is_active else "[FAIL]"
        return f"{status} {self.name} ({self.priority})"


class AlertSubscription(SoftDeleteMixin, models.Model):
    """
    Suscripción de usuario a alertas específicas
    
    Permite que usuarios elijan a qué alertas suscribirse
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='alert_subscriptions',
        verbose_name='Usuario'
    )
    alert_configuration = models.ForeignKey(
        AlertConfiguration,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Configuración de Alerta'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activa'
    )
    subscribed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de suscripción'
    )
    
    class Meta:
        db_table = 'alerts_alert_subscription'
        unique_together = ('user', 'alert_configuration')
        verbose_name = 'Suscripción a Alerta'
        verbose_name_plural = 'Suscripciones a Alertas'
        indexes = [
            models.Index(fields=['user', 'is_active'], name='idx_sub_user_active'),
        ]
    
    def __str__(self):
        status = "[OK]" if self.is_active else "[FAIL]"
        return f"{status} {self.user.username} -> {self.alert_configuration.name}"
