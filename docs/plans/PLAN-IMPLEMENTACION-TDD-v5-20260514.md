# Plan de Implementación TDD v5.0.0

**Versión:** 5.0.0
**Fecha:** 2026-05-14
**Base:** `develop` @ `fd7711d` (análisis de gaps commiteado)
**Referencia:** `ANALISIS-GAPS-POST-PLAN-TDD-v4-20260513.md`
**Metodología:** Red → Green → Refactor por CA. Tareas atómicas. Una tarea = un commit.

----

## Convenciones del plan

### Identificadores de tarea

Cada tarea lleva un identificador único de la forma:

```
F<fase>-<GRUPO>-T<nro>
```

Ejemplos: `F6-P0-T1` (FASE 6, Grupo Prerrequisitos, tarea 1),
`F6-GA-T3` (FASE 6, Grupo A, tarea 3).

### Criterio de completitud

Una tarea está **completa** cuando su commit pasa la suite de verificación
sin nuevas colisiones de drf-spectacular y sin FAIL en el bloque de
verificación correspondiente a esa tarea.

### Estimaciones

Las estimaciones son en horas de trabajo efectivo de un desarrollador
individual. No incluyen revisión de código (CR), que se asume como proceso
paralelo.

### Columnas de la tabla de tareas

| Columna | Significado |
|---|---|
| ID | Identificador único de la tarea |
| Horas | Estimación en horas efectivas |
| Artefactos | Archivos creados o modificados |
| Dep. | Tareas que deben estar completas antes |
| Criterio | Verificación binaria de completitud |

----

## FASE 6 — Remediación de deuda técnica + cobertura TDD de UCs IMPL

**Objetivo:** Llevar al 85 % del corpus a estado TDD canónico.
Remediar la totalidad de la deuda técnica de drf-spectacular.
**Estimación total:** 26 días (43 tareas atómicas).
**Precondición:** `develop @ fd7711d` en estado limpio, sin conflictos.

----

### GRUPO P0 — Prerrequisitos de FASE 6

Estas tareas deben ejecutarse antes de cualquier otro grupo. Son independientes
entre sí y pueden asignarse en paralelo, pero todas deben completarse antes de
iniciar el Grupo GA.

---

**F6-P0-T1 — Fix DT-SPECTACULAR-001: colisión `audit_event_export`**

| Campo | Valor |
|---|---|
| Horas | 2 |
| Artefactos | `apps/audit/audit_event_views.py`, `apps/audit/urls.py` |
| Dep. | ninguna |
| Criterio | `drf-spectacular` no emite `audit_event_export collision` en el output de generación del schema. Test: `python manage.py spectacular --validate` sin warnings de colisión. |

Pasos:
1. Crear `AuditExportView` separada (hereda de `AuditEventExportView`) con `@extend_schema(operation_id='audit_legacy_export')` o añadir `operation_id` diferenciado directamente en la ruta de `audit/urls.py`.
2. Registrar la URL `/api/audit/export/` apuntando a la vista con su `operation_id` propio.
3. Verificar que ambas rutas responden correctamente.
4. Commit: `fix(spectacular): DT-SPECTACULAR-001 — audit_event_export collision`.

---

**F6-P0-T2 — Fix DT-SPECTACULAR-002: colisión `access_access_groups_retrieve`**

| Campo | Valor |
|---|---|
| Horas | 2 |
| Artefactos | `apps/access/access_group_view.py` |
| Dep. | ninguna |
| Criterio | `access_access_groups_retrieve collision` no aparece en output de drf-spectacular. |

Pasos:
1. Añadir `@extend_schema(operation_id='access_group_list', ...)` en el método `get` de `AccessGroupListCreateView`.
2. Añadir `@extend_schema(operation_id='access_group_retrieve', ...)` en el método `get` de `AccessGroupDetailView`.
3. Commit: `fix(spectacular): DT-SPECTACULAR-002 — access_group_retrieve collision`.

---

**F6-P0-T3 — Fix DT-SPECTACULAR-003: colisión `auth_change_password_create`**

| Campo | Valor |
|---|---|
| Horas | 1 |
| Artefactos | `apps/authentication/urls.py` |
| Dep. | ninguna |
| Criterio | `auth_change_password_create collision` no aparece. |

Pasos:
1. Localizar la URL legacy `/api/auth/change_password/` (con underscore).
2. Eliminar la ruta legacy o añadir `include` con namespace diferenciado que asigne un `operation_id` explícito.
3. Verificar que el endpoint canónico `/api/auth/change-password/` (con guión) sigue funcionando.
4. Commit: `fix(spectacular): DT-SPECTACULAR-003 — change_password URL legacy eliminada`.

---

**F6-P0-T4 — Fix DT-SPECTACULAR-004/005: colisiones `users_partial_update` y `users_destroy`**

| Campo | Valor |
|---|---|
| Horas | 2 |
| Artefactos | `apps/users/urls.py` |
| Dep. | ninguna |
| Criterio | `users_partial_update collision` y `users_destroy collision` no aparecen. |

Pasos:
1. Identificar la ruta legacy `users/{id}/` vs la ruta canónica `users/{user_id}/`.
2. Si la ruta legacy está en el router automático, añadir `basename` explícito o sobrescribir los `operation_id` con `@action(url_path=..., detail=True)`.
3. Alternativa: deprecar la ruta `{id}/` añadiendo `@extend_schema(deprecated=True, operation_id='users_legacy_update')`.
4. Commit: `fix(spectacular): DT-SPECTACULAR-004/005 — users URL collision resuelta`.

---

**F6-P0-T5 — Fix DT-SPECTACULAR-007: `PriorityEa7Enum` naming**

| Campo | Valor |
|---|---|
| Horas | 1 |
| Artefactos | `config/settings/spectacular.py` (o equivalente) |
| Dep. | ninguna |
| Criterio | El schema generado no contiene `PriorityEa7Enum`. Usa nombres explícitos. |

Pasos:
1. Identificar los modelos que tienen campo `priority` con choices (InternalMailbox, AlertRule, ExportJob, etc.).
2. Añadir en la configuración de drf-spectacular:
   ```python
   SPECTACULAR_SETTINGS = {
       'ENUM_NAME_OVERRIDES': {
           'MailboxPriorityEnum': 'apps.alerts.models.MAILBOX_PRIORITY_CHOICES',
           'AlertSeverityPriorityEnum': 'apps.alerts.models.ALERT_SEVERITY_CHOICES',
       }
   }
   ```
3. Commit: `fix(spectacular): DT-SPECTACULAR-007 — PriorityEa7Enum naming`.

---

**F6-P0-T6 — Implementar DT-REQUIRED-FUNCTION-001: test de regresión de `required_function`**

| Campo | Valor |
|---|---|
| Horas | 3 |
| Artefactos | `tests/unit/config/test_required_function_catalog.py` |
| Dep. | ninguna |
| Criterio | El test pasa en estado actual y falla si se añade una vista con un código inexistente. |

Pasos:
1. Crear `tests/unit/config/test_required_function_catalog.py`.
2. El test introspecciona todas las URLs de `config.urls`, extrae vistas con atributo `required_function`, y verifica que cada código existe en `Function.objects.values_list('code', flat=True)`.
3. El test también verifica que `required_function` sea una cadena no vacía (no `None`, no `''`).
4. Commit: `test(config): DT-REQUIRED-FUNCTION-001 — regresión required_function`.

---

**F6-P0-T7 — Añadir AUD-005 `view_general_audit` al catálogo**

| Campo | Valor |
|---|---|
| Horas | 1 |
| Artefactos | `apps/access/management/commands/create_functions.py` |
| Dep. | ninguna |
| Criterio | `Function.objects.filter(code='AUD-005').exists()` retorna `True` tras ejecutar `create_functions`. Catálogo = 74 funciones. |

Pasos:
1. Verificar que `AUD-004` existe y no hay `AUD-005` duplicado.
2. Añadir la entrada `('AUD-005', 'view_general_audit', 'MOD_AUD', 'Ver timeline general de auditoría cross-módulo (UC_AUD_01).')`.
3. Actualizar el total esperado de 73 a 74.
4. Commit: `feat(catalog): AUD-005 view_general_audit — UC_AUD_01 prerequisito`.

---

**F6-P0-T8 — Añadir `GENERAL_AUDIT_QUERIED` a `VALID_EVENT_TYPES`**

| Campo | Valor |
|---|---|
| Horas | 1 |
| Artefactos | `apps/audit/models.py` |
| Dep. | ninguna |
| Criterio | `'GENERAL_AUDIT_QUERIED' in VALID_EVENT_TYPES` retorna `True`. |

Pasos:
1. Añadir `'GENERAL_AUDIT_QUERIED'` al set `VALID_EVENT_TYPES` en `apps/audit/models.py`.
2. Ejecutar la verificación: `AuditLogService.emit('GENERAL_AUDIT_QUERIED', ...)` no lanza `AuditValidationError`.
3. Commit: `feat(audit): GENERAL_AUDIT_QUERIED en VALID_EVENT_TYPES — UC_AUD_01`.

---

**F6-P0-T9 — Verificación integral de Grupo P0**

| Campo | Valor |
|---|---|
| Horas | 1 |
| Artefactos | — (solo verificación, sin cambios de código) |
| Dep. | F6-P0-T1 a F6-P0-T8 |
| Criterio | `python manage.py spectacular --validate` sin warnings de colisión. `Function.objects.count() == 74`. `'GENERAL_AUDIT_QUERIED' in VALID_EVENT_TYPES`. Test de regresión `test_required_function_catalog.py` PASS. |

---

### GRUPO GA — Auth (paralelo con GB, GC)

Prerequisito: F6-P0-T9 completo.

---

**F6-GA-T1 — Leer corpus UC_AUTH_04 y mapear gaps**

| Campo | Valor |
|---|---|
| Horas | 1 |
| Artefactos | — (solo lectura y anotación) |
| Dep. | F6-P0-T9 |
| Criterio | Lista de CAs no cubiertos por los tests legacy documentada. Verificación de `ChangePasswordView.permission_classes` y throttle contra CAs del corpus. |

Pasos:
1. Leer `uc-auth-04/criterios-aceptacion.rst` completo (16 CAs).
2. Ejecutar los tests legacy `tests/integration/users/test_auth_viewset.py::TestAuthViewSetChangePassword` y anotar cuáles CAs faltan.
3. Verificar que `ChangePasswordView` no tiene `required_function` (CA-01 no requiere RBAC, solo `IsAuthenticated`). Correcto según corpus.
4. Registrar los gaps: CA-07 (brute force), CA-08 (scope upgrade), CA-09 (otras sesiones cerradas), CA-11 (atomicidad rollback), CA-12 (sin password en logs), CA-16 (BLOCKED puede cambiar).

---

**F6-GA-T2 — Tests TDD UC_AUTH_04: UT/IT fases Red**

| Campo | Valor |
|---|---|
| Horas | 3 |
| Artefactos | `tests/unit/authentication/test_change_password.py` (nuevo) |
| Dep. | F6-GA-T1 |
| Criterio | Archivo creado con tests que cubren CA-01..CA-16. Todos FAIL en estado Red. |

Pasos:
1. Crear `tests/unit/authentication/test_change_password.py`.
2. Escribir tests para: CA-01 flujo principal, CA-02 wrong_current, CA-03 política violada, CA-04 reuso, CA-05 same_as_current, CA-06 mismatch, CA-07 brute force 429, CA-08 scope_upgraded, CA-09 otras sesiones cerradas, CA-11 atomicidad, CA-12 sin password en logs, CA-13 sin password en audit payload, CA-16 BLOCKED puede cambiar.
3. Verificar que los que no están implementados fallan (Red).
4. Commit: `test(authentication+users+access+audit): UC_AUTH_04 — tests TDD Red phase (CA-01..16)`.

---

**F6-GA-T3 — Green: completar CAs faltantes de UC_AUTH_04**

| Campo | Valor |
|---|---|
| Horas | 4 |
| Artefactos | `apps/authentication/change_password_view.py` |
| Dep. | F6-GA-T2 |
| Criterio | `tests/unit/authentication/test_change_password.py` — 100 % PASS. Sin regresiones en suite existente. |

Pasos:
1. Implementar CA-07: throttle de 5 intentos fallidos en 5 min → 429 `TOO_MANY_ATTEMPTS` + `AuditEvent SUSPICIOUS_PASSWORD_CHANGE_ATTEMPTS`.
2. Verificar CA-08: `scope_upgraded` en el body cuando `first_login` era True.
3. Verificar CA-09: `CLOSE_OTHER_SESSIONS` setting — cerrar otras sesiones post-cambio exitoso.
4. Verificar CA-11: `transaction.atomic()` cubre User + PasswordHistory + Session-close.
5. Verificar CA-12: ningún `logger.xxx(password)` en el flujo.
6. Commit: `feat(auth): UC_AUTH_04 — CA-07/08/09/11 completos (Green phase)`.

---

**F6-GA-T4 — Tests TDD UC_AUTH_05: UT/IT Red**

| Campo | Valor |
|---|---|
| Horas | 2 |
| Artefactos | `tests/unit/authentication/test_session_management.py` (nuevo) |
| Dep. | F6-P0-T9 |
| Criterio | Tests cubren CA-01..12. Los gaps identificados fallan. |

Pasos:
1. Crear `tests/unit/authentication/test_session_management.py`.
2. Tests para: CA-01 listado paginado, CA-02 filtro user_id + `SESSIONS_VIEWED_FOR_USER`, CA-03 sin PII, CA-04 cierre individual + `SESSION_CLOSED`, CA-05 idempotencia `SESSION_CLOSE_NOOP`, CA-06 bulk close, CA-07 SELF_BULK_CLOSE_FORBIDDEN, CA-08 sin AUTH-004 → 403, CA-09 sin AUTH-002 → 403, CA-11 InternalMessage notificación, CA-12 solo sesiones del invocante.
3. Commit: `test(authentication+users+access+audit): UC_AUTH_05 — tests TDD Red phase (CA-01..12)`.

---

**F6-GA-T5 — Green: completar CAs faltantes de UC_AUTH_05**

| Campo | Valor |
|---|---|
| Horas | 3 |
| Artefactos | `apps/authentication/session_admin_view.py` |
| Dep. | F6-GA-T4 |
| Criterio | `tests/unit/authentication/test_session_management.py` — 100 % PASS. |

Pasos:
1. Verificar CA-02: filtro `?user_id` genera `AuditEvent SESSIONS_VIEWED_FOR_USER` con el user_id correcto en payload.
2. Verificar CA-11: cierre de sesión envía `InternalMessage` al usuario afectado vía `InternalMailbox`.
3. Verificar CA-12: endpoint `own/` retorna solo sesiones del invocante — no puede ver sesiones ajenas.
4. Commit: `feat(auth): UC_AUTH_05 — CA-02/11/12 completos (Green phase)`.

---

### GRUPO GB — Users (paralelo con GA, GC)

---

**F6-GB-T1 — Leer corpus UC_USR_02/03/04 y mapear gaps**

| Campo | Valor |
|---|---|
| Horas | 1 |
| Artefactos | — |
| Dep. | F6-P0-T9 |
| Criterio | Gaps documentados por CA para USR_02, USR_03, USR_04. `UserViewSet.required_function` verificado contra catálogo. |

Pasos:
1. Leer CAs de `uc-usr-02`, `uc-usr-03`, `uc-usr-04`.
2. Ejecutar tests legacy y anotar qué CAs no están cubiertos.
3. Verificar `required_function` de `UserViewSet`, `ModifyUserView`, `EliminateUserView`.
4. Verificar que `CNST-026` (sin PII en response de listado) está implementado en `UserListSerializer`.

---

**F6-GB-T2 — Tests TDD UC_USR_02: Red phase**

| Campo | Valor |
|---|---|
| Horas | 2 |
| Artefactos | `tests/unit/users/test_user_list_search.py` (nuevo) |
| Dep. | F6-GB-T1 |
| Criterio | Tests cubren CA-01..08. Los CAs que faltan están en rojo. |

Pasos:
1. Crear `tests/unit/users/test_user_list_search.py`.
2. Tests para: CA-01 paginación 50/página, CA-02 sin `email`/`full_name` en listado (CNST-026), CA-03 detalle con `username` sólo, CA-04 filtro `?state=ACTIVE`, CA-05 filtros sin SQLi (ordenamiento whitelist), CA-06 sin permiso `list_users` → 403, CA-07 cursor paginación estable, CA-08 timeout BD → 503.
3. Commit: `test(authentication+users+access+audit): UC_USR_02 — tests TDD Red phase`.

---

**F6-GB-T3 — Green: completar CAs faltantes de UC_USR_02**

| Campo | Valor |
|---|---|
| Horas | 3 |
| Artefactos | `apps/users/viewsets/user_viewset.py`, `apps/users/serializers/user_list_serializer.py` |
| Dep. | F6-GB-T2 |
| Criterio | `tests/unit/users/test_user_list_search.py` — 100 % PASS. |

Pasos:
1. Verificar CNST-026: `UserListSerializer` no expone `email`, `date_of_birth`, `phone`. Si lo hace, corregir.
2. Verificar whitelist de `ordering` — prevenir SQLi por parámetros de ordenamiento no controlados.
3. Verificar timeout handling: BD timeout → 503 `SERVICE_UNAVAILABLE`.
4. Commit: `feat(users): UC_USR_02 — CA-02/05/08 completos (Green phase)`.

---

**F6-GB-T4 — Tests TDD UC_USR_03/04: Red phase**

| Campo | Valor |
|---|---|
| Horas | 2 |
| Artefactos | `tests/unit/users/test_user_modify_eliminate.py` (nuevo) |
| Dep. | F6-GB-T1 |
| Criterio | Tests cubren CAs principales de USR_03 (CA-01..08) y USR_04 (CA-01..06). |

Pasos:
1. Crear `tests/unit/users/test_user_modify_eliminate.py`.
2. Tests USR_03: CA-01 PATCH parcial, CA-02 BLOCKED cierra Sessions + BlacklistedTokens, CA-04 SELF_STATE_CHANGE_FORBIDDEN, CA-05 state=ELIMINATED → 400, CA-08 transiciones inválidas → 409, CA-09 `USER_MODIFIED` AuditEvent con `fields_changed`.
3. Tests USR_04: CA-01 state=ELIMINATED + Assignments REVOKED + Sessions CLOSED, CA-02 BR-009 registro preservado, CA-03 SELF_ELIMINATION_FORBIDDEN, CA-06 idempotencia `USER_ELIMINATE_NOOP`.
4. Commit: `test(authentication+users+access+audit): UC_USR_03/04 — tests TDD Red phase`.

---

**F6-GB-T5 — Green: completar CAs faltantes de UC_USR_03/04**

| Campo | Valor |
|---|---|
| Horas | 3 |
| Artefactos | `apps/users/modify_user_view.py` |
| Dep. | F6-GB-T4 |
| Criterio | `tests/unit/users/test_user_modify_eliminate.py` — 100 % PASS. |

Pasos:
1. USR_03 CA-02: verificar que `BLOCKED` cierra Sessions activas + añade tokens a `BlacklistedToken`.
2. USR_03 CA-09: verificar que `USER_MODIFIED` audit incluye `payload.fields_changed` como lista de campos.
3. USR_04 CA-06: verificar idempotencia — si User ya es ELIMINATED, retornar 200 `USER_ELIMINATE_NOOP`.
4. Commit: `feat(users): UC_USR_03/04 — CAs faltantes completados (Green phase)`.

---

### GRUPO GC — Permissions (orden interno importa: PERM_07 primero)

---

**F6-GC-T1 — Leer corpus UC_PERM_07 y mapear gaps críticos**

| Campo | Valor |
|---|---|
| Horas | 1 |
| Artefactos | — |
| Dep. | F6-P0-T9 |
| Criterio | Gaps de CA-09/10/11/17 (caché + bulk) documentados con nivel de severidad. |

Pasos:
1. Leer los 17 CAs de `uc-perm-07`.
2. Ejecutar los 4 tests existentes en `test_effective_permissions_view.py` y mapear a CAs del corpus.
3. Identificar: CA-09 (caché TTL) y CA-10 (invalidación por evento) como gaps más graves — impactan corrección en producción.
4. Determinar si `EffectivePermissionsView` retorna actualmente campo `origin` en la respuesta (CA-01..04 lo requieren).

---

**F6-GC-T2 — Tests TDD UC_PERM_07: Red phase**

| Campo | Valor |
|---|---|
| Horas | 3 |
| Artefactos | `tests/unit/access/test_effective_permissions_engine.py` (nuevo) |
| Dep. | F6-GC-T1 |
| Criterio | Tests cubren CA-01..17. Los gaps identificados están en rojo. |

Pasos:
1. Crear `tests/unit/access/test_effective_permissions_engine.py`.
2. Tests para: CA-01 AGR otorga con `origin=GRANTED_BY_AGR`, CA-02 revocación excepcional gana con `origin=REVOKED_EXCEPTIONAL`, CA-03 concesión sin AGR `origin=GRANTED_EXCEPTIONAL`, CA-04 sin nada `origin=DENIED_NO_GRANT`, CA-05 AGR INACTIVE no cuenta, CA-06 Assignment expirado no cuenta, CA-07 concesión expirada no cuenta, CA-08 multi-AGR retorna lista, CA-09 cache hit (`cache=true`), CA-10 cache invalidate por evento, CA-11 bulk check 50 codes (1 query), CA-12 función no existe → 400, CA-15 fail-closed en BD timeout, CA-16 cero AuditEvents, CA-17 TTL ajustado por valid_until.
3. Commit: `test(authentication+users+access+audit): UC_PERM_07 — tests TDD Red phase (CA-01..17)`.

---

**F6-GC-T3 — Green UC_PERM_07: campo `origin` en response**

| Campo | Valor |
|---|---|
| Horas | 2 |
| Artefactos | `apps/access/views.py` (EffectivePermissionsView) o servicio equivalente |
| Dep. | F6-GC-T2 |
| Criterio | CA-01, CA-02, CA-03, CA-04 PASS: `origin` presente en respuesta. |

Pasos:
1. Modificar `EffectivePermissionsView.get()` para que retorne `origin` junto con `allowed`.
2. El cálculo de `origin` debe provenir de `calculate_effective_functions()` que ya tiene la lógica de precedencia.
3. Commit: `feat(permissions): UC_PERM_07 CA-01..04 — campo origin en response`.

---

**F6-GC-T4 — Green UC_PERM_07: caché TTL + invalidación (CA-09/10/17)**

| Campo | Valor |
|---|---|
| Horas | 4 |
| Artefactos | `apps/access/views.py` o `apps/access/permission_cache.py` (nuevo) |
| Dep. | F6-GC-T3 |
| Criterio | CA-09, CA-10, CA-17 PASS. `cache=True` en respuesta hit. Invalidación funciona. TTL respeta valid_until. |

Pasos:
1. Crear `apps/access/permission_cache.py` con `PermissionCache` usando Django cache backend.
2. `PermissionCache.get(user_id, function_code)` retorna `(result, hit)`.
3. `PermissionCache.set(user_id, function_code, result, ttl)` donde `ttl = min(DEFAULT_TTL, seconds_to_valid_until)`.
4. `PermissionCache.invalidate(user_id)` borra todas las entradas del usuario.
5. Conectar invalidación al signal `post_save` de `UserFunctionAssignment` y `ExceptionalPermission`.
6. Commit: `feat(permissions): UC_PERM_07 CA-09/10/17 — caché TTL + invalidación`.

---

**F6-GC-T5 — Green UC_PERM_07: bulk check optimizado (CA-11)**

| Campo | Valor |
|---|---|
| Horas | 2 |
| Artefactos | `apps/access/views.py` |
| Dep. | F6-GC-T4 |
| Criterio | CA-11 PASS: 50 códigos → 1 query a BD para misses (no N queries). |

Pasos:
1. Modificar el endpoint bulk para recibir `function_codes: []` en el body.
2. Separar los códigos en hits de caché y misses.
3. Para los misses, hacer una sola query `Function.objects.filter(code__in=misses)`.
4. Combinar resultados y retornar array de 50 elementos.
5. Commit: `feat(permissions): UC_PERM_07 CA-11 — bulk check optimizado (1 query)`.

---

**F6-GC-T6 — Tests TDD UC_PERM_05: Red phase**

| Campo | Valor |
|---|---|
| Horas | 2 |
| Artefactos | `tests/unit/access/test_access_group_management.py` (nuevo) |
| Dep. | F6-P0-T9 |
| Criterio | Tests para PERM_05 y PERM_06 cubren sus CAs. Los gaps están en rojo. |

Pasos:
1. Crear `tests/unit/access/test_access_group_management.py`.
2. Tests PERM_05: CA-01 crear AGR 201, CA-02 code duplicado 409, CA-03 code formato inválido 400, CA-04 is_predefined bloqueado, CA-07 PREDEFINED_NOT_MUTABLE al intentar editar un AGR predefinido, CA-09 AGR retirado no asignable 400, CA-10 sin `manage_access_groups` → 403.
3. Tests PERM_06: CA-01 add functions + COMPOSITION_CHANGED, CA-02 remove functions, CA-04 función ya en AGR idempotente (add duplicado → 200, no 409), CA-06 AGR PREDEFINED no editable → 403, CA-08 función inactiva → 400.
4. Commit: `test(authentication+users+access+audit): UC_PERM_05/06 — tests TDD Red phase`.

---

**F6-GC-T7 — Green: completar CAs faltantes de UC_PERM_05**

| Campo | Valor |
|---|---|
| Horas | 2 |
| Artefactos | `apps/access/access_group_view.py` |
| Dep. | F6-GC-T6 |
| Criterio | CAs de PERM_05 PASS. |

Pasos:
1. CA-02: verificar que `AccessGroupListCreateView.post()` retorna 409 cuando `code` ya existe (no 400).
2. CA-07: verificar que intento de PATCH/DELETE sobre `is_predefined=True` retorna 403 `PREDEFINED_NOT_MUTABLE`.
3. CA-09: verificar que `state=RETIRED` bloquea asignación (`AGRAssignView` verifica `state` del AGR).
4. Commit: `feat(permissions): UC_PERM_05 — CA-02/07/09 completos (Green phase)`.

---

**F6-GC-T8 — Green: completar CAs faltantes de UC_PERM_06**

| Campo | Valor |
|---|---|
| Horas | 2 |
| Artefactos | `apps/access/function_assign_view.py` (FunctionGroupFnView) |
| Dep. | F6-GC-T6 |
| Criterio | CAs de PERM_06 PASS. |

Pasos:
1. CA-04: verificar idempotencia de add — si la función ya está en el AGR, retornar 200 sin error.
2. CA-08: verificar que función con `state=INACTIVE` no puede añadirse → 400 `FUNCTION_INACTIVE`.
3. CA-06: verificar que AGRs `is_predefined=True` no pueden modificar su composición.
4. Commit: `feat(permissions): UC_PERM_06 — CA-04/06/08 completos (Green phase)`.

---

**F6-GC-T9 — Tests TDD UC_PERM_01/02: Red phase**

| Campo | Valor |
|---|---|
| Horas | 2 |
| Artefactos | `tests/unit/access/test_agr_assign_revoke_perm_view.py` (nuevo) |
| Dep. | F6-GC-T5 (PERM_07 completo — las vistas PERM dependen del motor) |
| Criterio | Tests para PERM_01 y PERM_02 cubren sus CAs adicionales. Los nuevos CAs están en rojo. |

Pasos:
1. Crear `tests/unit/access/test_agr_assign_revoke_perm_view.py`.
2. PERM_01 CAs adicionales (vs UC_ACC_04): preview de impacto SoD antes de confirmar la asignación, endpoint de confirmación explícita en dos pasos.
3. PERM_02 CAs adicionales: CA-PERM-01 (404 si AGR nunca fue asignado, no 400 — anti-info-leak por AGR nunca asignado).
4. Commit: `test(authentication+users+access+audit): UC_PERM_01/02 — tests TDD Red phase (CAs adicionales)`.

---

**F6-GC-T10 — Green: CAs adicionales de UC_PERM_01/02**

| Campo | Valor |
|---|---|
| Horas | 3 |
| Artefactos | `apps/access/function_assign_view.py` (AGRAssignView, AGRRevokeView) |
| Dep. | F6-GC-T9 |
| Criterio | `tests/unit/access/test_agr_assign_revoke_perm_view.py` — 100 % PASS. |

Pasos:
1. UC_PERM_01: añadir endpoint `GET /api/access/users/{id}/agr/{agr_id}/preview/` que retorna impacto SoD sin persistir.
2. UC_PERM_02 CA-PERM-01: en `AGRRevokeView`, si el `UserAccessGroupAssignment` no existe para ese par (user, agr), retornar 404 en lugar de 400. (Actualmente puede retornar un error genérico.)
3. Commit: `feat(permissions): UC_PERM_01/02 — CAs adicionales completados`.

---

**F6-GC-T11 — Tests TDD UC_PERM_08: Red phase**

| Campo | Valor |
|---|---|
| Horas | 2 |
| Artefactos | `tests/unit/authentication/test_dynamic_menu.py` (nuevo) |
| Dep. | F6-GC-T5 (PERM_07 completo — el menú depende del motor) |
| Criterio | Tests cubren CAs de PERM_08. Los gaps están en rojo. |

Pasos:
1. Crear `tests/unit/authentication/test_dynamic_menu.py`.
2. Tests: CA-01 menú con múltiples dominios, CA-02 User sin funciones → `domains: []`, CA-03 función REVOKED no aparece, CA-06 locale=es retorna labels en español, CA-07 locale=en retorna labels en inglés, CA-15 cero AuditEvents por invocación.
3. Commit: `test(authentication+users+access+audit): UC_PERM_08 — tests TDD Red phase`.

---

**F6-GC-T12 — Green: completar CAs faltantes de UC_PERM_08**

| Campo | Valor |
|---|---|
| Horas | 2 |
| Artefactos | `apps/authentication/menu_view.py` |
| Dep. | F6-GC-T11 |
| Criterio | `tests/unit/authentication/test_dynamic_menu.py` — 100 % PASS. |

Pasos:
1. CA-03: verificar que `MenuBuilder` llama a `EffectivePermissionsView` (via `calculate_effective_functions()`) para excluir funciones `REVOKED_EXCEPTIONAL`.
2. CA-06/07: verificar que `?locale=en` retorna labels en inglés y `?locale=es` en español, usando los campos de `MenuItem`.
3. CA-15: verificar que ningún `AuditLogService.emit()` se llama en el path de `MenuView.get()`.
4. Commit: `feat(permissions): UC_PERM_08 — CA-03/06/07/15 completos`.

---

### GRUPO GD — Audit (UC_AUD_01 — nuevo endpoint)

Prerequisito: F6-P0-T7 y F6-P0-T8 completos.

---

**F6-GD-T1 — Tests TDD UC_AUD_01: Red phase**

| Campo | Valor |
|---|---|
| Horas | 2 |
| Artefactos | `tests/unit/audit/test_general_audit_timeline.py` (nuevo) |
| Dep. | F6-P0-T7, F6-P0-T8 |
| Criterio | Tests cubren CA-01..08. Todos en rojo (endpoint no existe). |

Pasos:
1. Crear `tests/unit/audit/test_general_audit_timeline.py`.
2. Tests: CA-01 list básico timeline, CA-02 filtro `?module=MOD_AUTH`, CA-03 filtro `?actor_id=X`, CA-04 cursor paginación estable, CA-05 range > 90 días → 400, CA-06 meta-audit `GENERAL_AUDIT_QUERIED` obligatorio, CA-07 sin `view_general_audit` → 403, CA-08 BD timeout → 503.
3. Commit: `test(authentication+users+access+audit): UC_AUD_01 — tests TDD Red phase`.

---

**F6-GD-T2 — Green UC_AUD_01: implementar `GeneralAuditListView`**

| Campo | Valor |
|---|---|
| Horas | 3 |
| Artefactos | `apps/audit/audit_event_views.py`, `apps/audit/urls.py` |
| Dep. | F6-GD-T1 |
| Criterio | `tests/unit/audit/test_general_audit_timeline.py` — 100 % PASS. URL `audit:general-audit-list` registrada. |

Pasos:
1. Añadir `GeneralAuditListView(APIView)` con `required_function = 'AUD-005'`.
2. Soporte filtros: `?module=`, `?actor_id=`, `?date_from=`, `?date_to=`, `?page_size=`.
3. Implementar cursor (reutilizar `CursorEncoder` de `audit_query_service.py`).
4. Emitir `GENERAL_AUDIT_QUERIED` vía `AuditLogService.emit()` en cada llamada exitosa (CA-06).
5. Registrar `GET /api/audit/general/` en `audit/urls.py` con `name='general-audit-list'`.
6. Commit: `feat(audit): UC_AUD_01 — GeneralAuditListView AUD-005 (Green phase)`.

---

### GRUPO P1 — Verificación integral y hallazgos de FASE 6

---

**F6-P1-T1 — Ejecutar suite de verificación integral FASE 6**

| Campo | Valor |
|---|---|
| Horas | 2 |
| Artefactos | — (solo verificación) |
| Dep. | F6-GA-T5, F6-GB-T5, F6-GC-T12, F6-GD-T2 |
| Criterio | Todos los tests `tests/unit/` PASS. `python manage.py spectacular --validate` sin warnings de colisión. Catálogo = 74. 0 regresiones en tests existentes. |

---

**F6-P1-T2 — Commit de documentación: hallazgos FASE 6**

| Campo | Valor |
|---|---|
| Horas | 2 |
| Artefactos | `docs/revision/HALLAZGOS-FASE6-TDD-20260514.md` (nuevo) |
| Dep. | F6-P1-T1 |
| Criterio | Documento creado con: resumen de verificaciones PASS, hallazgos detectados en cada UC, decisiones de diseño tomadas. |

Commit: `docs(arch): HALLAZGOS-FASE6-TDD — deuda técnica drf-spectacular saldada + 12 UCs TDD canónico`.

---

## FASE 7 — App operator: estado de agente (sin integración PBX)

**Objetivo:** Implementar la gestión de estado del agente como recursos REST
puros, sin dependencias de telefonía. Cubre UC_OPR_01, UC_OPR_08, UC_OPR_09,
UC_OPR_10.
**Estimación total:** 10 días (20 tareas atómicas).
**Precondición:** FASE 6 completada. Decisión de arquitectura sobre SSE vs
polling tomada por el equipo.

---

### GRUPO P0 — Prerrequisitos FASE 7

---

**F7-P0-T1 — Crear app Django `operator`**

| Campo | Valor |
|---|---|
| Horas | 2 |
| Artefactos | `apps/operator/__init__.py`, `apps/operator/apps.py`, `apps/operator/models.py` (vacío), `apps/operator/urls.py`, config/settings agregado |
| Dep. | FASE 6 completa |
| Criterio | `python manage.py check` sin errores. App `operator` en `INSTALLED_APPS`. |

Pasos:
1. Crear estructura de directorios de la app.
2. Añadir `'apps.operator'` a `INSTALLED_APPS` en todos los settings activos.
3. Registrar `path('api/operator/', include('apps.operator.urls'))` en `config/urls.py`.
4. Commit: `feat(operator): crear app Django operator — scaffold`.

---

**F7-P0-T2 — Modelo `AgentSession` + migración inicial**

| Campo | Valor |
|---|---|
| Horas | 3 |
| Artefactos | `apps/operator/models.py`, migración `0001_initial.py` |
| Dep. | F7-P0-T1 |
| Criterio | `AgentSession` creado con todos los campos del corpus. `makemigrations` + `migrate` sin errores. |

Pasos:
1. Definir `AgentSession`:
   ```python
   class AgentSession(models.Model):
       STATE_AVAILABLE = 'available'
       STATE_BUSY      = 'busy'
       STATE_BREAK     = 'break'
       STATE_ACW       = 'acw'        # After Call Work
       STATE_TRAINING  = 'training'
       STATE_OFFLINE   = 'offline'
       # ... choices, agent FK a User, current_state, started_at,
       # last_transition_at, break_reason FK, inactivity_threshold_minutes
   ```
2. Definir `AgentStateTransition` (historial inmutable — CNST-025):
   ```python
   class AgentStateTransition(models.Model):
       agent_session, from_state, to_state, reason, duration_seconds, created_at
   ```
3. Definir `BreakReason` (catálogo):
   ```python
   class BreakReason(models.Model):
       code, label_es, label_en, max_minutes, is_active
   ```
4. Definir validez de transiciones como constante de clase (máquina de estados).
5. Commit: `feat(operator): AgentSession + AgentStateTransition + BreakReason — migración 0001`.

---

**F7-P0-T3 — Añadir event types de operador a `VALID_EVENT_TYPES`**

| Campo | Valor |
|---|---|
| Horas | 1 |
| Artefactos | `apps/audit/models.py` |
| Dep. | F7-P0-T1 |
| Criterio | `AGENT_STATE_CHANGED`, `AGENT_BREAK_STARTED`, `AGENT_ACW_STARTED`, `AGENT_LOGGED_OUT`, `AGENT_FORCED_OFFLINE` en `VALID_EVENT_TYPES`. |

---

**F7-P0-T4 — Añadir funciones de operador al catálogo**

| Campo | Valor |
|---|---|
| Horas | 1 |
| Artefactos | `apps/access/management/commands/create_functions.py` |
| Dep. | F7-P0-T3 |
| Criterio | `OPR-001 manage_own_agent_state`, `OPR-002 force_agent_offline` en catálogo. Total = 76 funciones. |

---

### GRUPO GA — UC_OPR_01: gestión de estado de agente

---

**F7-GA-T1 — Tests TDD UC_OPR_01: Red phase**

| Campo | Valor |
|---|---|
| Horas | 3 |
| Artefactos | `tests/unit/operator/test_agent_state_transitions.py` (nuevo) |
| Dep. | F7-P0-T4 |
| Criterio | Tests cubren CA-01..10. Todos en rojo (endpoint no existe). |

Pasos:
1. Crear `tests/unit/operator/test_agent_state_transitions.py`.
2. Tests: CA-01 transición valid (available→break con reason), CA-04 break sin reason → 400, CA-05 transición inválida (offline→ACW) → 409, CA-06 audit `AGENT_STATE_CHANGED` con from/to/duration, CA-08 logout fuerza offline, CA-09 inactividad → offline (mock timer), CA-10 break exceeded → 409.

---

**F7-GA-T2 — Servicio `AgentStateService`**

| Campo | Valor |
|---|---|
| Horas | 4 |
| Artefactos | `apps/operator/agent_state_service.py` (nuevo) |
| Dep. | F7-P0-T4 |
| Criterio | Unit tests del servicio PASS. `AgentStateService.transition()` valida, registra en historial, emite audit. |

Pasos:
1. Implementar `AgentStateService.transition(agent_session, new_state, reason=None, invoker=None)`.
2. Validar la transición contra `VALID_TRANSITIONS` (máquina de estados definida en el modelo).
3. Calcular `duration_seconds` desde `last_transition_at`.
4. Crear `AgentStateTransition` (inmutable, no UPDATE).
5. Emitir `AGENT_STATE_CHANGED` vía `AuditLogService.emit()`.
6. `BREAK_REASON` requerido para `break` y `training`.
7. Commit: `feat(operator): AgentStateService — transiciones validadas + audit`.

---

**F7-GA-T3 — Vista `AgentStateView` (UC_OPR_01)**

| Campo | Valor |
|---|---|
| Horas | 2 |
| Artefactos | `apps/operator/views.py` (nuevo), `apps/operator/urls.py` |
| Dep. | F7-GA-T2 |
| Criterio | `POST /api/operator/me/state/` registrado. CA-01..10 de UC_OPR_01 PASS. |

Pasos:
1. Crear `AgentStateView(APIView)` con `required_function = 'OPR-001'`.
2. `POST` con `{new_state, reason, break_reason_id}`.
3. Crear `AgentSession` si no existe para el usuario.
4. Delegar a `AgentStateService.transition()`.
5. Registrar URL `POST /api/operator/me/state/`.
6. Commit: `feat(operator): UC_OPR_01 — AgentStateView + AgentStateService (Green phase)`.

---

**F7-GA-T4 — Inactividad automática: task periódica**

| Campo | Valor |
|---|---|
| Horas | 3 |
| Artefactos | `apps/operator/tasks.py` (nuevo), configuración APScheduler |
| Dep. | F7-GA-T3 |
| Criterio | CA-09 PASS: agente inactivo N minutos → transición forzada a offline. Test usa mock de tiempo. |

Pasos:
1. Crear `check_agent_inactivity()` como job de APScheduler (no Celery, CNST-004).
2. El job corre cada minuto: `AgentSession.objects.filter(current_state__in=['available','break'], last_transition_at__lt=threshold)`.
3. Llama a `AgentStateService.transition(..., new_state='offline', invoker=None)` con contexto `reason='INACTIVITY_TIMEOUT'`.
4. Emite `AGENT_FORCED_OFFLINE`.
5. Commit: `feat(operator): UC_OPR_01 CA-09 — inactividad automática (APScheduler job)`.

---

### GRUPO GB — UC_OPR_08/09/10: ACW, Break, Logout

---

**F7-GB-T1 — Tests TDD UC_OPR_08/09/10: Red phase**

| Campo | Valor |
|---|---|
| Horas | 2 |
| Artefactos | `tests/unit/operator/test_agent_acw_break_logout.py` (nuevo) |
| Dep. | F7-GA-T3 |
| Criterio | Tests cubren CAs de UC_OPR_08 (ACW), UC_OPR_09 (Break), UC_OPR_10 (Logout). |

Pasos:
1. Tests UC_OPR_08 (ACW): transición automática a ACW al colgar, `max_acw_minutes` configurable, timeout → available.
2. Tests UC_OPR_09 (Break): `BreakReason` requerido, `max_minutes` respetado, exceeded → 409.
3. Tests UC_OPR_10 (Logout): `state=OFFLINE`, `AgentSession.ended_at` registrado, audit `AGENT_LOGGED_OUT`.

---

**F7-GB-T2 — Green UC_OPR_08/09/10**

| Campo | Valor |
|---|---|
| Horas | 3 |
| Artefactos | `apps/operator/agent_state_service.py`, `apps/operator/views.py` |
| Dep. | F7-GB-T1 |
| Criterio | `tests/unit/operator/test_agent_acw_break_logout.py` — 100 % PASS. |

Pasos:
1. UC_OPR_08: registrar `ACW_STARTED` audit. Configurar `max_acw_minutes` en `AgentSession`. APScheduler job para timeout de ACW.
2. UC_OPR_09: implementar validación `BreakReason.max_minutes` — si se excede, `BREAK_EXCEEDED` → 409.
3. UC_OPR_10: `DELETE /api/operator/me/session/` — transición a OFFLINE + `AgentSession.ended_at`.
4. Commit: `feat(operator): UC_OPR_08/09/10 — ACW + Break + Logout (Green phase)`.

---

### GRUPO P1 — Verificación integral FASE 7

---

**F7-P1-T1 — Verificación integral FASE 7**

| Campo | Valor |
|---|---|
| Horas | 2 |
| Artefactos | — |
| Dep. | F7-GA-T4, F7-GB-T2 |
| Criterio | `tests/unit/` PASS. Migraciones aplican limpiamente. drf-spectacular sin colisiones nuevas. |

---

**F7-P1-T2 — Hallazgos FASE 7**

| Campo | Valor |
|---|---|
| Horas | 2 |
| Artefactos | `docs/revision/HALLAZGOS-FASE7-TDD-20260514.md` |
| Dep. | F7-P1-T1 |
| Criterio | Documento creado. Commit firmado. |

---

## FASE 8 — Supervision: broadcast + correcciones cross-repo

**Objetivo:** Implementar UC_SUP_03 (Broadcast a agentes — REST puro, sin PBX).
Documentar los ítems pendientes en IACT-docs y IACT-ui.
**Estimación total:** 6 días (10 tareas atómicas).
**Precondición:** FASE 7 completa.

> UC_SUP_01 (Silent monitor) y UC_SUP_02 (Barge) quedan excluidos de FASE 8
> porque requieren acceso al call leg SIP. Se documentan como bloqueados.

---

### GRUPO GA — UC_SUP_03: Broadcast a agentes

---

**F8-GA-T1 — Tests TDD UC_SUP_03: Red phase**

| Campo | Valor |
|---|---|
| Horas | 2 |
| Artefactos | `tests/unit/operator/test_agent_broadcast.py` (nuevo) |
| Dep. | FASE 7 completa |
| Criterio | Tests cubren CA-01..05. Todos en rojo. |

Pasos:
1. Crear `tests/unit/__init__.py` y `tests/unit/operator/test_agent_broadcast.py`.
2. Tests: CA-01 broadcast básico → `InternalMessage` entregado a receptores, CA-02 cross-segmento → 403, CA-03 `recipients` vacío → 400, CA-04 urgente → priority=critical en `InternalMessage`, CA-05 `BROADCAST_SENT` AuditEvent con count de receptores.

---

**F8-GA-T2 — Implementar `BroadcastView` (UC_SUP_03)**

| Campo | Valor |
|---|---|
| Horas | 3 |
| Artefactos | `apps/operator/broadcast_views.py` (nuevo), `apps/operator/urls.py` |
| Dep. | F8-GA-T1 |
| Criterio | `POST /api/operator/broadcast/` registrado. CA-01..05 PASS. |

Pasos:
1. `BroadcastView` con `required_function = 'OPR-003'` (`broadcast_to_agents`).
2. Añadir `OPR-003` al catálogo (P-8-T1 previo si no existe).
3. Recibe `{message, recipients: [user_id, ...], priority}`.
4. Valida que todos los `user_id` están en el segmento del invoker.
5. Por cada receptor, llama a `InternalMailbox.deliver_message()`.
6. Emite `BROADCAST_SENT` con `recipient_count`.
7. Commit: `feat(operator): UC_SUP_03 — BroadcastView (Green phase)`.

---

### GRUPO GB — Documentación cross-repo y cierre

---

**F8-GB-T1 — Documentar UCs bloqueados UC_SUP_01/02 y UC_OPR_02..07**

| Campo | Valor |
|---|---|
| Horas | 1 |
| Artefactos | `docs/revision/BLOQUEADOS-PBX-20260514.md` (nuevo) |
| Dep. | F8-GA-T2 |
| Criterio | Documento creado con: lista de UCs bloqueados, dependencia técnica requerida, decisión arquitectónica necesaria. |

---

**F8-GB-T2 — Instrucciones para commit pendiente en IACT-docs (H-M-001)**

| Campo | Valor |
|---|---|
| Horas | 1 |
| Artefactos | `docs/revision/INSTRUCCIONES-IACT-DOCS-H-M-001.md` (nuevo) |
| Dep. | ninguna (puede hacerse en paralelo) |
| Criterio | Documento con comandos exactos de git para commitear los 4 archivos pendientes en IACT-docs. |

Contenido del documento:
```bash
# Ejecutar en el repositorio IACT-docs
git checkout develop
git add source/normativa/restricciones/cnst-030-reglas-de-separacion-de-funciones-sod.rst
git add source/normativa/restricciones/cnst-033-vocabulario-unificado-rbac.rst
git add source/arquitectura-tecnica/rbac/modelo-rbac-iact.rst
git add source/normativa/gobernanza/adr-gob-009-rbac-modelo-conceptual.rst
git commit -m "docs(normativa): STD-008 FASES 4-5 — CNST-033 v2.0.0 + CNST-030 v3.0.0 + modelo v5.4.0 + ADR-GOB-009 v2.0.0"
```

---

**F8-GB-T3 — Instrucciones para merge IACT-ui (STD-008)**

| Campo | Valor |
|---|---|
| Horas | 1 |
| Artefactos | `docs/revision/INSTRUCCIONES-IACT-UI-STD008.md` (nuevo) |
| Dep. | ninguna |
| Criterio | Documento con checklist de verificación pre-merge y comando de merge. |

---

**F8-P1-T1 — Verificación integral FASE 8**

| Campo | Valor |
|---|---|
| Horas | 2 |
| Artefactos | — |
| Dep. | F8-GA-T2, F8-GB-T1, F8-GB-T2, F8-GB-T3 |
| Criterio | `tests/unit/` PASS. drf-spectacular sin colisiones. Cobertura corpus: 70 UCs TDD canónico (87.5 %). |

---

**F8-P1-T2 — Hallazgos FASE 8 y cierre del plan v5**

| Campo | Valor |
|---|---|
| Horas | 2 |
| Artefactos | `docs/revision/HALLAZGOS-FASE8-TDD-20260514.md`, actualizar `ANALISIS-GAPS-POST-PLAN-TDD-v4-20260513.md` con estado final |
| Dep. | F8-P1-T1 |
| Criterio | Documento de hallazgos creado. Estado de cada UC actualizado en el análisis de gaps. Commit final del plan. |

---

## Resumen del plan v5.0.0

### Métricas globales

| FASE | Tareas | Horas | UCs cubiertos | Deuda saldada |
|---|---|---|---|---|
| FASE 6 | 23 | 63h | 13 (12 IMPL + UC_AUD_01) | DT-SPECTACULAR-001..007, DT-REQUIRED-FUNCTION-001 |
| FASE 7 | 12 | 30h | 4 (UC_OPR_01/08/09/10) | — |
| FASE 8 | 8 | 13h | 1 (UC_SUP_03) | H-M-001 (docs), STD-008 IACT-ui |
| **Total** | **43** | **106h** | **18** | todas las DT activas |

### Cobertura al finalizar el plan v5

```
Al completar FASE 8:
  70 UCs con TDD canónico  (87.5 % del corpus)
   0 deuda técnica drf-spectacular activa
   0 vistas con required_function incorrecto (test de regresión activo)
  10 UCs bloqueados por PBX (UC_OPR_02..07, UC_SUP_01/02, UC_CLI_01..05)
   4 UCs sin corpus definido (UC_RPT_05/06, UC_ACC_06/07)
```

### Grafo de dependencias críticas

```
F6-P0 (prerrequisitos) ──── F6-GA (auth)
       │                └── F6-GB (users)
       │                └── F6-GC-T1..T5 (PERM_07) ─── F6-GC-T9..T12 (PERM_01/02/08)
       │                └── F6-GD (AUD_01)
       └────────────────────────────────────── F6-P1 (verificación)
                                                    │
                                                F7-P0 ─── F7-GA (OPR_01) ─── F7-GB (OPR_08/09/10)
                                                               │
                                                           F7-P1 ─── F8-GA (SUP_03) ─── F8-P1
```

### Bloqueadores externos (sin acción posible en IACT-api)

| Bloqueador | Acción requerida | Responsable |
|---|---|---|
| UC_CLI_01..05 | Decisión arquitectónica PBX + contrato de webhooks con vendor IVR | Arquitectura / negocio |
| UC_OPR_02..07 | Integración `TelephonyClient` SIP — definición de interfaz | Arquitectura |
| UC_SUP_01/02 | Acceso a call leg SIP activo — misma dependencia que UC_OPR_02..07 | Arquitectura |
| UC_RPT_05/06 | Definición de requisitos de negocio | Product |
| UC_ACC_06/07 | Definición de requisitos de negocio | Product |
| H-M-001 IACT-docs | Ejecutar commit descrito en F8-GB-T2 | Coatl / equipo |
| STD-008 IACT-ui | Merge de `claude/project-analysis-N9IkV` en `develop` | Coatl / equipo |
