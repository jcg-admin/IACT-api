"""
tests/factories/access_factories.py

Factory Boy factories for apps/access/ models.
All field names follow RA-011 (English identifiers).
"""
from datetime import timedelta

import factory
from django.utils import timezone
from factory.django import DjangoModelFactory

from apps.access.models import (
    Module,
    Function,
    UserPermission,
    AccessGroup,
    UserAccessGroup,
    SeparationRule,
    ExceptionalPermission,
    UserFunctionAssignment,
    UserModuleAccess,
)
from .user_test_data import UserTestData


# ---------------------------------------------------------------------------
# Module
# ---------------------------------------------------------------------------

class ModuleTestData(DjangoModelFactory):
    """Factory for Module."""

    name  = factory.Sequence(lambda n: f'Module {n}')
    code  = factory.Sequence(lambda n: f'MOD_{n:04d}')
    icon  = factory.Iterator(['dashboard', 'users', 'reports', 'settings'])
    order = factory.Sequence(lambda n: n)

    class Meta:
        model = Module
        django_get_or_create = ('code',)


class ChildModuleTestData(ModuleTestData):
    """Factory for a sub-module with a parent."""
    parent = factory.SubFactory(ModuleTestData)
    code   = factory.Sequence(lambda n: f'SUB_{n:04d}')


# ---------------------------------------------------------------------------
# Function
# ---------------------------------------------------------------------------

class FunctionTestData(DjangoModelFactory):
    """
    Factory for Function (granular RBAC unit).

    Usage:
        fn = FunctionTestData()
        fn = FunctionTestData(code='reports.view', permission_django='reports.view')
    """

    module            = factory.SubFactory(ModuleTestData)
    name              = factory.Sequence(lambda n: f'Function {n}')
    code              = factory.Sequence(lambda n: f'TST-{n:03d}')  # v5.4.0 format: MOD-NNN
    permission_django = factory.Sequence(lambda n: f'module.action_{n}')
    description       = factory.Faker('sentence', nb_words=8)
    is_active         = True
    status            = 'activo'

    class Meta:
        model = Function
        django_get_or_create = ('code',)


# ---------------------------------------------------------------------------
# UserPermission
# ---------------------------------------------------------------------------

class UserPermissionTestData(DjangoModelFactory):
    """Factory for direct user-to-function assignment."""

    user     = factory.SubFactory(UserTestData)
    function = factory.SubFactory(FunctionTestData)

    class Meta:
        model = UserPermission


# ---------------------------------------------------------------------------
# M-001 — AccessGroup
# ---------------------------------------------------------------------------

class AccessGroupTestData(DjangoModelFactory):
    """
    Factory for AccessGroup (function bundle assignable to a user).

    Usage:
        group = AccessGroupTestData()
        group = AccessGroupTestData(code='SUPERVISOR_IVR')
        group_with_fns = AccessGroupTestData.create()
        group_with_fns.functions.set([fn1, fn2])
    """

    name        = factory.Sequence(lambda n: f'Access Group {n}')
    code        = factory.Sequence(lambda n: f'GRP_{n:04d}')
    description = factory.Faker('sentence', nb_words=6)
    is_active   = True

    class Meta:
        model = AccessGroup
        django_get_or_create = ('code',)


# ---------------------------------------------------------------------------
# M-004 — UserAccessGroup
# ---------------------------------------------------------------------------

class UserAccessGroupTestData(DjangoModelFactory):
    """
    Factory for UserAccessGroup (user membership in an AccessGroup).

    Usage:
        membership = UserAccessGroupTestData()
        membership = UserAccessGroupTestData(user=user, access_group=group)
    """

    user         = factory.SubFactory(UserTestData)
    access_group = factory.SubFactory(AccessGroupTestData)
    granted_by   = factory.SubFactory(UserTestData)

    class Meta:
        model = UserAccessGroup
        django_get_or_create = ('user', 'access_group')


# ---------------------------------------------------------------------------
# M-002 — SeparationRule
# ---------------------------------------------------------------------------

class SeparationRuleTestData(DjangoModelFactory):
    """
    Factory for SeparationRule (incompatible function pair).

    Usage:
        rule = SeparationRuleTestData()
        rule = SeparationRuleTestData(
            function_a=fn_a, function_b=fn_b, status='active')
    """

    name          = factory.Sequence(lambda n: f'Separation Rule {n}')
    function_a    = factory.SubFactory(FunctionTestData)
    function_b    = factory.SubFactory(FunctionTestData)
    justification = factory.Faker('paragraph', nb_sentences=2)
    status        = 'active'
    created_by    = factory.SubFactory(UserTestData)

    class Meta:
        model = SeparationRule


# ---------------------------------------------------------------------------
# M-003 — ExceptionalPermission
# ---------------------------------------------------------------------------

class ExceptionalPermissionTestData(DjangoModelFactory):
    """
    Factory for ExceptionalPermission (temporary out-of-band permission).

    Usage:
        pending = ExceptionalPermissionTestData()
        approved = ExceptionalPermissionTestData(
            status='approved',
            granted_by=admin_user)
        expired = ExceptionalPermissionTestData(
            status='approved',
            valid_from=timezone.now() - timedelta(days=10),
            valid_until=timezone.now() - timedelta(days=3))
    """

    user          = factory.SubFactory(UserTestData)
    function      = factory.SubFactory(FunctionTestData)
    justification = factory.Faker('paragraph', nb_sentences=5)
    status        = 'pending'
    valid_from    = factory.LazyFunction(timezone.now)
    valid_until   = factory.LazyFunction(
        lambda: timezone.now() + timedelta(days=7))
    granted_by    = None

    class Meta:
        model = ExceptionalPermission


class ApprovedExceptionalPermissionTestData(ExceptionalPermissionTestData):
    """Pre-approved ExceptionalPermission, currently active."""
    status     = 'approved'
    granted_by = factory.SubFactory(UserTestData)


class ExpiredExceptionalPermissionTestData(ExceptionalPermissionTestData):
    """Expired ExceptionalPermission — valid_until in the past."""
    status      = 'approved'
    granted_by  = factory.SubFactory(UserTestData)
    valid_from  = factory.LazyFunction(
        lambda: timezone.now() - timedelta(days=10))
    valid_until = factory.LazyFunction(
        lambda: timezone.now() - timedelta(days=3))


# ---------------------------------------------------------------------------
# UserFunctionAssignment (supplementary)
# ---------------------------------------------------------------------------

class UserFunctionAssignmentTestData(DjangoModelFactory):
    """Factory for UserFunctionAssignment (full assignment with history)."""

    user        = factory.SubFactory(UserTestData)
    function    = factory.SubFactory(FunctionTestData)
    reason      = factory.Faker('sentence', nb_words=6)
    is_active   = True
    assigned_by = factory.SubFactory(UserTestData)

    class Meta:
        model = UserFunctionAssignment
        django_get_or_create = ('user', 'function')


# ---------------------------------------------------------------------------
# UserModuleAccess (supplementary)
# ---------------------------------------------------------------------------

class UserModuleAccessTestData(DjangoModelFactory):
    """Factory for UserModuleAccess (coarse-grained module access)."""

    user       = factory.SubFactory(UserTestData)
    module     = factory.SubFactory(ModuleTestData)
    is_active  = True
    granted_by = factory.SubFactory(UserTestData)

    class Meta:
        model = UserModuleAccess
        django_get_or_create = ('user', 'module')


# ---------------------------------------------------------------------------
# Compatibility aliases (referenced by tests/factories/__init__.py)
# ---------------------------------------------------------------------------

ModuleWithParentTestData = ChildModuleTestData


class FunctionCreateTestData(FunctionTestData):
    code              = factory.Sequence(lambda n: f'create_{n:04d}')
    permission_django = factory.Sequence(lambda n: f'module.create_{n}')


class FunctionViewTestData(FunctionTestData):
    code              = factory.Sequence(lambda n: f'view_{n:04d}')
    permission_django = factory.Sequence(lambda n: f'module.view_{n}')


class FunctionEditTestData(FunctionTestData):
    code              = factory.Sequence(lambda n: f'edit_{n:04d}')
    permission_django = factory.Sequence(lambda n: f'module.edit_{n}')


class FunctionDeleteTestData(FunctionTestData):
    code              = factory.Sequence(lambda n: f'delete_{n:04d}')
    permission_django = factory.Sequence(lambda n: f'module.delete_{n}')


class UserWithModuleAccessTestData(UserTestData):
    @factory.post_generation
    def permissions(self, create, extracted, **kwargs):
        if not create:
            return
        UserPermissionTestData(user=self)


class UserWithFunctionTestData(UserTestData):
    @factory.post_generation
    def functions(self, create, extracted, **kwargs):
        if not create:
            return
        for fn in (extracted or []):
            UserPermissionTestData(user=self, function=fn)
        if not extracted:
            UserPermissionTestData(user=self)


class CompleteUserTestData(UserTestData):
    @factory.post_generation
    def complete_access(self, create, extracted, **kwargs):
        if not create:
            return
        group = AccessGroupTestData()
        UserAccessGroupTestData(user=self, access_group=group)
        UserPermissionTestData(user=self, function=FunctionTestData())
