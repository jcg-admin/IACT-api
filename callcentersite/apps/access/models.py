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


class AccessGroup(SoftDeleteModel):
    """
    Agrupador de funciones RBAC (UC_ACC_04, UC_PERM_01..06, UC_ADM_03).

    Un AccessGroup es un conjunto nombrado de Functions que puede
    asignarse a un usuario como unidad. Permite gestionar permisos
    en bloque en lugar de funcion por funcion.

    Ejemplo: AccessGroup 'Supervisor IVR' puede contener
    view_reports, view_pipeline_status, view_data_availability.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Nombre'),
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Codigo'),
        help_text='Identificador unico. Ej: SUPERVISOR_IVR',
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Descripcion'),
    )
    functions = models.ManyToManyField(
        Function,
        blank=True,
        related_name='access_groups',
        verbose_name=_('Funciones'),
    )

    class Meta:
        verbose_name = _('Grupo de acceso')
        verbose_name_plural = _('Grupos de acceso')
        ordering = ['name']
        db_table = 'access_group'

    def __str__(self):
        return self.code


class UserAccessGroup(models.Model):
    """
    Asignacion de un AccessGroup a un usuario (UC_ACC_04, UC_PERM_01..02).
    Un usuario puede pertenecer a multiples grupos.
    """
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='access_group_memberships',
        verbose_name=_('Usuario'),
    )
    access_group = models.ForeignKey(
        AccessGroup,
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name=_('Grupo de acceso'),
    )
    granted_at = models.DateTimeField(auto_now_add=True)
    granted_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='granted_access_groups',
        verbose_name=_('Otorgado por'),
    )

    class Meta:
        verbose_name = _('Membresia de grupo')
        verbose_name_plural = _('Membresias de grupo')
        unique_together = [('user', 'access_group')]
        db_table = 'access_user_group'

    def __str__(self):
        return f'{self.user} -> {self.access_group.code}'


class SeparationRule(SoftDeleteModel):
    """
    Regla de Separacion de Deberes / Separation of Duties
    (UC_ACC_05, UC_ADM_01).

    Una SeparationRule define que dos funciones son incompatibles:
    un usuario no puede tener ambas asignadas simultaneamente.

    Ejemplo: 'aprobar_reporte' y 'crear_reporte' pueden ser
    incompatibles para evitar que alguien cree y apruebe sus
    propios reportes.
    """
    ESTADO_CHOICES = [
        ('activa',    'Activa'),
        ('suspendida','Suspendida'),
        ('eliminada', 'Eliminada'),
    ]

    name = models.CharField(
        max_length=200,
        verbose_name=_('Nombre de la regla'),
    )
    function_a = models.ForeignKey(
        Function,
        on_delete=models.CASCADE,
        related_name='separation_rules_as_a',
        verbose_name=_('Funcion A'),
    )
    function_b = models.ForeignKey(
        Function,
        on_delete=models.CASCADE,
        related_name='separation_rules_as_b',
        verbose_name=_('Funcion B'),
    )
    justificacion = models.TextField(
        verbose_name=_('Justificacion'),
        help_text='Razon de negocio por la que estas funciones son incompatibles.',
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='activa',
        verbose_name=_('Estado'),
    )
    creado_por = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='separation_rules_created',
        verbose_name=_('Creado por'),
    )

    class Meta:
        verbose_name = _('Regla de separacion')
        verbose_name_plural = _('Reglas de separacion')
        ordering = ['name']
        db_table = 'access_separation_rule'
        constraints = [
            models.UniqueConstraint(
                fields=['function_a', 'function_b'],
                condition=models.Q(deleted_at__isnull=True),
                name='unique_separation_pair_active',
            )
        ]

    def __str__(self):
        return f'SepRule: {self.function_a.code} ⊕ {self.function_b.code}'


class ExceptionalPermission(models.Model):
    """
    Permiso temporal excepcional para un usuario (UC_ACC_08, UC_PERM_03..04).

    Otorga una Function especifica a un usuario por un periodo limitado,
    incluso si violaría una SeparationRule. Requiere justificacion y aprobacion.
    """
    ESTADO_CHOICES = [
        ('pendiente',  'Pendiente de aprobacion'),
        ('aprobado',   'Aprobado'),
        ('activo',     'Activo'),
        ('expirado',   'Expirado'),
        ('revocado',   'Revocado'),
    ]

    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='exceptional_permissions',
        verbose_name=_('Usuario'),
    )
    function = models.ForeignKey(
        Function,
        on_delete=models.CASCADE,
        related_name='exceptional_grants',
        verbose_name=_('Funcion'),
    )
    justificacion = models.TextField(
        verbose_name=_('Justificacion'),
        help_text='Minimo 50 caracteres explicando la necesidad.',
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente',
        verbose_name=_('Estado'),
    )
    valido_desde = models.DateTimeField(
        verbose_name=_('Valido desde'),
    )
    valido_hasta = models.DateTimeField(
        verbose_name=_('Valido hasta'),
    )
    otorgado_por = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='exceptional_permissions_otorgados',
        verbose_name=_('Otorgado por'),
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Permiso excepcional')
        verbose_name_plural = _('Permisos excepcionales')
        ordering = ['-creado_en']
        db_table = 'access_exceptional_permission'

    def __str__(self):
        return f'Exc: {self.user} -> {self.function.code} [{self.estado}]'
