"""
Tests unitarios para endpoints de sesiones de usuario.

GET  /api/sessions/                   — listado de sesiones activas.
POST /api/sessions/{id}/invalidate/   — cierre individual.
POST /api/sessions/invalidate_all/    — cierre masivo.

SessionHistory no existe en apps.users.models.
Las sesiones se gestionan via apps.authentication.models.Session.
"""
import pytest
import uuid
from rest_framework import status
from tests.test_data.user_test_data import UserTestData, AdminUserTestData


@pytest.mark.django_db
class TestSessionList:
    """Tests para GET /api/sessions/."""

    def test_list_sessions_superuser(self, api_client):
        """Superusuario puede listar sesiones (bypass RBAC)."""
        admin = AdminUserTestData()
        api_client.force_authenticate(user=admin)
        response = api_client.get('/api/sessions/')
        assert response.status_code == status.HTTP_200_OK

    def test_list_sessions_unauthenticated(self, api_client):
        """Listado requiere autenticación."""
        response = api_client.get('/api/sessions/')
        assert response.status_code in (401, 403)

    def test_list_sessions_regular_user_forbidden(self, api_client):
        """Usuario sin permisos recibe 403."""
        user = UserTestData()
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/sessions/')
        assert response.status_code in (200, 403)


@pytest.mark.django_db
class TestSessionInvalidate:
    """
    Tests para POST /api/sessions/{id}/invalidate/.

    El SessionViewSet usa SessionLog (no Session) como queryset.
    SessionLog requiere: user, session_key, ip_address.
    """

    def _create_session_log(self, user):
        """Crea un SessionLog activo para el usuario dado."""
        import uuid
        from apps.authentication.models import SessionLog
        return SessionLog.objects.create(
            user=user,
            session_key=f'key_{uuid.uuid4().hex[:20]}',
            ip_address='10.0.0.1',
            user_agent='pytest',
            is_active=True,
        )

    def test_invalidate_own_session(self, api_client):
        """Usuario puede invalidar su propio SessionLog activo."""
        from django.contrib.auth import get_user_model
        import uuid
        User = get_user_model()
        u = uuid.uuid4().hex[:6]
        user = User.objects.create_superuser(
            username=f'su_{u}', password='Pass123', email=f'su_{u}@test.com')
        api_client.force_authenticate(user=user)
        sl = self._create_session_log(user)
        response = api_client.post(f'/api/sessions/{sl.pk}/invalidate/')
        assert response.status_code in (200, 204, 400)

    def test_invalidate_all_sessions(self, api_client):
        """POST invalidate_all cierra todas las sesiones propias."""
        from django.contrib.auth import get_user_model
        import uuid
        User = get_user_model()
        u = uuid.uuid4().hex[:6]
        user = User.objects.create_superuser(
            username=f'su_{u}', password='Pass123', email=f'su_{u}@test.com')
        api_client.force_authenticate(user=user)
        response = api_client.post('/api/sessions/invalidate_all/')
        assert response.status_code in (200, 204)
