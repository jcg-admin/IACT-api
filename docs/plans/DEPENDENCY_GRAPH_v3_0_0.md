# Grafo de dependencias — Planes v3.0.0, v3.1.0, v3.2.0

**Fecha:** 2026-05-08
**Base:** Plan v2.0.1 completado (640 passed, 0 failed en `tests/unit/`)
**Documentos relacionados:**
- `plans/GAP_ANALYSIS_v3_0_0.md`
- `plans/PLAN_v3_0_0.md`
- `plans/PLAN_v3_1_0.md`
- `plans/PLAN_v3_2_0.md`

---

## Resumen: cuántos planes y por qué

**3 planes** después del v2.0.1. Ni más ni menos.

| Plan | Scope | Prerequisito estricto |
|------|-------|-----------------------|
| v3.0.0 | Pipeline ETL IVR (5 tareas) | v2.0.1 ✓ |
| v3.1.0 | MenuItem + deuda de navegación (5 tareas) | ninguno técnico — v3.0.0 por orden |
| v3.2.0 | Reports/Audit faltantes (5 tareas) | ninguno técnico — v3.1.0 por orden |

v3.1.0 y v3.2.0 **pueden arrancar en paralelo con v3.0.0** porque sus entradas
ya existen en la base. El orden sugerido (v3.0.0 → v3.1.0 → v3.2.0) es
por riesgo, no por dependencia técnica estricta.

---

## Inventario completo de tareas

### v3.0.0 — Pipeline ETL IVR

| Tarea | Descripción | Prerequisito |
|-------|-------------|-------------|
| T-001 | `manage.py run_etl` con heartbeat threading | ninguno |
| T-002 | ETLScheduler → CronTrigger + `sp_etl_maestro` | T-001 |
| T-003 | Separar endpoints `ivr/menu-redirigidos/` e `ivr/menu-centro/` | ninguno |
| T-004 | Tests unitarios de `run_etl` (mock `connections['ivr']`) | T-001 |
| T-005 | Tests de integración para ambos endpoints de menú IVR | T-003 |

### v3.1.0 — MenuItem y deuda de navegación

| Tarea | Descripción | Prerequisito |
|-------|-------------|-------------|
| T-101 | Quitar `pytestmark = skip` injustificado en `test_utils_network.py` | ninguno |
| T-102 | Modelo `MenuItem` (CNST-032 v5.6.x, OneToOne sobre `Function`) | ninguno |
| T-103 | Decisión DT-002: eliminar los 17 tests de clases eliminadas | ninguno |
| T-104 | `MenuLifecycleService` (state machine DRAFT→ACTIVE→DEPRECATED→ARCHIVED) | T-102 |
| T-105 | Tests de `MenuItem` y `MenuLifecycleService` | T-102, T-104 |

### v3.2.0 — Reports y Audit faltantes

| Tarea | Descripción | Prerequisito |
|-------|-------------|-------------|
| T-201 | UC_RPT_03 históricos (`HistoricalReportView`, periodos last_7d..custom) | ninguno |
| T-202 | UC_RPT_09 filtros guardados (modelo `SavedFilter` + CRUD) | ninguno |
| T-203 | UC_RPT_11 compartir reporte (campos `is_public`+`shared_with` a `SavedView`) | ninguno |
| T-204 | UC_AUD_03 exportar auditoría async (modelo `AuditExportJob` + worker) | ninguno |
| T-205 | Tests unitarios del plan v3.2.0 | T-201, T-202, T-203, T-204 |

---

## Grafo de dependencias

Las flechas indican "debe completarse antes de".

```
BASE (v2.0.1)
├── connections['ivr']  ──────────────────► T-001
│   etl_runs (MariaDB)                         │
│                                              ▼
│                                          T-002 (ETLScheduler)
│                                              │
│                                              ▼
│                                          T-004 (tests run_etl)
│
├── ivr_services.py ──────────────────────► T-003
│   ivr_views.py                               │
│                                              ▼
│                                          T-005 (tests menú)
│
├── Function (model) ─────────────────────► T-102
│                                              │
│                                              ▼
│                                          T-104 (MenuLifecycle)
│                                              │
│                                              ▼
│                                          T-105 (tests MenuItem)
│
├── Report (model) ───────────────────────► T-201
│
├── SavedView (model) ────────────────────► T-203
│
│   [T-202 SavedFilter: modelo nuevo, sin prerequisito]
│   [T-204 AuditExportJob: modelo nuevo, sin prerequisito]
│
│                        T-201 ─┐
│                        T-202 ─┤
│                        T-203 ─┼──► T-205 (tests v3.2.0)
│                        T-204 ─┘
│
└── [T-101, T-103: sin prerequisito — solo decisiones/fixes triviales]
```

---

## Dependencias cruzadas entre planes

No hay dependencias técnicas entre los tres planes. Cada plan opera
sobre módulos distintos:

- v3.0.0: `apps/pipeline/`, `apps/reports/ivr_views.py`
- v3.1.0: `apps/access/` (modelo `MenuItem`)
- v3.2.0: `apps/reports/` (modelos nuevos), `apps/audit/` (modelo nuevo)

Los únicos modelos que podrían crear conflicto de migración son los de
`apps/reports/` — T-202 (`SavedFilter`) y T-203 (extensión de `SavedView`)
tocan el mismo app. Si se ejecutan en paralelo, deben coordinarse
para que sus migraciones no colisionen en numeración.

---

## Qué queda fuera del scope de los tres planes

### Extension points declarados — no implementar

| Módulo | UCs | Estado en spec |
|--------|-----|----------------|
| MOD_Supervision | UC_SUP_01..03 | Fuera de scope — extension point |
| MOD_Operator | UC_OPR_01..10 | Fuera de scope — extension point |
| Caller (IVR cliente) | UC_CLI_01..05 | Fuera de scope |

Estos UCs están preservados en el spec como base para activación futura.
No son especificación implementable en el proyecto IACT actual.

### Infraestructura MariaDB — responsabilidad de ops

- `evt_etl_diario` (MySQL Event Scheduler): se despliega con
  `CREATE EVENT` vía script SQL.
- Carga histórica: `CALL sp_etl_historico(year, quarter)` manualmente.

### Skips intencionales que permanecen

| Archivo | Cantidad | Razón |
|---------|----------|-------|
| `access/test_services.py::ModuleAccessService` | 2 | RBAC v6.0.0 lo simplificó — decisión intencional documentada |

Estos 2 skips permanecen después de los tres planes. Son deuda
técnica aceptada, no un fallo.

---

## Conteo de tests esperado al cierre de cada plan

| Estado | `tests/unit/` passed | `tests/integration/` passed | Skips |
|--------|---------------------|----------------------------|-------|
| Actual (v2.0.1) | 640 | 13 | 4 |
| Post v3.0.0 | ~648 | ~17 | 4 |
| Post v3.1.0 | ~680 | ~17 | 2 |
| Post v3.2.0 | ~710 | ~17 | 2 |

Los números son estimados. El criterio de cierre definitivo para cada plan
está en su documento correspondiente.

---

## Invariantes que no deben romperse en ningún plan

| Invariante | Verificación |
|-----------|-------------|
| `tests/unit/access/` 100 passed, 2 skipped | `python -m pytest tests/unit/access/ --tb=no -q` |
| `tests/integration/pipeline/` 13+ passed | `python -m pytest tests/integration/ --tb=no -q` |
| `python manage.py check` — 0 issues | Ejecutar al final de cada tarea |
| 0 migraciones pendientes | `python manage.py showmigrations \| grep "\[ \]"` → vacío |
| Alias `connections['ivr']` — no cambiar | El settings usa `ivr`, no `ivr_cliente` |
