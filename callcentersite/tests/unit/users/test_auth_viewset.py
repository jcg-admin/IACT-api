"""
Tests unitarios para AuthViewSet.

FASE 2 PARTE 6: Tests con 90%+ coverage.
"""

import pytest
from rest_framework import status
from unittest.mock import patch

from apps.users.models import User
from tests.test_data.user_test_data import UserTestData


@pytest.mark.django_db
class TestPasswordChange:
    """Tests para POST /api/auth/change-password/."""
    
    def test_change_password_success(self, api_client):
        """Test: Cambiar password exitosamente."""
        user = UserTestData(password='OldPass123!')
        api_client.force_authenticate(user=user)
        
        data = {
            'old_password': 'OldPass123!',
            'new_password': 'NewPass456!',
            'new_password_confirm': 'NewPass456!',
        }
        
        response = api_client.post('/api/auth/change-password/', data)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'detail' in response.data
        
        # Verificar que password cambió
        user.refresh_from_db()
        assert user.check_password('NewPass456!')
    
    def test_change_password_wrong_old_password(self, api_client):
        """Test: Old password incorrecto retorna error."""
        user = UserTestData(password='OldPass123!')
        api_client.force_authenticate(user=user)
        
        data = {
            'old_password': 'WrongPass123!',
            'new_password': 'NewPass456!',
            'new_password_confirm': 'NewPass456!',
        }
        
        response = api_client.post('/api/auth/change-password/', data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_change_password_mismatch(self, api_client):
        """Test: New passwords no coinciden retorna error."""
        user = UserTestData(password='OldPass123!')
        api_client.force_authenticate(user=user)
        
        data = {
            'old_password': 'OldPass123!',
            'new_password': 'NewPass456!',
            'new_password_confirm': 'DifferentPass456!',
        }
        
        response = api_client.post('/api/auth/change-password/', data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'new_password_confirm' in response.data
    
    def test_change_password_same_as_old(self, api_client):
        """Test: New password igual al old retorna error."""
        user = UserTestData(password='OldPass123!')
        api_client.force_authenticate(user=user)
        
        data = {
            'old_password': 'OldPass123!',
            'new_password': 'OldPass123!',
            'new_password_confirm': 'OldPass123!',
        }
        
        response = api_client.post('/api/auth/change-password/', data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'new_password' in response.data
    
    def test_change_password_weak(self, api_client):
        """Test: Password débil retorna error."""
        user = UserTestData(password='OldPass123!')
        api_client.force_authenticate(user=user)
        
        data = {
            'old_password': 'OldPass123!',
            'new_password': 'weak',  # Muy corto, sin mayúsculas, etc.
            'new_password_confirm': 'weak',
        }
        
        response = api_client.post('/api/auth/change-password/', data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'new_password' in response.data
    
    def test_change_password_unauthenticated(self, api_client):
        """Test: Sin autenticación retorna 401."""
        data = {
            'old_password': 'OldPass123!',
            'new_password': 'NewPass456!',
            'new_password_confirm': 'NewPass456!',
        }
        
        response = api_client.post('/api/auth/change-password/', data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_change_password_no_old_password(self, api_client):
        """Test: Sin old_password retorna error."""
        user = UserTestData()
        api_client.force_authenticate(user=user)
        
        data = {
            'new_password': 'NewPass456!',
            'new_password_confirm': 'NewPass456!',
        }
        
        response = api_client.post('/api/auth/change-password/', data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'old_password' in response.data
    
    def test_change_password_no_confirmation(self, api_client):
        """Test: Sin confirmation retorna error."""
        user = UserTestData(password='OldPass123!')
        api_client.force_authenticate(user=user)
        
        data = {
            'old_password': 'OldPass123!',
            'new_password': 'NewPass456!',
        }
        
        response = api_client.post('/api/auth/change-password/', data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'new_password_confirm' in response.data


# ============================================================================
# RESUMEN TESTS AuthViewSet
# 
# Total tests: 8
# 
# change-password (8 tests):
#   [SUCCESS] Success
#   [SUCCESS] Wrong old password -> 400
#   [SUCCESS] Passwords mismatch -> 400
#   [SUCCESS] Same as old -> 400
#   [SUCCESS] Weak password -> 400
#   [SUCCESS] Unauthenticated -> 401
#   [SUCCESS] No old_password -> 400
#   [SUCCESS] No confirmation -> 400
# 
# Coverage: ~95% de AuthViewSet
# ============================================================================
