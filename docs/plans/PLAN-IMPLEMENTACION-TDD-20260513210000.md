# Plan de Implementación — IACT-api (TDD)

**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Fuentes:**
- IACT-db `develop` — 12 SPs + 3 vistas + pipeline_event_log (100% implementados)
- IACT-docs `feature/wp-content-5-6-diagram-types` — 61 UCs especificados (97 en catálogo)
- IACT-api `develop` — estado post-FASE 8 (plan anterior completo)
**Metodología:** Red → Green → Refactor (TDD estricto por FASE)

---

## Contexto: por qué los tests deben cambiar

El plan anterior (FASES 1-8) limpió código muerto, renombró, agregó endpoints y corrigió tests incorrectos. Lo que restaba después de FASE 8 es lo que **falta construir**: código de producción que cumpla los criterios de aceptación documentados en los 61 UCs de IACT-docs.

La auditoría revela tres tipos de brechas:

| Tipo | Descripción | Ejemplo |
|---|---|---|
| **Test ausente** | Un UC documentado no tiene ningún test | UC_RPT_01 Dashboard |
| **Test incompleto** | El test existe pero no verifica los CAs reales | UC_PIP_01 no verifica caché ni stale |
| **Implementación stub** | El endpoint existe pero devuelve respuesta vacía/falsa | `RealtimeMetricsView` |

El efecto TDD se logra escribiendo primero los tests contra los CAs del UC, verificando que fallen (Red), luego implementando hasta que pasen (Green), y refactorizando sin romper (Refactor).

---

## Principios del plan

1. **Un UC = una FASE mínima.** Los UCs CRÍTICOS son FASEs independientes; los MEDIOS/BAJOS se pueden agrupar.
2. **Tests primero, siempre.** Cada FASE comienza con la sección de tests; el código viene después.
3. **Sin deuda técnica.** Si un test existente verifica comportamiento incorrecto, se corrige en la misma FASE.
4. **IACT-db es inmutable desde IACT-api.** Solo lectura de MariaDB vía SPs y vistas. PostgreSQL para tablas de IACT.
5. **Los UCs de CTI quedan fuera.** UC_OPR, UC_CLI, UC_SUP_01..02 son capa de telefonía — no entran en este plan.

---

## Mapa de gaps: UCs documentados vs implementación actual

### Cluster PIPELINE (UC_PIP)

| UC | Nombre | Estado actual | Gap |
|---|---|---|---|
| UC_PIP_01 | Supervisar ETL | `etl_status` existe | CA-04 caché ausente; CA-02 stale detection incompleta |
| UC_PIP_02 | Ver Errores ETL | `etl_errors` existe | CA-05 PII scrubbing ausente en stack traces |
| UC_PIP_03 | Ver Disponibilidad Datos | `etl_data_availability` existe | CA-05 thresholds en settings, no hardcoded |
| UC_PIP_04 | Solicitar Reintento | `etl_retry` existe | CA validations incompletas: reason ≥ 20 chars, no RUNNING |

### Cluster REPORTS (UC_RPT)

| UC | Nombre | Estado actual | Gap |
|---|---|---|---|
| UC_RPT_01 | Ver Dashboard | **No implementado** | Endpoint completo con KPIs de IVR |
| UC_RPT_02 | Ver Métricas Tiempo Real | Stub `RealtimeMetricsView` | CNST: no WebSockets/SSE; stub correcto — aclarar en response |
| UC_RPT_03 | Ver Reportes Históricos | `ReportViewSet` existe | No lee datos de IVR; solo Django ORM |
| UC_RPT_04 | Exportar Reporte | `ExportJobViewSet` existe | Sin datos IVR; worker no genera archivo real |
| UC_RPT_07 | Programar Reporte | `ScheduledReportViewSet` existe | Sin job scheduler real |
| UC_RPT_08..11 | Reportes programados / filtros / vistas guardadas | ViewSets existen | Funcionalidad incompleta |
| UC_RPT_12..17 | Reportes IVR vía SPs | Implementados en FASES 1-8 | **Cubiertos** |

### Cluster LOGS (UC_LOG)

| UC | Nombre | Estado actual | Gap |
|---|---|---|---|
| UC_LOG_01..07 | Logs del sistema | Implementados | **Cubiertos** |
| UC_LOG_08 | Pipeline Event Log | Implementado en FASE 4 | **Cubierto** |

### Cluster ACCESS/PERMISSIONS (UC_ACC, UC_PERM)

| UC | Nombre | Estado actual | Gap |
|---|---|---|---|
| UC_ACC_01 | Asignar Funciones | `UserFunctionAssignView` existe | Sin throttle 30/min; sin audit `FUNCTION_ASSIGNED` |
| UC_ACC_02 | Revocar Funciones | `UserFunctionRevokeView` existe | Sin anti-self-revoke; sin warnings calculator |
| UC_ACC_03 | Consultar Permisos | `EffectivePermissionsView` existe | **Cubrir CA completos** |
| UC_ACC_04 | Asignar Grupo | `UserAccessGroupViewSet` existe | Sin SoD validator en assign |
| UC_ACC_05 | Gestionar AccessGroup | `AccessGroupViewSet` existe | Sin validación unicidad funciones |
| UC_ACC_08..09 | Expirar/Auditar permisos | Parcial | Sin `expire_exceptional_permissions` command completo |
| UC_PERM_07 | **Verificar Permiso** | **No implementado como endpoint** | Endpoint `GET /api/access/permissions/verify/` |
| UC_PERM_08..10 | Ver funciones propias, Expiración alerta | Parcial | Gaps en respuesta |

### Objetos IACT-db sin endpoint

| Objeto | Tipo | Endpoint propuesto |
|---|---|---|
| `v_sla_distribucion` | Vista MariaDB | `GET /api/reports/ivr/sla-distribution/` |
| `v_quarter_actual` | Vista MariaDB | `GET /api/pipeline/current-quarter/` |

---

## FASE 9 — `GET /api/reports/dashboard/` (UC_RPT_01 — CRÍTICO)

**Prioridad:** CRÍTICA. UC_RPT_01 es uno de los 8 UCs críticos del sistema — sin él, IACT no entrega su propósito principal.

### 9.1 Tests a escribir primero

Archivo: `tests/unit/reports/test_dashboard_view.py`

```python
# CA-01: Dashboard básico con datos
def test_dashboard_returns_kpis_with_data(authenticated_client, mock_ivr_conn):
    # DADO usuario con 'reports.view_ivr' y datos en MariaDB
    # ENTONCES 200 con total_abandonadas, pct_abandono, total_clientes, quarter_actual

# CA-02: Sin datos → KPIs en 0
def test_dashboard_returns_zeros_without_data(authenticated_client, mock_ivr_empty):
    # ENTONCES 200 con KPIs en 0, message='Sin datos para el quarter actual'

# CA-03: Sin permiso → 403
def test_dashboard_requires_reports_view_ivr(api_client, user_without_permission):
    # ENTONCES 403

# CA-04: MariaDB no disponible → 503
def test_dashboard_503_on_mariadb_unavailable(authenticated_client, mock_ivr_timeout):
    # ENTONCES 503

# CA-05: quarter_actual viene de v_quarter_actual
def test_dashboard_uses_v_quarter_actual(authenticated_client, mock_ivr_conn):
    # VERIFICAR que el quarter en response proviene de v_quarter_actual
```

Archivo: `tests/integration/reports/test_dashboard_integration.py`

```python
# Integración completa: GET /api/reports/dashboard/ → MariaDB → respuesta
def test_dashboard_end_to_end(authenticated_admin_client, real_mariadb):
    # Requiere MariaDB real con datos en base_ivr_detalle
```

### 9.2 Implementación requerida

**Servicio nuevo** — `apps/reports/ivr_services.py`:

```python
def get_dashboard_summary() -> dict:
    """
    UC_RPT_01 — KPIs ejecutivos del dashboard.
    Combina v_quarter_actual + v_sla_distribucion + sp_rpt_resumen_abandono_rollup.
    """

def get_current_quarter() -> str:
    """Lee v_quarter_actual en MariaDB."""
```

**View nueva** — `apps/reports/ivr_views.py`:

```python
@extend_schema(
    summary="UC_RPT_01 — Dashboard ejecutivo IVR",
    tags=["Reportes de Llamadas"],
    ...
)
class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'reports.view_ivr'

    def get(self, request):
        # 1. Obtener quarter actual de v_quarter_actual
        # 2. Obtener resumen de abandono de sp_rpt_resumen_abandono_rollup
        # 3. Obtener distribución SLA de v_sla_distribucion
        # 4. Retornar payload estructurado
```

**Ruta** — `apps/reports/urls.py`:
```
path('dashboard/', DashboardSummaryView.as_view(), name='ivr-dashboard'),
```

**Respuesta esperada:**
```json
{
  "quarter": "Q02_26",
  "quarter_fecha_inicio": "2026-04-01",
  "quarter_fecha_fin": "2026-06-30",
  "abandono": {
    "total_abandonadas": 12450,
    "pct_del_quarter": 100.0,
    "por_segmento": [...]
  },
  "sla": {
    "dentro_sla": 18,
    "riesgo_sla": 4,
    "fuera_sla": 2,
    "total_centros": 24
  },
  "data_freshness": "ok"
}
```

### 9.3 Tests que cambian

`tests/unit/reports/test_cnst007_compliance.py` — verificar que el dashboard respeta límites.

---

## FASE 10 — Nuevas vistas IACT-db: `v_sla_distribucion` y `v_quarter_actual`

**Prioridad:** ALTA. Objetos ya implementados en IACT-db sin exposición en IACT-api.

### 10.1 Tests a escribir primero

Archivo: `tests/unit/reports/test_sla_distribution_view.py`

```python
# GET /api/reports/ivr/sla-distribution/
def test_sla_distribution_returns_pivot_by_quarter(authenticated_client, mock_ivr_conn):
    # DADO v_sla_distribucion con datos
    # ENTONCES columnas: trimestre, fuera_sla, riesgo_sla, dentro_sla,
    #          activo_hoy, volumen_medio, bajo_volumen, total_centros

def test_sla_distribution_empty_on_no_data(authenticated_client, mock_ivr_empty):
    # ENTONCES total: 0, data: []

def test_sla_distribution_requires_permission(api_client):
    # 401 sin autenticación
```

Archivo: `tests/unit/pipeline/test_current_quarter_view.py`

```python
# GET /api/pipeline/current-quarter/
def test_current_quarter_returns_quarter_name(authenticated_client, mock_ivr_conn):
    # DADO v_quarter_actual con datos
    # ENTONCES quarter, tabla_origen, fecha_inicio, fecha_fin

def test_current_quarter_503_on_mariadb_unavailable(authenticated_client):
    # ENTONCES 503
```

### 10.2 Implementación requerida

**En `ivr_services.py`:**
```python
def get_sla_distribution() -> list[dict]:
    """Lee v_sla_distribucion — pivot SLA por quarter."""
    with connections['ivr'].cursor() as cursor:
        cursor.execute(
            "SELECT trimestre, fuera_sla, riesgo_sla, dentro_sla, "
            "activo_hoy, volumen_medio, bajo_volumen, total_centros "
            "FROM v_sla_distribucion ORDER BY trimestre"
        )
        ...

def get_current_quarter() -> dict:
    """Lee v_quarter_actual — quarter activo calculado por MariaDB."""
    with connections['ivr'].cursor() as cursor:
        cursor.execute(
            "SELECT quarter, tabla_origen, fecha_inicio, fecha_fin "
            "FROM v_quarter_actual"
        )
        ...
```

**Views nuevas:**
- `SlaDistributionView` → `GET /api/reports/ivr/sla-distribution/` — RBAC: `reports.view_ivr`
- `CurrentQuarterView` → `GET /api/pipeline/current-quarter/` — RBAC: `pipeline.view_status`

---

## FASE 11 — Refuerzo UC_PIP_01..04 contra criterios de aceptación

**Prioridad:** ALTA. Los endpoints existen pero los CAs documentados no se cumplen.

### 11.1 UC_PIP_01 — Caché (CA-04) y stale detection (CA-02)

**Tests a escribir/corregir:**

```python
# tests/unit/pipeline/test_views.py — ampliar
def test_etl_status_uses_cache_on_hit(authenticated_client, mock_cache):
    # CA-04: segunda llamada debe llegar del cache, no de MariaDB

def test_etl_status_marks_stale_when_no_recent_success(authenticated_client, mock_mariadb):
    # CA-02: si última exitosa > 14h → status='degradado'; > 24h → 'critico'

def test_etl_status_403_without_permission(api_client, user_no_permissions):
    # CA-05

def test_etl_status_503_on_mariadb_timeout(authenticated_client, mock_timeout):
    # CA-06
```

**Implementación:**
- Agregar `cache.get/set` con TTL=30s en `etl_status`
- `_build_pipeline_health_summary` ya implementa la lógica de stale — verificar umbrales contra thresholds configurables en settings

### 11.2 UC_PIP_02 — PII scrubbing (CA-05)

**Tests:**
```python
def test_etl_errors_sanitizes_phone_numbers_in_stack_traces(authenticated_client, mock_mariadb):
    # CA-05: stack traces con teléfonos → reemplazados por [REDACTED_PHONE]

def test_etl_errors_sanitizes_emails_in_stack_traces(authenticated_client, mock_mariadb):
    # CA-05: emails → [REDACTED_EMAIL]
```

**Implementación:**
- Función `_sanitize_stack_trace(text: str) -> str` en `pipeline/views.py`
- Regex para detectar y redactar teléfonos y emails

### 11.3 UC_PIP_04 — Validaciones completas (CA-04)

**Tests:**
```python
def test_etl_retry_rejects_reason_under_20_chars(authenticated_client):
    # CA-04.1: reason = "corto" → 400

def test_etl_retry_rejects_when_pipeline_running(authenticated_client, mock_running):
    # CA-04.3: pipeline.status = 'RUNNING' → 409 ALREADY_RUNNING

def test_etl_retry_rejects_when_last_run_not_failed(authenticated_client, mock_success):
    # CA-04.4: último run = SUCCESS → 409 LAST_RUN_NOT_FAILED

def test_etl_retry_emits_audit_event(authenticated_client, mock_audit):
    # CA-06: AuditLog 'PIPELINE_RETRY_REQUESTED' emitido con actor + reason
```

**Implementación:**
- Agregar validación `len(reason) < 20` en `etl_retry`
- Verificar status del último run en MariaDB antes de encolar
- Emitir `AuditLog` via `apps.audit.services.AuditLogService`

---

## FASE 12 — `UC_PERM_07`: Verificar Permiso (CRÍTICO)

**Prioridad:** CRÍTICA. UC_PERM_07 es uno de los 8 UCs críticos — es el gate de seguridad universal.

### 12.1 Tests a escribir primero

Archivo: `tests/unit/access/test_permission_verify_view.py`

```python
# GET /api/access/permissions/verify/?function=reports.view_ivr
def test_verify_permission_returns_true_for_assigned_function(
        authenticated_client, user_with_function):
    # ENTONCES 200, {"has_permission": true, "function": "reports.view_ivr"}

def test_verify_permission_returns_false_for_unassigned_function(
        authenticated_client, user_without_function):
    # ENTONCES 200, {"has_permission": false}

def test_verify_permission_requires_authentication(api_client):
    # ENTONCES 401

def test_verify_permission_validates_function_exists(authenticated_client):
    # DADO function="FUNCION_INEXISTENTE"
    # ENTONCES 400 INVALID_FUNCTION

def test_verify_permission_works_for_superuser(superuser_client):
    # ENTONCES 200, {"has_permission": true} siempre

def test_verify_permission_batch_check_multiple_functions(authenticated_client):
    # GET ?functions=reports.view_ivr,pipeline.view_status
    # ENTONCES {"results": {"reports.view_ivr": true, "pipeline.view_status": false}}
```

### 12.2 Implementación requerida

**View nueva** — `apps/access/views.py`:

```python
@extend_schema(
    summary="UC_PERM_07 — Verificar permiso de función RBAC",
    parameters=[
        OpenApiParameter('function', str, description='Código de función a verificar'),
        OpenApiParameter('functions', str, description='Funciones separadas por coma (batch)'),
    ],
    tags=["Control de Acceso"],
)
class PermissionVerifyView(APIView):
    """
    UC_PERM_07 — Gate de seguridad universal.
    GET /api/access/permissions/verify/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        function_code = request.query_params.get('function')
        functions_raw = request.query_params.get('functions')
        # Verificar contra UserFunctionAssignment o is_superuser
        # Retornar {has_permission: bool} o {results: {fn: bool}}
```

**Ruta** — `apps/access/urls.py`:
```python
path('permissions/verify/', PermissionVerifyView.as_view(), name='permission-verify'),
```

---

## FASE 13 — UC_ACC_01/02: Asignar/Revocar Funciones — completar CAs

**Prioridad:** ALTA. Los endpoints existen pero faltan guardianes de negocio críticos.

### 13.1 Tests a escribir primero

```python
# tests/unit/access/test_function_assignment.py
def test_assign_function_emits_audit_event(authenticated_admin, mock_audit):
    # CA: AuditLog 'FUNCTION_ASSIGNED' emitido

def test_assign_function_throttled_at_30_per_minute(authenticated_admin):
    # CA: 31 llamadas → 429 Too Many Requests

def test_revoke_function_anti_self_revoke(authenticated_admin):
    # CA: admin se revoca a sí mismo → 400 SELF_REVOKE_FORBIDDEN
    # P-11 del UC_ACC_02

def test_revoke_function_warns_when_user_has_no_functions_left(authenticated_admin):
    # CA: última función → response incluye "warnings": ["no_functions"]

def test_revoke_function_warns_when_last_holder(authenticated_admin):
    # CA: único holder de una función crítica → warnings: ["last_holder"]
```

### 13.2 Implementación requerida

- Throttle `ThrottlePolicy(30/min/invoker)` en `UserFunctionAssignView`
- Anti-self-revoke guard en `UserFunctionRevokeView`
- `WarningsCalculator` service: `no_functions`, `critical_function`, `last_holder`
- Integración con `AuditLogService.emit('FUNCTION_ASSIGNED', ...)`

---

## FASE 14 — UC_ACC_04: SoD Validator en asignación de AccessGroup

**Prioridad:** MEDIA. El viewset existe pero no valida Separation of Duties al asignar.

### 14.1 Tests

```python
# tests/unit/access/test_access_group_sod.py
def test_assign_group_raises_sod_conflict(authenticated_admin, conflicting_group):
    # CA: asignar grupo que viola SeparationRule existente → 409 SOD_CONFLICT

def test_assign_group_succeeds_without_sod_conflict(authenticated_admin, clean_group):
    # CA: sin conflicto → 201 Created

def test_sod_conflict_reports_conflicting_functions(authenticated_admin, conflicting_group):
    # CA: response incluye qué funciones están en conflicto
```

### 14.2 Implementación

- `SoDValidator.check(user, access_group)` en `apps/access/services/`
- Llamar en `UserAccessGroupViewSet.perform_create()`

---

## FASE 15 — `UC_SUP_03`: Broadcast Team Messages

**Prioridad:** MEDIA. Es el único UC_SUP implementable en IACT-api (los otros son CTI).

### 15.1 Contexto

UC_SUP_01 (monitor_live_calls) y UC_SUP_02 (barge_in_calls) requieren integración con telefonía CTI — fuera de scope. UC_SUP_03 (broadcast_team_messages) es un mensaje interno vía InternalMailbox — sí implementable en IACT-api dado que `InternalMessage` ya existe en `apps.alerts`.

### 15.2 Tests

```python
# tests/unit/alerts/test_broadcast_view.py
def test_broadcast_sends_to_all_users_in_team(authenticated_supervisor, mock_team):
    # POST /api/alerts/broadcast/ con type='info', message='...', team_id=X
    # ENTONCES InternalMessage creado para cada miembro del team

def test_broadcast_urgente_marks_all_messages_urgent(authenticated_supervisor):
    # type='urgente' → InternalMessage.priority='URGENTE'

def test_broadcast_requires_broadcast_team_messages_function(authenticated_client):
    # Sin función 'broadcast_team_messages' → 403
```

### 15.3 Implementación

- View nueva `BroadcastTeamMessageView` en `apps/alerts/views.py`
- Endpoint: `POST /api/alerts/broadcast/`
- RBAC: `broadcast_team_messages` (agregar a `create_functions.py`)

---

## FASE 16 — Infrastructure: DB router y test configuration

**Prioridad:** ALTA — sin esto los tests de integración fallan al crear la BD de test.

### 16.1 Tests a escribir primero

```python
# tests/unit/config/test_db_router.py
def test_ivr_router_allow_migrate_returns_false(db):
    # IVRRouter.allow_migrate(db='ivr', app_label=...) == False (no None)

def test_ivr_router_allow_migrate_returns_none_for_default(db):
    # IVRRouter.allow_migrate(db='default', app_label='ivr') == None (delega)

def test_test_database_ivr_name_is_none():
    # DATABASES['ivr']['TEST']['NAME'] is None
    # → Django no intenta crear test_ivr_legacy
```

### 16.2 Implementación

`config/db_router.py`:
```python
def allow_migrate(self, db, app_label, model_name=None, **hints):
    if db == 'ivr':
        return False    # antes: return None → causa migrations en MariaDB
    if app_label == 'ivr':
        return False
    return None
```

`config/settings/base.py` (sección DATABASES):
```python
'ivr': {
    ...
    'TEST': {
        'NAME': None,   # Django no crea test_ivr_legacy
    },
}
```

---

## FASE 17 — Completar cobertura de `UC_LOG_01..07` con tests de integración

**Prioridad:** MEDIA. Las views existen pero los tests son solo unitarios con mocks.

### 17.1 Tests de integración a crear

```python
# tests/integration/logs/test_log_endpoints.py

def test_django_log_tail_requires_logs_view_function(api_client, user_without_permission):
    # 403

def test_django_log_tail_returns_lines_list(authenticated_admin):
    # 200 con {"lines": [...], "file": "..."}

def test_log_export_requires_logs_export_function(api_client, user_without_permission):
    # 403

def test_pipeline_event_log_filters_by_error_type(authenticated_admin, mock_mariadb):
    # GET /api/logs/pipeline-events/?error_type=PARAM_INVALIDO
    # ENTONCES solo eventos de ese tipo
```

---

## Orden de ejecución recomendado

```
FASE 16 (infra) → FASE 9 (dashboard CRÍTICO) → FASE 12 (verify CRÍTICO)
    → FASE 10 (vistas IACT-db) → FASE 11 (PIP refuerzo)
    → FASE 13 (ACC_01/02) → FASE 14 (SoD) → FASE 15 (SUP_03)
    → FASE 17 (LOG integración)
```

La FASE 16 va primero porque sin el fix del router, los tests de integración que usan `pytest.mark.django_db` pueden fallar al intentar crear `test_ivr_legacy`.

---

## Tabla de nuevas funciones RBAC requeridas

Las siguientes funciones RBAC deben agregarse a `create_functions.py` antes o durante la FASE correspondiente:

| Código | Permission Django | UC relacionado | FASE |
|---|---|---|---|
| `DASH_VIEW_IVR` | `reports.view_dashboard` | UC_RPT_01 | 9 |
| `SLA_VIEW` | `reports.view_sla` | FASE 10 | 10 |
| `PERM_VERIFY` | `access.verify_permission` | UC_PERM_07 | 12 |
| `BROADCAST_TEAM` | `alerts.broadcast_team` | UC_SUP_03 | 15 |

---

## Tests existentes que necesitan corrección

| Archivo | Problema | FASE correctora |
|---|---|---|
| `tests/unit/pipeline/test_views.py` | No verifica caché (CA-04) ni stale (CA-02) de UC_PIP_01 | FASE 11 |
| `tests/unit/access/test_views.py` | No verifica throttle ni audit en assign/revoke | FASE 13 |
| `tests/integration/pipeline/test_ivr_endpoints.py` | No verifica PII scrubbing en errores | FASE 11 |
| `tests/unit/reports/test_report_model.py` | Verifica solo modelo Django, no datos IVR | FASE 9 |

---

## Criterios de "DONE" por FASE

Cada FASE se considera terminada cuando:

1. Todos los tests de esa FASE pasan (`pytest -k "test_fase_N"`)
2. No hay regresión en tests de FASEs anteriores
3. Sintaxis válida en todos los archivos modificados
4. `@extend_schema` completo en todos los endpoints nuevos (summary + description + tags + responses + required_function)
5. Hallazgos documentados en `docs/architecture/HALLAZGOS-FASEXX-*.md`
6. Commit convencional: `feat/fix/refactor(scope): descripcion`

---

## Relación con IACT-docs `feature/wp-content-5-6-diagram-types`

El branch agrega documentación UML PlantUML para los 97 UCs del catálogo completo, especialmente diagramas de componentes (tipo 5) y despliegue (tipo 6). Para este plan de implementación, los artefactos más relevantes son:

- **Diagrama de secuencias** de UC_RPT_01 (FASE 9): define el flujo GET → JWT → RBAC → caché → MariaDB → payload
- **Diagrama de estados** de UC_ACC_01/02 (FASE 13): define transiciones ACTIVE → REVOKED de `UserFunctionAssignment`
- **Diagrama de componentes** del sistema: confirma la separación IACT-api / IACT-db y que los SPs son la frontera de integración

La convención del proyecto establece PlantUML (no Mermaid) para todos los diagramas. Si durante la implementación se generan diagramas arquitectónicos adicionales, deben seguir esta convención.

---

## Resumen de volumen estimado

| FASE | UCs cubiertos | Archivos nuevos | Archivos modificados | Tests nuevos |
|---|---|---|---|---|
| FASE 16 | — (infra) | 0 | 2 | 3 |
| FASE 9 | UC_RPT_01 | 1 view, 1 service fn | 2 | 5 |
| FASE 10 | 2 vistas IACT-db | 2 views, 2 service fns | 2 | 6 |
| FASE 11 | UC_PIP_01..04 | 1 utility fn | 2 | 8 |
| FASE 12 | UC_PERM_07 | 1 view | 2 | 6 |
| FASE 13 | UC_ACC_01..02 | 1 service, 1 calculator | 2 | 5 |
| FASE 14 | UC_ACC_04 | 1 validator | 1 | 3 |
| FASE 15 | UC_SUP_03 | 1 view | 2 | 3 |
| FASE 17 | UC_LOG_01..08 | 1 integration test file | 1 | 8 |
| **Total** | **~20 UCs** | **~8 archivos** | **~16 archivos** | **~47 tests** |
