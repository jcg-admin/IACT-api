# Plan de implementación v3.0.0 — IACT API

**Versión:** 3.0.0
**Fecha:** 2026-05-08
**Prerrequisito:** Plan v2.0.1 completado (640 passed, 0 failed en `tests/unit/`)
**Scope:** Pipeline ETL IVR — integración Django con los SPs de MariaDB
**Estado:** COMPLETADO — implementado en sesión 2026-05-08/09
**Gap analysis:** `plans/GAP_ANALYSIS_v3_0_0.md`

---

## Contexto

El spec v2.1 del pipeline ETL IVR (`feature/etl-ivr-pipeline-spec`) define cómo
Django debe integrarse con los stored procedures de MariaDB. Al cierre del plan
v2.0.1 existían tres brechas reales:

1. `manage.py run_etl` no existía — el ETL solo podía dispararse por scheduler.
2. `ETLScheduler` llamaba a `ETLService` (desactivado), no a `sp_etl_maestro`.
3. Los reportes de menú IVR (`sp_rpt_menu_redirigidos` y `sp_rpt_menu_centro`)
   estaban fusionados en un único endpoint con parámetro `?vista=`, cuando el
   spec los define como endpoints independientes con semántica distinta.

---

## Distinción fundamental: menú IVR vs menú del sistema

**Menú IVR** es el campo `cMenu` en `tbl_historico_*` — la opción del árbol
telefónico que navegó el llamante. El ETL lo normaliza con `fn_normalizar_menu()`
y lo materializa en `base_ivr_detalle.menu`. Los SPs `sp_rpt_menu_redirigidos`
y `sp_rpt_menu_centro` producen reportes analíticos sobre este campo.

**Menú del sistema** es el árbol de navegación UX del sistema IACT
(`Domain → Section → Action`). Definido por `CNST-032`. Implementado como
`MenuItem` en `apps/access/`. Es responsabilidad del plan v3.1.0.

---

## Tareas

### T-001 — `manage.py run_etl` (UC_ETL_04) — COMPLETADO

**Archivo:** `apps/pipeline/management/commands/run_etl.py`

- `_quarter_activo()`: calcula `Q0N_YY` desde `date.today()`.
- `_registrar_inicio()`: INSERT en `etl_runs` con `status='en_ejecucion'`,
  `trigger_source='django_command'`, `inicio_at`, `timeout_at`.
- `_heartbeat()`: thread daemon — actualiza `heartbeat_at` cada 60s,
  marca `timeout` si `timeout_at < NOW()`.
- `handle()`: inicio → thread heartbeat → `callproc('sp_etl_maestro', [])` →
  UPDATE en `finally`. No propaga excepciones.

**Commit:** `754fc32`

---

### T-002 — `ETLScheduler` → `CronTrigger` + `sp_etl_maestro` — COMPLETADO

**Archivo:** `apps/pipeline/scheduler.py`

- `IntervalTrigger(hours=12)` → `CronTrigger(hour=2, minute=0)`.
- `ETLService.run()` → INSERT `etl_runs` + `callproc('sp_etl_maestro', [])`.
- `trigger_source='mysql_event'`.
- `OperationalError` capturado para no matar el scheduler.

**Commit:** `754fc32`

---

### T-003 — Separar endpoints `ivr/menu-redirigidos/` e `ivr/menu-centro/` — COMPLETADO

| SP | Grain | Endpoint |
|---|---|---|
| `sp_rpt_menu_redirigidos` | `menu × opcion` | `GET /api/reports/ivr/menu-redirigidos/` |
| `sp_rpt_menu_centro` | `menu × centro_transferencia` | `GET /api/reports/ivr/menu-centro/` |

El endpoint unificado `ivr/menus/` se conserva como legacy.

**Nota:** La firma real en MariaDB es `(p_quarter, p_segmento)`. No es brecha
con el spec — los SPs desplegados aceptan ambos parámetros.

**Archivos:** `apps/reports/ivr_views.py`, `apps/reports/urls.py`
**Commit:** `c6f0502` (recuperado 2026-05-09)

---

### T-004 — Tests unitarios `run_etl` — COMPLETADO

**Archivo:** `tests/unit/pipeline/test_run_etl_command.py` — 25 tests

| Clase | Tests |
|---|---|
| `TestQuarterActivo` | 2 |
| `TestRegistrarInicio` | 3 |
| `TestEjecutarSP` | 2 |
| `TestUpdateRun` | 3 |
| `TestHandle` | 7 |
| `TestHeartbeat` | 2 |
| `TestHeartbeatTimeout` | 6 |

**Commit:** `754fc32`

---

### T-005 — Tests de integración endpoints de menú — COMPLETADO

**Archivo:** `tests/integration/pipeline/test_ivr_endpoints.py` — 25 tests

| Clase | Tests |
|---|---|
| `TestIVRMenuRedirigidos` | 3 |
| `TestIVRMenuCentro` | 3 |
| `TestRendimientoEndpoints` | 1 |
| Otros (ETL status, retry, clients, etc.) | 18 |

**Commit:** `c6f0502` (recuperado 2026-05-09)

---

## Estado al cierre

| Tarea | Estado | Commit |
|---|---|---|
| T-001 `manage.py run_etl` | COMPLETADO | `754fc32` |
| T-002 `ETLScheduler` → CronTrigger | COMPLETADO | `754fc32` |
| T-003 endpoints menú separados | COMPLETADO | `c6f0502` |
| T-004 tests unitarios run_etl | COMPLETADO | `754fc32` |
| T-005 tests integración menú | COMPLETADO | `c6f0502` |

**Tests al cierre:**

| Suite | Resultado esperado |
|---|---|
| `tests/unit/` | 686 passed (con PostgreSQL) |
| `tests/integration/pipeline/` | 39 passed (con MariaDB) |

---

## Ver también

- `plans/GAP_ANALYSIS_v3_0_0.md` — brechas que originaron este plan
- `plans/PLAN_v3_1_0.md` — siguiente plan (MenuItem CNST-032)
- `plans/DEPENDENCY_GRAPH_v3_0_0.md` — grafo maestro de los tres planes
