from django.contrib import admin
from apps.alerts.models import (
    InternalMessage,
    MessageRecipient,
    AlertConfiguration,
    AlertSubscription
)


class MessageRecipientInline(admin.TabularInline):
    """Inline para MessageRecipient"""
    model = MessageRecipient
    extra = 0
    readonly_fields = ('read_at', 'archived_at', 'created_at')
    fields = ('user', 'read_at', 'archived_at')


@admin.register(InternalMessage)
class InternalMessageAdmin(admin.ModelAdmin):
    """
    Admin para mensajes internos
    
    Features:
    - Lista mensajes con sender, subject, priority
    - Filtros por priority, created_at
    - Búsqueda por subject, body
    - Readonly fields para created_at
    - Inline para MessageRecipient
    """
    
    list_display = (
        'id',
        'sender',
        'subject',
        'priority',
        'recipient_count',
        'created_at'
    )
    
    list_filter = (
        'priority',
        'created_at'
    )
    
    search_fields = (
        'subject',
        'body',
        'sender__username'
    )
    
    readonly_fields = ('created_at',)
    
    inlines = [MessageRecipientInline]
    
    fieldsets = (
        ('Información del Mensaje', {
            'fields': ('sender', 'subject', 'body', 'priority')
        }),
        ('Metadata', {
            'fields': ('created_at', 'deleted_at'),
            'classes': ('collapse',)
        })
    )
    
    def recipient_count(self, obj):
        """Contar destinatarios"""
        return obj.recipients.count()
    recipient_count.short_description = 'Destinatarios'
    
    def has_delete_permission(self, request, obj=None):
        """Solo soft delete"""
        return True


@admin.register(AlertConfiguration)
class AlertConfigurationAdmin(admin.ModelAdmin):
    """
    Admin para configuraciones de alertas
    
    Features:
    - Lista configuraciones con name, priority, is_active
    - Filtros por priority, is_active
    - Búsqueda por name, description
    - Readonly fields para last_evaluated_at, last_triggered_at
    - Display para subscriber_count
    """
    
    list_display = (
        'id',
        'name',
        'priority',
        'is_active',
        'subscriber_count',
        'last_triggered_at',
        'created_at'
    )
    
    list_filter = (
        'priority',
        'is_active',
        'created_at'
    )
    
    search_fields = (
        'name',
        'description'
    )
    
    readonly_fields = (
        'last_evaluated_at',
        'last_triggered_at',
        'created_at',
        'updated_at'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'description', 'priority', 'is_active')
        }),
        ('Condición de Alerta', {
            'fields': ('condition',),
            'description': 'JSONField con: metric, operator, value, period'
        }),
        ('Estado', {
            'fields': ('last_evaluated_at', 'last_triggered_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',)
        })
    )
    
    def subscriber_count(self, obj):
        """Contar suscriptores activos"""
        return obj.subscriptions.filter(
            is_active=True,
            deleted_at__isnull=True
        ).count()
    subscriber_count.short_description = 'Suscriptores'


@admin.register(AlertSubscription)
class AlertSubscriptionAdmin(admin.ModelAdmin):
    """
    Admin para suscripciones a alertas
    
    Features:
    - Lista suscripciones con user, alert_configuration, is_active
    - Filtros por is_active, subscribed_at
    - Búsqueda por user, alert_configuration
    - Readonly fields para subscribed_at
    """
    
    list_display = (
        'id',
        'user',
        'alert_configuration',
        'is_active',
        'subscribed_at'
    )
    
    list_filter = (
        'is_active',
        'subscribed_at'
    )
    
    search_fields = (
        'user__username',
        'alert_configuration__name'
    )
    
    readonly_fields = ('subscribed_at',)
    
    fieldsets = (
        ('Suscripción', {
            'fields': ('user', 'alert_configuration', 'is_active')
        }),
        ('Metadata', {
            'fields': ('subscribed_at', 'deleted_at'),
            'classes': ('collapse',)
        })
    )
    
    def has_add_permission(self, request):
        """Permitir agregar suscripciones desde admin"""
        return True

