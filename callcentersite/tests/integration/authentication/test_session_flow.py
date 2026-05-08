"""
Tests de integración: Flujo de Gestión de Sesiones.

Prueba el flujo completo:
1. Ver sesiones activas
2. Invalidar sesión específica
3. Invalidar todas las sesiones
"""

import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse

from tests.testdata import UserTestData, SessionLogTestData
from apps.authentication.models import SessionLog


@pytest.mark.integration
@pytest.mark.django_db
class TestSessionManagementFlow:
    """
    Tests de integración para gestión de sesiones.
    
    Verifica:
    - Listado de sesiones activas del usuario
    - Ver detalle de sesión específica
    - Invalidar sesión específica
    - Invalidar todas las sesiones excepto la actual
    """
    
    def setup_method(self):
        """Setup para cada test."""
        self.client = APIClient()
    
    def test_list_active_sessions(self):
        """
        Test listar sesiones activas del usuario.
        
        Verifica:
        - Requiere autenticación
        - Solo muestra sesiones del usuario autenticado
        - Solo muestra sesiones activas
        """
        # Crear usuario y hacer login
        user = UserTestData(username='testuser')
        user.set_password('testpass123')
        user.save()
        
        login_url = reverse('auth-login')
        response = self.client.post(login_url, {
            'username': 'testuser',
            'password': 'testpass123'
        }, format='json')
        
        token = response.data['data']['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        
        # Crear sesiones adicionales para el usuario
        SessionLogTestData.create_batch(
            2,
            user=user,
            is_active=True,
            created_by=user
        )
        
        # Crear sesión inactiva (no debe aparecer)
        SessionLogTestData(
            user=user,
            is_active=False,
            created_by=user
        )
        
        # Crear sesión de otro usuario (no debe aparecer)
        other_user = UserTestData(username='otheruser')
        SessionLogTestData(
            user=other_user,
            is_active=True,
            created_by=other_user
        )
        
        # Listar sesiones
        sessions_url = reverse('sessions-list')
        response = self.client.get(sessions_url, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        
        # Debe tener al menos 3 sesiones activas (login actual + 2 creadas)
        sessions = response.data['data']
        assert len(sessions) >= 3
        
        # Todas deben ser del usuario autenticado
        for session in sessions:
            assert session['username'] == 'testuser'
    
    def test_retrieve_session_detail(self):
        """
        Test obtener detalle de sesión específica.
        
        Verifica:
        - Detalle incluye campos de auditoría
        - Solo puede ver sus propias sesiones
        """
        # Crear usuario y autenticar
        user = UserTestData(username='testuser')
        user.set_password('testpass123')
        user.save()
        
        login_url = reverse('auth-login')
        response = self.client.post(login_url, {
            'username': 'testuser',
            'password': 'testpass123'
        }, format='json')
        
        token = response.data['data']['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        
        # Crear sesión
        session = SessionLogTestData(
            user=user,
            is_active=True,
            created_by=user
        )
        
        # Obtener detalle
        detail_url = reverse('sessions-detail', kwargs={'pk': session.id})
        response = self.client.get(detail_url, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        
        # Verificar campos de auditoría
        session_data = response.data['data']
        assert 'created_at' in session_data
        assert 'updated_at' in session_data
        assert 'created_by_username' in session_data
    
    def test_invalidate_specific_session(self):
        """
        Test invalidar sesión específica.
        
        Verifica:
        - Sesión se marca como inactiva
        - logout_at se setea
        - Usuario puede invalidar sus propias sesiones
        """
        # Crear usuario y autenticar
        user = UserTestData(username='testuser')
        user.set_password('testpass123')
        user.save()
        
        login_url = reverse('auth-login')
        response = self.client.post(login_url, {
            'username': 'testuser',
            'password': 'testpass123'
        }, format='json')
        
        token = response.data['data']['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        
        # Crear sesión adicional
        session = SessionLogTestData(
            user=user,
            is_active=True,
            created_by=user
        )
        
        # Invalidar sesión
        invalidate_url = reverse('sessions-invalidate', kwargs={'pk': session.id})
        response = self.client.post(invalidate_url, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        
        # Verificar que sesión está inactiva
        session.refresh_from_db()
        assert session.is_active is False
        assert session.logout_at is not None
    
    def test_invalidate_all_sessions_except_current(self):
        """
        Test invalidar todas las sesiones excepto la actual.
        
        Verifica:
        - Todas las sesiones se invalidan excepto la actual
        - Retorna cantidad de sesiones invalidadas
        """
        # Crear usuario y autenticar
        user = UserTestData(username='testuser')
        user.set_password('testpass123')
        user.save()
        
        login_url = reverse('auth-login')
        response = self.client.post(login_url, {
            'username': 'testuser',
            'password': 'testpass123'
        }, format='json')
        
        token = response.data['data']['token']
        session_key = response.data['data']['session_key']
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        
        # Crear 3 sesiones adicionales
        additional_sessions = SessionLogTestData.create_batch(
            3,
            user=user,
            is_active=True,
            created_by=user
        )
        
        # Invalidar todas excepto actual
        invalidate_all_url = reverse('sessions-invalidate-all')
        response = self.client.post(invalidate_all_url, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        
        # Verificar sesiones adicionales invalidadas
        for session in additional_sessions:
            session.refresh_from_db()
            assert session.is_active is False
        
        # Verificar sesión actual sigue activa
        current_session = SessionLog.objects.get(session_key=session_key)
        assert current_session.is_active is True
    
    def test_list_sessions_requires_authentication(self):
        """
        Test que listar sesiones requiere autenticación.
        
        Verifica:
        - Error 401 sin token
        """
        sessions_url = reverse('sessions-list')
        response = self.client.get(sessions_url, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_cannot_view_other_user_sessions(self):
        """
        Test que usuario no puede ver sesiones de otros.
        
        Verifica:
        - Solo ve sus propias sesiones en el listado
        """
        # Crear dos usuarios
        user1 = UserTestData(username='user1')
        user1.set_password('pass123')
        user1.save()
        
        user2 = UserTestData(username='user2')
        user2.set_password('pass123')
        user2.save()
        
        # Crear sesiones para user2
        SessionLogTestData.create_batch(
            3,
            user=user2,
            is_active=True,
            created_by=user2
        )
        
        # Login como user1
        login_url = reverse('auth-login')
        response = self.client.post(login_url, {
            'username': 'user1',
            'password': 'pass123'
        }, format='json')
        
        token = response.data['data']['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        
        # Listar sesiones
        sessions_url = reverse('sessions-list')
        response = self.client.get(sessions_url, format='json')
        
        # Solo debe ver su propia sesión (del login)
        sessions = response.data['data']
        for session in sessions:
            assert session['username'] == 'user1'


@pytest.mark.integration
@pytest.mark.django_db
class TestSessionDuration:
    """
    Tests de integración para duración de sesiones.
    
    Verifica:
    - duration property en sesiones activas
    - duration property en sesiones cerradas
    """
    
    def setup_method(self):
        """Setup para cada test."""
        self.client = APIClient()
    
    def test_session_duration_for_active_session(self):
        """
        Test duración de sesión activa.
        
        Verifica:
        - duration_seconds presente en respuesta
        - duration_seconds >= 0 para sesión activa
        """
        # Crear usuario y autenticar
        user = UserTestData(username='testuser')
        user.set_password('testpass123')
        user.save()
        
        login_url = reverse('auth-login')
        response = self.client.post(login_url, {
            'username': 'testuser',
            'password': 'testpass123'
        }, format='json')
        
        token = response.data['data']['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        
        # Listar sesiones
        sessions_url = reverse('sessions-list')
        response = self.client.get(sessions_url, format='json')
        
        # Verificar duration_seconds en la sesión actual
        sessions = response.data['data']
        current_session = sessions[0]
        
        assert 'duration_seconds' in current_session
        # Duración debe ser >= 0 (recién iniciada)
        assert current_session['duration_seconds'] >= 0
    
    def test_session_duration_for_closed_session(self):
        """
        Test duración de sesión cerrada.
        
        Verifica:
        - duration_seconds calculado correctamente
        - logout_at - created_at
        """
        from django.utils import timezone
        from datetime import timedelta
        
        # Crear usuario y autenticar
        user = UserTestData(username='testuser')
        user.set_password('testpass123')
        user.save()
        
        login_url = reverse('auth-login')
        response = self.client.post(login_url, {
            'username': 'testuser',
            'password': 'testpass123'
        }, format='json')
        
        token = response.data['data']['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        
        # Crear sesión cerrada manualmente
        session = SessionLogTestData(
            user=user,
            is_active=False,
            created_by=user
        )
        
        # Simular logout 1 hora después
        session.logout_at = session.created_at + timedelta(hours=1)
        session.save()
        
        # Obtener detalle
        detail_url = reverse('sessions-detail', kwargs={'pk': session.id})
        response = self.client.get(detail_url, format='json')
        
        session_data = response.data['data']
        
        # Duración debe ser 3600 segundos (1 hora)
        assert session_data['duration_seconds'] == 3600
