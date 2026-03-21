# ANÁLISIS — Schema y Datos IVR en Provisioners MariaDB
## Deuda Técnica: call_logs para test_ivr_legacy

**Versión:** 1.0.0
**Fecha:** 2026-03-21
**Timestamp:** 20260321224221
**Origen:** Comentario en `config/settings/testing.py`:
```
# PENDIENTE (deuda técnica):
#   test_ivr_legacy requiere fixture que cree tabla call_logs via SQL
#   y factories para sembrar datos de prueba reales.
#   Hasta entonces los tests IVR usan mocks (database_mocks.py).
```

---

## 1. DIAGNÓSTICO — Estado actual del ecosistema IVR

### 1.1 BD `ivr_legacy` en producción

La BD de producción **solo tiene una tabla**:

```sql
SHOW TABLES FROM ivr_legacy;
→ schema_version   ← creada por db_setup.sh
-- NO existe: call_logs
```

La tabla `call_logs` **no existe en producción** actualmente. Es parte de la
arquitectura IVR legacy que aún no fue provisionada.

### 1.2 El modelo `CallLog` tiene `managed = False`

```python
# apps/ivr/models.py
class CallLog(models.Model):
    fecha              = DateField()
    telefono           = CharField(max_length=20)
    servicio_800       = CharField(max_length=20)
    total_llamadas     = IntegerField(default=0)
    llamadas_contestadas = IntegerField(default=0)
    llamadas_abandonadas = IntegerField(default=0)
    created_at         = DateTimeField()

    class Meta:
        managed = False          # Django NO gestiona el schema
        db_table = 'call_logs'   # Tabla existente en ivr_legacy
```

`managed = False` implica:
- Django **no crea** la tabla `call_logs`
- Django **no modifica** la tabla `call_logs`
- Django **no la destruye** en tests
- La tabla debe existir **por medios externos** (SQL directo)

### 1.3 Los tests `test_viewsets.py` usan `CallLog.objects.create()`

```python
# apps/ivr/tests/test_viewsets.py — setUp()
self.calllog1 = CallLog.objects.create(
    fecha=date(2025, 1, 15),
    telefono='912345678',
    ...
)
```

Esto **fallará** a menos que:
1. La tabla `call_logs` exista en `test_ivr_legacy`
2. `django_user` tenga `INSERT` en `test_ivr_legacy` (actualmente no tiene)

Con la configuración actual (`MIGRATE=False`), la tabla NO existe
en `test_ivr_legacy`. Estos tests están rotos por diseño incompleto.

### 1.4 Las `ivr_factories.py` importan modelos inexistentes

```python
# tests/factories/ivr_factories.py
from apps.ivr.models import (
    QuarterlyReport,   # NO EXISTE
    TransferReport,    # NO EXISTE
    AbandonedReport,   # NO EXISTE
    CallRecordQ1,      # NO EXISTE
    ...
)
```

El único modelo en `apps/ivr/models.py` es `CallLog`. Las factories
están basadas en un diseño anterior o futuro, no en el modelo actual.
Son **código muerto** que causa ImportError en colección.

### 1.5 El provisioner `db_setup.sh` no crea `call_logs`

```bash
# scripts/provisioners/mariadb/db_setup.sh — lo que hace:
check_prerequisites   # ✓
create_database       # crea ivr_legacy
create_user           # crea django_user
grant_privileges      # SELECT en ivr_legacy, CREATE+DROP en test_ivr_legacy
verify_connection     # verifica

# Lo que NO hace:
# ✗ CREATE TABLE call_logs   ← ausente
# ✗ INSERT datos de prueba   ← ausente
```

---

## 2. LA DECISIÓN DEL USUARIO ES CORRECTA

### "No se tiene que hacer por Python — es más relacionado con scripts/provisioners/mariadb"

**Argumento técnico:**

| Criterio | Python (factories/fixtures) | SQL Provisioner |
|---|---|---|
| Alineado con `managed=False` | ❌ Contradice el contrato | ✅ Es el mecanismo correcto |
| Responsabilidad del schema | ❌ Django no debe gestionarlo | ✅ Le corresponde al DBA/provisioner |
| Idempotencia | ❌ Factory boy puede crear duplicados | ✅ `CREATE TABLE IF NOT EXISTS` |
| Portabilidad | ❌ Acopla tests a la BD | ✅ Separación de concerns |
| Refleja producción | ❌ Schema inventado por Python | ✅ Misma DDL que producción |

**Principio:**
```
managed = False → "Esta tabla no es responsabilidad de Django"
                   → El schema vive en los provisioners
                   → Los datos de prueba viven en SQL seed scripts
                   → Python solo CONSUME (SELECT) → nunca define DDL
```

---

## 3. LO QUE SE NECESITA

Hay **dos niveles** de provisioning para IVR:

```
scripts/provisioners/mariadb/
  ├── db_setup.sh          ← Existe: crea BD + usuario + permisos
  ├── schema.sh            ← PENDIENTE: crea tabla call_logs (y futuras)
  └── seed_test_data.sh    ← PENDIENTE: inserta datos para test_ivr_legacy
```

### Nivel 1 — Schema (`schema.sh`)

Define la DDL de `call_logs` basada en el modelo `CallLog`:

```sql
-- DDL inferida de apps/ivr/models.py (CallLog)
CREATE TABLE IF NOT EXISTS `call_logs` (
    `id`                   INT(11) NOT NULL AUTO_INCREMENT,
    `fecha`                DATE        NOT NULL,
    `telefono`             VARCHAR(20) NOT NULL,
    `servicio_800`         VARCHAR(20) NOT NULL,
    `total_llamadas`       INT(11)     NOT NULL DEFAULT 0,
    `llamadas_contestadas` INT(11)     NOT NULL DEFAULT 0,
    `llamadas_abandonadas` INT(11)     NOT NULL DEFAULT 0,
    `created_at`           DATETIME(6) NOT NULL,
    PRIMARY KEY (`id`),
    INDEX `idx_fecha`        (`fecha`),
    INDEX `idx_servicio_800` (`servicio_800`),
    INDEX `idx_telefono`     (`telefono`)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;
```

**¿Dónde se aplica?**
- En `ivr_legacy` (producción) → `schema.sh` como parte del provisioning normal
- En `test_ivr_legacy` → El mismo script con la BD como parámetro

### Nivel 2 — Seed data de test (`seed_test_data.sh`)

Datos mínimos que permiten que `test_viewsets.py` funcione:

```sql
-- seed_test_data.sql
-- Datos de referencia para test_ivr_legacy.call_logs
INSERT INTO `call_logs`
    (fecha, telefono, servicio_800, total_llamadas, llamadas_contestadas, llamadas_abandonadas, created_at)
VALUES
    ('2025-01-15', '912345678', '800-123-4567', 100, 85, 15, NOW()),
    ('2025-01-16', '987654321', '800-987-6543',  50, 40, 10, NOW()),
    ('2025-01-17', '912345678', '800-123-4567', 200,180, 20, NOW()),
    ('2025-01-18', '000000000', '800-000-0000',   0,  0,  0, NOW());
```

---
## 4. IMPACTO EN LOS TESTS

### 4.1 Con el provisioner creando call_logs (objetivo)

```
test_ivr_legacy/
  call_logs   ← creada por schema.sh (DDL externa)
              ← populada por seed_test_data.sh
              ← MIGRATE=False → Django no la toca

test_viewsets.py → CallLog.objects.create() → funciona ✅
                   CallLog.objects.all()    → funciona ✅
                   CallLog.objects.filter() → funciona ✅
```

Para que `CallLog.objects.create()` funcione en tests, `django_user` necesita
`INSERT` en `test_ivr_legacy`. Ver sección 5.2 — Permisos.

### 4.2 Sin el provisioner (estado actual)

```
test_ivr_legacy/
  (vacía — MIGRATE=False no crea nada)

test_viewsets.py → CallLog.objects.create() → Table doesn't exist ❌
```

Los tests de `apps/ivr/tests/test_viewsets.py` actualmente no pasan.
Con mocks (`database_mocks.py`) tampoco porque el setUp usa el ORM directo.

### 4.3 `ivr_factories.py` — debe reescribirse o eliminarse

El archivo `tests/factories/ivr_factories.py` importa 11 modelos
que no existen en el código actual (`QuarterlyReport`, `TransferReport`, etc.).
Es una de las causas del ImportError B-02.

**Opciones:**
- **Eliminar**: `ivr_factories.py` es código muerto para el modelo actual
- **Reescribir**: una sola `CallLogFactory` basada en `CallLog` real

```python
# tests/factories/ivr_factories.py — versión correcta (solo CallLog)
class CallLogFactory(DjangoModelFactory):
    class Meta:
        model = CallLog
        database = 'ivr'   # apunta a test_ivr_legacy

    fecha              = factory.Faker('date_object')
    telefono           = factory.Sequence(lambda n: f'9{n:08d}')
    servicio_800       = factory.Iterator(['800-123-4567', '800-987-6543'])
    total_llamadas     = factory.Faker('pyint', min_value=0, max_value=500)
    llamadas_contestadas = factory.LazyAttribute(lambda o: int(o.total_llamadas * 0.85))
    llamadas_abandonadas = factory.LazyAttribute(lambda o: o.total_llamadas - o.llamadas_contestadas)
    created_at         = factory.Faker('date_time')
```

Sin embargo, si el seed SQL ya carga los datos necesarios para los tests,
la factory solo es útil para tests que necesiten variabilidad en los datos.

---

## 5. DISEÑO DE LA SOLUCIÓN PROVISIONER

### 5.1 Estructura de archivos propuesta

```
scripts/provisioners/mariadb/
  ├── db_setup.sh          ← Existe ✅ (crea BD, usuario, permisos básicos)
  ├── schema.sh            ← NUEVO: CREATE TABLE para ivr_legacy
  └── seed_test_data.sh    ← NUEVO: INSERT datos para test_ivr_legacy
```

### 5.2 Permisos adicionales para `test_ivr_legacy`

Para que los tests puedan operar en `test_ivr_legacy`, `django_user` necesita:

```sql
-- Permisos actuales en test_ivr_legacy:
GRANT CREATE, DROP ON test_ivr_legacy.*       ← existe

-- Permisos adicionales para tests:
GRANT INSERT, SELECT, UPDATE, DELETE ON test_ivr_legacy.*  ← AGREGAR en db_setup.sh
```

**¿Viola CNST-003?**
No. CNST-003 aplica a `ivr_legacy` (producción READ-ONLY).
`test_ivr_legacy` es la BD de tests — los datos son ficticios, se crean
y destruyen con cada run. Necesita escritura para los test setUp/tearDown.

**¿Por qué no se agregó antes?**
Porque con `MIGRATE=False` Django no intenta escribir en `test_ivr_legacy`.
Los tests que usan el ORM directamente (`test_viewsets.py`) aún fallan.
Cuando se habiliten esos tests, se necesitarán estos permisos.

### 5.3 `schema.sh` — CREATE TABLE idempotente

```bash
#!/bin/bash
# scripts/provisioners/mariadb/schema.sh
# Crea el schema de ivr_legacy (tablas legacy).
# IDEMPOTENTE: usa CREATE TABLE IF NOT EXISTS.
# Parámetro DB_NAME permite aplicar a ivr_legacy O test_ivr_legacy.

create_call_logs() {
    local db_name="${1:-ivr_legacy}"
    local sql="
    CREATE TABLE IF NOT EXISTS \`${db_name}\`.\`call_logs\` (
        \`id\`                   INT(11)     NOT NULL AUTO_INCREMENT,
        \`fecha\`                DATE        NOT NULL,
        \`telefono\`             VARCHAR(20) NOT NULL,
        \`servicio_800\`         VARCHAR(20) NOT NULL,
        \`total_llamadas\`       INT(11)     NOT NULL DEFAULT 0,
        \`llamadas_contestadas\` INT(11)     NOT NULL DEFAULT 0,
        \`llamadas_abandonadas\` INT(11)     NOT NULL DEFAULT 0,
        \`created_at\`           DATETIME(6) NOT NULL,
        PRIMARY KEY (\`id\`),
        INDEX \`idx_fecha\`        (\`fecha\`),
        INDEX \`idx_servicio_800\` (\`servicio_800\`),
        INDEX \`idx_telefono\`     (\`telefono\`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    "
    sudo mysql -e "${sql}"
}
```

### 5.4 `seed_test_data.sh` — INSERT idempotente

```bash
#!/bin/bash
# scripts/provisioners/mariadb/seed_test_data.sh
# Inserta datos mínimos en test_ivr_legacy para que los tests funcionen.
# IDEMPOTENTE: TRUNCATE + INSERT (datos fijos y conocidos).
# NO tocar ivr_legacy (producción).

seed_call_logs_test() {
    local sql="
    TRUNCATE TABLE test_ivr_legacy.call_logs;
    INSERT INTO test_ivr_legacy.call_logs
        (fecha, telefono, servicio_800, total_llamadas,
         llamadas_contestadas, llamadas_abandonadas, created_at)
    VALUES
        ('2025-01-15', '912345678', '800-123-4567', 100, 85, 15, NOW()),
        ('2025-01-16', '987654321', '800-987-6543',  50, 40, 10, NOW()),
        ('2025-01-17', '912345678', '800-123-4567', 200,180, 20, NOW()),
        ('2025-01-18', '000000000', '800-000-0000',   0,  0,  0, NOW());
    "
    sudo mysql -e "${sql}"
}
```

### 5.5 Integración con el flujo de tests

```
Antes de correr pytest (una sola vez por entorno):
  1. scripts/provisioners/mariadb/db_setup.sh    → BD + usuario + permisos
  2. scripts/provisioners/mariadb/schema.sh      → CREATE TABLE call_logs
  3. scripts/provisioners/mariadb/seed_test_data.sh → datos de prueba

Luego, pytest corre:
  → MIGRATE=False → Django no toca el schema
  → call_logs existe con datos conocidos
  → test_viewsets.py funciona directamente (sin mocks)
  → database_mocks.py queda para tests de servicios/ETL (no de ORM)
```

---

## 6. LO QUE NO CAMBIA

| Elemento | Estado | Motivo |
|---|---|---|
| `MIGRATE=False` en testing.py | Permanece | Correcto para managed=False |
| `SELECT ON ivr_legacy.*` | Permanece | CNST-003 producción READ-ONLY |
| `db_router.allow_migrate` | Permanece | Bug corregido en Tarea 0.0 |
| `database_mocks.py` | Permanece | Útil para tests de servicios/ETL |
| `test_viewsets.py` | Requiere ajuste | setUp debe usar datos del seed, no crear |

---

## 7. RELACIÓN CON EL PLAN v2.3.0

El comentario "PENDIENTE (deuda técnica)" en `testing.py` documenta algo
que **no es una tarea de Python** y por tanto no está en las Tareas 0.x.

La deuda técnica IVR se cierra con:

| Acción | Dónde | Prioridad |
|---|---|---|
| Crear `schema.sh` | `scripts/provisioners/mariadb/` | Media |
| Crear `seed_test_data.sh` | `scripts/provisioners/mariadb/` | Media |
| Ampliar permisos en `db_setup.sh` | INSERT,SELECT,UPDATE,DELETE en test_ivr_legacy | Media |
| Reescribir `ivr_factories.py` → solo `CallLogFactory` | `tests/factories/` | Alta (B-02) |
| Actualizar `test_viewsets.py` → usar datos del seed | `apps/ivr/tests/` | Media |
| Eliminar comentario "PENDIENTE" de `testing.py` | `config/settings/testing.py` | Baja |

El item de `ivr_factories.py` (reescribir → solo CallLogFactory) sí
entra como parte de la Tarea 0.2 del plan, ya que es un ImportError B-02.

---

## 8. RESUMEN EJECUTIVO

| Pregunta | Respuesta |
|---|---|
| ¿El comentario "PENDIENTE" era correcto? | Sí, identifica una deuda real |
| ¿Debe hacerse en Python? | **No** — `managed=False` implica gestión externa |
| ¿Dónde vive el schema? | `scripts/provisioners/mariadb/schema.sh` |
| ¿Dónde viven los datos de prueba? | `scripts/provisioners/mariadb/seed_test_data.sh` |
| ¿Qué pasa con `ivr_factories.py`? | Reescribir: solo `CallLogFactory` real |
| ¿Viola CNST-003? | No — aplica a `ivr_legacy`, no a `test_ivr_legacy` |
| ¿Afecta el plan v2.3.0? | Sí — agregar tareas en sección provisioners |

---

*Análisis generado: 2026-03-21T22:42:21*
*Autor: Claude Code — IACT-api*
*Basado en inspección de: db_setup.sh, models.py, test_viewsets.py,*
*ivr_factories.py, database_mocks.py*

