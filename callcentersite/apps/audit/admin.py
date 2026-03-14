from django.contrib import admin
from apps.audit.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """
    Admin para logs auditoria.
    
    SOLO LECTURA (CNST-009).
    """
    
    list_display = (
        'timestamp',
        'user',
        'action',
        'resource',
        'result',
        'ip_address'
    )
    list_filter = ('result', 'action', 'timestamp')
    search_fields = ('user__username', 'action', 'resource', 'ip_address')
    readonly_fields = (
        'user',
        'action',
        'resource',
        'result',
        'timestamp',
        'ip_address',
        'user_agent',
        'details'
    )
    
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Accion', {
            'fields': ('user', 'action', 'resource', 'result')
        }),
        ('Contexto', {
            'fields': ('timestamp', 'ip_address', 'user_agent')
        }),
        ('Detalles', {
            'fields': ('details',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """NO permitir crear logs desde admin."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """NO permitir modificar logs."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """NO permitir eliminar logs."""
        return False
