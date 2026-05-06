import pytest
from django.contrib.auth.models import User
from apps.access.models import Function, UserPermission
"""Tests para modelos Module y UserPermission."""
import pytest
from django.contrib.auth import get_user_model
from apps.access.models import Module, UserPermission

User = get_user_model()


@pytest.mark.django_db
class TestModuleModel:
    """Tests para Module model."""
    
    def test_create_root_module(self):
        """Test crear módulo raíz."""
        module = Module.objects.create(
            code='MOD_Test',
            name='Test Module',
            description='Test',
        )
        assert module.is_root() is True
        assert module.get_level() == 0
    
    def test_create_child_module(self):
        """Test crear módulo hijo."""
        parent = Module.objects.create(code='MOD_Parent', name='Parent')
        child = Module.objects.create(
            code='MOD_Child',
            name='Child',
            parent=parent,
        )
        assert child.is_root() is False
        assert child.get_level() == 1
        assert child.parent == parent
    
    def test_get_ancestors(self):
        """Test obtener ancestros."""
        root = Module.objects.create(code='ROOT', name='Root')
        child1 = Module.objects.create(code='CHILD1', name='Child1', parent=root)
        child2 = Module.objects.create(code='CHILD2', name='Child2', parent=child1)
        
        ancestors = child2.get_ancestors()
        assert len(ancestors) == 2
        assert child1 in ancestors
        assert root in ancestors
    
    def test_soft_delete_module(self):
        """Test soft delete de módulo."""
        module = Module.objects.create(code='MOD_Delete', name='Delete')
        module.delete()
        
        assert module.is_deleted is True
        assert Module.objects.count() == 0
        assert Module.objects.all_with_deleted().count() == 1


@pytest.mark.django_db
class TestUserPermissionModel:
    """Tests para UserPermission model."""
    
    def test_grant_access(self):
        """Test otorgar acceso a módulo."""
        user = User.objects.create_user(username='test')
        module = Module.objects.create(code='MOD_Test', name='Test')
        
        access = UserPermission.objects.create(
            user=user,
            module=module,
        )
        
        assert access.is_active is True
        assert access.user == user
        assert access.module == module
    
    def test_get_user_modules(self):
        """Test obtener módulos de usuario."""
        user = User.objects.create_user(username='test')
        parent = Module.objects.create(code='PARENT', name='Parent')
        child = Module.objects.create(code='CHILD', name='Child', parent=parent)
        
        # Acceso al padre
        UserPermission.objects.create(user=user, module=parent)
        
        # Debe incluir hijo automáticamente
        modules = UserPermission.get_user_modules(user)
        assert parent in modules
        assert child in modules


@pytest.mark.unit
@pytest.mark.django_db
class TestFunction:
    """Tests modelo Function (RBAC atomico)."""
    
    def test_create_function(self):
        """Crear funcion atomica."""
        func = Function.objects.create(
            code='ve_reportes',
            module='MOD_Reports',
            name='Ver Reportes',
            description='Consultar reportes del sistema',
        )
        
        assert func.id is not None
        assert func.code == 've_reportes'
        assert func.module == 'MOD_Reports'
        assert func.is_active is True
    
    def test_function_str(self):
        """__str__ muestra code y module."""
        func = Function.objects.create(
            code='crea_usuarios',
            module='MOD_Users',
            name='Crear Usuarios',
        )
        
        assert str(func) == 'crea_usuarios (MOD_Users)'
    
    def test_function_code_unique(self):
        """Code debe ser unico."""
        Function.objects.create(
            code='test_func',
            module='MOD_Test',
            name='Test'
        )
        
        with pytest.raises(Exception):  # IntegrityError
            Function.objects.create(
                code='test_func',
                module='MOD_Test',
                name='Test2'
            )
    
    def test_function_ordering(self):
        """Funciones ordenadas por module, code."""
        Function.objects.create(code='zz', module='MOD_Z', name='Z')
        Function.objects.create(code='aa', module='MOD_A', name='A')
        Function.objects.create(code='bb', module='MOD_A', name='B')
        
        funcs = list(Function.objects.all())
        
        # Primero MOD_A (aa, bb), luego MOD_Z (zz)
        assert funcs[0].code == 'aa'
        assert funcs[1].code == 'bb'
        assert funcs[2].code == 'zz'


@pytest.mark.unit
@pytest.mark.django_db
class TestUserPermission:
    """Tests asignacion funciones a usuarios."""
    
    def test_assign_function_to_user(self):
        """Asignar funcion a usuario."""
        user = User.objects.create_user('testuser')
        admin = User.objects.create_user('admin')
        func = Function.objects.create(
            code='crea_usuarios',
            module='MOD_Users',
            name='Crear Usuarios',
        )
        
        assignment = UserPermission.objects.create(
            user=user,
            function=func,
            assigned_by=admin,
            reason='Permisos iniciales',
        )
        
        assert assignment.user == user
        assert assignment.function == func
        assert assignment.is_active is True
        assert assignment.assigned_by == admin
        assert assignment.reason == 'Permisos iniciales'
    
    def test_assignment_str(self):
        """__str__ muestra username -> function_code."""
        user = User.objects.create_user('testuser')
        admin = User.objects.create_user('admin')
        func = Function.objects.create(
            code='test_func',
            module='MOD_Test',
            name='Test'
        )
        
        assignment = UserPermission.objects.create(
            user=user,
            function=func,
            assigned_by=admin,
            reason='Test'
        )
        
        assert str(assignment) == 'testuser -> test_func'
    
    def test_get_user_functions(self):
        """Obtener funciones activas de usuario."""
        user = User.objects.create_user('testuser')
        admin = User.objects.create_user('admin')
        
        func1 = Function.objects.create(code='func1', module='MOD1', name='F1')
        func2 = Function.objects.create(code='func2', module='MOD2', name='F2')
        func3 = Function.objects.create(code='func3', module='MOD3', name='F3')
        
        # Asignar func1 y func2 (activas)
        UserPermission.objects.create(
            user=user,
            function=func1,
            assigned_by=admin,
            reason='test'
        )
        UserPermission.objects.create(
            user=user,
            function=func2,
            assigned_by=admin,
            reason='test'
        )
        
        # func3 inactiva
        UserPermission.objects.create(
            user=user,
            function=func3,
            assigned_by=admin,
            reason='test',
            is_active=False
        )
        
        active_funcs = UserPermission.get_user_functions(user)
        
        assert active_funcs.count() == 2
        codes = [a.function.code for a in active_funcs]
        assert 'func1' in codes
        assert 'func2' in codes
        assert 'func3' not in codes
    
    def test_unique_together_user_function(self):
        """Usuario no puede tener misma funcion asignada 2 veces."""
        user = User.objects.create_user('testuser')
        admin = User.objects.create_user('admin')
        func = Function.objects.create(
            code='test',
            module='MOD',
            name='Test'
        )
        
        UserPermission.objects.create(
            user=user,
            function=func,
            assigned_by=admin,
            reason='first'
        )
        
        with pytest.raises(Exception):  # IntegrityError
            UserPermission.objects.create(
                user=user,
                function=func,
                assigned_by=admin,
                reason='second'
            )
