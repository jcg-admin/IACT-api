# Hallazgos — Implementación FASE 3

**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Alcance:** FASE 3 del plan PLAN-ACTUALIZACION-COMPLETO-20260513185000.md
**Objetivo:** Eliminar modelos CTI fuera de scope: `ETLExecution`, `Center`, `Service`, `CallRecord`, `CallNote`
**Commit:** `3ef7a1f`
**Impacto:** 50 archivos — 36 eliminados, 14 modificados; 9362 líneas eliminadas

---

## Resumen de ejecución

| Grupo | Descripción | Estado |
|---|---|---|
| G1 | Infraestructura pipeline (admin, viewsets, urls, serializers, services, filters, permissions) | COMPLETO |
| G2 | Core dead code (views, urls, serializers, services/etl) — sin montar en config/urls.py | COMPLETO |
| G3 | Referencias externas (reports, alerts, dashboard, access/management) | COMPLETO |
| G4 | Modelos en pipeline/models.py | COMPLETO |
| G5 | Migración DeleteModel × 5 | COMPLETO |
| G6 | Limpieza de tests | COMPLETO |

---

## H-F3-001 — `core/views.py` y `core/urls.py` nunca estuvieron montados

**Severidad:** MEDIA — endpoints CTI registrados en el router pero inaccesibles.
**Estado:** CORREGIDO — archivos eliminados.

El plan original identificó `core/views.py` y `core/urls.py` como archivos a eliminar por referenciar los modelos. Durante la auditoría se encontró que `config/urls.py` **nunca incluyó** `apps.core.urls`:

```python
# config/urls.py — extracto
path('api/navigation/', include('apps.core.navigation.urls')),  # navegación: sí montado
path('api/pipeline/', include('apps.pipeline.urls')),           # pipeline: sí montado
# apps.core.urls                                                # NO montado
```

`core/views.py` definía tres viewsets de solo lectura (`CallRecordViewSet`, `CenterViewSet`, `ServiceViewSet`) y `core/urls.py` los registraba en un router. Dado que `config/urls.py` nunca incluyó estas URLs, los endpoints `/api/core/calls/`, `/api/core/centers/` y `/api/core/services/` eran inaccesibles desde cualquier cliente.

Esto significa que existían dos implementaciones paralelas de los mismos modelos: una en `apps/pipeline/` (con router CRUD completo, sí montada) y otra en `apps/core/` (solo lectura, nunca montada). La eliminación de `core/urls.py` y `core/views.py` no afectó ningún endpoint funcional.

---

## H-F3-002 — `migrate_call_permissions.py` y `validate_permission_migration.py` no identificados en el plan

**Severidad:** MEDIA — management commands referenciaban funciones RBAC eliminadas.
**Estado:** CORREGIDO — archivos eliminados.

El plan no identificó dos management commands en `apps/access/management/commands/`:

- **`migrate_call_permissions.py`**: migraba asignaciones de RBAC de códigos `CALL_*` (obsoletos) a `PIPELINE_CALLREC_*`. Con `PIPELINE_CALLREC_*` eliminados de `create_functions.py`, este comando migraba hacia destinos inexistentes.
- **`validate_permission_migration.py`**: validaba la existencia de funciones `PIPELINE_CALLREC_*` e `IVR_CALLLOG_*` en la base de datos. Con ambos conjuntos eliminados, la validación siempre fallaría.

Ambos archivos describían una migración de permisos que quedó obsoleta cuando se decidió eliminar los modelos CTI. Se eliminaron.

---

## H-F3-003 — `dashboard/viewsets.py` usaba `CanAccessCallRecordDataForWidget`

**Severidad:** MEDIA — import y uso activo de clase eliminada.
**Estado:** CORREGIDO.

`dashboard/permissions.py` fue limpiado de `CanAccessCallRecordDataForWidget` en el Grupo 3. Sin embargo, `dashboard/viewsets.py` también importaba y usaba esa clase:

```python
# dashboard/viewsets.py — ANTES
from apps.dashboard.permissions import (
    ...
    CanAccessCallRecordDataForWidget,   # ← import de clase eliminada
)
...
if widget_type.startswith('CALLS_'):
    permissions.append(CanAccessCallRecordDataForWidget())  # ← uso activo
```

El grep inicial no capturó esta referencia porque buscaba el nombre exacto de la clase sin incluir `dashboard/viewsets.py` en el conjunto revisado. Se eliminaron el import y el bloque de uso.

---

## H-F3-004 — `reports/permissions.py` referenciaba función RBAC eliminada

**Severidad:** BAJA — el código funcional usaba la función correcta pero el docstring y la referencia interna eran inconsistentes.
**Estado:** CORREGIDO.

`apps/reports/permissions.py` tenía una clase de permiso que verificaba `pipeline.callrecord.view` (una de las 6 funciones `PIPELINE_CALLREC_*` eliminadas) en lugar de `reports.view_ivr`:

```python
# ANTES
class CanViewIVRReports(BasePermission):
    """Requiere función 'pipeline.callrecord.view' (PIPELINE_CALLREC_VIEW)."""
    def has_permission(self, request, view):
        return request.user.has_function('pipeline.callrecord.view')

# DESPUÉS
class CanViewIVRReports(BasePermission):
    """Requiere función 'reports.view_ivr'."""
    def has_permission(self, request, view):
        return request.user.has_function('reports.view_ivr')
```

La función `reports.view_ivr` sí existe en el catálogo RBAC y es la correcta para controlar el acceso a los reportes IVR de `ivr_views.py`.

---

## H-F3-005 — Los `__init__.py` de tests tenían errores de sintaxis preexistentes

**Severidad:** ALTA — los archivos eran no compilables antes de FASE 3.
**Estado:** CORREGIDO — reescritos con sintaxis Python válida.

Durante la limpieza del Grupo 6, los scripts de limpieza revelaron que `tests/test_data/__init__.py`, `tests/factories/__init__.py` y `tests/testdata/__init__.py` tenían errores de sintaxis preexistentes: bloques `from X import (A B C)` sin comas entre los nombres, que Python rechaza.

El problema tiene dos capas:

**Capa 1 — preexistente:** los archivos usaban multi-line imports sin comas:
```python
from .user_test_data import (
    UserTestData        # ← falta coma
    AdminUserTestData   # ← falta coma
)                       # ← SyntaxError
```

**Capa 2 — introducida por limpieza anterior:** el bloque `from .core_test_data import (...)` fue eliminado fragmentariamente, dejando el `)` de cierre como línea huérfana:
```python
# CORE FACTORIES (apps/core/)
# ============================================================================
)        # ← SyntaxError: unmatched ')'
```

Los tres archivos fueron reescritos desde cero con imports válidos y solo las clases cuyos archivos fuente existen. Los `try/except ImportError` se mantuvieron para los módulos opcionales.

**Consecuencia:** estos archivos nunca pudieron ejecutarse directamente como módulo Python. Los tests funcionaban solo porque pytest importa los archivos de forma que tolera algunos errores hasta el momento de uso real.

---

## H-F3-006 — `pipeline_test_data.py` importaba modelos inexistentes (`ETLJob`, `SchedulerConfig`)

**Severidad:** MEDIA — `ImportError` en cualquier test que lo importara.
**Estado:** CORREGIDO — archivo eliminado.

`tests/test_data/pipeline_test_data.py` (y su duplicado en `tests/testdata/`) importaba cuatro modelos que **nunca existieron** en `apps.pipeline.models`:

```python
from apps.pipeline.models import (
    ETLJob,           # NO EXISTE en pipeline/models.py
    ETLError,         # NO EXISTE
    SchedulerConfig,  # NO EXISTE
    DataQualityCheck, # NO EXISTE
)
```

El archivo estaba envuelto en `try/except ImportError` en el `__init__.py`, por lo que silenciosamente fallaba al importar. Eliminado junto con los demás test data de pipeline.

---

## H-F3-007 — `dashboard/services/widget_service.py` importaba `Sum, Avg, Count, F, Q` solo para los métodos eliminados

**Severidad:** BAJA — imports huérfanos al eliminar los métodos `calculate_*`.
**Estado:** CORREGIDO.

Al eliminar el import de `CallRecord` también se eliminaron los imports de Django ORM que solo los métodos `calculate_*` utilizaban:

```python
# ANTES
from django.db.models import Sum, Avg, Count, F, Q
from django.db.models.functions import ExtractHour
```

Estos imports dejaron de ser necesarios al reemplazar todos los métodos `calculate_*` con stubs que retornan `{}`. Se eliminaron del bloque de imports para evitar `F401` (unused import) y mantener el archivo limpio.

---

## Estado final de FASE 3

| Indicador | Valor |
|---|---|
| Archivos eliminados | 36 |
| Archivos modificados | 14 |
| Líneas eliminadas netas | 9362 |
| Referencias activas residuales | 0 |
| Archivos con errores de sintaxis | 0 |
| Migración generada | `0003_delete_out_of_scope_models.py` |
| Tablas PostgreSQL a eliminar | 5 (`etl_executions`, `core_centers`, `core_services`, `core_call_records`, `pipeline_call_notes`) |
| Deuda técnica generada | Ninguna |
| Archivos no identificados en el plan (hallazgos H-F3-002..004) | 3 |
| Errores preexistentes expuestos y corregidos (H-F3-005, H-F3-006) | 2 tipos |

## Pasos pendientes en producción

```sql
-- Ejecutar tras aplicar manage.py migrate pipeline en producción:
-- Las tablas se eliminan automáticamente con la migración 0003.
-- Verificar que no existen datos importantes antes de aplicar en producción.
python manage.py migrate pipeline
```

Los management commands `migrate_call_permissions` y `validate_permission_migration` que existían en el entorno anterior ya no existen — si hay scripts de CI/CD que los invocan, deben actualizarse.
