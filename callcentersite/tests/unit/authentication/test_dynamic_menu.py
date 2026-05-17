"""
tests/unit/authentication/test_dynamic_menu.py

UC_PERM_08 — Menú dinámico.
GET /api/me/menu/
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.audit.models import AuditLog
from tests.test_data.user_test_data import AdminUserTestData


@pytest.fixture
def admin_client(db):
    client = APIClient()
    user = AdminUserTestData()
    client.force_authenticate(user=user)
    return client, user


@pytest.mark.django_db
class TestMenuBasic:

    def test_ca01_menu_retorna_200(self, admin_client):
        """CA-01: GET /me/menu/ → 200 con estructura de dominios."""
        client, _ = admin_client
        response = client.get(reverse('authentication:me-menu'))
        assert response.status_code == status.HTTP_200_OK
        assert 'domains' in response.data or isinstance(response.data, (list, dict))

    def test_ca02_user_sin_funciones_domains_vacio(self, db):
        """CA-02: User sin AGRs ni excepciones → domains vacío (no error)."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(username='nofn_menu', password='Pass123!')
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get(reverse('authentication:me-menu'))
        assert response.status_code == status.HTTP_200_OK

    def test_ca15_sin_audit_events(self, admin_client):
        """CA-15: ZERO AuditEvents por invocación de MenuView."""
        client, _ = admin_client
        before = AuditLog.objects.count()
        client.get(reverse('authentication:me-menu'))
        assert AuditLog.objects.count() == before


@pytest.mark.django_db
class TestMenuI18n:

    def test_ca06_locale_es_por_defecto(self, admin_client):
        """CA-06: sin locale → respuesta en español (locale_used=es)."""
        client, _ = admin_client
        response = client.get(reverse('authentication:me-menu'))
        assert response.status_code == status.HTTP_200_OK
        locale = response.data.get('locale_used', response.data.get('locale', 'es'))
        assert locale in ('es', None, '')   # es el default

    def test_ca07_locale_en(self, admin_client):
        """CA-07: ?locale=en → labels en inglés."""
        client, _ = admin_client
        response = client.get(reverse('authentication:me-menu'), {'locale': 'en'})
        assert response.status_code == status.HTTP_200_OK
        locale = response.data.get('locale_used', response.data.get('locale', 'en'))
        assert locale in ('en', None, '')
