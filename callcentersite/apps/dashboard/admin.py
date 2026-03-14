"""
Configuración del Django Admin para la app Dashboard.

Admin classes:
- DashboardConfigAdmin (con WidgetConfigInline)
- WidgetConfigAdmin
- SavedFilterAdmin
- UserDashboardPreferenceAdmin

FASE 9: Integración con Django Admin.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from apps.dashboard.models import (
    DashboardConfig,
    WidgetConfig,
    SavedFilter,
    UserDashboardPreference
)


# ==============================================================================
# INLINE ADMIN
# ==============================================================================

class WidgetConfigInline(admin.TabularInline):
    """
    Inline para widgets dentro de dashboard.
    
    Permite agregar/editar widgets directamente desde el dashboard.
    """
    model = WidgetConfig
    extra = 0
    fields = [
        'widget_type',
        'widget_name',
        'position_x',
        'position_y',
        'width',
        'height',
        'is_visible'
    ]
    readonly_fields = []
    
    def get_queryset(self, request):
        """Optimizar queryset."""
        qs = super().get_queryset(request)
        return qs.select_related('dashboard')


# ==============================================================================
# MODEL ADMIN
# ==============================================================================

@admin.register(DashboardConfig)
class DashboardConfigAdmin(admin.ModelAdmin):
    """
    Admin para DashboardConfig.
    
    Features:
    - Inline de widgets
    - Filtros por usuario, público, default
    - Búsqueda por nombre
    - Acciones custom (marcar_default, marcar_publico)
    """
    
    list_display = [
        'id',
        'config_name',
        'user_link',
        'widget_count',
        'is_default_badge',
        'is_public_badge',
        'created_at',
        'updated_at'
    ]
    
    list_filter = [
        'is_default',
        'is_public',
        'created_at',
        'updated_at'
    ]
    
    search_fields = [
        'config_name',
        'description',
        'user__username',
        'user__email'
    ]
    
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'deleted_at',
        'widget_count'
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'id',
                'user',
                'config_name',
                'description'
            )
        }),
        ('Configuración', {
            'fields': (
                'layout_config',
                'is_default',
                'is_public'
            )
        }),
        ('Metadata', {
            'fields': (
                'created_at',
                'updated_at',
                'deleted_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    inlines = [WidgetConfigInline]
    
    actions = ['marcar_como_default', 'marcar_como_publico', 'marcar_como_privado']
    
    def get_queryset(self, request):
        """Optimizar queryset."""
        qs = super().get_queryset(request)
        return qs.select_related('user').prefetch_related('widgets')
    
    def user_link(self, obj):
        """Link al usuario propietario."""
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'Usuario'
    
    def widget_count(self, obj):
        """Contador de widgets."""
        count = obj.widgets.count()
        return format_html('<strong>{}</strong>', count)
    widget_count.short_description = 'Widgets'
    
    def is_default_badge(self, obj):
        """Badge para is_default."""
        if obj.is_default:
            return format_html(
                '<span style="background-color: #28a745; color: white; '
                'padding: 3px 8px; border-radius: 3px;">Default</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; '
            'padding: 3px 8px; border-radius: 3px;">No</span>'
        )
    is_default_badge.short_description = 'Default'
    
    def is_public_badge(self, obj):
        """Badge para is_public."""
        if obj.is_public:
            return format_html(
                '<span style="background-color: #007bff; color: white; '
                'padding: 3px 8px; border-radius: 3px;">Público</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; '
            'padding: 3px 8px; border-radius: 3px;">Privado</span>'
        )
    is_public_badge.short_description = 'Visibilidad'
    
    def marcar_como_default(self, request, queryset):
        """Acción: marcar como default."""
        for dashboard in queryset:
            # Desmarcar otros dashboards del mismo usuario
            DashboardConfig.objects.filter(
                user=dashboard.user,
                is_default=True
            ).exclude(id=dashboard.id).update(is_default=False)
            
            # Marcar este como default
            dashboard.is_default = True
            dashboard.save()
        
        self.message_user(
            request,
            f'{queryset.count()} dashboard(s) marcado(s) como default'
        )
    marcar_como_default.short_description = 'Marcar como default'
    
    def marcar_como_publico(self, request, queryset):
        """Acción: marcar como público."""
        updated = queryset.update(is_public=True)
        self.message_user(
            request,
            f'{updated} dashboard(s) marcado(s) como público(s)'
        )
    marcar_como_publico.short_description = 'Marcar como público'
    
    def marcar_como_privado(self, request, queryset):
        """Acción: marcar como privado."""
        updated = queryset.update(is_public=False)
        self.message_user(
            request,
            f'{updated} dashboard(s) marcado(s) como privado(s)'
        )
    marcar_como_privado.short_description = 'Marcar como privado'


@admin.register(WidgetConfig)
class WidgetConfigAdmin(admin.ModelAdmin):
    """
    Admin para WidgetConfig.
    
    Features:
    - Filtros por tipo, dashboard, visibilidad
    - Búsqueda por nombre
    - Vista de configuración JSON
    """
    
    list_display = [
        'id',
        'widget_name',
        'widget_type_badge',
        'dashboard_link',
        'position_display',
        'size_display',
        'is_visible_badge',
        'created_at'
    ]
    
    list_filter = [
        'widget_type',
        'is_visible',
        'created_at'
    ]
    
    search_fields = [
        'widget_name',
        'dashboard__config_name',
        'dashboard__user__username'
    ]
    
    readonly_fields = [
        'id',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'id',
                'dashboard',
                'widget_type',
                'widget_name'
            )
        }),
        ('Posición y Tamaño', {
            'fields': (
                ('position_x', 'position_y'),
                ('width', 'height')
            )
        }),
        ('Configuración', {
            'fields': (
                'config_data',
                'is_visible',
                'refresh_interval_seconds'
            )
        }),
        ('Metadata', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        """Optimizar queryset."""
        qs = super().get_queryset(request)
        return qs.select_related('dashboard', 'dashboard__user')
    
    def dashboard_link(self, obj):
        """Link al dashboard padre."""
        url = reverse('admin:dashboard_dashboardconfig_change', args=[obj.dashboard.id])
        return format_html('<a href="{}">{}</a>', url, obj.dashboard.config_name)
    dashboard_link.short_description = 'Dashboard'
    
    def widget_type_badge(self, obj):
        """Badge con color por tipo de widget."""
        colors = {
            'METRICS_SUMMARY': '#28a745',
            'CALLS_CHART': '#007bff',
            'TRANSFERS_CHART': '#17a2b8',
            'RESPONSE_TIME_CHART': '#ffc107',
            'ABANDONMENT_CHART': '#dc3545',
            'RECENT_CALLS_TABLE': '#6c757d',
            'TOP_DIDS_TABLE': '#fd7e14',
            'CUSTOM': '#6f42c1'
        }
        color = colors.get(obj.widget_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_widget_type_display()
        )
    widget_type_badge.short_description = 'Tipo'
    
    def position_display(self, obj):
        """Display de posición."""
        return f'({obj.position_x}, {obj.position_y})'
    position_display.short_description = 'Posición (x,y)'
    
    def size_display(self, obj):
        """Display de tamaño."""
        return f'{obj.width} × {obj.height}'
    size_display.short_description = 'Tamaño'
    
    def is_visible_badge(self, obj):
        """Badge para is_visible."""
        if obj.is_visible:
            return format_html(
                '<span style="color: #28a745;">[OK] Visible</span>'
            )
        return format_html(
            '<span style="color: #dc3545;">[FAIL] Oculto</span>'
        )
    is_visible_badge.short_description = 'Visible'


@admin.register(SavedFilter)
class SavedFilterAdmin(admin.ModelAdmin):
    """
    Admin para SavedFilter.
    
    Features:
    - Filtros por tipo, usuario, público
    - Búsqueda por nombre
    """
    
    list_display = [
        'id',
        'filter_name',
        'filter_type_badge',
        'user_link',
        'is_public_badge',
        'created_at'
    ]
    
    list_filter = [
        'filter_type',
        'is_public',
        'created_at'
    ]
    
    search_fields = [
        'filter_name',
        'user__username',
        'user__email'
    ]
    
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'deleted_at'
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'id',
                'user',
                'filter_name',
                'filter_type'
            )
        }),
        ('Configuración', {
            'fields': (
                'filter_config',
                'is_public'
            )
        }),
        ('Metadata', {
            'fields': (
                'created_at',
                'updated_at',
                'deleted_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        """Optimizar queryset."""
        qs = super().get_queryset(request)
        return qs.select_related('user')
    
    def user_link(self, obj):
        """Link al usuario propietario."""
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'Usuario'
    
    def filter_type_badge(self, obj):
        """Badge para tipo de filtro."""
        colors = {
            'call': '#007bff',
            'transfer': '#17a2b8',
            'custom': '#6f42c1'
        }
        color = colors.get(obj.filter_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_filter_type_display()
        )
    filter_type_badge.short_description = 'Tipo'
    
    def is_public_badge(self, obj):
        """Badge para is_public."""
        if obj.is_public:
            return format_html(
                '<span style="background-color: #007bff; color: white; '
                'padding: 3px 8px; border-radius: 3px;">Público</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; '
            'padding: 3px 8px; border-radius: 3px;">Privado</span>'
        )
    is_public_badge.short_description = 'Visibilidad'


@admin.register(UserDashboardPreference)
class UserDashboardPreferenceAdmin(admin.ModelAdmin):
    """
    Admin para UserDashboardPreference.
    
    Features:
    - Filtros por tema, refresh
    - Búsqueda por usuario
    """
    
    list_display = [
        'id',
        'user_link',
        'default_dashboard_link',
        'theme_badge',
        'refresh_enabled_badge',
        'show_notifications_badge'
    ]
    
    list_filter = [
        'theme',
        'refresh_enabled',
        'show_notifications'
    ]
    
    search_fields = [
        'user__username',
        'user__email'
    ]
    
    readonly_fields = [
        'id',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Usuario', {
            'fields': (
                'id',
                'user',
                'default_dashboard'
            )
        }),
        ('Preferencias de Visualización', {
            'fields': (
                'theme',
                'show_notifications'
            )
        }),
        ('Preferencias de Actualización', {
            'fields': (
                'refresh_enabled',
                'refresh_interval_seconds'
            )
        }),
        ('Configuración Adicional', {
            'fields': (
                'preferences',
            )
        }),
        ('Metadata', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        """Optimizar queryset."""
        qs = super().get_queryset(request)
        return qs.select_related('user', 'default_dashboard')
    
    def user_link(self, obj):
        """Link al usuario."""
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'Usuario'
    
    def default_dashboard_link(self, obj):
        """Link al dashboard default."""
        if obj.default_dashboard:
            url = reverse(
                'admin:dashboard_dashboardconfig_change',
                args=[obj.default_dashboard.id]
            )
            return format_html(
                '<a href="{}">{}</a>',
                url,
                obj.default_dashboard.config_name
            )
        return '-'
    default_dashboard_link.short_description = 'Dashboard Default'
    
    def theme_badge(self, obj):
        """Badge para tema."""
        colors = {
            'light': '#f8f9fa',
            'dark': '#343a40'
        }
        color = colors.get(obj.theme, '#6c757d')
        text_color = '#000' if obj.theme == 'light' else '#fff'
        return format_html(
            '<span style="background-color: {}; color: {}; '
            'padding: 3px 8px; border-radius: 3px; border: 1px solid #ddd;">{}</span>',
            color,
            text_color,
            obj.get_theme_display()
        )
    theme_badge.short_description = 'Tema'
    
    def refresh_enabled_badge(self, obj):
        """Badge para refresh_enabled."""
        if obj.refresh_enabled:
            return format_html(
                '<span style="color: #28a745;">[OK] Activado</span>'
            )
        return format_html(
            '<span style="color: #dc3545;">[FAIL] Desactivado</span>'
        )
    refresh_enabled_badge.short_description = 'Auto-refresh'
    
    def show_notifications_badge(self, obj):
        """Badge para show_notifications."""
        if obj.show_notifications:
            return format_html(
                '<span style="color: #28a745;">[OK] Mostrar</span>'
            )
        return format_html(
            '<span style="color: #dc3545;">[FAIL] Ocultar</span>'
        )
    show_notifications_badge.short_description = 'Notificaciones'
