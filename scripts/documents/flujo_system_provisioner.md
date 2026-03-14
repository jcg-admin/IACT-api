# Flujo: scripts/provisioners/system/

Scripts de nivel sistema para Ubuntu 24.04.x LTS.
Son invocados por `bootstrap.sh` pero tambien pueden ejecutarse de forma independiente.

Todos son idempotentes: ejecutarlos N veces produce el mismo resultado final.

---

## Estructura

```
scripts/provisioners/system/
|-- check_os.sh          Verifica SO Ubuntu 24.04.x LTS  (Fase 1)
|-- install_packages.sh  Instala paquetes del sistema     (Fase 2)
+-- check_tools.sh       Verifica estado del entorno      (Fase 6)
```

---

## check_os.sh

### Proposito

Gate de entrada: aborta cualquier provisionamiento si el SO no es
Ubuntu 24.04.x LTS. No instala ni modifica nada.

### Invocacion

```bash
bash scripts/provisioners/system/check_os.sh
# o automaticamente desde:
sudo bash scripts/bootstrap.sh
```

### Logica

```
check_os.sh
     |
     |-- Lee /etc/os-release
     |       NO existe --> log_fatal + exit 1
     |
     |-- ID == "ubuntu" ?
     |       NO --> log_fatal + exit 1
     |               Imprime: SO detectado vs SO requerido
     |
     |-- VERSION_ID comienza con "24.04" ?
     |       NO --> log_fatal + exit 1
     |               Acepta: 24.04 / 24.04.1 / 24.04.2 / 24.04.3 / ...
     |
     +-- SI --> log_success "Ubuntu 24.04.x LTS confirmado"
                exit 0
```

### Codigos de salida

| Codigo | Significado                        |
|--------|------------------------------------|
| 0      | Ubuntu 24.04.x LTS confirmado      |
| 1      | SO no compatible o no determinable |

---

## install_packages.sh

### Proposito

Instala todos los paquetes del sistema necesarios para ejecutar IACT API.
Idempotente: verifica el estado dpkg antes de instalar.
Requiere root (sudo).

### Invocacion

```bash
sudo bash scripts/provisioners/system/install_packages.sh
# o automaticamente desde:
sudo bash scripts/bootstrap.sh
```

### Grupos de paquetes

```
Grupo red
  net-tools      netstat, arp, ifconfig
  iproute2       ss, ip

Grupo python
  python3        interprete
  python3-dev    headers para compilar extensiones C (psycopg2, mysqlclient)
  python3-pip    gestor de paquetes
  build-essential gcc, make, etc.
  pkg-config     compilacion de modulos nativos

Grupo postgresql
  libpq-dev      headers para compilar psycopg2

Grupo mariadb
  default-libmysqlclient-dev  headers para compilar mysqlclient
  mariadb-client              cliente mysql / mysqladmin

Grupo general
  curl           descarga de recursos y healthchecks
  git            control de versiones
```

### Meta-paquetes (verificacion funcional)

Ubuntu 24.04 instala algunos paquetes con nombre versionado en vez del
nombre generico del meta-paquete. Se verifican por funcionalidad,
no por nombre exacto dpkg:

```
Meta-paquete       Nombre real en Ubuntu 24.04   Verificacion
--------------     ---------------------------    ---------------
python3-venv       python3.12-venv                python3 -m venv --help
postgresql-client  postgresql-client-16           psql --version
```

Si el comando funciona: marca como OK sin instalar nada.
Si el comando falla: intenta `apt-get install <meta-paquete>` como fallback.

### Flujo interno

```
install_packages.sh
     |
     |-- PASO 1/5: Prerequisitos
     |       EUID == 0 ?  NO --> exit 1
     |       apt-get disponible ? NO --> exit 1
     |
     |-- PASO 2/5: apt-get update
     |       indice < 1 hora de antiguedad --> omite (optimizacion)
     |       >= 1 hora --> apt-get update -qq
     |
     |-- PASO 3/5: Grupo red
     |       Para net-tools, iproute2:
     |         dpkg instalado? SI --> skip
     |                         NO --> apt-get install -y -qq
     |
     |-- PASO 4/5: Grupos python, postgresql, mariadb, general
     |       Para cada paquete en cada grupo:
     |         dpkg instalado? SI --> skip
     |                         NO --> acumula en lista to_install[]
     |       apt-get install -y -qq ${to_install[@]}
     |       Verifica post-instalacion via dpkg
     |
     |       Meta-paquetes (verificacion funcional):
     |         comando disponible? SI --> "funcional" (no instala)
     |                             NO --> apt-get install fallback
     |
     +-- PASO 5/5: Verificacion de herramientas clave
             python3, pip3, git, curl, psql, mysql, netstat, ss
             Muestra version de cada una
             Herramientas faltantes --> WARN (no es fatal)
```

### Codigos de salida

| Codigo | Significado                                |
|--------|--------------------------------------------|
| 0      | Todos los grupos instalados correctamente  |
| 1      | Uno o mas grupos fallaron                  |

---

## check_tools.sh

### Proposito

Verificacion completa del entorno de desarrollo: Python, paquetes pip,
herramientas del sistema, conectividad a bases de datos, variables .env
y estructura del proyecto. Produce un resumen con conteo OK / WARN / ERROR.

Es el script de diagnostico principal. Ejecutarlo muestra el estado de TODO.

### Invocacion

```bash
# Directo (verifica con el Python del sistema):
bash scripts/provisioners/system/check_tools.sh

# Via redirect legacy (compatible con sesiones anteriores):
bash scripts/check_tools.sh

# Como Fase 6 del bootstrap (con venv activado):
sudo bash scripts/bootstrap.sh
```

> Cuando es invocado por bootstrap.sh, el venv esta en PATH
> para que los paquetes instalados en el entorno virtual sean visibles.

### Variables de configuracion

Lee `.env` si existe. Fallback a defaults de Vagrant:

```
DB_HOST        --> POSTGRES_HOST  (default: 192.168.56.11)
DB_PORT        --> POSTGRES_PORT  (default: 5432)
IVR_DB_HOST    --> MARIADB_HOST   (default: 192.168.56.10)
IVR_DB_PORT    --> MARIADB_PORT   (default: 3306)
```

### Verificaciones realizadas

```
check_tools.sh
     |
     |-- Python (requerido >= 3.11)
     |       python3 version
     |       pip disponible
     |       python3 -m venv disponible
     |
     |-- Paquetes Python (drivers y core)
     |       Criticos (ERROR si faltan): psycopg2, MySQLdb, django
     |       Resto    (WARN si faltan):
     |         djangorestframework, djangorestframework-simplejwt,
     |         django-filter, drf-spectacular, APScheduler, boto3,
     |         openpyxl, python-decouple, pytz, python-dateutil,
     |         PyJWT, sqlparse, tzlocal, PyYAML
     |
     |-- Herramientas de testing (WARN si faltan)
     |       pytest, pytest-django, pytest-cov,
     |       factory-boy, faker, coverage
     |
     |-- Herramientas dev opcionales (WARN si faltan)
     |       django-debug-toolbar, django-extensions, ipython
     |
     |-- Calidad de codigo (WARN si faltan)
     |       black, flake8, isort, mypy
     |
     |-- Herramientas del sistema
     |       Requeridas (ERROR): git, bash, curl
     |       Opcionales (WARN): mysqladmin, psql, pg_isready
     |       Red        (WARN): netstat, ss
     |
     |-- Conectividad TCP a bases de datos
     |       PostgreSQL ${POSTGRES_HOST}:${POSTGRES_PORT}  (timeout 3s)
     |       MariaDB    ${MARIADB_HOST}:${MARIADB_PORT}    (timeout 3s)
     |       Resultado: WARN si no alcanzable (no es ERROR)
     |
     |-- Variables en .env
     |       SECRET_KEY, DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD,
     |       IVR_DB_HOST, IVR_DB_PORT, IVR_DB_NAME, IVR_DB_USER, IVR_DB_PASSWORD
     |
     +-- Estructura del proyecto
             callcentersite/manage.py
             callcentersite/static/icons/{menu,submenu,defaults}/
```

### Resumen de salida

```
============================================================
OK:           57
Advertencias: 2
Errores:      0
------------------------------------------------------------
Entorno funcional con advertencias. Revisar items marcados.
```

### Codigos de salida

| Codigo | Condicion                      |
|--------|--------------------------------|
| 0      | Sin errores (puede haber WARN) |
| 1      | Uno o mas errores criticos     |

---

## Relacion con bootstrap.sh

```
sudo bash scripts/bootstrap.sh
          |
          | Fase 1  --> check_os.sh          (FATAL si falla)
          | Fase 2  --> install_packages.sh  (FATAL si falla)
          | Fase 3  --> Python inline
          | Fase 4  --> postgres/db_setup.sh + mariadb/db_setup.sh
          | Fase 5  --> apache/setup_apache.sh
          | Fase 6  --> check_tools.sh       (INFO, nunca FATAL)
```

Los tres scripts de `provisioners/system/` pueden ejecutarse
independientemente para diagnostico puntual:

```bash
# Solo verificar el SO:
bash scripts/provisioners/system/check_os.sh

# Solo instalar paquetes del sistema:
sudo bash scripts/provisioners/system/install_packages.sh

# Solo ver estado completo del entorno:
bash scripts/provisioners/system/check_tools.sh
```
