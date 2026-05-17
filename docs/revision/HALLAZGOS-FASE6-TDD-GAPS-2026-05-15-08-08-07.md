# Hallazgos — FASE 6: Implementación TDD de gaps IACT-db

**Artefacto:** HALLAZGOS-FASE6-TDD-GAPS-2026-05-15-08-08-07
**Versión:** 1.0.0
**Fecha:** 2026-05-15
**Commit:** `7f60e20` en `develop`
**Estado:** Cerrado — 0 deuda técnica activa

---

## Contexto

Análisis exhaustivo de `/tmp/references/IACT-db/` contra `/tmp/references/IACT-api/`
reveló 4 objetos de MariaDB `ivr_legacy` sin cobertura en la API.
Se implementaron con metodología TDD (Red → Green → Refactor) los 4 endpoints
correspondientes, añadiendo 37 tests nuevos.

El análisis confirmó además que:
- `UC_ALR_03` (Reconocer Alerta) estaba incorrectamente marcado como GAP en el documento
  anterior — la implementación es completa con `alert.save()` y `AuditLogService.emit()`.
- Los SPs de ETL internos (`sp_etl_base_detalle`, `sp_etl_base_clientes`, `sp_etl_validar`)
  no tienen endpoint propio porque son llamados exclusivamente por `sp_etl_maestro` — correcto.
- `evt_etl_diario` no está desplegado como evento MariaDB porque `event_scheduler=ON`
  no está activo en el sandbox. IACT-api lo suple con `APScheduler` en `scheduler.py`.

---

## Inventario completo de objetos ivr_legacy

| Objeto | Tipo | API antes | API después |
|---|---|---|---|
| `sp_etl_maestro` v2.5.0 | PROCEDURE | SI (`scheduler.py`, `run_etl.py`) | SI |
| `sp_etl_historico` | PROCEDURE | SI (`views.py`) | SI |
| `sp_etl_base_detalle` | PROCEDURE (interno) | NO — correcto | NO |
| `sp_etl_base_clientes` | PROCEDURE (interno) | NO — correcto | NO |
| `sp_etl_validar` | PROCEDURE (interno) | NO — correcto | NO |
| `sp_rpt_clientes` | PROCEDURE | SI (`ivr_services.py`) | SI |
| `sp_rpt_centros_transferencia` | PROCEDURE | SI | SI |
| `sp_rpt_llamadas_abandonadas` | PROCEDURE | SI | SI |
| `sp_rpt_menu_centro` | PROCEDURE | SI | SI |
| `sp_rpt_menu_redirigidos` | PROCEDURE | SI | SI |
| `sp_rpt_cMENU_ERROR` | PROCEDURE | SI | SI |
| `sp_rpt_centros_xsegmento` | PROCEDURE | SI | SI |
| `sp_rpt_resumen_abandono_rollup` v1.0.0 | PROCEDURE | SI (`AbandonmentSummaryView`) | SI |
| `v_etl_rendimiento` | VIEW | SI (`views.py:693`) | SI |
| `v_quarter_actual` | VIEW | SI (`dashboard_view.py`) | SI |
| `v_sla_distribucion` | VIEW | NO — GAP | **SI** (nuevo) |
| `v_eventos_recientes` | VIEW | NO — GAP | **SI** (nuevo) |
| `vw_monitor_dias_semana` | VIEW | NO — GAP | **SI** (nuevo) |
| `fn_did_segmento` y 6 más | FUNCTION (interna) | NO — correcto | NO |
| `evt_etl_diario` | EVENT | NO — APScheduler suple | NO |
| `job_config` | TABLE | NO — GAP | **SI** (nuevo) |
| `job_execution_log` | TABLE | SI (`views.py:66`) | SI |
| `pipeline_event_log` | TABLE | SI (`views.py:514`) | SI |
| `base_ivr_detalle` | TABLE | SI (`ivr_services.py`) | SI |
| `base_ivr_clientes` | TABLE | NO — acceso vía SPs | NO |
| `tbl_historico_tN_YYYY` | TABLE | NO — fuente ETL directa | NO |

Los SPs de reporte con `p_segmento` (`sp_rpt_centros_transferencia`, etc.) reciben
`[quarter, segmento]` desde `ivr_services.py` — las vistas de IACT-api invocan el SP
3 veces (una por segmento: `nacional_A`, `nacional_B`, `puebla`) y consolidan el resultado.

---

## H-GAP-001 — job_config sin endpoint de lectura ni escritura

### Descripción

La tabla `job_config` en `ivr_legacy` controla si el ETL nocturno se ejecuta:

```sql
SELECT job_name, is_enabled, timeout_seconds, ventana_inicio, ventana_fin
FROM job_config;
-- job_name='etl_diario'   is_enabled=1  timeout=1800  ventana=02:00-04:00
-- job_name='etl_historico' is_enabled=0  timeout=7200  ventana=02:00-04:00
```

Sin endpoint, la única forma de habilitar o deshabilitar el ETL era acceder
directamente a MariaDB, lo que viola el principio de gestión declarativa de la API.

### Corrección aplicada — UC_PIP_05

**Nuevos endpoints:**

```
GET  /api/pipeline/job-config/             PIP-001  lista de jobs
GET  /api/pipeline/job-config/{job_name}/  PIP-001  detalle
PATCH /api/pipeline/job-config/{job_name}/ PIP-005  habilitar/deshabilitar
```

**Regla de negocio BR-ETL-01:** solo `is_enabled` y `notas` son modificables via API.
`timeout_seconds`, `ventana_inicio`, `ventana_fin` y `min_intervalo_h` requieren
despliegue de BD (cambios operacionales de infraestructura).

**Nueva función RBAC:** `PIP-005` `manage_pipeline_config` — separada de `PIP-001`
para respetar el principio de menor privilegio.

**Evento de auditoría:** `JOB_CONFIG_UPDATED` registrado en `AuditLog` al cambiar
`is_enabled`, incluyendo actor y valor anterior/nuevo.

**Archivo:** `apps/pipeline/job_config_views.py`

### Tests TDD (13 tests)

```
TestJobConfigList:
  test_it01_lista_todos_los_jobs
  test_it02_retorna_estado_general
  test_it03_mariadb_no_disponible_retorna_503
  test_sec01_sin_permiso_retorna_403

TestJobConfigDetail:
  test_it01_detalle_job_existente
  test_it02_job_inexistente_retorna_404

TestJobConfigUpdate:
  test_it01_deshabilitar_job_retorna_200
  test_it02_habilitar_job_retorna_200
  test_it03_patch_notas_permitido
  test_it04_patch_timeout_rechazado          ← BR-ETL-01
  test_it05_patch_sin_campos_validos_400
  test_it06_audit_emitido_al_cambiar_estado
  test_sec01_sin_permiso_escritura_403
```

---

## H-GAP-002 — v_eventos_recientes sin endpoint

### Descripción

La vista `v_eventos_recientes` enriquece `pipeline_event_log` con un JOIN a
`job_execution_log`, añadiendo el contexto del job que originó cada evento:
`job_status`, `job_step`, `job_inicio`. Sin endpoint, la trazabilidad de errores
del pipeline requería consultas manuales a la BD.

```sql
-- v_eventos_recientes — columnas relevantes
id, ts, error_type, severity, sp_nombre, sql_state,
p_quarter, p_segmento, error_resumen, ejecutado_por,
job_status, job_step, job_inicio
```

`pipeline_event_log` tenía 10 filas en el sandbox con errores reales de pruebas.

### Corrección aplicada — UC_PIP_02 extensión

**Nuevo endpoint:**

```
GET /api/pipeline/events/          PIP-002
  ?severity=CRITICA|ALTA|MEDIA|BAJA|INFO
  ?error_type=ETL_FALLO|PARAM_INVALIDO|VALIDACION|...
  ?limit=N  (default 50, max 200)
```

Diferencia con el endpoint existente `GET /api/pipeline/errors/` (que lee
`pipeline_event_log` directamente): este endpoint usa `v_eventos_recientes`
que incluye el contexto del job via JOIN.

**Archivo:** `apps/pipeline/pipeline_event_views.py`

### Tests TDD (8 tests)

```
TestPipelineEventsEndpoint:
  test_it01_lista_eventos_recientes
  test_it02_filtra_por_severity
  test_it03_filtra_por_error_type
  test_it04_sin_eventos_retorna_lista_vacia
  test_it05_incluye_contexto_job
  test_it06_mariadb_no_disponible_retorna_503
  test_it07_limit_defecto_50
  test_sec01_sin_permiso_retorna_403
```

---

## H-GAP-003 — v_sla_distribucion sin endpoint

### Descripción

La vista `v_sla_distribucion` clasifica centros de transferencia por categoría SLA
por trimestre usando un PIVOT emulado con `SUM(CASE WHEN)`:

```
trimestre | fuera_sla | riesgo_sla | dentro_sla | activo_hoy | volumen_medio | bajo_volumen | total_centros
Q01_25    |    24     |     0      |     0      |     0      |      36       |     24       |     84
Q02_25    |    23     |     0      |     0      |     0      |      42       |     26       |     91
Q02_26    |    18     |     4      |     2      |     1      |      38       |     21       |     84
```

Sin endpoint, el dashboard ejecutivo de compliance SLA no tenía fuente de datos.

### Corrección aplicada

**Nuevo endpoint:**

```
GET /api/reports/ivr/sla/     RPT-019  view_ivr_reports
  ?quarter=Q0N_YY  (opcional — filtra por trimestre)
```

**Validación:** `quarter` debe cumplir `^Q0[1-4]_\d{2}$` — `400` si inválido.

**Serialización:** `Decimal` se convierte a `float` para compatibilidad JSON.

**Archivo:** `apps/reports/sla_views.py`

### Tests TDD (8 tests)

```
TestSLADistribucionEndpoint:
  test_it01_retorna_todos_los_trimestres
  test_it02_filtra_por_trimestre
  test_it03_quarter_invalido_retorna_400
  test_it04_sin_datos_retorna_lista_vacia
  test_it05_incluye_resumen_global
  test_it06_mariadb_no_disponible_retorna_503
  test_it07_valores_decimales_serializables
  test_sec01_sin_permiso_retorna_403
```

---

## H-GAP-004 — vw_monitor_dias_semana sin endpoint

### Descripción

La vista `vw_monitor_dias_semana` monitorea la distribución de llamadas por días de
semana (hábiles vs fin de semana) mes a mes. El campo `error_suma` detecta
inconsistencias del ETL (cuando `habiles + fin_semana != total`):

```
trimestre | fecha  | total | habiles | fin_semana | error_suma | pct_entre_semana | estado_monitor
Q01_25    | 202501 | 40918 | 30383   | 10535      | 0          | 74.3             | OK
Q02_26    | 202604 | 9500  | 6800    | 2710       | 10         | 71.6             | ALERTA
```

`estado_monitor = ALERTA` indica que el ETL pudo haber procesado registros con
valores de `llamadas_entre_semana` o `llamadas_fines_semana` inconsistentes.

### Corrección aplicada

**Nuevo endpoint:**

```
GET /api/pipeline/monitor/weekdays/   PIP-001  view_pipeline_status
  ?quarter=Q0N_YY  (opcional)
```

El resumen incluye `alertas` — cuenta de filas con `estado_monitor != OK`.

**Archivo:** `apps/pipeline/monitor_weekday_views.py`

### Tests TDD (8 tests)

```
TestMonitorWeekdaysEndpoint:
  test_it01_retorna_filas_con_campos_correctos
  test_it02_filtra_por_trimestre
  test_it03_quarter_invalido_retorna_400
  test_it04_resumen_incluye_alertas
  test_it05_sin_datos_retorna_vacio
  test_it06_mariadb_no_disponible_retorna_503
  test_it07_decimales_serializados_como_float
  test_sec01_sin_permiso_retorna_403
```

---

## Corrección — UC_ALR_03 no es GAP

El documento anterior marcaba `UC_ALR_03` (Reconocer Alerta) como GAP porque
`AlertAcknowledgeView` "no tenía lógica de cambio de estado". El análisis de código
confirmó que la implementación es completa:

```python
# apps/alerts/alert_views.py — AlertAcknowledgeView.post()
with transaction.atomic():
    alert.state             = Alert.STATE_ACKNOWLEDGED
    alert.acknowledged_by   = request.user
    alert.acknowledged_at   = timezone.now()
    alert.acknowledged_note = note
    alert.save(update_fields=[
        'state', 'acknowledged_by', 'acknowledged_at', 'acknowledged_note',
    ])
    AuditLogService.emit(event_type='ALERT_ACKNOWLEDGED', ...)
```

Los tests en `TestAcknowledgeEndpoint` (6 casos) cubren correctamente este flujo.
`UC_ALR_03` se reclasifica de **GAP** a **IMPLEMENTADO**.

---

## Flujo ETL completo verificado

```
evt_etl_diario (02:00 AM MariaDB) ← no activo en sandbox
     ↓
APScheduler (IACT-api scheduler.py) ← activo en producción
     ↓
CALL sp_etl_maestro()    [v2.5.0]
  PASO 0: job_config.is_enabled  ← ahora gestionable via /api/pipeline/job-config/
  PASO 1: concurrencia (6h)
  PASO 2: calcular quarter + tabla (v_quarter_actual)  ← ya expuesto en dashboard
  PASO 3: RUNNING en job_execution_log  ← /api/pipeline/status/ (UC_PIP_01)
  PASO 4: CALL sp_etl_base_detalle → base_ivr_detalle (16,689 filas)
  PASO 5: CALL sp_etl_base_clientes → base_ivr_clientes (3 filas/trimestre)
  PASO 6: CALL sp_etl_validar (5 checks EXCEPT/INTERSECT)
  PASO 7: status SUCCESS/PARTIAL/FAILED
     ↓
SPs de reporte (9 SPs activos con datos reales):
  sp_rpt_clientes           →  /api/reports/ivr/clients/
  sp_rpt_centros_transf.    →  /api/reports/ivr/transfer-centers/
  sp_rpt_llamadas_abandon.  →  /api/reports/ivr/abandoned/
  sp_rpt_menu_centro        →  /api/reports/ivr/menu-center/
  sp_rpt_menu_redirigidos   →  /api/reports/ivr/menu-redirected/
  sp_rpt_cMENU_ERROR        →  /api/reports/ivr/menu-errors/
  sp_rpt_centros_xsegmento  →  /api/reports/ivr/centers-by-segment/
  sp_rpt_resumen_abandono   →  /api/reports/ivr/abandonment-summary/
  sp_rpt_clientes (directo) →  /api/reports/ivr/unique-clients/

Vistas operacionales (todas cubiertas):
  v_etl_rendimiento   →  /api/pipeline/performance/
  v_quarter_actual    →  dashboard_view.py (UC_RPT_01)
  v_sla_distribucion  →  /api/reports/ivr/sla/          ← NUEVO
  v_eventos_recientes →  /api/pipeline/events/           ← NUEVO
  vw_monitor_dias_sem →  /api/pipeline/monitor/weekdays/ ← NUEVO
```

---

## Verificación final

```
# drf-spectacular
python manage.py spectacular --validate --file /dev/null
Warnings: 49 (11 unique)   ← benignos
Errors:   0 (0 unique)

# Schema
163 paths (+5), 239 operaciones (+6)

# tests/unit/ — PostgreSQL + MariaDB reales
python3 -m pytest tests/unit/ --no-header -q --tb=no --reuse-db
1060 passed (+37 nuevos), 0 failed

# tests/integration/ — PostgreSQL + MariaDB reales
python3 -m pytest tests/integration/ --no-header -q --tb=no --reuse-db
54 passed, 0 failed

# Nuevos tests por gap
- H-GAP-001 job_config:    13 tests RED → GREEN (13/13)
- H-GAP-002 events:         8 tests RED → GREEN (8/8)
- H-GAP-003 sla:            8 tests RED → GREEN (8/8)
- H-GAP-004 monitor:        8 tests RED → GREEN (8/8)
```

Commit: `7f60e20` en `develop`.
