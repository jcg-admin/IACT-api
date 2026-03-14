"""Tests para Service Access."""
import pytest
from django.contrib.auth import get_user_model
from apps.core.models import Service, Center, UserServiceAccess, CallRecord
from apps.core.services import ServiceAccessService

User = get_user_model()


@pytest.mark.django_db
class TestUserServiceAccess:
    """Tests para UserServiceAccess model."""
    
    def test_grant_service_access(self):
        """Test otorgar acceso a servicio."""
        user = User.objects.create_user(username='test')
        center = Center.objects.create(nombre='Centro1', codigo='C1')
        service = Service.objects.create(
            numero_800='800-123-4567',
            nombre='Servicio Test',
            center=center
        )
        
        access = UserServiceAccess.objects.create(
            user=user,
            service=service
        )
        
        assert access.is_active is True
        assert access.user == user
        assert access.service == service
    
    def test_get_user_services(self):
        """Test obtener servicios de usuario."""
        user = User.objects.create_user(username='test')
        center = Center.objects.create(nombre='Centro1', codigo='C1')
        service1 = Service.objects.create(numero_800='800-111-1111', nombre='S1', center=center)
        service2 = Service.objects.create(numero_800='800-222-2222', nombre='S2', center=center)
        service3 = Service.objects.create(numero_800='800-333-3333', nombre='S3', center=center)
        
        # Usuario solo tiene acceso a service1 y service2
        UserServiceAccess.objects.create(user=user, service=service1)
        UserServiceAccess.objects.create(user=user, service=service2)
        
        services = UserServiceAccess.get_user_services(user)
        
        assert services.count() == 2
        assert service1 in services
        assert service2 in services
        assert service3 not in services
    
    def test_superuser_sees_all_services(self):
        """Test que superusuario ve todos los servicios."""
        superuser = User.objects.create_user(username='admin', is_superuser=True)
        center = Center.objects.create(nombre='Centro1', codigo='C1')
        service1 = Service.objects.create(numero_800='800-111-1111', nombre='S1', center=center)
        service2 = Service.objects.create(numero_800='800-222-2222', nombre='S2', center=center)
        
        services = UserServiceAccess.get_user_services(superuser)
        
        assert services.count() == 2
        assert service1 in services
        assert service2 in services


@pytest.mark.django_db
class TestServiceAccessService:
    """Tests para ServiceAccessService."""
    
    def test_has_service_access(self):
        """Test verificar acceso a servicio."""
        user = User.objects.create_user(username='test')
        center = Center.objects.create(nombre='Centro1', codigo='C1')
        service = Service.objects.create(numero_800='800-123-4567', nombre='S1', center=center)
        
        # Sin acceso
        assert ServiceAccessService.has_service_access(user, service) is False
        
        # Con acceso
        UserServiceAccess.objects.create(user=user, service=service)
        assert ServiceAccessService.has_service_access(user, service) is True
    
    def test_filter_by_user_services(self):
        """Test filtrar queryset por servicios."""
        user = User.objects.create_user(username='test')
        center = Center.objects.create(nombre='Centro1', codigo='C1')
        service1 = Service.objects.create(numero_800='800-111-1111', nombre='S1', center=center)
        service2 = Service.objects.create(numero_800='800-222-2222', nombre='S2', center=center)
        
        # Crear registros
        from datetime import date
        call1 = CallRecord.objects.create(
            fecha=date.today(),
            telefono='555-1234',
            servicio_800='800-111-1111',
            total_llamadas=10
        )
        call2 = CallRecord.objects.create(
            fecha=date.today(),
            telefono='555-5678',
            servicio_800='800-222-2222',
            total_llamadas=5
        )
        
        # Usuario solo tiene acceso a service1
        UserServiceAccess.objects.create(user=user, service=service1)
        
        # Filtrar CallRecords
        all_calls = CallRecord.objects.all()
        filtered = ServiceAccessService.filter_by_user_services(
            all_calls, user, 'servicio_800'
        )
        
        assert filtered.count() == 1
        assert call1 in filtered
        assert call2 not in filtered
    
    def test_grant_and_revoke_access(self):
        """Test otorgar y revocar acceso."""
        user = User.objects.create_user(username='test')
        admin = User.objects.create_user(username='admin')
        center = Center.objects.create(nombre='Centro1', codigo='C1')
        service = Service.objects.create(numero_800='800-123-4567', nombre='S1', center=center)
        
        # Otorgar
        access = ServiceAccessService.grant_service_access(
            user, service, admin, "Test reason"
        )
        assert access.is_active is True
        
        # Revocar
        revoked = ServiceAccessService.revoke_service_access(user, service, admin)
        assert revoked.is_active is False
        assert revoked.revoked_by == admin
    
    def test_get_services_summary(self):
        """Test obtener resumen de servicios."""
        user = User.objects.create_user(username='test')
        center = Center.objects.create(nombre='Centro1', codigo='C1')
        service = Service.objects.create(numero_800='800-123-4567', nombre='S1', center=center)
        UserServiceAccess.objects.create(user=user, service=service)
        
        summary = ServiceAccessService.get_services_summary(user)
        
        assert summary['total_services'] == 1
        assert len(summary['services']) == 1
        assert summary['services'][0]['numero_800'] == '800-123-4567'


@pytest.mark.django_db  
class TestServiceFilterMixin:
    """Tests para ServiceFilterMixin."""
    
    def test_mixin_filters_queryset(self):
        """Test que mixin filtra correctamente."""
        from apps.core.mixins import ServiceFilterMixin
        from rest_framework.test import APIRequestFactory
        
        user = User.objects.create_user(username='test')
        center = Center.objects.create(nombre='Centro1', codigo='C1')
        service1 = Service.objects.create(numero_800='800-111-1111', nombre='S1', center=center)
        service2 = Service.objects.create(numero_800='800-222-2222', nombre='S2', center=center)
        
        UserServiceAccess.objects.create(user=user, service=service1)
        
        # Mock ViewSet con mixin
        class TestViewSet(ServiceFilterMixin):
            service_field = 'servicio_800'
            
            def get_queryset(self):
                return CallRecord.objects.all()
        
        # Crear calls
        from datetime import date
        call1 = CallRecord.objects.create(
            fecha=date.today(), telefono='555-1234',
            servicio_800='800-111-1111', total_llamadas=10
        )
        call2 = CallRecord.objects.create(
            fecha=date.today(), telefono='555-5678',
            servicio_800='800-222-2222', total_llamadas=5
        )
        
        # Simular request
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = user
        
        viewset = TestViewSet()
        viewset.request = request
        
        filtered = viewset.get_queryset()
        
        assert filtered.count() == 1
        assert call1 in filtered
        assert call2 not in filtered
