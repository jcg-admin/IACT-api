"""
ETL Service - IACT Call Center System.

CNST-004: NO Celery (ejecutar con APScheduler).

Pipeline ETL:
1. Extract: IVR legacy DB (MariaDB READ-ONLY)
2. Transform: Procesar y limpiar datos
3. Load: Guardar en analytics DB (PostgreSQL)
"""
import logging
from datetime import date
from typing import List, Dict

# =============================================================================
# DEUDA TÉCNICA — PENDIENTE
# =============================================================================
# Fecha de eliminación: 2026-03-21
# Motivo: IVRAdapter desactivado. La tabla call_logs no existe en ivr_legacy.
#         El método extract() retorna lista vacía hasta que el adapter
#         sea reactivado.
#         Reactivar cuando:
#           1. La tabla call_logs exista en ivr_legacy
#           2. IVRAdapter sea reactivado en apps/ivr/adapters.py
# Ver: documentos/planes/PLAN_IVR_SIMPLIFICACION_20260321.md
# =============================================================================
# from apps.ivr.adapters import IVRAdapter

from apps.pipeline.models import CallRecord

logger = logging.getLogger(__name__)


class ETLService:
    """
    Servicio ETL para procesar datos IVR legacy.
    
    CNST-003: Acceso READ-ONLY a ivr_legacy.
    CNST-004: Ejecutar con APScheduler (NO Celery).
    """
    
    def __init__(self):
        """Initialize ETL service."""
        # DEUDA TÉCNICA: self.adapter = IVRAdapter() — desactivado 2026-03-21
        self.adapter = None
    
    def extract(
        self,
        fecha_inicio: date,
        fecha_fin: date
    ) -> List[Dict]:
        """
        Extraer datos de IVR legacy.
        
        Step 1 del pipeline ETL.
        
        Args:
            fecha_inicio: Fecha inicio
            fecha_fin: Fecha fin
        
        Returns:
            List[Dict]: Datos raw de IVR legacy
        """
        logger.info(f"ETL Extract: {fecha_inicio} a {fecha_fin}")
        
        # DEUDA TÉCNICA: IVRAdapter desactivado — retorna vacío hasta reactivar
        # Ver: documentos/planes/PLAN_IVR_SIMPLIFICACION_20260321.md
        logger.warning("ETL Extract: IVRAdapter desactivado (deuda técnica) — retornando []")
        return []
    
    def transform(self, raw_data: List[Dict]) -> List[Dict]:
        """
        Transformar y limpiar datos raw.
        
        Step 2 del pipeline ETL.
        
        Args:
            raw_data: Datos raw de extract()
        
        Returns:
            List[Dict]: Datos transformados y validados
        """
        logger.info(f"ETL Transform: {len(raw_data)} registros a transformar")
        
        if not raw_data:
            return []
        
        transformed = []
        
        for record in raw_data:
            # Validar y limpiar
            if not self._validate_record(record):
                logger.warning(f"ETL Transform: registro invalido ignorado")
                continue
            
            # Normalizar
            cleaned = self._clean_record(record)
            transformed.append(cleaned)
        
        logger.info(f"ETL Transform: {len(transformed)} registros validos")
        return transformed
    
    def load(self, transformed_data: List[Dict]) -> int:
        """
        Cargar datos en analytics DB.
        
        Step 3 del pipeline ETL.
        
        Args:
            transformed_data: Datos transformados
        
        Returns:
            int: Numero de registros cargados/actualizados
        """
        logger.info(f"ETL Load: {len(transformed_data)} registros a cargar")
        
        if not transformed_data:
            return 0
        
        loaded_count = 0
        
        for record in transformed_data:
            try:
                # update_or_create: actualiza si existe, crea si no
                obj, created = CallRecord.objects.update_or_create(
                    fecha=record['fecha'],
                    telefono=record['telefono'],
                    servicio_800=record['servicio_800'],
                    defaults={
                        'total_llamadas': record['total_llamadas'],
                        'llamadas_contestadas': record['llamadas_contestadas'],
                        'llamadas_abandonadas': record['llamadas_abandonadas'],
                    }
                )
                
                loaded_count += 1
                
                if created:
                    logger.debug(f"ETL Load: registro creado: {obj}")
                else:
                    logger.debug(f"ETL Load: registro actualizado: {obj}")
            
            except Exception as e:
                logger.error(f"ETL Load error en registro {record}: {e}")
                continue
        
        logger.info(f"ETL Load: {loaded_count} registros cargados/actualizados")
        return loaded_count
    
    def run_etl(
        self,
        fecha: date = None,
        fecha_inicio: date = None,
        fecha_fin: date = None
    ) -> Dict:
        """
        Ejecutar pipeline ETL completo.
        
        Extract -> Transform -> Load
        
        Args:
            fecha: Fecha unica (fecha_inicio = fecha_fin = fecha)
            fecha_inicio: Fecha inicio (si no fecha)
            fecha_fin: Fecha fin (si no fecha)
        
        Returns:
            Dict: Estadisticas de ejecucion
        """
        # Determinar rango fechas
        if fecha:
            fecha_inicio = fecha
            fecha_fin = fecha
        
        if not fecha_inicio or not fecha_fin:
            raise ValueError("Debe proporcionar fecha o fecha_inicio/fecha_fin")
        
        logger.info(f"ETL Pipeline START: {fecha_inicio} a {fecha_fin}")
        
        stats = {
            'extracted': 0,
            'transformed': 0,
            'loaded': 0,
            'success': False,
            'errors': []
        }
        
        try:
            # Step 1: Extract
            raw_data = self.extract(
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin
            )
            stats['extracted'] = len(raw_data)
            
            # Step 2: Transform
            transformed_data = self.transform(raw_data)
            stats['transformed'] = len(transformed_data)
            
            # Step 3: Load
            loaded_count = self.load(transformed_data)
            stats['loaded'] = loaded_count
            
            stats['success'] = True
            
            logger.info(
                f"ETL Pipeline SUCCESS: "
                f"extracted={stats['extracted']}, "
                f"transformed={stats['transformed']}, "
                f"loaded={stats['loaded']}"
            )
        
        except Exception as e:
            stats['success'] = False
            stats['errors'].append(str(e))
            logger.error(f"ETL Pipeline ERROR: {e}", exc_info=True)
        
        logger.info("ETL Pipeline END")
        
        return stats
    
    def _validate_record(self, record: Dict) -> bool:
        """Validar registro."""
        required_fields = [
            'fecha', 'telefono', 'servicio_800',
            'total_llamadas', 'llamadas_contestadas',
            'llamadas_abandonadas'
        ]
        
        for field in required_fields:
            if field not in record:
                return False
        
        # Validar telefono (minimo 10 digitos)
        telefono = str(record['telefono']).strip()
        if len(telefono) < 10:
            return False
        
        return True
    
    def _clean_record(self, record: Dict) -> Dict:
        """Limpiar y normalizar registro."""
        cleaned = {
            'fecha': record['fecha'],
            'telefono': str(record['telefono']).strip(),
            'servicio_800': str(record['servicio_800']).strip(),
            'total_llamadas': int(record['total_llamadas']),
            'llamadas_contestadas': int(record['llamadas_contestadas']),
            'llamadas_abandonadas': int(record['llamadas_abandonadas']),
        }
        
        return cleaned
