"""
Tests serializers core.

TDD: Tests PRIMERO.
"""
import pytest
from datetime import date

from apps.pipeline.models import CallRecord, Center, Service
from apps.core.serializers import (
    CallRecordSerializer,
    CenterSerializer,
    ServiceSerializer,
)

@pytest.mark.django_db
class TestCallRecordSerializer:
    """Tests CallRecordSerializer."""
    
    def test_serialize_call_record(self):
        """Serializar CallRecord."""
        call = CallRecord.objects.create(
            fecha=date(2024, 1, 15),
            telefono='5551234567',
            servicio_800='8001234567',
            total_llamadas=100,
            llamadas_contestadas=85,
            llamadas_abandonadas=15,
        )
        
        serializer = CallRecordSerializer(call)
        data = serializer.data
        
        assert data['id'] == call.id
        assert data['fecha'] == '2024-01-15'
        assert data['telefono'] == '5551234567'
    
    def test_deserialize_call_record(self):
        """Deserializar y crear CallRecord."""
        data = {
            'fecha': '2024-01-15',
            'telefono': '5551234567',
            'servicio_800': '8001234567',
            'total_llamadas': 100,
            'llamadas_contestadas': 85,
            'llamadas_abandonadas': 15,
        }
        
        serializer = CallRecordSerializer(data=data)
        assert serializer.is_valid()
        
        call = serializer.save()
        assert call.id is not None


@pytest.mark.django_db
class TestCenterSerializer:
    """Tests CenterSerializer."""
    
    def test_serialize_center(self):
        """Serializar Center."""
        center = Center.objects.create(
            nombre='Centro CDMX',
            codigo='CDMX01',
            activo=True
        )
        
        serializer = CenterSerializer(center)
        data = serializer.data
        
        assert data['id'] == center.id
        assert data['nombre'] == 'Centro CDMX'


@pytest.mark.django_db
class TestServiceSerializer:
    """Tests ServiceSerializer."""
    
    def test_serialize_service(self):
        """Serializar Service."""
        center = Center.objects.create(
            nombre='Centro Test',
            codigo='TEST01'
        )
        
        service = Service.objects.create(
            numero_800='8001234567',
            nombre='Atencion Cliente',
            center=center
        )
        
        serializer = ServiceSerializer(service)
        data = serializer.data
        
        assert data['id'] == service.id
        assert data['numero_800'] == '8001234567'
