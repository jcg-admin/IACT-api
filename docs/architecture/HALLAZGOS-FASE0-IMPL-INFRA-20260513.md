# Hallazgos FASE 0 — Implementación Infraestructura Transversal

**Artefacto:** HALLAZGOS-FASE0-IMPL-INFRA-20260513
**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Rama:** `develop`
**Commits:** `270f8af` → `288d627` (5 commits)

---

## Contexto

FASE 0 implementa la infraestructura transversal que los 61 UCs del catálogo IACT
requieren como prerequisito. No implementa UCs — prepara el terreno para que FASE 1
pueda empezar con una base sin deuda técnica.

Fuentes de verdad consultadas:
- `IACT-docs/source/arquitectura-tecnica/rbac/modelo-rbac-iact.rst` v5.4.0
- `IACT-docs/source/arquitectura-tecnica/modelo-dominio-iact.rst` § 4.1..4.7
- `IACT-docs/source/backend/adr-back-006-rbac-estrategia-implementacion.rst`
- BR-001, BR-004, BR-007, BR-009, BR-010
- CNST-001, CNST-010, CNST-025, CNST-026, CNST-032, CNST-033

---

## Hallazgo F0-H-001 — Validator de Function.code rechazaba el 100% del catálogo v5.4.0

**Severidad:** Crítica
**Archivo:** `apps/core/validators.py` — `validate_function_code()`
**Commit que lo resuelve:** `270f8af`

**Estado anterior:**
```python
# Regex anterior: solo MAYUSCULAS + guion_bajo
if not re.match(r'^[A-Z][A-Z0-9_]{1,49}$', value):
```

**Impacto:** Todos los 61 códigos canónicos del catálogo v5.4.0 (`AUTH-001`, `USR-009`,
`LOG-007`, etc.) fallan este validator. Ningún código v5.4.0 podría haberse
cargado a través de formularios Django admin o serializers DRF que llamen
`full_clean()`.

**Resolución:**
```python
# Nuevo regex: formato MOD-NNN
if not re.match(r'^[A-Z]{2,4}-\d{3}$', value):
```

Acepta: `AUTH-001`, `RPT-011`, `LOG-007`
Rechaza: `USR_VIEW` (legacy), `reports.view` (namespace), `fn_0001` (factory)

---

## Hallazgo F0-H-002 — FunctionTestData generaba códigos inválidos para v5.4.0

**Severidad:** Alta
**Archivo:** `tests/test_data/access_test_data.py`
**Commit que lo resuelve:** `270f8af`

**Estado anterior:**
```python
code = factory.Sequence(lambda n: f'fn_{n:04d}')  # fn_0001, fn_0002...
```

**Impacto:** El código `fn_0001` no pasa el validator actualizado. Tests que
crearan `Function` con `full_clean()` fallarían. La factory es la base de
casi todos los tests de acceso.

**Resolución:**
```python
code = factory.Sequence(lambda n: f'TST-{n:03d}')  # TST-001, TST-002...
```

El prefijo `TST` es válido para v5.4.0 y es fácilmente identificable como
código de test.

---

## Hallazgo F0-H-003 — SeparationRule con estructura binaria incompatible con SoD grupal

**Severidad:** Crítica
**Archivo:** `apps/access/models.py` — `class SeparationRule`
**Commit que lo resuelve:** `270f8af`

**Estado anterior:**
```python
class SeparationRule(SoftDeleteModel):
    function_a = models.ForeignKey(Function, ...)   # solo 2 funciones por regla
    function_b = models.ForeignKey(Function, ...)
    status = models.CharField(choices=[('active','Active'),('suspended','Suspended'),('deleted','Deleted')])
```

**Impacto:** El modelo solo puede expresar "función X incompatible con función Y"
(par). Los 3 SoD del v5.4.0 son grupales:
- SOD-001: Pipeline (4 funciones PIP-*) vs Auditoría (4 funciones AUD-*)
- SOD-002: Usuarios (9 funciones USR-*) vs Auditoría
- SOD-003: Acceso (12 funciones ACC-*) vs Auditoría

Con el modelo binario se necesitarían `4×4 + 9×4 + 12×4 = 100 reglas`
para modelar los 3 SoD. El modelo correcto es grupal con M2M.

Adicionalmente, los choices `active/suspended/deleted` violan BR-009
(debe ser `ENABLED/DISABLED`, nunca `deleted`).

**Resolución:**
```python
class SeparationRule(models.Model):
    code = models.CharField(max_length=20, unique=True)  # SOD-001
    name = models.CharField(max_length=200)
    state = models.CharField(choices=[('ENABLED','Enabled'),('DISABLED','Disabled')])
    functions_set_a = models.ManyToManyField(Function, related_name='sod_rules_as_set_a')
    functions_set_b = models.ManyToManyField(Function, related_name='sod_rules_as_set_b')

    def is_violated_by(self, function_codes: set[str]) -> bool:
        """Patrón Specification — FR-010-02, BR-007."""

    def find_conflict(self, function_codes: set[str]) -> tuple[str, str] | None:
        """Retorna el primer par en conflicto."""
```

Migración 0005 elimina las FKs binarias y el constraint `unique_separation_pair_active`,
y crea los campos nuevos.

---

## Hallazgo F0-H-004 — UserFunctionAssignment sin estado canónico, sin expiración ni revocación

**Severidad:** Crítica
**Archivo:** `apps/access/models.py` — `class UserFunctionAssignment`
**Commit que lo resuelve:** `270f8af`

**Estado anterior:**
```python
class UserFunctionAssignment(models.Model):
    is_active = models.BooleanField(default=True)
    # Sin state, sin expires_at, sin revoked_at, sin revoke_reason
```

**Impacto:** Los siguientes UCs no pueden implementarse correctamente:
- UC_ACC_02 CA-01: `Assignment.state='REVOKED'`, `revoked_at`, `revoke_reason` — campos inexistentes
- UC_ACC_02 CA-02: Soft-delete (BR-009) requiere `state` no solo `is_active`
- UC_ACC_01 CA-02: Asignación temporal con `expires_at` — campo inexistente
- UC_PERM_07 CA-06: "Assignment expirado no cuenta" — sin `expires_at` no verificable
- UC_PERM_07 CA-07: "Concesión expirada no cuenta" — idem

`is_active` es un boolean que no diferencia entre `EXPIRED` y `REVOKED`, dos
estados con semánticas distintas (uno es automático, el otro es explícito).

**Resolución:**
```python
class UserFunctionAssignment(models.Model):
    state = models.CharField(
        choices=[('ACTIVE','Active'), ('EXPIRED','Expired'), ('REVOKED','Revoked')],
        default='ACTIVE', db_index=True,
    )
    is_active = models.BooleanField(default=True)  # compatibilidad — sincronizado
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey(User, null=True, blank=True, ...)
    revoke_reason = models.CharField(max_length=500, blank=True)

    def revoke(self, revoked_by, reason: str) -> None: ...
    def is_currently_valid(self) -> bool: ...  # state=ACTIVE + not expired
```

---

## Hallazgo F0-H-005 — InternalMailbox no existía en el proyecto

**Severidad:** Crítica
**Archivo:** `apps/alerts/models.py` (creado)
**Commit que lo resuelve:** `0b630cf`

**Estado anterior:** Solo existía `InternalMessage` (mensajes entre usuarios
con M2M `recipients`). El concepto de buzón individual 1:1 por usuario
no existía.

**Impacto:** Los siguientes UCs requieren `InternalMailbox`:
- UC_USR_01 CA-01: "1 InternalMessage en buzón del nuevo User"
- UC_AUTH_01 FA-01: notificación en el buzón al primer login
- UC_AUTH_03 CA-01: contraseña temporal entregada vía buzón (no email)
- UC_ALR_05: alertas entregadas vía buzón

Sin `InternalMailbox`, CNST-001 ("solo buzón interno, sin email externo")
y BR-004 ("no canales externos") no podían cumplirse estructuralmente.

**Resolución:**
Modelos nuevos:
- `InternalMailbox`: OneToOneField → User, con `deliver_message()`
- `MailboxMessage`: FK → InternalMailbox, state UNREAD/READ/DELETED (BR-009)

Señal:
- `post_save(User)` → `InternalMailbox.get_or_create(owner=user)`

Migración: `alerts/0003_fase0_internal_mailbox.py`

---

## Hallazgo F0-H-006 — create_functions.py tenía bug crítico: 'module' como string en campo FK

**Severidad:** Alta
**Archivo:** `apps/access/management/commands/create_functions.py`
**Commit que lo resuelve:** `5f3199d`

**Estado anterior:**
```python
Function.objects.update_or_create(
    permission_django=permission_django,
    defaults={
        'module': data['module'],  # ← STRING 'MOD_Users', pero es FK!
        ...
    }
)
```

**Impacto:** `Function.module` es `ForeignKey(Module, ...)`. Pasar un string
`'MOD_Users'` al campo `module` en `update_or_create` lanza `ValueError` en
runtime. El comando nunca funcionó correctamente. Además, usaba `permission_django`
como campo de búsqueda (legacy), no `code` (canónico).

**Resolución:** Reescritura completa del comando:
```python
# Crear módulos primero (FK), luego funciones con FK real
module = modules[module_code]  # dict {code: Module instance}
Function.objects.update_or_create(
    code=code,                 # campo canónico como lookup
    defaults={'module': module, 'name': name, ...}
)
```

---

## Hallazgo F0-H-007 — HasFunction verificaba por permission_django (legacy), no por Function.code

**Severidad:** Alta
**Archivos:** `apps/access/permissions/function_permissions.py`, 4 archivos de views
**Commit que lo resuelve:** `288d627`

**Estado anterior:**
```python
class HasFunction(BasePermission):
    def has_permission(self, request, view):
        ...
        return request.user.has_function(required_function)
        # has_function() busca por permission_django, no por code

# En views:
required_function = 'logs.view'       # namespace legacy
required_function = 'reports.view_ivr' # namespace legacy
```

**Impacto:** Cuando se cargue el catálogo v5.4.0, los 61 códigos canónicos
no tienen `permission_django` configurado. `has_function('logs.view')` busca
`Function.objects.get(permission_django='logs.view')` — que no existirá.
Todos los endpoints protegidos devuelven 403 después de cargar el catálogo v5.4.0.

**Resolución:**
```python
class HasFunction(BasePermission):
    def has_permission(self, request, view):
        ...
        return request.user.has_function_by_code(required_function)
        # has_function_by_code() busca por code canónico

# User.has_function_by_code(code):
#   return code in self.get_functions()
#   get_functions() devuelve códigos v5.4.0
```

38 endpoints actualizados:
- `logs/views.py`: `'logs.view'` → `'LOG-001'` (7x), `'logs.export'` → `'LOG-002'` (2x)
- `reports/views.py`: `'reports.view'` → `'RPT-001'` (2x), `'reports.export'` → `'RPT-004'` (1x), `'reports.schedule'` → `'RPT-009'` (1x)
- `reports/ivr_views.py`: `'reports.view_ivr'` → `'RPT-001'` (9x)
- `access/views.py`: `'access.view_permissions'` → `'ACC-003'` (3x), `'access.assign_functions'` → `'ACC-001'` (5x), `'access.view_separation_rules'` → `'ACC-005'` (4x), `'access.view_groups'` → `'ACC-003'` (4x)

---

## Resumen de implementación FASE 0

| Task | Descripción | Estado | Commit |
|---|---|---|---|
| F0-T1 | Validator + schema canónico (SeparationRule + UserFunctionAssignment) | Completo | `270f8af` |
| F0-T2 | Catálogo RBAC v5.4.0 (61 fns + 10 AGRs + 3 SoD) | Completo | `5f3199d` |
| F0-T3 | SQL functions PostgreSQL (5 funciones PL/pgSQL) | Completo | `288d627` |
| F0-T4 | InternalMailbox + MailboxMessage + señal post_save | Completo | `0b630cf` |
| F0-T5 | AuditEvent canónico + emit() + PII stripping | Completo | `4ed36c8` |
| F0-T6 | DB router + test config ivr | Completo | `270f8af` |
| F0-T7 | HasFunction v5.4.0 + required_function → código canónico | Completo | `288d627` |

### Migraciones generadas

| App | Migración | Descripción |
|---|---|---|
| `access` | `0005_fase0_schema_canonico.py` | SeparationRule M2M + UserFunctionAssignment state/expires/revoke |
| `access` | `0006_fase0_sql_functions_postgresql.py` | 5 funciones PL/pgSQL (solo PostgreSQL) |
| `alerts` | `0003_fase0_internal_mailbox.py` | InternalMailbox + MailboxMessage |

### Archivos modificados (fuera de migraciones)

| Archivo | Cambio |
|---|---|
| `apps/core/validators.py` | `validate_function_code`: regex nuevo |
| `apps/access/models.py` | `SeparationRule` (M2M grupal) + `UserFunctionAssignment` (state, expires, revoke) |
| `apps/access/permissions/function_permissions.py` | `HasFunction` → `has_function_by_code()` |
| `apps/access/management/commands/create_functions.py` | Reescrito: 61 fns v5.4.0, FK correcta |
| `apps/access/management/commands/create_access_groups.py` | Nuevo: 10 AGRs |
| `apps/access/management/commands/create_sod_rules.py` | Nuevo: 3 SoD |
| `apps/alerts/models.py` | InternalMailbox + MailboxMessage (agregados) |
| `apps/alerts/signals.py` | Nuevo: post_save(User) → InternalMailbox |
| `apps/alerts/apps.py` | Import de signals en ready() |
| `apps/audit/models.py` | VALID_EVENT_TYPES + AuditValidationError + _PII_FIELDS |
| `apps/audit/services.py` | AuditLogService.emit() + _strip_pii() |
| `apps/users/models.py` | User.has_function_by_code() |
| `tests/test_data/access_test_data.py` | FunctionTestData.code → TST-NNN |
| `apps/logs/views.py` | 9 required_function → LOG-001/002 |
| `apps/reports/views.py` | 4 required_function → RPT-001/004/009 |
| `apps/reports/ivr_views.py` | 9 required_function → RPT-001 |
| `apps/access/views.py` | 16 required_function → ACC-001/003/005 |
| `config/settings/fase0_testing.py` | Nuevo: SQLite en memoria + ivr TEST NAME=None |

### Tests verificados (todos PASS)

| Test | Resultado |
|---|---|
| F0-T6: `allow_migrate('ivr', ...)` retorna `False` (no None) | PASS |
| F0-T6: ivr TEST NAME es None en fase0_testing | PASS |
| F0-T1: 61 códigos v5.4.0 pasan el nuevo validator | PASS |
| F0-T1: Códigos legacy (USR_VIEW, fn_0001) fallan el validator | PASS |
| F0-T1: SeparationRule crea con code + M2M | PASS |
| F0-T1: UserFunctionAssignment.revoke() actualiza state + campos | PASS |
| F0-T2: `create_functions` carga 61/61 funciones en 8 módulos | PASS |
| F0-T2: `create_access_groups` carga 10/10 AGRs con funciones correctas | PASS |
| F0-T2: AGR-001 tiene las 6 funciones exactas del catálogo | PASS |
| F0-T2: `create_sod_rules` carga 3/3 SoD ENABLED | PASS |
| F0-T2: SOD-001.is_violated_by(PIP+AUD)=True | PASS |
| F0-T4: post_save crea InternalMailbox al crear User | PASS |
| F0-T4: deliver_message no llama send_mail (CNST-001) | PASS |
| F0-T4: BR-009: delete() en MailboxMessage es baja lógica | PASS |
| F0-T5: emit() retorna AuditLog con pk asignado (UC_PERM_09 CA-01) | PASS |
| F0-T5: save() en AuditLog existente lanza PermissionError (CA-02) | PASS |
| F0-T5: event_type desconocido lanza AuditValidationError (CA-03) | PASS |
| F0-T5: password y token redactados, username preservado (CNST-026) | PASS |
| F0-T5: delete() en AuditLog lanza PermissionError (BR-010) | PASS |
| F0-T7: has_function_by_code('RPT-001')=True, ('LOG-001')=False | PASS |
| F0-T7: HasFunction verifica RPT-001=True, LOG-001=False | PASS |
| F0-T7: 0 required_function legacy en views (logs, reports, access) | PASS |
