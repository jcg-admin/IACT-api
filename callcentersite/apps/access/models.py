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

    # -- Campos de menú dinámico (F2-H-004 / UC_PERM_08) --
    menu_visible  = models.BooleanField(default=False, verbose_name=_('Visible en menú'))
    menu_domain   = models.CharField(max_length=50,  blank=True, default='', verbose_name=_('Dominio'))
    menu_section  = models.CharField(max_length=50,  blank=True, default='', verbose_name=_('Sección'))
    menu_action   = models.CharField(max_length=50,  blank=True, default='', verbose_name=_('Acción'))
    menu_label_es = models.CharField(max_length=100, blank=True, default='', verbose_name=_('Label ES'))
    menu_label_en = models.CharField(max_length=100, blank=True, default='', verbose_name=_('Label EN'))
    menu_icon     = models.CharField(max_length=100, blank=True, default='', verbose_name=_('Icono'))
    menu_order    = models.PositiveSmallIntegerField(default=0, verbose_name=_('Orden menú'))

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

    is_predefined = models.BooleanField(
        default=False,
        verbose_name=_('Predefinido'),
        help_text='True para los 10 AGRs del catálogo v5.4.0. UC_PERM_05 CA-07: inmutables.',
        db_index=True,
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Activo'),
        help_text='BR-009: desactivar en lugar de eliminar.',
        db_index=True,
    )
    retired_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_('Retirado en'),
    )
    retire_reason = models.CharField(
        max_length=500, blank=True, default='', verbose_name=_('Razón de retiro'),
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


class SeparationRule(models.Model):
    """
    Regla de Separacion de Deberes — Separation of Duties (SoD).

    UC_ACC_05 (ACC-005/011/012), BR-007, CNST-030.

    Modela conflictos GRUPALES entre conjuntos de funciones:
    - functions_set_a: primer conjunto de funciones en conflicto
    - functions_set_b: segundo conjunto de funciones en conflicto
    Un usuario NO puede tener funciones de AMBOS conjuntos simultaneamente.

    Diseño canónico (FASE 0 — modelo-rbac-iact.rst v5.4.0):
      SOD-001 pipeline_audit_separation   (PIP-* vs AUD-*)
      SOD-002 user_management_audit_separation (USR-* vs AUD-*)
      SOD-003 access_management_audit_separation (ACC-* vs AUD-*)

    Estado: ENABLED / DISABLED (BR-009 — baja lógica, no DELETE).

    Hallazgo F0-H-003: el modelo anterior usaba FKs binarios (function_a,
    function_b) que solo permiten pares de funciones. Los SoD del v5.4.0
    son grupales (múltiples funciones por lado). Se reestructura a M2M.
    """

    STATE_ENABLED  = 'ENABLED'
    STATE_DISABLED = 'DISABLED'

    STATE_CHOICES = [
        (STATE_ENABLED,  'Enabled'),   # BR-009: ENABLED por defecto
        (STATE_DISABLED, 'Disabled'),  # BR-009: desactivar, no eliminar
    ]

    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_('Codigo'),
        help_text='Identificador canónico. Ej: SOD-001. '
                  'Fuente: modelo-rbac-iact.rst v5.4.0.',
    )
    name = models.CharField(
        max_length=200,
        verbose_name=_('Nombre'),
        help_text='Nombre legible. Ej: pipeline_audit_separation.',
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Descripcion'),
        help_text='Razon de negocio por la que estos conjuntos son incompatibles.',
    )
    functions_set_a = models.ManyToManyField(
        Function,
        blank=True,
        related_name='separation_rules_as_set_a',
        verbose_name=_('Conjunto A'),
        help_text='Funciones del primer conjunto en conflicto (ej: Pipeline).',
    )
    functions_set_b = models.ManyToManyField(
        Function,
        blank=True,
        related_name='separation_rules_as_set_b',
        verbose_name=_('Conjunto B'),
        help_text='Funciones del segundo conjunto en conflicto (ej: Auditoria).',
    )
    state = models.CharField(
        max_length=10,
        choices=STATE_CHOICES,
        default=STATE_ENABLED,
        verbose_name=_('Estado'),
        help_text='ENABLED | DISABLED. BR-009: nunca DELETE.',
    )
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='separation_rules_created',
        verbose_name=_('Creado por'),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Creado'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Actualizado'))

    class Meta:
        verbose_name = _('Regla SoD')
        verbose_name_plural = _('Reglas SoD')
        ordering = ['code']
        db_table = 'access_separation_rule'

    def __str__(self) -> str:
        return f'SoD {self.code}: {self.name} [{self.state}]'

    def is_violated_by(self, function_codes: set[str]) -> bool:
        """
        Verifica si un conjunto de códigos de función viola esta regla SoD.

        FR-010-02: validar SoD antes de asignar (BR-007).
        La regla se viola cuando el conjunto contiene funciones de AMBOS grupos.

        Args:
            function_codes: set de strings con los códigos de función del usuario.

        Returns:
            True si hay violación (usuario tiene fns de ambos sets), False si no.
        """
        if self.state == self.STATE_DISABLED:
            return False

        codes_a = set(self.functions_set_a.values_list('code', flat=True))
        codes_b = set(self.functions_set_b.values_list('code', flat=True))

        has_a = bool(function_codes & codes_a)
        has_b = bool(function_codes & codes_b)

        return has_a and has_b

    def find_conflict(self, function_codes: set[str]) -> tuple[str, str] | None:
        """
        Retorna el primer par en conflicto o None si no hay violación.

        Patrón Specification (patrones-diseno.rst UC_ACC_01).
        """
        if not self.is_violated_by(function_codes):
            return None

        codes_a = set(self.functions_set_a.values_list('code', flat=True))
        codes_b = set(self.functions_set_b.values_list('code', flat=True))

        fn_a = next(iter(function_codes & codes_a))
        fn_b = next(iter(function_codes & codes_b))
        return (fn_a, fn_b)


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
    Asignacion de funcion RBAC a usuario — fuente de verdad para FASE 1+.

    UC_ACC_01 (assign_functions), UC_ACC_02 (revoke_functions).
    Fuente: modelo-dominio-iact.rst § 4.2, Assignment class.

    Estado canónico (BR-009 — baja lógica siempre):
    - ACTIVE: asignación vigente
    - EXPIRED: caducó por expires_at < now
    - REVOKED: revocada explícitamente por UC_ACC_02

    Hallazgo F0-H-004 (FASE 0): el modelo anterior solo tenía is_active
    boolean. Sin state enum, expires_at, revoked_at ni revoke_reason, los
    UCs UC_ACC_02 y UC_PERM_07 no pueden implementarse correctamente.

    Se mantiene is_active como campo de conveniencia (sincronizado con state).
    """

    STATE_ACTIVE  = 'ACTIVE'
    STATE_EXPIRED = 'EXPIRED'
    STATE_REVOKED = 'REVOKED'

    STATE_CHOICES = [
        (STATE_ACTIVE,  'Active'),   # Asignación vigente
        (STATE_EXPIRED, 'Expired'),  # Caducó por expires_at
        (STATE_REVOKED, 'Revoked'),  # Revocada explícitamente — BR-009
    ]

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
    state = models.CharField(
        max_length=10,
        choices=STATE_CHOICES,
        default=STATE_ACTIVE,
        verbose_name=_('Estado'),
        help_text='ACTIVE | EXPIRED | REVOKED. BR-009: nunca DELETE.',
        db_index=True,
    )
    # Compatibilidad con código existente — sincronizado con state
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Activa'),
        help_text='True cuando state=ACTIVE. Sincronizado automáticamente.',
    )
    # Trazabilidad de asignación (UC_ACC_01)
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
    reason = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Motivo de asignacion'),
        help_text='Razón de la asignación (opcional).',
    )
    # Expiración temporal (UC_ACC_01 CA-02, UC_PERM_07 CA-06/07/17)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Expira en'),
        help_text='Nullable: si es None la asignación no expira. '
                  'UC_PERM_07 CA-06: expired assignment no cuenta.',
        db_index=True,
    )
    # Trazabilidad de revocación (UC_ACC_02)
    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Revocada en'),
    )
    revoked_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='function_assignments_revoked',
        verbose_name=_('Revocada por'),
    )
    revoke_reason = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_('Motivo de revocacion'),
        help_text='UC_ACC_02: revoke_reason obligatorio al revocar.',
    )

    class Meta:
        verbose_name = _('Asignacion de funcion')
        verbose_name_plural = _('Asignaciones de funcion')
        db_table = 'access_user_function_assignment'
        # F2-H-006: unique_together (user, function) eliminado.
        # CA-21 UC_ACC_01: nueva asignación tras revocación preserva historial REVOKED.
        indexes = [
            models.Index(fields=['user', 'state'], name='idx_ufassign_user_state'),
            models.Index(fields=['state', 'expires_at'], name='idx_ufassign_state_expires'),
        ]

    def __str__(self) -> str:
        return f'{self.user} -> {self.function.code} [{self.state}]'

    def revoke(self, revoked_by, reason: str) -> None:
        """
        UC_ACC_02: revocar asignación (baja lógica, BR-009).

        Args:
            revoked_by: User que revoca.
            reason: Razón de revocación (requerida).
        """
        from django.utils import timezone
        self.state = self.STATE_REVOKED
        self.is_active = False
        self.revoked_at = timezone.now()
        self.revoked_by = revoked_by
        self.revoke_reason = reason
        self.save(update_fields=[
            'state', 'is_active', 'revoked_at', 'revoked_by', 'revoke_reason'
        ])

    @property
    def is_currently_valid(self) -> bool:
        """
        UC_PERM_07 CA-06: asignación expirada no cuenta.
        True si state=ACTIVE y no ha expirado.
        """
        from django.utils import timezone
        if self.state != self.STATE_ACTIVE:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True


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
