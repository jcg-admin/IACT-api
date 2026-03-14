"""
Tests modelos ivr_legacy.

CNST-003: Acceso READ-ONLY a MariaDB legacy.
"""
import pytest
from datetime import date


@pytest.mark.django_db
class TestCallLogModel:
    """Tests modelo CallLog (unmanaged, READ-ONLY)."""
    
    def test_calllog_importable(self):
        """CallLog debe ser importable."""
        from apps.ivr.models import CallLog
        assert CallLog is not None
    
    def test_calllog_model_structure(self):
        """CallLog debe tener campos correctos."""
        from apps.ivr.models import CallLog
        
        # Verificar campos existen
        assert hasattr(CallLog, 'fecha')
        assert hasattr(CallLog, 'telefono')
        assert hasattr(CallLog, 'servicio_800')
        assert hasattr(CallLog, 'total_llamadas')
    
    def test_calllog_meta_unmanaged(self):
        """CallLog debe ser unmanaged."""
        from apps.ivr.models import CallLog
        
        assert CallLog._meta.managed is False
    
    def test_calllog_meta_db_table(self):
        """CallLog debe apuntar a tabla call_logs."""
        from apps.ivr.models import CallLog
        
        assert CallLog._meta.db_table == 'call_logs'
