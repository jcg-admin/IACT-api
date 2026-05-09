#!/usr/bin/env python3
"""
make_libmysqlclient_stub.py

Crea /usr/local/lib/libmysqlclient.so.21 como librería stub cuando
libmysqlclient21 no está instalado en el sistema.

Uso:
    sudo python3 scripts/setup/make_libmysqlclient_stub.py

Propósito:
    En el entorno de sandbox, la red bloquea archive.ubuntu.com, por lo que
    no se puede instalar libmysqlclient21 vía apt. Sin la librería, Django
    lanza ImportError al cargar django.db.backends.mysql, incluso si ningún
    test usa MariaDB directamente.

    Este stub expone los 50 símbolos que mysqlclient==2.2.1 necesita para
    importar. Satisface al linker dinámico. No simula conexiones reales —
    cualquier intento de conectarse a MySQL lanzará una excepción en runtime,
    lo cual es correcto para unit tests que mockean la BD.

    Ver: IACT-api/docs/architecture/HALLAZGOS-ENTORNO-SANDBOX-2026-05-10.md H-ENV-001

Condiciones de aplicación:
    - Solo en entornos sin libmysqlclient21 instalado.
    - En producción y en el entorno de desarrollo con IACT-db, la librería
      real está disponible y este script no debe ejecutarse.

Requiere:
    - gcc disponible en el sistema.
    - Permisos de escritura en /usr/local/lib/.
    - ldconfig disponible.
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
VERSION_SCRIPT = "libmysqlclient_21.0"


def real_library_installed() -> bool:
    """Devuelve True si la librería real ya está disponible."""
    result = subprocess.run(
        ["ldconfig", "-p"],
        capture_output=True, text=True,
    )
    lines = result.stdout.splitlines()
    return any("libmysqlclient.so.21" in line and "/usr/local/lib" not in line
               for line in lines)


def stub_already_present() -> bool:
    return os.path.exists(TARGET)


def build_stub() -> None:
    c_code = "/* stub: libmysqlclient.so.21 — sandbox sin MariaDB instalado */\n"
    for sym in SYMBOLS:
        c_code += f"void* {sym}() {{ return 0; }}\n"

    vs_code = f"{VERSION_SCRIPT} {{\n  global:\n"
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
            [
                "gcc", "-shared", "-fPIC",
                f"-Wl,--version-script={vs_path}",
                "-o", TARGET,
                c_path,
            ],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"ERROR: gcc falló\n{result.stderr}", file=sys.stderr)
            sys.exit(1)

    subprocess.run(["ldconfig"], check=True, capture_output=True)


def main() -> None:
    if real_library_installed():
        print("libmysqlclient.so.21 ya está instalada (real). No se requiere stub.")
        sys.exit(0)

    if stub_already_present():
        print(f"Stub ya presente en {TARGET}. Actualizando...")

    if os.geteuid() != 0:
        print("ERROR: requiere permisos root (sudo).", file=sys.stderr)
        sys.exit(1)

    build_stub()

    # Verificar que MySQLdb importa
    result = subprocess.run(
        [sys.executable, "-c", "import MySQLdb; print('MySQLdb OK')"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print(f"Stub creado en {TARGET}")
        print(result.stdout.strip())
    else:
        print(f"ADVERTENCIA: stub creado pero MySQLdb sigue fallando:")
        print(result.stderr.strip(), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
