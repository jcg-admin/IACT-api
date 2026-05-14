# [DEPRECADO] Plan de Implementación TDD — IACT-api v3.0.0

> **ESTADO: DEPRECADO** — 2026-05-13
>
> Reemplazado por `PLAN-IMPLEMENTACION-TDD-v4-20260513.md`.
>
> Razón: el ciclo de remediación STD-008 §3.3/§3.5 (5 fases, commits
> `c9cfae7`, `4f19034` en IACT-api; `885290f` en IACT-ui; IACT-docs pendiente)
> produjo cambios estructurales en nomenclatura, routing y documentación
> normativa que este plan no contempla:
> - `sod-rules/` → `separation-rules/` (routing canónico)
> - `sod_rule_view.py` → `separation_rule_view.py` (archivo renombrado)
> - `SoDRule*` → `SeparationRule*` (clases, serializers, event types)
> - `validate-sod` → `separation-rules/validate` (endpoint canónico)
> - `SeparationRuleViewSet` eliminado del router (drf-spectacular)
> - 4 codenames en catalog.js (IACT-ui)
> - CNST-030 v3.0.0, CNST-033 v2.0.0 (normativa)
>
> Las FASES 0, 1, 2 del plan TDD están implementadas pero la rama
> `refactor/std008-sod-naming` (IACT-api) y `claude/project-analysis-N9IkV`
> (IACT-ui) deben mergearse a `develop` antes de continuar con FASE 3.
>
> Ver: `PLAN-IMPLEMENTACION-TDD-v4-20260513.md`

## Fuente única: IACT-docs `source/requisitos/` y `source/arquitectura-tecnica/`

**Versión:** 3.0.0
**Fecha:** 2026-05-13
**Metodología:** Red → Green → Refactor por CA, con tests derivados de `Parte 12 — Testing` de cada UC
**Principio:** Los documentos de IACT-docs son la fuente de verdad. Los nombres de
componentes, funciones, contratos y tests en este plan provienen literalmente de los
artefactos canónicos — no de inferencias sobre el código existente.

---

## Por qué existe FASE 0

La `matriz-dependencias-uc-iact.rst` identifica tres dependencias transversales:

- **T-01** (Session activa): prerequisito de 59/61 UCs
- **T-02** (UC_PERM_07 — Verificar Permiso): prerequisito de 59/61 UCs
- **T-03** (AuditEvent — CNST-025): prerequisito de 35/61 UCs

El `ADR-BACK-006` (Vigente, 2026-04-29) define además que la verificación de permiso
**siempre debe pasar por una función SQL canónica** (`user_has_function()`), nunca
por lógica ORM propia. Esta función, junto a otras cuatro funciones PostgreSQL, es
infraestructura que debe existir antes de implementar cualquier UC.

**FASE 0 no implementa UCs. Implementa la infraestructura que hace posible que los
61 UCs tengan una base de autorización, auditoría y comunicación correcta.**

T-02 es parcialmente FASE 0 (las funciones SQL) y parcialmente FASE 1 (UC_PERM_07
como servicio Python con cache y endpoint).

---

## FASE 0 — Infraestructura transversal
**Fuente:** `ADR-BACK-006`, `modelo-rbac-iact.rst` v5.4.0, `modelo-dominio-iact.rst`,
BR-004, BR-009, BR-010, CNST-001, CNST-010, CNST-025, CNST-026, CNST-032, CNST-033

### F0-T1 — Schema canónico y modelos Django alineados con v5.4.0

**Qué dice ADR-BACK-006 § 2.3:** Los nombres de modelo en código deben seguir la
nomenclatura inglesa del corpus. Los modelos legacy con nombre en español deben
renombrarse:

| Nombre legacy | Nombre canónico | Fuente |
|---|---|---|
| `PermisoExcepcional` | `ExceptionalGrant` | ADR-BACK-006 § 2.3 |
| `AuditoriaPermiso` | `FunctionAccessAudit` | ADR-BACK-006 § 2.3 |
| `ReglaSoD` | `SeparationRule` | ADR-BACK-006 § 2.3 |
| `UserPermission` (code antiguo) | `UserFunctionAssignment` | modelo-dominio |

**Tests primero** (`tests/unit/access/test_schema_canonical.py`):

```python
def test_assignment_model_has_state_field_with_correct_choices():
    # BR-009: baja lógica — Assignment.state ∈ {ACTIVE, EXPIRED, REVOKED}
    choices = [c[0] for c in Assignment._meta.get_field('state').choices]
    assert set(choices) == {'ACTIVE', 'EXPIRED', 'REVOKED'}

def test_exceptional_permission_has_valid_until_field():
    # CNST-031: ExceptionalPermission.valid_until nullable
    field = ExceptionalPermission._meta.get_field('valid_until')
    assert field.null is True

def test_separation_rule_state_supports_enabled_disabled():
    # BR-009 + ADR-BACK-006 § 2.3: SeparationRule.state ∈ {ENABLED, DISABLED}
    choices = [c[0] for c in SeparationRule._meta.get_field('state').choices]
    assert 'ENABLED' in choices and 'DISABLED' in choices

def test_user_has_internal_mailbox_after_creation():
    # modelo-dominio-iact § 4.1: User 1:1 InternalMailbox (CNST-001)
    from django.test import TestCase
    user = UserFactory()
    assert InternalMailbox.objects.filter(owner=user).exists()
```

### F0-T2 — Catálogo RBAC v5.4.0: 61 funciones + 10 AGRs + 3 SoD

**Qué dice `modelo-rbac-iact.rst` v5.4.0:** 61 funciones en 8 módulos, con nombres
en inglés (CNST-033). El catálogo actual en `create_functions.py` usa strings como
`'USR_VIEW'`, `'RPT_VIEW'` que no existen en v5.4.0.

**Tests primero** (`tests/unit/access/test_rbac_catalog_v540.py`):

```python
CATALOG_V540 = [
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
def test_function_catalog_has_exactly_61_functions():
    assert Function.objects.count() == 61

@pytest.mark.django_db
@pytest.mark.parametrize("func_id, func_name", CATALOG_V540)
def test_canonical_function_exists(func_id, func_name):
    assert Function.objects.filter(
        code=func_id, name=func_name
    ).exists(), f"Falta en catálogo: {func_id} — {func_name}"

@pytest.mark.django_db
def test_10_access_groups_predefined():
    # modelo-rbac-iact AGR-001..010
    assert AccessGroup.objects.filter(
        code__in=['AGR-001','AGR-002','AGR-003','AGR-004','AGR-005',
                  'AGR-006','AGR-007','AGR-008','AGR-009','AGR-010']
    ).count() == 10

@pytest.mark.django_db
def test_agr_001_basic_operator_has_6_functions():
    # modelo-rbac-iact: AGR-001 basic_operator_group tiene 6 funciones exactas
    agr = AccessGroup.objects.get(code='AGR-001')
    assert agr.functions.count() == 6
    fn_names = set(agr.functions.values_list('name', flat=True))
    assert fn_names == {
        'view_own_sessions', 'view_all_active_sessions',
        'view_reports', 'view_dashboard', 'view_kpis', 'view_charts'
    }

@pytest.mark.django_db
def test_3_sod_rules_enabled():
    # modelo-rbac-iact: SOD-001, SOD-002, SOD-003
    assert SeparationRule.objects.filter(state='ENABLED').count() == 3

@pytest.mark.django_db
def test_sod_001_pipeline_audit_separation():
    # SOD-001: Pipeline NO puede combinarse con Auditoría
    rule = SeparationRule.objects.get(code='SOD-001')
    fn_codes = set(rule.functions.values_list('code', flat=True))
    pip_codes = {'PIP-001', 'PIP-002', 'PIP-003', 'PIP-004'}
    aud_codes = {'AUD-001', 'AUD-002', 'AUD-003', 'AUD-004'}
    assert pip_codes.issubset(fn_codes) or aud_codes.issubset(fn_codes)
```

**Implementación:**
- Reescribir `apps/access/management/commands/create_functions.py` con 61 funciones v5.4.0
- Crear `apps/access/management/commands/create_access_groups.py` con 10 AGRs y sus funciones
- Crear `apps/access/management/commands/create_sod_rules.py` con 3 reglas
- Actualizar todos los `required_function` en views al nombre canónico v5.4.0

### F0-T3 — Cinco funciones SQL en PostgreSQL (ADR-BACK-006 § 2.3)

**Qué dice ADR-BACK-006:** La verificación final de "usuario X tiene Función Y" SIEMPRE
pasa por la función SQL canónica. El ORM Django NO implementa lógica propia de evaluación.

Las 5 funciones SQL canónicas (PL/pgSQL en PostgreSQL):

```sql
-- 1. Verificación booleana O(log n)
user_has_function(p_user_id INTEGER, p_function_code VARCHAR) RETURNS BOOLEAN

-- 2. Array de funciones efectivas del usuario
get_user_functions(p_user_id INTEGER) RETURNS VARCHAR[]

-- 3. JSONB de grupos del usuario
get_user_groups(p_user_id INTEGER) RETURNS JSONB

-- 4. Atómico: check + write audit (CNST-025)
check_function_and_audit(p_user_id INTEGER, p_function_code VARCHAR) RETURNS BOOLEAN

-- 5. Genera menú dinámico (CNST-032 — obligatoria)
get_user_menu(p_user_id INTEGER) RETURNS JSONB
```

**Tests primero** (`tests/unit/access/test_sql_functions.py`):

```python
@pytest.mark.django_db
def test_user_has_function_returns_true_for_assigned():
    # user_has_function(): Usuario en AGR con fn → True
    user = UserFactory(in_agr='AGR-001')
    result = db_call('user_has_function', user.pk, 'view_reports')
    assert result is True

@pytest.mark.django_db
def test_user_has_function_returns_false_for_unassigned():
    user = UserFactory()
    result = db_call('user_has_function', user.pk, 'export_csv')
    assert result is False

@pytest.mark.django_db
def test_get_user_menu_returns_jsonb_structure():
    # CNST-032: get_user_menu obligatoria — retorna JSONB con modules
    user = UserFactory(in_agr='AGR-001')
    menu = db_call('get_user_menu', user.pk)
    assert isinstance(menu, dict)
    assert 'modules' in menu

@pytest.mark.django_db
def test_check_function_and_audit_writes_audit_atomically():
    # check_function_and_audit: check + AuditEvent en misma transacción
    user = UserFactory(in_agr='AGR-001')
    before = AuditLog.objects.count()
    result = db_call('check_function_and_audit', user.pk, 'view_reports')
    assert result is True
    assert AuditLog.objects.count() == before + 1
```

**Implementación:**
- Crear migración Django con `RunSQL` que define las 5 funciones PL/pgSQL
- Crear helper Python `apps/access/db_functions.py` que llama a estas funciones

### F0-T4 — InternalMailbox model y servicio (CNST-001, BC Auth)

**Qué dice `modelo-dominio-iact.rst` § 4.1:** `InternalMailbox` es una de las tres
clases del bounded context Auth. Todo User posee exactamente un InternalMailbox.
CNST-001 prohíbe email externo, SMS o webhooks; toda comunicación pasa por este buzón.

**Tests primero** (`tests/unit/alerts/test_internal_mailbox.py`):

```python
@pytest.mark.django_db
def test_user_has_mailbox_after_creation():
    # modelo-dominio § 4.1: User 1:1 InternalMailbox
    user = UserFactory()
    assert InternalMailbox.objects.filter(owner=user).count() == 1

@pytest.mark.django_db
def test_deliver_message_creates_internal_message():
    # CNST-001: entrega sin email externo
    user = UserFactory()
    mailbox = InternalMailbox.objects.get(owner=user)
    msg = mailbox.deliver_message(
        subject='Contraseña temporal',
        body='Tu contraseña es: TempX1!@'
    )
    assert InternalMessage.objects.filter(mailbox=mailbox).count() == 1
    assert msg.subject == 'Contraseña temporal'

def test_mailbox_service_never_calls_send_mail(mock_send_mail):
    # CNST-001: prohibición absoluta de email externo
    # BR-004: todas las notificaciones vía buzón interno
    mailbox = InternalMailbox()
    mailbox.deliver_message(subject='Test', body='Test body')
    mock_send_mail.assert_not_called()

@pytest.mark.django_db
def test_internal_message_is_preserved_on_soft_delete():
    # BR-009: baja lógica — mensajes no se eliminan físicamente
    user = UserFactory()
    mailbox = InternalMailbox.objects.get(owner=user)
    msg = mailbox.deliver_message(subject='Test', body='body')
    msg.delete()  # baja lógica
    assert InternalMessage.objects.filter(pk=msg.pk).exists()
    assert InternalMessage.objects.get(pk=msg.pk).state == 'DELETED'
```

### F0-T5 — AuditEvent service universal (BR-008, BR-010, CNST-025, CNST-026)

**Qué dice `modelo-dominio-iact.rst` § 4.7:** AuditEvent es append-only, inmutable.
BR-010: sin UPDATE ni DELETE sobre la tabla de auditoría. CNST-026: sin PII en payload.

**Tests primero** (`tests/unit/audit/test_audit_service_universal.py`):

```python
@pytest.mark.django_db
def test_audit_event_cannot_be_updated():
    # BR-010: tabla append-only
    event = AuditLogFactory(event_type='LOGIN')
    with pytest.raises(Exception):
        AuditLog.objects.filter(pk=event.pk).update(event_type='LOGOUT')

@pytest.mark.django_db
def test_audit_event_cannot_be_deleted():
    # BR-010: ningún rol tiene permiso DELETE sobre auditoría
    event = AuditLogFactory(event_type='LOGIN')
    with pytest.raises(Exception):
        event.delete()

@pytest.mark.django_db
def test_audit_service_emit_returns_persisted_event():
    # uc-perm-09 CA-01: emit básico → AuditEvent persistido + id
    service = AuditLogService()
    event = service.emit(
        event_type='LOGIN',
        actor_user_id=1,
        payload={'username': 'alice'}
    )
    assert event.pk is not None
    assert AuditLog.objects.filter(pk=event.pk).exists()

def test_audit_service_strips_password_from_payload():
    # CNST-026: payload sin PII — password, tokens excluidos
    service = AuditLogService()
    event = service.emit(
        event_type='LOGIN',
        actor_user_id=1,
        payload={'username': 'alice', 'password': 'Secret1!'}
    )
    saved_payload = AuditLog.objects.get(pk=event.pk).payload
    assert 'password' not in str(saved_payload)

def test_audit_service_raises_on_unknown_event_type():
    # uc-perm-09 CA-03: event_type desconocido → AuditValidationError
    service = AuditLogService()
    with pytest.raises(AuditValidationError):
        service.emit(event_type='TIPO_INEXISTENTE', actor_user_id=1)
```

### F0-T6 — DB router e infraestructura de base de datos

**Qué dice `databases/modelo-dual.rst`:** IACT opera sobre dos BDs: MySQL/MariaDB
(IVR, solo lectura, BR-001) y PostgreSQL (Analytics, lectura+escritura). El router
Django debe devolver `False` (no `None`) para `allow_migrate` en la BD IVR.

**Tests primero** (`tests/unit/config/test_db_router.py`):

```python
def test_ivr_router_allow_migrate_returns_false():
    # BR-001: IVR readonly — Django nunca migra en ivr_legacy
    from config.db_router import IVRRouter
    router = IVRRouter()
    assert router.allow_migrate('ivr', 'any_app') is False  # False, no None

def test_ivr_router_db_for_write_raises():
    # BR-001: escritura prohibida en IVR
    from config.db_router import IVRRouter
    router = IVRRouter()
    with pytest.raises(Exception):
        router.db_for_write(MockModel(app_label='ivr'))

def test_test_database_ivr_name_is_none():
    # Sin TEST NAME → Django no crea test_ivr_legacy
    from django.conf import settings
    assert settings.DATABASES['ivr'].get('TEST', {}).get('NAME') is None
```

---

## FASE 1 — Los 8 UCs CRÍTICOS
**Fuente:** `arquitectura-tecnica/matriz-dependencias-uc-iact.rst` § 1.2.1 y § 3.1
**Orden respeta el grafo de dependencias del corpus**

```
UC_AUTH_01 Iniciar Sesión          5 días  → raíz
UC_PERM_07 Verificar Permiso       4 días  → raíz (T-02 completo como servicio)
UC_USR_02  Consultar Usuarios      3 días  → raíz
UC_ACC_03  Consultar Permisos      3 días  → raíz
UC_PIP_01  Supervisar ETL          4 días  → raíz
UC_AUD_01  Consultar Auditoría     3 días  → raíz
UC_AUTH_04 Cambiar Contraseña      2 días  → requiere UC_AUTH_01
UC_RPT_01  Ver Dashboard           5 días  → requiere datos de UC_PIP_01
                                  ─────
                                  29 días estimados
```

### FASE 1.1 — UC_AUTH_01: Iniciar Sesión

**Fuente:** `casos-uso/auth/uc-auth-01/` (12 partes), `requisitos-funcionales/auth/uc-001-*/`

Los 16 tests están documentados en `Parte 12 — Testing`. Se transcriben con firma exacta:

```python
# tests/unit/authentication/test_uc_auth_01.py
# Fuente: uc-auth-01/testing.rst § 12.2

class TestLoginHappyPath:
    def test_login_happy_path(self):
        """CA-01: User ACTIVE sin Sessions previas. Fuente: CA-01 + testing.rst §12.2.1"""
        user = make_active_user(username='alice', password='S3cret!XY')
        response = client.post('/api/auth/login/', {
            'username': 'alice', 'password': 'S3cret!XY'
        }, format='json')
        assert response.status_code == 200
        assert response.data['tokens']['access']
        assert response.data['user']['user_id'] == str(user.user_id)
        assert response.data['next_step'] is None
        assert response.data['warning'] is None
        assert Session.objects.filter(user=user, state='ACTIVE').count() == 1
        # Session.expires_at = started_at + 15 min (CNST-002)
        session = Session.objects.get(user=user, state='ACTIVE')
        delta = session.expires_at - session.started_at
        assert abs(delta.total_seconds() - 900) < 5  # 15 min ± 5s
        # BR-008, CNST-025: AuditEvent LOGIN
        assert AuditLog.objects.filter(
            event_type='LOGIN', actor_user_id=user.pk
        ).exists()
        # CNST-026: sin password ni tokens en payload de audit
        audit = AuditLog.objects.get(event_type='LOGIN', actor_user_id=user.pk)
        assert 'password' not in str(audit.payload)
        assert 'access' not in str(audit.payload)
        # User.last_login_at actualizado (flujo paso 14)
        user.refresh_from_db()
        assert user.last_login_at is not None

    def test_login_supersedes_previous_session(self):
        """CA-02: BR-005 sesión única. Fuente: CA-02 + testing.rst §12.2.1"""
        user = make_active_user(username='bob', password='S3cret!XY')
        prev = Session.objects.create(
            user=user, state='ACTIVE',
            expires_at=now() + timedelta(minutes=15),
            client_info={'device': 'old-device'}
        )
        response = client.post('/api/auth/login/', {
            'username': 'bob', 'password': 'S3cret!XY',
            'client_info': {'device': 'new-device'},
        }, format='json')
        assert response.status_code == 200
        prev.refresh_from_db()
        assert prev.state == 'CLOSED'
        assert prev.close_reason == 'SUPERSEDED'
        assert AuditLog.objects.filter(event_type='SESSION_CLOSED').exists()

    def test_login_rollback_on_db_failure(self):
        """CA-03: atomicidad transacción pasos 10-14. Fuente: testing.rst §12.2.1"""
        user = make_active_user(username='carol', password='S3cret!XY')
        with mock.patch('apps.audit.models.AuditLog.objects.create',
                        side_effect=DatabaseError):
            response = client.post('/api/auth/login/', {
                'username': 'carol', 'password': 'S3cret!XY'
            }, format='json')
        assert response.status_code == 503
        assert response.data['error']['code'] == 'DB_TRANSIENT_ERROR'
        assert Session.objects.filter(user=user).count() == 0  # rollback

    def test_login_first_login_redirects_to_change_password(self):
        """CA-04: FA-01 primer login. Fuente: CA-04 + testing.rst §12.2.2"""
        user = make_active_user(username='dan', password='temp-Pwd1!',
                                first_login=True)
        response = client.post('/api/auth/login/', {
            'username': 'dan', 'password': 'temp-Pwd1!'
        }, format='json')
        assert response.status_code == 200
        assert response.data['next_step'] == 'change_password'
        # Session con scope reducido (solo UC_AUTH_04 + UC_AUTH_02)
        session = Session.objects.get(user=user, state='ACTIVE')
        assert session.scope == 'restricted'
        # first_login sigue True hasta que UC_AUTH_04 complete
        user.refresh_from_db()
        assert user.first_login is True

    def test_login_warns_when_no_permissions(self):
        """CA-06: FA-04 User sin Assignments. Fuente: CA-06"""
        user = make_active_user(username='eve', password='S3cret!XY')
        # No Assignments ACTIVE para eve
        response = client.post('/api/auth/login/', {
            'username': 'eve', 'password': 'S3cret!XY'
        }, format='json')
        assert response.status_code == 200
        assert response.data['warning']['type'] == 'no_permissions'
        # AuditEvent extra para alertar a AGR-006
        assert AuditLog.objects.filter(
            event_type='LOGIN_NO_PERMISSIONS'
        ).exists()

class TestLoginExceptions:
    def test_login_unknown_username_returns_401(self):
        """CA-07 / EX-01. Fuente: uc-auth-01/excepciones.rst EX-01"""
        response = client.post('/api/auth/login/', {
            'username': 'noexiste', 'password': 'S3cret!XY'
        }, format='json')
        assert response.status_code == 401
        # No exponer si user existe (timing attack mitigation)
        assert response.data['error']['code'] == 'INVALID_CREDENTIALS'

    def test_login_wrong_password_returns_401(self):
        """CA-08 / EX-02"""
        user = make_active_user(username='frank', password='Correct!1')
        response = client.post('/api/auth/login/', {
            'username': 'frank', 'password': 'WrongPwd!'
        }, format='json')
        assert response.status_code == 401
        assert response.data['error']['code'] == 'INVALID_CREDENTIALS'

    def test_login_blocked_user_returns_401_and_audits(self):
        """CA-11 / EX-03. BR-015: bloqueo tras 5 intentos fallidos"""
        user = make_active_user(username='grace', password='S3cret!XY',
                                state='BLOCKED')
        response = client.post('/api/auth/login/', {
            'username': 'grace', 'password': 'S3cret!XY'
        }, format='json')
        assert response.status_code == 401
        assert AuditLog.objects.filter(
            event_type='BLOCKED_LOGIN_ATTEMPT'
        ).exists()

    def test_login_throttled_after_5_attempts(self):
        """BR-015: 5 intentos fallidos → cuenta bloqueada 30 min"""
        user = make_active_user(username='henry', password='S3cret!XY')
        for _ in range(5):
            client.post('/api/auth/login/', {
                'username': 'henry', 'password': 'wrong'
            }, format='json')
        user.refresh_from_db()
        assert user.state == 'BLOCKED'

    def test_login_db_timeout_returns_503(self):
        """EX-07: BD timeout → 503"""

    def test_login_invalid_payload_returns_400(self):
        """EX-06: datos malformados → 400 VALIDATION_ERROR"""
```

**Componentes a implementar** (de `uc-auth-01/implementacion-tecnica.rst` § 11):
- `LocalPasswordStrategy` — autenticación username+password, bcrypt
- `AuthService.login(credentials, client_info)` → `LoginOutput`
- `LoginView(APIView)` — `POST /api/auth/login/`
- `LoginSerializer` — validar formato username + password
- Transacción atómica: cerrar Session previa → crear Session nueva → emitir AuditEvent → actualizar last_login_at

**CNST-010:** `permission_classes = []` explícito (endpoint público).

---

### FASE 1.2 — UC_PERM_07: Verificar Permiso (T-02 completo)

**Fuente:** `casos-uso/permissions/uc-perm-07/` (12 partes)

Los tests están documentados en `uc-perm-07/testing.rst` § 12.2:

```python
# tests/unit/access/test_uc_perm_07.py
# Fuente: uc-perm-07/testing.rst § 12.2 — UT-01..UT-10 + IT-01..IT-06

class TestPrecedenceEvaluator:
    """UT-01..UT-09: PrecedenceEvaluator como función pura"""

    def test_ut_01_revoke_wins(self):
        """UT-01: revoke=True gana sobre grant y AGRs"""
        result = PrecedenceEvaluator.evaluate(
            revoke_active=True,
            grant_active=GrantInfo(valid_until=None),
            agr_codes=['A', 'B']
        )
        assert result.allowed is False
        assert result.origin == 'REVOKED_EXCEPTIONAL'

    def test_ut_02_grant_without_agr(self):
        """UT-02: grant excepcional sin AGR → allowed=True"""
        t = now() + timedelta(hours=1)
        result = PrecedenceEvaluator.evaluate(
            revoke_active=False,
            grant_active=GrantInfo(valid_until=t),
            agr_codes=[]
        )
        assert result.allowed is True
        assert result.origin == 'GRANTED_EXCEPTIONAL'
        assert result.valid_until == t

    def test_ut_03_agr_grants(self):
        """UT-03: AGR otorga → allowed=True, via_agr_codes completo"""
        result = PrecedenceEvaluator.evaluate(
            revoke_active=False, grant_active=None,
            agr_codes=['A', 'B', 'C']
        )
        assert result.allowed is True
        assert result.origin == 'GRANTED_BY_AGR'
        assert sorted(result.via_agr_codes) == ['A', 'B', 'C']

    def test_ut_04_no_match_denied(self):
        """UT-04: ningún match → DENIED_NO_GRANT"""
        result = PrecedenceEvaluator.evaluate(
            revoke_active=False, grant_active=None, agr_codes=[]
        )
        assert result.allowed is False
        assert result.origin == 'DENIED_NO_GRANT'

    def test_ut_05_ttl_truncated_by_valid_until(self):
        """UT-05: valid_until=now+30s, default=60s → ttl=30s"""
        valid_until = now() + timedelta(seconds=30)
        ttl = PermissionCache.compute_ttl(
            default=60, valid_until=valid_until
        )
        assert ttl <= 30

    def test_ut_06_ttl_default_when_null(self):
        """UT-06: valid_until=null → ttl=60s (default)"""
        ttl = PermissionCache.compute_ttl(default=60, valid_until=None)
        assert ttl == 60

    def test_ut_07_cache_key_construction(self):
        """UT-07: (user=42, fn='view_reports') → key='perm:42:view_reports'"""
        key = PermissionCache.build_key(user_id=42, function_code='view_reports')
        assert key == 'perm:42:view_reports'

    def test_ut_09_revoke_beats_grant_tiebreaker(self):
        """UT-09: ambos activos → revoke gana (determinismo)"""
        result = PrecedenceEvaluator.evaluate(
            revoke_active=True,
            grant_active=GrantInfo(valid_until=now() + timedelta(hours=1)),
            agr_codes=['A']
        )
        assert result.allowed is False
        assert result.origin == 'REVOKED_EXCEPTIONAL'

    def test_ut_10_invalidate_clears_all_user_keys(self):
        """UT-10: invalidate(user_id=42) → borra perm:42:* del cache"""
        cache.set('perm:42:view_reports', 'x')
        cache.set('perm:42:export_csv', 'x')
        PermissionCache.invalidate(user_id=42)
        assert cache.get('perm:42:view_reports') is None
        assert cache.get('perm:42:export_csv') is None

class TestPermissionServiceIntegration:
    """IT-01..IT-06: PermissionService con BD real"""

    @pytest.mark.django_db
    def test_it_01_agr_grants_cache_miss(self):
        """IT-01: AGR otorga, cache miss → query BD, response GRANTED_BY_AGR, cache poblado"""
        user = UserFactory(in_agr='AGR-001')  # view_reports incluida en AGR-001
        result = PermissionService.check(user.pk, 'view_reports')
        assert result.allowed is True
        assert result.origin == 'GRANTED_BY_AGR'
        assert result.cache is False
        # Segunda llamada: cache hit
        result2 = PermissionService.check(user.pk, 'view_reports')
        assert result2.cache is True

    @pytest.mark.django_db
    def test_it_02_inactive_agr_does_not_grant(self):
        """IT-02: AGR.state=INACTIVE → DENIED_NO_GRANT"""

    @pytest.mark.django_db
    def test_it_03_expired_assignment_does_not_grant(self):
        """IT-03: Assignment.valid_until pasado → DENIED"""

    @pytest.mark.django_db
    def test_it_05_revocation_over_agr(self):
        """IT-05: User en AGR + ExceptionalPermission REVOKE → REVOKED_EXCEPTIONAL"""

    @pytest.mark.django_db
    def test_it_06_multi_agr_returns_all_codes(self):
        """IT-06: 3 AGRs otorgan F → via_agr_codes tiene los 3"""

class TestPermissionServiceProperties:
    """CA-15..CA-17: propiedades de seguridad y rendimiento"""

    def test_ca_15_fail_closed_on_bd_timeout(self):
        """CA-15: BD timeout → 503, caller DENIEGA"""

    def test_ca_16_no_audit_event_on_check(self):
        """CA-16: N invocaciones → 0 AuditEvents emitidos por UC_PERM_07"""
        before = AuditLog.objects.count()
        PermissionService.check(1, 'view_reports')
        assert AuditLog.objects.count() == before  # sin audit

    def test_ca_11_bulk_check_50_functions_single_query(self):
        """CA-11: check_bulk 50 funciones → una sola query BD para misses"""
```

**Componentes a implementar** (de `uc-perm-07/implementacion-tecnica.rst` § 11.1):
- `PrecedenceEvaluator.evaluate(revoke, grant, agr_codes)` → `(allowed, origin, via_agr_codes, valid_until)` — función pura
- `PermissionCache.get/set/invalidate/compute_ttl/build_key` — wrapper sobre `django.core.cache`
- `PermissionService.check(user_id, function_code, bypass_cache=False)` → `CheckPermissionOutput`
- `PermissionService.check_bulk(user_id, function_codes)` → `BulkCheckOutput`
- Actualizar `HasFunction` DRF permission class para usar `PermissionService.check()` (ADR-BACK-006 § 2.2)
- `CheckPermissionView` (GET, admin) — requiere `view_assignments`
- `BulkCheckView` (POST) — requiere `view_assignments`

---

### FASE 1.3 — UC_USR_02: Consultar Usuarios (CRÍTICO)

**Fuente:** `casos-uso/users/uc-usr-02/`

```python
def test_list_users_paginated_50_per_page():
    """CA-01: 187 Users → page 1 tiene 50 items, count=187"""
    # fuente: uc-usr-02 CA-01

def test_list_users_masks_pii_in_response():
    """CA-02: CNST-026 — email mascarado o ausente en listado"""
    # response items NO contienen email completo

def test_list_users_requires_list_or_search_permission():
    """CA: sin USR-004/USR-005/USR-009 → 403"""
    # required_function='list_users' o 'search_users' o 'view_users'
```

---

### FASE 1.4 — UC_ACC_03: Consultar Permisos (CRÍTICO)

**Fuente:** `casos-uso/access/uc-acc-03/`

```python
def test_view_assignments_returns_consolidated_count():
    """CA-01: 3 directas + 1 AGR con 2 fns → effective_total_count=5"""

def test_view_assignments_deduplicates_functions():
    """CA-02: fn_id=1 directo Y vía AGR → aparece UNA vez, sources=[direct, via_agr:6]"""

def test_view_assignments_empty_for_user_without_assignments():
    """CA-03: User sin Assignments → 200 con listas vacías (no 404)"""

def test_view_assignments_requires_view_assignments_function():
    """CA: sin ACC-003 'view_assignments' → 403"""
```

---

### FASE 1.5 — UC_PIP_01: Supervisar ETL (CRÍTICO)

**Fuente:** `casos-uso/pipeline/uc-pip-01/`
**Función RBAC:** PIP-001 `view_pipeline_status` (no `'pipeline.view_status'`)

```python
def test_etl_status_returns_summary_with_correct_structure():
    """CA-01: summary correcto — jobs, status, lag, throughput"""

def test_etl_status_detects_stale_pipeline():
    """CA-02: última exitosa > umbral configurable → pipeline stale detectado"""

def test_etl_status_cache_hit_on_second_call():
    """CA-04: TTL 30s — segunda llamada sin query a BD"""

def test_etl_status_requires_view_pipeline_status():
    """CA-05: sin PIP-001 'view_pipeline_status' → 403"""
    # NOTA: corregir required_function del endpoint actual

def test_etl_status_503_on_mariadb_timeout():
    """CA-06: EX-03 BD timeout → 503"""
```

---

### FASE 1.6 — UC_AUD_01: Consultar Auditoría (CRÍTICO)

**Fuente:** `casos-uso/audit/uc-aud-01/`
**Función RBAC:** AUD-001 `view_audit_log` (no `'audit.view_log'`)

```python
def test_audit_list_returns_timeline_with_cursor():
    """CA-01: lista timeline con cursor y summary"""

def test_audit_list_filtered_by_module():
    """CA-02: filtro module → solo eventos de ese módulo"""

def test_audit_list_requires_view_audit_log():
    """CA: sin AUD-001 'view_audit_log' → 403"""

def test_general_audit_queried_event_emitted():
    """uc-aud-01 datos-involucrados: meta-audit GENERAL_AUDIT_QUERIED emitido (UC_PERM_09)"""
```

---

### FASE 1.7 — UC_AUTH_04: Cambiar Contraseña (CRÍTICO)

**Fuente:** `casos-uso/auth/uc-auth-04/`

```python
def test_change_password_happy_path():
    """CA-01: password_hash cambia, first_login=False, 1 PasswordHistory, 1 AuditEvent"""

def test_change_password_body_never_contains_new_password():
    """CA-01: CNST-026 — body NO contiene la contraseña nueva"""

def test_change_password_wrong_current_returns_400():
    """CA-02: password actual incorrecto → 400"""

def test_change_password_weak_new_password_returns_400():
    """CA-03: nueva contraseña no cumple política → 400"""

def test_change_password_clears_first_login_and_promotes_session():
    """CA-04: first_login=True → tras cambio exitoso, Session pasa a scope ACTIVE pleno"""
```

---

### FASE 1.8 — UC_RPT_01: Ver Dashboard (CRÍTICO)

**Fuente:** `casos-uso/reports/uc-rpt-01/`
**Función RBAC:** RPT-001 `view_reports`
**Contrato:** `DashboardService.get(user_id, period, context)` → `DashboardOutput`

```python
def test_dashboard_returns_kpis_populated():
    """CA-01: User con view_reports + segmento + datos → 200 con KPIs"""
    # DashboardOutput: period, refreshed_at, kpis, trend, segments_applied, cache, staleness_minutes

def test_dashboard_returns_zeros_without_data():
    """CA-02: sin rows en período → 200 con KPIs en 0, 'Sin datos para hoy'"""

def test_dashboard_400_when_user_without_segment():
    """CA-05: User sin segmento → 400 USER_WITHOUT_SEGMENT"""
    # SegmentResolver no resuelve segmento → error

def test_dashboard_default_period_is_today():
    """CA-06: sin param period → datos del día actual"""

def test_dashboard_requires_view_reports():
    """CA: sin RPT-001 'view_reports' → 403"""

def test_dashboard_503_on_analytics_db_timeout():
    """CA: AnalyticsRepo timeout → 503"""
```

---

## FASE 2 — UCs ALTOS (39 días estimados)
**Orden respeta cadenas de dependencia de `matriz-dependencias-uc-iact.rst` § 3.3**

```
UC_AUTH_02 Cerrar Sesión            1d  → req: UC_AUTH_01
UC_AUTH_05 Gestionar Sesiones       3d  → req: UC_AUTH_01, UC_AUTH_02
UC_USR_01  Crear Usuario            4d  → req: UC_ACC_01, UC_ACC_04
UC_USR_03  Modificar Usuario        3d  → req: UC_USR_02, UC_AUTH_05
UC_USR_04  Eliminar Usuario (baja)  2d  → req: UC_USR_02, UC_AUTH_05
UC_ACC_05  Gestionar SoD            5d  → raíz
UC_PERM_05 Crear Grupo Funciones    2d  → raíz
UC_ACC_01  Asignar Funciones        4d  → req: UC_ACC_05
UC_ACC_02  Revocar Funciones        2d  → req: UC_ACC_01
UC_ACC_04  Asignar Agrupador        2d  → req: UC_USR_02, UC_ACC_03
UC_PERM_06 Asignar Fns a Grupo      3d  → req: UC_PERM_05, UC_ACC_05
UC_PERM_01 Asignar Grupo a Usuario  2d  → req: UC_PERM_05
UC_PERM_02 Revocar Grupo            2d  → req: UC_PERM_01
UC_PERM_08 Generar Menú Dinámico    3d  → req: UC_PERM_07
UC_AUTH_03 Recuperar Contraseña     3d  → req: UC_USR_03
```

**CAs específicos de nota por UC:**

**UC_AUTH_02** (Cerrar Sesión):
- `Session.state='CLOSED'`, `close_reason='USER_LOGOUT'`, `closed_at` no NULL
- 2 entradas en `BlacklistedToken` (access + refresh)
- 1 `AuditEvent` con `event_type='LOGOUT'`

**UC_USR_01** (Crear Usuario):
- `User.username` auto-generado formato `base.NNNN` (BR-013, CNST-029)
- `User.first_login=True`, `User.state='ACTIVE'`
- `PasswordGenerator`: contraseña temporal con entropía criptográficamente segura
- `PasswordHasher`: bcrypt cost ≥ 12
- `InternalMessage` en buzón del nuevo User (CNST-001, BR-004)
- 1 `AuditEvent USER_CREATED`
- Body NO contiene contraseña (CNST-026)
- `access_group_id` opcional: si se omite, User creado sin Assignments (FA-01)

**UC_ACC_01** (Asignar Funciones):
- `FR-010-02`: validar SoD antes de asignar (BR-007) — `SoDValidator.validate()`
- `FR-010-04`: calcular permisos efectivos (preview antes de confirmar)
- `SeparationRule` como `Specification` evaluable
- `AuditEvent FUNCTIONS_ASSIGNED` con `function_ids_assigned`
- Cache de permisos invalidado post-COMMIT (P-29)
- Throttle 30 POST/min/invoker
- EX-05: auto-asignación prohibida (P-11)
- EX-08: SoD violation → 409

**UC_ACC_02** (Revocar Funciones):
- `FR-011-02`: `Assignment.state='REVOKED'` (BR-009 — no DELETE físico)
- `FR-011-03`: recalcular permisos efectivos tras revocación
- `revoke_reason` obligatorio
- `WarningsCalculator`: `no_functions`, `critical_function`, `last_holder`

**UC_PERM_08** (Generar Menú Dinámico):
- CNST-032: `get_user_menu(p_user_id)` SQL function — obligatoria
- CA-01: User con funciones en múltiples dominios → `domains` con N items
- CA-02: User sin funciones → `domains: []` (no error)
- CA-03: Function REVOKED no aparece en menú

---

## FASE 3 — UCs ALTOS RPT, ALR, PIP, LOG (27 días estimados)

```
UC_RPT_02 Ver Métricas Tiempo Real  4d  (stub documentado — CNST-003 sin SSE)
UC_RPT_03 Ver Reportes Históricos   4d  → req: UC_RPT_01
UC_RPT_04 Exportar Reporte          6d  → req: UC_RPT_01
UC_ALR_01 Configurar Umbrales       3d  → raíz
UC_ALR_02 Ver Alertas Activas       2d  → req: UC_ALR_01
UC_ALR_03 Reconocer Alerta          2d  → req: UC_ALR_02
UC_PIP_02 Consultar Errores ETL     2d  → req: UC_PIP_01
UC_PIP_03 Consultar Disponibilidad  2d  → req: UC_PIP_01
UC_PIP_04 Solicitar Reintento       3d  → req: UC_PIP_01, UC_PIP_02
UC_LOG_01 Ver Logs Aplicación       2d  → raíz
UC_LOG_02 Ver Logs ETL              2d  → req: UC_PIP_01
```

**CAs específicos de FASE 3:**

**UC_RPT_04** (Exportar Reporte — patrón Larman):
- POST /api/reports/export/ → 202 con `job_id`
- Formatos: CSV (RPT-004), Excel (RPT-005), PDF (RPT-006) — 3 funciones RBAC separadas
- `ExportJob.state` transitions: QUEUED → PROCESSING → DONE/FAILED
- `InternalMailbox.deliver_message()` cuando el export completa (CNST-001)

**UC_ALR_03** (Reconocer Alerta):
- `alert.state`: ACTIVE → ACKNOWLEDGED
- `acknowledged_by`, `acknowledged_at`, `acknowledged_note`
- `AuditEvent ALERT_ACKNOWLEDGED` (D-02 del corpus)
- EX: CrossSegment → 403; InvalidState (ya acknowledged) → 409

**UC_PIP_04** (Solicitar Reintento):
- `reason` ≥ 20 caracteres (validación documentada en flujo-principal)
- Pipeline no puede estar en `RUNNING`
- Último run debe ser `FAILED`
- `AuditEvent ETL_RETRY` con `actor_id + reason + run_id_origen`

---

## FASE 4 — UCs MEDIOS (38 días estimados)

```
UC_ACC_08  Permiso Temporal Excepcional   3d
UC_RPT_07  Programar Reporte             3d  → req: UC_RPT_01, UC_RPT_04
UC_RPT_08  Ver Reportes Programados      2d  → req: UC_RPT_07
UC_RPT_11  Compartir Reporte             3d  → req: UC_RPT_01 + InternalMailbox
UC_RPT_12..14 Reportes variantes         2d c/u (Agentes, Colas, Campañas)
UC_RPT_15..17 Reportes IVR SPs           2d c/u (Transferencias, Menús, Clientes)
UC_ALR_04  Ver Historial Alertas         2d  → req: UC_ALR_02
UC_ALR_05  Gestionar Suscripciones       4d  (ALR-008/009/010 — 3 funciones por SoD)
UC_AUD_04  Generar Reporte Compliance    5d  → req: UC_AUD_01, UC_AUD_03
UC_LOG_04  Exportar Logs                 3d  → req: UC_LOG_01
UC_LOG_05  Ver Logs Infraestructura      2d  → raíz
UC_PERM_03 Conceder Permiso Excepcional  3d
UC_PERM_04 Revocar Permiso Excepcional   1d
UC_AUTH_03 Recuperar Contraseña         3d  (InternalMailbox, no email)
```

---

## FASE 5 — UCs BAJOS (21 días estimados)

```
UC_ACC_09  Auditar Cambios de Acceso     2d
UC_RPT_09  Configurar Filtros            2d
UC_RPT_10  Guardar Vista                 2d
UC_PERM_09 Auditar Acceso               1d
UC_PERM_10 Consultar Auditoría Permisos  2d
UC_LOG_06  Ver Estado del Sistema        2d
UC_LOG_07  Ver Métricas Técnicas         3d
UC_LOG_03  Buscar Logs                   3d
UC_AUD_02  Buscar Auditoría              3d
UC_AUD_03  Exportar Auditoría            3d
```

---

## Tabla de volumen y estimaciones

| FASE | Descripción | UCs | Días |
|---|---|---|---|
| FASE 0 | Infraestructura transversal (T1-T6) | — | 8 |
| FASE 1 | 8 UCs CRÍTICOS | 8 | 29 |
| FASE 2 | 15 UCs ALTOS AUTH/USR/ACC/PERM | 15 | 39 |
| FASE 3 | 11 UCs ALTOS RPT/ALR/PIP/LOG | 11 | 27 |
| FASE 4 | 17 UCs MEDIOS | 17 | 38 |
| FASE 5 | 10 UCs BAJOS | 10 | 21 |
| **Total** | **61 UCs** | **61** | **162 días** |

---

## Criterio de DONE por FASE — derivado de los documentos

1. **Cada CA documentado en `Parte 9`** del UC tiene un test que lo verifica
2. **Los nombres de función en `required_function`** coinciden con el catálogo v5.4.0
3. **`permission_classes` es explícito** en cada view (CNST-010)
4. **AuditEvent emitido** en todas las operaciones de escritura (T-03, CNST-025)
5. **InternalMailbox** usado en lugar de email externo (CNST-001, BR-004)
6. **BR-009** (baja lógica) en todos los modelos con ciclo de vida — nunca DELETE
7. **Sin PII** en payloads de AuditEvent (CNST-026)
8. **Cobertura mínima** según `Parte 12` del UC: `AuthService` ≥ 95%, vistas ≥ 90%, serializers 100%
9. **Hallazgos documentados** en `docs/architecture/HALLAZGOS-FASEXX-*.md`

---

## Tests existentes identificados como incorrectos

| Archivo | Problema documentado | Corrección en FASE |
|---|---|---|
| `test_views.py` (authentication) | No cubre CA-02 (BR-005), CA-03 (atomicidad), CA-04 (first_login scope) | FASE 1.1 |
| `test_permissions.py` (access) | `HasFunction` no usa `PermissionService` con precedencia P-50 | FASE 1.2 |
| `test_views.py` (pipeline) | `required_function='pipeline.view_status'` vs canónico `'view_pipeline_status'` | FASE 1.5 |
| `test_api.py` (audit) | No verifica inmutabilidad BR-010 (UPDATE/DELETE rechazados) | FASE 0-T5 |
| Todos los endpoints con `required_function` | Usan strings pre-v5.4.0 (ej: `'logs.view'` vs `'view_application_logs'`) | FASE 0-T2 |
| `test_navigation_views.py` (core) | Corregido en FASE 7 — verificar que no regresionó | FASE 1 smoke |
