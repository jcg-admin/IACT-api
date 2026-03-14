# Flujo: scripts/bootstrap.sh

Entrypoint unico de provisioning y verificacion del entorno IACT API.

Un solo comando cubre desde la verificacion del sistema operativo
hasta la configuracion de bases de datos y Apache.
En ejecuciones posteriores actua como verificador de estado.

## Invocacion

```bash
sudo bash scripts/bootstrap.sh
```

> Requiere `sudo` porque las fases 2, 4 y 5 instalan paquetes del sistema,
> crean bases de datos y configuran Apache.

## Requisito de SO

Ubuntu 24.04.x LTS (noble). Cualquier otra distribucion o version
aborta en la Fase 1 antes de ejecutar nada mas.

---

## Utils cargados al inicio

```
bootstrap.sh
|-- utils/logging.sh       log_*, init_log, start_timer, show_elapsed, log_separator
|-- utils/core.sh          command_exists, require_command, exists_dir, exists_file,
|                          is_service_active, is_package_installed
|-- utils/validation.sh    validate_root, validate_file_exists
|-- utils/network.sh       tcp_is_reachable, can_reach_port
|-- utils/database.sh      mysql_wait_ready, pg_isready wrappers
+-- utils/provisioning.sh  init_log, step_header, log_step
```

---

## Estructura de scripts invocados

```
sudo bash scripts/bootstrap.sh
          |
          |-- provisioners/system/check_os.sh          [Fase 1]
          |-- provisioners/system/install_packages.sh  [Fase 2]
          |-- (Python inline)                           [Fase 3]
          |-- provisioners/postgres/db_setup.sh        [Fase 4]
          |-- provisioners/mariadb/db_setup.sh         [Fase 4]
          |-- apache/setup_apache.sh                   [Fase 5]
          +-- provisioners/system/check_tools.sh       [Fase 6]
```

---

## Fases

```
sudo bash scripts/bootstrap.sh
     |
     v
+------------------------------------------------------------+
|  FASE 1/6 -- Sistema operativo                  FATAL     |
+------------------------------------------------------------+
|  /etc/os-release                                          |
|    ID == ubuntu ?                                         |
|      NO --> log_fatal + exit 1  (no continua nada)        |
|    VERSION_ID comienza con "24.04" ?                      |
|      NO --> log_fatal + exit 1                            |
|      SI --> Ubuntu 24.04.x LTS confirmado                 |
+------------------------------------------------------------+
     | OK
     v
+------------------------------------------------------------+
|  FASE 2/6 -- Paquetes del sistema               FATAL     |
+------------------------------------------------------------+
|  Requiere root (validate_root)                            |
|  apt-get update (omite si indice < 1 hora)               |
|                                                           |
|  Grupo red        : net-tools, iproute2                   |
|  Grupo python     : python3, python3-dev, python3-pip,    |
|                     build-essential, pkg-config           |
|  Grupo postgresql : libpq-dev                             |
|  Grupo mariadb    : default-libmysqlclient-dev,           |
|                     mariadb-client                        |
|  Grupo general    : curl, git                             |
|                                                           |
|  Cada paquete: dpkg check ANTES de instalar (idempotente) |
|                                                           |
|  Meta-paquetes (verificacion funcional):                  |
|    python3-venv      --> python3 -m venv --help           |
|    postgresql-client --> psql --version                   |
|    (Ubuntu 24.04 los instala como python3.X-venv,         |
|     postgresql-client-16; se verifica el comando,         |
|     no el nombre exacto del paquete dpkg)                 |
+------------------------------------------------------------+
     | OK
     v
+------------------------------------------------------------+
|  FASE 3/6 -- Entorno Python                     FATAL     |
+------------------------------------------------------------+
|  python3 >= 3.11 ?                                        |
|      NO --> exit 1                                        |
|                                                           |
|  venv/ existe y tiene bin/pip ?                           |
|      SI --> skip creacion (idempotente)                   |
|      NO --> python3 -m venv venv/                         |
|                                                           |
|  requirements/development.txt existe ?                    |
|      NO --> exit 1                                        |
|                                                           |
|  venv/bin/pip install -r requirements/development.txt     |
|  import psycopg2 --> falla --> exit 1                     |
|  import MySQLdb  --> falla --> exit 1                     |
+------------------------------------------------------------+
     | OK
     v
+------------------------------------------------------------+
|  FASE 4/6 -- Bases de datos                     WARN      |
+------------------------------------------------------------+
|  provisioners/postgres/db_setup.sh                        |
|    Servicio activo ? NO --> WARN (continua)               |
|    SI:                                                    |
|      usuario django_user existe ? SI --> sync password    |
|                                    NO --> CREATE USER     |
|      base iact_analytics existe ? SI --> skip             |
|                                    NO --> CREATE DATABASE  |
|      GRANT ALL PRIVILEGES (idempotente en PostgreSQL)     |
|      Verifica conexion como django_user                   |
|                                                           |
|  provisioners/mariadb/db_setup.sh                         |
|    Servicio activo ? NO --> WARN (continua)               |
|    SI:                                                     |
|      base ivr_legacy existe ?    SI --> skip              |
|                                  NO --> CREATE DATABASE   |
|      usuario django_user existe ? SI --> sync password    |
|          (hosts % y localhost)    NO --> CREATE USER      |
|      GRANT SELECT (READ-ONLY, CNST-003 -- idempotente)    |
|      Verifica conexion y ausencia de permisos escritura   |
|                                                           |
|  Si ambas DBs inaccesibles --> WARN, bootstrap continua  |
+------------------------------------------------------------+
     |
     v
+------------------------------------------------------------+
|  FASE 5/6 -- Apache                             WARN      |
+------------------------------------------------------------+
|  apache/setup_apache.sh existe ? NO --> skip con WARN    |
|  apache2 / apache2ctl instalado? NO --> skip con WARN    |
|  SI:                                                      |
|    Verifica mod_wsgi habilitado                           |
|    Crea symlink sites-available/iact.conf                 |
|    Crea directorios static, media, logs                   |
|    collectstatic                                          |
|    Reinicia Apache                                        |
+------------------------------------------------------------+
     |
     v
+------------------------------------------------------------+
|  FASE 6/6 -- Verificacion completa              INFO      |
+------------------------------------------------------------+
|  Activa venv/bin en PATH (paquetes Python visibles)      |
|  Ejecuta provisioners/system/check_tools.sh:             |
|    Python version y pip                                   |
|    17 paquetes Python (django, psycopg2, mysqlclient...)  |
|    6 herramientas de testing                              |
|    3 herramientas dev opcionales                          |
|    4 herramientas de calidad de codigo                    |
|    Herramientas del sistema (git, curl, netstat, ss...)   |
|    Conectividad TCP a PostgreSQL y MariaDB                |
|    Variables en .env                                      |
|    Estructura del proyecto                                |
|  Muestra resumen: OK / WARN / ERROR                       |
+------------------------------------------------------------+
     |
     v
+------------------------------+
|  RESULTADO FINAL             |
|  Tiempo total en segundos    |
|  "Bootstrap completado."     |
|                              |
|  exit 0 siempre              |
|  (Fases 4-6 no son fatales) |
+------------------------------+
```

---

## Tabla de severidad por fase

| Fase | Descripcion              | Si falla   | Comportamiento              |
|------|--------------------------|------------|-----------------------------|
| 1    | SO Ubuntu 24.04.x        | FATAL      | exit 1, no ejecuta nada mas |
| 2    | Paquetes del sistema     | FATAL      | exit 1                      |
| 3    | Python + venv + pip      | FATAL      | exit 1                      |
| 4    | Bases de datos           | WARN       | Continua al paso siguiente  |
| 5    | Apache                   | WARN       | Continua al paso siguiente  |
| 6    | Verificacion             | INFO       | Muestra estado, no bloquea  |

---

## Idempotencia por fase

| Accion                         | Como se comprueba antes de ejecutar |
|--------------------------------|-------------------------------------|
| Verificar SO                   | /etc/os-release (solo lectura)      |
| Instalar paquete apt           | dpkg-query --status                 |
| Meta-paquete (venv, psql)      | Comando funcional (python3 -m venv) |
| Crear venv                     | exists_dir venv/ + exists bin/pip   |
| pip install                    | pip detecta versiones ya instaladas |
| Crear usuario DB               | SELECT en pg_roles / mysql.user     |
| Crear base de datos            | SELECT en pg_database / information_schema |
| GRANT privilegios              | Idempotente en PostgreSQL y MariaDB |
| Configurar Apache virtual host | Symlink ya existe --> skip          |

---

## Uso como verificador de estado

El bootstrap es idempotente: ejecutarlo en una maquina ya provisionada
muestra el estado actual de todo sin modificar nada (o solo sincroniza
contrasenas si cambiaron en .env).

```bash
# Verificar si las DBs estan activas, Python OK, Apache corriendo:
sudo bash scripts/bootstrap.sh
```

La Fase 6 (check_tools) siempre muestra el resumen completo del entorno.

---

## Scripts invocados y su ubicacion

```
scripts/
|-- bootstrap.sh                         <- ENTRYPOINT (este flujo)
|
+-- provisioners/
|   |-- system/
|   |   |-- check_os.sh                  <- Fase 1
|   |   |-- install_packages.sh          <- Fase 2
|   |   +-- check_tools.sh              <- Fase 6
|   |
|   |-- postgres/
|   |   +-- db_setup.sh                  <- Fase 4 (PostgreSQL)
|   |
|   +-- mariadb/
|       +-- db_setup.sh                  <- Fase 4 (MariaDB)
|
+-- apache/
|   +-- setup_apache.sh                  <- Fase 5
|
+-- utils/                               <- cargados por bootstrap.sh
|   |-- logging.sh, core.sh, validation.sh
|   +-- network.sh, database.sh, provisioning.sh
|
+-- check_tools.sh                       <- redirect a provisioners/system/
                                            (compatibilidad con scripts anteriores)
```

---

## Siguiente paso tras la primera ejecucion

```bash
source venv/bin/activate
cp .env.example .env        # si no existe todavia
# editar .env con los valores del entorno

cd callcentersite
python manage.py migrate
python manage.py createsuperuser
```
