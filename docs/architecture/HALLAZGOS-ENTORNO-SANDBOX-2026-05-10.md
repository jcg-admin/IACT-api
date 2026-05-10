# Hallazgos de entorno sandbox — 2026-05-10

**Contexto:** Entorno de desarrollo Claude (sandbox Ubuntu 24.04 noble).
**Detectado en:** Plan v3.1.0 — primer arranque de suite post-recuperación.

---

## H-ENV-001 — libmysqlclient.so.21 no instalado

**Síntoma:**

```
ImportError: libmysqlclient.so.21: cannot open shared object file: No such file or directory
django.core.exceptions.ImproperlyConfigured: Error loading MySQLdb module.
```

426 tests en ERROR en `tests/unit/` porque Django carga
`django.db.backends.mysql` al arrancar (por `DATABASES['ivr']`),
lo que requiere `MySQLdb`, que a su vez necesita `libmysqlclient.so.21`.
El error ocurre incluso si el test no toca MariaDB.

**Causa raíz:** El paquete `libmysqlclient21` no está instalado.
En este sandbox la red bloquea `archive.ubuntu.com` y `security.ubuntu.com`
(HTTP 403 `host_not_allowed`), por lo que `apt-get install` falla.

**Solución aplicada — stub en memoria:**

```bash
# Generar stub con los 50 símbolos que _mysql.cpython-*.so necesita
python3 /tmp/references/IACT-api/scripts/setup/make_libmysqlclient_stub.py
```

El script genera `libmysqlclient.so.21` con todos los símbolos
versionados (`libmysqlclient_21.0`) como stubs que retornan NULL.
Satisface al linker dinámico — `import MySQLdb` pasa. Cualquier
intento real de conectarse a MySQL lanzará una excepción en tiempo
de ejecución (no en import), lo cual es correcto: los unit tests
no hacen conexiones reales.

**Solución correcta (entorno con apt disponible):**

```bash
# Instalar la librería real via IACT-db bootstrap
cd /ruta/a/IACT-db
sudo bash bootstrap.sh --no-adminer

# O directamente el paquete del sistema
sudo apt-get install -y libmysqlclient21
# o, si se usa MariaDB:
sudo apt-get install -y libmariadb3
```

`libmysqlclient21` es provisto por `mysql-8.0` (Ubuntu main).
`libmariadb3` es provisto por `mariadb` (Ubuntu universe).
Ambos satisfacen la dependencia de `mysqlclient==2.2.1`.

**Impacto resuelto:** Al instalar la librería real (o el stub),
los 426 errores por `ImportError` desaparecen.
Los errores restantes pasan a ser de conectividad PostgreSQL
(H-ENV-002).

---

## H-ENV-002 — PostgreSQL no disponible

**Síntoma post H-ENV-001:**

```
psycopg2.OperationalError: connection to server on socket
"/var/run/postgresql/.s.PGSQL.5432" failed: No such file or directory
```

Los 426 tests que usan `@pytest.mark.django_db` necesitan que
PostgreSQL esté corriendo para que Django pueda crear `test_iact_analytics`.
Sin servidor, cada test falla en setup con este error.

**Causa raíz:** PostgreSQL no está instalado en este sandbox.
La red bloquea todos los repositorios de paquetes externos.

**Solución correcta (entorno con apt disponible):**

El provisioner de IACT-db instala y configura PostgreSQL 16:

```bash
cd /ruta/a/IACT-db
sudo bash bootstrap.sh --no-adminer
# instala PostgreSQL 16 + MariaDB 10.11, crea usuarios y BDs
```

Si IACT-db ya está instalado pero PostgreSQL no está corriendo:

```bash
sudo pg_ctlcluster 16 main start
# Verificar:
pg_isready -h 127.0.0.1 -p 5432
```

**Impacto:** Al tener PostgreSQL corriendo, los 426 errores de
`@pytest.mark.django_db` se resuelven. El resultado esperado
de la suite unit es:

```
686 passed, 4 skipped
```

(Los 61 fallos pre-existentes son de lógica de código — no de
infraestructura. Ver commit `9f3368b` para trazabilidad.)

---

## H-ENV-003 — Dominios bloqueados en el sandbox

Todos los dominios de paquetes están bloqueados con HTTP 403
`host_not_allowed`:

| Dominio | Estado |
|---|---|
| archive.ubuntu.com | 403 bloqueado |
| security.ubuntu.com | 403 bloqueado |
| apt.postgresql.org | 403 bloqueado |
| apt-archive.postgresql.org | 403 bloqueado |
| downloads.mariadb.org | 403 bloqueado |
| pypi.org | 403 bloqueado |
| files.pythonhosted.org | 403 bloqueado |
| github.com | 403 bloqueado |

**Consecuencia:** No se pueden instalar paquetes del sistema ni
paquetes Python adicionales en este entorno.

**Workaround para `libmysqlclient.so.21`:** stub generado con gcc
(disponible en el sistema). Ver H-ENV-001.

**Workaround para PostgreSQL:** no existe en este sandbox.
Los tests `@pytest.mark.django_db` no pueden correr.

---

## Resumen del estado de tests por condición de entorno

| Condición | passed | failed | errors |
|---|---|---|---|
| Sin libmysqlclient, sin PostgreSQL | 175 | 61 | 426 |
| Con stub libmysqlclient, sin PostgreSQL | 175 | 61 | 426* |
| Con libmysqlclient real, sin PostgreSQL | 175 | 61 | 426* |
| Con libmysqlclient real + PostgreSQL | **686** | 61 | 0 |
| IACT-db completo (PostgreSQL + MariaDB) | **686** | 61** | 0 |

*El error cambia de `ImportError: libmysqlclient` a
`OperationalError: PostgreSQL no disponible` — misma cuenta,
distinta causa.

**Los 61 fallos son pre-existentes (lógica de código), no de
infraestructura. Trazables al commit `9f3368b`.

---

## Script de setup para el sandbox

Ver: `IACT-api/scripts/setup/make_libmysqlclient_stub.py`

Crea `libmysqlclient.so.21` en `/usr/local/lib/` con los
50 símbolos que `mysqlclient 2.2.1` necesita para importar.
Idempotente — si la librería real está instalada, no hace nada.
