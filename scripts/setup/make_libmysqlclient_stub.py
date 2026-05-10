#!/usr/bin/env python3
"""
make_libmysqlclient_stub.py

Crea /usr/local/lib/libmysqlclient.so.21 como librería stub cuando
libmysqlclient21 no está instalado en el sistema.

CUÁNDO USAR:
    Solo en el sandbox de desarrollo donde archive.ubuntu.com está bloqueado.
    En cualquier entorno con apt disponible, instalar la librería real:

        sudo apt-get install -y libmysqlclient21   # MySQL 8.0
        # o
        sudo apt-get install -y libmariadb3        # MariaDB

POR QUÉ EXISTE:
    Django carga django.db.backends.mysql al arrancar (por DATABASES['ivr']),
    lo que importa MySQLdb, que necesita libmysqlclient.so.21. Sin ella,
    426 tests de la suite unit fallan con ImportError antes de ejecutar
    una sola línea de código de test.

    El stub expone los 50 símbolos que mysqlclient==2.2.1 necesita para
    importar. Las funciones retornan NULL — cualquier intento real de
    conectarse a MariaDB fallará en runtime, no en import.

IDEMPOTENTE: Si la librería real o el stub ya existen, no hace nada.

Ver: docs/architecture/HALLAZGOS-ENTORNO-SANDBOX-2026-05-10.md H-ENV-001
"""

import os
import subprocess
import sys
import tempfile

SYMBOLS = [
    "mysql_affected_rows", "mysql_autocommit", "mysql_change_user",
    "mysql_character_set_name", "mysql_close", "mysql_commit",
    "mysql_data_seek", "mysql_debug", "mysql_dump_debug_info",
    "mysql_errno", "mysql_error", "mysql_escape_string",
    "mysql_fetch_fields", "mysql_fetch_lengths", "mysql_fetch_row",
    "mysql_field_count", "mysql_free_result", "mysql_get_character_set_info",
    "mysql_get_client_info", "mysql_get_host_info", "mysql_get_proto_info",
    "mysql_get_server_info", "mysql_info", "mysql_init",
    "mysql_insert_id", "mysql_kill", "mysql_more_results",
    "mysql_next_result", "mysql_num_fields", "mysql_num_rows",
    "mysql_options", "mysql_ping", "mysql_read_query_result",
    "mysql_real_connect", "mysql_real_escape_string_quote",
    "mysql_real_query", "mysql_rollback", "mysql_select_db",
    "mysql_send_query", "mysql_server_init", "mysql_set_character_set",
    "mysql_set_server_option", "mysql_shutdown", "mysql_sqlstate",
    "mysql_ssl_set", "mysql_stat", "mysql_store_result",
    "mysql_thread_id", "mysql_use_result", "mysql_warning_count",
]

TARGET = "/usr/local/lib/libmysqlclient.so.21"
VERSION_TAG = "libmysqlclient_21.0"


def real_library_installed():
    result = subprocess.run(["ldconfig", "-p"], capture_output=True, text=True)
    for line in result.stdout.splitlines():
        if "libmysqlclient.so.21" in line and "/usr/local/lib" not in line:
            return True
    return False


def stub_already_present():
    return os.path.exists(TARGET)


def build_stub():
    c_code = "/* stub: libmysqlclient.so.21 — sandbox sin MariaDB/MySQL */\n"
    c_code += "#include <stddef.h>\n\n"
    for sym in SYMBOLS:
        c_code += f"void* {sym}() {{ return 0; }}\n"

    vs_code = f"{VERSION_TAG} {{\n  global:\n"
    for sym in SYMBOLS:
        vs_code += f"    {sym};\n"
    vs_code += "  local:\n    *;\n};\n"

    with tempfile.TemporaryDirectory() as tmp:
        c_path = os.path.join(tmp, "stub.c")
        vs_path = os.path.join(tmp, "stub.map")
        with open(c_path, "w") as f:
            f.write(c_code)
        with open(vs_path, "w") as f:
            f.write(vs_code)

        result = subprocess.run(
            ["gcc", "-shared", "-fPIC",
             f"-Wl,--version-script={vs_path}",
             "-o", TARGET, c_path],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"ERROR gcc: {result.stderr}", file=sys.stderr)
            sys.exit(1)

    subprocess.run(["ldconfig"], check=True)


def verify_import():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    venv_python = os.path.join(script_dir, "../../venv/bin/python")
    python = venv_python if os.path.exists(venv_python) else sys.executable
    r = subprocess.run([python, "-c", "import MySQLdb; print('OK')"],
                       capture_output=True, text=True)
    return r.returncode == 0 and "OK" in r.stdout


def main():
    if os.geteuid() != 0:
        print("Ejecutar con: sudo python3 scripts/setup/make_libmysqlclient_stub.py",
              file=sys.stderr)
        sys.exit(1)

    if real_library_installed():
        print("libmysqlclient.so.21 real instalada — nada que hacer.")
        return

    if stub_already_present():
        if verify_import():
            print(f"Stub ya presente en {TARGET} y MySQLdb importa. OK.")
            return
        print("Stub presente pero roto — reconstruyendo...")

    print(f"Construyendo stub con {len(SYMBOLS)} símbolos...")
    build_stub()

    if verify_import():
        print(f"OK — {TARGET} instalado. MySQLdb importa correctamente.")
        print()
        print("Este es un stub de desarrollo — no hace conexiones reales.")
        print("Para entorno completo: cd /ruta/IACT-db && sudo bash bootstrap.sh")
    else:
        print("ERROR: stub creado pero MySQLdb no importa.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
