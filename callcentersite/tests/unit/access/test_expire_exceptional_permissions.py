"""
tests/unit/access/test_expire_exceptional_permissions.py

N-007 — Tests de expire_exceptional_permissions().
Permisos con valid_until en el pasado → status='EXPIRED'.
Permisos vigentes no se tocan.
"""
import pytest
from datetime import timedelta
from django.utils import timezone

from apps.access.scheduler import expire_exceptional_permissions
from apps.access.models import ExceptionalPermission
from tests.test_data.access_test_data import ExceptionalPermissionTestData


@pytest.mark.django_db
class TestExpireExceptionalPermissions:
    """N-007: expire_exceptional_permissions()."""

    def test_expires_approved_permission_past_valid_until(self):
        now = timezone.now()
        perm = ExceptionalPermissionTestData(
            status='ACTIVE',
            granted_at=now - timedelta(days=10),
            expires_at=now - timedelta(hours=1),  # pasado
        )

        updated = expire_exceptional_permissions()

        perm.refresh_from_db()
        assert perm.status == 'EXPIRED'
        assert updated >= 1

    def test_does_not_expire_currently_valid_permission(self):
        now = timezone.now()
        perm = ExceptionalPermissionTestData(
            status='ACTIVE',
            granted_at=now - timedelta(hours=1),
            expires_at=now + timedelta(days=7),  # vigente
        )

        expire_exceptional_permissions()

        perm.refresh_from_db()
        assert perm.status == 'ACTIVE'

    def test_does_not_touch_pending_permissions(self):
        now = timezone.now()
        perm = ExceptionalPermissionTestData(
            status='pending',
            granted_at=now - timedelta(days=10),
            expires_at=now - timedelta(hours=1),
        )

        expire_exceptional_permissions()

        perm.refresh_from_db()
        assert perm.status == 'pending'

    def test_does_not_touch_already_revoked_permissions(self):
        now = timezone.now()
        perm = ExceptionalPermissionTestData(
            status='revoked',
            granted_at=now - timedelta(days=10),
            expires_at=now - timedelta(hours=1),
        )

        expire_exceptional_permissions()

        perm.refresh_from_db()
        assert perm.status == 'revoked'

    def test_returns_count_of_updated_permissions(self):
        now = timezone.now()
        ExceptionalPermissionTestData.create_batch(
            3,
            status='ACTIVE',
            granted_at=now - timedelta(days=10),
            expires_at=now - timedelta(hours=1),
        )

        updated = expire_exceptional_permissions()

        assert updated >= 3
