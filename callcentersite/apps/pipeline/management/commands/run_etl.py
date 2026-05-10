"""
management/commands/run_etl.py

Disparo manual del pipeline ETL IVR con observabilidad completa.

Spec: arquitectura-tecnica/pipeline-etl-iact/triggers.rst (Mecanismo B)
DDL:  arquitectura-tecnica/pipeline-etl-iact/intermediate-tables.rst

Responsabilidades:
  1. Registrar inicio en etl_runs (MariaDB, alias 'ivr') con timeout_at.
  2. Lanzar thread de heartbeat que actualiza heartbeat_at cada 60s
     y marca timeout si el SP supera 30 min sin responder.
  3. Invocar sp_etl_maestro() — el SP maneja concurrencia internamente
     (consulta job_execution_log con status='RUNNING' en las últimas 6h).
  4. Actualizar etl_runs.status en finally.

Restricciones:
  CNST-ETL-001: solo SELECT en tbl_historico_* (el SP lo respeta).
  ADR-BACK-012: sin Redis/RabbitMQ — heartbeat con threading.Thread.
  CNST-003: min_intervalo_h=6 — sp_etl_maestro lo gestiona, no este command.

Nota sobre nomenclatura:
  El alias de conexión es 'ivr' (config/settings/base.py), no 'ivr_cliente'
  como aparece en el código de ejemplo del spec. El DDL es la fuente de
  verdad para los nombres de columna de etl_runs.
"""
import threading
from datetime import date

from django.core.management.base import BaseCommand, CommandError
from django.db import OperationalError, connections


class Command(BaseCommand):
    help = (
        "Dispara el pipeline ETL IVR invocando sp_etl_maestro() en MariaDB. "
        "Registra la ejecución en etl_runs con heartbeat de timeout."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--quarter",
            type=str,
            default=None,
            help="Quarter a procesar, ej: Q02_26. Default: quarter activo.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            default=False,
            help=(
                "Forzar ejecución aunque haya un run reciente. "
                "sp_etl_maestro respetará min_intervalo_h igualmente."
            ),
        )

    def handle(self, *args, **options):
        quarter = options["quarter"] or self._quarter_activo()
        self.stdout.write(f"Iniciando ETL para quarter: {quarter}")

        run_id = self._registrar_inicio(quarter)
        self.stdout.write(f"etl_runs.id={run_id} registrado")

        stop_event = threading.Event()
        heartbeat = threading.Thread(
            target=self._heartbeat,
            args=(run_id, stop_event),
            daemon=True,
        )
        heartbeat.start()

        try:
            self._ejecutar_sp()
            self._update_run(run_id, "success")
            self.stdout.write(self.style.SUCCESS("ETL completado exitosamente"))
        except OperationalError as exc:
            self._update_run(run_id, "failed", str(exc))
            raise CommandError(f"Error de base de datos: {exc}") from exc
        except Exception as exc:
            self._update_run(run_id, "failed", str(exc))
            raise
        finally:
            stop_event.set()

    # ------------------------------------------------------------------ #

    def _quarter_activo(self) -> str:
        """
        Calcula el quarter activo a partir de la fecha actual.
        Formato: Q0N_YY (ej: Q02_26 para abril-junio 2026).
        """
        today = date.today()
        quarter_num = (today.month - 1) // 3 + 1
        year_short = today.year % 100
        return f"Q0{quarter_num}_{year_short:02d}"

    def _registrar_inicio(self, quarter: str) -> int:
        """
        INSERT en etl_runs con timeout_at = NOW() + 30 MIN.
        Retorna el id generado.

        Columnas del DDL (intermediate-tables.rst):
          trimestre, inicio_at, timeout_at, status, trigger_source
        """
        with connections["ivr"].cursor() as c:
            c.execute(
                """
                INSERT INTO etl_runs
                    (trimestre, inicio_at, timeout_at, status, trigger_source)
                VALUES
                    (%s, NOW(), DATE_ADD(NOW(), INTERVAL 30 MINUTE),
                     'en_ejecucion', 'django_command')
                """,
                [quarter],
            )
            return c.lastrowid

    def _ejecutar_sp(self) -> None:
        """
        Llama sp_etl_maestro() en MariaDB.
        El SP gestiona concurrencia y checkpoints internamente.
        """
        with connections["ivr"].cursor() as c:
            c.callproc("sp_etl_maestro", [])

    def _heartbeat(self, run_id: int, stop_event: threading.Event) -> None:
        """
        Thread daemon: actualiza heartbeat_at cada 60s y marca timeout
        si el SP supera 30 min sin responder (timeout_at < NOW()).

        El intervalo de 60s viene de intermediate-tables.rst:
          "El management command run_etl actualiza heartbeat_at cada
           60 segundos en un threading.Thread paralelo."
        """
        while not stop_event.wait(timeout=60):
            try:
                with connections["ivr"].cursor() as c:
                    # Actualizar heartbeat si sigue en ejecución
                    c.execute(
                        """
                        UPDATE etl_runs
                        SET heartbeat_at = NOW()
                        WHERE id = %s
                          AND status = 'en_ejecucion'
                        """,
                        [run_id],
                    )
                    # Marcar timeout si superó los 30 min
                    c.execute(
                        """
                        UPDATE etl_runs
                        SET status        = 'timeout',
                            fin_at        = NOW(),
                            error_message = 'Sin respuesta > 30 min'
                        WHERE id = %s
                          AND status = 'en_ejecucion'
                          AND timeout_at < NOW()
                        """,
                        [run_id],
                    )
            except Exception:
                # El heartbeat no debe matar el thread principal
                pass

    def _update_run(
        self, run_id: int, status: str, error: str | None = None
    ) -> None:
        """
        UPDATE etl_runs al finalizar (éxito, fallo o timeout externo).
        Columnas del DDL: status, fin_at, error_message.
        """
        try:
            with connections["ivr"].cursor() as c:
                c.execute(
                    """
                    UPDATE etl_runs
                    SET status        = %s,
                        fin_at        = NOW(),
                        error_message = %s
                    WHERE id = %s
                    """,
                    [status, error, run_id],
                )
        except Exception:
            # Si la BD no está disponible en el finally, no propagar
            pass
