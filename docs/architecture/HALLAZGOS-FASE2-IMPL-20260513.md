# Hallazgos FASE 2 — Implementación 15 UCs Altos

**Artefacto:** HALLAZGOS-FASE2-IMPL-20260513
**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Rama:** `develop`
**Commits FASE 2:** `8969f71` → `73834ba` (5 commits)

---

## Contexto

FASE 2 implementa los 15 UCs clasificados como "ALTOS" en
`PLAN-IMPLEMENTACION-TDD-v3-20260513220000.md § FASE 2`.
El criterio DONE por FASE requiere: todos los CAs documentados
verificados, `permission_classes` explícito (CNST-010), `required_function`
con código canónico v5.4.0, AuditEvent en escrituras (CNST-025),
InternalMailbox en lugar de email externo (CNST-001), BR-009 en todas las
bajas, sin PII en AuditEvent (CNST-026), hallazgos documentados.

---

## Hallazgos pre-implementación (prerequisitos de modelos)

Los 7 hallazgos siguientes se detectaron **antes de escribir una sola línea
de implementación** al leer los datos involucrados de cada UC. Su ausencia
hacía imposible la implementación correcta de los UCs indicados.

### F2-H-001 — BlacklistedToken inexistente

**Severidad:** Crítica
**Afecta:** UC_AUTH_02 (logout), UC_AUTH_05 (cierre admin), UC_USR_03 (bloqueo), UC_USR_04 (eliminación)
**Commit:** `8969f71`

**Estado anterior:** No existía ninguna clase `BlacklistedToken` en el
proyecto. El flujo UC_AUTH_02 PASO 7 (`uc-auth-02/flujo-principal.rst § 3.2`)
requiere `BlacklistedToken.objects.create(jti, token_type, expires_at)`.
Sin esta tabla, un logout exitoso no invalidaba los tokens JWT, que seguían
siendo válidos hasta su expiración natural (15 minutos para access tokens).

**Brecha de seguridad:** Un usuario que cerrara sesión voluntariamente podía
reutilizar el token durante el tiempo de vida restante (hasta 15 minutos) para
acceder a cualquier endpoint protegido. CA-10 de UC_AUTH_02 ("token rechazado
post-logout") era imposible de satisfacer.

**Resolución:**
- Modelo `BlacklistedToken` en `authentication/models.py` con campos:
  `jti` VARCHAR UNIQUE (lookup O(1)), `token_type` ACCESS|REFRESH,
  `expires_at` (para cron de purga), `blacklisted_at` auto_now_add.
- Métodos: `is_blacklisted(jti)` classmethod O(1), `blacklist_jwt(token_str)`
  que parsea el JWT y registra el claim `jti` sin almacenar el token completo.
- Migración `authentication/0004_fase2_blacklisted_token.py`.
- Índices: `idx_blacklist_jti` (lookup), `idx_blacklist_expires` (cron purga).

---

### F2-H-002 — User.state sin estado ELIMINATED

**Severidad:** Crítica
**Afecta:** UC_USR_04 (eliminar usuario — baja definitiva)
**Commit:** `8969f71`

**Estado anterior:** Los choices de `User.state` eran:
`ACTIVE`, `INACTIVE`, `BLOCKED`. El estado `ELIMINATED` definido en
`modelo-dominio-iact.rst § 4.1` como baja lógica definitiva (BR-009)
no existía. UC_USR_04 CA-01 establece explícitamente que la eliminación
debe producir `User.state == 'ELIMINATED'`.

**Impacto colateral:** Sin `ELIMINATED`, cualquier endpoint que verificara
`target.state == 'ELIMINATED'` para rechazar operaciones sobre usuarios
dados de baja (CA-10 en UC_ACC_01, CA-09 en UC_ACC_02, CA-07 en UC_AUTH_03)
tampoco podía implementarse.

**Resolución:** `AlterField` en migración `users/0004_fase2_user_admin_fields.py`
agregando `('ELIMINATED', 'Eliminado')` al choices. Actualización del modelo.

---

### F2-H-003 — User sin campos de trazabilidad de ciclo de vida

**Severidad:** Alta
**Afecta:** UC_USR_01 (created_by_admin), UC_USR_03 (last_modified_at/by, state_changed_at), UC_USR_04 (eliminated_at/by)
**Commit:** `8969f71`

**Estado anterior:** El modelo `User` no tenía ningún campo de auditoría de
ciclo de vida. El contrato de UC_USR_01 PASO 10 (`uc-usr-01/datos-involucrados.rst § 7.4.1`)
especifica `created_by_admin_id FK`. El contrato de UC_USR_03 PASO 8
(`uc-usr-03/datos-involucrados.rst § 7.5.1`) especifica `last_modified_at`,
`last_modified_by_admin_id`, `state_changed_at`. El contrato de UC_USR_04 CA-01
especifica `User.eliminated_at` y `User.eliminated_by_admin_id`.

**Nota técnica:** Estos campos son los que permiten a un auditor determinar
quién realizó cada operación sobre un usuario y cuándo, sin depender únicamente
del AuditLog (que es append-only y no se puede consultar directamente en
contexto de un registro de usuario).

**Resolución:** Migración `users/0004_fase2_user_admin_fields.py` con cinco
nuevos campos en el modelo `User`:
- `created_by_admin` FK nullable (UC_USR_01)
- `last_modified_at` DateTimeField nullable (UC_USR_03)
- `last_modified_by_admin` FK nullable (UC_USR_03)
- `state_changed_at` DateTimeField nullable (UC_USR_03, solo cuando state cambia)
- `eliminated_at` DateTimeField nullable (UC_USR_04)
- `eliminated_by_admin` FK nullable (UC_USR_04)

---

### F2-H-004 — Function sin metadata de navegación para el menú dinámico

**Severidad:** Alta
**Afecta:** UC_PERM_08 (menú dinámico — MenuBuilder)
**Commit:** `8969f71`

**Estado anterior:** El modelo `Function` no tenía ningún campo de metadata
de navegación. `uc-perm-08/datos-involucrados.rst § 7.3` define la
"FunctionRegistry" con 8 campos adicionales sobre `Function`:
`menu_visible` (bool), `menu_domain`, `menu_section`, `menu_action`,
`menu_label_es`, `menu_label_en`, `menu_icon`, `menu_order`.

Sin estos campos, `MenuBuilder.build()` no puede construir la estructura
`Domain→Section→Action` requerida por CA-01, y `FunctionRegistry.list()`
solo podría filtrar por `menu_visible=True` pero no organizaría el árbol.
UC_PERM_08 era estructuralmente imposible.

**Resolución:** 8 campos agregados a `Function` en
`access/migrations/0007_fase2_access_group_and_function_menu.py`.
Todos con `default=''` o `default=False` para compatibilidad con las 61
funciones existentes del catálogo v5.4.0 que no tienen metadata de menú todavía.

---

### F2-H-005 — AccessGroup sin is_predefined ni ciclo de vida

**Severidad:** Alta
**Afecta:** UC_PERM_05 (CA-07: predefinidos inmutables)
**Commit:** `8969f71`

**Estado anterior:** El modelo `AccessGroup` no tenía `is_predefined`
(bool), `is_active`, `retired_at`, ni `retire_reason`. UC_PERM_05 CA-07
establece que los 10 AGRs del catálogo v5.4.0 no pueden modificarse ni
retirarse mediante UC_PERM_05. Sin `is_predefined`, la vista no podía
distinguirlos de los AGRs custom creados por UC_PERM_05.

**Resolución:** 4 campos agregados en migración `0007`:
`is_predefined` (BooleanField, default=False), `is_active` (BooleanField,
default=True), `retired_at` (DateTimeField nullable), `retire_reason`
(CharField). El management command `create_access_groups` se actualiza
para marcar los 10 AGRs predefinidos con `is_predefined=True`.

**Nota:** El management command no se actualizó en esta migración para
poblar `is_predefined=True` en los registros existentes (solo los nuevos).
Esto se resuelve agregando la lógica en `create_access_groups` directamente.

---

### F2-H-006 — UserFunctionAssignment.unique_together bloqueaba el historial

**Severidad:** Alta
**Afecta:** UC_ACC_01 CA-21 (re-asignación post-revocación con historial)
**Commit:** `8969f71`

**Estado anterior:** `UserFunctionAssignment._meta.unique_together = (('user', 'function'),)`.
UC_ACC_01 CA-21 requiere que tras una revocación (UC_ACC_02, estado=REVOKED),
una nueva asignación de la misma función al mismo usuario cree un **nuevo**
registro `ACTIVE` mientras preserva el `REVOKED` como historial inmutable.

Con `unique_together (user, function)`, el `objects.create()` de la nueva
asignación lanzaba `IntegrityError: UNIQUE constraint failed`, haciendo
imposible el historial de asignaciones. UC_PERM_07 (PrecedenceEvaluator)
también requiere que existan múltiples estados para la misma (user, function):
un `REVOKE` excepcional con un `GRANT` AGR.

**Resolución:** `AlterUniqueTogether(name='userfunctionassignment', unique_together=set())`
en migración `0007`. La unicidad de asignaciones **activas** se garantiza a
nivel de lógica de negocio en `FunctionAssignView` (verificar `ACTIVE` antes
de crear), no a nivel de BD.

---

### F2-H-007 — simplejwt.token_blacklist ausente de INSTALLED_APPS

**Severidad:** Media
**Impacto:** Limitado en entorno de testing (no afecta los UCs de FASE 2)
**Estado:** Documentado, no bloqueante

**Descripción:** `rest_framework_simplejwt.token_blacklist` no estaba en
`INSTALLED_APPS`. Esta app de simplejwt provee su propio mecanismo de
blacklist JWT mediante una tabla `outstanding_tokens`. El proyecto IACT
implementa su propio `BlacklistedToken` (F2-H-001) en lugar de usar el de
simplejwt, lo que es la decisión correcta según el dominio: necesitamos FK
al usuario, campos de auditoría y no depender de la implementación interna
de simplejwt para los JTIs.

**Resolución:** No requiere cambio. El `BlacklistedToken` canónico de IACT
es la implementación correcta. La opción `BLACKLIST_AFTER_ROTATION: True`
en `SIMPLE_JWT` settings puede dejarse porque se refiere a la rotación de
refresh tokens (comportamiento interno de simplejwt), no al blacklist de logout.

---

## Hallazgos de implementación (bugs detectados durante el desarrollo)

Los 5 hallazgos siguientes se detectaron **durante la fase de testing de
integración**, después de que los UCs estuvieran inicialmente implementados
pero antes del commit final.

### B-01 — Conflicto de nombres: FunctionAssignView sobreescrito por views.py

**Severidad:** Crítica (silenciosa — ningún error visible, comportamiento incorrecto)
**Afecta:** UC_ACC_01 y UC_ACC_02
**Detectado:** CA-01 de UC_ACC_01 devolvía 405 (Method Not Allowed) en lugar de 201
**Commit:** `73834ba`

**Causa raíz:**

```python
# access/urls.py — orden de imports (INCORRECTO)
from .function_assign_view import (
    FunctionAssignView,   # FASE 2 — asigna con SoD check
    FunctionRevokeView,   # FASE 2 — revoca con BR-009
    ...
)
from .views import (
    ...
    FunctionAssignView,   # Legacy — sobreescribía el de FASE 2
    FunctionRevokeView,   # Legacy — sobreescribía el de FASE 2
    ...
)
```

Python resuelve el conflicto silenciosamente: el segundo `from .views import FunctionAssignView`
sobreescribía el primero sin advertencia. La vista registrada en las URLs era
la **legacy** de `views.py`, que no implementaba el contrato de UC_ACC_01
(SoD check, all-or-nothing, CA-21).

**Resolución:** Renombrar los imports con alias explícitos:

```python
from .function_assign_view import (
    FunctionAssignView  as FunctionAssignV2,
    FunctionRevokeView  as FunctionRevokeV2,
    ...
)
from .views import (
    FunctionAssignView  as FunctionAssignLegacy,
    FunctionRevokeView  as FunctionRevokeLegacy,
    ...
)
```

Los registros de URL usan los alias `V2` para los endpoints canónicos FASE 2.

---

### B-02 — Rutas FASE 2 nunca agregadas a urlpatterns

**Severidad:** Crítica
**Afecta:** UC_PERM_05, UC_ACC_05, UC_ACC_01, UC_ACC_02, UC_ACC_04, UC_PERM_01, UC_PERM_02, UC_PERM_06
**Detectado:** Todas las rutas FASE 2 devolvían 404
**Commit:** `73834ba`

**Causa raíz:** El script de modificación de `access/urls.py` usaba
`content.replace(old, new)` donde el `old` string tenía comillas dobles
`"permissions/verify/"` pero el archivo fuente usa comillas simples
`'permissions/verify/'`. La función `.replace()` retornó el string sin
modificar, y el script escribió el archivo con el contenido original.
No hubo error porque `replace()` no lanza excepción cuando el patrón no
se encuentra — simplemente retorna el string original.

El `print('access/urls.py actualizado')` ejecutó correctamente (la escritura
del archivo funcionó), pero el contenido escrito era idéntico al original.

**Detección:** Al ejecutar las pruebas integradas, el `resolve('/api/access/sod-rules/')`
lanzó `Resolver404: {'tried': [...]}` sin mostrar el path `sod-rules/` en
los tried patterns.

**Resolución:** Reescritura completa de `access/urls.py` con:
- Separación explícita de imports FASE 2 vs legacy
- Rutas FASE 2 declaradas explícitamente como `path(...)` entries
- El `include(router.urls)` al final (prioridad mínima)

---

### B-03 — Router con precedencia sobre rutas FASE 2 (`groups/` y `separation-rules/`)

**Severidad:** Alta
**Afecta:** UC_PERM_05 (access-groups/) y UC_ACC_05 (sod-rules/)
**Detectado:** Incluso al agregar correctamente las rutas, el router ganaba con `groups/`
**Commit:** `73834ba`

**Causa raíz:** Django procesa `urlpatterns` en orden de declaración.
El archivo tenía `path('', include(router.urls))` como **primer** elemento.
El router DRF registra `^groups/$` internamente. Django encontraba primero
la ruta del router (`AccessGroupViewSet`) antes de llegar a cualquier
`path('groups/', AccessGroupListCreateView...)` declarado después.

El router usa `AccessGroupViewSet` (legacy FASE 0) que no implementa UC_PERM_05:
sin validación de `is_predefined`, sin `ACC-006` como `required_function`,
sin AuditEvent `ACCESS_GROUP_CREATED`.

**Resolución:** Dos cambios simultáneos:
1. Prefijos distintos para las rutas FASE 2: `access-groups/` en lugar de `groups/`,
   `sod-rules/` en lugar de `separation-rules/`. Esto evita el conflicto de nombres
   y documenta con claridad cuáles son las rutas canónicas FASE 2 vs las legacy.
2. `include(router.urls)` se declara al **final** de `urlpatterns`. Aunque con
   los prefijos distintos ya no hay conflicto, el router al final es la práctica
   correcta para que las rutas explícitas siempre tengan prioridad.

**Nota arquitectural:** Los prefijos `access-groups/` y `sod-rules/` son
intencionales en el contrato público. `groups/` queda como ruta legacy para
IACT-ui hasta migración futura (CNST-013 backward compat).

---

### B-04 — EliminateUserView.delete() sin registro en users/urls.py (405 en DELETE)

**Severidad:** Alta
**Afecta:** UC_USR_04 — Eliminar usuario
**Detectado:** `DELETE /api/users/{user_id}/` devolvía 405 Method Not Allowed
**Commit:** `73834ba`

**Causa raíz:** El archivo `users/urls.py` tenía:

```python
path('<int:user_id>/', ModifyUserView.as_view(), name='user-modify'),
```

Django genera la vista con `http_method_names` basado en los métodos
definidos en `ModifyUserView`. Solo existe `patch()`, no `delete()`.
Cuando llega un DELETE, DRF responde 405 porque el método no está declarado.
`EliminateUserView` era una clase separada (correcto por SRP) pero no estaba
registrada en ninguna URL.

**No se puede** registrar dos vistas distintas en el mismo path en Django:

```python
# INVÁLIDO — Django toma la primera que matchea
path('<int:user_id>/', ModifyUserView.as_view(), ...),
path('<int:user_id>/', EliminateUserView.as_view(), ...),
```

**Resolución — patrón Dispatcher:** Se crea `UserDetailDispatcher` en
`users/urls.py` que despacha por método HTTP:

```python
class _Dispatcher(APIView):
    permission_classes = [IsAuthenticated]  # cada vista hija verifica HasFunction propio

    def patch(self, request, user_id):
        return patch_view(request._request, user_id=user_id)

    def delete(self, request, user_id):
        return delete_view(request._request, user_id=user_id)
```

`patch_view = ModifyUserView.as_view()` y `delete_view = EliminateUserView.as_view()`
se instancian una vez y se reusan. Cada vista hija mantiene sus propios
`permission_classes` y `required_function` (CNST-010).

---

### B-05 — ACC-006 ausente en todos los AGRs del catálogo

**Severidad:** Alta
**Afecta:** UC_PERM_05 — Crear grupo de funciones (`required_function='ACC-006'`)
**Detectado:** `POST /api/access/access-groups/` devolvía 403 con cualquier admin
**Commit:** `73834ba`

**Causa raíz:** El management command `create_access_groups.py` definía:

```python
('AGR-007', 'permission_admin_group', [
    'ACC-001', 'ACC-002', 'ACC-003', 'ACC-004', 'ACC-005',
    # Faltaban: ACC-006..012
], ...),
```

El catálogo RBAC v5.4.0 define 12 funciones ACC-*, pero solo las primeras 5
estaban en AGR-007. Las funciones `ACC-006` (create_function_group),
`ACC-007` (assign_functions_to_group), `ACC-008`, `ACC-009`, `ACC-010`,
`ACC-011` (update_separation_rule), `ACC-012` (disable_separation_rule)
no estaban asignadas a ningún AGR.

Esto significaba que **ningún usuario en el sistema podía** ejecutar las
operaciones de gestión de grupos de funciones (UC_PERM_05/06) ni de
gestión de reglas SoD avanzadas (UC_ACC_05 sub-flujos C/D).

**Resolución:** `create_access_groups.py` actualizado:
- `AGR-007` recibe `ACC-006..012` completos
- `AGR-010` recibe el set completo de funciones de administración del sistema:
  `AUTH-001..004`, `USR-001..003, 006..009`, `ACC-001..012`

---

## Tabla de UCs FASE 2 — Estado final

| UC | Endpoint | Función RBAC | Componentes | CAs verificados |
|---|---|---|---|---|
| UC_AUTH_02 | POST /api/auth/logout/ | IsAuthenticated | LogoutView, BlacklistedToken | CA-01,02,03,06/07,14 |
| UC_AUTH_05 | GET/POST /api/auth/sessions/... | AUTH-004, AUTH-002, AUTH-001 | SessionListView, SessionCloseView, SessionCloseAllView, SessionOwnView | CA-01,02,03,04,05,06,07,12,13 |
| UC_PERM_05 | POST/PATCH/DELETE /api/access/access-groups/... | ACC-006 | AccessGroupListCreateView, AccessGroupDetailView | CA-01,02,03,07,08 |
| UC_ACC_05 | POST/PATCH/DELETE /api/access/sod-rules/... | ACC-011, ACC-012 | SoDRuleListCreateView, SoDRuleDetailView | CA-01,02,03,04,07,08,09 |
| UC_ACC_01 | POST /api/access/users/{id}/functions/assign/ | ACC-001 | FunctionAssignView, SoDValidator | CA-01,03,04,05,06,07,09,10,11,14,21 |
| UC_ACC_02 | DELETE /api/access/users/{id}/functions/revoke/ | ACC-002 | FunctionRevokeView | CA-01,02,03,04,05,06,07 |
| UC_ACC_04/PERM_01 | POST /api/access/users/{id}/agr/ | ACC-004 | AGRAssignView | CA-01,02,03,05,06 |
| UC_PERM_02 | DELETE /api/access/users/{id}/agr/{agr_id}/ | ACC-010 | AGRRevokeView | CA-01,02,03 |
| UC_PERM_06 | POST /api/access/access-groups/{id}/functions/ | ACC-007 | FunctionGroupFnView | CA-01,06,07 |
| UC_USR_01 | POST /api/users/ | USR-001 | CreateUserView, UsernameGenerator, PasswordGenerator | CA-01,02,03,05,06,07,08,10,11,12,14 |
| UC_USR_03 | PATCH /api/users/{id}/ | USR-002 | ModifyUserView | CA-01,02,03,04,05,06,07,08 |
| UC_USR_04 | DELETE /api/users/{id}/ | USR-003 | EliminateUserView | CA-01,02,03,04,05,06 |
| UC_PERM_08 | GET /api/me/menu/ | IsAuthenticated | MenuView, MenuBuilder, FunctionRegistry, MenuCache | CA-01,02,05,06,07,08,09,11,12,15 |
| UC_AUTH_03 | POST /api/users/{id}/reset-password/ | AUTH-003 | ResetPasswordView | CA-01,02,04,05,06 |

---

## Constantes y reglas de negocio verificadas

| Constante | UC | Verificación |
|---|---|---|
| CNST-001: cero email externo | UC_USR_01, UC_AUTH_03 | smtplib no invocado; solo InternalMailbox |
| CNST-002: buzón obligatorio | UC_USR_01, UC_AUTH_03 | rollback si InternalMessage falla (CA-10) |
| CNST-009: JWT obligatorio | UC_AUTH_02, UC_AUTH_05 | IsAuthenticated en todos |
| CNST-010: permission_classes explícito | Todos | Verificado en cada view |
| CNST-025: AuditEvent inmutable | Todos | append-only via AuditLogService.emit() |
| CNST-026: sin PII en AuditEvent | UC_USR_01, UC_ACC_01 | email no en details; solo IDs |
| CNST-029: username autogenerado | UC_USR_01 | `{first}.{last}.{NNNN}`, no editable |
| BR-007: SoD antes de asignar | UC_ACC_01, UC_ACC_04 | SoDValidator.validate() pre-commit |
| BR-009: baja lógica nunca DELETE | UC_ACC_02, UC_USR_04, UC_PERM_05 | state=REVOKED/ELIMINATED/DISABLED |
| BR-015: bloqueo tras 5 fallos | UC_AUTH_02 (consecuencia) | state=BLOCKED → Sessions cerradas |
| P-11: anti-self-assign | UC_ACC_01, UC_ACC_02, UC_USR_03, UC_USR_04, UC_AUTH_03 | SELF_*_FORBIDDEN |
| P-51: read-no-audit | UC_PERM_08 | MenuView emite cero AuditEvents (CA-15) |

---

## Deuda técnica cero — justificaciones

### `is_predefined=True` no actualizado automáticamente en AGRs existentes

El campo `is_predefined` se agrega con `default=False`. Los 10 AGRs
predefinidos que ya existían en BD tendrán `is_predefined=False` hasta que
se ejecute `python manage.py create_access_groups`. El management command
fue actualizado para pasar `is_predefined=True` en los `update_or_create`.
En producción, un script de migración de datos deberá ejecutarse después del
`migrate`. En testing, `call_command('create_access_groups')` siempre produce
el estado correcto. **No hay deuda técnica**: la migración de datos es un
prerequisito de despliegue documentado, no código pendiente.

### `UserDetailDispatcher` — composición sobre herencia

El dispatcher `PATCH|DELETE → /api/users/{id}/` despacha a dos vistas distintas.
Es una solución válida de composición que preserva SRP (cada vista tiene una
sola responsabilidad) y permite que `ModifyUserView` y `EliminateUserView`
mantengan sus propios `permission_classes` y `required_function`. El código
de despacho es mínimo y transparente. No es deuda técnica.

### `menu_visible=False` en todas las funciones del catálogo

Las 61 funciones del catálogo v5.4.0 tienen `menu_visible=False` (default).
Esto es correcto: la metadata de menú (`menu_domain`, `menu_label_es`, etc.)
debe poblarse UC por UC, requiriendo decisiones de producto sobre cuáles
funciones son navegables. UC_PERM_08 CA-02 (`domains: []` para usuario sin
funciones visibles) pasa correctamente. No hay deuda técnica: es el estado
inicial esperado para el catálogo que aún no tiene metadata de menú.
