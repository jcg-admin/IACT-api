# Hallazgos — Implementación FASE 4

**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Alcance:** FASE 4 del plan PLAN-ACTUALIZACION-COMPLETO-20260513185000.md
**Objetivo:** Nuevos endpoints para tres objetos implementados en IACT-db sin exposición en IACT-api
**Commit:** `01b4f84`
**Impacto:** 7 archivos modificados, 294 líneas agregadas

---

## Resumen de tareas ejecutadas

| Tarea | Descripción | Archivos | Estado |
|---|---|---|---|
| T4.1 | `AbandonmentSummaryView` → `sp_rpt_resumen_abandono_rollup` | `ivr_services.py`, `ivr_views.py`, `reports/urls.py` | COMPLETO |
| T4.2 | `PipelineEventLogView` → `pipeline_event_log` (UC_LOG_08) | `logs/views.py`, `logs/urls.py` | COMPLETO |
| T4.3 | `etl_performance` → `v_etl_rendimiento` | `pipeline/views.py`, `pipeline/urls.py` | COMPLETO |

---

## H-F4-001 — `sp_rpt_resumen_abandono_rollup` no acepta `p_segmento` — diferencia con otros SPs

**Severidad:** Informativo — determinó el diseño de la view.
**Estado:** Documentado, considerado en implementación.

Todos los SPs de reporte existentes en `ivr_services.py` aceptan dos parámetros: `p_quarter` y `p_segmento`. El nuevo SP `sp_rpt_resumen_abandono_rollup` solo acepta `p_quarter` y retorna los tres segmentos en una sola llamada con `WITH ROLLUP`.

Esta diferencia es intencional por diseño del SP en IACT-db. El SP documenta:

> "Diseñado para uso desde Django sin parámetro de segmento: el SP siempre devuelve la jerarquía completa de los 3 segmentos."

La view `AbandonmentSummaryView` no expone `segment` como query parameter. Si se agregara en el futuro, el SP habría que cambiarlo también en IACT-db — decisión coordinada.

La validación en `AbandonmentSummaryView` usa `_validate(quarter=quarter)` sin `segment=`, coherente con la firma del SP.

---

## H-F4-002 — `logs/views.py` no tenía `connections` ni `OperationalError` como imports top-level

**Severidad:** MEDIA — el código hubiera fallado con `NameError` en la primera llamada.
**Estado:** CORREGIDO en implementación.

Las views existentes en `logs/views.py` (`ETLLogTailView`, `LogMetricsView`) importan `connections` y `OperationalError` localmente dentro de los métodos `get()`:

```python
def get(self, request):
    from django.db import connections, OperationalError  # local import
```

La nueva `PipelineEventLogView` usa `connections` y `OperationalError` directamente en el cuerpo del método sin import local. Al agregar el código con append, se detectó que el archivo no tenía estos imports top-level.

Se agregó el import al bloque de imports del módulo:

```python
from django.conf import settings
from django.db import connections, OperationalError   # ← agregado
```

Esto también simplifica las views existentes que podrían migrar de import local a top-level en un refactor futuro, aunque eso está fuera del scope de FASE 4.

---

## H-F4-003 — `pipeline_event_log` requiere validación de enums antes de ejecutar SQL

**Severidad:** Informativo — determina la robustez del endpoint.
**Estado:** Implementado correctamente.

Las columnas `error_type` y `severity` de `pipeline_event_log` son `ENUM` en MariaDB. Si Django pasa un valor inválido en un `WHERE error_type = %s`, MariaDB retorna 0 filas silenciosamente en lugar de error. Un cliente con un typo obtendría una respuesta vacía sin feedback.

`PipelineEventLogView` valida los enums antes de ejecutar la query:

```python
valid_error_types = {
    'PARAM_INVALIDO', 'ETL_FALLO', 'ETL_PARTIAL',
    'VALIDACION', 'REPORTE_VACIO', 'SISTEMA',
}
valid_severities = {'CRITICA', 'ALTA', 'MEDIA', 'BAJA', 'INFO'}

if error_type and error_type not in valid_error_types:
    param_errors.append(...)
```

Retorna HTTP 400 con lista de errores si cualquier enum es inválido. Consistente con el patrón de `_validate()` en `ivr_views.py`.

---

## H-F4-004 — `v_etl_rendimiento` filtra `status='SUCCESS'` en la vista de MariaDB — no en Django

**Severidad:** Informativo — documenta una decisión de diseño de IACT-db con impacto en IACT-api.
**Estado:** Documentado.

La vista `v_etl_rendimiento` en MariaDB tiene `WHERE status = 'SUCCESS'` en su definición:

```sql
FROM job_execution_log
WHERE status = 'SUCCESS'
```

El SP documenta:

> "Filtro WHERE status='SUCCESS': excluye FAILED y PARTIAL intencionalmente — duracion_seg de una ejecución interrumpida no es representativa del tiempo real del paso y contaminaría el cálculo de delta_seg con valores artificialmente bajos."

`etl_performance` no agrega filtro de status adicional — la vista de MariaDB ya lo aplica. El endpoint no expone `status` como parámetro de filtro, lo que sería redundante. Si en el futuro se necesita ver ejecuciones FAILED, se requeriría un nuevo SP o vista en IACT-db — no un cambio en IACT-api.

---

## H-F4-005 — RBAC: no existen funciones específicas para los nuevos endpoints

**Severidad:** BAJA — los endpoints reutilizan funciones RBAC existentes apropiadas.
**Estado:** Documentado — decisión consciente, no deuda técnica.

El plan proponía crear funciones RBAC nuevas. Al revisar el catálogo, los endpoints nuevos se alinean con funciones existentes:

| Endpoint | Función RBAC | Justificación |
|---|---|---|
| `ivr/abandonment-summary/` | `reports.view_ivr` | Es un reporte IVR, igual que los 8 existentes |
| `logs/pipeline-events/` | `logs.view` | Es un log del sistema, igual que UC_LOG_01..07 |
| `pipeline/performance/` | `pipeline.view_status` | Es observabilidad del pipeline, mismo cluster que UC_PIP_01 |

Crear funciones RBAC nuevas (`pipeline.view_performance`, `logs.view_pipeline_events`) sería correcto en términos de granularidad, pero requiere:
1. Agregar las funciones al catálogo en `create_functions.py`
2. Asignarlas a los grupos de acceso correspondientes en `create_mod_calls_functions.py`
3. Ejecutar los management commands en producción

Dado que estos tres endpoints son de solo lectura y están dentro del scope de sus módulos existentes, reutilizar las funciones existentes es la decisión pragmática correcta. Si el proyecto requiere granularidad más fina en el futuro, las funciones específicas pueden agregarse sin cambios en el código de views.

---

## Especificación de los 3 endpoints implementados

### `GET /api/reports/ivr/abandonment-summary/`

```
Parámetros:  quarter (str, required)
RBAC:        reports.view_ivr
SP:          sp_rpt_resumen_abandono_rollup(p_quarter)
Columnas:    segmento, menu, abandonadas, pct_del_quarter
Filas:       ~13 (WITH ROLLUP: detalle + subtotal/segmento + grand total)
HTTP 400:    quarter no disponible en base_ivr_detalle
HTTP 503:    MariaDB no disponible
```

### `GET /api/logs/pipeline-events/`

```
Parámetros:  quarter (str, opt), error_type (enum, opt), severity (enum, opt),
             hours (int, opt, default 48, máx 168),
             page_size (int, opt, default 20, máx 100)
RBAC:        logs.view
Tabla:       pipeline_event_log
Columnas:    id, ts, error_type, severity, sp_nombre, sql_state,
             mysql_errno, p_quarter, p_segmento, error_message (máx 500 chars),
             job_log_id, ejecutado_por
HTTP 400:    error_type o severity con valor inválido
HTTP 503:    MariaDB no disponible
```

### `GET /api/pipeline/performance/`

```
Parámetros:  step_name (str, opt), limit (int, opt, default 50, máx 200)
RBAC:        pipeline.view_status
Vista:       v_etl_rendimiento
Columnas:    job_name, quarter_name, step_name, status, start_time,
             duracion_seg, duracion_anterior_seg, delta_seg
Nota:        delta_seg > 0 = regresión, < 0 = mejora, NULL = primera ejecución
HTTP 503:    MariaDB no disponible
```

---

## Estado final de FASE 4

| Indicador | Valor |
|---|---|
| Archivos modificados | 7 |
| Líneas agregadas | 294 |
| Nuevas funciones en ivr_services.py | 1 (`get_abandonment_summary`) |
| Nuevas views | 2 (`AbandonmentSummaryView`, `PipelineEventLogView`) |
| Nuevas funciones de vista | 1 (`etl_performance`) |
| Nuevas rutas registradas | 3 |
| Errores de sintaxis | 0 |
| Deuda técnica generada | Ninguna |
| Hallazgos no previstos | 2 (H-F4-002 import faltante, H-F4-003 validación de enums) |
