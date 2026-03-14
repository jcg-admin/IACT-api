from django.contrib import admin
from apps.pipeline.models import ETLExecution, Center, Service, CallRecord


# ============================================================================
# ETL ADMIN
# ============================================================================

@admin.register(ETLExecution)
class ETLExecutionAdmin(admin.ModelAdmin):
    """
    Admin para ETLExecution.
    
    Solo lectura - las ejecuciones se crean automaticamente.
    """
    
    list_display = (
        'id',
        'start_date',
        'end_date',
        'status',
        'records_extracted',
        'records_loaded',
        'started_at',
        'completed_at',
    )
    
    list_filter = ('status', 'started_at')
    
    search_fields = ('error_message',)
    
    readonly_fields = (
        'start_date',
        'end_date',
        'status',
        'records_extracted',
        'records_loaded',
        'started_at',
        'completed_at',
        'error_message',
    )
    
    date_hierarchy = 'started_at'
    
    def has_add_permission(self, request):
        """NO permitir crear manualmente."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """NO permitir modificar."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Permitir eliminar (limpiar logs viejos)."""
        return True


# ============================================================================
# CENTER ADMIN (Moved from apps/core/)
# ============================================================================

@admin.register(Center)
class CenterAdmin(admin.ModelAdmin):
    """
    Admin para Center.
    
    Gestión de centros de atención.
    """
    
    list_display = (
        'id',
        'codigo',
        'nombre',
        'activo',
        'get_services_count',
        'created_at',
    )
    
    list_filter = ('activo', 'created_at')
    
    search_fields = ('codigo', 'nombre', 'descripcion')
    
    readonly_fields = ('created_at', 'updated_at', 'is_deleted', 'deleted_at')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo', 'nombre', 'descripcion', 'direccion')
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'is_deleted', 'deleted_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_services_count(self, obj):
        """Cantidad de servicios del centro."""
        return obj.services.count()
    get_services_count.short_description = 'Servicios'


# ============================================================================
# SERVICE ADMIN (Moved from apps/core/)
# ============================================================================

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """
    Admin para Service.
    
    Gestión de servicios 800.
    """
    
    list_display = (
        'id',
        'numero_800',
        'nombre',
        'center',
        'activo',
        'get_users_count',
        'created_at',
    )
    
    list_filter = ('activo', 'center', 'created_at')
    
    search_fields = ('numero_800', 'nombre', 'descripcion')
    
    readonly_fields = ('created_at', 'updated_at', 'is_deleted', 'deleted_at')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('numero_800', 'nombre', 'descripcion')
        }),
        ('Centro', {
            'fields': ('center',)
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'is_deleted', 'deleted_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_users_count(self, obj):
        """Cantidad de usuarios con acceso."""
        return obj.user_accesses.filter(is_active=True).count()
    get_users_count.short_description = 'Usuarios'


# ============================================================================
# CALLRECORD ADMIN (Moved from apps/core/)
# ============================================================================

@admin.register(CallRecord)
class CallRecordAdmin(admin.ModelAdmin):
    """
    Admin para CallRecord.
    
    Registros de llamadas procesados (output ETL).
    Solo lectura - se crean via ETL.
    """
    
    list_display = (
        'id',
        'fecha',
        'telefono',
        'servicio_800',
        'total_llamadas',
        'llamadas_contestadas',
        'llamadas_abandonadas',
        'get_answer_rate',
        'created_at',
    )
    
    list_filter = ('fecha', 'created_at')
    
    search_fields = ('telefono', 'servicio_800')
    
    readonly_fields = (
        'fecha',
        'telefono',
        'servicio_800',
        'total_llamadas',
        'llamadas_contestadas',
        'llamadas_abandonadas',
        'duracion_total_segundos',
        'created_at',
        'updated_at',
        'is_deleted',
        'deleted_at',
    )
    
    date_hierarchy = 'fecha'
    
    fieldsets = (
        ('Identificación', {
            'fields': ('fecha', 'telefono', 'servicio_800')
        }),
        ('Estadísticas', {
            'fields': (
                'total_llamadas',
                'llamadas_contestadas',
                'llamadas_abandonadas',
                'duracion_total_segundos',
            )
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'is_deleted', 'deleted_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_answer_rate(self, obj):
        """Tasa de respuesta."""
        return f"{obj.answer_rate()}%"
    get_answer_rate.short_description = 'Tasa Respuesta'
    
    def has_add_permission(self, request):
        """NO permitir crear manualmente (se crea via ETL)."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """NO permitir modificar (readonly)."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Permitir eliminar (limpiar datos viejos)."""
        return True
