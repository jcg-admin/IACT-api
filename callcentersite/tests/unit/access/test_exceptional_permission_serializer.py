"""
tests/unit/access/test_exceptional_permission_serializer.py

N-002 — Tests del serializer de ExceptionalPermission.
"""
import pytest
from datetime import timedelta
from django.utils import timezone

from apps.access.serializers.exceptional_permission_serializers import (
    ExceptionalPermissionSerializer,
)
from tests.test_data.access_test_data import FunctionTestData
from tests.test_data.user_test_data import UserTestData


@pytest.fixture
def valid_payload(db):
    user = UserTestData()
    function = FunctionTestData()
    now = timezone.now()
    return {
        'user':          user.pk,
        'function':      function.pk,
        'justification': 'A' * 55,  # >= 50 chars
        'valid_from':    now.isoformat(),
        'valid_until':   (now + timedelta(days=7)).isoformat(),
    }


@pytest.mark.django_db
class TestExceptionalPermissionSerializerValidation:
    """N-002: validación de justification y fechas."""

    def test_valid_payload_passes(self, valid_payload):
        serializer = ExceptionalPermissionSerializer(data=valid_payload)
        assert serializer.is_valid(), serializer.errors

    def test_short_justification_fails(self, valid_payload):
        valid_payload['justification'] = 'too short'
        serializer = ExceptionalPermissionSerializer(data=valid_payload)
        assert not serializer.is_valid()
        assert 'justification' in serializer.errors

    def test_empty_justification_fails(self, valid_payload):
        valid_payload['justification'] = ''
        serializer = ExceptionalPermissionSerializer(data=valid_payload)
        assert not serializer.is_valid()
        assert 'justification' in serializer.errors

    def test_inverted_dates_fail(self, valid_payload):
        now = timezone.now()
        valid_payload['valid_from']  = (now + timedelta(days=7)).isoformat()
        valid_payload['valid_until'] = now.isoformat()
        serializer = ExceptionalPermissionSerializer(data=valid_payload)
        assert not serializer.is_valid()
        assert 'valid_until' in serializer.errors or \
               'non_field_errors' in serializer.errors

    def test_equal_dates_fail(self, valid_payload):
        """valid_until debe ser POSTERIOR a valid_from — no puede ser igual."""
        now = timezone.now()
        valid_payload['valid_from']  = now.isoformat()
        valid_payload['valid_until'] = now.isoformat()  # igual, no posterior
        serializer = ExceptionalPermissionSerializer(data=valid_payload)
        assert not serializer.is_valid()
        assert 'non_field_errors' in serializer.errors or \
               'valid_until' in serializer.errors

    def test_past_dates_accepted_if_until_after_from(self, valid_payload):
        """El serializer NO valida que las fechas sean futuras — solo el orden.
        Un permiso retroactivo es válido a nivel de serializer;
        la expiración la gestiona expire_exceptional_permissions().
        """
        now = timezone.now()
        valid_payload['valid_from']  = (now - timedelta(days=2)).isoformat()
        valid_payload['valid_until'] = (now - timedelta(days=1)).isoformat()
        serializer = ExceptionalPermissionSerializer(data=valid_payload)
        # Pasa porque valid_until > valid_from (aunque ambas sean pasadas)
        assert serializer.is_valid(), serializer.errors
