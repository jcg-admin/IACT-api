# Hallazgos FASE 1 — Implementación 8 UCs Críticos

**Artefacto:** HALLAZGOS-FASE1-IMPL-20260513
**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Rama:** `develop`
**Commits:** `69e83e1` → `8d5b86d` (9 commits)

---

## Contexto

FASE 1 implementa los 8 UCs críticos de la matriz de dependencias
(`matriz-dependencias-uc-iact.rst` § 1.2.1). Son "críticos" porque
59 de los 61 UCs del catálogo dependen de al menos uno de ellos.

Fuentes de verdad consultadas por UC:
- `uc-auth-01/` — LoginService, LoginView
- `uc-perm-07/` — PrecedenceEvaluator, PermissionCache, PermissionService
- `uc-usr-02/` — UserListSerializer, UserDetailSerializer
- `uc-acc-03/` — EffectivePermissionsView (existente, completado)
- `uc-pip-01/` — etl_status (existente, corregido)
- `uc-aud-01/` — AuditLogViewSet (existente, corregido)
- `uc-auth-04/` — ChangePasswordView, PasswordHistory
- `uc-rpt-01/` — DashboardView, DashboardService

---

## Hallazgo F1-H-001 — User sin campos canónicos del modelo de dominio

**Severidad:** Crítica
**Archivo:** `apps/users/models.py`
**Commit que lo resuelve:** `69e83e1`

**Estado anterior:** El modelo `User` no tenía `state`, `first_login`,
`password_expires_at`, ni `last_login_at`.

**Impacto:**
- UC_AUTH_01 no podía verificar `state=BLOCKED` (CA-09) ni `state=INACTIVE` (CA-10)
- UC_AUTH_01 FA-01 no podía detectar `first_login=True`
- UC_AUTH_01 FA-02 no podía advertir sobre expiración de contraseña
- UC_AUTH_01 paso 14 no podía actualizar `last_login_at`

**Resolución:** Cuatro campos con migración `users/0002_fase1_user_canonical_fields.py`.

---

## Hallazgo F1-H-002 — SessionLog estructura incorrecta para UC_AUTH_01

**Severidad:** Crítica
**Archivo:** `apps/authentication/models.py` — clase `SessionLog`
**Commit que lo resuelve:** `54cacd4`

**Estado anterior:** `SessionLog` tenía `is_active` boolean, `session_key` string
(clave de sesión Django), sin `state` enum, sin `close_reason`, sin `client_info`,
sin `session_id` UUID, sin `expires_at`.

**Impacto:** No modelaba el concepto de Session del dominio
(`modelo-dominio-iact.rst § 4.1`). UC_AUTH_01 CA-02 requiere
`Session.state='CLOSED'` + `close_reason='SUPERSEDED'` al reemplazar
sesión previa (BR-005). Con `is_active` boolean eso era imposible.

**Resolución:** Modelo `Session` separado con todos los campos del dominio.
`SessionLog` se preserva (compatibilidad) pero el nuevo flujo usa `Session`.

---

## Hallazgo F1-H-003 — PermissionVerifyView importada en urls.py sin existir en views.py

**Severidad:** Alta (servidor no levantaba)
**Archivo:** `apps/access/urls.py` línea 91
**Commit que lo resuelve:** `6d4ab9d`

**Estado anterior:** La línea
`path('permissions/verify/', PermissionVerifyView.as_view(), name='permission-verify')`
fue agregada al final de `urls.py` pero `PermissionVerifyView` no estaba en
el bloque de imports. Cualquier request a cualquier endpoint de `apps.access`
producía `NameError: name 'PermissionVerifyView' is not defined`.

**Resolución:** Agregar `PermissionVerifyView` al bloque de imports del archivo.

---

## Hallazgo F1-H-004 — AuditLogViewSet sin HasFunction ni required_function

**Severidad:** Alta (exposición de seguridad)
**Archivo:** `apps/audit/views.py` — clase `AuditLogViewSet`
**Commit que lo resuelve:** `aaa48df`

**Estado anterior:**
```python
permission_classes = [IsAuthenticated]
# Sin HasFunction, sin required_function
```

**Impacto:** Cualquier usuario autenticado podía leer el log de auditoría
completo de la organización, incluyendo logs de otros usuarios. La función
`AUD-001 view_audit_log` no se verificaba en absoluto.

**Resolución:**
```python
permission_classes = [IsAuthenticated, HasFunction]
required_function = 'AUD-001'
```
Se agrega además `@extend_schema_view` completo con descripción, parámetros
y tags para drf-spectacular.

---

## Hallazgo F1-H-005 — etl_status con verificación manual de permiso usando namespace legado

**Severidad:** Media
**Archivo:** `apps/pipeline/views.py` — función `etl_status`
**Commit que lo resuelve:** `aaa48df`

**Estado anterior:**
```python
def etl_status(request):
    if not (request.user.is_superuser or
            request.user.has_function('pipeline.view_status')):
        return Response({'error': 'Function pipeline.view_status required.'}, 403)
```

**Impacto dual:**
1. La verificación era redundante porque `@permission_classes([IsAuthenticated, HasFunction])`
   ya estaba en el decorador, pero `HasFunction` necesita `required_function` para funcionar.
   Sin `required_function`, `HasFunction` no verificaba nada (retornaba `True` siempre).
2. `has_function('pipeline.view_status')` buscaba `Function.objects.get(permission_django='pipeline.view_status')`.
   Después de cargar el catálogo v5.4.0, ese campo no existe — la función es `PIP-001`, no `pipeline.view_status`.

**Resolución:**
```python
# Eliminar el if manual del body.
etl_status.required_function = 'PIP-001'
# HasFunction lo lee vía getattr(view, 'required_function')
```

---

## Hallazgo F1-H-006 — Dos implementaciones de UserViewSet en conflicto; function_map con namespaces legados

**Severidad:** Alta
**Archivos:** `apps/users/viewsets.py` y `apps/users/viewsets/user_viewset.py`
**Commit que lo resuelve:** `a977f68`

**Estado anterior:** Existían dos clases `UserViewSet`:
- `apps/users/viewsets.py` — con `@extend_schema_view` completo pero `function_map` legado
- `apps/users/viewsets/user_viewset.py` — sin `@extend_schema_view` y `function_map` legado

`urls.py` registraba `from .viewsets.user_viewset import UserViewSet`, por lo que el que
se usaba en producción era el que carecía de documentación drf-spectacular.

Ambos tenían `function_map` con namespaces Django legacy:
```python
function_map = {
    'list': 'users.view',    # <- namespace legacy
    'retrieve': 'users.view',
    ...
}
```

Combinado con F1-H-007 (abajo), ningún endpoint de users verificaba permisos RBAC
correctamente después de cargar el catálogo v5.4.0.

**Resolución:**
- Ambos `UserViewSet` actualizados a `function_map` con códigos v5.4.0
- `viewsets/user_viewset.py` usa `UserListSerializer` y `UserDetailSerializer` canónicos
- Se preserva ambas implementaciones para compatibilidad durante la transición

---

## Hallazgo F1-H-007 — RequiresFunctionPermission llamaba has_function() con namespace legado

**Severidad:** Alta
**Archivo:** `apps/core/permissions.py` — clase `RequiresFunctionPermission`
**Commit que lo resuelve:** `a977f68`

**Estado anterior:**
```python
permission_django = function_map[action]
return request.user.has_function(permission_django)
```

`has_function()` buscaba `Function.objects.get(permission_django=permission_django)`.
Después de cargar el catálogo v5.4.0, `Function.permission_django` no tiene valores
para los 61 códigos canónicos (`AUTH-001`, `USR-004`, etc.) — solo las funciones legacy
tenían ese campo populado.

**Impacto:** Todos los ViewSets que usaran `RequiresFunctionPermission` + `function_map`
con códigos v5.4.0 denegarían acceso a todos los usuarios porque la función no se
encontraría en BD.

**Resolución:**
```python
required_code = function_map[action]
return request.user.has_function_by_code(required_code)
```
`has_function_by_code()` verifica directamente `code in self.get_functions()`
sin pasar por `permission_django`.

---

## Hallazgo F1-H-008 — PasswordHistory y password_changed_at inexistentes

**Severidad:** Crítica
**Archivos:** `apps/users/models.py`, `apps/users/migrations/`
**Commit que lo resuelve:** `552ceae`

**Estado anterior:** El modelo `User` no tenía `password_changed_at`. No existía
modelo `PasswordHistory`.

**Impacto:** UC_AUTH_04 no podía implementarse:
- PASO 9 (`uc-auth-04/flujo-principal.rst § 3.2`): verificar reuso de los últimos
  5 hashes requiere `PasswordHistory`
- PASO 10: actualizar `User.password_changed_at = NOW()` requiere el campo
- PASO 14: el response incluye `changed_at` que viene de `password_changed_at`

**Resolución:**
- `User.password_changed_at`: DateTimeField nullable (migración `0003`)
- `PasswordHistory`: modelo con `user FK`, `password_hash`, `changed_at auto_now_add`
  + método `record_and_purge()` que mantiene máximo `HISTORY_DEPTH=5` entradas

---

## Hallazgo F1-H-009 — DashboardSummaryView completamente ausente

**Severidad:** Crítica
**Archivos:** `apps/reports/` — ningún archivo
**Commit que lo resuelve:** `8d5b86d`

**Estado anterior:** No existía `DashboardView`, `DashboardService`, `KPICalculator`,
`TrendBuilder`, `StalenessChecker`, `MetricsCache`, `AnalyticsRepo` ni `SegmentResolver`.
`reports/urls.py` no registraba ningún endpoint `/api/reports/dashboard/`.

**Impacto:** UC_RPT_01 era el único UC crítico sin ninguna implementación de base.
Dado que UC_RPT_01 depende de datos del pipeline (UC_PIP_01) y que 
el dashboard es la pantalla principal post-login, su ausencia bloqueaba
cualquier smoke test end-to-end del sistema.

**Resolución:** Implementación completa desde cero:
- `PeriodValidator`: valida `today`/`yesterday`/`last_7d`
- `SegmentResolver`: resuelve segmentos del usuario via AccessGroups (CNST-008)
- `KPICalculator.derive(rows)`: TMO, Service Level %, Abandon Rate %
- `TrendBuilder.build(rows, period)`: buckets por hora (today) o por día (last_7d)
- `StalenessChecker.compute(rows)`: detecta datos con > 90 min de antigüedad
- `MetricsCache`: TTL adaptativo por período (30s/60s/300s)
- `AnalyticsRepo`: lee `base_ivr_detalle` en MariaDB; devuelve `[]` si no disponible
- `DashboardService.get()`: orquesta todo el flujo
- `DashboardView`: endpoint con `required_function='RPT-001'`, `@extend_schema` completo

---

## Resumen de implementación FASE 1

| UC | Componentes producidos | Estado | Commit |
|---|---|---|---|
| UC_AUTH_01 | LoginService, LoginView, Session model | Completo | `40403d3` |
| UC_PERM_07 | PrecedenceEvaluator, PermissionCache, PermissionService, PermissionVerifyView | Completo | `6d4ab9d` |
| UC_USR_02 | UserListSerializer (email_masked), UserDetailSerializer, function_map v5.4.0 | Completo | `a977f68` |
| UC_ACC_03 | EffectivePermissionsView (existente, required_function='ACC-003' ya correcto) | Completo | — |
| UC_PIP_01 | etl_status.required_function='PIP-001' (elimina verificación manual legada) | Completo | `aaa48df` |
| UC_AUD_01 | AuditLogViewSet + required_function='AUD-001' + HasFunction + @extend_schema | Completo | `aaa48df` |
| UC_AUTH_04 | ChangePasswordView, PasswordHistory, password_changed_at | Completo | `552ceae` |
| UC_RPT_01 | DashboardView, DashboardService, KPICalculator, TrendBuilder, StalenessChecker | Completo | `8d5b86d` |

### Prerrequisitos commiteados antes de los UCs

| Prerequisito | Commit |
|---|---|
| User.state + first_login + password_expires_at + last_login_at | `69e83e1` |
| Session modelo canónico (separado de SessionLog) | `54cacd4` |
| Fix NameError PermissionVerifyView en access/urls.py | `6d4ab9d` (parte) |
| Fix AuditLogViewSet + etl_status | `aaa48df` |

### Tests verificados (selección)

| Test | UC | Resultado |
|---|---|---|
| CA-01: login exitoso, tokens, session, AuditLog, last_login_at | UC_AUTH_01 | PASS |
| CA-02: Session previa SUPERSEDED | UC_AUTH_01 | PASS |
| CA-03: rollback atómico → 503 DB_TRANSIENT_ERROR | UC_AUTH_01 | PASS |
| CA-04: first_login → next_step + scope=restricted | UC_AUTH_01 | PASS |
| CA-05: password expirando → warning.type=password_expiring | UC_AUTH_01 | PASS |
| CA-06: sin permisos → warning.type=no_permissions | UC_AUTH_01 | PASS |
| CA-07..10: credenciales inválidas, BLOCKED, INACTIVE | UC_AUTH_01 | PASS |
| CA-11: 5 fallos → BLOCKED → 6to intento 403 | UC_AUTH_01 | PASS |
| CA-12: payload inválido → 400 VALIDATION_ERROR | UC_AUTH_01 | PASS |
| CA-14: AuditLog inmutable | UC_AUTH_01 | PASS |
| CA-15b: no PII en AuditLog payload | UC_AUTH_01 | PASS |
| UT-01..09: PrecedenceEvaluator función pura | UC_PERM_07 | PASS |
| UT-10: invalidate clears perm:42:* del cache | UC_PERM_07 | PASS |
| IT-01: AGR grants cache miss → GRANTED_BY_AGR | UC_PERM_07 | PASS |
| IT-01b: cache hit segunda llamada | UC_PERM_07 | PASS |
| CA-11: check_bulk 4 códigos | UC_PERM_07 | PASS |
| CA-12: función no existe → ValueError | UC_PERM_07 | PASS |
| CA-13: user no existe → LookupError | UC_PERM_07 | PASS |
| CA-02: email_masked en listado (CNST-026) | UC_USR_02 | PASS |
| CA-03: email completo en detalle | UC_USR_02 | PASS |
| CA-01: cambio exitoso → first_login=False, PasswordHistory, AuditLog | UC_AUTH_04 | PASS |
| CA-02: password actual incorrecto → 400 WRONG_CURRENT_PASSWORD | UC_AUTH_04 | PASS |
| CA-03: contraseña débil → 400 WEAK_PASSWORD + violations | UC_AUTH_04 | PASS |
| CA-05: igual a actual → 400 SAME_AS_CURRENT | UC_AUTH_04 | PASS |
| CNST-026: no PII en AuditLog PASSWORD_CHANGED | UC_AUTH_04 | PASS |
| UT-01: TMO = sum_duration / answered | UC_RPT_01 | PASS |
| UT-02: Service Level % | UC_RPT_01 | PASS |
| UT-03: Abandon Rate % | UC_RPT_01 | PASS |
| UT-04: rows vacías → KPIs en 0 | UC_RPT_01 | PASS |
| UT-07: período inválido rechazado | UC_RPT_01 | PASS |
| CA-06: sin param → today | UC_RPT_01 | PASS |
| SEC-02: sin RPT-001 → 403 | UC_RPT_01 | PASS |
