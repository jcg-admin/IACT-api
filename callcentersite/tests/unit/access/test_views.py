"""Tests para Views de módulos."""
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.access.models import Module, UserModuleAccess

User = get_user_model()


@pytest.mark.django_db
class TestMyModulesView:
    """Tests para /my-modules/ endpoint."""
    
    def test_my_modules_authenticated(self):
        """Test obtener módulos propios."""
        user = User.objects.create_user(username='test', password='test')
        module = Module.objects.create(code='MOD_Test', name='Test')
        UserModuleAccess.objects.create(user=user, module=module)
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        response = client.get('/api/v1/access/my-modules/')
        
        assert response.status_code == 200
        assert response.data['total_count'] == 1
    
    def test_my_modules_unauthorized(self):
        """Test sin autenticación."""
        client = APIClient()
        response = client.get('/api/v1/access/my-modules/')
        assert response.status_code == 401
