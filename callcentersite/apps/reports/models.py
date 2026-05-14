"""
Modelos app reports.

CNST-007: Límite 100,000 registros por exportación.
"""
import uuid as _uuid

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
    Job de exportación de reporte — modelo canónico UC_RPT_04.

    Fuente: uc-rpt-04/datos-involucrados.rst § 7.1
    Patrón Larman async: POST → 202 + job_id, worker procesa en background.

    BR-009: no DELETE físico — baja lógica vía status=cancelled/expired.
    CNST-001: notificación vía InternalMailbox (no email externo).
    CNST-007: límite 1M filas (CA-07), 200 MB (CA-10).
    P-64: re-check de permiso al ejecutar el worker (CA-09).

    Migración: 0004_fase3_exportjob_canonical.py
    """

    STATUS_QUEUED    = 'queued'
    STATUS_RUNNING   = 'running'
    STATUS_DONE      = 'done'
    STATUS_FAILED    = 'failed'
    STATUS_EXPIRED   = 'expired'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_QUEUED,    'En cola'),
        (STATUS_RUNNING,   'Ejecutando'),
        (STATUS_DONE,      'Completado'),
        (STATUS_FAILED,    'Fallido'),
        (STATUS_EXPIRED,   'Expirado'),
        (STATUS_CANCELLED, 'Cancelado'),
    ]

    FORMAT_CHOICES = [
        ('csv',  'CSV'),
        ('xlsx', 'Excel'),
        ('json', 'JSON'),
        ('pdf',  'PDF'),
    ]

    VALID_REPORT_TYPES = {
        'call_summary', 'agent_performance', 'queue_stats',
        'campaign_summary', 'ivr_navigation', 'audit_export',
    }

    # --- Identidad ---
    id              = models.UUIDField(
        primary_key=True, default=_uuid.uuid4, editable=False,
        verbose_name='ID',
    )
    actor           = models.ForeignKey(
        User, on_delete=models.PROTECT,
        related_name='export_jobs',
        null=True, blank=True,            # nullable para registros legacy pre-UC_RPT_04
        verbose_name='Actor',
        help_text='Usuario que solicitó la exportación. Obligatorio para UC_RPT_04.',
    )

    # --- Parámetros de consulta (inmutables tras creación) ---
    report_type     = models.CharField(
        max_length=50, verbose_name='Tipo de reporte',
        null=True, blank=True,            # nullable para registros legacy
        help_text='Enum: ' + ', '.join(sorted(VALID_REPORT_TYPES)),
    )
    filters         = models.JSONField(default=dict, verbose_name='Filtros')
    period          = models.JSONField(default=dict, verbose_name='Período')
    group_by        = models.JSONField(default=list, verbose_name='Agrupar por')
    format          = models.CharField(
        max_length=10, choices=FORMAT_CHOICES, default='csv',
        verbose_name='Formato',
    )

    # --- Estado ---
    status          = models.CharField(
        max_length=15, choices=STATUS_CHOICES,
        default=STATUS_QUEUED, db_index=True,
        verbose_name='Estado',
    )
    progress_pct    = models.PositiveSmallIntegerField(
        default=0, verbose_name='Progreso (%)',
        help_text='0..100.',
    )
    cancellation_requested = models.BooleanField(
        default=False, verbose_name='Cancelación solicitada',
        help_text='True cuando se hace DELETE durante status=running.',
    )

    # --- Resultado ---
    file_path       = models.CharField(
        max_length=500, blank=True, verbose_name='Ruta de archivo',
    )
    file_url        = models.CharField(
        max_length=2000, blank=True, null=True,
        verbose_name='URL firmado',
        help_text='URL con TTL 24h (CA-12).',
    )
    file_url_expires_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name='URL expira en',
        help_text='Timestamp de expiración de file_url.',
    )
    row_count       = models.PositiveIntegerField(
        null=True, blank=True, verbose_name='Filas',
    )
    byte_count      = models.PositiveIntegerField(
        null=True, blank=True, verbose_name='Bytes',
    )
    error_code      = models.CharField(
        max_length=50, blank=True, null=True,
        verbose_name='Código de error',
        help_text='PERMISSION_REVOKED | TOO_LARGE | STORAGE_UNAVAILABLE | BD_TIMEOUT | …',
    )

    # --- Timestamps ---
    created_at      = models.DateTimeField(auto_now_add=True, verbose_name='Creado')
    completed_at    = models.DateTimeField(
        null=True, blank=True, verbose_name='Completado en',
    )

    # --- Backward compat: campos legacy (preservados para legacy ExportJobViewSet) ---
    report          = models.ForeignKey(
        Report, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='export_jobs',
        verbose_name='Reporte legacy',
        help_text='FK legacy — null para jobs UC_RPT_04.',
    )
    total_records   = models.IntegerField(
        null=True, blank=True,
        help_text='Legacy. Usar row_count para UC_RPT_04.',
    )
    exported_records = models.IntegerField(
        default=0,
        help_text='Legacy. Usar progress_pct para UC_RPT_04.',
    )
    error_message   = models.TextField(
        blank=True,
        help_text='Legacy. Usar error_code para UC_RPT_04.',
    )
    started_at      = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'reports_exportjob'
        verbose_name = 'Export Job'
        verbose_name_plural = 'Export Jobs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['actor', 'status'], name='idx_expjob_actor_status'),
            models.Index(fields=['-created_at'], name='idx_expjob_created'),
            models.Index(fields=['status', 'file_url_expires_at'],
                         name='idx_expjob_status_expiry'),
        ]

    def __str__(self) -> str:
        return f'ExportJob({self.report_type}/{self.format}/{self.status})'

    @property
    def is_active(self) -> bool:
        """True si el job está en un estado que cuenta para el límite de 5 simultáneos."""
        return self.status in (self.STATUS_QUEUED, self.STATUS_RUNNING)
    
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
    Reporte programado periódico — UC_RPT_07/08.

    Fuente: uc-rpt-07/criterios-aceptacion.rst
    Fuente: uc-rpt-08/criterios-aceptacion.rst
    Patrón: cada tick del scheduler verifica next_run_at y encola ExportJob.
    BR-009: no DELETE físico — status=deleted.
    """

    STATUS_ACTIVE      = 'active'
    STATUS_PAUSED      = 'paused'
    STATUS_AUTO_PAUSED = 'auto_paused'  # CA-10: 3 fallos consecutivos
    STATUS_DELETED     = 'deleted'

    STATUS_CHOICES = [
        (STATUS_ACTIVE,      'Activo'),
        (STATUS_PAUSED,      'Pausado'),
        (STATUS_AUTO_PAUSED, 'Auto-pausado'),
        (STATUS_DELETED,     'Eliminado'),
    ]

    FREQ_DAILY   = 'daily'
    FREQ_WEEKLY  = 'weekly'
    FREQ_MONTHLY = 'monthly'
    FREQ_CRON    = 'cron'

    FREQ_CHOICES = [
        (FREQ_DAILY,   'Diario'),
        (FREQ_WEEKLY,  'Semanal'),
        (FREQ_MONTHLY, 'Mensual'),
        (FREQ_CRON,    'Expresión cron personalizada'),
    ]

    actor = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='scheduled_reports',
        null=True, blank=True,       # nullable para registros legacy sin actor
        verbose_name='Actor',
        help_text='Usuario que programó el reporte. Obligatorio para UC_RPT_07.',
    )
    report_type = models.CharField(
        max_length=50, verbose_name='Tipo de reporte',
        blank=True, default='',
        help_text='Mismo enum que ExportJob.report_type.',
    )
    format = models.CharField(
        max_length=10, default='csv',
        choices=[('csv','CSV'),('xlsx','Excel'),('json','JSON'),('pdf','PDF')],
    )
    filters  = models.JSONField(default=dict)
    group_by = models.JSONField(default=list)

    # Programación
    frequency      = models.CharField(max_length=15, choices=FREQ_CHOICES, default=FREQ_DAILY)
    cron_expression = models.CharField(
        max_length=100, blank=True,
        help_text="'0 6 * * 1' — solo para frequency=cron (CA-04).",
    )
    day_of_week  = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text='0=lunes … 6=domingo — solo para frequency=weekly (CA-02).',
    )
    day_of_month = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text='1..31 — solo para frequency=monthly (CA-03).',
    )
    run_at_hour   = models.PositiveSmallIntegerField(default=6,
        help_text='Hora local de ejecución (0..23).')
    run_at_minute = models.PositiveSmallIntegerField(default=0)

    # Estado
    status         = models.CharField(
        max_length=15, choices=STATUS_CHOICES,
        default=STATUS_ACTIVE, db_index=True,
    )
    next_run_at    = models.DateTimeField(null=True, blank=True, db_index=True)
    last_run_at    = models.DateTimeField(null=True, blank=True)
    failure_count  = models.PositiveSmallIntegerField(
        default=0,
        help_text='Fallos consecutivos. ≥3 → auto_paused (CA-10).',
    )
    auto_paused_at = models.DateTimeField(null=True, blank=True)
    last_job       = models.ForeignKey(
        'ExportJob',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='scheduled_source',
    )

    # Backward compat — FK legacy a Report (nullable)
    report = models.ForeignKey(
        Report,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='scheduled_runs',
        verbose_name='Reporte legacy',
    )
    cron_expr_legacy = models.CharField(
        max_length=50, blank=True,
        help_text='Legacy field — usar cron_expression.',
    )
    is_active = models.BooleanField(
        default=True, help_text='Legacy — usar status.',
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='scheduled_reports_legacy',
        help_text='Legacy — usar actor.',
    )

    created_at = models.DateTimeField(auto_now_add=True)

    MAX_SCHEDULES_PER_USER = 10  # CA-07: 11ª → 429

    class Meta:
        db_table = 'reports_scheduledreport'
        verbose_name = 'Scheduled Report'
        verbose_name_plural = 'Scheduled Reports'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['actor', 'status'], name='idx_schedrpt_actor_status'),
            models.Index(fields=['next_run_at', 'status'], name='idx_schedrpt_next_run'),
        ]

    def __str__(self) -> str:
        return f'ScheduledReport({self.report_type}/{self.frequency}/{self.status})'


class SavedView(models.Model):
    """
    Vista guardada de un reporte — UC_RPT_10.

    Fuente: uc-rpt-10/criterios-aceptacion.rst
    Almacena: filters + columns + chart_config por report_type.
    Límite: 30 vistas por usuario (CA-04).
    """

    actor       = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='saved_views', null=True, blank=True,
        help_text='UC_RPT_10 canonical actor. Null para registros legacy.',
    )
    name        = models.CharField(max_length=100)
    report_type = models.CharField(max_length=50, blank=True, default='')
    filters     = models.JSONField(default=dict, blank=True)
    columns     = models.JSONField(default=list, blank=True)
    chart_config= models.JSONField(default=dict, blank=True)
    is_default  = models.BooleanField(
        default=False,
        help_text='CA-05: único is_default por report_type por usuario.',
    )
    is_available = models.BooleanField(
        default=True,
        help_text='CA-08: False si alguna columna fue deprecada.',
    )
    # Backward compat
    report     = models.ForeignKey(
        Report, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='saved_views', verbose_name='Reporte legacy',
    )
    created_by  = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='saved_views_legacy', null=True, blank=True,
        help_text='Legacy — usar actor.',
    )
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    MAX_VIEWS_PER_USER = 30  # CA-04

    class Meta:
        ordering         = ['-created_at']
        verbose_name     = 'Saved View'
        verbose_name_plural = 'Saved Views'
        db_table         = 'reports_savedview'
        indexes          = [
            models.Index(fields=['actor', 'report_type'], name='idx_savedview_actor_type'),
        ]

    def __str__(self) -> str:
        return f'SavedView({self.name}/{self.report_type})'


class SavedFilter(models.Model):
    """
    Filtro guardado para reportes — UC_RPT_09.

    Fuente: uc-rpt-09/criterios-aceptacion.rst
    Límite: 50 filtros por usuario (CA-04).
    """

    actor       = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='report_saved_filters',   # prefijo 'report_' para evitar colisión con dashboard.SavedFilter
    )
    name        = models.CharField(max_length=100)
    report_type = models.CharField(
        max_length=50, blank=True,
        help_text='Tipo de reporte al que aplica (CA-09: default único por tipo).',
    )
    applies_to  = models.JSONField(
        default=list,
        help_text='Lista de report_types a los que aplica este filtro.',
    )
    filters     = models.JSONField(default=dict, blank=True)
    is_default  = models.BooleanField(
        default=False,
        help_text='CA-09: único is_default por report_type por usuario.',
    )
    is_valid    = models.BooleanField(
        default=True,
        help_text='CA-10: False si el usuario pierde el segmento requerido.',
    )
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    MAX_FILTERS_PER_USER = 50  # CA-04

    class Meta:
        ordering            = ['-created_at']
        verbose_name        = 'Saved Filter'
        verbose_name_plural = 'Saved Filters'
        db_table            = 'reports_savedfilter'
        indexes             = [
            models.Index(fields=['actor', 'report_type'], name='idx_savedfilter_actor_type'),
        ]

    def __str__(self) -> str:
        return f'SavedFilter({self.actor.username}/{self.name})'
