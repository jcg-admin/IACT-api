# ANÁLISIS — GRANT ALTER en test_ivr_legacy
## Tarea 0.0 del Plan v2.2.1

**Versión:** 1.0.0
**Fecha:** 2026-03-21
**Referencia:** `plan_implementacion_v2.2.1_20260321214437.md` → Tarea 0.0

---

## CONTEXTO

El plan v2.2.1 propone como Tarea 0.0 ejecutar:

```sql
DROP DATABASE IF EXISTS test_ivr_legacy;
GRANT ALTER ON `test_ivr_legacy`.* TO 'django_user'@'localhost';
FLUSH PRIVILEGES;
```

Este documento analiza en profundidad **por qué se produce el error**,
**qué se necesita exactamente** y **si la solución propuesta es la correcta**.

---

## 1. ESTADO ACTUAL VERIFICADO

### 1.1 Permisos de `django_user` en MariaDB 10.11

```sql
GRANT USAGE ON *.*                    -- conexión básica
GRANT SELECT ON ivr_legacy.*          -- lectura en producción (CNST-003)
GRANT CREATE, DROP ON test_ivr_legacy.*  -- crear/borrar tablas en test DB
-- FALTA: ALTER ON test_ivr_legacy.*
```

### 1.2 Estado de `test_ivr_legacy`

La base de datos **existe** (stale de una ejecución anterior):

```
Tables_in_test_ivr_legacy
  django_content_type    ← 0 registros
  django_migrations      ← 0 registros
```

Esquema de `django_content_type` en `test_ivr_legacy`:
```sql
CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,      ← campo ANTIGUO (Django < 1.8)
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`)
)
```

**Observación crítica:** La tabla tiene el esquema de Django < 1.8 (incluye el
campo `name` que fue eliminado en Django 1.8). El proyecto usa Django 5.0.1.
Esto confirma que la BD quedó de una ejecución muy antigua y está corrupta
para el propósito actual.

### 1.3 Modelo IVR — `CallLog`

```python
# apps/ivr/models.py
class CallLog(models.Model):
    class Meta:
        managed = False       # NO genera migrations
        db_table = 'call_logs'
```

**`managed = False`** significa que Django NO intenta crear, modificar
ni eliminar esta tabla. El test runner tampoco lo hace.

### 1.4 Router — `allow_migrate` con bug

```python
# config/db_router.py
def allow_migrate(self, db, app_label, model_name=None, **hints):
    if app_label in self.ivr_apps:       # {'ivr'}
        return db == 'ivr'
    if app_label in self.default_apps:   # {'core', 'auth', 'users', ...}
        return db == 'default'
    return None                           # ← BUG: None para contenttypes, sessions, etc.
```

Cuando `allow_migrate` retorna `None`, Django interpreta: **"no tengo
preferencia, corre la migration en esta DB"**. Esto hace que Django
ejecute migrations de `contenttypes`, `sessions` y otras apps del
framework sobre `test_ivr_legacy`.

---

## 2. ANATOMÍA DEL ERROR

### 2.1 Secuencia de eventos al correr pytest

```
1. pytest inicia
2. Django intenta crear test_ivr_legacy
   → FALLA: "Can't create database 'test_ivr_legacy'; database exists"
   (stale de ejecución anterior)

3. Django detecta BD existente, intenta usarla
4. Django corre migrations de contenttypes en test_ivr_legacy
   → migration 0002: ALTER TABLE django_content_type DROP COLUMN name
   → ERROR: ALTER command denied to django_user@localhost
```

### 2.2 El error exacto

```
MySQLdb.OperationalError: (1142,
  "ALTER command denied to user 'django_user'@'localhost'
   for table 'test_ivr_legacy'.'django_content_type'")
```

### 2.3 ¿Por qué necesita ALTER?

La migration `contenttypes/0002_remove_content_type_name` ejecuta:

```sql
ALTER TABLE django_content_type DROP COLUMN name;
ALTER TABLE django_content_type ADD CONSTRAINT ...;
```

Esta es la migración que elimina el campo `name` obsoleto (Django < 1.8).
Como la tabla stale tiene el esquema antiguo, Django intenta aplicar esta
migration — y necesita `ALTER TABLE`.

---

## 3. OPCIONES DE SOLUCIÓN

### Comparativa

| # | Solución | Cambio requerido | Riesgo | Permanencia |
|---|---|---|---|---|
| A | GRANT ALTER en test_ivr_legacy | SQL en MariaDB (root) | Bajo | Permanente |
| B | Corregir `allow_migrate` en el router | Código Python | Bajo | Permanente + elimina causa raíz |
| C | `TEST: NAME: None` en settings/testing.py | Python settings | Muy bajo | Permanente |
| D | GRANT ALTER + corregir router | SQL + Python | Bajo | Óptimo |

---

### Opción A — GRANT ALTER (plan v2.2.1 original)

```sql
-- Ejecutar como root en MariaDB
DROP DATABASE IF EXISTS test_ivr_legacy;
GRANT ALTER ON `test_ivr_legacy`.* TO 'django_user'@'localhost';
FLUSH PRIVILEGES;
```

**¿Qué resuelve?**
- Permite a Django ejecutar `ALTER TABLE` al aplicar migrations en `test_ivr_legacy`
- Elimina el error 1142

**¿Qué NO resuelve?**
- No elimina la causa raíz: el router sigue enviando migrations de
  `contenttypes` y otras apps del framework a la BD IVR
- En cada run de tests, Django sigue corriendo migrations innecesarias
  en `test_ivr_legacy` (django_content_type, django_migrations, etc.)
- Si la BD vuelve a quedar stale, el error reaparecerá

**¿Viola CNST-003?**
No. CNST-003 aplica a `ivr_legacy` (producción). `test_ivr_legacy` es
exclusiva del entorno de test.

---

### Opción B — Corregir `allow_migrate` en el router (CAUSA RAÍZ)

```python
# config/db_router.py — allow_migrate corregido
def allow_migrate(self, db, app_label, model_name=None, **hints):
    if app_label in self.ivr_apps:
        return db == 'ivr'
    # ANTES: return None  ← BUG — causaba migrations en IVR
    # AHORA: todo lo demás solo migra en default
    return db == 'default'
```

**¿Qué resuelve?**
- Django deja de ejecutar migrations de `contenttypes`, `sessions`, `auth`,
  etc. sobre `test_ivr_legacy`
- Como `CallLog` tiene `managed=False`, NO hay nada que migrar en IVR
- El test runner no necesita `ALTER` porque ya no intenta modificar tablas
- Elimina la causa raíz del problema

**¿Qué NO resuelve?**
- La BD stale `test_ivr_legacy` sigue existiendo (hay que limpiarla aparte)
- Django todavía CREA `test_ivr_legacy` al inicio del run (necesita
  `CREATE DATABASE`, no cubierto por `CREATE ON test_ivr_legacy.*`)

**Impacto adicional:**
- Tests de `default` que actualmente pasan en `ivr` dejarían de hacerlo
  (impacto mínimo — era un error de configuración, no funcionalidad)

---

### Opción C — TEST: NAME: None en settings/testing.py

```python
# config/settings/testing.py
DATABASES['ivr']['TEST'] = {'NAME': None}
```

**¿Qué resuelve?**
- Django NO crea ni destruye `test_ivr_legacy`
- No necesita ningún privilegio en MariaDB para tests
- Tests IVR usan mocks (ya definidos en `tests/mocks/database_mocks.py`)
- Solución mínima, sin cambios en BD

**¿Qué NO resuelve?**
- Tests que necesiten datos reales de IVR no podrán usar BD de test
  (deben usar mocks — comportamiento correcto para READ-ONLY)
- La BD stale `test_ivr_legacy` sigue existiendo (no interfiere pero
  es ruido)

**¿Viola CNST-003?**
No. Refuerza el principio: si IVR es READ-ONLY, no necesita BD de test
con datos mutables.

---

### Opción D — Corregir router + limpiar stale (RECOMENDADA)

Combina la corrección de causa raíz con limpieza:

```bash
# 1. Limpiar BD stale
mysql -u root -e "DROP DATABASE IF EXISTS test_ivr_legacy;"
```

```python
# 2. Corregir router
def allow_migrate(self, db, app_label, model_name=None, **hints):
    if app_label in self.ivr_apps:
        return db == 'ivr'
    return db == 'default'   # antes retornaba None para sys apps
```

```python
# 3. Evitar creación de BD de test IVR vacía
# config/settings/testing.py
DATABASES['ivr']['TEST'] = {'NAME': None}
```

**¿Por qué es la mejor?**
- Elimina la causa raíz (router devolvía `None`)
- Elimina la BD stale
- No requiere privilegios adicionales en MariaDB
- Alinea el comportamiento con el diseño: IVR es READ-ONLY, sin BD de test
- Los tests de IVR ya tienen mocks preparados en `database_mocks.py`

---

## 4. DECISIÓN REVISADA

### El plan v2.2.1 propuso la Opción A. Tras el análisis completo:

| Criterio | Opción A (GRANT ALTER) | Opción D (Router + None) |
|---|---|---|
| Elimina el error 1142 | ✅ | ✅ |
| Elimina la causa raíz | ❌ (parcha síntoma) | ✅ |
| Requiere acceso root MariaDB | ✅ (una vez) | ❌ (no requiere) |
| Cambios en código | ❌ | ✅ (2 archivos) |
| Migrations innecesarias en IVR | Siguen ocurriendo | Eliminadas |
| Riesgo de BD stale futura | Reaparece | No aplica |
| Alineado con CNST-003 | ✅ | ✅ (mejor alineado) |

### DECISIÓN FINAL: Opción D

**Motivo:** La Opción A resuelve el síntoma. La Opción D elimina la causa
raíz y es más robusta. El cambio en el router (`return None` → `return db == 'default'`)
es una corrección de bug, no un feature. Agregar `TEST: NAME: None` alinea
el entorno de test con el contrato de producción (IVR es READ-ONLY).

---

## 5. PLAN DE IMPLEMENTACIÓN

### Prerequisito — Limpiar BD stale

```bash
mysql -u root -e "DROP DATABASE IF EXISTS test_ivr_legacy;"
```

**Verificación:**
```bash
mysql -u root -e "SHOW DATABASES LIKE 'test_%';"
# No debe aparecer test_ivr_legacy
```

---

### Paso 1 — Corregir `config/db_router.py`

**Archivo:** `callcentersite/config/db_router.py`

**Cambio en `allow_migrate`:**

```python
# ANTES (bug):
def allow_migrate(self, db, app_label, model_name=None, **hints):
    if app_label in self.ivr_apps:
        return db == 'ivr'
    if app_label in self.default_apps:
        return db == 'default'
    return None   # ← BUG: contenttypes, sessions, auth → migrations en IVR

# DESPUÉS (corrección):
def allow_migrate(self, db, app_label, model_name=None, **hints):
    if app_label in self.ivr_apps:
        return db == 'ivr'
    return db == 'default'   # todo lo demás solo migra en default
```

**Impacto en tests del router:**
Los tests existentes en `db_router.py` deben actualizarse:

```python
def test_router_migrations_readonly():
    router = DatabaseRouter()
    # IVR app: solo en ivr
    assert router.allow_migrate('default', 'ivr') is False
    assert router.allow_migrate('ivr', 'ivr') is True
    # Contenttypes: solo en default (no None)
    assert router.allow_migrate('default', 'contenttypes') is True
    assert router.allow_migrate('ivr', 'contenttypes') is False  # antes era None
```

---

### Paso 2 — Actualizar `config/settings/testing.py`

**Agregar al bloque DATABASES:**

```python
# config/settings/testing.py — bloque DATABASES
DATABASES['default']['TEST'] = {'NAME': 'test_iact_analytics'}
DATABASES['ivr']['TEST'] = {'NAME': None}   # ← AGREGAR: no crear test DB para IVR
```

**Comentario a agregar:**
```python
# ivr TEST NAME=None: IVR es READ-ONLY (CNST-003), no necesita BD de test.
# Tests de IVR usan mocks (tests/mocks/database_mocks.py).
```

---

### Paso 3 — Verificar resultado

```bash
cd /home/user/IACT-api/callcentersite
source ../venv/bin/activate

# Verificar que no hay errores de BD en test run
python -m pytest tests/ --continue-on-collection-errors -q --tb=line 2>&1 | \
  grep -E "OperationalError|ALTER|ivr_legacy|344|errors"

# Objetivo: ninguna línea con OperationalError relacionada a IVR
```

**Criterio de aceptación:**
```
pytest tests/ --continue-on-collection-errors
→ Antes: 119 passed / 59 failed / 344 errors
→ Después: 119 passed / 59 failed / 0 errors de BD
          (los 59 failures son bugs de lógica — Tareas 0.4-0.6)
```

---

## 6. ARCHIVOS A MODIFICAR

| Archivo | Tipo de cambio | Líneas aprox. |
|---|---|---|
| `callcentersite/config/db_router.py` | Bug fix en `allow_migrate` | 1 línea eliminada |
| `callcentersite/config/settings/testing.py` | Agregar `TEST: NAME: None` | 1 línea |

---

## 7. RELACIÓN CON CNST-003

```
CNST-003: IVR Legacy Database — READ-ONLY
  ├── Producción: django_user solo tiene SELECT en ivr_legacy  ✅
  ├── Router: db_for_write retorna None para app ivr           ✅
  └── Tests: IVR no tiene BD de test (NAME=None)              ✅ (tras este cambio)

Resultado: CNST-003 completamente alineado en los 3 niveles.
```

---

## 8. ACTUALIZACIÓN AL PLAN v2.2.1

La Tarea 0.0 original en el plan v2.2.1 debe reemplazarse:

**ANTES (Tarea 0.0 en plan v2.2.1):**
```sql
DROP DATABASE IF EXISTS test_ivr_legacy;
GRANT ALTER ON test_ivr_legacy.* TO 'django_user'@'localhost';
FLUSH PRIVILEGES;
```

**DESPUÉS (Tarea 0.0 revisada):**
```bash
# 1. Limpiar BD stale (una vez)
mysql -u root -e "DROP DATABASE IF EXISTS test_ivr_legacy;"

# 2. Corregir router: allow_migrate devuelve db=='default' en vez de None
# config/db_router.py — ver Paso 1

# 3. Agregar TEST NAME=None para IVR
# config/settings/testing.py — ver Paso 2
```

---

*Análisis generado: 2026-03-21*
*Autor: Claude Code — IACT-api*
*Reemplaza la decisión de Opción A del plan v2.2.1 por Opción D*

