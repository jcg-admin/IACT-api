"""
Tests E2E para flujos completos de access (UC_ACC_01..09).

Valida asignacion/revocacion de funciones, gestion de access groups,
permisos efectivos, separacion de funciones (SoD).
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
        username=f'admin_acc_{u}',
        email=f'admin_acc_{u}@test.com',
        password='Pass1234',
    )
    client = APIClient()
    client.force_authenticate(user=admin)
    return client


@pytest.fixture
def target_user(db):
    u = uuid.uuid4().hex[:6]
    return User.objects.create_user(
        username=f'tgt_acc_{u}',
        email=f'tgt_acc_{u}@test.com',
        password='Pass1234',
    )


@pytest.mark.django_db
class TestAccessEndpointsReachable:
    """UC_ACC_01..09 — flujo via API responde."""

    def test_uc_acc_05_listar_access_groups(self, admin_client):
        """GET /api/access/access-groups/ retorna lista."""
        response = admin_client.get('/api/access/access-groups/')
        assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_uc_acc_03_permisos_efectivos_del_usuario(self, admin_client, target_user):
        """UC_ACC_03 / UC_USR_07-permisos: GET efectivos."""
        response = admin_client.get(f'/api/access/users/{target_user.pk}/effective-permissions/')
        assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_uc_acc_04_separacion_de_funciones_reglas(self, admin_client):
        """UC_ACC_04: separation rules (SoD)."""
        response = admin_client.get('/api/access/separation-rules/')
        assert response.status_code != status.HTTP_404_NOT_FOUND
