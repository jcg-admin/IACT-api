# Flujo: scripts/bootstrap.sh

Prepara el entorno local de desarrollo. No instala ni configura bases de datos.

## Invocacion

```bash
bash scripts/bootstrap.sh
```

## Utils cargados al inicio

```
bootstrap.sh
|-- utils/core.sh          require_command, command_exists, is_package_installed
|-- utils/logging.sh       log_*, init_log, start_timer, show_elapsed
|-- utils/network.sh       can_reach_port
|-- utils/database.sh      tcp_is_reachable
|-- utils/validation.sh    validate_file_exists, exists_file, exists_dir
+-- utils/provisioning.sh  step_header, log_step, log_separator
```

## Pasos

```
bootstrap.sh
     |
     v
+------------------------------------------------------------+
|  PASO 1/6 -- Python                            BLOQUEANTE  |
+------------------------------------------------------------+
|  python3 --version >= 3.11 ?                               |
|      NO --> log_fatal -> exit 1                            |
|      SI --> check pip3 / pip disponible                    |
+------------------------------------------------------------+
     | OK
     v
+------------------------------------------------------------+
|  PASO 2/6 -- Entorno virtual                   BLOQUEANTE  |
+------------------------------------------------------------+
|  venv/ existe ?                                            |
|      NO --> python3 -m venv venv                           |
|      SI --> skip (idempotente)                             |
|  venv/bin/pip existe ?                                     |
|      NO --> log_error -> return 1                          |
+------------------------------------------------------------+
     | OK
     v
+------------------------------------------------------------+
|  PASO 3/6 -- Dependencias del sistema          BLOQUEANTE  |
+------------------------------------------------------------+
|  apt-get update -qq                                        |
|  Para cada paquete:                                        |
|    libpq-dev, default-libmysqlclient-dev,                  |
|    python3-dev, build-essential, pkg-config                |
|                                                            |
|    instalado ? SI --> skip (idempotente)                   |
|               NO --> apt-get install -y                    |
+------------------------------------------------------------+
     | OK
     v
+------------------------------------------------------------+
|  PASO 4/6 -- Dependencias Python               BLOQUEANTE  |
+------------------------------------------------------------+
|  venv/bin/pip install -r requirements/development.txt      |
|  import psycopg2  -> falla --> return 1                    |
|  import MySQLdb   -> falla --> return 1                    |
+------------------------------------------------------------+
     | OK
     v
+------------------------------------------------------------+
|  PASO 5/6 -- Archivo .env                  NO BLOQUEANTE   |
+------------------------------------------------------------+
|  .env existe ?                                             |
|      NO --> log_error (continua)                           |
|      SI --> verifica variables:                            |
|             SECRET_KEY, DB_HOST, DB_NAME, DB_USER,         |
|             DB_PASSWORD, IVR_DB_HOST, IVR_DB_NAME          |
|             faltante --> log_warn (no bloquea)             |
+------------------------------------------------------------+
     |
     v
+------------------------------------------------------------+
|  PASO 6/6 -- Conectividad DB               NO BLOQUEANTE   |
+------------------------------------------------------------+
|  tcp_is_reachable 127.0.0.1 5432 (timeout 3s)              |
|      NO --> log_warn                                       |
|  tcp_is_reachable 127.0.0.1 3306 (timeout 3s)              |
|      NO --> log_warn                                       |
+------------------------------------------------------------+
     |
     v
+------------------------------+
|  RESUMEN                     |
|  failed == 0 --> exit 0      |
|  failed  > 0 --> exit 0 *    |
|  paso 1-4 fallo --> exit 1   |
+------------------------------+
```

> Los pasos 5 y 6 cuentan como advertencias, no como errores fatales.

## Idempotencia

- venv ya existe: no se recrea
- paquete del sistema instalado: apt-get hace skip
- dependencias pip: no reinstala si la version es correcta
- se puede ejecutar N veces sin efecto colateral

## Siguiente paso sugerido

```bash
source venv/bin/activate
cd callcentersite && python manage.py migrate
```
