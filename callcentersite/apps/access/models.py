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
    permission_django = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True,
        verbose_name=_('Namespace Django'),
        help_text='Formato: app.accion. Ej: reports.view, dashboard.export',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Activa'),
    )
    status = models.CharField(
        max_length=20,
        choices=[('activo', 'Activo'), ('inactivo', 'Inactivo')],
        default='activo',
        verbose_name=_('Estado'),
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
        ('active',    'Active'),
        ('suspended', 'Suspended'),
        ('deleted',   'Deleted'),
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
    justification = models.TextField(
        verbose_name=_('Justificacion'),
        help_text='Razon de negocio por la que estas funciones son incompatibles.',
    )
    status = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='active',
        verbose_name=_('Estado'),
    )
    created_by = models.ForeignKey(
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
                condition=models.Q(is_active=True),
                name='unique_separation_pair_active',
            )
        ]

    def __str__(self):
        return f'SepRule: {self.function_a.code} ⊕ {self.function_b.code}'


class ExceptionalPermission(models.Model):
    """
    Permiso temporal excepcional para un usuario (UC_ACC_08, UC_PERM_03..04).

    Otorga una Function especifica a un usuario por un periodo limitado,
    incluso si violaría una SeparationRule. Requiere justification y aprobacion.
    """
    ESTADO_CHOICES = [
        ('pending',  'Pending approval'),
        ('approved', 'Approved'),
        ('active',   'Active'),
        ('expired',  'Expired'),
        ('revoked',  'Revoked'),
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
    justification = models.TextField(
        verbose_name=_('Justificacion'),
        help_text='Minimo 50 caracteres explicando la necesidad.',
    )
    status = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pending',
        verbose_name=_('Estado'),
    )
    valid_from = models.DateTimeField(
        verbose_name=_('Valido desde'),
    )
    valid_until = models.DateTimeField(
        verbose_name=_('Valido hasta'),
    )
    granted_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='exceptional_permissions_otorgados',
        verbose_name=_('Otorgado por'),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Permiso excepcional')
        verbose_name_plural = _('Permisos excepcionales')
        ordering = ['-created_at']
        db_table = 'access_exceptional_permission'

    def __str__(self):
        return f'Exc: {self.user} -> {self.function.code} [{self.status}]'


class UserModuleAccess(models.Model):
    """
    Acceso de un usuario a un modulo completo (granularidad gruesa).

    Complementa a UserPermission (funcion individual) y AccessGroup.
    Controla si el usuario puede ver el modulo en la navegacion.

    Nota: La autorizacion fina de acciones dentro del modulo
    se controla mediante UserPermission y AccessGroup.
    """
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='module_accesses',
        verbose_name=_('Usuario'),
    )
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name='user_accesses',
        verbose_name=_('Modulo'),
    )
    reason = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Motivo'),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Activo'),
    )
    granted_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Otorgado en'),
    )
    granted_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='module_accesses_granted',
        verbose_name=_('Otorgado por'),
    )
    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Revocado en'),
    )
    revoked_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='module_accesses_revoked',
        verbose_name=_('Revocado por'),
    )

    class Meta:
        verbose_name = _('Acceso a modulo')
        verbose_name_plural = _('Accesos a modulos')
        unique_together = [('user', 'module')]
        db_table = 'access_user_module_access'

    def __str__(self):
        status = 'active' if self.is_active else 'revoked'
        return f'{self.user} -> {self.module.code} [{status}]'


class UserFunctionAssignment(models.Model):
    """
    Asignacion de una funcion especifica a un usuario (RBAC granular).

    Modelo completo con soporte de soft-delete (is_active),
    trazabilidad (assigned_by, reason) y auditoria.

    Coexiste con UserPermission (modelo simplificado) durante la
    transicion. UserFunctionAssignment es la fuente de verdad para
    la asignacion de funciones con historial completo.
    """
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='function_assignments',
        verbose_name=_('Usuario'),
    )
    function = models.ForeignKey(
        Function,
        on_delete=models.CASCADE,
        related_name='user_assignments',
        verbose_name=_('Funcion'),
    )
    reason = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Motivo'),
        help_text='Razon de la asignacion (opcional).',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Activa'),
    )
    assigned_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Asignada en'),
    )
    assigned_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='function_assignments_granted',
        verbose_name=_('Asignada por'),
    )

    class Meta:
        verbose_name = _('Asignacion de funcion')
        verbose_name_plural = _('Asignaciones de funcion')
        unique_together = [('user', 'function')]
        db_table = 'access_user_function_assignment'

    def __str__(self):
        status = 'active' if self.is_active else 'revoked'
        return f'{self.user} -> {self.function.code} [{status}]'


class MenuItem(models.Model):
    """
    Wrapper UX sobre Function — árbol de navegación del sistema IACT.

    Invariante I-1 (CNST-032): 1 Function = 0..1 MenuItem.
    La relación OneToOneField lo garantiza a nivel de BD.

    El acceso al recurso lo controla Function.
    MenuItem solo contiene metadata visual (label, icono, ruta, orden).
    """

    STATUS_DRAFT      = 'DRAFT'
    STATUS_ACTIVE     = 'ACTIVE'
    STATUS_DEPRECATED = 'DEPRECATED'
    STATUS_ARCHIVED   = 'ARCHIVED'

    STATUS_CHOICES = [
        (STATUS_DRAFT,      'Draft'),
        (STATUS_ACTIVE,     'Active'),
        (STATUS_DEPRECATED, 'Deprecated'),
        (STATUS_ARCHIVED,   'Archived'),
    ]

    function = models.OneToOneField(
        'access.Function',
        on_delete=models.PROTECT,
        related_name='menu_item',
        verbose_name=_('Función'),
    )
    display_label = models.CharField(
        max_length=100,
        verbose_name=_('Etiqueta'),
    )
    icon = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name=_('Icono'),
    )
    route = models.CharField(
        max_length=200,
        blank=True,
        default='',
        verbose_name=_('Ruta'),
    )
    order = models.PositiveSmallIntegerField(
        default=0,
        verbose_name=_('Orden'),
    )
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='children',
        verbose_name=_('Padre'),
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
        verbose_name=_('Estado'),
    )
    deprecated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Fecha deprecación'),
    )
    archived_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Fecha archivo'),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'access'
        ordering  = ['order']
        verbose_name = _('Item de menú')
        verbose_name_plural = _('Items de menú')
        db_table = 'access_menu_item'

    def __str__(self):
        return f'{self.display_label} [{self.status}]'
