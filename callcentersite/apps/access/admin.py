"""
apps/access/admin.py

Django Admin registration for the access app models.
"""
from django.contrib import admin
from django.utils.html import format_html

from apps.access.models import (
    Module, Function, UserPermission,
    AccessGroup, UserAccessGroup,
    SeparationRule, ExceptionalPermission,
    UserFunctionAssignment, UserModuleAccess,
)


# ---------------------------------------------------------------------------
# Pre-existing models
# ---------------------------------------------------------------------------

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display  = ['code', 'name', 'parent', 'order', 'is_active']
    list_filter   = ['is_active', 'parent']
    search_fields = ['code', 'name']
    ordering      = ['order', 'name']


@admin.register(Function)
class FunctionAdmin(admin.ModelAdmin):
    list_display  = ['code', 'name', 'permission_django', 'module', 'is_active', 'status']
    list_filter   = ['is_active', 'status', 'module']
    search_fields = ['code', 'name', 'permission_django']
    ordering      = ['module__code', 'code']


@admin.register(UserPermission)
class UserPermissionAdmin(admin.ModelAdmin):
    list_display  = ['user', 'function']
    search_fields = ['user__email', 'function__code']
    raw_id_fields = ['user', 'function']


# ---------------------------------------------------------------------------
# J-001: AccessGroup
# ---------------------------------------------------------------------------

@admin.register(AccessGroup)
class AccessGroupAdmin(admin.ModelAdmin):
    list_display      = ['code', 'name', 'function_count', 'is_active']
    list_filter       = ['is_active']
    search_fields     = ['code', 'name']
    filter_horizontal = ['functions']
    ordering          = ['name']

    @admin.display(description='Functions')
    def function_count(self, obj) -> int:
        return obj.functions.count()


# ---------------------------------------------------------------------------
# J-002: UserAccessGroup
# ---------------------------------------------------------------------------

@admin.register(UserAccessGroup)
class UserAccessGroupAdmin(admin.ModelAdmin):
    list_display  = ['user', 'access_group', 'granted_at', 'granted_by']
    list_filter   = ['access_group']
    search_fields = ['user__email', 'access_group__code']
    raw_id_fields = ['user', 'granted_by']
    ordering      = ['-granted_at']
    date_hierarchy = 'granted_at'


# ---------------------------------------------------------------------------
# J-001: SeparationRule
# ---------------------------------------------------------------------------

@admin.register(SeparationRule)
class SeparationRuleAdmin(admin.ModelAdmin):
    list_display  = ['code', 'name', 'state', 'created_by']
    list_filter   = ['state']
    search_fields = ['code', 'name']
    raw_id_fields = ['created_by']
    # functions_set_a/b son M2M — se gestionan en inline o filter_horizontal
    filter_horizontal = []
    ordering      = ['name']


# ---------------------------------------------------------------------------
# J-001: ExceptionalPermission
# ---------------------------------------------------------------------------

@admin.register(ExceptionalPermission)
class ExceptionalPermissionAdmin(admin.ModelAdmin):
    list_display  = ['user', 'function', 'status', 'valid_from', 'valid_until',
                     'granted_by', 'is_currently_active']
    list_filter   = ['status']
    search_fields = ['user__email', 'function__code']
    raw_id_fields = ['user', 'function', 'granted_by']
    ordering      = ['-created_at']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']

    @admin.display(description='Active now', boolean=True)
    def is_currently_active(self, obj) -> bool:
        from django.utils import timezone
        now = timezone.now()
        return (
            obj.status == 'approved'
            and obj.valid_from <= now <= obj.valid_until
        )


# ---------------------------------------------------------------------------
# Supplementary models
# ---------------------------------------------------------------------------

@admin.register(UserFunctionAssignment)
class UserFunctionAssignmentAdmin(admin.ModelAdmin):
    list_display  = ['user', 'function', 'is_active', 'assigned_at', 'assigned_by']
    list_filter   = ['is_active']
    search_fields = ['user__email', 'function__code']
    raw_id_fields = ['user', 'function', 'assigned_by']
    ordering      = ['-assigned_at']


@admin.register(UserModuleAccess)
class UserModuleAccessAdmin(admin.ModelAdmin):
    list_display  = ['user', 'module', 'is_active', 'granted_at', 'revoked_at']
    list_filter   = ['is_active', 'module']
    search_fields = ['user__email', 'module__code']
    raw_id_fields = ['user', 'module', 'granted_by', 'revoked_by']
    ordering      = ['-granted_at']
