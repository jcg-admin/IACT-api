# PLAN — Reparación del Sistema de Tests
## Basado en: ANALISIS_TESTS_ESTADO_20260321.md

**Versión:** 1.0.0
**Fecha:** 2026-03-21
**Objetivo:** Llevar los 20 archivos con ImportError a 0 errores de colección

---

## RESUMEN DE HALLAZGOS (investigación post-análisis)

| Grupo | Símbolo | ¿Existe? | Dónde | Acción |
|---|---|---|---|---|
| A | `CallRecord`, `Service` | ✅ Sí | `apps/pipeline/models.py` | Corregir import |
| B | `Role` | ❌ No | En ningún lado | Marcar deuda técnica |
| C | `HasModuleAccess` | ✅ Sí | `apps/access/permissions/module_permissions.py` (comentado en `__init__`) | Corregir import |
| D | `HasServiceAccess` | ❌ No | Eliminado deliberadamente (DT-002) | Marcar deuda técnica |
| E | `LoggingMiddleware` | ✅ Sí | `apps/core/middleware/logging.py` | Investigar por qué falla |
| F | `ServiceFilterMixin` | ❌ No | Eliminado deliberadamente (DT-002) | Marcar deuda técnica |
| G | `LoginSerializer`, `UserProfileSerializer` | ✅ Sí | `apps/users/serializers.py` | Investigar por qué falla |
| H | `CustomTokenObtainPairSerializer` | ✅ Sí | `apps/authentication/serializers.py` | Investigar por qué falla |
| I | `format_phone` | ❌ (es `format_phone_cl`) | `apps/utils/formatters.py` | Corregir nombre |
| I | módulo `apps.utils.network` | ❌ No | No existe | Marcar deuda técnica |

---

## FASES DEL PLAN

### FASE 1 — Limpieza inmediata (archivos zombie y duplicados)

**Objetivo:** Eliminar ruido sin afectar ningún test activo.

| Acción | Archivo | Justificación |
|---|---|---|
| Eliminar | `tests/conftest_COMPLETE.py` | Zombie — no cargado por pytest, 761 líneas de deuda |
| Eliminar | `tests/unit/core/test_core_serializers_OLD.py` | Duplicado exacto de `test_core_serializers.py` |

**Riesgo:** Ninguno. Ninguno de estos archivos es cargado por pytest actualmente (el conftest por nombre incorrecto, el OLD por ser duplicado del que también falla).

---

### FASE 2 — Corregir imports erróneos (símbolos que SÍ existen)

**Objetivo:** Corregir rutas de import sin cambiar lógica de tests.

#### 2.1 — Grupo A: `CallRecord` y `Service` → mover a `apps.pipeline.models`

**Archivos a editar:**
- `tests/unit/core/test_core_models.py`
- `tests/unit/core/test_core_serializers.py`
- `tests/unit/core/test_core_etl_service.py`

**Cambio:**
```python
# ANTES
from apps.core.models import CallRecord, Service

# DESPUÉS
from apps.pipeline.models import CallRecord, Service
```

**Nota:** `test_core_serializers_OLD.py` se elimina en Fase 1, no requiere corrección aquí.

#### 2.2 — Grupo C: `HasModuleAccess` → import directo desde submódulo

**Archivo a editar:**
- `tests/unit/access/test_permissions.py`

**Cambio:**
```python
# ANTES
from apps.access.permissions import HasModuleAccess

# DESPUÉS
from apps.access.permissions.module_permissions import HasModuleAccess
```

**Contexto:** El símbolo existe pero está comentado en `apps/access/permissions/__init__.py`
por deuda técnica pendiente de implementar `ModuleAccessService`. El import directo al submódulo evita el problema.

#### 2.3 — Grupo I (parcial): `format_phone` → `format_phone_cl`

**Archivo a editar:**
- `tests/unit/utils/test_formatters.py`

**Cambio:**
```python
# ANTES
from apps.utils.formatters import format_phone

# DESPUÉS
from apps.utils.formatters import format_phone_cl
```

**Nota:** También actualizar todas las referencias al nombre en el cuerpo del test.

---

### FASE 3 — Marcar como deuda técnica (símbolos eliminados deliberadamente)

**Objetivo:** Deshabilitar los tests que prueban código eliminado, documentando
la razón y el reemplazo esperado. Usar el mismo patrón ya establecido en el proyecto.

**Patrón a aplicar:**
```python
# DEUDA TÉCNICA 2026-03-21
# Este módulo prueba [símbolo] que fue eliminado en [referencia].
# Razón: [razón del análisis]
# Reemplazo: [qué usar en su lugar]
# TODO: Reescribir usando [nuevo enfoque] cuando se implemente.

import pytest
pytestmark = pytest.mark.skip(reason="DEUDA TÉCNICA: [símbolo] eliminado — ver comentario de archivo")
```

**Archivos a marcar:**

| Archivo | Símbolo | Referencia eliminación |
|---|---|---|
| `tests/unit/core/test_service_access.py` | `ServiceFilterMixin` + `HasServiceAccess` | DT-002 / `apps/core/mixins.py` líneas 114-124 |
| `tests/unit/core/test_permissions.py` | `HasServiceAccess` | DT-002 / `apps/core/permissions.py` líneas 264-282 |
| `tests/unit/authentication/test_models.py` | `Role` | No existe en `apps.access.models` |
| `tests/integration/authentication/test_auth_flow.py` | `Role` | No existe en `apps.access.models` |
| `tests/integration/authentication/test_recovery_flow.py` | `Role` | No existe en `apps.access.models` |
| `tests/integration/authentication/test_session_flow.py` | `Role` | No existe en `apps.access.models` |
| `tests/unit/utils/test_utils_network.py` | módulo `apps.utils.network` | Módulo nunca creado |

---

### FASE 4 — Investigar y corregir imports que "deberían funcionar"

**Objetivo:** Los Grupos E, G, H tienen sus símbolos en el lugar correcto pero
aún fallan en colección. Determinar la causa raíz (import circular, dependencia
en `__init__`, etc.) y corregir.

**Archivos a diagnosticar:**

| Archivo | Import | Estado |
|---|---|---|
| `tests/unit/core/test_middleware.py` | `from apps.core.middleware.logging import LoggingMiddleware` | Símbolo existe — causa desconocida |
| `tests/unit/users/test_auth_serializers.py` | `from apps.users.serializers import LoginSerializer` | Símbolo existe — causa desconocida |
| `tests/unit/users/test_serializers.py` | `from apps.users.serializers import UserProfileSerializer` | Símbolo existe — causa desconocida |
| `tests/unit/authentication/test_serializers.py` | `from apps.authentication.serializers import CustomTokenObtainPairSerializer` | Símbolo existe — causa desconocida |

**Método de diagnóstico:**
```bash
cd callcentersite
python -c "from apps.core.middleware.logging import LoggingMiddleware"
python -c "from apps.users.serializers import LoginSerializer"
python -c "from apps.authentication.serializers import CustomTokenObtainPairSerializer"
```

Si los imports funcionan desde la REPL pero no en pytest, el problema es el contexto
de carga (settings, apps no inicializadas, etc.).

---

### FASE 5 — Evaluar fixtures JSON sin uso

**Objetivo:** Determinar destino de los 4 archivos JSON en `tests/fixtures/`.

**Archivos:**
- `tests/fixtures/sample_data.json`
- `tests/fixtures/initial_modules.json`
- `tests/fixtures/reports_rbac.json`
- `tests/fixtures/modules.json`

**Hallazgo:** Ninguno es referenciado en ningún test Python (0 referencias encontradas).

**Opciones:**
1. **Eliminar** si son datos de migración/seed que ya se aplicaron
2. **Documentar** si son fixtures de referencia para futuros tests
3. **Integrar** si algún test debería estar usando `@pytest.mark.django_db(fixtures=[...])`

**Decisión requerida:** Requiere revisión humana del contenido de cada JSON.

---

## ORDEN DE EJECUCIÓN RECOMENDADO

```
Fase 1 → Fase 2 → Fase 3 → Fase 4 → Fase 5
```

**Criterio de éxito:** Después de Fase 3, el resultado de
`python -m pytest --collect-only -q` debe mostrar **0 errores de colección**.

**Métrica objetivo:**

| Métrica | Actual | Objetivo |
|---|---|---|
| Tests colectados | 625 | ~625 (sin cambio en tests activos) |
| Errores de colección | 20 | **0** |
| Tests skipped (deuda técnica) | 0 | ~7 nuevos |
| Tests corregidos (import fix) | 0 | ~3 archivos |

---

## ARCHIVOS NO MODIFICADOS

Los siguientes archivos **no se tocan** en este plan:

- `pytest.ini` — correcto, solo considerar documentar `testpaths`
- `tests/conftest.py` — funciona correctamente
- `tests/mocks/` — todos sin ImportError
- `tests/fixtures/*.py` — todos funcionales
- `apps/*/tests/` — colectan correctamente
- `tests/unit/ivr_legacy/` — 13/13 passing

---

*Plan generado: 2026-03-21*
*Basado en: ANALISIS_TESTS_ESTADO_20260321.md + investigación de símbolos*
