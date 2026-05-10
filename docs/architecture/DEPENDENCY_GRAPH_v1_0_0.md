# Grafo de dependencias — IACT API

**Version:** 1.0.0
**Fecha:** 2026-05-07
**Fuente:** ANALISIS-UC-vs-IACT-API-V2 + implementacion brechas B-01..B-09
**Scope:** 65 UCs (excluye operator, supervision, caller)

---

## Capas del sistema

```
┌─────────────────────────────────────────────────────────────┐
│ CAPA 0 — MariaDB ivr_legacy                                 │
│                                                             │
│  job_execution_log   base_ivr_detalle   etl_runs           │
│  sp_rpt_* (7 SPs)   sp_etl_* (5 SPs)   base_ivr_clientes  │
└──────────────────────────┬──────────────────────────────────┘
                           │ connections['ivr'].cursor()
┌──────────────────────────▼──────────────────────────────────┐
│ CAPA 1 — Servicios de acceso a MariaDB                      │
│                                                             │
│  pipeline/views.py       reports/ivr_services.py           │
│  ├── etl_status          ├── get_clientes()                 │
│  ├── etl_errors          ├── get_centros_transferencia()    │
│  ├── etl_data_avail.     ├── get_llamadas_abandonadas()     │
│  └── etl_retry           ├── get_cmenu_error()              │
│                          ├── get_centros_xsegmento()        │
│  logs/views.py           ├── get_menu_redirigidos()         │
│  └── ETLLogTailView      └── get_menu_centro()              │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│ CAPA 2 — Modelos Django (PostgreSQL)                        │
│                                                             │
│  access/models.py                                           │
│  ├── Module             ├── AccessGroup                    │
│  ├── Function           ├── UserAccessGroup                │
│  ├── UserPermission     ├── SeparationRule  (ex SodRule)   │
│  └──                    └── ExceptionalPermission          │
│                                                             │
│  authentication/  users/  audit/  alerts/  pipeline/       │
│  reports/models.py: Report, ExportJob, ETLExecution        │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│ CAPA 3 — config/urls.py                                     │
│                                                             │
│  /api/                 → apps.authentication.urls           │
│  /api/users/           → apps.users.urls                   │
│  /api/access/          → apps.access.urls                  │
│  /api/audit/           → apps.audit.urls                   │
│  /api/alerts/          → apps.alerts.urls                  │
│  /api/pipeline/        → apps.pipeline.urls                │
│  /api/reports/         → apps.reports.urls                 │
│  /api/logs/            → apps.logs.urls                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│ CAPA 4 — Casos de uso (65 en scope)                         │
│                                                             │
│  auth (5) ✓    users (4) ✓    audit (4) ✓    alerts (5) ✓  │
│  logs (7) ✓    pipeline (4) ✓                               │
│  access (7) ~  perms (10) ~   reports (16) ~ admin (3) ~   │
└─────────────────────────────────────────────────────────────┘
```

---

## Dependencias entre UCs

### Dependencias bloqueantes (A requiere B)

```
UC_ACC_04  requiere → AccessGroup (modelo)
UC_ACC_05  requiere → SeparationRule (modelo)
UC_ACC_08  requiere → ExceptionalPermission (modelo)
UC_PERM_01 requiere → AccessGroup
UC_PERM_02 requiere → AccessGroup
UC_PERM_03 requiere → ExceptionalPermission
UC_PERM_04 requiere → ExceptionalPermission
UC_PERM_05 requiere → AccessGroup
UC_PERM_06 requiere → AccessGroup
UC_ADM_01  requiere → SeparationRule
UC_ADM_03  requiere → AccessGroup

UC_PIP_02..04 requieren → connections['ivr'] activo
UC_RPT_12..17 requieren → ivr_services.py (callproc)
UC_LOG_02     requiere  → job_execution_log en MariaDB
```

### Dependencia de inclusion (UC_INC)

```
UC_INC_RPT_01 (SegmentResolver) es incluido por:
  → UC_RPT_12, UC_RPT_13, UC_RPT_14, UC_RPT_15,
    UC_RPT_16, UC_RPT_17
```

---

## Cadenas de llamada completas

### Cadena de reportes — Reporte de clientes (UC_RPT_17)

```
GET /api/reports/ivr/clients/?quarter=Q01_25
    → reports/urls.py
    → reports/ivr_views.py :: ClientesReportView.get()
        → reports/ivr_services.py :: get_clientes(quarter)
            → _call_sp('sp_rpt_clientes', [quarter])
                → connections['ivr'].cursor().callproc()
                    → MariaDB :: sp_rpt_clientes(p_quarter)
                        → SELECT FROM base_ivr_clientes
```

### Cadena del pipeline — Estado de ejecucion (UC_PIP_01)

```
GET /api/pipeline/status/
    → pipeline/urls.py
    → pipeline/views.py :: etl_status()
        → _get_pipeline_runs(limit=20)
            → connections['ivr'].cursor().execute()
                → MariaDB :: SELECT FROM job_execution_log
        → _build_resumen_salud(runs)  [ok | degradado | critico]
```

### Cadena Pipeline — Reintento (UC_PIP_04)

```
POST /api/pipeline/retry/ { trimestre, motivo }
    → pipeline/views.py :: etl_retry()
        → verificar no RUNNING en job_execution_log
        → connections['ivr'].cursor().callproc()
            → MariaDB :: sp_etl_historico(year, quarter_num)
                → sp_etl_base_detalle()
                → SLEEP(5)
                → sp_etl_base_clientes()
                → sp_etl_validar()
```

### Cadena de permisos efectivos (UC_ACC_03 / UC_PERM_07)

```
GET /api/access/users/{id}/effective-permissions/
    → access/urls.py
    → access/views.py :: EffectivePermissionsView.get()
        → UserPermission.objects.filter(user=user)   [directos]
        → Function.objects.filter(
              access_groups__memberships__user=user)  [via grupo]
        → ExceptionalPermission.objects.filter(
              user=user, estado='aprobado', ...)       [temporales]
        → union de tres fuentes → Response
```

---

## Endpoints activos por dominio

### /api/ — authentication (5 UCs)

```
POST   /api/auth/login/                    UC_AUTH_01
POST   /api/auth/logout/                   UC_AUTH_02
POST   /api/auth/reset-password/           UC_AUTH_03
POST   /api/auth/change-password/          UC_AUTH_04
GET    /api/sessions/                      UC_AUTH_05
DELETE /api/sessions/{id}/                 UC_AUTH_05
```

### /api/users/ — users (4 UCs)

```
GET    /api/users/                         UC_USR_02
POST   /api/users/                         UC_USR_01
GET    /api/users/{id}/                    UC_USR_02
PATCH  /api/users/{id}/                    UC_USR_03
DELETE /api/users/{id}/                    UC_USR_04
```

### /api/access/ — access + permissions + admin (17 UCs)

```
GET/POST /api/access/modules/              UC_ADM_02
GET/POST /api/access/groups/               UC_PERM_05, UC_ADM_03
POST     /api/access/groups/{id}/add-function/     UC_PERM_06
DELETE   /api/access/groups/{id}/remove-function/  UC_PERM_06
GET/POST /api/access/user-groups/          UC_ACC_04, UC_PERM_01
DELETE   /api/access/user-groups/{id}/     UC_PERM_02
GET/POST /api/access/separation-rules/     UC_ACC_05, UC_ADM_01
PATCH    /api/access/separation-rules/{id}/ UC_ACC_05
GET      /api/access/separation-rules/check/ UC_ACC_05
GET/POST /api/access/exceptional/          UC_ACC_08, UC_PERM_03
PATCH    /api/access/exceptional/{id}/approve/ UC_ACC_08, UC_PERM_03
PATCH    /api/access/exceptional/{id}/revoke/  UC_PERM_04
GET      /api/access/my-modules/           UC_PERM_08
GET      /api/access/users/{id}/effective-permissions/ UC_ACC_03, UC_PERM_07
```

### /api/pipeline/ — pipeline (4 UCs)

```
GET    /api/pipeline/status/               UC_PIP_01
GET    /api/pipeline/errors/               UC_PIP_02
GET    /api/pipeline/data-availability/    UC_PIP_03
POST   /api/pipeline/retry/                UC_PIP_04
```

### /api/reports/ — reports (13 de 16 UCs)

```
GET/POST /api/reports/reports/             UC_RPT_03
POST     /api/reports/export-jobs/         UC_RPT_04
GET      /api/reports/ivr/clients/         UC_RPT_17
GET      /api/reports/ivr/transfer-centers/ UC_RPT_12
GET      /api/reports/ivr/abandoned/       UC_RPT_13
GET      /api/reports/ivr/menu-errors/     UC_RPT_14
GET      /api/reports/ivr/centers-by-segment/ UC_RPT_15
GET      /api/reports/ivr/menus/           UC_RPT_16
-- UC_RPT_02 (SSE) pendiente ASGI --
-- UC_RPT_07, 08, 09, 10, 11 pendientes --
```

### /api/audit/ — audit (4 UCs)

```
GET    /api/audit/logs/                    UC_AUD_01, UC_AUD_02
GET    /api/audit/integrity/verify/        UC_AUD_04
POST   /api/audit/integrity/sign/          UC_AUD_04
```

### /api/alerts/ — alerts (5 UCs)

```
GET/POST /api/alerts/configurations/       UC_ALR_01
GET/POST /api/alerts/messages/             UC_ALR_03, UC_ALR_05
GET/POST /api/alerts/subscriptions/        UC_ALR_04
```

### /api/logs/ — logs (7 UCs)

```
GET  /api/logs/django/tail/               UC_LOG_01
GET  /api/logs/etl/tail/                  UC_LOG_02
GET  /api/logs/search/                    UC_LOG_03
POST /api/logs/export/                    UC_LOG_04
GET  /api/logs/infra/                     UC_LOG_05
GET  /api/logs/health/                    UC_LOG_06
GET  /api/logs/metrics/                   UC_LOG_07
```

---

## Pendientes post-grafo

| Item | Descripcion | Prioridad |
|---|---|---|
| B-10 | UC_RPT_02 SSE requiere ASGI | Media |
| Migraciones | makemigrations access (4 modelos nuevos) | Alta |
| Permisos granulares | UC_ACC_01/02 usar UserPermission en vez de UserModuleAccess | Alta |
| drf_spectacular | Decorar todos los endpoints con @extend_schema | Alta |
| Tests | Cobertura de los endpoints nuevos | Alta |
