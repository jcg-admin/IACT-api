from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ETLScheduler:
    """
    Scheduler para ETL programado.
    
    CNST-004: ETL cada 12 horas (NO real-time).
    
    Responsabilidades:
    - Iniciar scheduler en background
    - Registrar job ETL con intervalo 12 horas
    - Ejecutar ETL automaticamente
    - Logging de ejecuciones
    """
    
    scheduler = None
    
    @classmethod
    def start(cls):
        """
        Iniciar scheduler.
        
        Si ya esta iniciado, no hace nada (idempotente).
        """
        if cls.scheduler is not None:
            logger.info("ETLScheduler ya iniciado")
            return
        
        logger.info("Iniciando ETLScheduler...")
        
        cls.scheduler = BackgroundScheduler()
        
        # ETL cada 12 horas
        cls.scheduler.add_job(
            cls.run_etl,
            trigger=IntervalTrigger(hours=12),
            id='etl_job',
            name='ETL IVR -> Analytics',
            replace_existing=True,
        )
        
        cls.scheduler.start()
        
        logger.info("ETLScheduler iniciado exitosamente")
    
    @classmethod
    def stop(cls):
        """
        Detener scheduler.
        
        Si no esta iniciado, no hace nada.
        """
        if cls.scheduler:
            logger.info("Deteniendo ETLScheduler...")
            cls.scheduler.shutdown()
            cls.scheduler = None
            logger.info("ETLScheduler detenido")
    
    @classmethod
    def run_etl(cls):
        """
        Ejecutar ETL.
        
        CNST-004: Programado cada 12 horas, NO real-time.
        
        Flujo:
        1. Calcular rango (ultimas 24 horas)
        2. Crear ETLExecution (status=RUNNING)
        3. Ejecutar ETLService
        4. Actualizar ETLExecution (status=SUCCESS/FAILED)
        """
        from apps.pipeline.models import ETLExecution
        from apps.pipeline.services import ETLService
        
        logger.info("=== Iniciando ejecucion ETL programada ===")
        
        # Calcular rango (ultimas 24 horas)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=1)
        
        logger.info(f"Rango: {start_date} a {end_date}")
        
        # Crear ejecucion
        execution = ETLExecution.objects.create(
            start_date=start_date,
            end_date=end_date,
            status='RUNNING',
        )
        
        logger.info(f"ETLExecution creada: {execution.id}")
        
        try:
            # Ejecutar ETL
            logger.info("Ejecutando ETLService...")
            result = ETLService.run(start_date, end_date)
            
            # Actualizar ejecucion
            execution.status = 'SUCCESS'
            execution.records_extracted = result['extracted']
            execution.records_loaded = result['loaded']
            execution.completed_at = datetime.now()
            execution.save()
            
            logger.info(f"ETL exitoso: {result['extracted']} extraidos, "
                       f"{result['loaded']} cargados")
            
        except Exception as e:
            logger.error(f"ETL fallido: {str(e)}", exc_info=True)
            
            execution.status = 'FAILED'
            execution.error_message = str(e)
            execution.completed_at = datetime.now()
            execution.save()
            
            # Re-raise para que APScheduler lo registre
            raise
        
        logger.info("=== Ejecucion ETL completada ===")
