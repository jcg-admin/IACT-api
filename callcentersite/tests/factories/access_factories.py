"""
Factories para apps/access/ (RBAC).

Factory boy para generación de datos test del sistema de permisos.
Basado en análisis ANALISIS_APP_ACCESS_v3_0_0.md (6 partes).

CLEAN_CODE v3.0.1: Nombres auto-documentados.
"""

import factory
from factory.django import DjangoModelFactory
from factory import fuzzy
from apps.access.models import (
    Module,
    Function,
    UserModuleAccess,
    UserFunctionAssignment,
)
# DEUDA TÉCNICA 2026-03-21: Role, UserRoleAssignment, RoleFunctionAssignment
# eliminados en DT-002 junto con UserServiceAccess (RBAC simplificado).
# TODO: Reescribir factories si se reimplementa sistema de Roles.
from .user_factory import UserFactory


# ============================================================================
# MODULE FACTORIES
# ============================================================================

class ModuleFactory(DjangoModelFactory):
    """
    Factory para Module (jerarquía MPTT).
    
    Uso básico:
        module = ModuleFactory(module_id='MODULE_001', name='Dashboard')
    
    Jerarquía:
        parent = ModuleFactory(name='Parent')
        child = ModuleFactory(name='Child', parent=parent)
    """
    
    class Meta:
        model = Module
        django_get_or_create = ('module_id',)
    
    module_id = factory.Sequence(lambda n: f'MODULE_{n:03d}')
    name = factory.Faker('word')
    description = factory.Faker('sentence', nb_words=10)
    parent = None  # Override para jerarquía
    icon = factory.Iterator(['dashboard', 'users', 'reports', 'settings'])
    path = factory.LazyAttribute(lambda obj: f'/modules/{obj.module_id.lower()}')
    order = factory.Sequence(lambda n: n)
    is_active = True


class ModuleWithParentFactory(ModuleFactory):
    """
    Factory para Module con parent (child module).
    
    Uso:
        parent = ModuleFactory()
        child = ModuleWithParentFactory(parent=parent)
    """
    parent = factory.SubFactory(ModuleFactory)


# ============================================================================
# FUNCTION FACTORIES
# ============================================================================

class FunctionFactory(DjangoModelFactory):
    """
    Factory para Function (permisos granulares).
    
    Uso básico:
        function = FunctionFactory(
            function_id='dashboard.view',
            name='Ver Dashboard'
        )
    
    Con módulo:
        module = ModuleFactory()
        function = FunctionFactory(module=module)
    """
    
    class Meta:
        model = Function
        django_get_or_create = ('function_id',)
    
    function_id = factory.Sequence(lambda n: f'function.{n}')
    name = factory.Faker('job')
    description = factory.Faker('sentence', nb_words=12)
    module = factory.SubFactory(ModuleFactory)
    is_active = True


class FunctionCreateFactory(FunctionFactory):
    """Factory para funciones de tipo CREATE."""
    function_id = factory.Sequence(lambda n: f'create.{n}')
    name = factory.LazyAttribute(lambda obj: f'Crear {obj.module.name}')


class FunctionViewFactory(FunctionFactory):
    """Factory para funciones de tipo VIEW."""
    function_id = factory.Sequence(lambda n: f'view.{n}')
    name = factory.LazyAttribute(lambda obj: f'Ver {obj.module.name}')


class FunctionEditFactory(FunctionFactory):
    """Factory para funciones de tipo EDIT."""
    function_id = factory.Sequence(lambda n: f'edit.{n}')
    name = factory.LazyAttribute(lambda obj: f'Editar {obj.module.name}')


class FunctionDeleteFactory(FunctionFactory):
    """Factory para funciones de tipo DELETE."""
    function_id = factory.Sequence(lambda n: f'delete.{n}')
    name = factory.LazyAttribute(lambda obj: f'Eliminar {obj.module.name}')


# ============================================================================
# ASSIGNMENT FACTORIES
# ============================================================================

class UserModuleAccessFactory(DjangoModelFactory):
    """
    Factory para UserModuleAccess (asignación usuario-módulo).
    
    Uso:
        user = UserFactory()
        module = ModuleFactory()
        access = UserModuleAccessFactory(user=user, module=module)
    """
    
    class Meta:
        model = UserModuleAccess
    
    user = factory.SubFactory(UserFactory)
    module = factory.SubFactory(ModuleFactory)
    granted_at = factory.Faker('date_time_this_year')
    granted_by = factory.SubFactory(UserFactory)
    reason = factory.Faker('sentence', nb_words=8)
    is_active = True


class UserFunctionAssignmentFactory(DjangoModelFactory):
    """
    Factory para UserFunctionAssignment (asignación usuario-función).
    
    Uso:
        user = UserFactory()
        function = FunctionFactory()
        assignment = UserFunctionAssignmentFactory(
            user=user,
            function=function
        )
    """
    
    class Meta:
        model = UserFunctionAssignment
    
    user = factory.SubFactory(UserFactory)
    function = factory.SubFactory(FunctionFactory)
    assigned_at = factory.Faker('date_time_this_year')
    assigned_by = factory.SubFactory(UserFactory)
    reason = factory.Faker('sentence', nb_words=8)
    is_active = True


# ============================================================================
# HELPER FACTORIES (Complex scenarios)
# ============================================================================

class UserWithModuleAccessFactory(UserFactory):
    """
    Factory que crea Usuario con acceso a módulo.
    
    Uso:
        user = UserWithModuleAccessFactory()
        # Usuario con 1 módulo asignado automáticamente
    """
    
    @factory.post_generation
    def modules(self, create, extracted, **kwargs):
        if not create:
            return
        
        if extracted:
            # Lista de módulos pasada
            for module in extracted:
                UserModuleAccessFactory(user=self, module=module)
        else:
            # Crear 1 módulo por defecto
            UserModuleAccessFactory(user=self)


class UserWithFunctionFactory(UserFactory):
    """
    Factory que crea Usuario con función asignada.
    
    Uso:
        user = UserWithFunctionFactory()
        # Usuario con 1 función asignada automáticamente
    """
    
    @factory.post_generation
    def functions(self, create, extracted, **kwargs):
        if not create:
            return
        
        if extracted:
            # Lista de funciones pasada
            for function in extracted:
                UserFunctionAssignmentFactory(user=self, function=function)
        else:
            # Crear 1 función por defecto
            UserFunctionAssignmentFactory(user=self)


class CompleteUserFactory(UserFactory):
    """
    Factory que crea Usuario con módulo + función.

    DEUDA TÉCNICA 2026-03-21: Roles eliminados en DT-002.
    El factory ya no asigna rol; solo módulo y función.
    """

    @factory.post_generation
    def complete_access(self, create, extracted, **kwargs):
        if not create:
            return

        # Crear módulo
        module = ModuleFactory()
        UserModuleAccessFactory(user=self, module=module)

        # Crear función
        function = FunctionFactory(module=module)
        UserFunctionAssignmentFactory(user=self, function=function)


# ============================================================================
# TOTAL FACTORIES: 18
# 
# Base Factories (7):
#   - ModuleFactory
#   - ModuleWithParentFactory
#   - FunctionFactory (+ 4 variantes: Create, View, Edit, Delete)
#   - RoleFactory (+ 4 variantes: Admin, Manager, Analyst, Viewer)
# 
# Assignment Factories (4):
#   - UserModuleAccessFactory
#   - UserFunctionAssignmentFactory
#   - UserRoleAssignmentFactory
#   - RoleFunctionAssignmentFactory
# 
# Helper Factories (4):
#   - UserWithModuleAccessFactory
#   - UserWithFunctionFactory
#   - UserWithRoleFactory
#   - CompleteUserFactory
# 
# CLEAN_CODE v3.0.1: Nombres auto-documentados [SUCCESS]
# ============================================================================
