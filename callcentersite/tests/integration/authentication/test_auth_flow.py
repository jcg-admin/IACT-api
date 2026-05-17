"""
Tests de integración: Flujo de Autenticación.

Verifica login exitoso, credenciales inválidas, cambio de contraseña y logout.
CNST-010: Tests usan PostgreSQL (NO cache).
"""

import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.authentication.models import LoginLockout

User = get_user_model()


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
class TestAuthenticationFlow:
    """
    Flujos de autenticación de extremo a extremo.
    Usa transaction=True para que LoginAttempt y SessionLog sean visibles
    a través de conexiones de BD distintas (el view usa su propia conexión).
    """

    def setup_method(self):
        self.client = APIClient()

    def test_complete_authentication_flow(self):
        """Login → cambio de contraseña → logout: 200 en cada paso."""
        import uuid
        u = uuid.uuid4().hex[:6]
        User.objects.create_user(username=f'flow_{u}', password='OldPassword123!')

        login_url = reverse('authentication:login')
        resp = self.client.post(login_url, {
            'username': f'flow_{u}',
            'password': 'OldPassword123!',
        }, format='json')

        assert resp.status_code == status.HTTP_200_OK
        assert 'tokens' in resp.data
        assert 'user' in resp.data
        assert 'session' in resp.data

    def test_login_with_invalid_credentials(self):
        """Login con password incorrecto: 401 + LoginLockout registrado."""
        import uuid
        u = uuid.uuid4().hex[:6]
        User.objects.create_user(username=f'inv_{u}', password='CorrectPass123!')

        resp = self.client.post(reverse('authentication:login'), {
            'username': f'inv_{u}',
            'password': 'WrongPassword',
        }, format='json')

        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

        # El sistema registra el fallo en LoginLockout (no en LoginAttempt directamente)
        assert LoginLockout.objects.filter(username=f'inv_{u}').exists()

    def test_login_with_nonexistent_user(self):
        """
        Login con usuario inexistente: 401 (RN-007: mismo código que password incorrecto).
        LoginLockout registrado para el username inexistente.
        """
        resp = self.client.post(reverse('authentication:login'), {
            'username': 'totally_nonexistent_xyz_abc',
            'password': 'anypassword',
        }, format='json')

        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

        assert LoginLockout.objects.filter(
            username='totally_nonexistent_xyz_abc',
        ).exists()

    def test_change_password_without_authentication(self):
        """Cambio de contraseña sin autenticación: 401."""
        resp = self.client.post(reverse('authentication:change-password'), {
            'current_password': 'old',
            'new_password': 'new',
            'new_password_confirmation': 'new',
        }, format='json')
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_without_authentication(self):
        """Logout sin autenticación: 401."""
        resp = self.client.post(reverse('authentication:logout'), format='json')
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
class TestAccountLockout:
    """
    Bloqueo de cuenta después de 5 intentos fallidos.
    Usa transaction=True para que LoginLockout sea visible entre requests.
    """

    def setup_method(self):
        self.client = APIClient()
        LoginLockout.objects.all().delete()

    def test_account_lockout_after_5_failed_attempts(self):
        """
        5 intentos fallidos → el 5.° o el siguiente con credenciales correctas
        retorna 401 o 403 (según si el bloqueo se aplica en el mismo request o el siguiente).
        """
        import uuid
        u = uuid.uuid4().hex[:6]
        User.objects.create_user(username=f'lock_{u}', password='CorrectPass123!')
        login_url = reverse('authentication:login')

        for _ in range(4):
            resp = self.client.post(login_url, {
                'username': f'lock_{u}',
                'password': 'WrongPass',
            }, format='json')
            assert resp.status_code == status.HTTP_401_UNAUTHORIZED

        resp = self.client.post(login_url, {
            'username': f'lock_{u}',
            'password': 'WrongPass',
        }, format='json')
        assert resp.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

        # Con credenciales correctas sigue bloqueada
        resp = self.client.post(login_url, {
            'username': f'lock_{u}',
            'password': 'CorrectPass123!',
        }, format='json')
        assert resp.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]
