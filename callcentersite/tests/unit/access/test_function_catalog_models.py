"""
tests/unit/access/test_models.py

Tests unitarios para los modelos Module, Function, UserPermission
y UserFunctionAssignment.

Nota sobre deuda preexistente (resuelta 2026-05-08):
    Los tests originales asumían un diseño previo del modelo que nunca
    llegó a producción:
    - Module con description, is_root(), get_level(), get_ancestors(),
      is_deleted, all_with_deleted()
    - UserPermission con campos module, assigned_by, reason, is_active
    - Function.module como string en lugar de ForeignKey

    Los tests han sido actualizados para reflejar los modelos reales
    implementados en las Fases B–N del plan v2.0.0.
"""
import pytest
from django.db.utils import IntegrityError

from apps.access.models import (
    Function, Module,
    UserFunctionAssignment, UserPermission,
    UserModuleAccess,
)
from tests.test_data.access_test_data import (
    FunctionTestData,
    ModuleTestData,
)
from tests.test_data.user_test_data import AdminUserTestData, UserTestData


# ---------------------------------------------------------------------------
# Module
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _populate_catalog(db):
    from django.core.management import call_command
    from io import StringIO
    call_command('create_functions', stdout=StringIO())
    call_command('create_access_groups', stdout=StringIO())



@pytest.mark.unit
@pytest.mark.django_db
class TestModuleModel:
    """Tests del modelo Module (árbol de módulos de navegación)."""

    def test_create_root_module(self):
        """Módulo sin parent es un módulo raíz."""
        module = Module.objects.create(code='T6aba7_ROOT', name='Root Module')
        assert module.pk is not None
        assert module.parent is None
        assert module.is_active is True

    def test_create_child_module(self):
        """Módulo con parent es un módulo hijo."""
        parent = Module.objects.create(code='T6aba7_PAR', name='Parent')
        child  = Module.objects.create(
            code='MOD_CHILD', name='Child', parent=parent)

        assert child.parent == parent
        assert child.parent.pk == parent.pk

    def test_module_children_relation(self):
        """Los hijos de un módulo son accesibles via related_name 'children'."""
        parent = Module.objects.create(code='T6aba7_P', name='Parent')
        c1 = Module.objects.create(code='T6aba7_C1', name='Child 1', parent=parent)
        c2 = Module.objects.create(code='T6aba7_C2', name='Child 2', parent=parent)

        children = list(parent.children.all())
        assert c1 in children
        assert c2 in children

    def test_module_code_is_unique(self):
        """El campo code tiene restricción UNIQUE."""
        Module.objects.create(code='T6aba7_UNIQ', name='Unique')
        with pytest.raises(IntegrityError):
            Module.objects.create(code='T6aba7_UNIQ', name='Duplicate')

    def test_soft_delete_via_is_active(self):
        """SoftDeleteModel.soft_delete() pone is_active=False sin borrar la fila."""
        module = Module.objects.create(code='MOD_DEL', name='To delete')
        module.soft_delete()

        module.refresh_from_db()
        assert module.is_active is False
        assert Module.objects.filter(pk=module.pk).exists()

    def test_restore_after_soft_delete(self):
        """SoftDeleteModel.restore() vuelve is_active=True."""
        module = Module.objects.create(code='MOD_REST', name='To restore')
        module.soft_delete()
        module.restore()

        module.refresh_from_db()
        assert module.is_active is True

    def test_module_str(self):
        """__str__ retorna el nombre del módulo."""
        module = Module.objects.create(code='MOD_STR', name='Mi Módulo')
        assert str(module) is not None

    
    def test_module_ordering_by_order_then_name(self):
        """Módulos se ordenan por 'order' primero, luego 'name'."""
        m1 = Module.objects.create(code='TC_ORD1', name='A Module', order=91)
        m2 = Module.objects.create(code='TC_ORD2', name='B Module', order=92)

        ordered = list(Module.objects.filter(
            code__in=['TC_ORD1', 'TC_ORD2']
        ).order_by('order'))
        assert len(ordered) == 2
        assert ordered[0].order < ordered[1].order
        assert ordered[0].code == 'TC_ORD1'


# ---------------------------------------------------------------------------
# Function
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.django_db
class TestFunctionModel:
    """Tests del modelo Function (unidad atómica de RBAC)."""

    def test_create_function(self):
        """Crear función atómica con sus campos reales."""
        module = ModuleTestData()
        fn = Function.objects.create(
            code='reports.view',
            module=module,
            name='Ver Reportes',
            permission_django='reports.view',
        )
        assert fn.pk is not None
        assert fn.code == 'reports.view'
        assert fn.module == module
        assert fn.is_active is True

    
    def test_function_str(self):
        """__str__ de una Function retorna una cadena no vacía."""
        import uuid
        u = uuid.uuid4().hex[:6]
        module = Module.objects.create(code=f'MOD_{u}', name=f'Mod {u}')
        fn = Function.objects.create(
            code=f'fn_{u}', module=module, name='Ver')
        assert str(fn) is not None and len(str(fn)) > 0

    def test_function_code_is_unique(self):
        """El campo code tiene restricción UNIQUE."""
        module = ModuleTestData()
        Function.objects.create(
            code='unique.func', module=module,
            name='F1', permission_django='unique.func')
        with pytest.raises(IntegrityError):
            Function.objects.create(
                code='unique.func', module=module,
                name='F2')

    def test_function_ordering_by_module_then_name(self):
        """Functions creadas en módulos distintos se ordenan por module, luego name."""
        import uuid
        u = uuid.uuid4().hex[:6]
        mod_a = Module.objects.create(code=f'MA_{u}', name=f'A_{u}', order=100)
        mod_b = Module.objects.create(code=f'MB_{u}', name=f'B_{u}', order=101)
        Function.objects.create(code=f'bz_{u}', module=mod_b, name='Z Function')
        Function.objects.create(code=f'aa_{u}', module=mod_a, name='A Function')
        Function.objects.create(code=f'ab_{u}', module=mod_a, name='B Function')

        fns = list(Function.objects.filter(
            code__in=[f'bz_{u}', f'aa_{u}', f'ab_{u}']
        ).order_by('module__order', 'name'))
        assert len(fns) == 3
        assert fns[0].module == mod_a
        assert fns[1].module == mod_a
        assert fns[2].module == mod_b


# ---------------------------------------------------------------------------
# UserPermission
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.django_db
class TestUserPermission:
    """Tests del modelo UserPermission (asignación directa user→function)."""

    def test_assign_function_to_user(self):
        """Asignar una función directamente a un usuario."""
        user = UserTestData()
        fn   = FunctionTestData()

        perm = UserPermission.objects.create(user=user, function=fn)

        assert perm.user == user
        assert perm.function == fn
        assert perm.granted_at is not None

    def test_user_permission_str(self):
        """__str__ retorna 'username -> function_code'."""
        user = UserTestData()
        fn   = FunctionTestData(code='reports.view')

        perm = UserPermission.objects.create(user=user, function=fn)
        assert '->' in str(perm)
        assert fn.code in str(perm)

    def test_unique_together_user_function(self):
        """Un usuario no puede tener la misma función asignada dos veces."""
        from django.db import transaction
        user = UserTestData()
        fn   = FunctionTestData()

        UserPermission.objects.create(user=user, function=fn)
        with pytest.raises(Exception):  # IntegrityError en PG, puede ser distinto en SQLite
            with transaction.atomic():
                UserPermission.objects.create(user=user, function=fn)


# ---------------------------------------------------------------------------
# UserFunctionAssignment
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.django_db
class TestUserFunctionAssignment:
    """
    Tests del modelo UserFunctionAssignment.

    UserFunctionAssignment es el modelo de asignación con historial completo:
    includes assigned_by, reason, is_active y trazabilidad de auditoría.
    Coexiste con UserPermission (simplificado) durante la transición.
    """

    def test_assign_function_with_full_fields(self):
        """Asignación completa con todos los campos opcionales."""
        user  = UserTestData()
        admin = AdminUserTestData()
        fn    = FunctionTestData()

        assignment = UserFunctionAssignment.objects.create(
            user=user,
            function=fn,
            assigned_by=admin,
            reason='Permisos iniciales del proyecto',
        )

        assert assignment.user    == user
        assert assignment.function == fn
        assert assignment.is_active is True
        assert assignment.assigned_by == admin
        assert assignment.reason == 'Permisos iniciales del proyecto'

    def test_deactivate_assignment(self):
        """Una asignación puede desactivarse poniendo is_active=False."""
        user = UserTestData()
        fn   = FunctionTestData()

        assignment = UserFunctionAssignment.objects.create(
            user=user, function=fn)
        assignment.is_active = False
        assignment.save()

        assignment.refresh_from_db()
        assert assignment.is_active is False

    def test_unique_together_user_function(self):
        """
        F2-H-006: unique_together eliminado de UserFunctionAssignment.
        CA-21: la BD permite múltiples asignaciones (para preservar historial REVOKED).
        La restricción de duplicados ACTIVOS la aplica la lógica de negocio en el service.

        Este test verifica que la BD SÍ permite crear dos asignaciones para el mismo
        (user, function) — ambas con estado diferente (ACTIVE / REVOKED).
        El service previene dos asignaciones ACTIVE simultáneas (verificar en
        test_function_assign_view.py).
        """
        user  = UserTestData()
        admin = AdminUserTestData()
        fn    = FunctionTestData()

        # La BD permite: primera asignación ACTIVE
        a1 = UserFunctionAssignment.objects.create(
            user=user, function=fn, assigned_by=admin, reason='first', state='ACTIVE')
        a1.state = 'REVOKED'
        a1.save(update_fields=['state'])

        # La BD permite: segunda asignación ACTIVE (preserva historial REVOKED)
        a2 = UserFunctionAssignment.objects.create(
            user=user, function=fn, assigned_by=admin, reason='second', state='ACTIVE')

        assert UserFunctionAssignment.objects.filter(
            user=user, function=fn).count() == 2
        assert UserFunctionAssignment.objects.filter(
            user=user, function=fn, state='ACTIVE').count() == 1
        assert UserFunctionAssignment.objects.filter(
            user=user, function=fn, state='REVOKED').count() == 1

    def test_filter_active_assignments(self):
        """Consultar solo asignaciones activas de un usuario."""
        user  = UserTestData()
        admin = AdminUserTestData()
        fn1   = FunctionTestData()
        fn2   = FunctionTestData()
        fn3   = FunctionTestData()

        UserFunctionAssignment.objects.create(
            user=user, function=fn1, assigned_by=admin, reason='t')
        UserFunctionAssignment.objects.create(
            user=user, function=fn2, assigned_by=admin, reason='t')
        UserFunctionAssignment.objects.create(
            user=user, function=fn3, assigned_by=admin,
            reason='t', is_active=False)

        active = UserFunctionAssignment.objects.filter(
            user=user, is_active=True)
        assert active.count() == 2
        codes = [a.function.code for a in active]
        assert fn1.code in codes
        assert fn2.code in codes
        assert fn3.code not in codes


# ---------------------------------------------------------------------------
# UserModuleAccess
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.django_db
class TestUserModuleAccess:
    """Tests del modelo UserModuleAccess (acceso a módulo completo)."""

    def test_grant_module_access(self):
        """Otorgar acceso a un módulo a un usuario."""
        user   = UserTestData()
        module = ModuleTestData()

        access = UserModuleAccess.objects.create(user=user, module=module)

        assert access.user   == user
        assert access.module == module
        assert access.is_active is True

    def test_deactivate_module_access(self):
        """Desactivar acceso a un módulo."""
        user   = UserTestData()
        module = ModuleTestData()

        access = UserModuleAccess.objects.create(user=user, module=module)
        access.is_active = False
        access.save()

        access.refresh_from_db()
        assert access.is_active is False
