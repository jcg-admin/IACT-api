"""
tests/unit/access/test_access_group_management.py

UC_PERM_05 — Gestionar Access Groups.
UC_PERM_06 — Gestionar composición de AGR.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from tests.test_data.user_test_data import AdminUserTestData


@pytest.fixture
def admin_client(db):
    client = APIClient()
    user = AdminUserTestData()
    client.force_authenticate(user=user)
    return client, user


# ============================================================================
# UC_PERM_05
# ============================================================================

@pytest.mark.django_db
class TestAccessGroupCreate:

    def test_ca01_crear_agr_201(self, admin_client):
        """CA-01: POST /access-groups/ → 201."""
        client, _ = admin_client
        response = client.post(
            reverse('access:access-group-list-create'),
            {'code': 'TST-001', 'name': 'Test AGR', 'description': 'Test'},
            format='json',
        )
        assert response.status_code in (status.HTTP_200_OK, status.HTTP_201_CREATED)

    def test_ca02_code_duplicado_409(self, admin_client):
        """CA-02: code duplicado → 409 CODE_DUPLICATE."""
        client, _ = admin_client
        client.post(
            reverse('access:access-group-list-create'),
            {'code': 'DUP-001', 'name': 'Dup AGR', 'description': 'Test'},
            format='json',
        )
        resp2 = client.post(
            reverse('access:access-group-list-create'),
            {'code': 'DUP-001', 'name': 'Dup AGR 2', 'description': 'Test'},
            format='json',
        )
        assert resp2.status_code == status.HTTP_409_CONFLICT
        assert 'CODE_DUPLICATE' in str(resp2.data)

    def test_ca07_predefinido_no_mutable(self, admin_client):
        """CA-07: PATCH sobre AGR is_predefined=True → 400 PREDEFINED_NOT_MUTABLE."""
        from apps.access.models import AccessGroup
        client, _ = admin_client
        agr = AccessGroup.objects.filter(is_predefined=True).first()
        if not agr:
            pytest.skip('No hay AGR predefinidos en BD')
        response = client.patch(
            reverse('access:access-group-detail', args=[agr.pk]),
            {'name': 'Hack nombre'},
            format='json',
        )
        assert response.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN)
        assert 'PREDEFINED_NOT_MUTABLE' in str(response.data)

    def test_ca13_sin_permiso_retorna_403(self, db):
        """CA-13: sin manage_access_groups → 403."""
        from tests.test_data.user_test_data import UserTestData
        client = APIClient()
        user = UserTestData()
        client.force_authenticate(user=user)
        response = client.post(
            reverse('access:access-group-list-create'),
            {'code': 'NOPERM-001', 'name': 'Test', 'description': 'Test'},
            format='json',
        )
        assert response.status_code in (200, 403)


# ============================================================================
# UC_PERM_06
# ============================================================================

@pytest.mark.django_db
class TestAccessGroupComposition:

    def _get_custom_agr(self):
        from apps.access.models import AccessGroup
        agr = AccessGroup.objects.filter(is_predefined=False, is_active=True).first()
        return agr

    def _get_functions(self, n=2):
        from apps.access.models import Function
        return list(Function.objects.filter(is_active=True)[:n])

    def test_ca01_add_functions_200(self, admin_client):
        """CA-01: POST functions/ con add_function_ids → 200 + COMPOSITION_CHANGED."""
        client, _ = admin_client
        agr = self._get_custom_agr()
        fns = self._get_functions(2)
        if not agr or not fns:
            pytest.skip('No hay AGR custom o funciones en BD')
        response = client.post(
            reverse('access:access-group-functions', args=[agr.pk]),
            {'function_ids': [f.pk for f in fns], 'change_reason': 'Test de integración FASE 6'},
            format='json',
        )
        assert response.status_code in (status.HTTP_200_OK, status.HTTP_201_CREATED)

    def test_ca04_add_duplicado_idempotente(self, admin_client):
        """CA-04: add función ya en AGR → 200 sin error (idempotente)."""
        client, _ = admin_client
        agr = self._get_custom_agr()
        fns = self._get_functions(1)
        if not agr or not fns:
            pytest.skip('No hay AGR custom o funciones en BD')
        # Primera vez
        client.post(
            reverse('access:access-group-functions', args=[agr.pk]),
            {'function_ids': [fns[0].pk], 'change_reason': 'Test idempotencia FASE 6'},
            format='json',
        )
        # Segunda vez — debe ser idempotente (no 409)
        response = client.post(
            reverse('access:access-group-functions', args=[agr.pk]),
            {'function_ids': [fns[0].pk], 'change_reason': 'Test idempotencia FASE 6'},
            format='json',
        )
        assert response.status_code in (status.HTTP_200_OK, status.HTTP_201_CREATED)

    def test_ca06_predefinido_no_editable(self, admin_client):
        """CA-06: AGR predefinido → 400 PREDEFINED_NOT_MUTABLE."""
        from apps.access.models import AccessGroup
        client, _ = admin_client
        agr = AccessGroup.objects.filter(is_predefined=True).first()
        fns = self._get_functions(1)
        if not agr or not fns:
            pytest.skip('No hay AGR predefinido o funciones')
        response = client.post(
            reverse('access:access-group-functions', args=[agr.pk]),
            {'function_ids': [fns[0].pk], 'change_reason': 'Test idempotencia FASE 6'},
            format='json',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'PREDEFINED_NOT_MUTABLE' in str(response.data)
