"""
Admin para app reports.

Registra modelos Report y ExportJob.
"""
from django.contrib import admin
from .models import Report, ExportJob


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """
    Admin para Report.

    Permite ver, filtrar y buscar reportes.
    """

    list_display = (
        'id',
        'name',
        'report_type',
        'created_by',
        'status',
        'total_records',
        'created_at',
    )

    list_filter = (
        'report_type',
        'status',
        'created_at',
    )

    search_fields = (
        'name',
        'created_by__username',
        'created_by__email',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
        'total_records',
        'status',
    )

    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'report_type', 'created_by')
        }),
        ('Configuración', {
            'fields': ('filters',)
        }),
        ('Metadata', {
            'fields': ('total_records', 'status', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    ordering = ('-created_at',)

    def has_delete_permission(self, request, obj=None):
        """Solo superuser puede eliminar reportes."""
        return request.user.is_superuser


@admin.register(ExportJob)
class ExportJobAdmin(admin.ModelAdmin):
    """
    Admin para ExportJob.

    Permite ver progreso y estado de exportaciones.
    """

    list_display = (
        'id',
        'report',
        'format',
        'status',
        'get_progress',
        'total_records',
        'created_at',
    )

    list_filter = (
        'format',
        'status',
        'created_at',
    )

    search_fields = (
        'report__name',
        'report__created_by__username',
    )

    readonly_fields = (
        'report',
        'format',
        'file_path',
        'total_records',
        'exported_records',
        'status',
        'created_at',
        'started_at',
        'completed_at',
        'error_message',
        'get_progress',
    )

    fieldsets = (
        ('Export Job', {
            'fields': ('report', 'format', 'file_path')
        }),
        ('Progreso', {
            'fields': ('total_records', 'exported_records', 'get_progress', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'started_at', 'completed_at'),
            'classes': ('collapse',)
        }),
        ('Errores', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )

    ordering = ('-created_at',)

    def get_progress(self, obj):
        """Mostrar progreso en %."""
        return f"{obj.progress_percentage:.2f}%"
    get_progress.short_description = 'Progreso'

    def has_add_permission(self, request):
        """No permitir crear jobs desde admin."""
        return False

    def has_change_permission(self, request, obj=None):
        """No permitir editar jobs (solo lectura)."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Solo superuser puede eliminar jobs."""
        return request.user.is_superuser
