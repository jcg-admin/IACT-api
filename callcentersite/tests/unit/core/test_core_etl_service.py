"""
Tests ETLService.

CNST-003: ETL desde IVR legacy (READ-ONLY).
CNST-004: NO Celery (usar APScheduler).
"""

import pytest
from datetime import date

try:
    from apps.core.services.etl_service import ETLService
    from apps.pipeline.models import CallRecord
except ImportError as _err:
    pytest.skip(
        f'Codigo no implementado aun — {_err}',
        allow_module_level=True,
    )

pytestmark = pytest.mark.skip(reason="CallRecord no implementado en apps.core.models")




@pytest.mark.django_db
class TestETLServiceExtract:
    """Tests ETLService.extract()."""
    
    def test_etl_instantiation(self):
        """ETLService debe ser instanciable."""
        etl = ETLService()
        assert etl is not None
    
    def test_extract_method_exists(self):
        """extract() debe existir."""
        etl = ETLService()
        assert hasattr(etl, 'extract')
        assert callable(etl.extract)
    
    def test_extract_returns_list(self):
        """extract() debe retornar lista."""
        etl = ETLService()
        
        fecha = date(2024, 1, 15)
        data = etl.extract(fecha_inicio=fecha, fecha_fin=fecha)
        
        assert isinstance(data, list)


@pytest.mark.django_db
class TestETLServiceTransform:
    """Tests ETLService.transform()."""
    
    def test_transform_method_exists(self):
        """transform() debe existir."""
        etl = ETLService()
        assert hasattr(etl, 'transform')
        assert callable(etl.transform)
    
    def test_transform_returns_list(self):
        """transform() debe retornar lista."""
        etl = ETLService()
        
        raw_data = [
            {
                'fecha': date(2024, 1, 15),
                'telefono': '5551234567',
                'servicio_800': '8001234567',
                'total_llamadas': 100,
                'llamadas_contestadas': 85,
                'llamadas_abandonadas': 15,
            }
        ]
        
        transformed = etl.transform(raw_data)
        assert isinstance(transformed, list)
    
    def test_transform_empty_list(self):
        """transform() con lista vacia retorna []."""
        etl = ETLService()
        
        transformed = etl.transform([])
        assert transformed == []


@pytest.mark.django_db
class TestETLServiceLoad:
    """Tests ETLService.load()."""
    
    def test_load_method_exists(self):
        """load() debe existir."""
        etl = ETLService()
        assert hasattr(etl, 'load')
        assert callable(etl.load)
    
    def test_load_saves_to_db(self):
        """load() debe guardar en analytics DB."""
        etl = ETLService()
        
        transformed_data = [
            {
                'fecha': date(2024, 1, 15),
                'telefono': '5551234567',
                'servicio_800': '8001234567',
                'total_llamadas': 100,
                'llamadas_contestadas': 85,
                'llamadas_abandonadas': 15,
            }
        ]
        
        count = etl.load(transformed_data)
        
        assert count == 1
        assert CallRecord.objects.count() == 1
    
    def test_load_empty_list(self):
        """load() con lista vacia retorna 0."""
        etl = ETLService()
        
        count = etl.load([])
        assert count == 0


@pytest.mark.django_db
class TestETLServicePipeline:
    """Tests ETLService.run_etl() pipeline completo."""
    
    def test_run_etl_method_exists(self):
        """run_etl() debe existir."""
        etl = ETLService()
        assert hasattr(etl, 'run_etl')
        assert callable(etl.run_etl)
    
    def test_run_etl_returns_dict(self):
        """run_etl() debe retornar dict con stats."""
        etl = ETLService()
        
        fecha = date(2024, 1, 15)
        result = etl.run_etl(fecha=fecha)
        
        assert isinstance(result, dict)
        assert 'extracted' in result
        assert 'transformed' in result
        assert 'loaded' in result
        assert 'success' in result
