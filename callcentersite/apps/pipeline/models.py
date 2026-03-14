"""
Modelos pipeline - IACT Call Center System.

CNST-003: ETL + Analytics (PostgreSQL default DB).
CNST-004: ETL programado cada 6-12 horas (NO real-time).
CLEAN_CODE v3.0.1: Nombres auto-documentados, docstrings completos.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal

from apps.core.models import SoftDeleteMixin
from apps.utils.validators import (
    validate_phone_number,
    validate_service_800,
    validate_codigo_center,
)

User = get_user_model()


# ============================================================================
# ETL EXECUTION MODEL
# ============================================================================

class ETLExecution(models.Model):
    """
    Registro de ejecucion ETL.
    
    CNST-004: ETL programado cada 6-12 horas (NO real-time).
    
    Tracking de:
    - Rango de fechas procesadas
    - Status de ejecucion
    - Registros procesados
    - Errores si ocurrieron
    """
    
    # Rango de datos procesados
    start_date = models.DateField(
        verbose_name='Fecha inicio'
    )
    end_date = models.DateField(
        verbose_name='Fecha fin'
    )
    
    # Status ejecucion
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pendiente'),
            ('RUNNING', 'Ejecutando'),
            ('SUCCESS', 'Exitoso'),
            ('FAILED', 'Fallido'),
        ],
        default='PENDING',
        verbose_name='Estado',
    )
    
    # Metricas
    records_extracted = models.IntegerField(
        default=0,
        verbose_name='Registros extraidos',
        help_text='Cantidad de registros extraidos de IVR',
    )
    records_loaded = models.IntegerField(
        default=0,
        verbose_name='Registros cargados',
        help_text='Cantidad de registros cargados en Analytics',
    )
    
    # Timestamps
    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Iniciado',
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Completado',
    )
    
    # Error tracking
    error_message = models.TextField(
        blank=True,
        verbose_name='Mensaje de error',
    )
    
    class Meta:
        db_table = 'etl_executions'
        verbose_name = 'Ejecucion ETL'
        verbose_name_plural = 'Ejecuciones ETL'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['-started_at']),
            models.Index(fields=['status', '-started_at']),
        ]
    
    def __str__(self):
        return f"ETL {self.start_date} to {self.end_date} - {self.status}"


# ============================================================================
# CENTER MODEL (Moved from apps/core/)
# ============================================================================

class Center(SoftDeleteMixin, models.Model):
    """
    Centro de atención telefónica.
    
    Representa un centro físico de call center donde se atienden llamadas.
    Cada centro puede tener múltiples servicios 800 asociados.
    
    Relaciones:
        - services (1:N): Servicios 800 del centro
    
    Soft Delete: Sí (usa SoftDeleteMixin)
    
    Ejemplo:
        >>> center = Center.objects.create(
        ...     nombre='Centro Santiago',
        ...     codigo='CT_SCL',
        ...     activo=True
        ... )
    """
    
    nombre = models.CharField(
        max_length=200,
        help_text='Nombre del centro de atención'
    )
    
    codigo = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        validators=[validate_codigo_center],
        help_text='Código único del centro (ej: CT01, CENTER_SCL)'
    )
    
    descripcion = models.TextField(
        blank=True,
        help_text='Descripción del centro'
    )
    
    direccion = models.CharField(
        max_length=500,
        blank=True,
        help_text='Dirección física del centro'
    )
    
    activo = models.BooleanField(
        default=True,
        db_index=True,
        help_text='¿Centro actualmente operativo?'
    )
    
    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Fecha de creación'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='Última actualización'
    )
    
    class Meta:
        db_table = 'core_centers'  # [SUCCESS] PRESERVADO - no cambiar
        ordering = ['nombre']
        verbose_name = 'Centro'
        verbose_name_plural = 'Centros'
        indexes = [
            models.Index(fields=['activo', 'codigo']),
        ]
    
    def __str__(self):
        """Representación string del centro."""
        return f"{self.codigo} - {self.nombre}"
    
    def get_active_services_count(self):
        """
        Obtener cantidad de servicios activos del centro.
        
        Returns:
            int: Número de servicios activos
        """
        return self.services.filter(activo=True).count()
    
    def deactivate(self):
        """
        Desactivar centro y todos sus servicios.
        
        Returns:
            tuple: (center, services_count)
        """
        services_count = self.services.filter(activo=True).update(activo=False)
        self.activo = False
        self.save()
        return self, services_count


# ============================================================================
# SERVICE MODEL (Moved from apps/core/)
# ============================================================================

class Service(SoftDeleteMixin, models.Model):
    """
    Servicio telefónico 800.
    
    Representa un número de servicio 800 asociado a un centro.
    Los usuarios pueden tener acceso segmentado por servicio.
    
    Relaciones:
        - center (N:1): Centro al que pertenece
        - user_accesses (1:N): Usuarios con acceso
    
    Soft Delete: Sí (usa SoftDeleteMixin)
    
    Ejemplo:
        >>> service = Service.objects.create(
        ...     numero_800='800-123-4567',
        ...     nombre='Soporte Técnico',
        ...     center=center,
        ...     activo=True
        ... )
    """
    
    numero_800 = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        validators=[validate_service_800],
        help_text='Número servicio 800 (ej: 800-123-4567)'
    )
    
    nombre = models.CharField(
        max_length=200,
        help_text='Nombre del servicio'
    )
    
    descripcion = models.TextField(
        blank=True,
        help_text='Descripción del servicio'
    )
    
    center = models.ForeignKey(
        'Center',  # [SUCCESS] Ahora en la misma app
        on_delete=models.PROTECT,
        related_name='services',
        help_text='Centro al que pertenece el servicio'
    )
    
    activo = models.BooleanField(
        default=True,
        db_index=True,
        help_text='¿Servicio actualmente operativo?'
    )
    
    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Fecha de creación'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='Última actualización'
    )
    
    class Meta:
        db_table = 'core_services'  # [SUCCESS] PRESERVADO - no cambiar
        ordering = ['numero_800']
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'
        indexes = [
            models.Index(fields=['activo', 'numero_800']),
            models.Index(fields=['center', 'activo']),
        ]
    
    def __str__(self):
        """Representación string del servicio."""
        return f"{self.numero_800} - {self.nombre}"


# ============================================================================
# CALLRECORD MODEL (Moved from apps/core/)
# ============================================================================

class CallRecord(SoftDeleteMixin, models.Model):
    """
    Registro de llamadas procesado.
    
    Almacena datos agregados por fecha/teléfono/servicio.
    Base de datos: default (PostgreSQL analytics).
    
    CNST-003: Este modelo usa 'default' DB (PostgreSQL).
    NO usa 'ivr_legacy' (MariaDB READ-ONLY).
    
    Propósito: Output del proceso ETL.
    Pipeline lee datos de apps/ivr/ (MariaDB readonly),
    procesa y agrega datos, y los escribe aquí (PostgreSQL).
    
    Soft Delete: Sí (usa SoftDeleteMixin)
    
    Ejemplo:
        >>> record = CallRecord.objects.create(
        ...     fecha=date(2025, 1, 15),
        ...     telefono='912345678',
        ...     servicio_800='800-123-4567',
        ...     total_llamadas=100,
        ...     llamadas_contestadas=85,
        ...     llamadas_abandonadas=15
        ... )
        >>> record.answer_rate()
        Decimal('85.00')
    """
    
    fecha = models.DateField(
        db_index=True,
        help_text='Fecha de las llamadas'
    )
    
    telefono = models.CharField(
        max_length=20,
        db_index=True,
        validators=[validate_phone_number],
        help_text='Número telefónico que realizó llamadas'
    )
    
    servicio_800 = models.CharField(
        max_length=20,
        db_index=True,
        validators=[validate_service_800],
        help_text='Número servicio 800 destino'
    )
    
    total_llamadas = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Total de llamadas realizadas'
    )
    
    llamadas_contestadas = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Llamadas contestadas por agente'
    )
    
    llamadas_abandonadas = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Llamadas abandonadas (colgadas antes de contestar)'
    )
    
    duracion_total_segundos = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Duración total en segundos'
    )
    
    # ============================================================================
    # CAMPOS ADICIONALES (FASE 0.2)
    # Agregados para enriquecer información de llamadas
    # Todos NULL/BLANK para compatibilidad con datos legacy
    # ============================================================================
    
    agent = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='call_records_as_agent',
        help_text='Agente que atendió la llamada (si aplica)',
        verbose_name='Agente'
    )
    
    call_type = models.CharField(
        max_length=20,
        choices=[
            ('INBOUND', 'Entrante'),
            ('OUTBOUND', 'Saliente'),
            ('INTERNAL', 'Interna'),
            ('UNKNOWN', 'Desconocido'),
        ],
        default='UNKNOWN',
        help_text='Tipo de llamada',
        verbose_name='Tipo de llamada'
    )
    
    recording_path = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text='Ruta de archivo de grabación (si existe)',
        verbose_name='Ruta grabación'
    )
    
    service = models.ForeignKey(
        'Service',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='call_records',
        help_text='Servicio asociado (si existe en tabla Service)',
        verbose_name='Servicio'
    )
    
    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Timestamp creación registro'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='Timestamp última actualización'
    )
    
    class Meta:
        db_table = 'core_call_records'  # [SUCCESS] PRESERVADO - no cambiar
        ordering = ['-fecha', '-created_at']
        unique_together = [['fecha', 'telefono', 'servicio_800']]
        indexes = [
            models.Index(fields=['fecha', 'servicio_800']),
            models.Index(fields=['fecha', 'telefono']),
            models.Index(fields=['-fecha', '-total_llamadas']),
            # FASE 0.2: Índices para campos adicionales
            models.Index(fields=['agent', 'fecha']),
            models.Index(fields=['call_type', 'fecha']),
        ]
        verbose_name = 'Registro de Llamada'
        verbose_name_plural = 'Registros de Llamadas'
    
    def __str__(self):
        """Representación string del registro."""
        return f"{self.fecha} - {self.telefono} -> {self.servicio_800}"
    
    def clean(self):
        """
        Validación del modelo.
        
        Valida que:
        - total_llamadas >= llamadas_contestadas + llamadas_abandonadas
        """
        from django.core.exceptions import ValidationError
        
        # Validar consistencia de llamadas
        sum_calls = self.llamadas_contestadas + self.llamadas_abandonadas
        if sum_calls > self.total_llamadas:
            raise ValidationError(
                'La suma de llamadas contestadas y abandonadas no puede '
                'ser mayor al total de llamadas.'
            )
    
    def answer_rate(self):
        """
        Calcular porcentaje de respuesta.
        
        Returns:
            Decimal: Porcentaje de llamadas contestadas (0-100)
        
        Examples:
            >>> record.total_llamadas = 100
            >>> record.llamadas_contestadas = 85
            >>> record.answer_rate()
            Decimal('85.00')
        """
        if self.total_llamadas == 0:
            return Decimal('0.00')
        
        rate = (Decimal(self.llamadas_contestadas) / 
                Decimal(self.total_llamadas)) * 100
        return rate.quantize(Decimal('0.01'))
    
    def abandonment_rate(self):
        """
        Calcular porcentaje de abandono.
        
        Returns:
            Decimal: Porcentaje de llamadas abandonadas (0-100)
        
        Examples:
            >>> record.total_llamadas = 100
            >>> record.llamadas_abandonadas = 15
            >>> record.abandonment_rate()
            Decimal('15.00')
        """
        if self.total_llamadas == 0:
            return Decimal('0.00')
        
        rate = (Decimal(self.llamadas_abandonadas) / 
                Decimal(self.total_llamadas)) * 100
        return rate.quantize(Decimal('0.01'))
    
    def avg_duration_seconds(self):
        """
        Calcular duración promedio por llamada.
        
        Returns:
            Decimal: Duración promedio en segundos
        """
        if self.llamadas_contestadas == 0:
            return Decimal('0.00')
        
        avg = (Decimal(self.duracion_total_segundos) / 
               Decimal(self.llamadas_contestadas))
        return avg.quantize(Decimal('0.01'))


# ============================================================================
# CALLNOTE MODEL (FASE 0.2)
# ============================================================================

class CallNote(SoftDeleteMixin, models.Model):
    """
    Nota o comentario sobre un CallRecord.
    
    Permite a usuarios agregar notas/observaciones DESPUÉS de 
    procesar la llamada (NO tiempo real).
    
    CNST-003: NO viola porque:
    - Se agrega DESPUÉS de la llamada (batch)
    - Usuario agrega manualmente (no automático)
    - No requiere WebSockets/SSE
    
    Relaciones:
        - call_record (N:1): Registro de llamada asociado
        - user (N:1): Usuario que creó la nota
    
    Soft Delete: Sí (usa SoftDeleteMixin)
    
    Ejemplo:
        >>> record = CallRecord.objects.get(id=1)
        >>> note = CallNote.objects.create(
        ...     call_record=record,
        ...     user=request.user,
        ...     note='Cliente reportó problema con facturación',
        ...     is_important=True
        ... )
    """
    
    call_record = models.ForeignKey(
        CallRecord,
        on_delete=models.CASCADE,
        related_name='notes',
        help_text='Registro de llamada asociado',
        verbose_name='Registro de llamada'
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='pipeline_call_notes',
        help_text='Usuario que creó la nota',
        verbose_name='Usuario'
    )
    
    note = models.TextField(
        help_text='Contenido de la nota',
        verbose_name='Nota'
    )
    
    is_important = models.BooleanField(
        default=False,
        help_text='Marcar como importante',
        verbose_name='¿Es importante?'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Fecha de creación',
        verbose_name='Creado'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='Última actualización',
        verbose_name='Actualizado'
    )
    
    class Meta:
        db_table = 'pipeline_call_notes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['call_record', '-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['is_important', '-created_at']),
        ]
        verbose_name = 'Nota de Llamada'
        verbose_name_plural = 'Notas de Llamadas'
    
    def __str__(self):
        """Representación string del registro."""
        return f"Nota de {self.user.username} en {self.call_record}"
