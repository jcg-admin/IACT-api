from django.contrib import admin
from apps.authentication.models import SecurityQuestion, UserSecurityAnswer


@admin.register(SecurityQuestion)
class SecurityQuestionAdmin(admin.ModelAdmin):
    """
    Admin para preguntas seguridad.

    Permite crear/editar preguntas de seguridad.
    """

    list_display = ('question', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('question',)
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Pregunta', {
            'fields': ('question', 'is_active')
        }),
        ('Auditoria', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserSecurityAnswer)
class UserSecurityAnswerAdmin(admin.ModelAdmin):
    """
    Admin para respuestas seguridad.

    SOLO LECTURA por seguridad.
    Las respuestas se crean via API, no via admin.
    """

    list_display = ('user', 'question', 'created_at')
    list_filter = ('created_at', 'question')
    search_fields = ('user__username', 'question__question')
    readonly_fields = ('user', 'question', 'answer_hash', 'created_at', 'updated_at')

    fieldsets = (
        ('Respuesta', {
            'fields': ('user', 'question', 'answer_hash')
        }),
        ('Auditoria', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        """NO permitir crear respuestas desde admin."""
        return False

    def has_change_permission(self, request, obj=None):
        """NO permitir modificar respuestas."""
        return False

    def has_delete_permission(self, request, obj=None):
        """NO permitir eliminar respuestas."""
        return False
