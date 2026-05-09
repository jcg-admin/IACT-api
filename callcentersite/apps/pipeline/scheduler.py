from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import date
import logging

from django.db import connections, OperationalError

logger = logging.getLogger(__name__)


class ETLScheduler:
    """
    Scheduler para ETL nocturno IVR.

    Dispara sp_etl_maestro() cada día a las 02:00 AM.
    CNST-004: NO Celery — usa APScheduler en proceso.
    """

    scheduler = None

    @classmethod
    def start(cls):
        if cls.scheduler is not None:
            logger.info("ETLScheduler ya iniciado")
            return

        logger.info("Iniciando ETLScheduler...")
        cls.scheduler = BackgroundScheduler()
        cls.scheduler.add_job(
            cls.run_etl,
            trigger=CronTrigger(hour=2, minute=0),
            id='etl_job',
            name='ETL IVR nocturno',
            replace_existing=True,
        )
        cls.scheduler.start()
        logger.info("ETLScheduler iniciado — job etl_job @ 02:00 AM")

    @classmethod
    def stop(cls):
        if cls.scheduler:
            cls.scheduler.shutdown()
            cls.scheduler = None

    @classmethod
    def _quarter_activo(cls):
        today = date.today()
        q = (today.month - 1) // 3 + 1
        return f"Q0{q}_{today.year % 100:02d}"

    @classmethod
    def _registrar_inicio(cls, cursor, quarter):
        from django.utils import timezone
        import datetime
        timeout_at = timezone.now() + datetime.timedelta(minutes=30)
        cursor.execute(
            """INSERT INTO etl_runs
               (trimestre, inicio_at, timeout_at, status, trigger_source)
               VALUES (%s, NOW(), %s, 'en_ejecucion', 'mysql_event')""",
            [quarter, timeout_at]
        )
        return cursor.lastrowid

    @classmethod
    def _update_run(cls, cursor, run_id, status, error_message=None):
        try:
            cursor.execute(
                """UPDATE etl_runs
                   SET status=%s, fin_at=NOW(), error_message=%s
                   WHERE id=%s AND status='en_ejecucion'""",
                [status, error_message, run_id]
            )
        except Exception:
            pass

    @classmethod
    def run_etl(cls):
        quarter = cls._quarter_activo()
        logger.info(f"ETL nocturno iniciando — quarter {quarter}")
        run_id = None
        try:
            with connections['ivr'].cursor() as cur:
                run_id = cls._registrar_inicio(cur, quarter)
                cur.callproc('sp_etl_maestro', [])
                cls._update_run(cur, run_id, 'success')
                logger.info(f"ETL nocturno completado — run_id={run_id}")
        except OperationalError as e:
            logger.error(f"ETL nocturno error BD: {e}")
            if run_id:
                try:
                    with connections['ivr'].cursor() as cur:
                        cls._update_run(cur, run_id, 'failed', str(e))
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"ETL nocturno error: {e}", exc_info=True)
            if run_id:
                try:
                    with connections['ivr'].cursor() as cur:
                        cls._update_run(cur, run_id, 'failed', str(e))
                except Exception:
                    pass
