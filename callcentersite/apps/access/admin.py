from django.contrib import admin
from apps.access.models import Module, Function, UserPermission

admin.site.register(Module)
admin.site.register(Function)
admin.site.register(UserPermission)
