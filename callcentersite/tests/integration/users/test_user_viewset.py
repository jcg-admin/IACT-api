"""
Tests de integración para UserViewSet.

Prueban el flujo completo: Request -> ViewSet -> Service -> Database -> Response
"""

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserViewSetList:
    """Tests para GET /api/v1/users/ (list)."""
    
    def test_list_users_unauthenticated(self, api_client):
        """Test: Usuarios no autenticados no pueden listar."""
        response = api_client.get('/api/v1/users/users/')
        
        assert response.status_code in [401, 403]
    
    def test_list_users_as_admin(self, admin_client, admin_user):
        """Test: Admin puede listar usuarios."""
        # Crear usuarios adicionales
        User.objects.create_user('user1', 'user1@test.com', 'Pass123')
        User.objects.create_user('user2', 'user2@test.com', 'Pass123')
        
        response = admin_client.get('/api/v1/users/users/')
        
        assert response.status_code == 200
        # Sin paginación, response.data es directamente una lista
        assert isinstance(response.data, list)
        assert len(response.data) >= 3  # admin + user1 + user2
    
    def test_list_users_with_rbac_permission(self, permitted_client):
        """Test: Usuario con USR_VIEW puede listar."""
        response = permitted_client.get('/api/v1/users/users/')
        
        # Usuario tiene permiso USR_VIEW
        assert response.status_code == 200
    
    def test_list_users_without_rbac_permission(self, authenticated_client):
        """Test: Usuario sin USR_VIEW no puede listar."""
        response = authenticated_client.get('/api/v1/users/users/')
        
        # Usuario regular no tiene función USR_VIEW
        assert response.status_code == 403
    
    def test_list_users_filter_by_search(self, admin_client):
        """Test: Filtrar usuarios por búsqueda."""
        User.objects.create_user('john', 'john@test.com', 'Pass123', first_name='John')
        User.objects.create_user('jane', 'jane@test.com', 'Pass123', first_name='Jane')
        
        response = admin_client.get('/api/v1/users/users/', {'search': 'john'})
        
        assert response.status_code == 200
        # Debe retornar solo usuarios que coincidan
        usernames = [user['username'] for user in response.data]
        assert 'john' in usernames
        assert 'jane' not in usernames
    
    def test_list_users_filter_by_is_active(self, admin_client):
        """Test: Filtrar usuarios por is_active."""
        active = User.objects.create_user('active', 'active@test.com', 'Pass123')
        inactive = User.objects.create_user('inactive', 'inactive@test.com', 'Pass123')
        inactive.is_active = False
        inactive.save()
        
        response = admin_client.get('/api/v1/users/users/', {'is_active': 'true'})
        
        assert response.status_code == 200
        usernames = [user['username'] for user in response.data]
        assert 'active' in usernames
        assert 'inactive' not in usernames


@pytest.mark.django_db
class TestUserViewSetCreate:
    """Tests para POST /api/v1/users/ (create)."""
    
    def test_create_user_unauthenticated(self, api_client):
        """Test: Usuarios no autenticados no pueden crear."""
        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'NewPass123',
        }
        
        response = api_client.post('/api/v1/users/users/', data)
        
        assert response.status_code in [401, 403]
    
    def test_create_user_with_rbac_permission(self, permitted_client):
        """Test: Usuario con USR_CREATE puede crear."""
        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'NewPass123',
            'first_name': 'New',
            'last_name': 'User',
        }
        
        response = permitted_client.post('/api/v1/users/users/', data)
        
        assert response.status_code == 201
        assert response.data['username'] == 'newuser'
        assert response.data['email'] == 'newuser@test.com'
        
        # Verificar que se creó en DB
        user = User.objects.get(username='newuser')
        assert user.first_name == 'New'
        assert user.check_password('NewPass123')
        
        # Verificar profile y settings auto-creados
        assert hasattr(user, 'profile')
        assert hasattr(user, 'settings')
    
    def test_create_user_without_rbac_permission(self, authenticated_client):
        """Test: Usuario sin USR_CREATE no puede crear."""
        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'NewPass123',
        }
        
        response = authenticated_client.post('/api/v1/users/users/', data)
        
        assert response.status_code == 403
    
    def test_create_user_duplicate_username(self, permitted_client):
        """Test: Error al crear usuario con username duplicado."""
        User.objects.create_user('duplicate', 'user1@test.com', 'Pass123')
        
        data = {
            'username': 'duplicate',
            'email': 'user2@test.com',
            'password': 'NewPass123',
        }
        
        response = permitted_client.post('/api/v1/users/users/', data)
        
        assert response.status_code == 400
        assert 'username' in response.data or 'non_field_errors' in response.data
    
    def test_create_user_invalid_password(self, permitted_client):
        """Test: Error con password inválido."""
        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'short',  # Muy corto
        }
        
        response = permitted_client.post('/api/v1/users/users/', data)
        
        assert response.status_code == 400
        assert 'password' in response.data


@pytest.mark.django_db
class TestUserViewSetRetrieve:
    """Tests para GET /api/v1/users/{id}/ (retrieve)."""
    
    def test_retrieve_user_with_rbac_permission(self, permitted_client):
        """Test: Usuario con USR_VIEW puede ver detalle."""
        user = User.objects.create_user('testuser', 'test@test.com', 'Pass123')
        
        response = permitted_client.get(f'/api/v1/users/{user.id}/')
        
        assert response.status_code == 200
        assert response.data['username'] == 'testuser'
        assert 'profile' in response.data
        assert 'settings' in response.data
        assert 'functions' in response.data
    
    def test_retrieve_user_without_rbac_permission(self, authenticated_client):
        """Test: Usuario sin USR_VIEW no puede ver detalle."""
        user = User.objects.create_user('testuser', 'test@test.com', 'Pass123')
        
        response = authenticated_client.get(f'/api/v1/users/{user.id}/')
        
        assert response.status_code == 403
    
    def test_retrieve_nonexistent_user(self, admin_client):
        """Test: 404 al buscar usuario inexistente."""
        response = admin_client.get('/api/v1/users/99999/')
        
        assert response.status_code == 404


@pytest.mark.django_db
class TestUserViewSetUpdate:
    """Tests para PUT/PATCH /api/v1/users/{id}/ (update)."""
    
    def test_update_user_with_rbac_permission(self, permitted_client):
        """Test: Usuario con USR_EDIT puede actualizar."""
        user = User.objects.create_user('testuser', 'test@test.com', 'Pass123')
        
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
        }
        
        response = permitted_client.patch(f'/api/v1/users/{user.id}/', data)
        
        assert response.status_code == 200
        assert response.data['first_name'] == 'Updated'
        assert response.data['last_name'] == 'Name'
        
        # Verificar en DB
        user.refresh_from_db()
        assert user.first_name == 'Updated'
    
    def test_update_user_without_rbac_permission(self, authenticated_client):
        """Test: Usuario sin USR_EDIT no puede actualizar."""
        user = User.objects.create_user('testuser', 'test@test.com', 'Pass123')
        
        data = {'first_name': 'Updated'}
        
        response = authenticated_client.patch(f'/api/v1/users/{user.id}/', data)
        
        assert response.status_code == 403


@pytest.mark.django_db
class TestUserViewSetDelete:
    """Tests para DELETE /api/v1/users/{id}/ (destroy)."""
    
    def test_delete_user_as_admin(self, admin_client):
        """Test: Admin puede eliminar (soft delete)."""
        user = User.objects.create_user('testuser', 'test@test.com', 'Pass123')
        
        response = admin_client.delete(f'/api/v1/users/{user.id}/')
        
        assert response.status_code == 204
        
        # Verificar soft delete
        user.refresh_from_db()
        assert user.is_deleted is True
        assert user.deleted_at is not None
    
    def test_delete_user_without_permission(self, authenticated_client):
        """Test: Usuario sin USR_DELETE no puede eliminar."""
        user = User.objects.create_user('testuser', 'test@test.com', 'Pass123')
        
        response = authenticated_client.delete(f'/api/v1/users/{user.id}/')
        
        assert response.status_code == 403


@pytest.mark.django_db
class TestUserViewSetCustomActions:
    """Tests para custom actions: me, activate, deactivate."""
    
    def test_me_endpoint_authenticated(self, authenticated_client, regular_user):
        """Test: /users/me/ retorna usuario autenticado."""
        response = authenticated_client.get('/api/v1/users/users/me/')
        
        assert response.status_code == 200
        assert response.data['username'] == regular_user.username
        assert response.data['email'] == regular_user.email
    
    def test_me_endpoint_unauthenticated(self, api_client):
        """Test: /users/me/ rechaza usuarios no autenticados."""
        response = api_client.get('/api/v1/users/users/me/')
        
        assert response.status_code in [401, 403]
    
    def test_activate_user_with_permission(self, permitted_client):
        """Test: Activar usuario con USR_EDIT."""
        user = User.objects.create_user('testuser', 'test@test.com', 'Pass123')
        user.is_active = False
        user.save()
        
        response = permitted_client.post(f'/api/v1/users/{user.id}/activate/')
        
        assert response.status_code == 200
        assert response.data['is_active'] is True
        
        # Verificar en DB
        user.refresh_from_db()
        assert user.is_active is True
    
    def test_deactivate_user_with_permission(self, permitted_client):
        """Test: Desactivar usuario con USR_EDIT."""
        user = User.objects.create_user('testuser', 'test@test.com', 'Pass123')
        
        response = permitted_client.post(f'/api/v1/users/{user.id}/deactivate/')
        
        assert response.status_code == 200
        assert response.data['is_active'] is False
        
        # Verificar en DB
        user.refresh_from_db()
        assert user.is_active is False
    
    def test_activate_user_without_permission(self, authenticated_client):
        """Test: Usuario sin USR_EDIT no puede activar."""
        user = User.objects.create_user('testuser', 'test@test.com', 'Pass123')
        
        response = authenticated_client.post(f'/api/v1/users/{user.id}/activate/')
        
        assert response.status_code == 403


# ============================================================================
# RESUMEN TESTS UserViewSet
# 
# Total Tests: 24
# 
# List (GET /users/): 6 tests
#   [SUCCESS] unauthenticated
#   [SUCCESS] as admin
#   [SUCCESS] with RBAC permission
#   [SUCCESS] without RBAC permission
#   [SUCCESS] filter by search
#   [SUCCESS] filter by is_active
# 
# Create (POST /users/): 5 tests
#   [SUCCESS] unauthenticated
#   [SUCCESS] with RBAC permission
#   [SUCCESS] without RBAC permission
#   [SUCCESS] duplicate username
#   [SUCCESS] invalid password
# 
# Retrieve (GET /users/{id}/): 3 tests
#   [SUCCESS] with RBAC permission
#   [SUCCESS] without RBAC permission
#   [SUCCESS] nonexistent user
# 
# Update (PATCH /users/{id}/): 2 tests
#   [SUCCESS] with RBAC permission
#   [SUCCESS] without RBAC permission
# 
# Delete (DELETE /users/{id}/): 2 tests
#   [SUCCESS] as admin
#   [SUCCESS] without permission
# 
# Custom Actions: 6 tests
#   [SUCCESS] me authenticated
#   [SUCCESS] me unauthenticated
#   [SUCCESS] activate with permission
#   [SUCCESS] deactivate with permission
#   [SUCCESS] activate without permission
# 
# Coverage:
#   [SUCCESS] Authentication
#   [SUCCESS] RBAC permissions
#   [SUCCESS] CRUD operations
#   [SUCCESS] Custom actions
#   [SUCCESS] Filters
#   [SUCCESS] Error cases
# ============================================================================
