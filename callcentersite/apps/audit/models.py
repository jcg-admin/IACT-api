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
