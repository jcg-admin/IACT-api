# ANÁLISIS DE VERIFICACIÓN — Tarea 0.0 Opción D
## Validación del impacto real en los 344 errores

**Versión:** 1.0.0
**Fecha:** 2026-03-21
**Timestamp:** 20260321223205
**Referencia plan:** `plan_implementacion_v2.3.0_20260321221530.md` → Tarea 0.0
**Referencia análisis:** `ANALISIS_GRANT_ALTER_IVR_v1.0.0_210326.md`

---

## OBJETIVO

Verificar, mediante ejecución real de pytest, si los cambios propuestos en la
Tarea 0.0 (Opción D) del plan v2.3.0 efectivamente eliminan o reducen los
344 errores de setup de BD.

---

## 1. BASELINE — Estado previo a cualquier cambio

### Ejecución:
```bash
pytest tests/ --continue-on-collection-errors -q --tb=no
```

### Resultado:
```
59 failed, 119 passed, 344 errors in 5.52s
```

### Clasificación de los 344 errors:
| Tipo | Cantidad |
|---|---|
| Errores de colección (ImportError — B-02) | 20 archivos |
| Errores en tests específicos (setup de BD) | 324 tests |
| **TOTAL** | **344** |

### Error dominante (324 errors):
```
MySQLdb.OperationalError: (1142,
  "ALTER command denied to user 'django_user'@'localhost'
   for table 'test_ivr_legacy'.'django_content_type'")
```

---

## 2. DESCUBRIMIENTO — DURANTE IMPLEMENTACIÓN

### 2.1 `TEST: NAME: None` no hace lo esperado

La Tarea 0.0 del plan v2.3.0 especificaba:
```python
DATABASES['ivr']['TEST'] = {'NAME': None}
```

Tras implementar y verificar con `get_unique_databases_and_mirrors()`:

```python
TEST DATABASES:
  ('127.0.0.1', '5432', ..., 'test_iact_analytics'): ('iact_analytics', ['default'])
  ('127.0.0.1', '3306', ..., 'test_ivr_legacy'): ('ivr_legacy', ['ivr'])
```

**Hallazgo:** `NAME: None` en Django no omite la creación de la BD de test.
Simplemente usa el nombre por defecto (`test_` + nombre original =
`test_ivr_legacy`). El comportamiento es idéntico a no especificar `NAME`.

**Causa:** `get_test_db_name()` en Django evalúa `if TEST['NAME']:` — `None`
es falsy, por lo que cae al default (`test_` + `NAME`).

### 2.2 Corrección: `MIGRATE: False`

La opción correcta de Django para no ejecutar migrations en una BD de test es:
```python
DATABASES['ivr']['TEST'] = {'NAME': 'test_ivr_legacy', 'MIGRATE': False}
```

Con `MIGRATE: False`:
- Django crea la BD vacía (usa `CREATE` privilege ✅)
- Django NO ejecuta migrations
- Django NO crea `django_migrations` table
- Django NO hace INSERT (no necesita ese permiso)
- Modelos `managed=False` → no se crean tablas → BD queda vacía ✅

---

## 3. IMPLEMENTACIÓN REAL EJECUTADA

### Paso 1 — DROP stale (prerequisito):
```bash
mysql -u root -e "DROP DATABASE IF EXISTS test_ivr_legacy;"
```
**Resultado:** BD eliminada ✅

### Paso 2 — Corrección `allow_migrate` en `config/db_router.py`:

```python
# ANTES (bug):
        # Default apps: migrations solo en default
        if app_label in self.default_apps:
            return db == 'default'
        return None   # ← contenttypes, auth, sessions → migran en IVR

# DESPUÉS (fix):
        # Default apps y framework apps (contenttypes, auth, sessions, etc.):
        # migrations solo en default. ANTES retornaba None, causando que
        # Django corriera migrations en ivr (BUG B-20).
        return db == 'default'
```

**Cambio:** 5 líneas → 3 líneas. Elimina el `if self.default_apps` redundante
(ya cubierto por el `return db == 'default'` final).

### Paso 3 — Actualizar `config/settings/testing.py`:

```python
# ANTES:
DATABASES['ivr']['TEST'] = {'NAME': 'test_ivr_legacy'}

# DESPUÉS:
# ivr MIGRATE=False: IVR es READ-ONLY (CNST-003). Modelos managed=False,
# no hay tablas que crear. Django no corre migrations ni necesita INSERT.
# Tests de IVR usan mocks (tests/mocks/database_mocks.py). Bug B-20/B-21.
DATABASES['ivr']['TEST'] = {'NAME': 'test_ivr_legacy', 'MIGRATE': False}
```

**Corrección respecto al plan v2.3.0:** `NAME: None` → `MIGRATE: False`.

---

## 4. ITERACIONES Y HALLAZGOS

### Iteración 1 — Solo DROP stale (sin cambios en código)

**Resultado:** Error persiste, cambia de forma:
```
# Antes:  ALTER TABLE django_content_type DROP COLUMN name (esquema stale)
# Después: ALTER TABLE django_content_type ADD CONSTRAINT UNIQUE (BD limpia)
```
**Conclusión:** El DROP solo no es suficiente. Django recrea la BD y el error
de ALTER persiste porque el router sigue enviando migrations de `contenttypes`
a `test_ivr_legacy`.

### Iteración 2 — Router fix + `NAME: None`

**Resultado:**
```
Error cambia: ALTER command denied → INSERT command denied
(test_ivr_legacy.django_migrations)
```

El router fix funcionó para `contenttypes` (ya no intenta `ALTER TABLE
django_content_type`). Pero Django aún intenta correr la migration
`ivr/0001_initial.py` en `test_ivr_legacy` y necesita INSERT en
`django_migrations` — permiso que `django_user` tampoco tiene.

**Conclusión:** El router fix es correcto pero `NAME: None` no evita la
ejecución de migrations del IVR app.

### Iteración 3 — Router fix + `MIGRATE: False` ← SOLUCIÓN FINAL

**Resultado:**
```
249 failed, 218 passed, 1 skipped, 23 warnings, 54 errors
```
**Reducción:** 344 → 54 errors **(−290, −84%)**

**Conclusión:** ✅ Esta combinación resuelve el problema de BD.

---
## 5. RESULTADOS FINALES

### 5.1 Comparativa cuantitativa

| Métrica | Baseline | Post-Tarea 0.0 | Δ | % cambio |
|---|---|---|---|---|
| **errors** | **344** | **54** | **−290** | **−84%** |
| passed | 119 | 218 | +99 | +83% |
| failed | 59 | 249 | +190 | +322% |
| skipped | 0 | 1 | +1 | — |

### 5.2 Interpretación del aumento en `failed`

El aumento de 59 → 249 fallos es **esperado y positivo**:

```
344 errors resueltos se distribuyen en:
  → 99 tests ahora PASAN  ✅  (estaban bloqueados por error de setup de BD)
  → 190 tests ahora FALLAN ❌  (pueden ejecutarse pero tienen bugs B-02, B-22, B-23)
  → 1 test SKIPPED
  Suma: 99 + 190 + 1 = 290 ✓
```

Los 190 nuevos `failed` son tests que **antes ni siquiera llegaban a correr**.
Ahora corren, y fallan por razones de código (ImportError, lógica incorrecta)
que son las brechas B-02, B-22, B-23 — abordadas en Tareas 0.1-0.6 del plan.

### 5.3 Clasificación de los 54 errors restantes

| Tipo | Cantidad | Brecha | Tarea del plan |
|---|---|---|---|
| Colección — ImportError (archivo completo) | 20 | B-02 | Tarea 0.1-0.3 |
| Test-específico — ImportError (setup) | 34 | B-02 | Tarea 0.1-0.3 |
| **TOTAL** | **54** | B-02 | 0.1-0.3 |

**Los 54 errors restantes son 100% B-02 (ImportError).** No hay ningún error
de BD restante. La Tarea 0.0 eliminó completamente los errores de BD.

### 5.4 Detalle de los ImportError restantes

| Símbolo faltante | Tipo de error | Tarea |
|---|---|---|
| `Role` from `apps.access.models` | ImportError | 0.1 |
| `HasModuleAccess` from `apps.access.permissions` | ImportError | 0.3 |
| `CustomTokenObtainPairSerializer` from `apps.authentication.serializers` | ImportError | 0.3 |
| `CallRecord` from `apps.core.models` | ImportError | 0.3 |
| `LoggingMiddleware` from `apps.core.middleware.logging` | ImportError | 0.3 |
| `ServiceFilterMixin` from `apps.core.mixins` | ImportError | 0.3 |
| `HasServiceAccess` from `apps.core.permissions` | ImportError | 0.3 |
| `Service` from `apps.core.models` | ImportError | 0.3 |
| `LoginSerializer` from `apps.users.serializers` | ImportError | 0.3 |
| `UserProfileSerializer` from `apps.users.serializers` | ImportError | 0.3 |
| `format_phone` from `apps.utils.formatters` | ImportError | 0.3 |
| `apps.ivr_legacy` (módulo) | ModuleNotFoundError | 0.2 |
| `apps.utils.network` (módulo) | ModuleNotFoundError | 0.3 |

---

## 6. CORRECCIÓN AL PLAN v2.3.0

El plan v2.3.0 especificaba `NAME: None`. Esto debe corregirse:

### Tarea 0.0 — Paso 3 (corregido):

```python
# plan v2.3.0 decía (INCORRECTO):
DATABASES['ivr']['TEST'] = {'NAME': None}

# Implementación real confirmada (CORRECTO):
DATABASES['ivr']['TEST'] = {'NAME': 'test_ivr_legacy', 'MIGRATE': False}
```

**Justificación técnica:**
- `NAME: None` → Django usa nombre por defecto `test_ivr_legacy` (sin efecto real)
- `MIGRATE: False` → Django crea la BD vacía pero NO ejecuta ninguna migration
  (no necesita INSERT, SELECT, ALTER en `django_migrations`)
- Con modelos `managed=False`, ninguna tabla es creada → BD queda vacía ✅

Se genera plan v2.3.1 como corrección de patch para este detalle.

---

## 7. ANÁLISIS DE PERFORMANCE DEL ROUTER

Con la corrección en `allow_migrate`, el comportamiento ahora es:

```
App               | ivr DB (antes) | ivr DB (ahora)
------------------+----------------+---------------
contenttypes      | None (migra)   | False (omite)
auth              | None (migra)   | False (omite)
sessions          | None (migra)   | False (omite)
admin             | None (migra)   | False (omite)
authtoken         | None (migra)   | False (omite)
ivr               | True (migra)   | True (migra)  ← sin cambio
core/default apps | default        | default       ← sin cambio
```

**Efecto:** Django ya no intenta crear `django_content_type`, `auth_user`,
`django_session`, etc. en `test_ivr_legacy`. Con `MIGRATE: False`, tampoco
corre la migration de IVR. La BD queda completamente vacía.

---

## 8. VALIDACIÓN CNST-003

```
CNST-003: IVR Legacy Database — READ-ONLY (verificado post-implementación)
  ├── Permisos MariaDB   : django_user → solo SELECT en ivr_legacy  ✅ sin cambio
  ├── Router db_for_write: retorna None para app ivr                 ✅ sin cambio
  ├── Router allow_migrate: retorna False para non-IVR en ivr DB    ✅ CORREGIDO
  └── Test settings      : MIGRATE=False → no corre migrations IVR  ✅ NUEVO
```

---

## 9. PRÓXIMOS PASOS — TAREAS 0.1-0.3

Con la Tarea 0.0 completada, el estado final es:

```
54 errors  ← 100% son B-02 ImportError
249 failed ← mezcla de B-02 y B-22/B-23 (lógica)
218 passed ← tests que funcionan correctamente
```

La Tarea 0.1 (corregir `Role` en factories) desbloquea ~9 archivos en cascada
y reducirá significativamente tanto los errors como los failed.

### Proyección tras Tarea 0.1:
```
Actual:  54 errors / 249 failed / 218 passed
Tarea 0.1 (Role→Function): ~34 errors / ~220 failed / ~280+ passed
Tarea 0.2 (ivr_legacy):    ~33 errors / ~219 failed / ~281+ passed
Tarea 0.3 (12 stubs):       ~0 errors / ~200  failed / ~320+ passed
```

---

## 10. RESUMEN EJECUTIVO

| Item | Conclusión |
|---|---|
| Opción D efectiva | **SÍ** — −290 errors (−84%) |
| Error de BD completamente eliminado | **SÍ** — 0 errors de BD restantes |
| Corrección al plan v2.3.0 | `NAME: None` → `MIGRATE: False` (patch v2.3.1) |
| Cambios en MariaDB necesarios | **NO** — sin tocar permisos |
| CNST-003 alineado | **SÍ** — 4 niveles cubiertos |
| Siguiente tarea desbloqueada | Tarea 0.1 (Role→Function en factories) |

---

## ARCHIVOS MODIFICADOS (implementados y verificados)

| Archivo | Cambio | Estado |
|---|---|---|
| `callcentersite/config/db_router.py` | `return None` → `return db == 'default'` en `allow_migrate` | ✅ Implementado |
| `callcentersite/config/settings/testing.py` | `{'NAME': 'test_ivr_legacy'}` → `{'NAME': 'test_ivr_legacy', 'MIGRATE': False}` | ✅ Implementado |

---

*Análisis generado: 2026-03-21T22:32:05*
*Autor: Claude Code — IACT-api*
*Basado en ejecución real de pytest (3 iteraciones de medición)*

