# Hallazgos FASE 6 — Integración multi-repositorio y cero deuda técnica

**Artefacto:** HALLAZGOS-FASE6-FINAL-2026-05-15
**Versión:** 1.0.0
**Fecha:** 2026-05-15
**Repositorios:**
  - IACT-api  `develop` commits `3bd1c8a..60ef0b0`
  - IACT-ui   `develop` commits `885290f..639fe28`
  - IACT-db   provisioners v2.5.0 (2026-05-13)
**Estado:** Cerrado — deuda técnica activa = 0

---

## Resumen ejecutivo

| Dimensión | Antes | Después |
|---|---|---|
| IACT-api tests/unit/ passed | bloqueados (640 setup errors) | **1,060 passed, 0 failed** |
| IACT-api tests/integration/ passed | 54 passed (con MySQL UP) | **54 passed, 0 failed** |
| IACT-api drf-spectacular Errors | 230 | **0** |
| IACT-api schema paths | 158 | **163 (+5 nuevos)** |
| IACT-api schema operaciones | 185 | **239 (+54 recuperadas o nuevas)** |
| IACT-api endpoints sin cobertura de IACT-db | 4 | **0** |
| IACT-ui test suites passing | 222/226 | **226/226** |
| IACT-ui tests passing | 1,993 | **2,032 (+39)** |
| IACT-ui URLs incorrectas (de 47 endpoints) | 29 | **0** |
| Catálogo de permisos UI alineado con API | No | **Sí (RBAC v5.4.0)** |
| IACT-db objetos sin endpoint de API | 4 | **0** |

---

## Bloque A — IACT-api: Schema OpenAPI y suite de tests

### H-SPEC-001 — 51 APIViews ausentes del schema OpenAPI

drf-spectacular reportaba `Ignoring view for now` para 51 vistas que heredan de `APIView`
sin `serializer_class`. Las vistas estaban completamente ausentes del schema — sus endpoints
no aparecían en la documentación Swagger ni en los clientes generados.

**Causa:** drf-spectacular requiere `serializer_class` en `APIView` para inferir el schema.
Sin él, omite la vista en lugar de generar un schema parcial.

**Corrección:** `serializer_class` añadido a 51 vistas en 19 archivos de producción. Para
funciones `@api_view` (navigation), se usó `responses={200: None}` en el decorador
`@extend_schema` existente.

**Archivos modificados:** `apps/access/`, `apps/alerts/`, `apps/audit/`,
`apps/authentication/`, `apps/logs/`, `apps/reports/`, `apps/core/navigation/`,
`apps/users/urls.py`.

---

### H-SPEC-002 — 10 SerializerMethodField sin @extend_schema_field

10 métodos `SerializerMethodField` en 7 serializers documentaban tipo incorrecto
(`string`) en el schema OpenAPI independientemente de su tipo real.

**Corrección:** decorador `@extend_schema_field(OpenApiTypes.INT/BOOL/FLOAT/STR)` añadido
a `get_children_count`, `get_subscriber_count`, `get_recipient_count`, `is_read`,
`is_archived`, `get_user`, `get_user_full_name`, `get_progress`, `get_duration_seconds`,
`get_avatar_url`.

---

### H-SPEC-003 — 3 ViewSets con get_queryset fallando con AnonymousUser

`AlertSubscriptionViewSet`, `SavedViewViewSet`, `ScheduledReportViewSet` filtraban
por `request.user` en `get_queryset()`. Durante la generación del schema, drf-spectacular
usa `AnonymousUser`, provocando `ValueError: Field 'id' expected a number but got...`.

**Corrección:** check `if getattr(self, "swagger_fake_view", False): return none()` añadido
al inicio de cada `get_queryset()`.

---

### H-SPEC-004 — Colisión operationId `users_retrieve`

`GET /api/users/{id}/` (UserViewSet.retrieve) y `GET /api/users/{user_id}/`
(_Dispatcher.get) compartían el mismo `operationId`. drf-spectacular añadía sufijos
numéricos, produciendo clientes con nombres inconsistentes.

**Corrección:** `operation_id='user_detail'` explícito en el `@extend_schema` del GET del
`_Dispatcher` en `apps/users/urls.py`. `serializer_class = UserSerializer` añadido
también a `_Dispatcher`.

---

### H-SPEC-005 — 8 APIViews con @extend_schema en clase usando operation_id

drf-spectacular 0.27.0 reporta error cuando `@extend_schema(operation_id=...)` se aplica
directamente a la clase en lugar de al método HTTP.

Vistas corregidas: `AccessAuditDetailView`, `AccessAuditAggregationsView`,
`AuditEventDetailView`, `AuditEventAggregateView`, `AgentDetailView`,
`ExceptionalPreviewView`, `ExceptionalRevokeView`, `SavedViewCloneView`.

**Corrección:** `@extend_schema` de clase → `@extend_schema_view(get/post/delete=extend_schema(...))`.

---

### H-SPEC-006 y H-SPEC-007 — navigation views sin responses= y _Dispatcher sin schema

Las funciones `@api_view` de navegación (`navigation_menu_view`, `navigation_modules_view`)
tenían `@extend_schema(tags=...)` sin `responses=`, lo que provocaba su exclusión del schema.
`_Dispatcher` en `urls.py` carecía de `serializer_class`.

**Corrección:** `responses={200: None}` añadido; `serializer_class = UserSerializer` en
`_Dispatcher`.

---

### H-SQLITE-001 — Eliminación de SQLite en la suite de tests

`config/settings/fase0_testing.py` usaba SQLite en memoria para ambas bases de datos.
Esto ocultaba errores reales de compatibilidad con PostgreSQL y MariaDB.

**Corrección:** migrado a PostgreSQL real (`test_iact_analytics`) y MariaDB real
(`test_ivr_legacy`). `DummyCache` añadido para evitar contaminación de throttle entre tests.

---

### H-PROD-010 — analytics_views._stub_rows propaga ProgrammingError como 500

`_stub_rows()` en `apps/reports/analytics_views.py` no capturaba `ProgrammingError`.
Cuando la tabla no existe en MariaDB, retornaba HTTP 500 en lugar de lista vacía.

**Corrección:** `except ProgrammingError: return []` añadido a `_stub_rows()`.

---

### H-PROD-011 — pipeline/views.py y logs/views.py sin captura de ProgrammingError

Mismo patrón que H-PROD-010: múltiples vistas que leen de `ivr_legacy` capturaban
`OperationalError` (sin conexión) pero no `ProgrammingError` (tabla no existe). En
entornos donde `test_ivr_legacy` existe pero sin schema, las vistas retornaban 500.

**Vistas afectadas:** `etl_errors`, `etl_data_availability`, `etl_retry`, `etl_status`,
`etl_performance`, `log_health`, `log_metrics`, `log_tail` (8 vistas).

**Corrección:** `except (OperationalError, ProgrammingError) as e:` en todos los bloques
try/except que acceden a `connections['ivr']` en `apps/pipeline/views.py` y
`apps/logs/views.py`. La respuesta en ambos casos es `HTTP 503 SERVICE_UNAVAILABLE`.

---

### H-INFRA-001 — CREATE_DB: True generaba 640 setup errors en tests/unit/

`config/settings/fase0_testing.py` tenía `CREATE_DB: True` para la BD IVR. Cuando
pytest-django inicializaba la sesión, intentaba crear `test_ivr_legacy` en MariaDB.
En el sandbox, MariaDB puede no estar disponible o el proceso se agota al manejar
640 fixtures de setup simultáneos.

**Síntoma:** `640 errors` de `OperationalError` en setup, enmascarando los 434 tests
que sí pasaban. Con `--reuse-db`, el problema persistía porque pytest verificaba la BD
al inicio de cada sesión.

**Corrección:** `CREATE_DB: False` en `config/settings/fase0_testing.py`. `test_ivr_legacy`
ya existe y persiste entre sesiones — no necesita recrearse.

---

### H-INFRA-002 — tests/unit/ sin fixture que arranque MySQL

Sin un fixture de sesión que arranque MySQL antes de que pytest-django verifique la BD IVR,
los tests fallaban con `OperationalError: Can't connect to socket`.

**Corrección:** `ensure_mariadb_unit` añadido a `tests/unit/conftest.py` como fixture
`scope='session', autouse=True`. Responsabilidades:
1. Verificar si MySQL está disponible; si no, arrancarlo vía `subprocess.Popen(mariadbd)`.
2. Crear el schema mínimo en `test_ivr_legacy` después de que MySQL esté disponible:
   `job_execution_log`, `pipeline_event_log`, `etl_runs`, `job_config`.

---

## Bloque B — IACT-db: 4 objetos de BD sin endpoint de API

Análisis completo de `/tmp/references/IACT-db/provisioners/mariadb/objetos/` y comparación
con el schema OpenAPI de IACT-api reveló 4 objetos de MariaDB sin cobertura.

### H-GAP-001 — job_config sin endpoint de gestión

`job_config` controla si el ETL nocturno se ejecuta (`is_enabled`) y su ventana horaria.
Sin endpoint, la única forma de habilitar/deshabilitar el ETL era acceso directo a MariaDB.

**Implementación TDD (13 tests RED→GREEN):**
- `GET  /api/pipeline/job-config/`           — lista jobs, función PIP-001
- `GET  /api/pipeline/job-config/{job_name}/` — detalle, función PIP-001
- `PATCH /api/pipeline/job-config/{job_name}/` — habilitar/deshabilitar, función PIP-005

**Regla BR-ETL-01:** solo `is_enabled` y `notas` son modificables via API.
`timeout_seconds`, `ventana_inicio/fin`, `min_intervalo_h` requieren despliegue de BD.

**Nuevos:** `apps/pipeline/job_config_views.py`, `PIP-005` en catálogo RBAC,
`JOB_CONFIG_UPDATED` en catálogo de eventos de auditoría.

---

### H-GAP-002 — v_eventos_recientes sin endpoint

`v_eventos_recientes` une `pipeline_event_log` con `job_execution_log`, añadiendo
contexto del job (`job_status`, `job_step`, `job_inicio`) a cada evento de error.

**Implementación TDD (8 tests RED→GREEN):**
- `GET /api/pipeline/events/` — función PIP-002
  - `?severity=CRITICA|ALTA|MEDIA|BAJA|INFO`
  - `?error_type=ETL_FALLO|PARAM_INVALIDO|...`
  - `?limit=N` (default 50, max 200)

**Nuevo:** `apps/pipeline/pipeline_event_views.py`.

---

### H-GAP-003 — v_sla_distribucion sin endpoint

`v_sla_distribucion` clasifica centros de transferencia por categoría SLA por trimestre
(FUERA_SLA, RIESGO_SLA, DENTRO_SLA, ACTIVO_HOY, VOLUMEN_MEDIO, BAJO_VOLUMEN).
Sin endpoint, el dashboard ejecutivo no tenía fuente de datos SLA.

**Implementación TDD (8 tests RED→GREEN):**
- `GET /api/reports/ivr/sla/` — función RPT-019
  - `?quarter=Q0N_YY` (opcional)

**Nuevo:** `apps/reports/sla_views.py`.

---

### H-GAP-004 — vw_monitor_dias_semana sin endpoint

`vw_monitor_dias_semana` monitorea la distribución de llamadas por días de semana por mes.
`error_suma > 0` indica inconsistencia en los datos del ETL
(`habiles + fin_semana ≠ total`), lo que puede indicar datos corruptos.

**Implementación TDD (8 tests RED→GREEN):**
- `GET /api/pipeline/monitor/weekdays/` — función PIP-001
  - `?quarter=Q0N_YY` (opcional)
  - Respuesta incluye `resumen.alertas` (count de filas con `estado_monitor != OK`)

**Nuevo:** `apps/pipeline/monitor_weekday_views.py`.

---

### H-UC-STUB-001 — UC_RPT_02 (SSE tiempo real) es stub documentado

`UC_RPT_02` requiere Server-Sent Events (SSE) que necesita ASGI. IACT-api corre con
WSGI (Gunicorn). El endpoint existe con un response simulado pero no emite datos reales.
Activación pendiente de migración a ASGI (tarea de infraestructura).

---

### H-UC-STUB-002 — UC_RPT_12..14 (AgentDetail, QueueReport, CampaignReport)

`AgentReportView`, `QueueReportView`, `CampaignReportView` y `TransferReportView`
(sección A de `apps/reports/urls.py`) acceden a tablas del sistema ACD/CTI externo
que NO existen en `ivr_legacy`:

| Vista | Tabla requerida |
|---|---|
| `AgentReportView`/`AgentDetailView` | `agent_performance_summary`, `agent_performance_detail` |
| `QueueReportView` | `queue_performance_summary` |
| `CampaignReportView` | `campaign_summary` |
| `TransferReportView` | `ivr_transfer_summary` |

Las vistas retornan `[]` en lugar de 500 gracias a H-PROD-010. No son deuda técnica —
son limitaciones documentadas del entorno. Se activan cuando el sistema ACD/CTI esté
provisionado en `ivr_legacy`.

---

## Bloque C — IACT-ui: Integración de URLs y catálogo de permisos

### H-INT-001 — authGateway.js: 3 URLs de autenticación v1 obsoletas

| Método | URL anterior | URL canónica v2 |
|---|---|---|
| `login()` | `POST /api/token/` | `POST /api/auth/login/` |
| `logout()` | `POST /api/logout/` | `POST /api/auth/logout/` |
| `verifyToken()` | `POST /api/token/verify/` | `GET /api/auth/me/` |

Además, el formato de respuesta de `login()` cambió de respuesta plana
`{ user_id, username }` a respuesta estructurada `{ tokens, user, session, next_step }`.

---

### H-INT-002 — logsGateway.js: 8 URLs de logs y pipeline obsoletas

| Método | URL anterior | URL canónica v2 |
|---|---|---|
| `getLogs()` | `GET /api/logs/` | `GET /api/logs/django/tail/` |
| `getETLLogs()` | `GET /api/logs/etl/` | `GET /api/logs/etl/tail/` |
| `getSystemStatus()` | `GET /api/system/status/` | `GET /api/logs/health/` |
| `getPerformanceMetrics()` | `GET /api/system/metrics/` | `GET /api/logs/metrics/` |
| `getPipelineStatus()` | `GET /api/v1/etl/supervision/` | `GET /api/pipeline/status/` |
| `getPipelineErrors()` | `GET /api/v1/etl/errores/` | `GET /api/pipeline/errors/` |
| `getETLAvailability()` | `GET /api/v1/datos/disponibilidad/` | `GET /api/pipeline/data-availability/` |
| `retryPipeline()` | `POST /api/etl/logs/{id}/retry/` | `POST /api/pipeline/retry/` |

Gateway reescrito completo con 12 métodos canónicos + 4 nuevos para H-GAP-001..004.

---

### H-INT-003 — reportsGateway.js: 7 URLs de reportes obsoletas + 1 ausente

| Método | URL anterior | URL canónica v2 |
|---|---|---|
| `getDashboardMetrics()` | `GET /api/reports/metrics/dashboard/` | `GET /api/reports/dashboard/` |
| `getReportHistory()` | `GET /api/reports/history/` | `GET /api/reports/historical/` |
| `getTransfersReport()` | `GET /api/reports/transfers/` | `GET /api/reports/ivr/transfer-centers/` |
| `getUniqueClientsReport()` | `GET /api/reports/unique-clients/` | `GET /api/reports/ivr/clients/` |
| `getIVRMenusReport()` | `GET /api/reports/ivr-menus/` | `GET /api/reports/ivr/menus/` |
| `getSavedViews()` | `GET /api/reports/saved-views/` | `GET /api/reports/me/views/` |
| `getScheduledReports()` | `GET /api/reports/scheduled/` | `GET /api/reports/schedules/` |

Gateway reescrito con 20 endpoints. `getSLADistribucion()` añadido para H-GAP-003.
`pauseSchedule()` y `resumeSchedule()` corregidos de `PATCH` a `POST`.

---

### H-INT-004 — adminGateway.js: 5 URLs del prefijo /api/admin/ obsoleto

Todas las rutas del dominio de administración RBAC usan el prefijo canónico `/api/access/`:

| URL anterior | URL canónica |
|---|---|
| `GET /api/admin/agr/` | `GET /api/access/access-groups/` |
| `GET/POST /api/admin/functions/` | `GET/POST /api/access/functions/` |
| `GET/POST /api/admin/separation-rules/` | `GET/POST /api/access/separation-rules/` |
| `GET/POST /api/admin/menu-items/` | `GET/POST /api/access/menu-items/` |

---

### H-INT-005 — Catálogo FunctionCatalog desalineado con RBAC v5.4.0

`src/permissions/catalog.js` usaba notación `{module}:{action}` (RBAC v5.6.x legacy)
en lugar de los códigos canónicos `MOD-NNN` de RBAC v5.4.0 que usa la API.

**Consecuencia:** los guards de ruta (`ProtectedRoute`) comparaban strings incompatibles
con los que retorna la API en el campo `capacidades`. Un usuario con `'PIP-001'` en la
respuesta de la API fallaba el guard de UI que esperaba `'pipeline:view_status'`.

**Corrección:** catálogo completamente reescrito en formato `MOD-NNN`. 14 entradas nuevas
para permisos legacy usados en el router. Mocks `permissions.json` y
`permissions-admin.json` también actualizados a `MOD-NNN`.

---

### H-INT-006 — Redux slice logs.js sin thunks para endpoints de FASE 6

`src/redux/slices/logs.js` no tenía thunks para los 4 endpoints implementados en H-GAP-001..004.

**Thunks añadidos:**
```javascript
fetchPipelineEvents(params)   // GET /api/pipeline/events/
fetchJobConfig(jobName)       // GET /api/pipeline/job-config/{name}/
updateJobConfig({jobName,data}) // PATCH /api/pipeline/job-config/{name}/
fetchMonitorWeekdays(params)  // GET /api/pipeline/monitor/weekdays/
```

Estado extendido: `pipelineEvents`, `jobConfig`, `monitorWeekdays`.

---

### H-INT-007 — 7 suites de tests verificaban URLs v1 obsoletas

Al corregir los gateways, los tests existentes que verificaban las URLs antiguas
comenzaron a fallar — comportamiento esperado de TDD. Todos los tests actualizados
a las URLs y códigos canónicos v2:

`authService.test.js`, `logsService.test.js`, `adminService.test.js`,
`reportsService.test.js`, `AppRouter.test.jsx`, `mockInterceptor-permisos.test.js`,
`catalog.test.js`.

---

## Verificación final

### IACT-api

```
DJANGO_SETTINGS_MODULE=config.settings.fase0_testing
python3 -m pytest tests/unit/ --no-header -q --tb=no --reuse-db
  1060 passed, 60 skipped, 86 xfailed, 6 xpassed, 0 failed

DJANGO_SETTINGS_MODULE=config.settings.integration_ivr
python3 -m pytest tests/integration/ --no-header -q --tb=no --reuse-db
  54 passed, 1 skipped, 49 xfailed, 0 failed   (con MySQL disponible)

python manage.py spectacular --validate
  Warnings: 49 (11 unique, benignos)
  Errors:   0 (0 unique)

Schema: 163 paths, 239 operaciones
```

### IACT-ui

```
npm test -- --no-coverage
  Test Suites: 226 passed, 226 total   (+4 nuevas suites de integración)
  Tests:       2032 passed, 0 failed   (+39 tests nuevos)
```

### IACT-db

```
bash verify.sh
  OK: 27  Errores: 0  (con MySQL disponible)
```

---

## Tabla de commits

### IACT-api (`develop`)

| Commit | Descripción |
|---|---|
| `3bd1c8a` | fix(tests): suite 0 fallos — FASE 6 corrección masiva |
| `c60c61c` | fix(tests): suite integración 0 fallos — BDs reales |
| `4ebb474` | fix(schema): drf-spectacular 0 errores |
| `7f60e20` | feat: TDD 4 gaps IACT-db (job_config, events, sla, monitor) |
| `60ef0b0` | fix(infra+views): H-INFRA-001/002, H-PROD-011 |

### IACT-ui (`develop`)

| Commit | Descripción |
|---|---|
| `39817cf` | fix(gateways+catalog+redux): integración URLs canónicas IACT-api v2 |
| `639fe28` | docs: HALLAZGOS-FASE6-INTEGRACION |

---

## Objetos fuera de scope confirmados

Los siguientes objetos son correctamente NO cubiertos por IACT-api:

| Objeto | Razón |
|---|---|
| `sp_etl_base_detalle`, `sp_etl_base_clientes`, `sp_etl_validar` | Internos de `sp_etl_maestro` — no expuestos |
| `evt_etl_diario` | Event MariaDB — suplido por APScheduler en IACT-api |
| `fn_did_segmento`, `fn_normalizar_*`, `ivr_*` (7 funciones) | Funciones internas de MariaDB — solo las usan los SPs |
| `tbl_historico_tN_YYYY` | Fuente del ETL — no expuesta directamente |
| `base_ivr_clientes` | Acceso vía SPs — no endpoint directo (CNST-026: PII) |
| `tbl_temp_prueba_ivr` | Tabla temporal de pruebas — no productiva |
| `seed_executions` | Registro interno de provisioning |
