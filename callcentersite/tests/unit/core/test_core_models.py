"""
Tests modelos core.

TDD: Tests PRIMERO.
"""
import pytest
from datetime import date
from decimal import Decimal
from django.db import IntegrityError
from apps.pipeline.models import CallRecord


@pytest.mark.django_db
class TestCallRecordModel:
    """Tests modelo CallRecord."""
    
    def test_create_call_record(self):
        """Crear CallRecord basico."""
        call = CallRecord.objects.create(
            fecha=date(2024, 1, 15),
            telefono='5551234567',
            servicio_800='8001234567',
            total_llamadas=100,
            llamadas_contestadas=85,
            llamadas_abandonadas=15,
        )
        
        assert call.id is not None
        assert call.fecha == date(2024, 1, 15)
        assert call.telefono == '5551234567'
        assert call.total_llamadas == 100
    
    def test_call_record_str(self):
        """__str__ debe retornar representacion legible."""
        call = CallRecord.objects.create(
            fecha=date(2024, 1, 15),
            telefono='5551234567',
            servicio_800='8001234567',
            total_llamadas=100,
            llamadas_contestadas=85,
            llamadas_abandonadas=15,
        )
        
        assert '2024-01-15' in str(call)
        assert '5551234567' in str(call)
    
    def test_answer_rate_calculation(self):
        """answer_rate() debe calcular porcentaje."""
        call = CallRecord.objects.create(
            fecha=date(2024, 1, 15),
            telefono='5551234567',
            servicio_800='8001234567',
            total_llamadas=100,
            llamadas_contestadas=85,
            llamadas_abandonadas=15,
        )
        
        rate = call.answer_rate()
        assert rate == Decimal('85.00')
    
    def test_answer_rate_zero_calls(self):
        """answer_rate() con 0 llamadas debe retornar 0."""
        call = CallRecord.objects.create(
            fecha=date(2024, 1, 15),
            telefono='5551234567',
            servicio_800='8001234567',
            total_llamadas=0,
            llamadas_contestadas=0,
            llamadas_abandonadas=0,
        )
        
        rate = call.answer_rate()
        assert rate == Decimal('0.00')
    
    def test_unique_constraint(self):
        """No permitir duplicados (fecha + telefono + servicio)."""
        CallRecord.objects.create(
            fecha=date(2024, 1, 15),
            telefono='5551234567',
            servicio_800='8001234567',
            total_llamadas=100,
            llamadas_contestadas=85,
            llamadas_abandonadas=15,
        )
        
        # Intentar crear duplicado
        with pytest.raises(IntegrityError):
            CallRecord.objects.create(
                fecha=date(2024, 1, 15),
                telefono='5551234567',
                servicio_800='8001234567',
                total_llamadas=50,
                llamadas_contestadas=40,
                llamadas_abandonadas=10,
            )
    
    def test_ordering(self):
        """Registros deben ordenarse por fecha DESC."""
        CallRecord.objects.create(
            fecha=date(2024, 1, 15),
            telefono='5551234567',
            servicio_800='8001234567',
            total_llamadas=100,
            llamadas_contestadas=85,
            llamadas_abandonadas=15,
        )
        CallRecord.objects.create(
            fecha=date(2024, 1, 16),
            telefono='5557654321',
            servicio_800='8001234567',
            total_llamadas=50,
            llamadas_contestadas=45,
            llamadas_abandonadas=5,
        )
        
        calls = list(CallRecord.objects.all())
        assert calls[0].fecha > calls[1].fecha


@pytest.mark.django_db
class TestCenterModel:
    """Tests modelo Center."""
    
    def test_create_center(self):
        """Crear Center basico."""
        from apps.core.models import Center
        
        center = Center.objects.create(
            nombre='Centro CDMX',
            codigo='CDMX01',
            activo=True
        )
        
        assert center.id is not None
        assert center.nombre == 'Centro CDMX'
        assert center.codigo == 'CDMX01'
        assert center.activo is True
    
    def test_center_str(self):
        """__str__ debe retornar nombre."""
        from apps.core.models import Center
        
        center = Center.objects.create(
            nombre='Centro CDMX',
            codigo='CDMX01'
        )
        
        assert str(center) == 'Centro CDMX'
    
    def test_center_unique_codigo(self):
        """Codigo debe ser unico."""
        from apps.core.models import Center
        
        Center.objects.create(
            nombre='Centro CDMX',
            codigo='CDMX01'
        )
        
        with pytest.raises(IntegrityError):
            Center.objects.create(
                nombre='Centro CDMX 2',
                codigo='CDMX01'  # Duplicado
            )
    
    def test_center_default_activo(self):
        """activo debe ser True por default."""
        from apps.core.models import Center
        
        center = Center.objects.create(
            nombre='Centro Test',
            codigo='TEST01'
        )
        
        assert center.activo is True


@pytest.mark.django_db
class TestServiceModel:
    """Tests modelo Service."""
    
    def test_create_service(self):
        """Crear Service con Center."""
        from apps.core.models import Center, Service
        
        center = Center.objects.create(
            nombre='Centro Test',
            codigo='TEST01'
        )
        
        service = Service.objects.create(
            numero_800='8001234567',
            nombre='Atencion Cliente',
            center=center
        )
        
        assert service.id is not None
        assert service.numero_800 == '8001234567'
        assert service.center == center
    
    def test_service_str(self):
        """__str__ debe mostrar numero y nombre."""
        from apps.core.models import Center, Service
        
        center = Center.objects.create(
            nombre='Centro Test',
            codigo='TEST01'
        )
        
        service = Service.objects.create(
            numero_800='8001234567',
            nombre='Atencion Cliente',
            center=center
        )
        
        assert '8001234567' in str(service)
        assert 'Atencion Cliente' in str(service)
    
    def test_service_unique_numero(self):
        """numero_800 debe ser unico."""
        from apps.core.models import Center, Service
        
        center = Center.objects.create(
            nombre='Centro Test',
            codigo='TEST01'
        )
        
        Service.objects.create(
            numero_800='8001234567',
            nombre='Servicio 1',
            center=center
        )
        
        with pytest.raises(IntegrityError):
            Service.objects.create(
                numero_800='8001234567',  # Duplicado
                nombre='Servicio 2',
                center=center
            )
    
    def test_service_center_relation(self):
        """Relacion con Center debe funcionar."""
        from apps.core.models import Center, Service
        
        center = Center.objects.create(
            nombre='Centro Test',
            codigo='TEST01'
        )
        
        service1 = Service.objects.create(
            numero_800='8001234567',
            nombre='Servicio 1',
            center=center
        )
        service2 = Service.objects.create(
            numero_800='8001234568',
            nombre='Servicio 2',
            center=center
        )
        
        # Reverse relation
        assert center.services.count() == 2
        assert service1 in center.services.all()
