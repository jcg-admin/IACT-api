from django.contrib import admin
from apps.access.models import Function, UserFunctionAssignment


@admin.register(Function)
class FunctionAdmin(admin.ModelAdmin):
    """
    Admin para funciones RBAC v6.0.0.
    
    RBAC v6.0.0: Muestra permission_django (namespace) y status.
    
    Features:
    - Lista funciones con namespace, código y status
    - Filtros por módulo, status y estado activo
    - Búsqueda por namespace, código y nombre
    - Fieldsets organizados
    """
    
    list_display = (
        'permission_django',
        'code',
        'module',
        'name',
        'status',
        'is_active',
        'created_at'
    )
    list_filter = (
        'module',
        'status',
        'is_active',
        'created_at'
    )
    search_fields = (
        'permission_django',
        'code',
        'name',
        'description'
    )
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Identificación RBAC v6.0.0', {
            'fields': ('permission_django', 'code', 'module'),
            'description': 'permission_django es el namespace Django (PK funcional)'
        }),
        ('Información', {
            'fields': ('name', 'description')
        }),
        ('Estado', {
            'fields': ('status', 'is_active'),
            'description': 'status: activo, planificado, deprecado'
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Ordenar por módulo y namespace
    ordering = ('module', 'permission_django')


@admin.register(UserFunctionAssignment)
class UserFunctionAssignmentAdmin(admin.ModelAdmin):
    """
    Admin para asignaciones de funciones RBAC v6.0.0.
    
    RBAC v6.0.0: Muestra namespaces y gestión completa de asignaciones.
    
    Features:
    - Lista asignaciones con namespace de función
    - Filtros por módulo, status y estado
    - Búsqueda por username y namespace
    - Auditoría completa (asignación/revocación)
    """
    
    list_display = (
        'user',
        'function_namespace',
        'function_status',
        'is_active',
        'assigned_by',
        'assigned_at'
    )
    list_filter = (
        'is_active',
        'function__module',
        'function__status',
        'assigned_at'
    )
    search_fields = (
        'user__username',
        'user__email',
        'function__permission_django',
        'function__code',
        'function__name'
    )
    readonly_fields = (
        'assigned_at',
        'assigned_by',
        'revoked_at',
        'revoked_by'
    )
    
    fieldsets = (
        ('Asignación', {
            'fields': ('user', 'function', 'reason')
        }),
        ('Estado', {
            'fields': ('is_active',)
        }),
        ('Auditoría Asignación', {
            'fields': ('assigned_at', 'assigned_by'),
            'classes': ('collapse',)
        }),
        ('Auditoría Revocación', {
            'fields': ('revoked_at', 'revoked_by'),
            'classes': ('collapse',)
        })
    )
    
    # Ordenar por usuario y función
    ordering = ('user__username', 'function__permission_django')
    
    def function_namespace(self, obj):
        """Muestra namespace de la función."""
        return obj.function.permission_django
    function_namespace.short_description = 'Función (Namespace)'
    function_namespace.admin_order_field = 'function__permission_django'
    
    def function_status(self, obj):
        """Muestra status de la función."""
        return obj.function.status
    function_status.short_description = 'Status'
    function_status.admin_order_field = 'function__status'
    
    def save_model(self, request, obj, form, change):
        """Guardar quien asigna la función."""
        if not change:  # Si es nuevo
            obj.assigned_by = request.user
        super().save_model(request, obj, form, change)
