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
    Suscripción de usuario a alertas específicas.

    Soporta dos FK:
    - `alert_configuration`: legacy (pre-FASE 4)
    - `rule`: canónico (UC_ALR_05 FASE 4)

    state: active | paused | cancelled | auto_paused
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
        null=True, blank=True,
        related_name='subscriptions',
        verbose_name='Configuración de Alerta (legacy)'
    )
    # UC_ALR_05: FK canónica a AlertRule
    rule = models.ForeignKey(
        'AlertRule',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='subscriptions',
        verbose_name='Regla de Alerta',
    )
    # Estado canónico
    state = models.CharField(
        max_length=20, default='active',
        choices=[
            ('active',      'Activa'),
            ('paused',      'Pausada'),
            ('cancelled',   'Cancelada'),
            ('auto_paused', 'Auto-pausada'),
        ],
        db_index=True,
    )
    severity_filter = models.CharField(
        max_length=20, default='warning',
        help_text='Filtro de severidad mínima para notificar.',
    )
    # Legacy
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activa (legacy)'
    )
    subscribed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de suscripción'
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = 'alerts_alert_subscription'
        verbose_name = 'Suscripción a Alerta'
        verbose_name_plural = 'Suscripciones a Alertas'
        indexes = [
            models.Index(fields=['user', 'is_active'], name='idx_sub_user_active'),
            models.Index(fields=['user', 'state'],     name='idx_sub_user_state'),
        ]

    def __str__(self):
        target = self.rule or self.alert_configuration
        return f"Sub[{self.state}] {self.user.username} -> {target}"


# ===========================================================================
# INTERNAL MAILBOX — FASE 0 (F0-T4)
# ===========================================================================
# Fuente: modelo-dominio-iact.rst § 4.1 (BC Auth), CNST-001, BR-004
# Hallazgo F0-H-005: InternalMailbox no existía. Se crea en FASE 0 porque
# es prerequisito de UC_USR_01 (CA-01: "1 InternalMessage en buzón del
# nuevo User"), UC_AUTH_01 (FA-01: notify), UC_AUTH_03, UC_ALR_05.

class InternalMailbox(models.Model):
    """
    Buzón de mensajes interno de un usuario (1:1 con User).

    CNST-001: PROHIBIDO email/SMS/webhooks externos. Toda comunicación
    relevante del sistema se entrega aquí. BR-004: no canales externos.

    El buzón se crea automáticamente al crear un User (señal post_save).
    El servicio MailboxService.deliver() es el único punto de entrada.

    Modelo: modelo-dominio-iact.rst § 4.1
    """

    owner = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='mailbox',
        verbose_name='Propietario',
        help_text='Usuario dueño del buzón (1:1).',
    )
    last_read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Última lectura',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado')

    class Meta:
        db_table = 'alerts_internal_mailbox'
        verbose_name = 'Buzón interno'
        verbose_name_plural = 'Buzones internos'

    def __str__(self) -> str:
        return f'Mailbox({self.owner.username})'

    def deliver_message(
        self,
        subject: str,
        body: str,
        priority: str = 'info',
        sender: 'User | None' = None,
    ) -> 'MailboxMessage':
        """
        Entrega un mensaje al buzón. NUNCA envía email externo (CNST-001).

        Args:
            subject: Asunto del mensaje.
            body: Cuerpo del mensaje.
            priority: 'info' | 'warning' | 'error' | 'critical'
            sender: Usuario remitente (None = sistema).

        Returns:
            MailboxMessage: Mensaje creado en BD.
        """
        return MailboxMessage.objects.create(
            mailbox=self,
            subject=subject,
            body=body,
            priority=priority,
            sender=sender,
        )

    def get_unread_count(self) -> int:
        """Retorna el número de mensajes no leídos."""
        return self.messages.filter(read_at__isnull=True).count()


class MailboxMessage(models.Model):
    """
    Mensaje en un InternalMailbox. Append-only (BR-009: no DELETE).

    No usa email externo (CNST-001). CNST-026: sin PII en subject/body
    más allá del identificador opaco del usuario.
    """

    # F6-P0-T5: unificado con PRIORITY_CHOICES de módulo para evitar PriorityEa7Enum
    PRIORITY_CHOICES = [
        ('info',     'Informativa'),
        ('warning',  'Advertencia'),
        ('error',    'Error'),
        ('critical', 'Crítica'),
    ]

    STATE_UNREAD   = 'UNREAD'
    STATE_READ     = 'READ'
    STATE_DELETED  = 'DELETED'   # BR-009: baja lógica

    STATE_CHOICES = [
        (STATE_UNREAD,  'Sin leer'),
        (STATE_READ,    'Leído'),
        (STATE_DELETED, 'Eliminado'),  # BR-009
    ]

    mailbox = models.ForeignKey(
        InternalMailbox,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Buzón',
    )
    subject = models.CharField(max_length=200, verbose_name='Asunto')
    body = models.TextField(verbose_name='Contenido')
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='info',
        verbose_name='Prioridad',
    )
    sender = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='mailbox_messages_sent',
        verbose_name='Remitente',
        help_text='None = mensaje del sistema.',
    )
    state = models.CharField(
        max_length=10,
        choices=STATE_CHOICES,
        default=STATE_UNREAD,
        verbose_name='Estado',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado')
    read_at = models.DateTimeField(null=True, blank=True, verbose_name='Leído en')

    class Meta:
        db_table = 'alerts_mailbox_message'
        ordering = ['-created_at']
        verbose_name = 'Mensaje de buzón'
        verbose_name_plural = 'Mensajes de buzón'
        indexes = [
            models.Index(fields=['mailbox', 'state'], name='idx_mbmsg_mailbox_state'),
            models.Index(fields=['-created_at'], name='idx_mbmsg_created'),
        ]

    def __str__(self) -> str:
        return f'[{self.priority}] {self.subject} → {self.mailbox.owner.username}'

    def delete(self, *args, **kwargs):
        """BR-009: baja lógica. No elimina físicamente."""
        self.state = self.STATE_DELETED
        self.save(update_fields=['state'])

    def mark_read(self):
        """Marcar como leído."""
        from django.utils import timezone
        self.state = self.STATE_READ
        self.read_at = timezone.now()
        self.save(update_fields=['state', 'read_at'])


# ===========================================================================
# UC_ALR_01/02/03 — AlertRule, AlertRuleHistory, Alert
# Prerequisito FASE 3 (2026-05-13):
# Fuente: uc-alr-01/datos-involucrados.rst § 7.1, uc-alr-02 § 7.1
# AlertConfiguration (existente) es un modelo diferente — mensajería/APScheduler.
# AlertRule es el modelo de RBAC-aware rules con metric/scope/condition.
# ===========================================================================

import uuid as _uuid


class AlertRule(models.Model):
    """
    Regla de alerta definida por un usuario (UC_ALR_01).

    Fuente: uc-alr-01/datos-involucrados.rst § 7.1
    RBAC: ACC-002 configure_alerts (propias), ACC-003 configure_team_alerts (equipo).

    Invariantes:
    - scope define el segmento/cola/campaña — RuleValidator verifica que
      el scope pertenezca a los segmentos del actor.
    - version se incrementa en cada update (CA-05).
    - state: active | paused (CA-06). BR-009: nunca DELETE.
    """

    STATUS_ACTIVE = 'active'
    STATUS_PAUSED = 'paused'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Activa'),
        (STATUS_PAUSED, 'Pausada'),
    ]
    SEVERITY_CHOICES = [
        ('info',     'Info'),
        ('warning',  'Warning'),
        ('error',    'Error'),
        ('critical', 'Critical'),
    ]

    id               = models.UUIDField(
        primary_key=True, default=_uuid.uuid4, editable=False,
        verbose_name='ID',
    )
    actor            = models.ForeignKey(
        User, on_delete=models.PROTECT,
        related_name='alert_rules',
        verbose_name='Propietario',
        help_text='Usuario que creó la regla.',
    )
    name             = models.CharField(max_length=200, verbose_name='Nombre')
    metric           = models.CharField(
        max_length=100, verbose_name='Métrica',
        help_text='Métrica evaluada (call_volume, avg_wait_time, sla_percentage…).',
    )
    scope            = models.JSONField(
        verbose_name='Scope',
        help_text='{"segment"?, "queue"?, "campaign"?}. Validado por RuleValidator.',
    )
    condition        = models.JSONField(
        verbose_name='Condición',
        help_text='{"op": "> | < | >= | <= | ==", "threshold": N}.',
    )
    window_minutes   = models.PositiveIntegerField(
        verbose_name='Ventana (min)',
        help_text='Ventana de evaluación en minutos.',
    )
    severity         = models.CharField(
        max_length=10, choices=SEVERITY_CHOICES, verbose_name='Severidad',
    )
    actions          = models.JSONField(
        default=list, verbose_name='Acciones',
        help_text='Lista de acciones a ejecutar cuando la regla se dispara.',
    )
    cooldown_minutes = models.PositiveIntegerField(
        default=60, verbose_name='Cooldown (min)',
        help_text='Minutos que deben pasar antes de que la regla se dispare de nuevo (CA-09).',
    )
    status           = models.CharField(
        max_length=10, choices=STATUS_CHOICES,
        default=STATUS_ACTIVE, verbose_name='Estado',
    )
    version          = models.PositiveIntegerField(
        default=1, verbose_name='Versión',
        help_text='Incrementado en cada update (CA-05). Permite trazabilidad de cambios.',
    )
    created_at       = models.DateTimeField(auto_now_add=True, verbose_name='Creado')
    updated_at       = models.DateTimeField(auto_now=True, verbose_name='Actualizado')

    class Meta:
        db_table = 'alerts_alert_rule'
        verbose_name = 'Regla de Alerta'
        verbose_name_plural = 'Reglas de Alerta'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['actor'], name='idx_alr_actor'),
            models.Index(fields=['status', 'version'], name='idx_alr_status_ver'),
        ]

    def __str__(self) -> str:
        return f'[{self.severity}] {self.name} ({self.status})'


class AlertRuleHistory(models.Model):
    """
    Snapshot inmutable de AlertRule por cada update (UC_ALR_01 CA-10 auditoría).

    BR-009: no DELETE. Los snapshots son evidencia de cambios de configuración.
    """

    rule       = models.ForeignKey(
        AlertRule, on_delete=models.CASCADE,
        related_name='history', verbose_name='Regla',
    )
    version    = models.PositiveIntegerField(verbose_name='Versión')
    snapshot   = models.JSONField(
        verbose_name='Snapshot',
        help_text='Copia completa del AlertRule en el momento del cambio.',
    )
    changed_by = models.ForeignKey(
        User, on_delete=models.PROTECT,
        related_name='alert_rule_changes', verbose_name='Cambiado por',
    )
    changed_at = models.DateTimeField(auto_now_add=True, verbose_name='Cambiado en')

    class Meta:
        db_table = 'alerts_alert_rule_history'
        verbose_name = 'Historial de Regla'
        verbose_name_plural = 'Historiales de Regla'
        unique_together = ('rule', 'version')
        ordering = ['-version']

    def __str__(self) -> str:
        return f'{self.rule.name} v{self.version}'


class Alert(models.Model):
    """
    Alerta disparada por una AlertRule (UC_ALR_02, UC_ALR_03).

    Fuente: uc-alr-02/datos-involucrados.rst § 7.1

    Ciclo de vida: firing → acknowledged → resolved → closed.
    BR-009: no DELETE físico.
    """

    STATE_FIRING       = 'firing'
    STATE_ACKNOWLEDGED = 'acknowledged'
    STATE_RESOLVED     = 'resolved'
    STATE_CLOSED       = 'closed'
    STATE_CHOICES = [
        (STATE_FIRING,       'Disparada'),
        (STATE_ACKNOWLEDGED, 'Reconocida'),
        (STATE_RESOLVED,     'Resuelta'),
        (STATE_CLOSED,       'Cerrada'),
    ]

    id                 = models.UUIDField(
        primary_key=True, default=_uuid.uuid4, editable=False,
    )
    rule               = models.ForeignKey(
        AlertRule, on_delete=models.PROTECT,
        related_name='alerts', verbose_name='Regla',
    )
    # Snapshots — inmutables, independientes del estado de la regla
    rule_name          = models.CharField(max_length=200, verbose_name='Nombre regla (snapshot)')
    metric             = models.JSONField(verbose_name='Métrica (snapshot)')
    scope              = models.JSONField(verbose_name='Scope (snapshot)')
    severity           = models.CharField(max_length=10, verbose_name='Severidad')
    # Estado mutable
    state              = models.CharField(
        max_length=15, choices=STATE_CHOICES,
        default=STATE_FIRING, verbose_name='Estado',
    )
    fired_at           = models.DateTimeField(verbose_name='Disparada en')
    acknowledged_by    = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='acknowledged_alerts', verbose_name='Reconocida por',
    )
    acknowledged_at    = models.DateTimeField(
        null=True, blank=True, verbose_name='Reconocida en',
    )
    acknowledged_note  = models.TextField(
        blank=True, verbose_name='Nota de reconocimiento',
        help_text='UC_ALR_03 CA-02: nota libre. Máx 500 chars — validado en servicio.',
    )
    resolved_at        = models.DateTimeField(null=True, blank=True, verbose_name='Resuelta en')
    current_value      = models.FloatField(
        null=True, blank=True, verbose_name='Valor actual',
        help_text='Valor de la métrica en el momento del query.',
    )
    threshold          = models.FloatField(
        null=True, blank=True, verbose_name='Umbral (snapshot)',
        help_text='Threshold de la condición en el momento del disparo.',
    )

    class Meta:
        db_table = 'alerts_alert'
        verbose_name = 'Alerta'
        verbose_name_plural = 'Alertas'
        ordering = ['-fired_at']
        indexes = [
            models.Index(fields=['state', 'severity', '-fired_at'],
                         name='idx_alert_state_sev'),
            models.Index(fields=['rule', '-fired_at'], name='idx_alert_rule'),
        ]

    def __str__(self) -> str:
        return f'[{self.severity}] {self.rule_name} — {self.state}'
