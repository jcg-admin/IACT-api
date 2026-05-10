"""
tests/unit/pipeline/test_run_etl_command.py

Tests unitarios para manage.py run_etl.

Todos los tests mockean connections['ivr'] — no requieren MariaDB real.
El cursor mock captura llamadas a execute() y callproc() para verificar
que el command usa las columnas correctas del DDL de etl_runs.
"""
import threading
from datetime import date
from unittest.mock import MagicMock, call, patch

import pytest

from apps.pipeline.management.commands.run_etl import Command


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def cmd():
    return Command()


@pytest.fixture
def mock_cursor():
    """Cursor mock con lastrowid=42."""
    cursor = MagicMock()
    cursor.__enter__ = lambda s: s
    cursor.__exit__ = MagicMock(return_value=False)
    cursor.lastrowid = 42
    return cursor


@pytest.fixture
def mock_connections(mock_cursor):
    """
    Parchea connections['ivr'] para todos los tests del archivo.
    El connection mock retorna siempre el mismo cursor.
    """
    conn = MagicMock()
    conn.cursor.return_value = mock_cursor
    with patch(
        "apps.pipeline.management.commands.run_etl.connections",
        {"ivr": conn},
    ) as patched:
        yield patched, conn, mock_cursor


# ── _quarter_activo() ─────────────────────────────────────────────────────────


class TestQuarterActivo:
    """Cálculo del quarter activo sin dependencias externas."""

    @pytest.mark.parametrize("month,expected", [
        (1,  "Q01_26"),
        (2,  "Q01_26"),
        (3,  "Q01_26"),
        (4,  "Q02_26"),
        (5,  "Q02_26"),
        (6,  "Q02_26"),
        (7,  "Q03_26"),
        (9,  "Q03_26"),
        (10, "Q04_26"),
        (12, "Q04_26"),
    ])
    def test_quarter_por_mes(self, cmd, month, expected):
        with patch("apps.pipeline.management.commands.run_etl.date") as mock_date:
            mock_date.today.return_value = date(2026, month, 1)
            assert cmd._quarter_activo() == expected

    def test_formato_dos_digitos_anio(self, cmd):
        with patch("apps.pipeline.management.commands.run_etl.date") as mock_date:
            mock_date.today.return_value = date(2030, 1, 1)
            result = cmd._quarter_activo()
            assert result == "Q01_30"


# ── _registrar_inicio() ───────────────────────────────────────────────────────


class TestRegistrarInicio:
    """INSERT en etl_runs con las columnas exactas del DDL."""

    def test_insert_usa_columnas_ddl(self, cmd, mock_connections):
        _, conn, cursor = mock_connections
        run_id = cmd._registrar_inicio("Q02_26")

        sql_llamado = cursor.execute.call_args[0][0]
        params = cursor.execute.call_args[0][1]

        assert "inicio_at" in sql_llamado
        assert "timeout_at" in sql_llamado
        assert "trigger_source" in sql_llamado
        assert "status" in sql_llamado
        assert "en_ejecucion" in sql_llamado
        assert "django_command" in sql_llamado
        assert params[0] == "Q02_26"

    def test_retorna_lastrowid(self, cmd, mock_connections):
        _, conn, cursor = mock_connections
        cursor.lastrowid = 99
        assert cmd._registrar_inicio("Q01_25") == 99

    def test_no_usa_columnas_del_borrador(self, cmd, mock_connections):
        """
        El código de ejemplo del spec usaba nombres distintos (iniciado_en,
        ejecutado_por). El DDL real es la fuente de verdad.
        """
        _, conn, cursor = mock_connections
        cmd._registrar_inicio("Q02_26")
        sql_llamado = cursor.execute.call_args[0][0]

        assert "iniciado_en" not in sql_llamado
        assert "ejecutado_por" not in sql_llamado
        assert "estado" not in sql_llamado


# ── _ejecutar_sp() ───────────────────────────────────────────────────────────


class TestEjecutarSP:
    """Llama exactamente callproc('sp_etl_maestro', [])."""

    def test_llama_sp_etl_maestro(self, cmd, mock_connections):
        _, conn, cursor = mock_connections
        cmd._ejecutar_sp()
        cursor.callproc.assert_called_once_with("sp_etl_maestro", [])

    def test_no_pasa_parametros_al_sp(self, cmd, mock_connections):
        _, conn, cursor = mock_connections
        cmd._ejecutar_sp()
        _, args = cursor.callproc.call_args
        # callproc(name, params) — params debe ser lista vacía
        assert cursor.callproc.call_args[0][1] == []


# ── _update_run() ─────────────────────────────────────────────────────────────


class TestUpdateRun:
    """UPDATE etl_runs con columnas del DDL."""

    def test_update_success(self, cmd, mock_connections):
        _, conn, cursor = mock_connections
        cmd._update_run(42, "success")
        sql = cursor.execute.call_args[0][0]
        params = cursor.execute.call_args[0][1]

        assert "fin_at" in sql
        assert "error_message" in sql
        assert params[0] == "success"
        assert params[2] == 42

    def test_update_failed_con_mensaje(self, cmd, mock_connections):
        _, conn, cursor = mock_connections
        cmd._update_run(7, "failed", "connection refused")
        params = cursor.execute.call_args[0][1]

        assert params[0] == "failed"
        assert params[1] == "connection refused"

    def test_no_propaga_excepcion_bd(self, cmd, mock_connections):
        """_update_run se llama en finally — no debe propagar si la BD cae."""
        _, conn, cursor = mock_connections
        cursor.execute.side_effect = Exception("BD caída")
        # No debe lanzar excepción
        cmd._update_run(1, "failed")


# ── handle() — flujo completo ─────────────────────────────────────────────────


class TestHandle:
    """Flujo completo del command con todos los métodos mockeados."""

    def _options(self, quarter=None, force=False):
        return {"quarter": quarter, "force": force}

    def test_exito_llama_update_success(self, cmd):
        with patch.object(cmd, "_registrar_inicio", return_value=1), \
             patch.object(cmd, "_ejecutar_sp"), \
             patch.object(cmd, "_update_run") as mock_update, \
             patch("apps.pipeline.management.commands.run_etl.threading"):
            cmd.handle(**self._options(quarter="Q02_26"))
            mock_update.assert_called_with(1, "success")

    def test_fallo_llama_update_failed(self, cmd):
        from django.core.management.base import CommandError

        with patch.object(cmd, "_registrar_inicio", return_value=2), \
             patch.object(cmd, "_ejecutar_sp",
                          side_effect=Exception("crash")), \
             patch.object(cmd, "_update_run") as mock_update, \
             patch("apps.pipeline.management.commands.run_etl.threading"):
            with pytest.raises(Exception, match="crash"):
                cmd.handle(**self._options(quarter="Q02_26"))
            mock_update.assert_called_with(2, "failed", "crash")

    def test_stop_event_se_setea_en_finally(self, cmd):
        stop_event = threading.Event()

        with patch.object(cmd, "_registrar_inicio", return_value=3), \
             patch.object(cmd, "_ejecutar_sp"), \
             patch.object(cmd, "_update_run"), \
             patch("apps.pipeline.management.commands.run_etl.threading.Event",
                   return_value=stop_event), \
             patch("apps.pipeline.management.commands.run_etl.threading.Thread"):
            cmd.handle(**self._options(quarter="Q02_26"))
            assert stop_event.is_set()

    def test_stop_event_se_setea_incluso_en_fallo(self, cmd):
        stop_event = threading.Event()

        with patch.object(cmd, "_registrar_inicio", return_value=4), \
             patch.object(cmd, "_ejecutar_sp",
                          side_effect=Exception("fallo")), \
             patch.object(cmd, "_update_run"), \
             patch("apps.pipeline.management.commands.run_etl.threading.Event",
                   return_value=stop_event), \
             patch("apps.pipeline.management.commands.run_etl.threading.Thread"):
            with pytest.raises(Exception):
                cmd.handle(**self._options(quarter="Q02_26"))
            assert stop_event.is_set()

    def test_usa_quarter_activo_si_no_se_pasa(self, cmd):
        with patch.object(cmd, "_registrar_inicio", return_value=5) as mock_reg, \
             patch.object(cmd, "_ejecutar_sp"), \
             patch.object(cmd, "_update_run"), \
             patch.object(cmd, "_quarter_activo", return_value="Q03_26"), \
             patch("apps.pipeline.management.commands.run_etl.threading"):
            cmd.handle(**self._options())
            mock_reg.assert_called_with("Q03_26")

    def test_usa_quarter_pasado_como_argumento(self, cmd):
        with patch.object(cmd, "_registrar_inicio", return_value=6) as mock_reg, \
             patch.object(cmd, "_ejecutar_sp"), \
             patch.object(cmd, "_update_run"), \
             patch("apps.pipeline.management.commands.run_etl.threading"):
            cmd.handle(**self._options(quarter="Q01_25"))
            mock_reg.assert_called_with("Q01_25")

    def test_heartbeat_thread_es_daemon(self, cmd):
        thread_mock = MagicMock()

        with patch.object(cmd, "_registrar_inicio", return_value=7), \
             patch.object(cmd, "_ejecutar_sp"), \
             patch.object(cmd, "_update_run"), \
             patch("apps.pipeline.management.commands.run_etl.threading.Thread",
                   return_value=thread_mock) as thread_cls, \
             patch("apps.pipeline.management.commands.run_etl.threading.Event"):
            cmd.handle(**self._options(quarter="Q02_26"))
            # daemon=True en la construcción del Thread
            assert thread_cls.call_args[1]["daemon"] is True


# ── _heartbeat() ─────────────────────────────────────────────────────────────


class TestHeartbeat:
    """El heartbeat actualiza heartbeat_at y detecta timeout."""

    def test_actualiza_heartbeat_at(self, cmd, mock_connections):
        _, conn, cursor = mock_connections
        stop_event = threading.Event()

        # Ejecutar una iteración: stop después del primer wait
        original_wait = threading.Event.wait

        call_count = [0]
        def fake_wait(self_ev, timeout=None):
            call_count[0] += 1
            if call_count[0] >= 2:
                return True   # sale del bucle
            return False

        with patch.object(threading.Event, "wait", fake_wait):
            cmd._heartbeat(42, stop_event)

        # Debe haber llamado execute al menos una vez con heartbeat_at
        calls_sql = [str(c) for c in cursor.execute.call_args_list]
        assert any("heartbeat_at" in s for s in calls_sql)

    def test_no_propaga_excepcion_en_heartbeat(self, cmd, mock_connections):
        """El heartbeat no debe matar el thread principal si la BD cae."""
        _, conn, cursor = mock_connections
        cursor.execute.side_effect = Exception("BD caída")
        stop_event = threading.Event()

        call_count = [0]
        def fake_wait(self_ev, timeout=None):
            call_count[0] += 1
            return call_count[0] >= 2

        with patch.object(threading.Event, "wait", fake_wait):
            # No debe lanzar excepción
            cmd._heartbeat(1, stop_event)



class TestHeartbeatTimeout:
    """
    T-056 — Verificar que el heartbeat marca status='timeout' cuando
    timeout_at < NOW() y status='en_ejecucion'.

    Tests unitarios: verifican la lógica SQL del UPDATE de timeout
    sin necesitar la BD real.
    """

    def _one_iteration(self, cmd, mock_connections):
        """Ejecuta exactamente una iteración del heartbeat."""
        _, conn, cursor = mock_connections
        stop_event = threading.Event()

        call_count = [0]
        def fake_wait(self_ev, timeout=None):
            call_count[0] += 1
            return call_count[0] >= 2   # una iteración, luego sale

        with patch.object(threading.Event, "wait", fake_wait):
            cmd._heartbeat(99, stop_event)

        return cursor

    def test_sql_timeout_usa_condicion_timeout_at(self, cmd, mock_connections):
        """
        El UPDATE de timeout debe incluir AND timeout_at < NOW()
        para no marcar como timeout un run que aún está dentro del plazo.
        """
        cursor = self._one_iteration(cmd, mock_connections)

        all_sql = " ".join(str(c) for c in cursor.execute.call_args_list)
        assert "timeout_at" in all_sql
        assert "timeout" in all_sql

    def test_sql_timeout_solo_afecta_estado_en_ejecucion(self, cmd, mock_connections):
        """
        El WHERE del UPDATE de timeout incluye AND status = 'en_ejecucion'.
        Un run ya cerrado (success/failed) no debe ser sobreescrito
        aunque su timeout_at esté en el pasado.
        """
        cursor = self._one_iteration(cmd, mock_connections)

        # Buscar el execute que hace el UPDATE de timeout
        timeout_calls = [
            str(c) for c in cursor.execute.call_args_list
            if "timeout" in str(c) and "UPDATE" in str(c)
        ]
        assert len(timeout_calls) >= 1
        sql = timeout_calls[-1]
        assert "en_ejecucion" in sql

    def test_sql_timeout_actualiza_fin_at(self, cmd, mock_connections):
        """El UPDATE de timeout debe escribir fin_at = NOW()."""
        cursor = self._one_iteration(cmd, mock_connections)
        all_sql = " ".join(str(c) for c in cursor.execute.call_args_list)
        assert "fin_at" in all_sql

    def test_sql_timeout_escribe_error_message(self, cmd, mock_connections):
        """El UPDATE de timeout incluye un error_message descriptivo."""
        cursor = self._one_iteration(cmd, mock_connections)
        all_sql = " ".join(str(c) for c in cursor.execute.call_args_list)
        assert "error_message" in all_sql
        assert "30 min" in all_sql

    def test_heartbeat_actualiza_heartbeat_at_antes_de_timeout(self, cmd, mock_connections):
        """
        En una misma iteración el heartbeat ejecuta DOS UPDATEs:
        1. heartbeat_at = NOW()   (liveness)
        2. timeout check          (si expiró)
        El UPDATE de heartbeat_at va PRIMERO.
        """
        cursor = self._one_iteration(cmd, mock_connections)
        calls = cursor.execute.call_args_list

        # Debe haber al menos 2 calls (heartbeat_at + timeout check)
        assert len(calls) >= 2

        first_sql  = str(calls[0])
        second_sql = str(calls[1])

        assert "heartbeat_at" in first_sql, "El primer UPDATE debe ser heartbeat_at"
        assert "timeout" in second_sql,     "El segundo UPDATE debe ser el check de timeout"

    def test_stop_event_detiene_el_heartbeat(self, cmd, mock_connections):
        """
        Cuando stop_event ya está seteado desde el inicio,
        el heartbeat no ejecuta ningún UPDATE.
        """
        _, conn, cursor = mock_connections
        stop_event = threading.Event()
        stop_event.set()   # ya está seteado

        # El wait(timeout=60) debe retornar True inmediatamente
        cmd._heartbeat(1, stop_event)

        # No debe haber ejecutado ningún UPDATE
        cursor.execute.assert_not_called()
