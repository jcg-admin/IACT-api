# Plan de Implementación TDD — IACT-api
## Fuente: IACT-docs `source/requisitos` y `source/arquitectura-tecnica`

**Versión:** 2.0.0
**Fecha:** 2026-05-13
**Rama IACT-docs:** `feature/wp-content-5-6-diagram-types`
**Metodología:** Red → Green → Refactor estricto por cada criterio de aceptación (CA)
**Principio:** Los UCs de IACT-docs son la fuente de verdad. El código existente se evalúa
contra sus CAs — si no los cumple, se corrige aunque el test anterior lo diera como verde.

---

## Por qué este plan es diferente al anterior

El plan v1.0.0 partió del código existente y preguntó "¿qué falta?".
Este plan parte de los **61 UCs documentados** y pregunta "¿cada CA está implementado y testado correctamente?".

La diferencia no es menor: la auditoría profunda de `requisitos/` reveló:

1. **Funciones RBAC desincronizadas**: el código usa `'logs.view'`, `'pipeline.view_status'`, `'reports.view_ivr'` — cadenas que **no existen en el catálogo v5.4.0**. El modelo canónico usa `view_application_logs` (LOG-001), `view_pipeline_status` (PIP-001), `view_reports` (RPT-001).

2. **T-02 ausente como servicio**: UC_PERM_07 (Verificar Permiso) es invocado implícitamente por **59/61 UCs** como dependencia transversal. Sin él implementado como `PermissionService` con cache y precedencia completa, todos los endpoints tienen un gate de seguridad incompleto.

3. **T-03 sin cobertura universal**: AuditEvent debe emitirse en **35/61 UCs**. Los que existen omiten o simulan la emisión.

4. **CAs de negocio no testados**: UC_AUTH_01 tiene 15 CAs documentados; los tests actuales cubren el happy path pero no CA-02 (sesión única), CA-03 (atomicidad rollback), CA-04 (first_login scope reducido), CA-06 (no_permissions warning).

5. **InternalMailbox sin implementar**: UC_USR_01, UC_AUTH_03, UC_AUTH_01 (FA-01) y UC_ALR_05 envían mensajes vía `InternalMailbox` — modelo que no existe en el código.

---

## Mapa de dependencias (fuente: `matriz-dependencias-uc-iact.rst`)

```
T-01: Session activa           → prerequisito de 59/61 UCs
T-02: UC_PERM_07 (gate RBAC)   → prerequisito de 59/61 UCs
T-03: AuditEvent emission      → prerequisito de 35/61 UCs

UCs raíz (sin dependencias UC explícitas, solo T-01/02/03):
  UC_AUTH_01, UC_USR_02, UC_ACC_03, UC_ACC_05,
  UC_PERM_05, UC_PERM_07, UC_RPT_01 (*),
  UC_ALR_01, UC_PIP_01, UC_AUD_01,
  UC_LOG_01, UC_LOG_05, UC_LOG_06, UC_LOG_07

(*) UC_RPT_01 requiere datos de UC_PIP_01 — es raíz estructural pero no de datos.
```

---

## FASE 0 — Prerequisitos transversales e infraestructura

**Por qué existe FASE 0:** Las dependencias T-01, T-02 (parcialmente), T-03 y el catálogo
RBAC deben estar operativos antes de implementar cualquier UC. Sin ellos, los tests de
cualquier UC fallarán por razones de infraestructura, no de lógica de negocio.

### F0-T1 — Infraestructura de base de datos

**Archivos:** `config/db_router.py`, `config/settings/base.py`

**Tests primero** (`tests/unit/config/test_db_router.py`):
```python
# Problema actual: allow_migrate devuelve None para 'ivr' → puede causar
# migrations accidentales en MariaDB en entornos sin la BD de test.
def test_ivr_router_allow_migrate_returns_false_not_none():
    # IVRRouter.allow_migrate(db='ivr', ...) IS False  (no None)

def test_ivr_test_database_name_is_none():
    # settings.DATABASES['ivr']['TEST']['NAME'] IS None
    # → Django no intenta crear test_ivr_legacy

def test_ivr_router_blocks_writes():
    # IVRRouter.db_for_write(model, hints) raises ProtectedError
    # o devuelve None dependiendo del diseño actual
```

**Implementación:**
- `allow_migrate` retorna `False` (no `None`) para `db='ivr'`
- `DATABASES['ivr']['TEST'] = {'NAME': None}`

### F0-T2 — Catálogo RBAC v5.4.0: 61 funciones + 10 AGRs + 3 SoD

**Fuente:** `arquitectura-tecnica/rbac/modelo-rbac-iact.rst` v5.4.0

El catálogo actual en `create_functions.py` usa nombres de función arbitrarios (`'logs.view'`, `'pipeline.view_status'`) que **no coinciden con el modelo canónico**. Los nombres canónicos son verbos en inglés (`view_application_logs`, `view_pipeline_status`).

**Tests primero** (`tests/unit/access/test_rbac_catalog.py`):
```python
# Las 61 funciones del catálogo v5.4.0
EXPECTED_FUNCTIONS_V540 = [
    # MOD_Auth (4)
    ('AUTH-001', 'view_own_sessions'),
    ('AUTH-002', 'close_user_session'),
    ('AUTH-003', 'reset_password'),
    ('AUTH-004', 'view_all_active_sessions'),
    # MOD_Users (9)
    ('USR-001', 'create_users'),
    ('USR-002', 'update_users'),
    ('USR-003', 'deactivate_users'),
    ('USR-004', 'list_users'),
    ('USR-005', 'search_users'),
    ('USR-006', 'block_users'),
    ('USR-007', 'unblock_users'),
    ('USR-008', 'reactivate_users'),
    ('USR-009', 'view_users'),
    # MOD_Access (12)
    ('ACC-001', 'assign_functions'),
    ('ACC-002', 'revoke_functions'),
    ('ACC-003', 'view_assignments'),
    ('ACC-004', 'assign_function_groups'),
    ('ACC-005', 'view_separation_rules'),
    ('ACC-006', 'create_function_group'),
    ('ACC-007', 'assign_functions_to_group'),
    ('ACC-008', 'grant_exceptional_permission'),
    ('ACC-009', 'revoke_exceptional_permission'),
    ('ACC-010', 'revoke_function_group'),
    ('ACC-011', 'update_separation_rule'),
    ('ACC-012', 'disable_separation_rule'),
    # MOD_Pipeline (4)
    ('PIP-001', 'view_pipeline_status'),
    ('PIP-002', 'view_pipeline_errors'),
    ('PIP-003', 'view_data_availability'),
    ('PIP-004', 'request_pipeline_retry'),
    # MOD_Reports (11)
    ('RPT-001', 'view_reports'),
    ('RPT-002', 'view_dashboard'),
    ('RPT-003', 'filter_reports'),
    ('RPT-004', 'export_csv'),
    ('RPT-005', 'export_excel'),
    ('RPT-006', 'export_pdf'),
    ('RPT-007', 'view_kpis'),
    ('RPT-008', 'view_charts'),
    ('RPT-009', 'schedule_report'),
    ('RPT-010', 'save_view'),
    ('RPT-011', 'share_report'),
    # MOD_Alerts (10)
    ('ALR-001', 'view_alerts'),
    ('ALR-002', 'configure_alerts'),
    ('ALR-003', 'configure_team_alerts'),
    ('ALR-004', 'pause_alerts'),
    ('ALR-005', 'disable_alerts'),
    ('ALR-006', 'view_alert_history'),
    ('ALR-007', 'acknowledge_alert'),
    ('ALR-008', 'subscribe_to_alert'),
    ('ALR-009', 'unsubscribe_from_alert'),
    ('ALR-010', 'configure_subscription_severity'),
    # MOD_Audit (4)
    ('AUD-001', 'view_audit_log'),
    ('AUD-002', 'search_audit_log'),
    ('AUD-003', 'export_audit_log'),
    ('AUD-004', 'generate_compliance_report'),
    # MOD_Logs (7)
    ('LOG-001', 'view_application_logs'),
    ('LOG-002', 'export_logs'),
    ('LOG-003', 'search_logs'),
    ('LOG-004', 'view_etl_logs'),
    ('LOG-005', 'view_infrastructure_logs'),
    ('LOG-006', 'view_system_health'),
    ('LOG-007', 'view_technical_metrics'),
]

@pytest.mark.django_db
def test_function_catalog_has_61_functions():
    from apps.access.models import Function
    assert Function.objects.count() == 61

@pytest.mark.django_db
def test_all_canonical_function_codes_exist():
    from apps.access.models import Function
    for func_id, func_name in EXPECTED_FUNCTIONS_V540:
        assert Function.objects.filter(
            code=func_id, name=func_name
        ).exists(), f"Missing: {func_id} {func_name}"

@pytest.mark.django_db
def test_10_access_groups_exist():
    from apps.access.models import AccessGroup
    assert AccessGroup.objects.count() == 10

@pytest.mark.django_db
def test_3_sod_rules_exist():
    from apps.access.models import SeparationRule
    assert SeparationRule.objects.filter(
        state='ENABLED'
    ).count() == 3
```

**Implementación:**
- Reescribir `apps/access/management/commands/create_functions.py` con las 61 funciones v5.4.0
- Crear `apps/access/management/commands/create_access_groups.py` (10 AGRs)
- Crear `apps/access/management/commands/create_sod_rules.py` (3 reglas)
- Actualizar todos los `required_function` en views existentes a los nombres canónicos

### F0-T3 — InternalMailbox model y servicio

**Fuente:** `arquitectura-tecnica/modelo-dominio-iact.rst` § 4.1; CNST-001, CNST-002; UC_AUTH_01 CA-02, UC_USR_01 CA-01, UC_AUTH_03 CA-01

**Tests primero** (`tests/unit/core/test_internal_mailbox.py`):
```python
@pytest.mark.django_db
def test_internal_mailbox_created_with_user():
    # CA (UC_USR_01): crear User → InternalMailbox creado automáticamente
    user = UserTestData()
    assert InternalMailbox.objects.filter(owner_user_id=user.pk).exists()

@pytest.mark.django_db
def test_deliver_message_creates_internal_message(user):
    # CNST-001: InternalMailbox.deliver_message() → InternalMessage en BD
    mailbox = InternalMailbox.objects.get(owner_user_id=user.pk)
    mailbox.deliver_message(
        subject='Contraseña temporal',
        body='Tu contraseña es: Temp123!',
        sender_system=True
    )
    assert InternalMessage.objects.filter(
        mailbox=mailbox, subject='Contraseña temporal'
    ).exists()

@pytest.mark.django_db
def test_deliver_message_never_sends_email(user, mock_send_mail):
    # CNST-001: PROHIBIDO email externo
    mailbox = InternalMailbox.objects.get(owner_user_id=user.pk)
    mailbox.deliver_message(subject='Test', body='Test')
    mock_send_mail.assert_not_called()
```

**Implementación:**
- Modelo `InternalMailbox` en `apps/alerts/models.py` (o `apps/core/`)
- Señal `post_save` en `User` → crear `InternalMailbox` automáticamente
- Servicio `MailboxService.deliver(user_id, subject, body)`

### F0-T4 — AuditEvent como servicio universal (T-03)

**Fuente:** BR-008, BR-010, CNST-025, CNST-026; `arquitectura-tecnica/modelo-dominio-iact.rst` § 4.7

**Tests primero** (`tests/unit/audit/test_audit_service_universal.py`):
```python
@pytest.mark.django_db
def test_audit_event_is_append_only():
    # BR-010: una vez creado, no puede ser modificado ni eliminado
    event = AuditLogTestData()
    with pytest.raises(Exception):
        event.delete()  # debe estar protegido a nivel de model

@pytest.mark.django_db
def test_audit_event_payload_has_no_password():
    # CNST-026: sin PII en payload
    service = AuditLogService()
    event = service.emit(
        event_type='LOGIN',
        actor_user_id=1,
        payload={'username': 'user', 'password': 'secret123'}
    )
    # El payload en BD no contiene 'password'
    saved = AuditLog.objects.get(pk=event.pk)
    assert 'password' not in str(saved.details)

@pytest.mark.django_db
def test_audit_event_emit_returns_id():
    # CA (UC_PERM_09): emit básico → AuditEvent persistido + id
    service = AuditLogService()
    event = service.emit(
        event_type='LOGIN',
        actor_user_id=1,
        payload={'test': True}
    )
    assert event.pk is not None

def test_audit_emit_raises_on_unknown_event_type():
    # CA (UC_PERM_09 CA-03): event_type desconocido → AuditValidationError
    service = AuditLogService()
    with pytest.raises(AuditValidationError):
        service.emit(event_type='TIPO_INVENTADO', actor_user_id=1)
```

---

## FASE 1 — Los 8 UCs CRÍTICOS

**Orden de implementación** (respeta el grafo de dependencias):

```
UC_AUTH_01 ──────────────────────────────── 5 días  (raíz)
UC_PERM_07 (T-02 completo)  ─────────────── 4 días  (raíz, gate universal)
UC_USR_02 ───────────────────────────────── 3 días  (raíz)
UC_ACC_03 ───────────────────────────────── 3 días  (raíz)
UC_PIP_01 ───────────────────────────────── 4 días  (raíz)
UC_AUD_01 ───────────────────────────────── 3 días  (raíz)
UC_AUTH_04 ──────────────────────────────── 2 días  (requiere UC_AUTH_01)
UC_RPT_01 ───────────────────────────────── 5 días  (requiere datos de UC_PIP_01)
```

### FASE 1.1 — UC_AUTH_01: Iniciar Sesión

**Fuente:** `casos-uso/auth/uc-auth-01/` (12 partes)
**Función RBAC:** pública (post-login usa AUTH-001)
**Clases de dominio:** `Session`, `User`, `AuditEvent`

**Tests a escribir/corregir** (`tests/unit/authentication/test_uc_auth_01.py`):

```python
# CA-01: Login exitoso (happy path)
def test_login_happy_path():
    # POST /api/auth/login/ con credenciales correctas
    # ENTONCES 200, tokens.access, tokens.refresh, next_step=null, warning=null
    # Session con state=ACTIVE, expires_at=started_at+15min
    # AuditEvent LOGIN con actor_user_id, sin password ni tokens en payload

# CA-02: Sesión única (BR-005, CNST-002)
def test_login_supersedes_previous_session():
    # DADO Session S1 ACTIVE previa
    # ENTONCES S1.state='CLOSED', S1.close_reason='SUPERSEDED'
    # AuditEvent SESSION_CLOSED para S1

# CA-03: Atomicidad — rollback si BD falla en AuditEvent
def test_login_rollback_on_db_failure():
    # DADO BD falla en INSERT AuditEvent DESPUÉS del INSERT Session
    # ENTONCES 503, NO Session en BD, NO tokens emitidos (rollback completo)

# CA-04: first_login → next_step='change_password' (FA-01)
def test_login_first_login_redirects_to_change_password():
    # User.first_login=True → 200 pero next_step='change_password'
    # Session scope reducido (solo UC_AUTH_04 + UC_AUTH_02)

# CA-06: User sin Assignments → warning no_permissions
def test_login_warns_when_no_permissions():
    # User ACTIVE sin Assignments ACTIVE
    # ENTONCES warning.type='no_permissions', AuditEvent LOGIN_NO_PERMISSIONS

# CA-07: username inexistente → 401
def test_login_unknown_username_returns_401():
    # No exponer si user existe o no (timing attack mitigation)

# CA-08: password incorrecto → 401
def test_login_wrong_password_returns_401():

# CA-09: throttling
def test_login_throttled_after_N_attempts():
    # CA: CNST-011 throttle → 429 después del límite

# CA-10: User INACTIVE → 401
def test_login_inactive_user_returns_401():
    # User.state = 'INACTIVE' → 401 USER_INACTIVE

# CA-11: User BLOCKED → 401 + AuditEvent BLOCKED_LOGIN_ATTEMPT
def test_login_blocked_user_returns_401():

# CA-12: No HTTPS → rechazado (CNST)
# CA-13: Payload inválido → 400 VALIDATION_ERROR
def test_login_invalid_payload_returns_400():
```

**Tests existentes que deben CORREGIRSE:**
- Los tests actuales en `test_views.py` no verifican CA-02, CA-03, CA-04, CA-06.

### FASE 1.2 — UC_PERM_07: Verificar Permiso (T-02 completo)

**Fuente:** `casos-uso/permissions/uc-perm-07/` (12 partes)
**Función RBAC:** ACC-003 `view_assignments` (admin endpoint)
**Clases de dominio:** `Assignment`, `ExceptionalPermission`

**Importancia crítica:** Es la dependencia T-02 usada implícitamente por 59/61 UCs.
La implementación en `HasFunction` actual es básica — no implementa la precedencia
completa ni el cache con TTL ajustado.

**Tests a escribir** (`tests/unit/access/test_uc_perm_07.py`):

```python
# CA-01: AGR otorga permiso
def test_check_returns_allowed_when_user_in_agr_with_function():
    # User en AGR con función F → allowed=True, origin=GRANTED_BY_AGR

# CA-02: Revocación excepcional gana sobre AGR
def test_revocation_takes_precedence_over_agr():
    # User en AGR + revocación excepcional ACTIVE → allowed=False
    # origin=REVOKED_EXCEPTIONAL

# CA-03: Concesión excepcional sin AGR
def test_exceptional_grant_allows_without_agr():
    # User sin AGR + concesión ACTIVE → allowed=True, origin=GRANTED_EXCEPTIONAL

# CA-04: Sin nada → DENIED_NO_GRANT
def test_no_grant_returns_denied():
    # User sin ninguna asignación → allowed=False, origin=DENIED_NO_GRANT

# CA-05: AGR INACTIVE no cuenta
def test_inactive_agr_does_not_grant():
    # AGR.state=INACTIVE → allowed=False aunque la función esté en él

# CA-06: Assignment expirado no cuenta
def test_expired_assignment_does_not_grant():
    # Assignment.valid_until < now → allowed=False

# CA-07: Concesión excepcional expirada no cuenta
def test_expired_exceptional_grant_does_not_grant():

# CA-08: Multi-AGR → lista de via_agr_codes
def test_multi_agr_returns_all_granting_agrs():
    # F otorgada por AGR-A, AGR-B, AGR-C → via_agr_codes=[A,B,C]

# CA-09: Cache hit
def test_second_check_returns_from_cache():
    # Mismo (user, F) dentro de TTL → cache=True en response

# CA-10: Cache invalidado por evento
def test_cache_invalidated_after_assignment_change():
    # assign/revoke → siguiente check es miss (cache invalidado)

# CA-11: Bulk check (50 funciones, 1 query para misses)
def test_bulk_check_uses_single_query():
    # POST /api/access/permissions/check-bulk/ con 50 codes
    # results.length=50, 1 query a BD para los misses

# CA-12: Función no existe → 400
def test_unknown_function_code_returns_400():

# CA-14: Sin permiso admin → 403
def test_admin_endpoint_requires_view_assignments():

# CA-15: Fail-closed en BD timeout → 503
def test_bd_timeout_returns_503_and_denies():

# CA-16: Sin AuditEvent por invocación normal
def test_check_permission_emits_no_audit_event():

# CA-17: TTL ajustado por valid_until de la concesión
def test_cache_ttl_adjusted_to_valid_until():
```

**Implementación requerida:**
- `PermissionService` en `apps/access/services/permission_service.py`
  - `check(user_id, function_code, bypass_cache=False)` → `CheckPermissionOutput`
  - `check_bulk(user_id, function_codes)` → `BulkCheckOutput`
  - `PrecedenceEvaluator.evaluate(revoke, grant, agr_codes)`
  - Cache con `django.core.cache` (DatabaseCache, no Redis per CNST)
  - TTL ajustado por `valid_until` de la concesión
- `PermissionVerifyView` (GET, admin)
- `PermissionBulkCheckView` (POST)
- Actualizar `HasFunction` para usar `PermissionService.check()`

### FASE 1.3 — UC_USR_02: Consultar Usuarios (CRÍTICO)

**Fuente:** `casos-uso/users/uc-usr-02/`
**Función RBAC:** USR-005 `search_users`, USR-009 `view_users`

**Tests a corregir/agregar** (`tests/unit/users/test_uc_usr_02.py`):
```python
# CA-01: Listado paginado (50 por defecto)
def test_list_users_paginated_50_per_page():

# CA-02: Restricción PII en listado (CNST-026)
def test_list_users_masks_email_in_response():
    # email NO aparece completo en listado — mascarado o ausente

# CA-03: Filtros — por estado, módulo, search
def test_list_users_filtered_by_state():

# CA-04: Sin permiso USR-004/005/009 → 403
def test_list_users_requires_list_users_or_search_users():
```

### FASE 1.4 — UC_ACC_03: Consultar Permisos (CRÍTICO)

**Fuente:** `casos-uso/access/uc-acc-03/`
**Función RBAC:** ACC-003 `view_assignments`

**Tests a corregir/agregar** (`tests/unit/access/test_uc_acc_03.py`):
```python
# CA-01: Vista consolidada — total, via_direct, via_agr, via_exceptional
def test_view_assignments_returns_consolidated_view():
    # effective_total_count, via_direct_count, via_agr_count, via_exceptional_count

# CA-02: Deduplicación — función en directo Y vía AGR → aparece UNA vez con ambos sources
def test_view_assignments_deduplicates_functions():

# CA-03: User sin permisos → 200 con listas vacías (no 404)
def test_view_assignments_returns_empty_for_user_without_permissions():
```

### FASE 1.5 — UC_PIP_01: Supervisar ETL (CRÍTICO)

**Fuente:** `casos-uso/pipeline/uc-pip-01/`
**Función RBAC:** PIP-001 `view_pipeline_status`

**Tests a corregir/agregar** (`tests/unit/pipeline/test_uc_pip_01.py`):
```python
# CA-01: Summary correcto (exists, partial coverage)
def test_etl_status_returns_summary():

# CA-02: Pipeline stale detectado
def test_etl_status_detects_stale_pipeline():
    # Última exitosa > 14h → status='degradado'
    # Última exitosa > 24h → status='critico'

# CA-04: Cache hit (TTL 30s)
def test_etl_status_returns_from_cache_on_second_call():

# CA-05: Sin permiso PIP-001 → 403
def test_etl_status_requires_view_pipeline_status():

# CA-06: BD timeout → 503
def test_etl_status_503_on_db_timeout():
```

**Nota sobre function code**: el endpoint actual usa `'pipeline.view_status'` como `required_function`. Debe actualizarse a `'view_pipeline_status'` (nombre canónico PIP-001 en v5.4.0).

### FASE 1.6 — UC_AUD_01: Consultar Auditoría (CRÍTICO)

**Fuente:** `casos-uso/audit/uc-aud-01/`
**Función RBAC:** AUD-001 `view_audit_log`

**Tests a corregir/agregar** (`tests/unit/audit/test_uc_aud_01.py`):
```python
# CA-01: Lista timeline básica (existen tests, verificar CAs completos)
def test_audit_list_returns_timeline():

# CA-02: Filtro por módulo
def test_audit_list_filtered_by_module():

# CA: Sin permiso AUD-001 → 403
def test_audit_list_requires_view_audit_log():
    # function='view_audit_log' (AUD-001), no 'audit.view_log' (nombre antiguo)
```

### FASE 1.7 — UC_AUTH_04: Cambiar Contraseña (CRÍTICO)

**Fuente:** `casos-uso/auth/uc-auth-04/`
**Función RBAC:** usuario sobre sí mismo

**Tests a corregir/agregar** (`tests/unit/authentication/test_uc_auth_04.py`):
```python
# CA-01: Cambio exitoso
def test_change_password_happy_path():
    # User.password_hash cambia, User.first_login=False
    # 1 entrada en PasswordHistory, 1 AuditEvent PASSWORD_CHANGED
    # Body NO contiene nueva contraseña

# CA-02: Password actual incorrecto → 400
def test_change_password_wrong_current_password():

# CA-03: Nueva contraseña no cumple política → 400
def test_change_password_weak_new_password():

# CA-04: Usuario con first_login=True → después del cambio exitoso, Session pasa a ACTIVE pleno
def test_change_password_clears_first_login_flag():
```

### FASE 1.8 — UC_RPT_01: Ver Dashboard (CRÍTICO)

**Fuente:** `casos-uso/reports/uc-rpt-01/`
**Función RBAC:** RPT-001 `view_reports`
**Clases de dominio:** `Report (scope=GENERAL)`

**Tests a escribir** (`tests/unit/reports/test_uc_rpt_01.py`):
```python
# CA-01: Dashboard básico con datos
def test_dashboard_returns_kpis_with_data():
    # GET /api/reports/dashboard/
    # ENTONCES 200 con KPIs poblados del IVR

# CA-02: Sin datos → 200 con KPIs en 0, mensaje "Sin datos para el quarter actual"
def test_dashboard_returns_zeros_without_data():

# CA-05: Sin segmento → 400 USER_WITHOUT_SEGMENT
def test_dashboard_400_when_user_without_segment():

# CA-07: Period 'last_7d' en respuesta
def test_dashboard_accepts_period_param():

# CA: Sin permiso RPT-001 → 403
def test_dashboard_requires_view_reports():

# CA: BD timeout → 503
def test_dashboard_503_on_mariadb_timeout():
```

---

## FASE 2 — UCs ALTOS de AUTH, USR, ACC, PERM

**Orden** (respeta dependencias):

```
UC_AUTH_02 Cerrar Sesión         1d  → requiere UC_AUTH_01
UC_AUTH_03 Recuperar Contraseña  3d  → requiere UC_USR_03 (cross USR)
UC_AUTH_05 Gestionar Sesiones    3d  → requiere UC_AUTH_01, UC_AUTH_02
UC_USR_01  Crear Usuario         4d  → requiere UC_ACC_01, UC_ACC_04
UC_USR_03  Modificar Usuario     3d  → requiere UC_USR_02, UC_AUTH_05
UC_USR_04  Eliminar Usuario      2d  → requiere UC_USR_02, UC_AUTH_05
UC_ACC_01  Asignar Funciones     4d  → requiere UC_ACC_05
UC_ACC_02  Revocar Funciones     2d  → requiere UC_ACC_01
UC_ACC_04  Asignar Agrupador     2d  → requiere UC_USR_02, UC_ACC_03
UC_ACC_05  Gestionar SoD         5d  → raíz
UC_PERM_05 Crear Grupo Permisos  2d  → raíz
UC_PERM_06 Asignar Fns a Grupo   3d  → requiere UC_PERM_05, UC_ACC_05
UC_PERM_01 Asignar Grupo         2d  → requiere UC_PERM_05
UC_PERM_02 Revocar Grupo         2d  → requiere UC_PERM_01
UC_PERM_08 Generar Menú Dinámico 3d  → requiere UC_PERM_07
```

**CAs clave de FASE 2 por UC:**

**UC_AUTH_02** (Cerrar Sesión):
- CA-01: `Session.state='CLOSED'`, `close_reason='USER_LOGOUT'`, 2 `BlacklistedToken`, 1 `AuditEvent LOGOUT`

**UC_USR_01** (Crear Usuario):
- CA-01: `User.username='ana.gomez.0001'`, `first_login=True`, 1 `Assignment` AGR-006, 1 `InternalMessage` en buzón, 1 `AuditEvent USER_CREATED`
- CA: Body NO contiene contraseña (CNST-026)

**UC_ACC_01** (Asignar Funciones):
- CA-01: 3 `Assignment` ACTIVE, AuditEvent `FUNCTIONS_ASSIGNED`, cache invalidado
- CA-02: Asignación temporal con `expires_at`
- CA: Throttle 30 POST/min/invoker

**UC_ACC_02** (Revocar Funciones):
- CA-01: `Assignment.state='REVOKED'`, `revoked_at`, AuditEvent `FUNCTIONS_REVOKED`, cache invalidado
- CA-02: Soft-delete (BR-009) — Assignment NO eliminado físicamente
- Anti-self-revoke (P-11): invoker no puede revocar sus propias funciones

**UC_ACC_05** (Gestionar SoD):
- CA-01: Listado paginado de SeparationRules
- CA-03: Crear regla → SoDRule ACTIVE, AuditEvent `SOD_RULE_CREATED`
- Nuevas funciones v5.4.0: `update_separation_rule` (ACC-011), `disable_separation_rule` (ACC-012)

**UC_PERM_08** (Generar Menú Dinámico):
- CA-01: User con funciones en múltiples dominios → menú con N domains
- CA-02: User sin funciones → `domains: []` (no error)
- CA-03: Function REVOKED no aparece en menú

---

## FASE 3 — UCs ALTOS de RPT, ALR, PIP

```
UC_RPT_02 Ver Métricas Tiempo Real   4d
UC_RPT_03 Ver Reportes Históricos    4d  → requiere UC_RPT_01
UC_RPT_04 Exportar Reporte (Larman)  6d  → requiere UC_RPT_01
UC_ALR_01 Configurar Umbrales        3d  → raíz
UC_ALR_02 Ver Alertas Activas        2d  → requiere UC_ALR_01
UC_ALR_03 Reconocer Alerta           2d  → requiere UC_ALR_02
UC_PIP_02 Consultar Errores ETL      2d  → requiere UC_PIP_01
UC_PIP_03 Consultar Disponibilidad   2d  → requiere UC_PIP_01
UC_PIP_04 Solicitar Reintento        3d  → requiere UC_PIP_01, UC_PIP_02
UC_LOG_01 Consultar Logs Sistema     2d  → raíz
UC_LOG_02 Consultar Logs ETL         2d  → requiere UC_PIP_01
```

**CAs clave:**

**UC_RPT_02** (Métricas Tiempo Real):
- CNST-003 prohíbe SSE/WebSockets — la respuesta debe explicar esto claramente
- El endpoint existe como stub; debe devolver respuesta documentada que explique la restricción

**UC_RPT_04** (Exportar Reporte — patrón Larman):
- CA-01: POST /api/reports/export/ → 202 con job_id
- CA-02: Worker procesa → `ExportJob.state='DONE'`, URL firmada
- Formatos: CSV (RPT-004), Excel (RPT-005), PDF (RPT-006) — 3 funciones RBAC separadas para SoD

**UC_PIP_02** (Errores ETL):
- CA-05: PII scrubbing en stack traces — reemplazar teléfonos/emails

**UC_PIP_04** (Solicitar Reintento):
- `reason` ≥ 20 caracteres (validación documentada)
- No encolar si pipeline RUNNING
- Último run debe ser FAILED
- AuditEvent `ETL_RETRY` con actor + reason + run_id

**UC_LOG_01/02**:
- Actualizar `required_function` a `view_application_logs` (LOG-001) y `view_etl_logs` (LOG-004)

---

## FASE 4 — UCs MEDIOS

```
UC_ACC_08 Permiso Temporal Excepcional   3d
UC_RPT_07 Programar Reporte             3d  → requiere UC_RPT_01, UC_RPT_04
UC_RPT_08 Ver Reportes Programados      2d  → requiere UC_RPT_07
UC_RPT_11 Compartir Reporte             3d  → requiere UC_RPT_01 + InternalMailbox
UC_RPT_12..14 Reportes variantes        2d c/u
UC_RPT_15..17 Reportes IVR SPs         2d c/u  (TIENEN código, verificar CAs)
UC_ALR_04 Ver Historial Alertas         2d
UC_ALR_05 Gestionar Suscripciones       4d
UC_AUD_04 Reporte Compliance            5d
UC_LOG_04 Exportar Logs                 3d
UC_LOG_05 Ver Logs Infraestructura      2d
UC_PERM_03 Conceder Permiso Excepcional 3d
UC_PERM_04 Revocar Permiso Excepcional  1d
AUTH_03 Recuperar Contraseña            3d
```

---

## FASE 5 — UCs BAJOS

```
UC_ACC_09 Auditar Cambios de Acceso     2d
UC_RPT_09 Configurar Filtros            2d
UC_RPT_10 Guardar Vista                 2d
UC_PERM_09 Auditar Acceso              1d
UC_PERM_10 Consultar Auditoría Permisos 2d
UC_LOG_06 Ver Estado Sistema            2d
UC_LOG_07 Ver Métricas Técnicas         3d
UC_LOG_03 Buscar Logs                   3d
UC_AUD_02 Buscar Auditoría              3d
UC_AUD_03 Exportar Auditoría            3d
```

---

## Tabla resumen del plan

| FASE | Scope | UCs | Días estimados | Prioridad |
|---|---|---|---|---|
| FASE 0 | Infraestructura transversal | — | 6 | Pre-requisito |
| FASE 1 | 8 UCs CRÍTICOS | 8 | 29 | Crítica |
| FASE 2 | UCs ALTOS AUTH/USR/ACC/PERM | 15 | 39 | Alta |
| FASE 3 | UCs ALTOS RPT/ALR/PIP/LOG | 11 | 27 | Alta |
| FASE 4 | UCs MEDIOS | 17 | 38 | Media |
| FASE 5 | UCs BAJOS | 10 | 21 | Baja |
| **Total** | **61 UCs** | **61** | **160 días** | |

---

## Criterio de DONE por FASE

1. Todos los CAs documentados en IACT-docs tienen test que los verifica (Red → Green)
2. La función RBAC usada en `required_function` coincide con el nombre canónico v5.4.0
3. AuditEvent emitido en todas las operaciones de escritura (T-03)
4. InternalMailbox usada en lugar de email externo (CNST-001)
5. Soft-delete (BR-009) en todos los modelos con ciclo de vida
6. Sin PII en payloads de AuditEvent (CNST-026)
7. Sintaxis válida, `@extend_schema` completo, hallazgos documentados

---

## Tests existentes que DEBEN corregirse (identificados en auditoría)

| Archivo | CA incumplido | FASE correctora |
|---|---|---|
| `test_views.py` (authentication) | CA-02 sesión única, CA-03 atomicidad, CA-04 first_login | FASE 1.1 |
| `test_permissions.py` (access) | No verifica precedencia completa de UC_PERM_07 | FASE 1.2 |
| `test_views.py` (pipeline) | No verifica cache TTL ni stale detection | FASE 1.5 |
| `test_api.py` (audit) | No verifica inmutabilidad append-only | FASE 0-T4 |
| `test_report_model.py` | No verifica ExportJob con formatos separados | FASE 3 |
| `test_services.py` (authentication) | No verifica AuditEvent LOGIN_NO_PERMISSIONS | FASE 1.1 |
| Todos los views con `required_function` | Usan nombres pre-v5.4.0 | FASE 0-T2 |
