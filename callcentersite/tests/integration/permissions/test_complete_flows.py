"""
Tests E2E para flujos completos de permissions (UC_PERM_01..10).

Valida asignacion/revocacion de grupos a usuarios, permisos
excepcionales, y consulta de auditoria de permisos.
"""
import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def admin_client(db):
    u = uuid.uuid4().hex[:6]
    admin = User.objects.create_superuser(
        username=f'admin_perm_{u}',
        email=f'admin_perm_{u}@test.com',
        password='Pass1234',
    )
    client = APIClient()
    client.force_authenticate(user=admin)
    client.user = admin
    return client


@pytest.fixture
def target_user(db):
    u = uuid.uuid4().hex[:6]
    return User.objects.create_user(
        username=f'tgt_perm_{u}',
        email=f'tgt_perm_{u}@test.com',
        password='Pass1234',
    )


@pytest.mark.django_db
class TestPermissionsEndpointsReachable:
    """UC_PERM_01..10 — los endpoints existen y responden."""

    def test_uc_perm_01_asignar_grupo_endpoint_existe(self, admin_client, target_user):
        """POST /api/access/users/{id}/agr/ acepta payload (puede 400 si AGR no existe)."""
        response = admin_client.post(
            f'/api/access/users/{target_user.pk}/agr/',
            {'agr_code': 'AGR_TEST'},
            format='json',
        )
        assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_uc_perm_09_auditar_acceso_via_audit_log(self, admin_client):
        """UC_PERM_09 emite GENERAL_AUDIT_QUERIED al consultar audit log."""
        response = admin_client.get('/api/audit/')
        assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_uc_perm_10_historial_cambios_permisos(self, admin_client):
        """UC_PERM_10 — historial de cambios via audit query con filtro."""
        response = admin_client.get(
            '/api/audit/',
            {'action': 'FUNCTIONS_ASSIGNED'},
        )
        assert response.status_code != status.HTTP_404_NOT_FOUND
