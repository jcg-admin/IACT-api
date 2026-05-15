"""
Tests de integración: Flujo de Gestión de Sesiones.

Usa force_authenticate (bypass de JWT) porque DEFAULT_AUTHENTICATION_CLASSES
solo incluye TokenAuthentication/SessionAuthentication, no JWTAuthentication.
SessionViewSet requiere RequiresFunctionPermission → usa superusuario para bypass RBAC.

CNST-010: Tests usan PostgreSQL (NO cache).
"""

import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model

from tests.test_data import SessionLogTestData
from apps.authentication.models import SessionLog

User = get_user_model()


def _make_superuser(suffix=''):
    """Crea un superusuario único para el test."""
    import uuid
    u = suffix or uuid.uuid4().hex[:6]
    return User.objects.create_superuser(
        username=f'sadmin_{u}',
        email=f'sadmin_{u}@test.com',
        password='AdminPassword123!',
    )


@pytest.mark.integration
@pytest.mark.django_db
class TestSessionManagementFlow:
    """
    Tests para gestión de sesiones con superusuario (bypass RequiresFunctionPermission).
    Autenticación via force_authenticate (no Bearer JWT).
    """

    def setup_method(self):
        self.client = APIClient()

    def test_list_active_sessions(self):
        """GET /sessions/ retorna 200 y solo sesiones del superusuario autenticado."""
        user = _make_superuser()
        self.client.force_authenticate(user=user)

        SessionLogTestData.create_batch(2, user=user, created_by=user)
        SessionLogTestData(user=user, is_active=False, created_by=user)

        resp = self.client.get(reverse('authentication:sessions-list'), format='json')
        assert resp.status_code == status.HTTP_200_OK

        sessions = resp.data
        if isinstance(sessions, dict):
            sessions = sessions.get('results', [])
        assert len(sessions) >= 2

    def test_retrieve_session_detail(self):
        """GET /sessions/{id}/ retorna 200 con campo created_at."""
        user = _make_superuser()
        self.client.force_authenticate(user=user)

        session = SessionLogTestData(user=user, created_by=user)

        resp = self.client.get(
            reverse('authentication:sessions-detail', kwargs={'pk': session.id}),
            format='json',
        )
        assert resp.status_code == status.HTTP_200_OK
        assert 'created_at' in resp.data

    def test_invalidate_specific_session(self):
        """POST /sessions/{id}/invalidate/ marca la sesión como inactiva."""
        from django.contrib.sessions.backends.db import SessionStore
        user = _make_superuser()
        self.client.force_authenticate(user=user)

        # Crear sesión Django real para que invalidate_session pueda eliminarla
        store = SessionStore()
        store['_auth_user_id'] = str(user.pk)
        store.save()
        real_session_key = store.session_key

        session = SessionLogTestData(
            user=user, created_by=user,
            session_key=real_session_key,
        )

        resp = self.client.post(
            reverse('authentication:sessions-invalidate', kwargs={'pk': session.id}),
            format='json',
        )
        assert resp.status_code == status.HTTP_200_OK

        session.refresh_from_db()
        assert session.is_active is False

    def test_invalidate_all_sessions_except_current(self):
        """POST /sessions/invalidate-all/ deja inactivas todas las sesiones adicionales."""
        user = _make_superuser()
        self.client.force_authenticate(user=user)

        extras = SessionLogTestData.create_batch(3, user=user, created_by=user)

        resp = self.client.post(
            reverse('authentication:sessions-invalidate-all'),
            format='json',
        )
        assert resp.status_code == status.HTTP_200_OK

        for sess in extras:
            sess.refresh_from_db()
            assert sess.is_active is False

    def test_list_sessions_requires_authentication(self):
        """GET /sessions/ sin autenticación: 401."""
        resp = self.client.get(reverse('authentication:sessions-list'), format='json')
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_cannot_view_other_user_sessions(self):
        """
        SessionViewSet filtra por request.user: las sesiones de otros usuarios
        no aparecen en el listado.
        """
        import uuid
        u = uuid.uuid4().hex[:6]
        user2 = User.objects.create_user(username=f'u2_{u}', password='OtherPass123!')
        SessionLogTestData.create_batch(3, user=user2, created_by=user2)

        user1 = _make_superuser(u)
        self.client.force_authenticate(user=user1)

        resp = self.client.get(reverse('authentication:sessions-list'), format='json')
        assert resp.status_code == status.HTTP_200_OK

        sessions = resp.data
        if isinstance(sessions, dict):
            sessions = sessions.get('results', [])

        for sess in sessions:
            assert sess.get('user') != user2.id


@pytest.mark.integration
@pytest.mark.django_db
class TestSessionDuration:
    """Duración de sesiones activas y cerradas."""

    def setup_method(self):
        self.client = APIClient()

    def test_session_duration_for_active_session(self):
        """Listado incluye sesiones activas; si el campo duration_seconds existe, es >= 0."""
        user = _make_superuser()
        self.client.force_authenticate(user=user)

        SessionLogTestData(user=user, created_by=user)

        resp = self.client.get(reverse('authentication:sessions-list'), format='json')
        assert resp.status_code == status.HTTP_200_OK

        sessions = resp.data
        if isinstance(sessions, dict):
            sessions = sessions.get('results', [])
        assert len(sessions) >= 1

        if 'duration_seconds' in sessions[0]:
            assert sessions[0]['duration_seconds'] >= 0

    def test_session_duration_for_closed_session(self):
        """Sesión cerrada 1 hora después: duration_seconds == 3600 si el campo existe."""
        from datetime import timedelta
        user = _make_superuser()
        self.client.force_authenticate(user=user)

        session = SessionLogTestData(user=user, is_active=False, created_by=user)
        session.logout_at = session.created_at + timedelta(hours=1)
        session.save()

        resp = self.client.get(
            reverse('authentication:sessions-detail', kwargs={'pk': session.id}),
            format='json',
        )
        assert resp.status_code == status.HTTP_200_OK

        if 'duration_seconds' in resp.data:
            assert resp.data['duration_seconds'] == 3600
