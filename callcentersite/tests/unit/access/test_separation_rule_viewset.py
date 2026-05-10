"""
tests/unit/access/test_separation_rule_viewset.py

N-004 — Tests del SeparationRuleViewSet.
GET /check/ retorna tiene_conflicto según reglas activas.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from tests.test_data.access_test_data import (
    FunctionTestData,
    SeparationRuleTestData,
)
from tests.test_data.user_test_data import AdminUserTestData


@pytest.fixture
def client_with_view_permission(db, api_client):
    user = AdminUserTestData()
    api_client.force_authenticate(user=user)
    from apps.access.models import UserPermission
    fn = FunctionTestData(
        code='access.view_separation_rules',
        permission_django='access.view_separation_rules',
    )
    UserPermission.objects.get_or_create(user=user, function=fn)
    return api_client


@pytest.mark.django_db
class TestSeparationRuleCheckEndpoint:
    """N-004: GET /api/access/separation-rules/check/"""

    def test_returns_conflict_when_rule_exists(self, client_with_view_permission):
        fn_a = FunctionTestData()
        fn_b = FunctionTestData()
        SeparationRuleTestData(
            function_a=fn_a, function_b=fn_b, status='active')

        url = reverse('access:separationrule-check-conflict')
        response = client_with_view_permission.get(
            url, {'function_a': fn_a.pk, 'function_b': fn_b.pk})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['tiene_conflicto'] is True
        assert response.data['regla'] is not None

    def test_returns_no_conflict_when_no_rule(self, client_with_view_permission):
        fn_a = FunctionTestData()
        fn_b = FunctionTestData()

        url = reverse('access:separationrule-check-conflict')
        response = client_with_view_permission.get(
            url, {'function_a': fn_a.pk, 'function_b': fn_b.pk})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['tiene_conflicto'] is False
        assert response.data['regla'] is None

    def test_detects_conflict_in_reverse_order(self, client_with_view_permission):
        """La regla (A, B) se detecta también cuando se consulta (B, A)."""
        fn_a = FunctionTestData()
        fn_b = FunctionTestData()
        SeparationRuleTestData(
            function_a=fn_a, function_b=fn_b, status='active')

        url = reverse('access:separationrule-check-conflict')
        response = client_with_view_permission.get(
            url, {'function_a': fn_b.pk, 'function_b': fn_a.pk})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['tiene_conflicto'] is True

    def test_suspended_rule_does_not_generate_conflict(
            self, client_with_view_permission):
        fn_a = FunctionTestData()
        fn_b = FunctionTestData()
        SeparationRuleTestData(
            function_a=fn_a, function_b=fn_b, status='suspended')

        url = reverse('access:separationrule-check-conflict')
        response = client_with_view_permission.get(
            url, {'function_a': fn_a.pk, 'function_b': fn_b.pk})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['tiene_conflicto'] is False
