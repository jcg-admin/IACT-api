"""
Modelos app reports.

CNST-007: Límite 100,000 registros por exportación.
"""
from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import SoftDeleteMixin

User = get_user_model()


class Report(SoftDeleteMixin, models.Model):
    """
    Reporte generado en el sistema.
    
    Usa SoftDeleteMixin para delete lógico.
    
    Attributes:
        name: Nombre descriptivo del reporte
        report_type: Tipo de reporte (calls, users, audit)
        created_by: Usuario que creó el reporte
        filters: Filtros aplicados (JSON)
        total_records: Total de registros (CNST-007)
        status: Estado del reporte
    """
    
    REPORT_TYPES = [
        ('calls', 'Llamadas'),
        ('users', 'Usuarios'),
        ('audit', 'Auditoría'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
    ]
    
    # Campos básicos
    name = models.CharField(
        max_length=200,
        help_text="Nombre descriptivo del reporte"
    )
    report_type = models.CharField(
        max_length=50,
        choices=REPORT_TYPES,
        db_index=True
    )
    
    # Usuario y fechas
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reports'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )
    updated_at = models.DateTimeField(auto_now=True)
    
    # Filtros y configuración
    filters = models.JSONField(
        default=dict,
        blank=True,
        help_text="Filtros aplicados al reporte (JSON)"
    )
    
    # Metadata
    total_records = models.IntegerField(
        default=0,
        help_text="Total de registros en el reporte"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Report'
        verbose_name_plural = 'Reports'
        indexes = [
            models.Index(fields=['-created_at', 'report_type']),
            models.Index(fields=['created_by', 'status']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"


class ExportJob(SoftDeleteMixin, models.Model):
    """
    Job de exportación de reporte.
    
    CNST-007: Límite 100,000 registros por exportación.
    
    Usa SoftDeleteMixin para delete lógico.
    
    Attributes:
        report: Reporte a exportar
        format: Formato de exportación (csv, excel)
        total_records: Total registros a exportar (validar CNST-007)
        exported_records: Registros exportados (progreso)
    """
    
    FORMAT_CHOICES = [
        ('csv', 'CSV'),
        ('excel', 'Excel'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('running', 'Ejecutando'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
    ]
    
    # Relación con Report
    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name='export_jobs'
    )
    
    # Configuración export
    format = models.CharField(
        max_length=10,
        choices=FORMAT_CHOICES,
        default='csv'
    )
    file_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Ruta del archivo exportado"
    )
    
    # CNST-007: Límites
    total_records = models.IntegerField(
        help_text="Total registros a exportar (max 100K CNST-007)"
    )
    exported_records = models.IntegerField(
        default=0,
        help_text="Registros exportados (progreso)"
    )
    
    # Estado
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Inicio de la exportación"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fin de la exportación"
    )
    
    # Error info
    error_message = models.TextField(
        blank=True,
        help_text="Mensaje de error si falla"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Export Job'
        verbose_name_plural = 'Export Jobs'
        indexes = [
            models.Index(fields=['report', 'status']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"Export {self.id} - {self.report.name} ({self.format})"
    
    @property
    def progress_percentage(self):
        """Calcular porcentaje de progreso."""
        if self.total_records == 0:
            return 0
        return (self.exported_records / self.total_records) * 100


class ScheduledReport(models.Model):
    """
    Scheduled report that runs periodically. UC_RPT_07/08.
    Uses cron_expression to define the schedule.
    APScheduler (CNST-004: no Celery) picks this up at runtime.
    """
    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name='scheduled_runs',
    )
    cron_expression = models.CharField(
        max_length=50,
        help_text="Cron expression, e.g. '0 6 * * 1' for every Monday at 06:00",
    )
    is_active = models.BooleanField(default=True)
    last_run_at = models.DateTimeField(null=True, blank=True)
    next_run_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='scheduled_reports',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Scheduled Report'
        verbose_name_plural = 'Scheduled Reports'

    def __str__(self) -> str:
        return f"ScheduledReport({self.report.name}, cron={self.cron_expression})"


class SavedView(models.Model):
    """
    Saved view of a report — filters + column configuration. UC_RPT_10.
    """
    name = models.CharField(max_length=100)
    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name='saved_views',
    )
    filters = models.JSONField(
        default=dict,
        blank=True,
        help_text="Filter configuration as JSON",
    )
    columns = models.JSONField(
        default=list,
        blank=True,
        help_text="Ordered list of visible column names",
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='saved_views',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Saved View'
        verbose_name_plural = 'Saved Views'
        unique_together = [('name', 'created_by')]

    def __str__(self) -> str:
        return f"SavedView({self.name} — {self.report.name})"
