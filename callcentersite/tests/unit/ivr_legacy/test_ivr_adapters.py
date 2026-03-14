"""
Tests IVRAdapter.

CNST-003: Validar acceso READ-ONLY.
"""
import pytest
from datetime import date
from apps.ivr.adapters import IVRAdapter


class TestIVRAdapter:
    """Tests IVRAdapter."""
    
    def test_adapter_instantiation(self):
        """IVRAdapter debe ser instanciable."""
        adapter = IVRAdapter()
        assert adapter is not None
    
    def test_adapter_has_get_calls_method(self):
        """IVRAdapter debe tener metodo get_calls."""
        adapter = IVRAdapter()
        assert hasattr(adapter, 'get_calls')
        assert callable(adapter.get_calls)
    
    def test_get_calls_returns_list(self):
        """get_calls() debe retornar lista."""
        adapter = IVRAdapter()
        
        fecha = date(2024, 1, 15)
        result = adapter.get_calls(fecha_inicio=fecha, fecha_fin=fecha)
        
        assert isinstance(result, list)
    
    def test_get_calls_returns_dicts(self):
        """get_calls() debe retornar lista de dicts."""
        adapter = IVRAdapter()
        
        fecha = date(2024, 1, 15)
        result = adapter.get_calls(fecha_inicio=fecha, fecha_fin=fecha)
        
        # Puede estar vacia si no hay datos
        if len(result) > 0:
            assert isinstance(result[0], dict)
