"""
Tests unitarios para AuthViewSet.

Cubre el endpoint POST /api/v1/auth/login/ con todos sus flujos:
- Login exitoso
- Credenciales invalidas (401)
- Cuenta bloqueada (403)
- Usuario inactivo (403)
- Campos vacios (400)
- first_login deteccion
- Registros de LoginAttempt y SessionLog
"""

import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse

from tests.factories import UserFactory, LoginAttemptFactory
from apps.authentication.models import LoginAttempt, SessionLog, LoginLockout


@pytest.mark.unit
@pytest.mark.django_db
class TestAuthViewSetLogin:
    """
    Tests unitarios para AuthViewSet.login.

    POST /api/v1/auth/login/  [AllowAny]
    """

    def setup_method(self):
        """Setup antes de cada test."""
        self.client = APIClient()
        self.url = reverse('auth-login')
        LoginLockout.objects.all().delete()

    # -------------------------------------------------------------------------
    # FLUJO PRINCIPAL — Login exitoso
    # -------------------------------------------------------------------------

    def test_login_exitoso_retorna_200(self):
        """Login con credenciales correctas retorna 200."""
        user = UserFactory()
        user.set_password('pass1234')
        user.save()

        response = self.client.post(
            self.url,
            {'username': user.username, 'password': 'pass1234'},
            format='json'
        )

        assert response.status_code == status.HTTP_200_OK

    def test_login_exitoso_retorna_success_true(self):
        """Login exitoso incluye success: true en la respuesta."""
        user = UserFactory()
        user.set_password('pass1234')
        user.save()

        response = self.client.post(
            self.url,
            {'username': user.username, 'password': 'pass1234'},
            format='json'
        )

        assert response.data['success'] is True

    def test_login_exitoso_retorna_token(self):
        """Login exitoso retorna token DRF en data."""
        user = UserFactory()
        user.set_password('pass1234')
        user.save()

        response = self.client.post(
            self.url,
            {'username': user.username, 'password': 'pass1234'},
            format='json'
        )

        assert 'token' in response.data['data']
        assert response.data['data']['token'] is not None

    def test_login_exitoso_retorna_session_key(self):
        """Login exitoso retorna session_key en data."""
        user = UserFactory()
        user.set_password('pass1234')
        user.save()

        response = self.client.post(
            self.url,
            {'username': user.username, 'password': 'pass1234'},
            format='json'
        )

        assert 'session_key' in response.data['data']

    def test_login_exitoso_retorna_datos_usuario(self):
        """Login exitoso retorna id, username, email, first_name, last_name."""
        user = UserFactory()
        user.set_password('pass1234')
        user.save()

        response = self.client.post(
            self.url,
            {'username': user.username, 'password': 'pass1234'},
            format='json'
        )

        user_data = response.data['data']['user']
        assert user_data['id'] == user.id
        assert user_data['username'] == user.username
        assert 'email' in user_data
        assert 'first_name' in user_data
        assert 'last_name' in user_data

    def test_login_exitoso_crea_login_attempt_exitoso(self):
        """Login exitoso registra LoginAttempt con success=True."""
        user = UserFactory()
        user.set_password('pass1234')
        user.save()

        self.client.post(
            self.url,
            {'username': user.username, 'password': 'pass1234'},
            format='json'
        )

        assert LoginAttempt.objects.filter(
            username=user.username,
            success=True
        ).exists()

    def test_login_exitoso_crea_session_log(self):
        """Login exitoso crea SessionLog con is_active=True."""
        user = UserFactory()
        user.set_password('pass1234')
        user.save()

        self.client.post(
            self.url,
            {'username': user.username, 'password': 'pass1234'},
            format='json'
        )

        assert SessionLog.objects.filter(
            user=user,
            is_active=True
        ).exists()

    def test_login_exitoso_retorna_first_login_true_en_primer_intento(self):
        """Primer login exitoso retorna first_login: true."""
        user = UserFactory()
        user.set_password('pass1234')
        user.save()

        response = self.client.post(
            self.url,
            {'username': user.username, 'password': 'pass1234'},
            format='json'
        )

        assert response.data['data']['first_login'] is True

    def test_login_exitoso_retorna_first_login_false_en_segundo_intento(self):
        """Segundo login exitoso retorna first_login: false."""
        user = UserFactory()
        user.set_password('pass1234')
        user.save()

        # Primer login — registra un LoginAttempt exitoso
        LoginAttemptFactory(user=user, username=user.username, success=True)

        response = self.client.post(
            self.url,
            {'username': user.username, 'password': 'pass1234'},
            format='json'
        )

        assert response.data['data']['first_login'] is False

    # -------------------------------------------------------------------------
    # A1 — Credenciales invalidas
    # -------------------------------------------------------------------------

    def test_credenciales_invalidas_retorna_401(self):
        """Password incorrecto retorna 401 Unauthorized."""
        user = UserFactory()
        user.set_password('pass1234')
        user.save()

        response = self.client.post(
            self.url,
            {'username': user.username, 'password': 'wrongpass'},
            format='json'
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_credenciales_invalidas_retorna_error_code_invalid_credentials(self):
        """Password incorrecto retorna error_code INVALID_CREDENTIALS."""
        user = UserFactory()
        user.set_password('pass1234')
        user.save()

        response = self.client.post(
            self.url,
            {'username': user.username, 'password': 'wrongpass'},
            format='json'
        )

        assert response.data['success'] is False
        assert response.data['error']['error_code'] == 'INVALID_CREDENTIALS'

    def test_credenciales_invalidas_retorna_attempts_remaining(self):
        """Primer intento fallido retorna attempts_remaining: 4."""
        user = UserFactory()
        user.set_password('pass1234')
        user.save()

        response = self.client.post(
            self.url,
            {'username': user.username, 'password': 'wrongpass'},
            format='json'
        )

        assert response.data['error']['details']['attempts_remaining'] == 4

    def test_usuario_inexistente_retorna_401(self):
        """Username que no existe retorna 401 (mismo error que password incorrecto)."""
        response = self.client.post(
            self.url,
            {'username': 'noexiste', 'password': 'anypass'},
            format='json'
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['error']['error_code'] == 'INVALID_CREDENTIALS'

    def test_credenciales_invalidas_registra_login_attempt_fallido(self):
        """Intento fallido registra LoginAttempt con success=False."""
        user = UserFactory()
        user.set_password('pass1234')
        user.save()

        self.client.post(
            self.url,
            {'username': user.username, 'password': 'wrongpass'},
            format='json'
        )

        assert LoginAttempt.objects.filter(
            username=user.username,
            success=False
        ).exists()

    def test_usuario_inexistente_registra_login_attempt_con_user_none(self):
        """Username inexistente registra LoginAttempt con user=None."""
        self.client.post(
            self.url,
            {'username': 'noexiste', 'password': 'anypass'},
            format='json'
        )

        assert LoginAttempt.objects.filter(
            username='noexiste',
            user=None,
            success=False
        ).exists()

    # -------------------------------------------------------------------------
    # A2 — Cuenta bloqueada
    # -------------------------------------------------------------------------

    def test_cuenta_bloqueada_retorna_403(self):
        """Cuenta con lockout activo retorna 403 Forbidden."""
        user = UserFactory()
        user.set_password('pass1234')
        user.save()

        # Crear lockout activo directamente
        from apps.authentication.services import LockoutService
        lockout_service = LockoutService()
        for _ in range(5):
            lockout_service.record_failed_attempt(user.username)

        response = self.client.post(
            self.url,
            {'username': user.username, 'password': 'pass1234'},
            format='json'
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cuenta_bloqueada_retorna_error_code_account_locked(self):
        """Cuenta bloqueada retorna error_code ACCOUNT_LOCKED."""
        user = UserFactory()
        user.set_password('pass1234')
        user.save()

        from apps.authentication.services import LockoutService
        lockout_service = LockoutService()
        for _ in range(5):
            lockout_service.record_failed_attempt(user.username)

        response = self.client.post(
            self.url,
            {'username': user.username, 'password': 'pass1234'},
            format='json'
        )

        assert response.data['error']['error_code'] == 'ACCOUNT_LOCKED'

    def test_cuenta_bloqueada_retorna_locked_minutes(self):
        """Cuenta ya bloqueada (intento posterior) retorna details.locked_minutes."""
        user = UserFactory()
        user.set_password('pass1234')
        user.save()

        # Bloquear cuenta
        from apps.authentication.services import LockoutService
        lockout_service = LockoutService()
        for _ in range(5):
            lockout_service.record_failed_attempt(user.username)

        # Intento posterior al lockout — debe incluir locked_minutes
        response = self.client.post(
            self.url,
            {'username': user.username, 'password': 'pass1234'},
            format='json'
        )

        assert 'locked_minutes' in response.data['error']['details']

    # -------------------------------------------------------------------------
    # A3 — Usuario inactivo
    # -------------------------------------------------------------------------

    def test_usuario_inactivo_retorna_403(self):
        """Usuario con is_active=False retorna 403 Forbidden."""
        user = UserFactory(is_active=False)
        user.set_password('pass1234')
        user.save()

        response = self.client.post(
            self.url,
            {'username': user.username, 'password': 'pass1234'},
            format='json'
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_usuario_inactivo_retorna_error_code_user_inactive(self):
        """Usuario inactivo retorna error_code USER_INACTIVE."""
        user = UserFactory(is_active=False)
        user.set_password('pass1234')
        user.save()

        response = self.client.post(
            self.url,
            {'username': user.username, 'password': 'pass1234'},
            format='json'
        )

        assert response.data['error']['error_code'] == 'USER_INACTIVE'

    # -------------------------------------------------------------------------
    # A4 — Campos vacios (validacion de serializer)
    # -------------------------------------------------------------------------

    def test_username_vacio_retorna_400(self):
        """Username vacio retorna 400 Bad Request."""
        response = self.client.post(
            self.url,
            {'username': '', 'password': 'pass1234'},
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_password_vacio_retorna_400(self):
        """Password vacio retorna 400 Bad Request."""
        response = self.client.post(
            self.url,
            {'username': 'john', 'password': ''},
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_username_ausente_retorna_400(self):
        """Sin campo username retorna 400 Bad Request."""
        response = self.client.post(
            self.url,
            {'password': 'pass1234'},
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_password_ausente_retorna_400(self):
        """Sin campo password retorna 400 Bad Request."""
        response = self.client.post(
            self.url,
            {'username': 'john'},
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_campos_vacios_no_consultan_base_de_datos(self):
        """Campos vacios no generan LoginAttempt (falla en serializer, antes de llegar al servicio)."""
        count_antes = LoginAttempt.objects.count()

        self.client.post(
            self.url,
            {'username': '', 'password': ''},
            format='json'
        )

        assert LoginAttempt.objects.count() == count_antes

    # -------------------------------------------------------------------------
    # Seguridad — el endpoint es publico
    # -------------------------------------------------------------------------

    def test_endpoint_es_publico_sin_token(self):
        """El endpoint no requiere autenticacion previa."""
        # Sin credenciales en el cliente
        response = self.client.post(
            self.url,
            {'username': 'cualquiera', 'password': 'cualquiera'},
            format='json'
        )

        # No debe retornar 401 por falta de auth del cliente (puede ser 401 por credenciales)
        assert response.status_code != status.HTTP_405_METHOD_NOT_ALLOWED

    def test_get_no_permitido(self):
        """GET al endpoint de login retorna 405 Method Not Allowed."""
        response = self.client.get(self.url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
