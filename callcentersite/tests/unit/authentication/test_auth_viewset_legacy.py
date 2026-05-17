"""
Tests unitarios para LoginView (API v2).

POST /api/auth/login/ — estructura de respuesta real:
  {tokens: {access, refresh, ...}, user: {user_id, username, first_login, ...},
   session: {session_id, ...}, next_step, warning, request_id, timestamp}

Errores: estructura {error: {error_code, message, details}}
El sistema registra fallos en LoginLockout, no en LoginAttempt directamente.
"""

import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse

from tests.test_data import UserTestData
from apps.authentication.models import SessionLog, LoginLockout


@pytest.fixture(autouse=True)
def disable_view_throttles(monkeypatch):
    """Deshabilitar throttle en vistas con throttle_classes explícito."""
    for cls_path in [
        ('apps.authentication.login_view', 'LoginView'),
        ('apps.authentication.logout_view', 'LogoutView'),
        ('apps.authentication.change_password_view', 'ChangePasswordView'),
    ]:
        try:
            import importlib
            mod = importlib.import_module(cls_path[0])
            monkeypatch.setattr(getattr(mod, cls_path[1]), 'throttle_classes', [])
        except Exception:
            pass


@pytest.mark.unit
@pytest.mark.django_db(transaction=True)
class TestAuthViewSetLogin:
    """Tests unitarios para POST /api/auth/login/."""

    def setup_method(self):
        self.client = APIClient()
        self.url = reverse('authentication:login')
        LoginLockout.objects.all().delete()

    # --- Flujo principal: login exitoso ---

    def test_login_exitoso_retorna_200(self):
        """Login con credenciales correctas retorna 200."""
        user = UserTestData()
        user.set_password('pass1234')
        user.save()

        resp = self.client.post(self.url,
            {'username': user.username, 'password': 'pass1234'}, format='json')

        assert resp.status_code == status.HTTP_200_OK

    def test_login_exitoso_retorna_tokens(self):
        """Login exitoso incluye tokens.access y tokens.refresh."""
        user = UserTestData()
        user.set_password('pass1234')
        user.save()

        resp = self.client.post(self.url,
            {'username': user.username, 'password': 'pass1234'}, format='json')

        assert 'tokens' in resp.data
        assert resp.data['tokens']['access'] is not None
        assert resp.data['tokens']['refresh'] is not None

    def test_login_exitoso_retorna_session_id(self):
        """Login exitoso incluye session.session_id en la respuesta."""
        user = UserTestData()
        user.set_password('pass1234')
        user.save()

        resp = self.client.post(self.url,
            {'username': user.username, 'password': 'pass1234'}, format='json')

        assert 'session' in resp.data
        assert resp.data['session']['session_id'] is not None

    def test_login_exitoso_retorna_datos_usuario(self):
        """Login exitoso retorna user_id, username en user block."""
        user = UserTestData()
        user.set_password('pass1234')
        user.save()

        resp = self.client.post(self.url,
            {'username': user.username, 'password': 'pass1234'}, format='json')

        user_data = resp.data['user']
        assert user_data['user_id'] == user.id
        assert user_data['username'] == user.username

    def test_login_exitoso_crea_session(self):
        """Login exitoso crea Session activa para el usuario (modelo API v2)."""
        from apps.authentication.models import Session
        user = UserTestData()
        user.set_password('pass1234')
        user.save()

        self.client.post(self.url,
            {'username': user.username, 'password': 'pass1234'}, format='json')

        assert Session.objects.filter(user=user, state='ACTIVE').exists()

    def test_login_exitoso_retorna_first_login_true_primer_intento(self):
        """Primer login retorna first_login: true."""
        user = UserTestData()
        user.set_password('pass1234')
        user.save()

        resp = self.client.post(self.url,
            {'username': user.username, 'password': 'pass1234'}, format='json')

        assert resp.data['user'].get('first_login') is True

    def test_login_exitoso_retorna_first_login_false_segundo_intento(self):
        """Segundo login (first_login=False en user): retorna first_login false."""
        import uuid
        u = uuid.uuid4().hex[:6]
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(username=f'u2_{u}', password='pass1234')
        user.first_login = False
        user.save(update_fields=['first_login'])

        resp = self.client.post(self.url,
            {'username': f'u2_{u}', 'password': 'pass1234'}, format='json')

        assert resp.data['user'].get('first_login') is False

    # --- Credenciales inválidas ---

    def test_credenciales_invalidas_retorna_401(self):
        """Password incorrecto retorna 401."""
        user = UserTestData()
        user.set_password('pass1234')
        user.save()

        resp = self.client.post(self.url,
            {'username': user.username, 'password': 'wrongpas'}, format='json')

        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_credenciales_invalidas_retorna_error_code(self):
        """Password incorrecto retorna error_code INVALID_CREDENTIALS."""
        user = UserTestData()
        user.set_password('pass1234')
        user.save()

        resp = self.client.post(self.url,
            {'username': user.username, 'password': 'wrongpas'}, format='json')

        assert resp.data.get('error', {}).get('code') == 'INVALID_CREDENTIALS'

    def test_credenciales_invalidas_registra_lockout(self):
        """Intento fallido incrementa LoginLockout para el username."""
        user = UserTestData()
        user.set_password('pass1234')
        user.save()

        self.client.post(self.url,
            {'username': user.username, 'password': 'wrongpas'}, format='json')

        assert LoginLockout.objects.filter(username=user.username).exists()

    def test_usuario_inexistente_retorna_401(self):
        """Username que no existe retorna 401 (RN-007: mismo código que pass incorrecto)."""
        resp = self.client.post(self.url,
            {'username': 'noexiste_xyz_abc', 'password': 'anypass1'}, format='json')

        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
        assert resp.data.get('error', {}).get('code') == 'INVALID_CREDENTIALS'

    def test_usuario_inexistente_registra_lockout(self):
        """Username inexistente crea LoginLockout para el username tentado."""
        self.client.post(self.url,
            {'username': 'noexiste_xyz_abc', 'password': 'anypass1'}, format='json')

        assert LoginLockout.objects.filter(username='noexiste_xyz_abc').exists()

    # --- Cuenta bloqueada ---

    def test_cuenta_bloqueada_retorna_403(self):
        """Cuenta con lockout activo retorna 403."""
        user = UserTestData()
        user.set_password('pass1234')
        user.save()

        lockout, _ = LoginLockout.objects.get_or_create(
            username=user.username, defaults={'failed_attempts': 0})
        lockout.failed_attempts = 5
        from django.utils import timezone
        from datetime import timedelta
        lockout.locked_until = timezone.now() + timedelta(minutes=15)
        lockout.save()

        resp = self.client.post(self.url,
            {'username': user.username, 'password': 'pass1234'}, format='json')

        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_cuenta_bloqueada_retorna_error_code_account_locked(self):
        """Cuenta bloqueada retorna error_code ACCOUNT_LOCKED."""
        user = UserTestData()
        user.set_password('pass1234')
        user.save()

        lockout, _ = LoginLockout.objects.get_or_create(
            username=user.username, defaults={'failed_attempts': 0})
        lockout.failed_attempts = 5
        from django.utils import timezone
        from datetime import timedelta
        lockout.locked_until = timezone.now() + timedelta(minutes=15)
        lockout.save()

        resp = self.client.post(self.url,
            {'username': user.username, 'password': 'pass1234'}, format='json')

        assert resp.data.get('error', {}).get('code') in ('ACCOUNT_LOCKED', 'ACCOUNT_BLOCKED')

    # --- Usuario inactivo ---

    def test_usuario_inactivo_retorna_400_o_403(self):
        """Usuario con state=INACTIVE retorna 400 o 403."""
        import uuid
        u = uuid.uuid4().hex[:6]
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(username=f'inact_{u}', password='pass1234')
        user.state = 'INACTIVE'
        user.save(update_fields=['state'])

        resp = self.client.post(self.url,
            {'username': f'inact_{u}', 'password': 'pass1234'}, format='json')

        assert resp.status_code in (400, 403)

    def test_usuario_inactivo_no_puede_hacer_login(self):
        """Usuario con state=INACTIVE no puede obtener tokens (no retorna 200)."""
        import uuid
        u = uuid.uuid4().hex[:6]
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(username=f'inact2_{u}', password='pass1234')
        user.state = 'INACTIVE'
        user.save(update_fields=['state'])

        resp = self.client.post(self.url,
            {'username': f'inact2_{u}', 'password': 'pass1234'}, format='json')

        # Cualquier respuesta de error es correcta — lo importante es que no hay tokens
        assert resp.status_code != 200 or 'tokens' not in resp.data

    # --- Validación de campos ---

    def test_username_vacio_retorna_400(self):
        resp = self.client.post(self.url,
            {'username': '', 'password': 'pass1234'}, format='json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_password_vacio_retorna_400(self):
        resp = self.client.post(self.url,
            {'username': 'john', 'password': ''}, format='json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_username_ausente_retorna_400(self):
        resp = self.client.post(self.url, {'password': 'pass1234'}, format='json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_password_ausente_retorna_400(self):
        resp = self.client.post(self.url, {'username': 'john'}, format='json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_no_permitido(self):
        """GET al endpoint de login retorna 405."""
        resp = self.client.get(self.url)
        assert resp.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
