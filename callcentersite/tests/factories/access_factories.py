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
from .user_factory import UserFactory


# ---------------------------------------------------------------------------
# Module
# ---------------------------------------------------------------------------

class ModuleFactory(DjangoModelFactory):
    """Factory for Module."""

    name  = factory.Sequence(lambda n: f'Module {n}')
    code  = factory.Sequence(lambda n: f'MOD_{n:04d}')
    icon  = factory.Iterator(['dashboard', 'users', 'reports', 'settings'])
    order = factory.Sequence(lambda n: n)

    class Meta:
        model = Module
        django_get_or_create = ('code',)


class ChildModuleFactory(ModuleFactory):
    """Factory for a sub-module with a parent."""
    parent = factory.SubFactory(ModuleFactory)
    code   = factory.Sequence(lambda n: f'SUB_{n:04d}')


# ---------------------------------------------------------------------------
# Function
# ---------------------------------------------------------------------------

class FunctionFactory(DjangoModelFactory):
    """
    Factory for Function (granular RBAC unit).

    Usage:
        fn = FunctionFactory()
        fn = FunctionFactory(code='reports.view', permission_django='reports.view')
    """

    module            = factory.SubFactory(ModuleFactory)
    name              = factory.Sequence(lambda n: f'Function {n}')
    code              = factory.Sequence(lambda n: f'fn_{n:04d}')
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

class UserPermissionFactory(DjangoModelFactory):
    """Factory for direct user-to-function assignment."""

    user     = factory.SubFactory(UserFactory)
    function = factory.SubFactory(FunctionFactory)

    class Meta:
        model = UserPermission


# ---------------------------------------------------------------------------
# M-001 — AccessGroup
# ---------------------------------------------------------------------------

class AccessGroupFactory(DjangoModelFactory):
    """
    Factory for AccessGroup (function bundle assignable to a user).

    Usage:
        group = AccessGroupFactory()
        group = AccessGroupFactory(code='SUPERVISOR_IVR')
        group_with_fns = AccessGroupFactory.create()
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

class UserAccessGroupFactory(DjangoModelFactory):
    """
    Factory for UserAccessGroup (user membership in an AccessGroup).

    Usage:
        membership = UserAccessGroupFactory()
        membership = UserAccessGroupFactory(user=user, access_group=group)
    """

    user         = factory.SubFactory(UserFactory)
    access_group = factory.SubFactory(AccessGroupFactory)
    granted_by   = factory.SubFactory(UserFactory)

    class Meta:
        model = UserAccessGroup
        django_get_or_create = ('user', 'access_group')


# ---------------------------------------------------------------------------
# M-002 — SeparationRule
# ---------------------------------------------------------------------------

class SeparationRuleFactory(DjangoModelFactory):
    """
    Factory for SeparationRule (incompatible function pair).

    Usage:
        rule = SeparationRuleFactory()
        rule = SeparationRuleFactory(
            function_a=fn_a, function_b=fn_b, status='active')
    """

    name          = factory.Sequence(lambda n: f'Separation Rule {n}')
    function_a    = factory.SubFactory(FunctionFactory)
    function_b    = factory.SubFactory(FunctionFactory)
    justification = factory.Faker('paragraph', nb_sentences=2)
    status        = 'active'
    created_by    = factory.SubFactory(UserFactory)

    class Meta:
        model = SeparationRule


# ---------------------------------------------------------------------------
# M-003 — ExceptionalPermission
# ---------------------------------------------------------------------------

class ExceptionalPermissionFactory(DjangoModelFactory):
    """
    Factory for ExceptionalPermission (temporary out-of-band permission).

    Usage:
        pending = ExceptionalPermissionFactory()
        approved = ExceptionalPermissionFactory(
            status='approved',
            granted_by=admin_user)
        expired = ExceptionalPermissionFactory(
            status='approved',
            valid_from=timezone.now() - timedelta(days=10),
            valid_until=timezone.now() - timedelta(days=3))
    """

    user          = factory.SubFactory(UserFactory)
    function      = factory.SubFactory(FunctionFactory)
    justification = factory.Faker('paragraph', nb_sentences=5)
    status        = 'pending'
    valid_from    = factory.LazyFunction(timezone.now)
    valid_until   = factory.LazyFunction(
        lambda: timezone.now() + timedelta(days=7))
    granted_by    = None

    class Meta:
        model = ExceptionalPermission


class ApprovedExceptionalPermissionFactory(ExceptionalPermissionFactory):
    """Pre-approved ExceptionalPermission, currently active."""
    status     = 'approved'
    granted_by = factory.SubFactory(UserFactory)


class ExpiredExceptionalPermissionFactory(ExceptionalPermissionFactory):
    """Expired ExceptionalPermission — valid_until in the past."""
    status      = 'approved'
    granted_by  = factory.SubFactory(UserFactory)
    valid_from  = factory.LazyFunction(
        lambda: timezone.now() - timedelta(days=10))
    valid_until = factory.LazyFunction(
        lambda: timezone.now() - timedelta(days=3))


# ---------------------------------------------------------------------------
# UserFunctionAssignment (supplementary)
# ---------------------------------------------------------------------------

class UserFunctionAssignmentFactory(DjangoModelFactory):
    """Factory for UserFunctionAssignment (full assignment with history)."""

    user        = factory.SubFactory(UserFactory)
    function    = factory.SubFactory(FunctionFactory)
    reason      = factory.Faker('sentence', nb_words=6)
    is_active   = True
    assigned_by = factory.SubFactory(UserFactory)

    class Meta:
        model = UserFunctionAssignment
        django_get_or_create = ('user', 'function')


# ---------------------------------------------------------------------------
# UserModuleAccess (supplementary)
# ---------------------------------------------------------------------------

class UserModuleAccessFactory(DjangoModelFactory):
    """Factory for UserModuleAccess (coarse-grained module access)."""

    user       = factory.SubFactory(UserFactory)
    module     = factory.SubFactory(ModuleFactory)
    is_active  = True
    granted_by = factory.SubFactory(UserFactory)

    class Meta:
        model = UserModuleAccess
        django_get_or_create = ('user', 'module')


# ---------------------------------------------------------------------------
# Compatibility aliases (referenced by tests/factories/__init__.py)
# ---------------------------------------------------------------------------

ModuleWithParentFactory = ChildModuleFactory


class FunctionCreateFactory(FunctionFactory):
    code              = factory.Sequence(lambda n: f'create_{n:04d}')
    permission_django = factory.Sequence(lambda n: f'module.create_{n}')


class FunctionViewFactory(FunctionFactory):
    code              = factory.Sequence(lambda n: f'view_{n:04d}')
    permission_django = factory.Sequence(lambda n: f'module.view_{n}')


class FunctionEditFactory(FunctionFactory):
    code              = factory.Sequence(lambda n: f'edit_{n:04d}')
    permission_django = factory.Sequence(lambda n: f'module.edit_{n}')


class FunctionDeleteFactory(FunctionFactory):
    code              = factory.Sequence(lambda n: f'delete_{n:04d}')
    permission_django = factory.Sequence(lambda n: f'module.delete_{n}')


class UserWithModuleAccessFactory(UserFactory):
    @factory.post_generation
    def permissions(self, create, extracted, **kwargs):
        if not create:
            return
        UserPermissionFactory(user=self)


class UserWithFunctionFactory(UserFactory):
    @factory.post_generation
    def functions(self, create, extracted, **kwargs):
        if not create:
            return
        for fn in (extracted or []):
            UserPermissionFactory(user=self, function=fn)
        if not extracted:
            UserPermissionFactory(user=self)


class CompleteUserFactory(UserFactory):
    @factory.post_generation
    def complete_access(self, create, extracted, **kwargs):
        if not create:
            return
        group = AccessGroupFactory()
        UserAccessGroupFactory(user=self, access_group=group)
        UserPermissionFactory(user=self, function=FunctionFactory())
