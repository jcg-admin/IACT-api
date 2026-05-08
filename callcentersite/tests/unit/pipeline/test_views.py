import pytest
from django.contrib.auth import get_user_model
User = get_user_model()
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import date
from apps.pipeline.models import ETLExecution


@pytest.mark.unit
@pytest.mark.django_db
class TestETLStatusView:
    """Tests endpoint status ETL."""
    
    def test_etl_status_requires_authentication(self):
        """Endpoint requiere autenticacion (CNST-005)."""
        client = APIClient()
        url = reverse('pipeline:etl_status')
        
        response = client.get(url)
        
        assert response.status_code == 401
    
    def test_etl_status_no_executions(self):
        """Status cuando no hay ejecuciones."""
        user = User.objects.create_user('testuser', password='test123')
        
        refresh = RefreshToken.for_user(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('pipeline:etl_status')
        response = client.get(url)
        
        assert response.status_code == 200
        assert response.data['last_execution'] is None
        assert response.data['next_execution'] is None
    
    def test_etl_status_with_execution(self):
        """Status con ultima ejecucion."""
        user = User.objects.create_user('testuser', password='test123')
        
        # Crear ejecucion
        execution = ETLExecution.objects.create(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 2),
            status='SUCCESS',
            records_extracted=1000,
            records_loaded=950,
        )
        
        refresh = RefreshToken.for_user(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('pipeline:etl_status')
        response = client.get(url)
        
        assert response.status_code == 200
        assert response.data['last_execution'] is not None
        assert response.data['last_execution']['status'] == 'SUCCESS'
        assert response.data['last_execution']['records_extracted'] == 1000
        assert response.data['last_execution']['records_loaded'] == 950
        assert response.data['next_execution'] is not None
