"""
Access control models for the IACT API.
Implements RBAC: Modules, Functions, Permissions.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import SoftDeleteModel
from apps.core.validators import validate_function_code, validate_module_name


class Module(SoftDeleteModel):
    """
    Navigation module. Can be a top-level module or a sub-module (via parent).
    """
    name = models.CharField(
        max_length=100,
        validators=[validate_module_name],
        verbose_name=_('Nombre'),
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Codigo'),
    )
    icon = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Icono'),
    )
    order = models.PositiveSmallIntegerField(
        default=0,
        verbose_name=_('Orden'),
    )
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='children',
        verbose_name=_('Modulo padre'),
    )

    class Meta:
        verbose_name = _('Modulo')
        verbose_name_plural = _('Modulos')
        ordering = ['order', 'name']
        db_table = 'access_module'

    def __str__(self):
        return self.name


class Function(SoftDeleteModel):
    """
    A specific function/action within a module (e.g., USERS_LIST, REPORTS_EXPORT).
    """
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name='functions',
        verbose_name=_('Modulo'),
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_('Nombre'),
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        validators=[validate_function_code],
        verbose_name=_('Codigo'),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Descripcion'),
    )

    class Meta:
        verbose_name = _('Funcion')
        verbose_name_plural = _('Funciones')
        ordering = ['module', 'name']
        db_table = 'access_function'

    def __str__(self):
        return f'{self.module.code}:{self.code}'


class UserPermission(models.Model):
    """Direct permission assignment: User <-> Function."""
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='user_permissions_rbac',
        verbose_name=_('Usuario'),
    )
    function = models.ForeignKey(
        Function,
        on_delete=models.CASCADE,
        related_name='user_permissions',
        verbose_name=_('Funcion'),
    )
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Permiso de usuario')
        verbose_name_plural = _('Permisos de usuario')
        unique_together = [('user', 'function')]
        db_table = 'access_user_permission'

    def __str__(self):
        return f'{self.user} -> {self.function.code}'
