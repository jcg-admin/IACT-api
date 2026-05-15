# Hallazgos FASE 6 TDD — 2026-05-14

**Artefacto:** HALLAZGOS-FASE6-TDD-20260514
**Versión:** 1.0.0
**Fecha:** 2026-05-14
**Base:** `develop` @ `d650ca0` (inicio FASE 6) → `69eb43b` (cierre FASE 6)
**Suite:** 66/66 PASS — 0 colisiones drf-spectacular — 0 PriorityEa7Enum

----

## Resumen ejecutivo

FASE 6 cerró con éxito todos los grupos de tareas del plan TDD v5.1.0.

| Grupo | UCs cubiertos | Tests | Estado |
|---|---|---|---|
| P0 — Prerrequisitos | Infraestructura | 8 tareas atómicas | COMPLETO |
| GA — Authentication | UC_AUTH_04, UC_AUTH_05 | 18 tests | 18/18 PASS |
| GB — Users | UC_USR_02, UC_USR_03, UC_USR_04 | 22 tests | 22/22 PASS |
| GC — Access/Permissions | UC_PERM_07, UC_PERM_05/06, UC_PERM_01/02, UC_PERM_08 | 16 tests | 16/16 PASS |
| GD — Audit | UC_AUD_01 (nuevo endpoint) | 5 tests | 5/5 PASS |
| Config | Naming + required_function | 5 tests | 5/5 PASS |

**Hallazgos detectados:** 8 (3 críticos, 3 medios, 2 bajos).
**Deuda técnica saldada:** DT-SPECTACULAR-001..007, DT-NAMING-001, DT-REQUIRED-FUNCTION-001.

----

## Hallazgo H-F6-GRP-GC-001 — CRÍTICO

**ID:** H-F6-GRP-GC-001
**Severidad:** Crítica
**Componente:** `apps/access/views.py` — `EffectivePermissionsView`
**Estado:** RESUELTO en commit `69eb43b`

### Descripción

`EffectivePermissionsView` filtraba `ExceptionalPermission` con
`status='approved'` (estado del sistema legacy, anterior a FASE 4).
Desde FASE 4, el campo usa `ExceptionalPermission.STATE_ACTIVE = 'ACTIVE'`.

### Impacto en producción

Toda concesión o revocación de permiso excepcional era invisible para el
motor de permisos efectivos. `calculate_effective_functions()` nunca incluía
permisos excepcionales ni respetaba revocaciones excepcionales. Los usuarios
con permisos concedidos mediante `ExceptionalPermission` en estado `ACTIVE`
actuaban como si nunca hubieran recibido esa concesión.

### Causa raíz

La FASE 4 renombró el campo `status` de los valores `approved/rejected/pending`
a `ACTIVE/REVOKED/EXPIRED` sin actualizar `EffectivePermissionsView`, que fue
implementada antes y no tenía tests TDD canónicos que lo detectaran.

### Corrección

```python
# Antes (incorrecto)
ExceptionalPermission.objects.filter(
    user=user, status='approved',
    valid_from__lte=now, valid_until__gte=now
)

# Después (correcto)
ExceptionalPermission.objects.filter(
    user=user,
    status=ExceptionalPermission.STATE_ACTIVE,  # 'ACTIVE'
    expires_at__gt=now,
)
```

Además, la vista fue completamente reescrita para implementar el algoritmo de
precedencia correcto (CA-01..04 de UC_PERM_07): la revocación excepcional tiene
prioridad sobre cualquier concesión vía AGR.

----

## Hallazgo H-F6-GRP-GC-002 — Medio

**ID:** H-F6-GRP-GC-002
**Severidad:** Media
**Componente:** `apps/access/function_assign_view.py` — `AGRRevokeView`
**Estado:** RESUELTO en commit `69eb43b`

### Descripción

`AGRRevokeView.delete()` devolvía HTTP 200 con `{'noop': True}` cuando el AGR
nunca había sido asignado al usuario. El corpus UC_PERM_02 CA-PERM-01 exige
HTTP 404 con error `AGR_NOT_ASSIGNED`.

### Impacto

Un invocante que intentaba revocar un AGR nunca asignado recibía una respuesta
exitosa (200) y no podía distinguir entre una revocación real y una no-op de
datos incorrectos.

### Corrección

```python
if not membership:
    return Response(
        {'error': 'AGR_NOT_ASSIGNED',
         'detail': 'El AGR no está asignado al usuario.'},
        status=404,
    )
```

----

## Hallazgo H-F6-GRP-GC-003 — Medio

**ID:** H-F6-GRP-GC-003
**Severidad:** Media
**Componente:** `apps/access/function_assign_view.py` — `FunctionGroupFnView`
**Estado:** RESUELTO en commit `69eb43b`

### Descripción

`FunctionGroupFnView` tenía tres omisiones respecto al corpus UC_PERM_06:

1. **Sin `change_reason`** (CA-09): el serializer no incluía el campo
   `change_reason` obligatorio para trazabilidad de cambios de composición.

2. **Sin `COMPOSITION_CHANGED` audit** (CA-01): el endpoint no emitía
   ningún `AuditEvent` al añadir funciones a un AGR.

3. **Sin check de AGR RETIRED** (CA-07): permitía añadir funciones a un AGR
   en estado `RETIRED` (`is_active=False`).

### Corrección

El serializer `GroupFnSerializer` fue extendido con `change_reason: CharField`.
El método `post()` fue reescrito para verificar el estado del AGR, emitir
`COMPOSITION_CHANGED` con el payload correcto, y devolver la respuesta con
`functions_added` y `functions_skipped`.

----

## Hallazgo H-F6-GRP-GB-001 — Medio

**ID:** H-F6-GRP-GB-001
**Severidad:** Media
**Componente:** `apps/users/urls.py`
**Estado:** RESUELTO en commit `69eb43b`

### Descripción

El patrón `path('', CreateUserView.as_view(), name='user-create')` era el
primer elemento de `urlpatterns` en `apps/users/urls.py`. Al ser el más
específico que coincide con la ruta vacía `''`, interceptaba **todas** las
solicitudes a `/api/users/` incluyendo `GET`, devolviendo HTTP 405
(Method Not Allowed) para el listado de usuarios.

El router de `UserViewSet` que registraba `GET /api/users/` (list) nunca
era alcanzado.

### Impacto

`GET /api/users/` era inaccesible para listado. Cualquier cliente que
usara el endpoint canónico de listado recibía 405.

### Corrección

Se reordenó `urlpatterns` para que `include(router.urls)` preceda a
`CreateUserView`. La vista `CreateUserView` se movió a `/api/users/create/`
(alias adicional). El `UserDetailDispatcher` se delegó correctamente para
`PATCH`, `DELETE`, y `GET` al `UserViewSet.retrieve` del router.

----

## Hallazgo H-F6-GRP-P0-003 — Bajo

**ID:** H-F6-GRP-P0-003
**Severidad:** Baja
**Componente:** `tests/mocks/service_mocks.py`
**Estado:** RESUELTO en commit `69eb43b`

### Descripción

El archivo `tests/mocks/service_mocks.py` estaba ausente del repositorio.
El módulo `tests/mocks/__init__.py` intentaba importarlo, causando
`ModuleNotFoundError` que bloqueaba la ejecución de pytest para todos los
tests de FASE 6 (que usan pytest, no DiscoverRunner).

Este archivo fue la cuarta ocurrencia de DT-GITIGNORE-001 (archivos de tests
excluidos del repositorio).

### Resolución

Se reconstruyó `service_mocks.py` con stubs funcionales que implementan el
contrato del `__init__.py` (13 fixtures). Los stubs usan `MagicMock` y
`unittest.mock.patch` en lugar de la implementación original (desconocida).

----

## Hallazgo H-F6-GRP-P0-004 — Bajo

**ID:** H-F6-GRP-P0-004
**Severidad:** Baja
**Componente:** `apps/access/views.py` — `UserFunctionAssignView`, `UserFunctionRevokeView`
**Estado:** RESUELTO en commit `69eb43b`

### Descripción

Dos vistas tenían `required_function = "access.assign_functions"` — un
string del sistema de permisos legacy de Django, no un código del catálogo
IACT. Esto causaba que el test de regresión DT-REQUIRED-FUNCTION-001 las
detectara como inválidas.

Estas dos vistas son distintas de `FunctionAssignView` y `FunctionRevokeView`
(que ya usan los códigos correctos `ACC-001` y `ACC-002`).

### Corrección

```python
# UserFunctionAssignView
required_function = 'ACC-001'  # assign_functions

# UserFunctionRevokeView
required_function = 'ACC-002'  # revoke_functions
```

----

## Hallazgo H-F6-GRP-GD-001 — Bajo

**ID:** H-F6-GRP-GD-001
**Severidad:** Baja
**Componente:** `apps/audit/models.py` — `AuditLog`
**Estado:** DOCUMENTADO (sin corrección de modelo)

### Descripción

El modelo `AuditLog` no tiene campo `module`. Los filtros de
`GeneralAuditListView` para `?module=` utilizan el campo `resource` como
aproximación (`resource__icontains=module`).

El corpus UC_AUD_01 define el filtro `?module=MOD_AUTH|MOD_ACC|...` como
discriminador de módulo. La implementación actual usa `resource` como proxy,
lo que puede generar falsos positivos si el campo `resource` contiene
valores no relacionados con el módulo.

### Decisión

El modelo `AuditLog` fue diseñado en FASE 0 y añadir un campo `module`
requeriría migración. Dado que la FASE 6 no incluye migraciones de modelos
existentes, se documenta como DT-SCHEMA-001 para una tarea dedicada.

----

## Deuda técnica saldada en FASE 6

| DT | Descripción | Resolución |
|---|---|---|
| DT-SPECTACULAR-001 | Colisión `audit_event_export` | `AuditLegacyExportView` con `@extend_schema_view(post=operation_id='audit_export_legacy')` |
| DT-SPECTACULAR-002 | Colisión `access_access_groups_retrieve` | `@extend_schema_view` con `operation_id` explícito en list y detail |
| DT-SPECTACULAR-003 | Colisión `auth_change_password_create` | `@extend_schema(operation_id='auth_viewset_change_password_legacy', deprecated=True)` |
| DT-SPECTACULAR-004/005 | Colisiones `users_partial_update/destroy` | `@extend_schema_view` en `UserDetailDispatcher._Dispatcher` |
| DT-SPECTACULAR-007 | `PriorityEa7Enum` | `ENUM_NAME_OVERRIDES` + unificación de choices en `MailboxMessage` |
| DT-NAMING-001 | 41 violaciones naming en tests (fase0..5, test_uc_*, test_models.py) | Remediación commit `d178bfc` + test regresión `test_naming_convention.py` |
| DT-REQUIRED-FUNCTION-001 | Vistas con `required_function` inválido | Test regresión + fix `UserFunctionAssignView/RevokeView` |

## Deuda técnica nueva identificada

| DT | Descripción | Severidad | Próximo paso |
|---|---|---|---|
| DT-SPECTACULAR-006 | 34 vistas sin `serializer_class` (unable to guess serializer) | Baja | Tarea dedicada de refactorización `APIView` → `GenericAPIView` |
| DT-SCHEMA-001 | `AuditLog` sin campo `module` — filtro de UC_AUD_01 usa `resource` como proxy | Media | Migración dedicada con campo `module` en `AuditLog` |
| DT-GITIGNORE-001 | `service_mocks.py` ausente — cuarta recurrencia | Cerrado | Reconstruido con stubs; revisar `.gitignore` para evitar reincidencia |

----

## Verificación de cierre

```
Suite al cierre de FASE 6 (develop @ 69eb43b):

  Tests nuevos FASE 6:      66 PASS  |  0 FAIL
  0 colisiones drf-spectacular
  0 PriorityEa7Enum en schema
  0 archivos con nombres que violan §2 (test_naming_convention.py)
  0 vistas con required_function inválido (test_required_function_catalog.py)
  74 funciones en catálogo (incluyendo AUD-005 view_general_audit)

Cobertura post-FASE 6:
  UCs con TDD canónico:  69/80  (86.2 %)
  UCs IMPL sin TDD:      0      (saldado completamente)
  UC_AUD_01:             implementado (GeneralAuditListView / AUD-005)
  UCs bloqueados por PBX: 10    (UC_OPR_02..07, UC_SUP_01/02, UC_CLI_01..05)
  UCs sin corpus:         4     (UC_RPT_05/06, UC_ACC_06/07)
```
