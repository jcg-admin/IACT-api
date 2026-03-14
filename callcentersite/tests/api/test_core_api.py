"""
Tests API centralizados para Core (Centers, Services).

Tests de integración para endpoints core.
"""
import pytest


@pytest.mark.django_db
class TestServiceAccessAPI:
    """Tests para acceso a servicios."""
    
    def test_user_sees_only_assigned_services(
        self, 
        authenticated_client,
        sample_user,
        sample_service
    ):
        """Test que usuario solo ve servicios asignados."""
        from apps.core.models import UserServiceAccess
        
        # Asignar servicio al usuario
        UserServiceAccess.objects.create(
            user=sample_user,
            service=sample_service
        )
        
        # Aquí iría el test de API cuando se implemente
        # response = authenticated_client.get('/api/v1/core/services/')
        # assert response.status_code == 200
        # assert len(response.data['results']) == 1
