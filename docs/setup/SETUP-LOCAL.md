# Setup local — IACT-api

> **Las bases de datos NO son responsabilidad de este repositorio.**
> PostgreSQL (`iact_analytics`) y MariaDB (`ivr_legacy`) son
> instaladas, configuradas y gestionadas por **IACT-db**.
>
> Antes de continuar con este documento, el entorno de IACT-db
> debe estar en funcionamiento.
> Ver: `IACT-db/docs/getting-started/QUICKSTART.md`

Procedimiento para configurar IACT-api una vez que IACT-db
tiene los servicios corriendo en `127.0.0.1`.

## Arquitectura de bases de datos

IACT-api consume dos bases de datos con roles distintos:

| BD | Motor | Host | Puerto | BD name | Rol Django |
|---|---|---|---|---|---|
| Operacional | PostgreSQL 16 | 127.0.0.1 | 5432 | iact_analytics | `default` — lectura/escritura |
| Legacy IVR | MariaDB 10.11+ | 127.0.0.1 | 3306 | ivr_legacy | `ivr` — solo lectura (CNST-003) |

PostgreSQL es la base de datos principal. MariaDB es el origen de
datos IVR legado, accedido exclusivamente en modo lectura.

> Para instalar y configurar las BDs, ver el repo `IACT-db`.

---

## Prerrequisitos

- Python 3.11+
- PostgreSQL 16 corriendo en `127.0.0.1:5432` con `iact_analytics`
  y usuario `django_user` creados
- MariaDB 10.11+ corriendo en `127.0.0.1:3306` con `ivr_legacy`
  y usuario `django_user` creados
- `libmysqlclient21` instalada en el sistema (ver sección Instalación)
- Ambas BDs aprovisionadas con `IACT-db`

Verificar que ambos motores responden antes de continuar:

```bash
pg_isready -h 127.0.0.1 -p 5432
mysql -u django_user -pdjango_pass -e "SELECT 1;"
```

O usar el script de verificación incluido:

```bash
bash scripts/setup/start_services.sh
```

---

## Instalación de servicios (primera vez)

Los servicios de BD se instalan y configuran desde el repositorio `IACT-db`:

```bash
cd /ruta/a/IACT-db

# Copiar y ajustar configuración
cp .env.example .env

# Instalar PostgreSQL 16 + MariaDB 10.11 + crear usuarios y BDs
sudo bash bootstrap.sh --no-adminer
```

El bootstrap instala:
- PostgreSQL 16 con usuario `django_user` y BD `iact_analytics`
- MariaDB 10.11 con usuario `django_user` y BD `ivr_legacy`
- `libmysqlclient21` como dependencia de MariaDB

### libmysqlclient21

`mysqlclient==2.2.1` (cliente Python para MariaDB) requiere
`libmysqlclient.so.21` en el sistema. Esta librería es instalada
automáticamente por el bootstrap de IACT-db.

Si `libmysqlclient21` no está disponible (por ejemplo, en el sandbox
de desarrollo con red restringida), el import de `MySQLdb` falla
con `ImportError` y produce 426 errores en `tests/unit/` aunque
ningún test toque MariaDB.

Solución para entorno sin apt:

```bash
# Genera /usr/local/lib/libmysqlclient.so.21 como stub
sudo python3 scripts/setup/make_libmysqlclient_stub.py
```

El stub satisface al linker dinámico. No hace conexiones reales —
es solo para que Django arranque sin `ImportError`.

**Ver:** `docs/architecture/HALLAZGOS-ENTORNO-SANDBOX-2026-05-10.md` H-ENV-001

### Arranque en sesiones posteriores

PostgreSQL y MariaDB arrancan automáticamente con systemd. Si no:

```bash
# PostgreSQL
sudo pg_ctlcluster 16 main start

# MariaDB
sudo systemctl start mariadb

# Verificar ambos
bash scripts/setup/start_services.sh
```

---

## 1. Entorno virtual y dependencias

```bash
cd IACT-api/callcentersite

python3 -m venv venv
source venv/bin/activate

pip install -r ../requirements/development.txt
```

---

## 2. Variables de entorno

```bash
cp .env.example .env
```

Para entorno local con servicios en `127.0.0.1`, el `.env` debe tener:

```
DEBUG=True
SECRET_KEY=<clave-larga-y-aleatoria>
ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL — BD principal (lectura/escritura)
DB_NAME=iact_analytics
DB_USER=django_user
DB_PASSWORD=django_pass
DB_HOST=127.0.0.1
DB_PORT=5432

# MariaDB — BD legacy IVR (solo lectura — CNST-003)
IVR_DB_NAME=ivr_legacy
IVR_DB_USER=django_user
IVR_DB_PASSWORD=django_pass
IVR_DB_HOST=127.0.0.1
IVR_DB_PORT=3306
```

> No usar las IPs de Vagrant (`192.168.56.10`, `192.168.56.11`) en
> entorno local. Esas IPs son para el entorno con VMs.

---

## 3. Verificar conectividad Django

Antes de migrar, confirmar que Django alcanza ambas BDs:

```bash
# BD principal — PostgreSQL
python manage.py check --database default
# Esperado: System check identified no issues (0 silenced).

# BD legacy — MariaDB
python manage.py check --database ivr
# Esperado: System check identified no issues (0 silenced).
```

Si falla `--database default`, revisar `DB_HOST`, `DB_PORT` y que
el usuario `django_user` existe en PostgreSQL.

Si falla `--database ivr`, revisar `IVR_DB_HOST`, `IVR_DB_PORT` y
que el usuario existe en MariaDB.

---

## 4. Migraciones

```bash
# Migraciones en PostgreSQL (BD principal — todas las apps Django)
python manage.py migrate

# Verificar que no hay migraciones pendientes
python manage.py showmigrations --database default | grep '\[ \]'
# Esperado: (sin salida — 0 pendientes)
```

MariaDB (`ivr_legacy`) no recibe migraciones Django porque sus tablas
son gestionadas por el sistema IVR externo. Django accede a ellas con
`managed = False`.

---

## 5. Cargar datos iniciales

```bash
python manage.py loaddata apps/access/fixtures/modules.json
python manage.py loaddata apps/authentication/fixtures/security_questions.json
python manage.py loaddata apps/alerts/fixtures/alert_configurations.json
```

---

## 6. Crear superusuario

```bash
python manage.py createsuperuser
```

---

## 7. Iniciar el servidor de desarrollo

```bash
python manage.py runserver
# Disponible en: http://localhost:8000
# API schema: http://localhost:8000/api/schema/swagger/
```

---

## Checklist de verificación completa

```bash
# 1. Servicios de BD corriendo
pg_isready -h 127.0.0.1 -p 5432
mysqladmin -h 127.0.0.1 -u django_user -pdjango_pass ping

# 2. Django conecta a ambas BDs
python manage.py check --database default
python manage.py check --database ivr

# 3. Sin migraciones pendientes
python manage.py showmigrations --database default | grep '\[ \]'

# 4. Fixtures cargados (verificar módulos de acceso)
python manage.py shell -c \
  "from apps.access.models import Module; print(Module.objects.count(), 'módulos')"

# 5. API responde
curl -s http://localhost:8000/api/schema/ | head -5
```

---

## Troubleshooting

**`ImportError: libmysqlclient.so.21: cannot open shared object file`**

MySQLdb no puede cargar porque `libmysqlclient21` no está instalada.
Produce 426 errores en `tests/unit/` aunque ningún test toque MariaDB.

```bash
# Con apt disponible (entorno normal):
sudo apt-get install -y libmysqlclient21

# Sin apt (sandbox con red restringida):
python3 scripts/setup/make_libmysqlclient_stub.py
```

Verificar:
```bash
venv/bin/python -c "import MySQLdb; print('OK')"
```

**`django.db.utils.OperationalError: connection refused` en PostgreSQL**

```bash
pg_isready -h 127.0.0.1 -p 5432

# Si no responde:
sudo pg_ctlcluster 16 main start
```

**`django.db.utils.OperationalError: (2003, "Can't connect to MySQL server")` en MariaDB**

```bash
sudo systemctl start mariadb

# Verificar con socket:
mysql --socket=/run/mysqld/mysqld.sock -u django_user -pdjango_pass -e "SELECT 1;"
```

**`FATAL: role "django_user" does not exist`**

```bash
cd /ruta/a/IACT-db
sudo bash provisioners/postgres/setup.sh
```

**`Access denied for user 'django_user'@'...' (MariaDB)`**

```bash
cd /ruta/a/IACT-db
sudo bash provisioners/mariadb/setup.sh
```

## Ver también

- `IACT-db/docs/getting-started/QUICKSTART.md` — setup de BDs
- `IACT-db/docs/getting-started/VERIFICACION-LOCAL-SIN-VAGRANT.md` — checklist de BDs
- `IACT-db/docs/architecture/SEPARACION-IACT-API.md` — división de responsabilidades
- `callcentersite/config/settings/base.py` — configuración DATABASES
- `callcentersite/config/database_router.py` — router de BDs
