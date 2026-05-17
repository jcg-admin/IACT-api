"""
Modelos para la app Dashboard.

Modelos:
- DashboardConfig: Configuración de dashboards personalizados
- WidgetConfig: Configuración de widgets dentro de dashboards
- SavedFilter: Filtros guardados para reutilización
- UserDashboardPreference: Preferencias de dashboard del usuario

FASE 1: Implementación de modelos.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.core.models import SoftDeleteMixin

User = get_user_model()


# ==============================================================================
# DASHBOARDCONFIG - Configuración de dashboard personalizado
# ==============================================================================

class DashboardConfig(SoftDeleteMixin, models.Model):
    """
    Configuración de dashboard personalizado por usuario.

    Un usuario puede tener múltiples dashboards.
    Un dashboard puede ser público (compartido) o privado.
    Solo un dashboard puede ser 'default' por usuario.

    Attributes:
        user: Usuario propietario del dashboard
        config_name: Nombre del dashboard
        description: Descripción opcional
        layout_config: Configuración de layout en JSON
        is_default: Si es el dashboard por defecto del usuario
        is_public: Si el dashboard es público (compartido)

    Example layout_config:
        {
            "columns": 12,
            "rowHeight": 100,
            "widgets": [
                {"id": 1, "x": 0, "y": 0, "w": 6, "h": 4},
                {"id": 2, "x": 6, "y": 0, "w": 6, "h": 4}
            ]
        }
    """

    # Relaciones
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='dashboards',
        verbose_name='Usuario',
        help_text='Usuario propietario del dashboard'
    )

    # Configuración
    config_name = models.CharField(
        max_length=100,
        verbose_name='Nombre',
        help_text='Nombre del dashboard'
    )

    description = models.TextField(
        blank=True,
        verbose_name='Descripción',
        help_text='Descripción del dashboard'
    )

    layout_config = models.JSONField(
        default=dict,
        verbose_name='Configuración de Layout',
        help_text='JSON con configuración de layout: columns, widgets, etc.'
    )

    # Estado
    is_default = models.BooleanField(
        default=False,
        verbose_name='Es Default',
        help_text='Si es el dashboard por defecto del usuario'
    )

    is_public = models.BooleanField(
        default=False,
        verbose_name='Es Público',
        help_text='Si el dashboard puede ser visto por otros usuarios'
    )

    # Timestamps (heredados de SoftDeleteMixin)
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Creado el'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Actualizado el'
    )

    class Meta:
        db_table = 'dashboard_config'
        verbose_name = 'Configuración de Dashboard'
        verbose_name_plural = 'Configuraciones de Dashboard'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', '-updated_at']),
            models.Index(fields=['is_default', 'user']),
            models.Index(fields=['is_public']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        default_tag = ' (default)' if self.is_default else ''
        public_tag = ' (público)' if self.is_public else ''
        return f"{self.config_name}{default_tag}{public_tag} - {self.user.username}"

    def clean(self):
        """Validar que layout_config tenga estructura básica."""
        super().clean()

        if self.layout_config and not isinstance(self.layout_config, dict):
            raise ValidationError({
                'layout_config': 'layout_config debe ser un objeto JSON (dict)'
            })


# ==============================================================================
# WIDGETCONFIG - Configuración de widget individual
# ==============================================================================

class WidgetConfig(models.Model):
    """
    Configuración de widget individual dentro de dashboard.

    Cada widget representa una visualización específica:
    - Gráficos de llamadas, transferencias, abandonos
    - Tablas de top clientes
    - Métricas resumidas (KPIs)
    - Estadísticas por hora
    - Rendimiento de agentes
    - Monitor de SLA

    Attributes:
        dashboard: Dashboard al que pertenece el widget
        widget_type: Tipo de widget (CALLS_CHART, etc.)
        widget_name: Nombre personalizado del widget
        position_x, position_y: Posición en grid
        width, height: Dimensiones en grid
        config_data: Configuración específica del widget
        is_visible: Si el widget está visible
        refresh_interval_seconds: Intervalo de actualización

    Example config_data:
        {
            "chart_type": "line",
            "metrics": ["total", "answered", "abandoned"],
            "time_range": "last_30_days",
            "filters": {
                "did": "800123456"
            }
        }
    """

    # Tipos de widgets disponibles
    WIDGET_TYPES = [
        ('CALLS_CHART', 'Gráfico de Llamadas'),
        ('TRANSFERS_CHART', 'Gráfico de Transferencias'),
        ('ABANDONMENTS_CHART', 'Gráfico de Abandonos'),
        ('TOP_CLIENTS', 'Top Clientes'),
        ('METRICS_SUMMARY', 'Resumen de Métricas'),
        ('HOURLY_STATS', 'Estadísticas por Hora'),
        ('AGENT_PERFORMANCE', 'Rendimiento de Agentes'),
        ('SLA_MONITOR', 'Monitor de SLA'),
    ]

    # Relaciones
    dashboard = models.ForeignKey(
        DashboardConfig,
        on_delete=models.CASCADE,
        related_name='widgets',
        verbose_name='Dashboard',
        help_text='Dashboard al que pertenece el widget'
    )

    # Configuración
    widget_type = models.CharField(
        max_length=50,
        choices=WIDGET_TYPES,
        verbose_name='Tipo de Widget',
        help_text='Tipo de visualización del widget'
    )

    widget_name = models.CharField(
        max_length=100,
        verbose_name='Nombre del Widget',
        help_text='Nombre personalizado para el widget'
    )

    # Posición en grid (grid de 12 columnas por defecto)
    position_x = models.IntegerField(
        default=0,
        verbose_name='Posición X',
        help_text='Posición horizontal en grid (0-11)'
    )

    position_y = models.IntegerField(
        default=0,
        verbose_name='Posición Y',
        help_text='Posición vertical en grid'
    )

    width = models.IntegerField(
        default=6,
        verbose_name='Ancho',
        help_text='Ancho en columnas de grid (1-12)'
    )

    height = models.IntegerField(
        default=4,
        verbose_name='Alto',
        help_text='Alto en unidades de grid'
    )

    # Configuración específica del widget
    config_data = models.JSONField(
        default=dict,
        verbose_name='Configuración del Widget',
        help_text='JSON con configuración: chart_type, metrics, filters, etc.'
    )

    # Estado y refresh
    is_visible = models.BooleanField(
        default=True,
        verbose_name='Visible',
        help_text='Si el widget está visible en el dashboard'
    )

    refresh_interval_seconds = models.IntegerField(
        default=300,  # 5 minutos
        verbose_name='Intervalo de Actualización',
        help_text='Intervalo de actualización automática en segundos (min: 60, max: 3600)'
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Creado el'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Actualizado el'
    )

    class Meta:
        db_table = 'widget_config'
        verbose_name = 'Configuración de Widget'
        verbose_name_plural = 'Configuraciones de Widgets'
        ordering = ['position_y', 'position_x']
        indexes = [
            models.Index(fields=['dashboard', 'position_y', 'position_x']),
            models.Index(fields=['widget_type']),
            models.Index(fields=['is_visible']),
        ]

    def __str__(self):
        return f"{self.widget_name} ({self.get_widget_type_display()}) - {self.dashboard.config_name}"

    def clean(self):
        """Validar configuración del widget."""
        super().clean()

        # Validar config_data es dict
        if self.config_data and not isinstance(self.config_data, dict):
            raise ValidationError({
                'config_data': 'config_data debe ser un objeto JSON (dict)'
            })

        # Validar dimensiones
        if self.width < 1 or self.width > 12:
            raise ValidationError({
                'width': 'El ancho debe estar entre 1 y 12'
            })

        if self.height < 1:
            raise ValidationError({
                'height': 'El alto debe ser mayor a 0'
            })

        # Validar refresh interval
        if self.refresh_interval_seconds < 60 or self.refresh_interval_seconds > 3600:
            raise ValidationError({
                'refresh_interval_seconds': 'El intervalo debe estar entre 60 y 3600 segundos'
            })


# ==============================================================================
# SAVEDFILTER - Filtro guardado para reutilización
# ==============================================================================

class SavedFilter(SoftDeleteMixin, models.Model):
    """
    Filtros guardados para reutilización rápida.

    Los usuarios pueden guardar combinaciones de filtros frecuentes:
    - Rangos de fechas
    - DIDs específicos
    - Clientes
    - Tipos de llamada
    - Agentes

    Attributes:
        user: Usuario propietario del filtro
        filter_name: Nombre del filtro
        filter_type: Tipo de filtro (CALLS, TRANSFERS, etc.)
        filter_config: Configuración del filtro en JSON
        is_public: Si el filtro es público

    Example filter_config:
        {
            "date_from": "2025-01-01",
            "date_to": "2025-01-31",
            "did": ["800123456", "800789012"],
            "call_type": "inbound",
            "agent_id": [1, 2, 3]
        }
    """

    # Tipos de filtros
    FILTER_TYPES = [
        ('CALLS', 'Llamadas'),
        ('TRANSFERS', 'Transferencias'),
        ('ABANDONED', 'Abandonadas'),
        ('CLIENTS', 'Clientes'),
        ('AGENTS', 'Agentes'),
        ('GENERAL', 'General'),
    ]

    # Relaciones
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='saved_filters',
        verbose_name='Usuario',
        help_text='Usuario propietario del filtro'
    )

    # Configuración
    filter_name = models.CharField(
        max_length=100,
        verbose_name='Nombre del Filtro',
        help_text='Nombre descriptivo del filtro'
    )

    filter_type = models.CharField(
        max_length=20,
        choices=FILTER_TYPES,
        default='GENERAL',
        verbose_name='Tipo de Filtro',
        help_text='Tipo de filtro para categorización'
    )

    filter_config = models.JSONField(
        default=dict,
        verbose_name='Configuración del Filtro',
        help_text='JSON con configuración: date_from, date_to, did, client_id, etc.'
    )

    # Compartir
    is_public = models.BooleanField(
        default=False,
        verbose_name='Es Público',
        help_text='Si el filtro puede ser usado por otros usuarios'
    )

    # Timestamps (heredados de SoftDeleteMixin)
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Creado el'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Actualizado el'
    )

    class Meta:
        db_table = 'saved_filter'
        verbose_name = 'Filtro Guardado'
        verbose_name_plural = 'Filtros Guardados'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', '-updated_at']),
            models.Index(fields=['filter_type']),
            models.Index(fields=['is_public']),
        ]

    def __str__(self):
        public_tag = ' (público)' if self.is_public else ''
        return f"{self.filter_name} ({self.get_filter_type_display()}){public_tag} - {self.user.username}"

    def clean(self):
        """Validar que filter_config tenga estructura básica."""
        super().clean()

        if self.filter_config and not isinstance(self.filter_config, dict):
            raise ValidationError({
                'filter_config': 'filter_config debe ser un objeto JSON (dict)'
            })


# ==============================================================================
# USERDASHBOARDPREFERENCE - Preferencias de dashboard del usuario
# ==============================================================================

class UserDashboardPreference(models.Model):
    """
    Preferencias de usuario para dashboards.

    Una única entrada por usuario con todas sus preferencias:
    - Dashboard por defecto
    - Tema (light/dark/auto)
    - Configuración de refresh
    - Notificaciones
    - Otras preferencias generales

    Attributes:
        user: Usuario (relación OneToOne)
        default_dashboard: Dashboard por defecto (opcional)
        theme: Tema visual
        refresh_enabled: Si el refresh automático está habilitado
        refresh_interval_seconds: Intervalo de refresh global
        show_notifications: Si muestra notificaciones
        preferences: Preferencias adicionales en JSON

    Example preferences:
        {
            "language": "es",
            "timezone": "America/Santiago",
            "date_format": "DD/MM/YYYY",
            "number_format": "es-CL"
        }
    """

    # Temas disponibles
    THEME_CHOICES = [
        ('light', 'Claro'),
        ('dark', 'Oscuro'),
        ('auto', 'Automático'),
    ]

    # Relaciones
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='dashboard_preference',
        verbose_name='Usuario',
        help_text='Usuario propietario de las preferencias'
    )

    default_dashboard = models.ForeignKey(
        DashboardConfig,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users_with_default',
        verbose_name='Dashboard por Defecto',
        help_text='Dashboard que se carga por defecto al entrar'
    )

    # Preferencias visuales
    theme = models.CharField(
        max_length=10,
        choices=THEME_CHOICES,
        default='light',
        verbose_name='Tema',
        help_text='Tema visual de la interfaz'
    )

    # Actualización automática
    refresh_enabled = models.BooleanField(
        default=True,
        verbose_name='Refresh Habilitado',
        help_text='Si el refresh automático de widgets está habilitado'
    )

    refresh_interval_seconds = models.IntegerField(
        default=300,  # 5 minutos
        verbose_name='Intervalo de Refresh Global',
        help_text='Intervalo de refresh global en segundos (min: 60, max: 3600)'
    )

    # Notificaciones
    show_notifications = models.BooleanField(
        default=True,
        verbose_name='Mostrar Notificaciones',
        help_text='Si se muestran notificaciones de alertas'
    )

    # Preferencias generales (JSON)
    preferences = models.JSONField(
        default=dict,
        verbose_name='Preferencias Adicionales',
        help_text='JSON con preferencias: language, timezone, date_format, etc.'
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Creado el'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Actualizado el'
    )

    class Meta:
        db_table = 'user_dashboard_preference'
        verbose_name = 'Preferencia de Dashboard'
        verbose_name_plural = 'Preferencias de Dashboard'

    def __str__(self):
        return f"Preferencias de {self.user.username}"

    def clean(self):
        """Validar preferencias."""
        super().clean()

        # Validar preferences es dict
        if self.preferences and not isinstance(self.preferences, dict):
            raise ValidationError({
                'preferences': 'preferences debe ser un objeto JSON (dict)'
            })

        # Validar refresh interval
        if self.refresh_interval_seconds < 60 or self.refresh_interval_seconds > 3600:
            raise ValidationError({
                'refresh_interval_seconds': 'El intervalo debe estar entre 60 y 3600 segundos'
            })

        # Validar que default_dashboard pertenezca al usuario
        if self.default_dashboard and self.default_dashboard.user != self.user:
            raise ValidationError({
                'default_dashboard': 'El dashboard por defecto debe pertenecer al mismo usuario'
            })
