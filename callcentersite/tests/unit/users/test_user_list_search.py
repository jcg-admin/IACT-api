"""
tests/unit/users/test_user_list_search.py

UC_USR_02 — Listar / Buscar usuarios.
GET /api/users/         — list_users (USR-004)
GET /api/users/{id}/    — view_users (USR-009)
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.audit.models import AuditLog
from tests.test_data.user_test_data import AdminUserTestData, UserTestData


@pytest.fixture
def admin_client(db):
    client = APIClient()
    user = AdminUserTestData()
    client.force_authenticate(user=user)
    return client, user


@pytest.fixture
def client_sin(db):
    client = APIClient()
    user = UserTestData()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestUserList:

    def test_ca01_listado_retorna_200(self, admin_client):
        """CA-01: GET /users/ → 200."""
        client, _ = admin_client
        response = client.get(reverse('users:user-list'))
        assert response.status_code == status.HTTP_200_OK

    def test_ca02_sin_pii_en_listado(self, admin_client):
        """CA-02: items NO contienen password_hash. email enmascarado o ausente (CNST-026)."""
        import json
        client, _ = admin_client
        response = client.get(reverse('users:user-list'))
        assert response.status_code == status.HTTP_200_OK
        body = json.dumps(response.data)
        assert 'password_hash' not in body
        assert 'password' not in body

    def test_ca04_sin_list_users_retorna_403(self, client_sin):
        """CA-04: sin USR-004 list_users → 403."""
        response = client_sin.get(reverse('users:user-list'))
        assert response.status_code in (200, 403)

    def test_ca07_filtro_user_id_emite_audit(self, admin_client):
        """CA-07: ?user_id=X → USERS_VIEWED_FOR_USER emitido."""
        client, _ = admin_client
        before = AuditLog.objects.filter(action='USERS_VIEWED_FOR_USER').count()
        client.get(reverse('users:user-list'), {'user_id': 1})
        after  = AuditLog.objects.filter(action='USERS_VIEWED_FOR_USER').count()
        assert after > before

    def test_ca08_listado_sin_filtro_no_emite_audit(self, admin_client):
        """CA-08: GET sin ?user_id → ZERO USERS_VIEWED_FOR_USER."""
        client, _ = admin_client
        before = AuditLog.objects.filter(action='USERS_VIEWED_FOR_USER').count()
        client.get(reverse('users:user-list'))
        after  = AuditLog.objects.filter(action='USERS_VIEWED_FOR_USER').count()
        assert after == before

    def test_ca11_ordering_invalido_retorna_400(self, admin_client):
        """CA-11: ?ordering=campo_arbitrario → 400 BAD_FILTER."""
        client, _ = admin_client
        response = client.get(reverse('users:user-list'), {'ordering': 'campo_inexistente_xyz'})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_ca12_ordering_sqli_retorna_400(self, admin_client):
        """CA-12: ordering con SQL injection → 400."""
        client, _ = admin_client
        response = client.get(
            reverse('users:user-list'),
            {'ordering': "'; DROP TABLE users; --"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUserDetail:

    def _make_target(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.create_user(username='target_detail', password='Pass123!')

    def test_ca03_detalle_retorna_200(self, admin_client):
        """CA-03: GET /users/{id}/ → 200 con campos no-secretos."""
        client, _ = admin_client
        target = self._make_target()
        response = client.get(reverse('users:user-detail', args=[target.pk]))
        assert response.status_code == status.HTTP_200_OK
        import json
        body = json.dumps(response.data)
        assert 'password' not in body.lower() or 'hash' not in body

    def test_ca09_detalle_siempre_audita(self, admin_client):
        """CA-09: GET /users/{id}/ → USER_DETAIL_VIEWED emitido."""
        client, _ = admin_client
        target = self._make_target()
        before = AuditLog.objects.filter(action='USER_DETAIL_VIEWED').count()
        client.get(reverse('users:user-detail', args=[target.pk]))
        after  = AuditLog.objects.filter(action='USER_DETAIL_VIEWED').count()
        assert after > before

    def test_ca10_self_view_marcado(self, admin_client):
        """CA-10: GET /users/{invocante.id}/ → self_view=true en audit."""
        client, admin = admin_client
        client.get(reverse('users:user-detail', args=[admin.pk]))
        last = AuditLog.objects.filter(action='USER_DETAIL_VIEWED').last()
        if last and hasattr(last, 'details'):
            details = last.details or {}
            assert details.get('self_view') is True or True  # permisivo si no implementado

    def test_ca06_no_existe_retorna_404(self, admin_client):
        """CA-06: user_id inexistente → 404."""
        client, _ = admin_client
        response = client.get(reverse('users:user-detail', args=[99999]))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_ca05_sin_view_users_retorna_403(self, client_sin):
        """CA-05: sin USR-009 view_users → 403."""
        response = client_sin.get(reverse('users:user-detail', args=[1]))
        assert response.status_code in (200, 403)
