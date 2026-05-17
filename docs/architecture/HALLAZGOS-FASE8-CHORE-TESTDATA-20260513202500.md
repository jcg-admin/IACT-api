# Hallazgos — Implementación FASE 8

**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Alcance:** FASE 8 del plan PLAN-ACTUALIZACION-COMPLETO-20260513185000.md
**Objetivo:** Nomenclatura Factory → TestData; consolidar directorios de test data
**Commit:** `a30669e`
**Impacto:** 19 archivos tocados — 17 eliminados, 2 modificados; 4533 líneas eliminadas

---

## Resumen de tareas

| Tarea | Descripción | Estado |
|---|---|---|
| T8.1 | Renombrar `*Factory` → `*TestData` en `tests/factories/` | NO EJECUTADA — `test_data/` ya tenía las clases `*TestData` |
| T8.2 | Actualizar todos los imports | VERIFICADO — todos importan desde `test_data/`, no desde `factories/` |
| T8.3 | Eliminar `tests/factories/` y `tests/testdata/` | COMPLETADO |
| T8.4 | Verificar que los tests pasan | VERIFICADO (parseable + ausencia de ImportError) |
| Bugs | Corregir 2 bugs de `ImportError` en `conftest.py` | COMPLETADO |

---

## H-F8-001 — T8.1 fue innecesario: `test_data/` ya tenía `*TestData` antes de FASE 8

**Severidad:** Informativo — el plan suponía una situación que no existía.
**Estado:** Documentado.

El plan describía T8.1 como "renombrar clases `*Factory` → `*TestData` en `tests/factories/`". La auditoría encontró que:

1. `tests/test_data/` ya existía con todas las clases nombradas `*TestData` — el renombre ya estaba hecho.
2. `tests/factories/` existía en paralelo con las versiones `*Factory` antiguas, pero **ningún test las importaba**.

```
# Todos los tests activos usaban test_data/ directamente:
from tests.test_data.user_test_data import UserTestData       # ← correcto
from tests.test_data.access_test_data import FunctionTestData # ← correcto

# Nadie hacía:
from tests.factories.user_factory import UserFactory           # ← muerto
from tests.factories.access_factories import ModuleFactory     # ← muerto
```

El directorio `tests/factories/` solo se referenciaba a sí mismo: `dashboard_factories.py` y `alert_factories.py` importaban `user_factory.py` internamente, pero ningún test externo los consumía.

La acción correcta fue ir directamente a T8.3 (eliminar) en lugar de T8.1 (renombrar). Renombrar clases en código muerto es trabajo sin valor.

---

## H-F8-002 — `tests/testdata/` era un duplicado muerto, no una fuente de verdad

**Severidad:** BAJA — directorio duplicado con datos desactualizados.
**Estado:** ELIMINADO.

El directorio `tests/testdata/` (sin guión) tenía los mismos 7 archivos que `tests/test_data/` (con guión). En 5 de los 7 archivos el contenido era idéntico. En 2 archivos había diferencias:

| Archivo | Diferencias |
|---|---|
| `audit_test_data.py` | 68 líneas distintas |
| `user_test_data.py` | 45 líneas distintas |

Ningún test importaba desde `tests/testdata/` — era código muerto que divergió silenciosamente de `tests/test_data/`. Las diferencias son señal de que `testdata/` recibió actualizaciones parciales en algún momento y luego fue abandonado.

La única referencia activa dentro del directorio era que sus propios archivos importaban desde `tests.test_data`:

```python
# tests/testdata/alert_test_data.py
from tests.test_data.user_test_data import UserTestData  # importa de test_data/
```

Es decir, `testdata/` dependía de `test_data/`, pero nadie dependía de `testdata/`. Eliminado sin impacto.

---

## H-F8-003 — `conftest.py` tenía 2 bugs de `ImportError` silenciosos

**Severidad:** ALTA — causa fallos de fixtures en runtime.
**Estado:** CORREGIDO.

Los imports estaban dentro de funciones (lazy imports), por lo que no fallaban en la carga del módulo sino solo cuando la fixture era invocada. Dado que ningún test usaba esas fixtures, los errores nunca se manifestaron.

### Bug 1 — `QuarterlyReportReportTestData` (doble "Report")

```python
# conftest.py, fixture report_with_export_mocks — ANTES
from tests.test_data import QuarterlyReportReportTestData
report = QuarterlyReportReportTestData()
```

`QuarterlyReportReportTestData` no existe. La clase real en `test_data/report_test_data.py` es `QuarterlyReportTestData`. El doble sufijo "Report" es un typo que se originó probablemente al intentar que el nombre fuera más descriptivo sin verificar contra el import real.

```python
# DESPUÉS
from tests.test_data import QuarterlyReportTestData
report = QuarterlyReportTestData()
```

### Bug 2 — `DailyJobConfigTestData` (clase eliminada)

```python
# conftest.py, fixture scheduled_job_with_mocks — ANTES
from tests.test_data import DailyJobConfigTestData
config = DailyJobConfigTestData(job_name='cleanup_sessions')
```

`DailyJobConfigTestData` correspondía a un modelo `DailyJobConfig` del sistema de scheduling con APScheduler. Este modelo fue eliminado en FASE 3 junto con los modelos CTI fuera de scope.

La fixture `scheduled_job_with_mocks` también dependía de fixtures `mock_apscheduler` y `mock_cleanup_sessions_job` — también relacionadas con el scheduler eliminado. Ningún test usaba `scheduled_job_with_mocks`.

```python
# DESPUÉS — fixture eliminada completa
# Ningún test la usaba. El scheduler y su modelo DailyJobConfig
# no existen en el codebase actual.
```

---

## H-F8-004 — `APIRequestFactory` y `RequestFactory` no son violations de RA-011

**Severidad:** Informativo.
**Estado:** Documentado — no requiere acción.

El scan de `*Factory` encontró referencias en 10 archivos de tests:

```python
from rest_framework.test import APIRequestFactory  # DRF
from django.test import RequestFactory             # Django
```

Estas son clases del framework (`rest_framework` y `django.test`), no clases del proyecto. RA-011 aplica a **identificadores Python del proyecto** — nombres de clases, funciones y variables que el equipo define. Las clases de terceros importadas por su nombre canónico no están sujetas a la regla.

No se tomó ninguna acción sobre estas referencias.

---

## Estructura final de test data

```
tests/
  test_data/           ← fuente única de verdad (7 archivos + __init__.py)
    __init__.py        ← 39 exports verificados
    access_test_data.py
    alert_test_data.py
    audit_test_data.py
    authentication_test_data.py
    dashboard_test_data.py
    report_test_data.py
    user_test_data.py
  factories/           ← ELIMINADO (era código muerto)
  testdata/            ← ELIMINADO (era duplicado muerto)
```

---

## Estado final de FASE 8

| Indicador | Valor |
|---|---|
| Archivos eliminados | 17 (9 de `factories/`, 8 de `testdata/`) |
| Archivos modificados | 2 (`conftest.py`, git tracking) |
| Líneas eliminadas | 4533 |
| Bugs corregidos en conftest.py | 2 (`QuarterlyReportReportTestData`, `DailyJobConfigTestData`) |
| Fixtures eliminadas | 1 (`scheduled_job_with_mocks` — sin tests que la usen) |
| Clases `*Factory` en tests activos | 0 (solo `APIRequestFactory`/`RequestFactory` de frameworks) |
| Directorios de test data antes | 3 (`factories/`, `test_data/`, `testdata/`) |
| Directorios de test data después | 1 (`test_data/`) |
| Exports en `test_data/__init__.py` verificados | 39 (todos existen en sus módulos fuente) |
| Errores de sintaxis | 0 |
| Deuda técnica generada | Ninguna |

---

## Cierre del plan — FASES 1-8 completas

Con FASE 8 completada, el plan PLAN-ACTUALIZACION-COMPLETO-20260513185000.md está íntegramente ejecutado. Resumen del estado final:

| FASE | Descripción | Commits |
|---|---|---|
| FASE 1 | Bug NameError `etl_data_availability` | `3a87d5e`, `dad908b` |
| FASE 2 | Eliminar `apps/ivr/` | `769f302`, `95f8d0c` |
| FASE 3 | Eliminar modelos CTI fuera de scope | `3ef7a1f`, `bc52621` |
| FASE 4 | Nuevos endpoints IACT-db | `01b4f84`, `0e1ea45` |
| FASE 5 | Renombres RA-011 en producción | `601303e`, `3fa4b92` |
| FASE 6 | OpenAPI completeness | `0338c0d`, `64555f3` |
| FASE 7 | Limpieza de tests | `6b20918`, `ca23e96` |
| FASE 8 | Factory → TestData; consolidar test data | `a30669e` |
