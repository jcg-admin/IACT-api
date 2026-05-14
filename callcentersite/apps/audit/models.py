from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class AuditLog(models.Model):
    """
    Log de auditoria INMUTABLE.

    CNST-009: Solo append, NO update, NO delete.

    Campos:
    - user: Quien realizo la accion
    - action: Que hizo (LOGIN, LOGOUT, CREATE, UPDATE, DELETE, etc)
    - resource: En que recurso
    - result: SUCCESS o FAILURE
    - timestamp: Cuando
    - ip_address: Desde donde
    - user_agent: Con que
    - details: Informacion adicional (JSON)
    """

    # Quien
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs',
        verbose_name='Usuario',
    )

    # Que
    action = models.CharField(
        max_length=50,
        verbose_name='Accion',
        help_text='LOGIN, LOGOUT, CREATE, UPDATE, DELETE, etc',
    )
    resource = models.CharField(
        max_length=200,
        verbose_name='Recurso',
        help_text='Recurso afectado',
    )
    result = models.CharField(
        max_length=20,
        choices=[
            ('SUCCESS', 'Exito'),
            ('FAILURE', 'Fallo'),
        ],
        verbose_name='Resultado',
    )

    # Cuando
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha/Hora',
    )

    # Donde
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='IP',
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name='User Agent',
    )

    # Detalles
    details = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Detalles adicionales',
    )

    class Meta:
        db_table = 'audit_logs'
        verbose_name = 'Log Auditoria'
        verbose_name_plural = 'Logs Auditoria'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.timestamp} {self.user} {self.action}"

    def save(self, *args, **kwargs):
        """
        INMUTABLE: Solo crear, NO modificar.

        CNST-009: Auditoria inmutable.

        Raises:
            PermissionError: Si se intenta modificar un log existente
        """
        if self.pk:
            raise PermissionError(
                "CNST-009 VIOLACION: AuditLog es inmutable, "
                "NO se permite UPDATE"
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        PROHIBIDO eliminar logs auditoria.

        CNST-009: Logs son inmutables.

        Raises:
            PermissionError: Siempre
        """
        raise PermissionError(
            "CNST-009 VIOLACION: AuditLog no se puede eliminar"
        )

    @classmethod
    def record(cls, user, action, resource, result, **kwargs):
        """
        Helper para crear log de auditoria.

        Args:
            user: Usuario que realiza la accion
            action: Accion realizada
            resource: Recurso afectado
            result: 'SUCCESS' o 'FAILURE'
            **kwargs: ip_address, user_agent, details, etc

        Returns:
            AuditLog: Log creado
        """
        return cls.objects.create(
            user=user,
            action=action,
            resource=resource,
            result=result,
            **kwargs
        )


# ===========================================================================
# EVENT TYPE CATALOG — FASE 0 (F0-T5)
# ===========================================================================
# Fuente: modelo-dominio-iact.rst § 4.7 (EventType enum), UC_PERM_09 CA-03

VALID_EVENT_TYPES = frozenset({
    # Auth (UC_AUTH_01..05)
    'LOGIN',
    'LOGOUT',
    'SESSION_CLOSED',
    'LOGIN_NO_PERMISSIONS',
    'BLOCKED_LOGIN_ATTEMPT',
    'PASSWORD_CHANGED',
    'PASSWORD_RESET',
    # Access assignments (UC_ACC_01..04)
    'FUNCTIONS_ASSIGNED',
    'FUNCTIONS_REVOKED',
    'AGR_ASSIGNED',
    'AGR_ASSIGN_NOOP',
    'AGR_REVOKED',
    # Access management (UC_ACC_05, UC_PERM_03..06)
    # STD_008 FASE 3 (2026-05-13): SOD_RULE_* → SEPARATION_RULE_*
    'SEPARATION_RULE_CREATED',
    'SEPARATION_RULE_UPDATED',
    'SEPARATION_RULE_DISABLED',
    'EXCEPTIONAL_GRANTED',
    'EXCEPTIONAL_REVOKED',
    # Users (UC_USR_01..04)
    'USER_CREATED',
    'USER_MODIFIED',
    'USER_DEACTIVATED',
    'USER_BLOCKED',
    'USER_UNBLOCKED',
    'USER_REACTIVATED',
    # Pipeline (UC_PIP_04)
    'PIPELINE_RETRY_REQUESTED',
    # UC_RPT_04 — Export de reporte (FASE 3 TDD 2026-05-13)
    'REPORT_EXPORT_QUEUED',
    'REPORT_EXPORT_COMPLETED',
    'REPORT_EXPORT_FAILED',
    # Reports (UC_RPT_04, UC_RPT_11)
    'EXPORT_REQUESTED',
    'REPORT_SHARED',
    # Alerts (UC_ALR_03)
    'ALERT_ACKNOWLEDGED',
    # UC_ALR_01 — CRUD de reglas de alerta (FASE 3 TDD 2026-05-13)
    'ALERT_RULE_CREATED',
    'ALERT_RULE_UPDATED',
    'ALERT_RULE_DELETED',
    'ALERT_RULE_PAUSED',
    'ALERT_RULE_RESUMED',
    # Audit (UC_AUD_01..04) — meta-audit
    'GENERAL_AUDIT_QUERIED',
    'AUDIT_EXPORTED',
    'COMPLIANCE_REPORT_GENERATED',
    # Auth extendido (UC_AUTH_02..05 — FASE 2)
    'LOGOUT_REPLAY',
    'LOGOUT_FAILED',
    'SESSIONS_VIEWED_FOR_USER',
    'BULK_SESSION_CLOSE',
    'BULK_SESSION_CLOSE_FAILED',
    'SESSION_CLOSE_NOOP',
    # Access — FASE 2 (UC_PERM_05, UC_ACC_01..02, UC_ACC_04)
    'ACCESS_GROUP_CREATED',
    'ACCESS_GROUP_MODIFIED',
    'ACCESS_GROUP_RETIRED',
    'FUNCTIONS_ASSIGN_NOOP',
    'FUNCTIONS_ASSIGN_FAILED',
    'FUNCTIONS_REVOKE_NOOP',
    'FUNCTIONS_REVOKE_FAILED',
    # Users — FASE 2 (UC_USR_01..04, UC_AUTH_03)
    'USER_ELIMINATED',
    'USER_ELIMINATE_NOOP',
    'USER_ELIMINATE_FAILED',
    'USER_MODIFY_FAILED',
    'USER_PASSWORD_RESET',
    # UC_AUTH_03 — alias canónico (corpus usa PASSWORD_RESET, FASE 2 usó USER_PASSWORD_RESET)
    # Ambos se mantienen para backward compat.
    # Unauthorized
    'UNAUTHORIZED_ACCESS_ATTEMPT',
    # System
    'ACCESS_DENIED',
    'CONFIG_CHANGED',
    # FASE 4 — UC_ACC_08, UC_PERM_03/04 (Permisos excepcionales)
    'EXCEPTIONAL_PERMISSION_GRANTED',
    'EXCEPTIONAL_PERMISSION_REVOKED',
    'EXCEPTIONAL_PERMISSION_EXPIRED',
    'EXCEPTIONAL_PERMISSION_REVOKE_NOOP',
    'SELF_GRANT_FORBIDDEN_ATTEMPT',
    # FASE 4 — UC_ALR_04 (Historial alertas)
    'ALERT_HISTORY_VIEWED',
    # FASE 4 — UC_ALR_05 (Suscripciones)
    'ALERT_SUBSCRIPTION_CREATED',
    'ALERT_SUBSCRIPTION_CANCELLED',
    'ALERT_SUBSCRIPTION_UPDATED',
    'ALERT_SUBSCRIPTION_AUTO_PAUSED',
    # FASE 4 — UC_AUD_04 (Compliance report)
    'COMPLIANCE_REPORT_REQUESTED',
    # FASE 4 — UC_LOG_04 (Export logs)
    'LOG_EXPORT_QUEUED',
    'LOG_EXPORT_COMPLETED',
    'LOG_EXPORT_FAILED',
    # FASE 4 — UC_RPT_07 (Scheduled reports)
    'SCHEDULED_REPORT_CREATED',
    'SCHEDULED_REPORT_EXECUTED',
    'SCHEDULED_REPORT_FAILED',
    'SCHEDULED_REPORT_PAUSED',
    'SCHEDULED_REPORT_RESUMED',
    'SCHEDULED_REPORT_DELETED',
    'SCHEDULED_REPORT_AUTO_PAUSED',
    # FASE 4 — UC_RPT_11 (Compartir reporte)
    'REPORT_SHARE_CREATED',
    'REPORT_SHARE_APPLIED',
    'REPORT_SHARE_REVOKED',
    # FASE 4 — UC_RPT_12..17 (Reportes analíticos)
    'AGENT_DETAIL_VIEWED',
})


class AuditValidationError(Exception):
    """UC_PERM_09 CA-03: event_type desconocido → AuditValidationError."""
    pass


# PII fields que NUNCA deben aparecer en el payload de AuditEvent
# CNST-026: Sin PII directa en payload audit
_PII_FIELDS = frozenset({
    'password', 'passwd', 'password_hash', 'token', 'access_token',
    'refresh_token', 'secret', 'api_key', 'credit_card', 'cvv',
    'ssn', 'pin',
})
