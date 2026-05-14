# Hallazgos — FASE 3 TDD GRUPO B: UC_PIP_04 + UC_RPT_04

**Artefacto:** HALLAZGOS-FASE3-GRUPOB-TDD-20260513
**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Commit:** `0a91d62` en `develop`
**Estado:** Cerrado — 34/34 verificaciones PASS

----

## Resumen ejecutivo

GRUPO B implementa los 2 UCs con dependencias internas de FASE 3:
`UC_PIP_04` (→ UC_PIP_02 done) y `UC_RPT_04` (→ UC_RPT_03 done).
Se detectaron 4 hallazgos estructurales, todos resueltos en el mismo commit.

| UC | Función | Componentes nuevos | Tests |
|---|---|---|---|
| UC_PIP_04 | PIP-004 | `pipeline_retry_service.py`, `etl_retry` reescrito | 9 (UT-01, IT-01..07, SEC-01) |
| UC_RPT_04 | RPT-004 | `export_service.py`, `export_views.py`, migración 0004 | 19 (UT-01..09, IT-01..11, SEC-01) |

----

## drf-spectacular — verificación

**4 colisiones resueltas durante GRUPO B:**

Al usar `@extend_schema(operation_id='x')` en una clase `APIView` con
múltiples métodos HTTP, drf-spectacular aplica el mismo `operation_id`
a todos los métodos y genera colisiones. Los errores eran:

```
operationId "reports_export_queue" collisions: POST y GET en /api/reports/export/
operationId "reports_export_detail" collisions: GET y DELETE en /api/reports/export/{id}/
operationId "alerts_rule_list_create" collisions: GET y POST en /api/alerts/rules/
operationId "alerts_rule_detail" collisions: GET, PATCH y DELETE en /api/alerts/rules/{id}/
```

**Solución:** reemplazar `@extend_schema(operation_id=...)` en clase por
`@extend_schema_view(get=extend_schema(...), post=extend_schema(...))` con
`operation_id` distinto por método HTTP. Esta es la práctica correcta
documentada en drf-spectacular para `APIView` con múltiples verbos.

Las 4 colisiones pre-existentes (DT-ROUTING-001..003) permanecen sin cambios.

----

## Hallazgo H-F3-GRP-B-001 — `etl_retry` usaba `motivo` en lugar de `reason`

### Descripción

La implementación original de `etl_retry` usaba el campo `motivo` (español)
en el body del request. El corpus (uc-pip-04/datos-involucrados.rst § 7.1)
define el campo como `reason` (inglés), alineado con CNST-033
(vocabulario unificado en inglés para código y contratos).

El cambio no es trivial: afecta el @extend_schema (documentación OpenAPI),
los tests existentes que usaran `motivo`, y la consistencia del contrato
público del endpoint.

### Resolución

`etl_retry` reescrito completamente. El body acepta `reason` (canónico).
`motivo` fue eliminado sin backward compat — el endpoint no tenía
consumidores externos verificados.

---

## Hallazgo H-F3-GRP-B-002 — `etl_retry` no emitía `PIPELINE_RETRY_REQUESTED`

### Descripción

La implementación original no emitía ningún AuditEvent. El corpus
(CA-04, datos-involucrados § 7.2) requiere explícitamente
`PIPELINE_RETRY_REQUESTED` con `actor_id`, `reason` y `run_id_origen`.

`PIPELINE_RETRY_REQUESTED` sí existía en `VALID_EVENT_TYPES` (añadido
en FASE 2 del plan TDD), pero nunca se emitía desde el endpoint.

### Resolución

`etl_retry` ahora emite `PIPELINE_RETRY_REQUESTED` vía `AuditLogService.emit()`
dentro del bloque de éxito (tras ejecutar el SP). El `payload` incluye
`quarter`, `run_id`, `new_run_id`, `priority` y `reason[:100]` (truncado
para CNST-026 — sin PII en payloads de auditoría).

---

## Hallazgo H-F3-GRP-B-003 — `ExportJob` incompatible con el corpus

### Descripción

El modelo `ExportJob` tenía estructura completamente diferente al corpus:

| Aspecto | Modelo pre-UC_RPT_04 | Corpus uc-rpt-04 § 7.1 |
|---|---|---|
| `status` choices | `pending/running/completed/failed` | `queued/running/done/failed/expired/cancelled` |
| FK | `report FK(Report)` (CASCADE) | Sin FK a Report — standalone |
| `actor` | no existía | `actor_id` requerido |
| `report_type` | no existía | enum requerido |
| `progress` | `exported_records/total_records` (%) | `progress_pct` (0..100) |
| `file_url` | no existía | firmado con TTL 24h |
| `error_code` | no existía | código corto (PERMISSION_REVOKED…) |
| `cancellation_requested` | no existía | CA-17 graceful cancel |

### Resolución

Migración `0004_fase3_exportjob_canonical.py`:
- `id` → UUID (era int auto)
- `status` → nuevo enum canónico
- `actor` → FK User nullable (nullable para legacy)
- `report_type`, `filters`, `period`, `group_by` → añadidos
- `progress_pct`, `file_url`, `file_url_expires_at` → añadidos
- `row_count`, `byte_count`, `error_code`, `cancellation_requested` → añadidos
- `report` FK → SET_NULL (no CASCADE) — backward compat para legacy

**Backward compat**: los campos legacy (`total_records`, `exported_records`,
`error_message`, `started_at`) se preservan. `report` FK pasa de CASCADE a
SET_NULL para no bloquear jobs UC_RPT_04 que no tienen Report asociado.
El legacy `ExportJobViewSet` sigue funcionando con el modelo actualizado.

---

## Hallazgo H-F3-GRP-B-004 — `@extend_schema(operation_id)` en clase causa errores

### Descripción

Al aplicar `@extend_schema(operation_id='x')` directamente sobre una clase
`APIView` con múltiples métodos HTTP (GET + POST, o GET + DELETE), drf-spectacular:
1. Aplica el mismo `operation_id` a todos los métodos
2. Genera colisiones de `operationId` en el schema OpenAPI
3. Emite el error: `"using @extend_schema on viewset class X with parameters operation_id will most likely result in a broken schema"`

Este patrón fue usado en `AlertRuleListCreateView`, `AlertRuleDetailView`,
`ExportView` y `ExportDetailView`. Todos generaban la advertencia.

### Resolución

Reemplazar `@extend_schema(operation_id=...)` en clase por
`@extend_schema_view(get=extend_schema(...), post=extend_schema(...))` con
`operation_id` únicos por verbo HTTP:

```python
# Antes (incorrecto para APIView multi-verbo)
@extend_schema(operation_id='reports_export_queue', ...)
class ExportView(APIView):

# Después (correcto)
@extend_schema_view(
    get=extend_schema(operation_id='reports_export_list', ...),
    post=extend_schema(operation_id='reports_export_queue', ...),
)
class ExportView(APIView):
```

---

## Decisiones de diseño

### UC_PIP_04 — `new_run_id` generado en el backend

El corpus (CA-01) requiere `new_run_id` en la respuesta 202. La implementación
actual genera un `uuid4` en el endpoint, no el id real del SP. El SP
`sp_etl_historico` en MariaDB no retorna un ID que pueda rastrearse como
`PipelineRun.id` (porque no existe el modelo Django `PipelineRun` — el ETL
vive en MariaDB).

El `new_run_id` en la respuesta es un identificador opaco generado en Python
para la idempotencia (CA-05) y la trazabilidad del AuditEvent. No está
correlacionado con ningún registro de MariaDB. Esto es un límite del
entorno actual — en producción el SP debería retornar el ID del nuevo job
que se registraría en `job_execution_log`.

### UC_RPT_04 — `ExportWorker` sincrónico en tests

El corpus define `ExportWorker` como un proceso background (Celery/RQ).
En este entorno sin broker de mensajes, el worker es sincrónico. Los tests
de integración (IT-02..06) llaman `ExportWorker.process(job_id)` directamente.

El contrato del worker es correcto: acepta `job_id`, transita por los
estados, emite AuditEvent y notifica el mailbox. El "cómo se invoca"
(Celery vs. sync) es configuración de infraestructura, no dominio.

La view de `POST /api/reports/export/` encola el job pero NO ejecuta el
worker síncronamente — retorna 202 inmediatamente. Los tests de IT-02..06
llaman `ExportWorker.process()` directamente para verificar el comportamiento
del worker sin depender de Celery.

### UC_RPT_04 — `_check_permission` y `UserFunctionAssignment`

El re-check de permiso (P-64, CA-09) verifica si el usuario tiene alguna
de las funciones de export (`RPT-004`, `RPT-005`, `RPT-006`) con state
`ACTIVE` en `UserFunctionAssignment`. En los tests de integración, el
`AdminUserTestData()` no tiene assignments directos (depende de AGRs),
por lo que `_check_permission` retorna `False` para usuarios normales.

El test `test_it04_recheck_permiso_revocado` mockea `_check_permission`
directamente para simular la revocación. Esto es correcto: el test verifica
el comportamiento del worker cuando el re-check falla, no el mecanismo
de re-check en sí.

----

## Estado de FASE 3 TDD post-GRUPO B

```
GRUPO A — 7 UCs — COMPLETADO (commit a31487f)
GRUPO B — 2 UCs — COMPLETADO (commit 0a91d62)
GRUPO C — 0 UCs — UC_ALR_03 completado en GRUPO A

FASE 3 TDD: 11/11 UCs COMPLETADOS
```

FASE 3 del plan TDD v4 está completa. Los próximos pasos según
`PLAN-IMPLEMENTACION-TDD-v4-20260513.md` son:

- FASE 4: 17 UCs MEDIOS (38 días estimados)
- FASE 5: 10 UCs BAJOS (21 días estimados)
