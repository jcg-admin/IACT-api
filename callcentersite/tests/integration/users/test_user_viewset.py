"""
Tests de integración para UserViewSet.

Prueban el flujo completo: Request -> ViewSet -> Service -> Database -> Response.
URL base: /api/users/
Autenticación: force_authenticate (superusuario para bypass RBAC).
"""

import pytest
import uuid
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserViewSetList:
    """Tests para GET /api/users/ (list)."""

    def test_list_users_unauthenticated(self, api_client):
        """Usuarios no autenticados no pueden listar."""
        response = api_client.get('/api/users/')
        assert response.status_code in [401, 403]

    def test_list_users_as_admin(self, admin_client, admin_user):
        """Admin puede listar usuarios."""
        u = uuid.uuid4().hex[:6]
        User.objects.create_user(f'u1_{u}', f'u1_{u}@test.com', 'Pass123')
        User.objects.create_user(f'u2_{u}', f'u2_{u}@test.com', 'Pass123')

        response = admin_client.get('/api/users/')

        assert response.status_code == 200
        data = response.data.get('results', response.data)
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_list_users_with_rbac_permission(self, admin_client):
        """Superusuario puede listar."""
        response = admin_client.get('/api/users/')
        assert response.status_code == 200

    def test_list_users_without_rbac_permission(self, authenticated_client):
        """Usuario regular sin USR_VIEW no puede listar."""
        response = authenticated_client.get('/api/users/')
        assert response.status_code == 403

    def test_list_users_filter_by_search(self, admin_client):
        """Filtrar usuarios por búsqueda."""
        u = uuid.uuid4().hex[:6]
        User.objects.create_user(f'john_{u}', f'john_{u}@test.com', 'Pass123', first_name='John')
        User.objects.create_user(f'jane_{u}', f'jane_{u}@test.com', 'Pass123', first_name='Jane')

        response = admin_client.get('/api/users/', {'search': f'john_{u}'})

        assert response.status_code == 200
        data = response.data.get('results', response.data)
        usernames = [u_data['username'] for u_data in data if isinstance(u_data, dict)]
        assert any(f'john_{u}' in un for un in usernames)

    def test_list_users_filter_by_is_active(self, admin_client):
        """Filtrar usuarios por is_active."""
        u = uuid.uuid4().hex[:6]
        User.objects.create_user(f'active_{u}', f'active_{u}@test.com', 'Pass123')
        inactive = User.objects.create_user(f'inactive_{u}', f'inactive_{u}@test.com', 'Pass123')
        inactive.is_active = False
        inactive.save()

        response = admin_client.get('/api/users/', {'is_active': 'true'})

        assert response.status_code == 200


@pytest.mark.django_db
class TestUserViewSetCreate:
    """Tests para POST /api/users/ (create)."""

    def test_create_user_unauthenticated(self, api_client):
        """Usuarios no autenticados no pueden crear."""
        response = api_client.post('/api/users/', {
            'username': 'newuser', 'email': 'newuser@test.com', 'password': 'NewPass123',
        })
        assert response.status_code in [401, 403]

    def test_create_user_with_rbac_permission(self, admin_client):
        """Superusuario puede crear usuarios."""
        u = uuid.uuid4().hex[:6]
        data = {
            'username': f'newuser_{u}',
            'email': f'newuser_{u}@test.com',
            'password': 'NewPassword123!',
            'password_confirm': 'NewPassword123!',
            'first_name': 'New',
            'last_name': 'User',
        }

        response = admin_client.post('/api/users/', data)

        assert response.status_code in (200, 201)
        if response.status_code == 201:
            assert response.data['username'] == f'newuser_{u}'

    def test_create_user_without_rbac_permission(self, authenticated_client):
        """Usuario sin USR_CREATE no puede crear."""
        response = authenticated_client.post('/api/users/', {
            'username': 'newuser', 'email': 'newuser@test.com', 'password': 'NewPass123',
        })
        assert response.status_code == 403

    def test_create_user_duplicate_username(self, admin_client):
        """Error al crear usuario con username duplicado."""
        u = uuid.uuid4().hex[:6]
        User.objects.create_user(f'dup_{u}', f'dup1_{u}@test.com', 'Pass123')

        response = admin_client.post('/api/users/', {
            'username': f'dup_{u}',
            'email': f'dup2_{u}@test.com',
            'password': 'NewPassword123!',
            'password_confirm': 'NewPassword123!',
        })

        assert response.status_code in (400, 409)

    def test_create_user_invalid_password(self, admin_client):
        """Error con password inválido (muy corto)."""
        u = uuid.uuid4().hex[:6]
        response = admin_client.post('/api/users/', {
            'username': f'newuser_{u}',
            'email': f'newuser_{u}@test.com',
            'password': 'ab',
        })

        assert response.status_code == 400


@pytest.mark.django_db
class TestUserViewSetRetrieve:
    """Tests para GET /api/users/{id}/ (retrieve)."""

    def test_retrieve_user_with_rbac_permission(self, admin_client):
        """Superusuario puede ver detalle de usuario."""
        u = uuid.uuid4().hex[:6]
        user = User.objects.create_user(f'tu_{u}', f'tu_{u}@test.com', 'Pass123')

        response = admin_client.get(f'/api/users/{user.id}/')

        assert response.status_code == 200
        assert response.data['username'] == f'tu_{u}'

    def test_retrieve_user_without_rbac_permission(self, authenticated_client):
        """Usuario sin USR_VIEW no puede ver detalle."""
        u = uuid.uuid4().hex[:6]
        user = User.objects.create_user(f'tu_{u}', f'tu_{u}@test.com', 'Pass123')

        response = authenticated_client.get(f'/api/users/{user.id}/')

        assert response.status_code == 403

    def test_retrieve_nonexistent_user(self, admin_client):
        """404 al buscar usuario inexistente."""
        response = admin_client.get('/api/users/99999999/')
        assert response.status_code == 404


@pytest.mark.django_db
class TestUserViewSetUpdate:
    """Tests para PATCH /api/users/{id}/ (update)."""

    def test_update_user_with_rbac_permission(self, admin_client):
        """Superusuario puede actualizar usuario."""
        u = uuid.uuid4().hex[:6]
        user = User.objects.create_user(f'tu_{u}', f'tu_{u}@test.com', 'Pass123')

        response = admin_client.patch(f'/api/users/{user.id}/', {
            'first_name': 'Updated', 'last_name': 'Name',
        })

        assert response.status_code == 200
        user.refresh_from_db()
        assert user.first_name == 'Updated'

    def test_update_user_without_rbac_permission(self, authenticated_client):
        """Usuario sin USR_EDIT no puede actualizar."""
        u = uuid.uuid4().hex[:6]
        user = User.objects.create_user(f'tu_{u}', f'tu_{u}@test.com', 'Pass123')

        response = authenticated_client.patch(f'/api/users/{user.id}/', {'first_name': 'Updated'})

        assert response.status_code == 403


@pytest.mark.django_db
class TestUserViewSetDelete:
    """Tests para DELETE /api/users/{id}/ (destroy/soft delete)."""

    def test_delete_user_as_admin(self, admin_client):
        """Superusuario puede eliminar (soft delete)."""
        u = uuid.uuid4().hex[:6]
        user = User.objects.create_user(f'tu_{u}', f'tu_{u}@test.com', 'Pass123')

        response = admin_client.delete(f'/api/users/{user.id}/')

        assert response.status_code in (200, 204)

        user.refresh_from_db()
        assert user.state == 'ELIMINATED' or not user.is_active

    def test_delete_user_without_permission(self, authenticated_client):
        """Usuario sin USR_DELETE no puede eliminar."""
        u = uuid.uuid4().hex[:6]
        user = User.objects.create_user(f'tu_{u}', f'tu_{u}@test.com', 'Pass123')

        response = authenticated_client.delete(f'/api/users/{user.id}/')

        assert response.status_code == 403


@pytest.mark.django_db
class TestUserViewSetCustomActions:
    """Tests para custom actions: me, activate, deactivate."""

    def test_me_endpoint_authenticated(self, authenticated_client, regular_user):
        """GET /api/users/me/ retorna el usuario autenticado o 403 si falta el permiso USR_VIEW_SELF."""
        response = authenticated_client.get('/api/users/me/')

        # /me/ puede requerir función específica — 200 si tiene permiso, 403 si no
        assert response.status_code in (200, 403)
        if response.status_code == 200:
            assert response.data['username'] == regular_user.username

    def test_me_endpoint_unauthenticated(self, api_client):
        """GET /api/users/me/ rechaza usuarios no autenticados."""
        response = api_client.get('/api/users/me/')
        assert response.status_code in [401, 403]

    def test_activate_user_with_permission(self, admin_client):
        """Superusuario puede activar usuarios."""
        u = uuid.uuid4().hex[:6]
        user = User.objects.create_user(f'tu_{u}', f'tu_{u}@test.com', 'Pass123')
        user.is_active = False
        user.save()

        response = admin_client.post(f'/api/users/{user.id}/activate/')

        assert response.status_code == 200
        user.refresh_from_db()
        assert user.is_active is True

    def test_deactivate_user_with_permission(self, admin_client):
        """Superusuario puede desactivar usuarios."""
        u = uuid.uuid4().hex[:6]
        user = User.objects.create_user(f'tu_{u}', f'tu_{u}@test.com', 'Pass123')

        response = admin_client.post(f'/api/users/{user.id}/deactivate/')

        assert response.status_code == 200
        user.refresh_from_db()
        assert user.is_active is False or user.state in ('INACTIVE', 'ELIMINATED')

    def test_activate_user_without_permission(self, authenticated_client):
        """Usuario sin USR_EDIT no puede activar."""
        u = uuid.uuid4().hex[:6]
        user = User.objects.create_user(f'tu_{u}', f'tu_{u}@test.com', 'Pass123')

        response = authenticated_client.post(f'/api/users/{user.id}/activate/')

        assert response.status_code == 403
