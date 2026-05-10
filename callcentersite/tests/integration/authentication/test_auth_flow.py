"""
Tests de integración: Flujo de Autenticación.

Prueba el flujo completo:
1. Login
2. Cambio de contraseña
3. Logout

CNST-010: Tests usan PostgreSQL (NO cache).
"""

import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse

from tests.test_data import UserTestData
from apps.authentication.models import LoginAttempt, SessionLog, LoginLockout


@pytest.mark.integration
@pytest.mark.django_db
class TestAuthenticationFlow:
    """
    Tests de integración para flujo de autenticación.
    
    Verifica:
    - Login exitoso con creación de token y sesión
    - Login fallido con registro de intento
    - Cambio de contraseña con autenticación
    - Logout con invalidación de sesión
    """
    
    def setup_method(self):
        """Setup para cada test."""
        self.client = APIClient()
    
    def test_complete_authentication_flow(self):
        """
        Test flujo completo: login -> cambio password -> logout.
        
        Steps:
        1. Crear usuario
        2. Login exitoso
        3. Verificar token y sesión creados
        4. Cambiar contraseña
        5. Logout
        6. Verificar sesión invalidada
        """
        # 1. Crear usuario
        user = UserTestData(username='testuser')
        user.set_password('oldpass123')
        user.save()
        
        # 2. Login exitoso
        login_url = reverse('auth-login')
        login_data = {
            'username': 'testuser',
            'password': 'oldpass123'
        }
        
        response = self.client.post(login_url, login_data, format='json')
        
        # Verificar respuesta
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'data' in response.data
        assert 'token' in response.data['data']
        assert 'session_key' in response.data['data']
        
        # Extraer token
        token = response.data['data']['token']
        
        # 3. Verificar LoginAttempt y SessionLog creados
        login_attempt = LoginAttempt.objects.filter(
            username='testuser',
            success=True
        ).latest('created_at')
        assert login_attempt is not None
        
        session_log = SessionLog.objects.filter(
            user=user,
            is_active=True
        ).latest('created_at')
        assert session_log is not None
        
        # 4. Cambiar contraseña (requiere autenticación)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        
        change_password_url = reverse('auth-change-password')
        change_data = {
            'current_password': 'oldpass123',
            'new_password': 'newpass456',
            'confirm_password': 'newpass456'
        }
        
        response = self.client.post(change_password_url, change_data, format='json')
        
        # Verificar cambio exitoso
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        
        # Verificar que la contraseña cambió
        user.refresh_from_db()
        assert user.check_password('newpass456') is True
        
        # 5. Logout
        logout_url = reverse('auth-logout')
        response = self.client.post(logout_url, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        
        # 6. Verificar sesión invalidada
        session_log.refresh_from_db()
        assert session_log.is_active is False
        assert session_log.logout_at is not None
    
    def test_login_with_invalid_credentials(self):
        """
        Test login con credenciales inválidas.
        
        Verifica:
        - Error 400 con credenciales incorrectas
        - LoginAttempt registrado como fallido
        """
        user = UserTestData(username='testuser')
        user.set_password('correctpass')
        user.save()
        
        login_url = reverse('auth-login')
        login_data = {
            'username': 'testuser',
            'password': 'wrongpass'
        }
        
        response = self.client.post(login_url, login_data, format='json')
        
        # Verificar error — InvalidCredentialsError retorna 401
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['success'] is False

        # Verificar LoginAttempt fallido registrado
        failed_attempt = LoginAttempt.objects.filter(
            username='testuser',
            success=False
        ).latest('created_at')
        assert failed_attempt is not None

    def test_login_with_nonexistent_user(self):
        """
        Test login con usuario inexistente.

        Verifica:
        - Error 401 (mismo codigo que password incorrecto, previene enumeracion RN-007)
        - LoginAttempt registrado sin user (user=None)
        """
        login_url = reverse('auth-login')
        login_data = {
            'username': 'nonexistent',
            'password': 'anypass'
        }

        response = self.client.post(login_url, login_data, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Verificar LoginAttempt con user=None
        attempt = LoginAttempt.objects.filter(
            username='nonexistent',
            user=None,
            success=False
        ).latest('created_at')
        assert attempt is not None
    
    def test_change_password_without_authentication(self):
        """
        Test cambio de contraseña sin autenticación.
        
        Verifica:
        - Error 401 Unauthorized
        """
        change_password_url = reverse('auth-change-password')
        change_data = {
            'current_password': 'oldpass',
            'new_password': 'newpass',
            'confirm_password': 'newpass'
        }
        
        response = self.client.post(change_password_url, change_data, format='json')
        
        # Debe requerir autenticación
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_logout_without_authentication(self):
        """
        Test logout sin autenticación.
        
        Verifica:
        - Error 401 Unauthorized
        """
        logout_url = reverse('auth-logout')
        response = self.client.post(logout_url, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.integration
@pytest.mark.django_db
class TestAccountLockout:
    """
    Tests de integración para bloqueo de cuenta.
    
    Verifica:
    - Bloqueo después de 5 intentos fallidos
    - Error específico cuando cuenta bloqueada
    """
    
    def setup_method(self):
        """
        Setup para cada test.
        
        CNST-010: Limpia LoginLockout de BD (NO cache).
        """
        self.client = APIClient()
        # Limpiar lockouts de tests anteriores
        LoginLockout.objects.all().delete()
    
    def test_account_lockout_after_5_failed_attempts(self):
        """
        Test bloqueo de cuenta después de 5 intentos.
        
        Steps:
        1. Crear usuario
        2. Hacer 5 intentos fallidos
        3. Verificar que cuenta se bloquea
        4. Verificar error específico
        """
        user = UserTestData(username='testuser')
        user.set_password('correctpass')
        user.save()
        
        login_url = reverse('auth-login')
        
        # 5 intentos fallidos
        for i in range(5):
            login_data = {
                'username': 'testuser',
                'password': 'wrongpass'
            }
            response = self.client.post(login_url, login_data, format='json')
            
            # Primeros 4 deben fallar con 401 INVALID_CREDENTIALS
            if i < 4:
                assert response.status_code == status.HTTP_401_UNAUTHORIZED
                assert response.data['error']['error_code'] == 'INVALID_CREDENTIALS'
            else:
                # 5to debe mostrar cuenta bloqueada
                assert response.status_code == status.HTTP_403_FORBIDDEN
                assert 'locked' in str(response.data).lower() or 'bloqueada' in str(response.data).lower()
        
        # Verificar que incluso con credenciales correctas no puede entrar
        login_data = {
            'username': 'testuser',
            'password': 'correctpass'
        }
        response = self.client.post(login_url, login_data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
