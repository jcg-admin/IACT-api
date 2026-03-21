# PLAN DE IMPLEMENTACIÓN POR FASES — IACT API
## Cierre de Brechas y Fortalecimiento del Sistema

**Versión:** 2.3.0
**Fecha:** 2026-03-21
**Autor:** Claude Code — Análisis automatizado
**Cambios vs v2.2.1:**
- **Tarea 0.0 reemplazada:** GRANT ALTER (Opción A) → Corregir router + TEST NAME=None (Opción D)
- Decisión basada en análisis `ANALISIS_GRANT_ALTER_IVR_v1.0.0_210326.md`
- Causa raíz identificada: `allow_migrate` retorna `None` para apps del framework → migrations innecesarias en IVR
- Opción D no requiere cambios en permisos MariaDB
- Resto del plan idéntico a v2.2.1

**Documentos base:**
- `documentos/analisis/ANALISIS_ESTADO_TESTS_v2_2_1.md`
- `documentos/analisis/ANALISIS_GRANT_ALTER_IVR_v1.0.0_210326.md` ← nuevo
- `documentos/planes/plan_implementacion_v2.2.1_20260321214437.md` ← supersedido

---

## ESTADO ACTUAL (verificado 2026-03-21)

| Componente | Estado | Detalle |
|---|---|---|
| PostgreSQL 16 | ✅ online | puerto 5432 |
| MariaDB 10.11 | ✅ online | puerto 3306 |
| Django → PostgreSQL (`default`) | ✅ conectado | `iact_analytics` READ+WRITE |
| Django → MariaDB (`ivr`) | ✅ conectado | `ivr_legacy` READ-ONLY (CNST-003) |
| Django system check | ✅ 0 errores | `manage.py check` limpio |
| Migraciones pendientes | ✅ ninguna | Todo en `[X]` |
| `tests/` — colección | ❌ 20 errores (13 ImportError) | Interrumpe sin `--continue-on-collection-errors` |
| `tests/` — ejecución | ⚠️ 119 passed / 59 failed / 344 errors | Requiere `--continue-on-collection-errors` |
| `test_ivr_legacy` | ❌ Stale (existe) | Contiene 2 tablas con esquema Django <1.8 |
| `db_router.allow_migrate` | ❌ Bug | Retorna `None` para framework apps → migrations en IVR |

### Cumplimiento funcional por módulo

| Módulo | Documentadas | Implementadas | % |
|---|---|---|---|
| MOD_Auth | 4 | 4 | **100%** |
| MOD_Users | 9 | 6 | **67%** |
| MOD_Access | 3 | 1 | **33%** |
| MOD_Reports | 6 | 2 | **33%** |
| MOD_Audit | 3 | 2 | **67%** |
| **TOTAL** | **25** | **15** | **60%** |

---

## DECISIÓN — 344 ERRORES DE SETUP DE BD (actualizada v2.3.0)

### Diagnóstico preciso

El error reportado en v2.2.1 era correcto:
```
MySQLdb.OperationalError: (1142,
  "ALTER command denied to user 'django_user'@'localhost'
   for table 'test_ivr_legacy'.'django_content_type'")
```

Sin embargo, el análisis posterior (`ANALISIS_GRANT_ALTER_IVR_v1.0.0_210326.md`)
identificó que **la falta de ALTER es síntoma, no causa raíz.**

### Causa raíz real

```python
# config/db_router.py — allow_migrate
def allow_migrate(self, db, app_label, model_name=None, **hints):
    if app_label in self.ivr_apps:       # {'ivr'}
        return db == 'ivr'
    if app_label in self.default_apps:   # {'core', 'auth', 'users', ...}
        return db == 'default'
    return None    # ← BUG: contenttypes, sessions → migrations en TODAS las BDs
```

`allow_migrate` retorna `None` para `contenttypes`, `sessions` y otras apps del
framework de Django. Django interpreta `None` como "sin preferencia → correr en
esta BD". Esto provoca que Django intente ejecutar
`contenttypes/0002_remove_content_type_name` (que usa `ALTER TABLE`) sobre
`test_ivr_legacy`, donde `django_user` no tiene permiso.

Adicionalmente, `test_ivr_legacy` tiene un esquema stale de Django <1.8
(tabla `django_content_type` con campo `name` obsoleto), lo que fuerza que
Django intente aplicar esa migration de limpieza.

### Opciones evaluadas

| Opción | Descripción | Diagnóstico |
|---|---|---|
| **A — GRANT ALTER** | `GRANT ALTER ON test_ivr_legacy.*` | Parcha el síntoma; migrations innecesarias siguen ocurriendo |
| **B — TEST: NAME: None** | No crear BD de test para IVR | Correcto pero no elimina el bug del router |
| **C — SQLite para tests IVR** | Reemplazar MariaDB por SQLite en testing | Puede haber incompatibilidades |
| **D — Corregir router + NAME: None** | Fix bug en `allow_migrate` + no crear BD test IVR | Elimina causa raíz + alinea con CNST-003 |

### DECISIÓN ADOPTADA v2.3.0

**Opción D — Corregir router + TEST: NAME: None**

**Justificación:**
1. **Elimina la causa raíz.** Cambiar `return None` → `return db == 'default'` en `allow_migrate` evita que Django corra migrations del framework en la BD IVR.
2. **Sin cambios en MariaDB.** No requiere acceso root ni nuevos GRANTs.
3. **Refuerza CNST-003.** Si IVR es READ-ONLY en producción, tampoco necesita BD de test con datos mutables. `TEST: NAME: None` alinea los 3 niveles: permisos de BD, router, y configuración de tests.
4. **Tests IVR ya usan mocks.** `tests/mocks/database_mocks.py` existe para este propósito.
5. **Más robusto.** Elimina el riesgo de BD stale futura causando el mismo error.

**Permisos MariaDB sin cambio:**
```sql
-- Estado actual → correcto, no se modifica
GRANT USAGE ON *.*
GRANT SELECT ON ivr_legacy.*          -- READ-ONLY producción (CNST-003) ✅
GRANT CREATE, DROP ON test_ivr_legacy.*  -- ya no se usa para tests IVR
```

---

## BRECHAS — ESTADO COMPLETO v2.3.0

### Brechas Críticas

| ID | Brecha | Prioridad |
|---|---|---|
| B-01 | JWT vs DRF Token sin expiración | P1 |
| B-02 | 13 ImportError en `tests/` (20 archivos bloqueados) | P1 |
| B-20 | Bug en `db_router.allow_migrate` → migrations innecesarias en IVR | P1 |
| B-21 | `test_ivr_legacy` stale (existe, bloquea y tiene esquema Django <1.8) | P1 |
| B-22 | Navigation builder: métodos faltantes en `MenuValidator`/`MenuBuilder` | P1 |
| B-23 | Validators: 8 bugs (RUT, phone, service 800, codigo, date range, ValueError→ValidationError) | P1 |
| B-04 | Validación SoD no existe en código | P2 |
| B-05 | Endpoints assign/revoke de funciones faltan | P2 |
| B-06 | `users.lock` implementado como `deactivate` | P2 |

### Detalle B-02 — ImportError (13 símbolos faltantes)

| Símbolo faltante | Módulo que lo busca | Tests afectados (cascada) |
|---|---|---|
| `Role` | `apps.access.models` | 9 archivos via `access_factories.py` |
| `HasModuleAccess` | `apps.access.permissions` | `test_permissions` |
| `CustomTokenObtainPairSerializer` | `apps.authentication.serializers` | `test_serializers` |
| `CallRecord` | `apps.core.models` | `test_core_models`, `test_core_serializers` (x2) |
| `Service` | `apps.core.models` | `test_service_access`, `test_core_serializers` |
| `UserServiceAccess` | `apps.core.models` | `test_service_access` |
| `LoggingMiddleware` | `apps.core.middleware.logging` | `test_middleware` |
| `ServiceFilterMixin` | `apps.core.mixins` | `test_mixins` |
| `HasServiceAccess` | `apps.core.permissions` | `test_permissions` (core) |
| `LoginSerializer` | `apps.users.serializers` | `test_auth_serializers` |
| `UserProfileSerializer` | `apps.users.serializers` | `test_serializers` (users) |
| `format_phone` | `apps.utils.formatters` | `test_formatters` |
| `apps.ivr_legacy` (módulo) | `etl_service.py` → tests | `test_core_etl_service` |
| `apps.utils.network` (módulo) | directo | `test_utils_network` |

### Brechas Importantes

| ID | Brecha | Prioridad |
|---|---|---|
| B-07 | Throttling por IP en login | P2 |
| B-08 | Inactividad automática 90 días (CNST-013) | P2 |
| B-03 | Serializers faltantes en pipeline | P2 |
| B-09 | `is_locked` en User vs tabla `LoginLockout` separada | P3 |
| B-10 | `UserActionLog` centralizado vs `LoginAttempt` específico | P3 |
| B-11 | `DeletionLog` no implementado | P3 |
| B-12 | CNST-010: `MAX_EXPORT_ROWS=100000` debe ser 10000 | P3 |
| B-13 | `reports.modify_data`, `reports.approve`, `reports.schedule` sin endpoint | P3 |
| B-14 | `users.export` sin endpoint | P3 |
| B-15 | CNST-015: retención 7 años sin política automática | P3 |

### Brechas Menores

| ID | Brecha | Prioridad |
|---|---|---|
| B-16 | `full_name`, `last_login`, `date_joined` faltan en login response | P4 |
| B-17 | `locked_until` timestamp vs `locked_minutes` entero | P4 |
| B-18 | Detección de sesión duplicada (Flujo A5) | P4 |
| B-19 | drf_spectacular: type hints faltantes en serializers | P5 |

---
## FASES DE IMPLEMENTACIÓN

---

### FASE 0 — ESTABILIZACIÓN (Prerequisito absoluto)

**Objetivo:** Test suite funcional. Sin Fase 0 no se puede medir el avance real.

---

#### Tarea 0.0 — Resolver 344 errores de BD (B-20 + B-21) ← DECISIÓN D (v2.3.0)

> **Cambio respecto a v2.2.1:** Se reemplaza `GRANT ALTER` por corrección del
> bug en el router y configuración `TEST: NAME: None`. Sin cambios en MariaDB.

**Paso 1 — Limpiar BD stale (una sola vez, como root):**
```bash
mysql -u root -e "DROP DATABASE IF EXISTS test_ivr_legacy;"
```

**Verificación:**
```bash
mysql -u root -e "SHOW DATABASES LIKE 'test_%';"
# Resultado esperado: vacío (no debe aparecer test_ivr_legacy)
```

---

**Paso 2 — Corregir `allow_migrate` en el router:**

Archivo: `callcentersite/config/db_router.py`

```python
# ANTES (bug — retorna None para framework apps):
def allow_migrate(self, db, app_label, model_name=None, **hints):
    if app_label in self.ivr_apps:
        return db == 'ivr'
    if app_label in self.default_apps:
        return db == 'default'
    return None   # ← Django corre migrations en TODAS las BDs

# DESPUÉS (corrección):
def allow_migrate(self, db, app_label, model_name=None, **hints):
    if app_label in self.ivr_apps:
        return db == 'ivr'
    return db == 'default'   # todo lo demás solo migra en default
```

**Tests del router a actualizar (`test_router_migrations_readonly`):**
```python
def test_router_migrations_readonly():
    router = DatabaseRouter()
    # IVR app: solo en ivr
    assert router.allow_migrate('default', 'ivr') is False
    assert router.allow_migrate('ivr', 'ivr') is True
    # Framework apps (contenttypes, auth, etc.): solo en default
    assert router.allow_migrate('default', 'contenttypes') is True
    assert router.allow_migrate('ivr', 'contenttypes') is False   # antes: None
    assert router.allow_migrate('default', 'sessions') is True
    assert router.allow_migrate('ivr', 'sessions') is False       # antes: None
```

---

**Paso 3 — Agregar `TEST: NAME: None` en settings de testing:**

Archivo: `callcentersite/config/settings/testing.py`

```python
# Agregar en el bloque DATABASES:

# ivr TEST NAME=None: IVR es READ-ONLY (CNST-003), no necesita BD de test.
# Los tests de IVR usan mocks (tests/mocks/database_mocks.py).
DATABASES['ivr']['TEST'] = {'NAME': None}
```

---

**Verificación post-implementación:**
```bash
cd /home/user/IACT-api/callcentersite
source ../venv/bin/activate

# Correr tests con --continue-on-collection-errors
python -m pytest tests/ --continue-on-collection-errors -q --tb=no 2>&1 | tail -5

# Objetivo: los "344 errors" desaparecen del output
# Esperado: X passed / Y failed / 0 errors setup BD
```

**Criterio de aceptación:**
```
pytest tests/ --continue-on-collection-errors
→ Antes: 119 passed / 59 failed / 344 errors
→ Después: 119 passed / 59 failed / 0 errors (errores de BD eliminados)
```

**Archivos modificados:**

| Archivo | Tipo de cambio |
|---|---|
| `callcentersite/config/db_router.py` | Eliminar `return None`, agregar `return db == 'default'` |
| `callcentersite/config/settings/testing.py` | Agregar `DATABASES['ivr']['TEST'] = {'NAME': None}` |

---

#### Tarea 0.1 — Corregir raíz de cascada: `Role` en access_factories (B-02)

El símbolo `Role` en `tests/factories/access_factories.py` fue reemplazado
en RBAC v6.0.0 por `Function` y `UserFunctionAssignment`.

```python
# tests/factories/access_factories.py — línea 13 (ACTUAL — roto)
from apps.access.models import (Role, ...)

# CORRECCIÓN
from apps.access.models import (
    Function,
    UserFunctionAssignment,
    Module,
    UserModuleAccess,
)
```

También actualizar las factories que usen `RoleFactory` / `UserRoleAssignmentFactory`
para usar `FunctionFactory` / `UserFunctionAssignmentFactory`.

**Impacto:** Desbloquea 9 archivos en cascada (todos los integration tests
de auth + la mayoría de authentication unit tests).

**Criterio de aceptación:**
```
pytest tests/factories/ --collect-only → 0 errores
```

---

#### Tarea 0.2 — Corregir import de `apps.ivr_legacy` en etl_service (B-02)

```python
# apps/core/services/etl_service.py:15 (ACTUAL — roto)
from apps.ivr_legacy.adapters import IVRAdapter

# CORRECCIÓN — verificar nombre real del módulo
from apps.ivr.adapters import IVRAdapter   # o el módulo que corresponda
```

También actualizar `tests/unit/ivr_legacy/test_ivr_app.py`:
```python
# Si el módulo se llama apps.ivr, corregir en el test
import apps.ivr  # en lugar de apps.ivr_legacy
```

**Criterio de aceptación:** `test_core_etl_service.py` y `test_ivr_app.py` coleccionan sin error.

---

#### Tarea 0.3 — Crear stubs para símbolos faltantes (B-02)

Los siguientes símbolos no existen aún. Crear stubs mínimos para desbloquear
los tests — la implementación real va en Fases 1-3:

| Símbolo | Archivo destino | Stub mínimo |
|---|---|---|
| `HasModuleAccess` | `apps/access/permissions/__init__.py` | `class HasModuleAccess(BasePermission): pass` |
| `HasServiceAccess` | `apps/core/permissions.py` | `class HasServiceAccess(BasePermission): pass` |
| `LoggingMiddleware` | `apps/core/middleware/logging.py` | `class LoggingMiddleware: def __init__(self, get_response): ...` |
| `ServiceFilterMixin` | `apps/core/mixins.py` | `class ServiceFilterMixin: pass` |
| `CustomTokenObtainPairSerializer` | `apps/authentication/serializers/__init__.py` | subclass de `TokenObtainPairSerializer` |
| `LoginSerializer` | `apps/users/serializers/__init__.py` | alias de serializer existente |
| `UserProfileSerializer` | `apps/users/serializers/__init__.py` | alias de `ProfileSerializer` |
| `format_phone` | `apps/utils/formatters.py` | función básica de formateo |
| `apps.utils.network` | `apps/utils/network.py` | módulo con `get_client_ip`, `get_user_agent`, `get_request_metadata` |
| `CallRecord` | — | Evaluar: ¿existe en otra app? ¿mover o crear? |
| `Service` | — | Evaluar: ¿existe en otra app? ¿mover o crear? |
| `UserServiceAccess` | — | Evaluar: ¿existe en otra app? ¿mover o crear? |

**Criterio de aceptación:**
```
pytest tests/ --collect-only → 0 errores de colección
```

---

#### Tarea 0.4 — Corregir Navigation Builder — MenuValidator/MenuBuilder (B-22)

Los tests de `test_navigation_builders.py` fallan con `AttributeError` porque
`MenuValidator` y `MenuBuilder` no tienen los métodos esperados.

**Métodos faltantes en `MenuValidator`:**
```python
validate_numeric_id(value) -> bool
validate_level1_id(value) -> bool
validate_level2_id(value) -> bool
validate_icon_path(path) -> bool
validate_menu_structure(menu_dict) -> bool
```

**Métodos faltantes en `MenuBuilder`:**
```python
build_user_menu(user, permissions) -> list
filter_by_permissions(menu, user_permissions) -> list
personalize_menu(menu, user) -> list
```

**Paso 1 — Identificar la implementación actual:**
```bash
grep -rn "class MenuValidator\|class MenuBuilder" apps/core/navigation/
```

**Paso 2 — Implementar métodos faltantes** según contrato de los tests.

**Criterio de aceptación:**
```
pytest tests/unit/core/test_navigation_builders.py → 0 failures
```

---

#### Tarea 0.5 — Corregir Validators (B-23)

**5a — `validate_export_row_limit`: ValueError → ValidationError + límite 10000:**
```python
# apps/utils/validators.py
from django.core.exceptions import ValidationError

def validate_export_row_limit(row_count: int, max_limit: int = 10000) -> None:
    if row_count > max_limit:
        raise ValidationError(
            f"Export limitado a {max_limit:,} filas. Solicitadas: {row_count:,}."
        )
```

**5b — `validate_rut`: aceptar formatos con/sin guión y con K:**
```python
import re
RUT_PATTERN = re.compile(r'^\d{7,8}-?[\dkK]$')
```

**5c — `validate_phone_number`: aceptar 8 dígitos (línea fija chilena):**
```python
if not (8 <= len(digits) <= 9):
    raise ValidationError(...)
```

**5d — `validate_service_800`: revisar regex para 800-XXXXXX:**
```python
SERVICE_800_PATTERN = re.compile(r'^800\d{6}$')
```

**5e — `validate_codigo_center`: agregar longitud mínima:**
```python
MIN_CODIGO_LENGTH = 3
if len(codigo) < MIN_CODIGO_LENGTH:
    raise ValidationError(...)
```

**5f — `validate_date_range`: corregir condición start > end:**
```python
if start_date > end_date:
    raise ValidationError("La fecha de inicio no puede ser posterior al fin.")
```

**Criterio de aceptación:**
```
pytest tests/unit/utils/test_validators.py tests/unit/utils_tests/test_validators.py → 0 failures
```

---

#### Tarea 0.6 — Corregir helpers, fixtures e ivr_legacy (B-23)

**Helpers** (`test_helpers.py`):
```python
def generate_random_token(length=32) -> str: ...

def get_client_ip(request) -> str | None:
    return request.META.get('HTTP_X_FORWARDED_FOR') or \
           request.META.get('REMOTE_ADDR') or None

def get_user_agent(request) -> str | None:
    return request.META.get('HTTP_USER_AGENT') or None

def safe_get(d, *keys, default=None):
    for key in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(key, default)
    return d
```

**Fixture** (`test_fixtures.py`):
Actualizar `user_data` fixture con los campos actuales del modelo `CustomUser`.

**IVR legacy** (`test_ivr_legacy/test_ivr_app.py`):
Actualizar import `apps.ivr_legacy` → `apps.ivr` (ver Tarea 0.2).

**Criterio de aceptación:**
```
pytest tests/unit/utils/test_helpers.py tests/unit/test_fixtures.py → 0 failures
```

---

#### Tarea 0.7 — Serializers faltantes en pipeline (B-03)

```python
# apps/pipeline/serializers/callrecord_serializers.py
class CallRecordBulkCreateSerializer(serializers.Serializer): ...
class DailyStatsSerializer(serializers.Serializer): ...
class ServiceStatsSerializer(serializers.Serializer): ...
class TopCallerSerializer(serializers.Serializer): ...
```

**Criterio de aceptación:** `python manage.py spectacular --validate` sin warnings en pipeline.

---
### FASE 1 — SEGURIDAD CRÍTICA
**Dependencias:** Fase 0 completada.

#### Tarea 1.1 — JWT access + refresh token (B-01)

Reemplazar DRF Token (sin expiración) por `rest_framework_simplejwt`:
- `access_token`: 15 minutos
- `refresh_token`: 7 días
- Blacklist en logout

#### Tarea 1.2 — Throttling por IP en login (B-07)

```python
# config/settings/base.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '5/min',   # CNST: máx 5 intentos/minuto por IP
    }
}
```

#### Tarea 1.3 — Inactividad automática 90 días (B-08)

Tarea Celery/APScheduler diaria que desactiva usuarios con último login > 90 días.

---

### FASE 2 — MODELO DE DATOS
**Dependencias:** Fase 0. Puede correr en paralelo con Fase 1.

#### Tarea 2.1 — Campo `is_locked` en User (B-06, B-09)

Agregar campo `is_locked` a `CustomUser` con semántica correcta (distinto a `is_active`).
Migración requerida.

#### Tarea 2.2 — `UserActionLog` centralizado (B-10)

Centralizar `LoginAttempt` en `UserActionLog` con `action_type` enum.

---

### FASE 3 — RBAC COMPLETO
**Dependencias:** Fase 0.

#### Tarea 3.1 — Endpoints assign/revoke funciones (B-05)
#### Tarea 3.2 — Validación SoD en código (B-04)
#### Tarea 3.3 — MOD_Reports funciones faltantes (B-13)
#### Tarea 3.4 — `users.export` + CNST-010 (B-14, B-12)
#### Tarea 3.5 — DeletionLog (B-11)

---

### FASE 4 — CALIDAD DE API
**Dependencias:** Fase 2.

#### Tarea 4.1 — Campos adicionales en login response (B-16)
#### Tarea 4.2 — `locked_until` timestamp (B-17)
#### Tarea 4.3 — Detección de sesión duplicada (B-18)

---

### FASE 5 — SCHEMA TÉCNICO
**Dependencias:** Ninguna — puede ejecutarse en cualquier momento.

#### Tarea 5.1 — Type hints en serializers (B-19)
#### Tarea 5.2 — Viewsets sin `serializer_class` (B-19)

---

## ORDEN DE EJECUCIÓN v2.3.0

```
FASE 0 — Estabilización (prerequisito absoluto)
  ├── [0.0] DROP stale + fix router + TEST NAME=None   ← Opción D (v2.3.0)
  │         Paso 1: mysql DROP DATABASE test_ivr_legacy
  │         Paso 2: corregir allow_migrate en db_router.py
  │         Paso 3: agregar DATABASES['ivr']['TEST'] = {'NAME': None}
  │         Criterio: 344 errors desaparecen
  ├── [0.1] Corregir Role → Function en factories      ← desbloquea 9 archivos en cascada
  ├── [0.2] Corregir apps.ivr_legacy → apps.ivr        ← desbloquea etl_service + test_ivr_app
  ├── [0.3] Stubs para 12 símbolos faltantes           ← desbloquea colección (0 ImportError)
  ├── [0.4] MenuValidator/MenuBuilder métodos          ← elimina 24 failures navigation
  ├── [0.5] Validators: 6 bugs                         ← elimina 8 failures validators
  ├── [0.6] Helpers, fixtures, ivr_legacy              ← elimina ~6 failures restantes
  └── [0.7] Serializers pipeline                       ← elimina warnings schema

FASE 1 — Seguridad (paralelo con Fase 2)
  ├── [1.1] JWT access + refresh token
  ├── [1.2] Throttling IP en login
  └── [1.3] Inactividad automática 90d

FASE 2 — Modelo datos (paralelo con Fase 1)
  ├── [2.1] is_locked en User
  └── [2.2] UserActionLog centralizado

FASE 3 — RBAC completo (después de Fase 0)
  ├── [3.1] assign/revoke endpoints
  ├── [3.2] Validación SoD
  ├── [3.3] MOD_Reports funciones
  ├── [3.4] users.export + CNST-010
  └── [3.5] DeletionLog

FASE 4 — Calidad API (después de Fase 2)
  ├── [4.1] Campos login response
  ├── [4.2] locked_until timestamp
  └── [4.3] Sesión duplicada

FASE 5 — Schema (cualquier momento)
  ├── [5.1] Type hints serializers
  └── [5.2] Viewsets sin serializer_class
```

---

## CUMPLIMIENTO CNST-003 TRAS TAREA 0.0

```
CNST-003: IVR Legacy Database — READ-ONLY
  ├── Permisos MariaDB: django_user solo tiene SELECT en ivr_legacy   ✅ (sin cambio)
  ├── Router: db_for_write retorna None para app ivr                  ✅ (sin cambio)
  ├── Router: allow_migrate retorna False para ivr en no-ivr apps     ✅ (corregido en v2.3.0)
  └── Tests: IVR no tiene BD de test (NAME=None)                      ✅ (nuevo en v2.3.0)

Resultado: CNST-003 completamente alineado en los 4 niveles.
```

---

## MÉTRICAS OBJETIVO

| Métrica | Estado actual | Objetivo tras Fase 0 | Objetivo final |
|---|---|---|---|
| Cumplimiento funcional | 60% (15/25) | 60% | **100% (25/25)** |
| `tests/` colección | ❌ 20 errores | ✅ 0 errores | ✅ 0 errores |
| `tests/` passed | 119 ✅ | ~450+ ✅ | ✅ >500 |
| `tests/` failed | 59 ❌ | 0 ❌ | 0 ❌ |
| Errores setup BD | 344 🔴 | **0** ✅ | 0 ✅ |
| Navigation builder | 24 fallos | 0 ✅ | 0 ✅ |
| Validators bugfree | 8 fallos | 0 ✅ | 0 ✅ |
| SoD en código | 0% | 0% | 100% (3 reglas) |
| Tokens | DRF sin expiración | DRF sin expiración | JWT 15min/7días |
| CNST-010 | 100K + ValueError | 10K + ValidationError | ✅ |
| CNST-013 | Sin automatización | Sin automatización | Task diaria activa |
| DeletionLog | No existe | No existe | Implementado |
| Schema warnings | ~55 | < 30 | < 10 |

---

## CHANGELOG

| Versión | Fecha | Cambio |
|---|---|---|
| v2.3.0 | 2026-03-21 | Reemplaza Tarea 0.0: GRANT ALTER → Opción D (router fix + TEST NAME=None) |
| v2.2.1 | 2026-03-21 | Diagnóstico 344 errores; decisión GRANT ALTER (Opción A) — supersedido |
| v2.0.1 | 2026-03-21 | Plan base con Fases 0-5 |

---

*Documento generado por Claude Code — IACT-api*
*Versión: 2.3.0 | Fecha: 2026-03-21*
*Supersede: plan_implementacion_v2.2.1_20260321214437.md*
*Análisis de referencia: ANALISIS_GRANT_ALTER_IVR_v1.0.0_210326.md*

