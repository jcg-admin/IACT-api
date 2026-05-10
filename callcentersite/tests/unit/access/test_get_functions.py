"""
tests/unit/access/test_get_functions.py

N-008 — Tests de User.get_functions() con las tres fuentes.
"""
import pytest
from datetime import timedelta
from django.utils import timezone

from apps.access.models import (
    ExceptionalPermission, UserPermission,
    AccessGroup, UserAccessGroup,
)
from tests.test_data.access_test_data import FunctionTestData
from tests.test_data.user_test_data import UserTestData


@pytest.mark.django_db
class TestGetFunctions:
    """N-008: get_functions() incluye las tres fuentes y excluye expirados."""

    def test_returns_empty_list_for_user_without_permissions(self):
        user = UserTestData()
        assert user.get_functions() == []

    def test_includes_direct_user_permission(self):
        user = UserTestData()
        fn = FunctionTestData()
        UserPermission.objects.create(user=user, function=fn)

        codes = user.get_functions()
        assert fn.code in codes

    def test_includes_function_from_access_group(self):
        user = UserTestData()
        fn = FunctionTestData()
        group = AccessGroup.objects.create(
            name='Group N008', code='GRP_N008')
        group.functions.add(fn)
        UserAccessGroup.objects.create(user=user, access_group=group)

        codes = user.get_functions()
        assert fn.code in codes

    def test_includes_active_exceptional_permission(self):
        user = UserTestData()
        fn = FunctionTestData()
        now = timezone.now()
        ExceptionalPermission.objects.create(
            user=user, function=fn,
            justification='J' * 55,
            status='approved',
            valid_from=now - timedelta(hours=1),
            valid_until=now + timedelta(days=7),
        )

        codes = user.get_functions()
        assert fn.code in codes

    def test_excludes_expired_exceptional_permission(self):
        user = UserTestData()
        fn = FunctionTestData()
        now = timezone.now()
        ExceptionalPermission.objects.create(
            user=user, function=fn,
            justification='J' * 55,
            status='approved',
            valid_from=now - timedelta(days=10),
            valid_until=now - timedelta(days=3),  # expirado
        )

        codes = user.get_functions()
        assert fn.code not in codes

    def test_excludes_pending_exceptional_permission(self):
        user = UserTestData()
        fn = FunctionTestData()
        now = timezone.now()
        ExceptionalPermission.objects.create(
            user=user, function=fn,
            justification='J' * 55,
            status='pending',
            valid_from=now,
            valid_until=now + timedelta(days=7),
        )

        codes = user.get_functions()
        assert fn.code not in codes

    def test_union_of_all_three_sources(self):
        user = UserTestData()
        fn_direct = FunctionTestData()
        fn_group = FunctionTestData()
        fn_exceptional = FunctionTestData()

        # Fuente 1
        UserPermission.objects.create(user=user, function=fn_direct)

        # Fuente 2
        group = AccessGroup.objects.create(
            name='Group N008b', code='GRP_N008B')
        group.functions.add(fn_group)
        UserAccessGroup.objects.create(user=user, access_group=group)

        # Fuente 3
        now = timezone.now()
        ExceptionalPermission.objects.create(
            user=user, function=fn_exceptional,
            justification='J' * 55, status='approved',
            valid_from=now - timedelta(hours=1),
            valid_until=now + timedelta(days=7),
        )

        codes = user.get_functions()
        assert fn_direct.code in codes
        assert fn_group.code in codes
        assert fn_exceptional.code in codes

    def test_result_is_sorted(self):
        user = UserTestData()
        for code in ['z_fn', 'a_fn', 'm_fn']:
            fn = FunctionTestData(code=code)
            UserPermission.objects.create(user=user, function=fn)

        codes = user.get_functions()
        assert codes == sorted(codes)

    def test_no_duplicates_when_function_in_multiple_sources(self):
        """La misma función en directo y en grupo aparece una sola vez."""
        user = UserTestData()
        fn = FunctionTestData()

        UserPermission.objects.create(user=user, function=fn)

        group = AccessGroup.objects.create(
            name='Group N008c', code='GRP_N008C')
        group.functions.add(fn)
        UserAccessGroup.objects.create(user=user, access_group=group)

        codes = user.get_functions()
        assert codes.count(fn.code) == 1
