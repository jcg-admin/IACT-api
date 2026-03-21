# ARRANQUE Y VALIDACIÓN DE BASES DE DATOS — IACT API
## Entorno sin systemd (contenedor)

**Versión:** 1.0.0
**Fecha:** 2026-03-21
**Autor:** Claude Code — Análisis automatizado

---

## CONTEXTO

El entorno IACT-api corre en un **contenedor sin systemd** como init system (PID 1).
Esto significa que `systemctl start postgresql` / `systemctl start mariadb` **no funcionan**.
Los servicios deben arrancarse directamente con sus binarios.

---

## ARQUITECTURA DE BASES DE DATOS

| BD real | Alias Django | Motor | Host | Puerto | Modo |
|---|---|---|---|---|---|
| `iact_analytics` | `default` | PostgreSQL 16 | 127.0.0.1 | 5432 | READ + WRITE |
| `ivr_legacy` | `ivr` | MariaDB 10.11 | 127.0.0.1 | 3306 | READ-ONLY (CNST-003) |

Credenciales en `.env` (raíz del proyecto):
```
DB_USER=django_user         DB_PASSWORD=django_pass
IVR_DB_USER=django_user     IVR_DB_PASSWORD=django_pass
DB_ROOT_PASSWORD=root_pass_CHANGE_ME
```

---

## ESTADO TÍPICO AL INICIAR EL ENTORNO

Cuando el contenedor arranca (o reinicia), las bases de datos quedan **detenidas** pero
dejan archivos PID y socket **stale** de la sesión anterior:

```
/var/run/postgresql/16-main.pid        ← PID stale de PostgreSQL
/var/run/postgresql/.s.PGSQL.5432      ← socket stale
/var/run/mysqld/mysqld.pid             ← PID stale de MariaDB
/var/run/mysqld/mysqld.sock            ← socket stale
```

`pg_lsclusters` reporta `down` aunque los archivos existan.
Conectar por TCP (127.0.0.1) falla con `Connection refused`.
Conectar por socket Unix falla con `Connection refused` (socket stale, no hay proceso).

---

## CÓMO ARRANCAR LAS BASES DE DATOS

### PostgreSQL

```bash
pg_ctlcluster 16 main start
```

- Si el cluster ya estaba corriendo devuelve: `Cluster is already running.`
- Si había archivos stale los limpia automáticamente: `Removed stale pid file.`
- Verificar estado:

```bash
pg_lsclusters
# Ver  Cluster  Port  Status  Owner     Data directory
# 16   main     5432  online  postgres  /var/lib/postgresql/16/main
```

### MariaDB

```bash
# 1. Limpiar archivos stale si existen
rm -f /var/run/mysqld/mysqld.sock /var/run/mysqld/mysqld.pid

# 2. Arrancar en background
mysqld_safe --user=mysql &

# 3. Esperar ~4 segundos hasta que levante
sleep 4
```

---

## VALIDAR CONEXIONES

### Validación rápida desde terminal

```bash
# PostgreSQL
PGPASSWORD=django_pass psql -U django_user -d iact_analytics -h 127.0.0.1 -p 5432 \
  -c "SELECT current_database(), version();"

# MariaDB
mysql -h 127.0.0.1 -P 3306 -u django_user -pdjango_pass \
  -e "SELECT current_user(), version();"
```

### Validación desde Django

```bash
cd /home/user/IACT-api/callcentersite
source ../venv/bin/activate

python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()
from django.db import connections

for alias in ['default', 'ivr']:
    try:
        conn = connections[alias]
        conn.ensure_connection()
        with conn.cursor() as cur:
            cur.execute('SELECT 1')
        print(f'[OK] {alias}: {conn.vendor} — {conn.settings_dict[\"NAME\"]}')
    except Exception as e:
        print(f'[FAIL] {alias}: {e}')
"
```

Salida esperada:
```
[OK] default: postgresql — iact_analytics
[OK] ivr:     mysql      — ivr_legacy
```

### Validar migraciones

```bash
python manage.py showmigrations --settings=config.settings.development
# Todos los módulos deben tener [X] en todas sus migraciones
```

---

## SECUENCIA COMPLETA DE ARRANQUE (copiar y pegar)

```bash
# 1. Arrancar PostgreSQL
pg_ctlcluster 16 main start

# 2. Arrancar MariaDB
rm -f /var/run/mysqld/mysqld.sock /var/run/mysqld/mysqld.pid
mysqld_safe --user=mysql &
sleep 4

# 3. Activar venv
cd /home/user/IACT-api/callcentersite
source ../venv/bin/activate

# 4. Validar desde Django
python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()
from django.db import connections
for alias in ['default', 'ivr']:
    try:
        connections[alias].ensure_connection()
        print(f'[OK] {alias}')
    except Exception as e:
        print(f'[FAIL] {alias}: {e}')
"
```

---

## POR QUÉ NO FUNCIONA `systemctl`

El entorno corre en contenedor. El proceso PID 1 **no es systemd**, por lo que:

```bash
systemctl start postgresql   # → Failed to connect to bus: Host is down
systemctl start mariadb      # → System has not been booted with systemd as init system
```

No es un error del proyecto — es la naturaleza del entorno de ejecución.
El script `bootstrap.sh` del proyecto usa `systemctl` (diseñado para VM/bare-metal con Ubuntu 24.04),
pero en este contenedor los servicios se arrancan directamente.

---

## SCRIPTS DEL PROYECTO (para VM/bare-metal)

Para entornos con systemd completo (VM, servidor físico), el proyecto incluye:

| Script | Propósito |
|---|---|
| `scripts/bootstrap.sh` | Entry point único — instala y configura todo |
| `scripts/provisioners/postgres/install.sh` | Instala PostgreSQL 16 |
| `scripts/provisioners/postgres/db_setup.sh` | Crea BD `iact_analytics` y usuario |
| `scripts/provisioners/mariadb/install.sh` | Instala MariaDB 11.4 |
| `scripts/provisioners/mariadb/db_setup.sh` | Crea BD `ivr_legacy` (read-only) |
| `scripts/run_db.sh` | Menú interactivo para migraciones Django |

En esos entornos el arranque se hace con:
```bash
sudo bash scripts/bootstrap.sh
```

---

## ROUTER DE BASES DE DATOS

Django sabe a qué BD enviar cada query mediante `config/db_router.py`:

```python
class DatabaseRouter:
    ivr_apps = {'ivr'}   # app_label de apps.ivr → MariaDB (solo lectura)

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.ivr_apps:
            return 'ivr'      # MariaDB
        return None           # todo lo demás → 'default' (PostgreSQL)

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.ivr_apps:
            return None       # CNST-003: bloquea writes en IVR
        return None
```

Configurado en `config/settings/base.py`:
```python
DATABASE_ROUTERS = ['config.db_router.DatabaseRouter']
```

---

*Documento generado por Claude Code — IACT-api*
*Versión: 1.0.0 | Fecha: 2026-03-21 | Timestamp: 210326045508*
