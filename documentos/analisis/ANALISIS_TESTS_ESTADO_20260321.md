# ANÁLISIS — Estado del Sistema de Tests
## pytest.ini + tests/ + colección + errores

**Versión:** 1.0.0
**Fecha:** 2026-03-21
**Comando base:** `python -m pytest --collect-only -q` desde `callcentersite/`

---

## RESUMEN EJECUTIVO

| Métrica | Valor |
|---|---|
| Tests colectados (OK) | **625** |
| Archivos con error de colección | **20** |
| ImportErrors únicos | **12** |
| Tests en `tests/` | 505 |
| Tests en `apps/` (testpaths) | 120 |
| Tests IVR nuevos | 13 (100% passing) |

---

## 1. ANÁLISIS DE `pytest.ini`

```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.testing
django_find_project = false
python_files = test_*.py
python_classes = Test*
python_functions = test_*
testpaths = tests apps
markers = unit, integration, api, e2e, slow, fast, access, audit, core
addopts = -ra --strict-markers --strict-config --showlocals --tb=short
```

### Observaciones

| Ítem | Estado | Nota |
|---|---|---|
| `DJANGO_SETTINGS_MODULE` | ✅ Correcto | Apunta a `config.settings.testing` |
| `django_find_project = false` | ✅ Correcto | Necesario porque el proyecto está en subdirectorio |
| `python_files = test_*.py` | ✅ Correcto | Patrón estándar |
| `python_classes = Test*` | ⚠️ Parcial | También hay clases con prefijo `Test` sin sufijo — funciona pero excluye clases con otro patrón |
| `python_functions = test_*` | ✅ Correcto | Patrón estándar |
| `testpaths = tests apps` | ⚠️ Revisar | Colecta tests desde **dos** ubicaciones. Los tests en `apps/` son de las apps mismas (alerts, dashboard, pipeline). Es válido pero genera mezcla de responsabilidades. |
| `addopts --strict-markers` | ✅ Correcto | Evita markers no declarados |
| `addopts --strict-config` | ✅ Correcto | Evita config inválida |
| `addopts --showlocals` | ⚠️ Impacto | Muestra variables locales en fallos — útil pero verbose |
| `addopts --tb=short` | ✅ Correcto | Traceback conciso |

### Problema: `testpaths = tests apps`

`apps/` contiene **120 tests** en `apps/alerts/tests/`, `apps/dashboard/tests/`,
`apps/pipeline/tests/`. Estos coexisten con los tests de `tests/`.

```
Consecuencia:
  - apps/alerts/tests/    → 3 archivos  → ~40 tests
  - apps/dashboard/tests/ → 5 archivos  → ~50 tests
  - apps/pipeline/tests/  → 1 archivo   → ~3 tests + apps/ivr/tests/ → 1 archivo

  ¿Están duplicados en tests/unit/?
  apps/alerts/tests/  → NO está duplicado en tests/unit/ ← OK
  apps/dashboard/tests/ → NO está duplicado en tests/unit/ ← OK
  apps/pipeline/tests/ → SÍ hay tests/unit/pipeline/ también ← POSIBLE DUPLICACIÓN
```

---

## 2. ESTADO DE COLECCIÓN: 625 OK + 20 ERRORES

### Tests que SÍ se colectan (625)

```
tests/unit/utils/test_helpers.py           40 tests
tests/unit/utils/test_validators.py        38 tests
tests/unit/users/test_user_model.py        29 tests
tests/unit/core/test_navigation_builders   28 tests
tests/integration/users/test_user_viewset  23 tests
apps/dashboard/tests/*                     ~50 tests
apps/alerts/tests/*                        ~40 tests
tests/unit/ivr_legacy/test_tbl_temp*       13 tests  ← NUEVO
... (resto)
```

### Archivos con ERROR de colección (20)

Todos son **ImportError** — símbolos que los tests importan pero que no existen
(o no están exportados) en el código de producción.

---

## 3. MAPA COMPLETO DE IMPORTERRORS

### Grupo A — `apps.core.models` (4 archivos afectados)

**Símbolo faltante:** `CallRecord`, `Service`

```python
# Los tests importan:
from apps.core.models import CallRecord   # NO EXISTE en core/models.py
from apps.core.models import Service      # NO EXISTE en core/models.py
```

**Archivos afectados:**
- `tests/unit/core/test_core_models.py`
- `tests/unit/core/test_core_serializers.py`
- `tests/unit/core/test_core_serializers_OLD.py`
- `tests/unit/core/test_core_etl_service.py`
- `tests/unit/core/test_service_access.py`

**Causa:** `CallRecord` y `Service` probablemente fueron modelos planeados
o movidos a otra app (`apps.pipeline.models`, `apps.ivr`). Los tests
fueron escritos anticipando una versión del modelo que no existe.

---

### Grupo B — `apps.access.models` (4 archivos afectados)

**Símbolo faltante:** `Role`

```python
from apps.access.models import Role   # NO EXISTE (o no está exportado)
```

**Archivos afectados:**
- `tests/unit/authentication/test_models.py`
- `tests/integration/authentication/test_auth_flow.py`
- `tests/integration/authentication/test_recovery_flow.py`
- `tests/integration/authentication/test_session_flow.py`

**Causa:** El modelo `Role` puede existir bajo otro nombre o en un módulo
diferente dentro de `apps.access`.

---

### Grupo C — `apps.access.permissions` (1 archivo)

**Símbolo faltante:** `HasModuleAccess`

```python
from apps.access.permissions import HasModuleAccess   # NO EXISTE
```

**Archivos afectados:**
- `tests/unit/access/test_permissions.py`

---

### Grupo D — `apps.core.permissions` (1 archivo)

**Símbolo faltante:** `HasServiceAccess`

```python
from apps.core.permissions import HasServiceAccess   # NO EXISTE
```

**Archivos afectados:**
- `tests/unit/core/test_permissions.py`

---

### Grupo E — `apps.core.middleware.logging` (1 archivo)

**Símbolo faltante:** `LoggingMiddleware`

```python
from apps.core.middleware.logging import LoggingMiddleware   # NO EXISTE
```

**Archivos afectados:**
- `tests/unit/core/test_middleware.py`

---

### Grupo F — `apps.core.mixins` (1 archivo)

**Símbolo faltante:** `ServiceFilterMixin`

```python
from apps.core.mixins import ServiceFilterMixin   # NO EXISTE
```

**Archivos afectados:**
- `tests/unit/core/test_mixins.py`

---

### Grupo G — `apps.users.serializers` (2 archivos)

**Símbolos faltantes:** `LoginSerializer`, `UserProfileSerializer`

```python
from apps.users.serializers import LoginSerializer       # NO EXISTE
from apps.users.serializers import UserProfileSerializer # NO EXISTE
```

**Archivos afectados:**
- `tests/unit/users/test_auth_serializers.py`
- `tests/unit/users/test_serializers.py`

---

### Grupo H — `apps.authentication.serializers` (1 archivo)

**Símbolo faltante:** `CustomTokenObtainPairSerializer`

```python
from apps.authentication.serializers import CustomTokenObtainPairSerializer
```

**Archivos afectados:**
- `tests/unit/authentication/test_serializers.py`

---

### Grupo I — `apps.utils` (2 archivos)

**Símbolos faltantes:** `format_phone` (en formatters), `apps.utils.network`

```python
from apps.utils.formatters import format_phone   # NO EXISTE en formatters.py
import apps.utils.network                         # MÓDULO NO EXISTE
```

**Archivos afectados:**
- `tests/unit/utils/test_formatters.py`
- `tests/unit/utils/test_utils_network.py`

---

## 4. PROBLEMAS ADICIONALES EN LA ESTRUCTURA

### 4.1 `tests/conftest_COMPLETE.py` — Archivo zombie

```
tests/conftest_COMPLETE.py   ← 19.8 KB, fecha: 2026-03-14
```

Este archivo **NO es cargado por pytest** (nombre no es `conftest.py`).
Es un artifact de desarrollo previo. Contiene:
- Imports de modelos IVR que no existen (`QuarterlyReport`, `TransferReport`, etc.)
- 218+ fixtures duplicadas con `tests/conftest.py`
- Estado inconsistente

**Riesgo:** Confusión para desarrolladores — ¿cuál es el conftest real?

### 4.2 `test_core_serializers_OLD.py` — Test legacy duplicado

```
tests/unit/core/test_core_serializers.py
tests/unit/core/test_core_serializers_OLD.py  ← DUPLICADO
```

Mismo contenido (2.5 KB cada uno), mismo ImportError. El sufijo `_OLD`
indica que debería haberse eliminado. Pytest lo colecta porque:
- `python_files = test_*.py` lo incluye (`test_core_serializers_OLD.py` empieza con `test_`)

### 4.3 `tests/factories/ivr_factories.py` — Todo comentado pero exportado

`tests/factories/__init__.py` exporta `ivr_factories` pero el archivo
tiene todo su contenido comentado (DEUDA TÉCNICA 2026-03-21).
El `__init__.py` general de factories probablemente intenta importar
factories IVR que ya no existen.

### 4.4 Tests en `apps/` y en `tests/unit/` — Doble cobertura en pipeline

```
apps/pipeline/tests/test_call_notes.py   ← 3 tests
tests/unit/pipeline/test_models.py       ← tests de pipeline
tests/unit/pipeline/test_scheduler.py
tests/unit/pipeline/test_views.py
```

Dos ubicaciones para tests de pipeline — puede haber superposición.

---

## 5. ESTADO DE LOS MOCKS

### `tests/mocks/database_mocks.py` — 4 fixtures activas

✅ `mock_postgresql_connection`
✅ `mock_connection_error`
✅ `mock_database_settings`
✅ `mock_transaction_atomic`

### `tests/mocks/service_mocks.py` — 13 fixtures

✅ Todas las importaciones desde `apps.*` resuelven correctamente.
Las fixtures de Dashboard/Alert están marcadas como FUTURO.

### `tests/mocks/file_mocks.py` — 17 fixtures

✅ Todas las importaciones resuelven correctamente.

### `tests/mocks/scheduler_mocks.py` — 19 fixtures

✅ APScheduler correctamente importado.

### `tests/mocks/external_mocks.py` — 20 fixtures

✅ Sin problemas de import.

---

## 6. ESTADO DE LAS FIXTURES (`tests/fixtures/`)

### `tests/fixtures/users.py` — 11 fixtures ✅
### `tests/fixtures/rbac.py` — 4 fixtures ✅
### `tests/fixtures/authentication.py` — 4 fixtures ✅

Los 4 archivos JSON (`.json`) son fixtures de datos para `pytest-django`
pero **no están siendo cargados** en ningún conftest (`@pytest.fixture`
con `django_db_setup`). Son datos estáticos no utilizados actualmente.

---

## 7. RESUMEN: QUÉ FUNCIONA, QUÉ NO, QUÉ SOBRA

### ✅ FUNCIONA CORRECTAMENTE

| Elemento | Detalle |
|---|---|
| `pytest.ini` base | Settings, discovery, markers, addopts |
| 625 tests colectados | Sin errores de colección |
| `tests/mocks/` (4 módulos) | 73 fixtures activas sin ImportError |
| `tests/fixtures/` | 19 fixtures pytest sin problemas |
| `tests/unit/ivr_legacy/test_tbl_temp_prueba_ivr.py` | 13/13 passed |
| `tests/unit/utils/` (5 archivos) | Colectan y corren |
| `tests/unit/users/` (mayoritario) | Colectan y corren |
| `apps/dashboard/tests/` | 5 archivos colectan OK |
| `apps/alerts/tests/` | 3 archivos colectan OK |

### ❌ NO FUNCIONA (20 archivos con ImportError)

| Grupo | Símbolo faltante | Archivos afectados |
|---|---|---|
| A | `CallRecord`, `Service` de `apps.core.models` | 5 archivos |
| B | `Role` de `apps.access.models` | 4 archivos |
| C | `HasModuleAccess` de `apps.access.permissions` | 1 archivo |
| D | `HasServiceAccess` de `apps.core.permissions` | 1 archivo |
| E | `LoggingMiddleware` de `apps.core.middleware.logging` | 1 archivo |
| F | `ServiceFilterMixin` de `apps.core.mixins` | 1 archivo |
| G | `LoginSerializer`, `UserProfileSerializer` de `apps.users.serializers` | 2 archivos |
| H | `CustomTokenObtainPairSerializer` de `apps.authentication.serializers` | 1 archivo |
| I | `format_phone` de `apps.utils.formatters`, módulo `apps.utils.network` | 2 archivos |

### ⚠️ SOBRA (archivos que deberían eliminarse o reorganizarse)

| Archivo | Problema |
|---|---|
| `tests/conftest_COMPLETE.py` | Zombie — no cargado por pytest, contiene modelos IVR inexistentes |
| `tests/unit/core/test_core_serializers_OLD.py` | Duplicado de `test_core_serializers.py` |
| `tests/factories/ivr_factories.py` | Todo comentado — DEUDA TÉCNICA, pero el `__init__` podría exportarlo vacío |

---

## 8. RECOMENDACIONES

### Inmediatas (errores en colección)

Los 20 archivos con error representan **tests escritos para código que no
existe aún** o que fue reorganizado. Opciones:

1. **Marcar como DEUDA TÉCNICA** con el mismo patrón que IVR:
   comentar el contenido y dejar nota de qué símbolo falta.
2. **Corregir los imports** si los símbolos existen bajo otro nombre.
3. **Eliminar** si los tests ya no son relevantes.

### Limpieza estructural

1. **Eliminar** `tests/conftest_COMPLETE.py` — es ruido, no tiene función.
2. **Eliminar** `tests/unit/core/test_core_serializers_OLD.py` — duplicado.
3. **Evaluar** si los 4 archivos JSON en `tests/fixtures/` se usan en algún test
   (`pytest.mark.django_db` con `fixtures=[...]`). Si no, son datos muertos.

### `pytest.ini`

El archivo está **bien configurado** salvo:
- `testpaths = tests apps` es válido pero implícitamente mezcla dos culturas
  de testing (tests aislados en `tests/` vs tests embebidos en `apps/`).
  Considerar documentar esta decisión.

---

*Análisis generado: 2026-03-21*
*Basado en: pytest --collect-only, inspección de 39+ archivos*
