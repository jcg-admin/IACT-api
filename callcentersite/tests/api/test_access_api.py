"""
Tests API centralizados para Access (Módulos).

Tests de integración para endpoints de módulos y accesos.
"""
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestModuleAPI:
    """Tests para /api/v1/access/modules/"""
    
    def test_list_modules_authenticated(self, authenticated_client):
        """Test listar módulos autenticado."""
        response = authenticated_client.get('/api/v1/access/modules/')
        assert response.status_code == 200
    
    def test_list_modules_unauthenticated(self, api_client):
        """Test sin autenticación."""
        response = api_client.get('/api/v1/access/modules/')
        assert response.status_code == 401
    
    def test_module_tree_endpoint(self, authenticated_client):
        """Test obtener jerarquía de módulos."""
        response = authenticated_client.get('/api/v1/access/modules/tree/')
        assert response.status_code == 200
        assert 'modules' in response.data


@pytest.mark.django_db
class TestMyModulesAPI:
    """Tests para /api/v1/access/my-modules/"""
    
    def test_my_modules_authenticated(self, authenticated_client):
        """Test obtener módulos propios."""
        response = authenticated_client.get('/api/v1/access/my-modules/')
        assert response.status_code == 200
        assert 'modules' in response.data
        assert 'total_count' in response.data
    
    def test_my_modules_unauthenticated(self, api_client):
        """Test sin autenticación."""
        response = api_client.get('/api/v1/access/my-modules/')
        assert response.status_code == 401
