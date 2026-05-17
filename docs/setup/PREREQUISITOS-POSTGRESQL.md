# Prerequisitos de infraestructura — PostgreSQL

**Versión:** 1.0.0 | **Fecha:** 2026-05-10  
**Referencia:** `IACT-db/docs/architecture/HALLAZGOS-PROVISIONER-POSTGRES-2026-05-10.md`

---

## Contexto

IACT-api en producción se conecta a PostgreSQL via socket Unix (`DB_SOCKET`).
Este documento describe los requisitos que el entorno de infraestructura
debe cumplir antes de ejecutar `manage.py migrate` o levantar el servidor.

---

## Método de conexión por ambiente

| Ambiente | Variable activa | Mecanismo |
|---|---|---|
| Producción | `DB_SOCKET=/var/run/postgresql` | Socket Unix |
| Desarrollo | `DB_HOST=localhost` + `DB_PORT=5432` | TCP |
| Testing | `DB_HOST=127.0.0.1` + `DB_PORT=5432` | TCP |

`base.py` resuelve el mecanismo así:

```python
'HOST': config('DB_SOCKET', default='') or config('DB_HOST', default='localhost'),
'PORT': '' if config('DB_SOCKET', default='') else config('DB_PORT', default='5432'),
```

Si `DB_SOCKET` tiene valor, `HOST` toma el path del socket y `PORT` queda
vacío. `DB_HOST` y `DB_PORT` se ignoran.

---

## Prerequisito crítico: `pg_hba.conf`

### Por qué falla con la configuración por defecto

La instalación estándar de PostgreSQL en Ubuntu incluye:

```
local   all   all   peer
```

`peer` exige que el usuario del SO que ejecuta Django coincida con el rol
de base de datos. `django_user` no existe como usuario del SO — la conexión
via socket falla con:

```
django.db.utils.OperationalError: FATAL: Peer authentication failed for user "django_user"
```

### Regla requerida

`pg_hba.conf` debe contener la siguiente regla **antes** de la línea `peer` genérica:

```
local   all   django_user   scram-sha-256
local   all   all           peer
```

Ubicación del archivo: `/etc/postgresql/16/main/pg_hba.conf`

Después de editar, reiniciar el cluster:

```bash
pg_ctlcluster 16 main restart
# o
systemctl restart postgresql
```

### Verificación

```bash
# Conectar via socket Unix con credenciales django_user
psql -U django_user -d iact_analytics -c "SELECT current_user, current_database();"
```

Resultado esperado:

```
 current_user | current_database
--------------+------------------
 django_user  | iact_analytics
```

---

## Variables `.env` requeridas (producción)

```
DB_NAME=iact_analytics
DB_USER=django_user
DB_PASSWORD=django_pass
DB_SOCKET=/var/run/postgresql
```

`DB_HOST` y `DB_PORT` se ignoran cuando `DB_SOCKET` está definido.

---

## Base de datos y usuario esperados

El provisioner `IACT-db/provisioners/postgres/setup.sh` crea:

| Objeto | Valor |
|---|---|
| Base de datos | `iact_analytics` |
| Usuario | `django_user` |
| Privilegios | `ALL PRIVILEGES` + `CREATEDB` (para pytest) |
| Extensiones | `uuid-ossp`, `pg_trgm`, `hstore`, `citext` |

Si el entorno fue aprovisionado con `IACT-db`, estos objetos existen.
Si no, crearlos manualmente:

```sql
CREATE USER django_user WITH PASSWORD 'django_pass';
CREATE DATABASE iact_analytics OWNER django_user ENCODING 'UTF8';
GRANT ALL PRIVILEGES ON DATABASE iact_analytics TO django_user;
GRANT ALL ON SCHEMA public TO django_user;
ALTER ROLE django_user CREATEDB;
```

---

## Diagnóstico rápido

```bash
# 1. PostgreSQL responde
pg_isready -h 127.0.0.1 -p 5432

# 2. Conexión TCP funciona
PGPASSWORD=django_pass psql -h 127.0.0.1 -U django_user -d iact_analytics -c "SELECT 1;"

# 3. Conexión socket funciona (requisito para producción)
psql -U django_user -d iact_analytics -c "SELECT 1;"

# 4. Regla en pg_hba.conf presente
grep "django_user" /etc/postgresql/16/main/pg_hba.conf
```

Si el paso 2 pasa y el 3 falla, la causa es la regla faltante en `pg_hba.conf`.

---

## Ver también

- `docs/setup/CONFIGURACION-ENTORNOS.md` — jerarquía de settings y qué va en `.env`
- `IACT-db/docs/architecture/HALLAZGOS-PROVISIONER-POSTGRES-2026-05-10.md` — defectos del provisioner y correcciones
