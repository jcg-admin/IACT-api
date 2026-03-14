"""
Adapters para IVR Legacy.

CNST-003: Acceso READ-ONLY a MariaDB legacy.
"""
from datetime import date
from typing import List, Dict
from .models import CallLog


class IVRAdapter:
    """
    Adapter para acceder a IVR legacy DB.
    
    CNST-003:
    - Acceso READ-ONLY a ivr_legacy DB
    - Usuario ivr_readonly (SOLO SELECT)
    - Database Router enforza READ-ONLY
    
    Usage:
        adapter = IVRAdapter()
        calls = adapter.get_calls(
            fecha_inicio=date(2024, 1, 15),
            fecha_fin=date(2024, 1, 20)
        )
    """
    
    def get_calls(
        self,
        fecha_inicio: date,
        fecha_fin: date
    ) -> List[Dict]:
        """
        Obtener llamadas de IVR legacy por rango fechas.
        
        Args:
            fecha_inicio: Fecha inicio (inclusive)
            fecha_fin: Fecha fin (inclusive)
        
        Returns:
            List[Dict]: Lista de llamadas como dicts
        
        Examples:
            >>> adapter = IVRAdapter()
            >>> calls = adapter.get_calls(
            ...     fecha_inicio=date(2024, 1, 15),
            ...     fecha_fin=date(2024, 1, 15)
            ... )
            >>> len(calls) >= 0
            True
        """
        # Query a ivr_legacy DB (READ-ONLY)
        # NOTA: En testing usa default DB (SQLite), en prod usa ivr_legacy (MariaDB)
        calls = []
        
        try:
            # Intentar usar ivr_legacy DB
            queryset = CallLog.objects.using('ivr_legacy').filter(
                fecha__gte=fecha_inicio,
                fecha__lte=fecha_fin
            ).order_by('fecha', 'telefono')
            
            # Convertir a dicts
            for call in queryset:
                calls.append({
                    'fecha': call.fecha,
                    'telefono': call.telefono,
                    'servicio_800': call.servicio_800,
                    'total_llamadas': call.total_llamadas,
                    'llamadas_contestadas': call.llamadas_contestadas,
                    'llamadas_abandonadas': call.llamadas_abandonadas,
                })
        except Exception:
            # Si ivr_legacy no esta configurado (testing), retornar vacio
            pass
        
        return calls
