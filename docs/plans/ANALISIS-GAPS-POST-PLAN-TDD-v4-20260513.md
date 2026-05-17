# Análisis de Gaps — Post Plan TDD v4

**Artefacto:** ANALISIS-GAPS-POST-PLAN-TDD-v4-20260513
**Versión:** 1.0.0
**Fecha:** 2026-05-14
**Base:** `develop` @ `cb235f3` — Plan TDD v4 completado (54/54 PASS)
**Autores:** Equipo IACT / Claude Sonnet 4.6
**Estado:** Borrador — pendiente aprobación

----

## 1. Propósito

El plan TDD v4 cerró con éxito sus cinco fases (FASES 0–5), cubriendo 56 UCs
del corpus IACT-docs. Este análisis mapea de forma exhaustiva los UCs que
**siguen sin cobertura TDD canónica** y la deuda técnica acumulada, clasificados
por naturaleza y esfuerzo estimado. El objetivo es proveer una base objetiva
para planificar el siguiente ciclo de trabajo.

----

## 2. Inventario de cobertura — corpus completo

El corpus IACT-docs contiene **80 UCs** distribuidos en 12 módulos. El siguiente
inventario indica el estado de cada UC en el repositorio `IACT-api @ develop`.

### Leyenda

| Símbolo | Significado |
|---|---|
| ✅ TDD | Implementado + tests TDD canónicos + hallazgos documentados |
| ⚠️ IMPL | Implementado, tests legacy, sin cobertura TDD canónica |
| ❌ PENDIENTE | Sin implementación Django |
| 🚫 FUERA DE SCOPE | Requiere infraestructura externa no HTTP (PBX, WebSocket) |

### 2.1 Módulo auth

| UC | Descripción | Estado | Evidencia |
|---|---|---|---|
| UC_AUTH_01 | Login / JWT | ✅ TDD | FASE 1 `test_uc_auth_01_login.py` |
| UC_AUTH_02 | Logout / BlacklistedToken | ✅ TDD | FASE 2 `test_uc_auth_02_logout.py` |
| UC_AUTH_03 | Recuperar contraseña | ✅ TDD | FASE 4 `test_uc_auth_03.py` |
| UC_AUTH_04 | Cambiar contraseña | ⚠️ IMPL | `ChangePasswordView` (commit 552ceae FASE 1). Tests legacy en `tests/integration/users/test_auth_viewset.py`. Sin `tests/unit/fase*/test_uc_auth_04.py`. |
| UC_AUTH_05 | Gestionar sesiones | ⚠️ IMPL | `SessionAdminView` 4 endpoints (commit df814b7 FASE 2). Tests legacy en `test_session_viewset.py`. Sin `tests/unit/fase*/test_uc_auth_05.py`. |

### 2.2 Módulo users

| UC | Descripción | Estado | Evidencia |
|---|---|---|---|
| UC_USR_01 | Crear usuario | ✅ TDD | FASE 2, commit 73834ba |
| UC_USR_02 | Listar / Buscar usuarios | ⚠️ IMPL | `UserViewSet` en `viewsets/user_viewset.py`. Tests en `tests/integration/users/test_user_viewset.py`. Sin `tests/unit/fase*/test_uc_usr_02.py`. |
| UC_USR_03 | Modificar usuario | ⚠️ IMPL | `ModifyUserView` en `modify_user_view.py` (commit 73834ba). Sin test TDD canónico. |
| UC_USR_04 | Eliminar usuario | ⚠️ IMPL | `EliminateUserView` en `modify_user_view.py` (commit 73834ba). Sin test TDD canónico. |

### 2.3 Módulo access

| UC | Descripción | Estado | Evidencia |
|---|---|---|---|
| UC_ACC_01 | Asignar funciones | ✅ TDD | `FunctionAssignView` FASE 2 |
| UC_ACC_02 | Revocar funciones | ✅ TDD | `FunctionRevokeView` FASE 2 |
| UC_ACC_03 | Verificar permisos | ✅ TDD | `PermissionVerifyView` FASE 2 |
| UC_ACC_04 | Asignar AGR | ✅ TDD | `AGRAssignView` FASE 2 |
| UC_ACC_05 | Gestionar reglas SoD | ✅ TDD | `SeparationRuleListCreateView` FASE 2 / STD-008 |
| UC_ACC_08 | Permiso temporal excepcional | ✅ TDD | FASE 4 `test_uc_acc08_perm03_perm04.py` |
| UC_ACC_09 | Auditar cambios de acceso | ✅ TDD | FASE 5 `test_uc_acc09_aud02_aud03.py` |

> **Ausentes del corpus:** UC_ACC_06, UC_ACC_07 — no existen archivos en
> `casos-uso/access/`. Se desconoce si fueron planificados y nunca documentados
> o reservados para una versión futura. No bloquean.

### 2.4 Módulo permissions

| UC | Descripción | Estado | Evidencia |
|---|---|---|---|
| UC_PERM_01 | Vista PERM: asignación AGR | ⚠️ IMPL | Hereda `AGRAssignView` (FASE 2). Los CAs adicionales de la vista PERM (preview de impacto, confirmación dos pasos) no están implementados como endpoints separados. |
| UC_PERM_02 | Vista PERM: revocación AGR | ⚠️ IMPL | Hereda `AGRRevokeView` (FASE 2). CAs específicos PERM sin implementar. |
| UC_PERM_03 | Preview permiso excepcional | ✅ TDD | `ExceptionalPreviewView` FASE 4 |
| UC_PERM_04 | Revocar permiso excepcional | ✅ TDD | `ExceptionalRevokeView` FASE 4 |
| UC_PERM_05 | Gestionar AccessGroups (CRUD) | ⚠️ IMPL | `AccessGroupListCreateView` (commit 73834ba FASE 2). Tests en `test_access_group_viewset.py` pero sin `tests/unit/fase*/test_uc_perm_05.py`. |
| UC_PERM_06 | Gestionar composición de AGR | ⚠️ IMPL | `FunctionGroupFnView` (commit 73834ba FASE 2). Sin test TDD canónico. |
| UC_PERM_07 | Motor de permisos efectivos | ⚠️ IMPL | `EffectivePermissionsView` en `access/views.py`. Tests en `test_effective_permissions_view.py` (4 tests, sin estructura FASE). |
| UC_PERM_08 | Menú dinámico | ⚠️ IMPL | `MenuView` en `authentication/menu_view.py` (commit 73834ba). Sin test TDD canónico. |
| UC_PERM_09 | Servicio de auditoría | ✅ TDD | FASE 5 `test_uc_perm09_perm10.py` |
| UC_PERM_10 | Consultar auditoría | ✅ TDD | FASE 5 `test_uc_perm09_perm10.py` |

### 2.5 Módulo alerts

| UC | Descripción | Estado | Evidencia |
|---|---|---|---|
| UC_ALR_01 | Configurar umbrales | ✅ TDD | FASE 3 `test_uc_alr_01_02_03.py` |
| UC_ALR_02 | Ver alertas activas | ✅ TDD | FASE 3 |
| UC_ALR_03 | Reconocer alerta | ✅ TDD | FASE 3 |
| UC_ALR_04 | Ver historial de alertas | ✅ TDD | FASE 4 `test_uc_alr_04.py` |
| UC_ALR_05 | Gestionar suscripciones | ✅ TDD | FASE 4 `test_uc_log_04_alr05_aud04.py` |

### 2.6 Módulo audit

| UC | Descripción | Estado | Evidencia |
|---|---|---|---|
| UC_AUD_01 | Listado general de auditoría (timeline) | ❌ PENDIENTE | No existe endpoint `GET /api/audit/events/?module=...` con `view_general_audit`. `UC_PERM_10` cubre `view_audit_log` pero es un scope distinto (permisos vs todo). Ver §4.1. |
| UC_AUD_02 | Buscar en auditoría | ✅ TDD | FASE 5 `test_uc_acc09_aud02_aud03.py` |
| UC_AUD_03 | Exportar auditoría | ✅ TDD | FASE 5 |
| UC_AUD_04 | Reporte de compliance | ✅ TDD | FASE 4 `test_uc_log_04_alr05_aud04.py` |

### 2.7 Módulo logs

| UC | Descripción | Estado | Evidencia |
|---|---|---|---|
| UC_LOG_01 | Ver logs de aplicación | ✅ TDD | FASE 3 `test_uc_log_01_02.py` |
| UC_LOG_02 | Ver logs ETL | ✅ TDD | FASE 3 |
| UC_LOG_03 | Buscar logs | ✅ TDD | FASE 5 `test_uc_log03_06_07_rpt09_10.py` |
| UC_LOG_04 | Exportar logs | ✅ TDD | FASE 4 |
| UC_LOG_05 | Ver logs de infraestructura | ✅ TDD | FASE 4 |
| UC_LOG_06 | Ver estado del sistema | ✅ TDD | FASE 5 |
| UC_LOG_07 | Ver métricas técnicas | ✅ TDD | FASE 5 |

### 2.8 Módulo pipeline

| UC | Descripción | Estado | Evidencia |
|---|---|---|---|
| UC_PIP_01 | Ver estado del pipeline ETL | ✅ TDD | FASE 3 |
| UC_PIP_02 | Consultar errores ETL | ✅ TDD | FASE 3 |
| UC_PIP_03 | Consultar disponibilidad de datos | ✅ TDD | FASE 3 |
| UC_PIP_04 | Reintento de pipeline | ✅ TDD | FASE 3 `test_uc_pip_04_retry.py` |

### 2.9 Módulo reports

| UC | Descripción | Estado | Evidencia |
|---|---|---|---|
| UC_RPT_01 | Ver dashboard de KPIs | ✅ TDD | FASE 1 |
| UC_RPT_02 | Ver dashboard de segmento | ✅ TDD | FASE 1 |
| UC_RPT_03 | Ver reportes históricos | ✅ TDD | FASE 3 |
| UC_RPT_04 | Exportar reportes | ✅ TDD | FASE 3 |
| UC_RPT_05 | — | — | **Ausente del corpus.** No existe directorio en `casos-uso/reports/`. |
| UC_RPT_06 | — | — | **Ausente del corpus.** No existe directorio en `casos-uso/reports/`. |
| UC_RPT_07 | Programar reporte | ✅ TDD | FASE 4 |
| UC_RPT_08 | Ver reportes programados | ✅ TDD | FASE 4 |
| UC_RPT_09 | Configurar filtros guardados | ✅ TDD | FASE 5 |
| UC_RPT_10 | Guardar vista | ✅ TDD | FASE 5 |
| UC_RPT_11 | Compartir reporte | ✅ TDD | FASE 4 |
| UC_RPT_12 | Reportes de agentes | ✅ TDD | FASE 4 |
| UC_RPT_13 | Reportes de colas | ✅ TDD | FASE 4 |
| UC_RPT_14 | Reportes de campañas | ✅ TDD | FASE 4 |
| UC_RPT_15 | Reportes de transferencias IVR | ✅ TDD | FASE 4 |
| UC_RPT_16 | Reportes de menús IVR | ✅ TDD | FASE 4 |
| UC_RPT_17 | Reportes de clientes únicos | ✅ TDD | FASE 4 |

### 2.10 Módulo caller (UCs IVR — sin interfaz HTTP)

| UC | Descripción | Estado | Infraestructura requerida |
|---|---|---|---|
| UC_CLI_01 | Recepción de llamada entrante | 🚫 FUERA DE SCOPE | TelephonyClient (PBX/SIP trunk), IVRRunner, protocolo DTMF |
| UC_CLI_02 | Navegación IVR (DTMF) | 🚫 FUERA DE SCOPE | IVRRunner, IVRDefinition, audio/TTS engine |
| UC_CLI_03 | Transferencia de llamada | 🚫 FUERA DE SCOPE | TelephonyClient, CallRouter |
| UC_CLI_04 | Cola de espera | 🚫 FUERA DE SCOPE | QueueManager, music-on-hold service |
| UC_CLI_05 | Colgado de llamada | 🚫 FUERA DE SCOPE | TelephonyClient, CallRouter |

**Nota:** Estos UCs no tienen interfaz HTTP REST. Son flujos de media plane que
dependen del PBX/SIP y del motor IVR. La API Django es irrelevante para este
scope. Si IACT-api va a interactuar con IVR, será como receptor de webhooks o
como proveedor de configuración, no como ejecutor del flujo. Requiere decisión
arquitectónica antes de planificar.

### 2.11 Módulo operator (sin app Django)

| UC | Descripción | Estado |
|---|---|---|
| UC_OPR_01 | Gestionar estado de agente | 🚫 FUERA DE SCOPE actual |
| UC_OPR_02 | Contestar llamada | 🚫 FUERA DE SCOPE actual |
| UC_OPR_03 | Marcar número saliente | 🚫 FUERA DE SCOPE actual |
| UC_OPR_04 | Transferir llamada | 🚫 FUERA DE SCOPE actual |
| UC_OPR_05 | Hold / Unhold | 🚫 FUERA DE SCOPE actual |
| UC_OPR_06 | Conferencia | 🚫 FUERA DE SCOPE actual |
| UC_OPR_07 | Disposición de llamada | 🚫 FUERA DE SCOPE actual |
| UC_OPR_08 | ACW (After Call Work) | 🚫 FUERA DE SCOPE actual |
| UC_OPR_09 | Break / Pausa | 🚫 FUERA DE SCOPE actual |
| UC_OPR_10 | Logout de agente | 🚫 FUERA DE SCOPE actual |

**Nota:** UC_OPR_01..10 dependen de `AgentStateRepo`, `CallRouter`,
`TelephonyClient` y un canal de tiempo real (WebSocket/SSE) que hoy no existen
en IACT-api. La app `operator` no existe en Django. Su implementación requiere
crear la app, definir el modelo `AgentSession`, integrar el broker de mensajes
y construir el canal bidireccional con el frontend.

### 2.12 Módulo supervision (sin app Django)

| UC | Descripción | Estado |
|---|---|---|
| UC_SUP_01 | Silent monitor / Whisper | 🚫 FUERA DE SCOPE actual |
| UC_SUP_02 | Barge / Take over | 🚫 FUERA DE SCOPE actual |
| UC_SUP_03 | Broadcast a agentes | 🚫 FUERA DE SCOPE actual |

**Nota:** UC_SUP_01..03 dependen del estado activo de las llamadas (acceso
al call leg SIP) y de `TelephonyClient`. Son imposibles sin integración PBX.
La app `supervision` no existe en Django.

----

## 3. Resumen cuantitativo

| Categoría | UCs | % del corpus |
|---|---|---|
| ✅ TDD completo | 56 | 70 % |
| ⚠️ Implementado, sin TDD canónico | 12 | 15 % |
| ❌ Pendiente (REST, Django app existe o es trivial) | 1 | 1 % |
| 🚫 Fuera de scope actual (infraestructura externa) | 18 | 23 % |
| — Ausentes del corpus (UC_RPT_05/06, UC_ACC_06/07) | 4 | — |
| **Total corpus** | **80** | 100 % |

> Los 4 UCs ausentes del corpus no se contabilizan en el total de pendientes
> porque no hay requisitos definidos para ellos.

----

## 4. Análisis de los pendientes Categoría A (12 UCs: IMPL sin TDD)

Estos UCs tienen una implementación funcional en Django que pasó por el ciclo
de desarrollo previo al plan TDD v4. El gap no es de código sino de **cobertura
canónica**: no existe un `tests/unit/faseN/test_uc_*.py` que valide
explícitamente los CAs del corpus, no hay hallazgo documentado y no se
verificó el `required_function` contra el catálogo.

### 4.1 UC_AUD_01 — Listado general de auditoría

**Estado:** ❌ PENDIENTE (no ⚠️ — la distinción importa).

`UC_PERM_10` implementa `AuditEventListView` con `required_function = 'AUD-001'`
(`view_audit_log`). Pero UC_AUD_01 define un endpoint diferente:

- URL: `GET /api/audit/events/` (timeline, todos los módulos)
- Función RBAC: `view_general_audit` — **no existe en el catálogo actual**
- Filtro clave: `?module=MOD_AUTH|MOD_ACC|MOD_RPT|...`
- Meta-audit: `GENERAL_AUDIT_QUERIED` (≠ `AUDIT_LOG_QUERIED`)

La diferencia semántica es que `view_audit_log` (UC_PERM_10) es para
compliance officers que revisan el log de permisos, mientras que
`view_general_audit` (UC_AUD_01) es para auditores con acceso al timeline
completo cross-módulo. No son el mismo rol ni el mismo scope.

**Esfuerzo estimado:** 3 días (añadir `view_general_audit` al catálogo +
nuevo endpoint + tests).

### 4.2 UC_AUTH_04 — Cambiar contraseña

`ChangePasswordView` está completo y bien implementado (commit 552ceae).
La brecha es exclusivamente de cobertura TDD estructurada:

- Falta: `tests/unit/fase6/test_uc_auth_04.py` con tests UT/IT/SEC por CA
- Falta: verificación de `required_function` en el catálogo
- Falta: documento de hallazgos para esta FASE

**Esfuerzo estimado:** 2 días.

### 4.3 UC_AUTH_05 — Gestionar sesiones

`SessionAdminView` (4 endpoints) está bien implementado. Similar a UC_AUTH_04.

**Esfuerzo estimado:** 2 días.

### 4.4 UC_USR_02 — Listar / Buscar usuarios

`UserViewSet` con `UserFilter` implementado. Tiene tests de integración.
La brecha es la ausencia de tests TDD canónicos que cubran explícitamente
CA-02 (restricción PII en listado, CNST-026) y CA-05 (filtros seguros).

**Esfuerzo estimado:** 2 días.

### 4.5 UC_USR_03 / UC_USR_04 — Modificar / Eliminar usuario

`ModifyUserView` + `EliminateUserView` implementados (FASE 2).
Brecha análoga a los anteriores.

**Esfuerzo estimado:** 3 días (ambos conjuntos).

### 4.6 UC_PERM_01 / UC_PERM_02 — Vista PERM de AGR

`AGRAssignView` y `AGRRevokeView` implementados como parte de UC_ACC_04/ACC_02.
El corpus de UC_PERM_01/02 agrega CAs propios de la "vista PERM":
preview de impacto SoD antes de confirmar, y un CA de 404 cuando el AGR nunca
fue asignado. Estos CAs adicionales no están implementados.

**Esfuerzo estimado:** 3 días (CAs adicionales + tests).

### 4.7 UC_PERM_05 / UC_PERM_06 — Gestionar AGRs y composición

`AccessGroupListCreateView` y `FunctionGroupFnView` implementados. Tests
en `test_access_group_viewset.py` pero sin estructura FASE.

**Esfuerzo estimado:** 2 días.

### 4.8 UC_PERM_07 — Motor de permisos efectivos

`EffectivePermissionsView` implementada. Tiene 4 tests en
`test_effective_permissions_view.py`. Los CAs del corpus incluyen:
- CA-02: revocación excepcional gana sobre AGR (testeado parcialmente)
- CA-06: `origin` en la respuesta indica la fuente del permiso
- Caché de permisos (no implementado el TTL/invalidación)

**Esfuerzo estimado:** 3 días (completar CAs + tests estructurados).

### 4.9 UC_PERM_08 — Menú dinámico

`MenuView` implementada (FASE 2). Los CAs incluyen i18n (locale=es|en) y
CA-03 (función REVOKED no aparece en menú). Sin test TDD.

**Esfuerzo estimado:** 2 días.

----

## 5. Deuda técnica acumulada

### 5.1 drf-spectacular — 5 warnings activos

Verificación ejecutada en `develop @ cb235f3`: el schema genera **5 warnings
de colisión** visibles en el output de generación (aunque la API interna de
warnings no los captura como colisiones — son `Warning`, no `Error`):

| ID | operationId en colisión | URLs en conflicto | Origen |
|---|---|---|---|
| DT-SPECTACULAR-001 | `audit_event_export` | `/api/audit/audit-events/export/` vs `/api/audit/export/` | **NUEVA** — FASE 5 creó ambas rutas apuntando a `AuditEventExportView` con el mismo `operation_id`. |
| DT-SPECTACULAR-002 | `access_access_groups_retrieve` | `/api/access/access-groups/` (GET list) vs `/api/access/access-groups/{agr_id}/` (GET detail) | Pre-existente desde FASE 2. Dos vistas distintas, mismo prefijo del `operationId` automático. |
| DT-SPECTACULAR-003 | `auth_change_password_create` | `/api/auth/change-password/` vs `/api/auth/change_password/` | Pre-existente. Ruta canónica (guión) más ruta legacy (underscore). |
| DT-SPECTACULAR-004 | `users_partial_update` | `/api/users/{id}/` vs `/api/users/{user_id}/` | Pre-existente. ViewSet legacy + vista canónica con diferente nombre de parámetro. |
| DT-SPECTACULAR-005 | `users_destroy` | `/api/users/{id}/` vs `/api/users/{user_id}/` | Pre-existente. Mismo origen que DT-SPECTACULAR-004. |

**DT-SPECTACULAR-001 es una regresión introducida en FASE 5.** La URL
`/api/audit/export/` (alias UC_AUD_03) y `/api/audit/audit-events/export/`
(UC_PERM_10 export) comparten el mismo `operation_id = 'audit_event_export'`
porque apuntan a la misma clase `AuditEventExportView`. La solución inmediata
es añadir `operation_id='audit_export'` explícito a la ruta `/api/audit/export/`.

**DT-SPECTACULAR-002 al 005** son colisiones pre-existentes que requieren un
ciclo de limpieza de routing: eliminar rutas legacy duplicadas o asignar
`operation_id` explícitos a las vistas afectadas.

### 5.2 DT-SPECTACULAR-006 — Vistas sin `serializer_class`

El schema genera `Error: unable to guess serializer` para **34 vistas** que
usan `APIView` sin `serializer_class` declarado. drf-spectacular puede
introspectarlas si se añade el decorador `@extend_schema(request=...,
responses=...)` completo o se migra a `GenericAPIView`.

Esto no rompe el schema (las vistas se ignoran gracefully) pero produce un
schema incompleto para Swagger/Redoc. Impacto bajo a medio según el uso que
haga el equipo de la documentación generada.

### 5.3 DT-SPECTACULAR-007 — `PriorityEa7Enum` naming

El campo `priority` existe en múltiples modelos con diferentes sets de
choices. drf-spectacular genera un nombre no determinístico (`PriorityEa7Enum`)
para resolver la ambigüedad. La solución es añadir entradas en
`ENUM_NAME_OVERRIDES` en `settings/spectacular.py`.

### 5.4 DT-SEGMENT-001 — SegmentResolver no implementado

Los segmentos de acceso están hardcodeados como `['all']` en múltiples
servicios (UC_ALR_02, UC_RPT_03, UC_ACC_09). El `SegmentResolver` real
requiere integrar con el modelo de segmentación de la empresa (unidades de
negocio, geografías). Hasta que no existan los requisitos del `SegmentModel`,
no es posible implementarlo.

### 5.5 DT-REQUIRED-FUNCTION-001 — Test de regresión pendiente

A lo largo de FASES 3, 4 y 5 se encontraron **4 vistas** con
`required_function = 'LOG-001'` incorrecto. La causa raíz es estructural:
no existe ningún test que verifique automáticamente que el `required_function`
de cada vista existe en el catálogo y corresponde al UC que implementa.

El test propuesto:
```python
# tests/unit/config/test_required_function_catalog.py
def test_todas_las_vistas_tienen_required_function_valido():
    """Verifica que todas las vistas con required_function usen un código del catálogo."""
    from apps.access.models import Function
    valid_codes = set(Function.objects.values_list('code', flat=True))
    # Introspección de todas las URLConf...
```

### 5.6 H-M-001 — IACT-docs: 4 documentos sin commit

Los siguientes archivos de IACT-docs fueron modificados pero **nunca
commiteados** (identificado en conversaciones anteriores):

- `cnst-030-reglas-de-separacion-de-funciones-sod.rst` — v3.0.0
- `cnst-033-vocabulario-unificado-rbac.rst` — v2.0.0
- `arquitectura-tecnica/rbac/modelo-rbac-iact.rst` — v5.4.0
- `normativa/gobernanza/adr-gob-009-rbac-modelo-conceptual.rst` — v2.0.0

Estos documentos reflejan los cambios de STD-008 que ya están implementados
en `IACT-api`. Su ausencia en el repositorio de docs crea inconsistencia entre
el código y la documentación normativa.

----

## 6. UCs fuera de scope actual — análisis de viabilidad

### 6.1 Caller (UC_CLI_01..05)

Estos UCs son flujos de **media plane**: el cliente llama por teléfono, el PBX
recibe la llamada y el motor IVR (IVRRunner) ejecuta el árbol de menús con
audio/DTMF. IACT-api no es el ejecutor — es el **proveedor de configuración**
(qué menús existen, qué agentes están disponibles) y el **receptor de eventos**
(CALL_STARTED, IVRSessionEvent).

Para integrar Django con este flujo se necesita:
1. Un modelo `IVRDefinition` con la estructura del árbol de menús.
2. Un endpoint de configuración que el IVRRunner consulte al arrancar.
3. Un webhook que reciba eventos del IVRRunner y los persista como AuditEvents.

Estos tres componentes son REST y son implementables en IACT-api. Los UCs
del corpus (que describen el flujo desde la perspectiva del llamante) no son
el objetivo — los objetivos son los endpoints que el IVRRunner consume.

**Recomendación:** Reformular como UC_IVR_CONFIG (configuración del árbol IVR)
y UC_IVR_EVENTS (webhooks de eventos). Estimación: 1–2 semanas con los
requisitos correctos.

### 6.2 Operator (UC_OPR_01..10)

Los UCs de operador son gestionados actualmente por el sistema legacy `ivr_legacy`
(app existente en Django). Si el objetivo es construir la nueva interfaz en
IACT-api, se requiere:

1. App `operator` con modelo `AgentSession` (estado: available/busy/break/ACW/offline).
2. Canal WebSocket (Django Channels) o SSE para notificar cambios de estado al frontend.
3. Integración `TelephonyClient` para acciones de llamada (contestar, colgar, transferir).
4. `CallRouter` para enrutamiento de llamadas entrantes según disponibilidad.

El esfuerzo es sustancial (3–6 semanas) y depende de decisiones de arquitectura
(¿Django Channels vs. servicio dedicado? ¿Integración SIP directa o proxy?).

**Recomendación:** Separar en dos fases: (a) gestión de estado de agente
(UC_OPR_01, UC_OPR_08/09/10) que son REST puro sin PBX, estimación 1 semana;
(b) acciones de llamada (UC_OPR_02..07) que requieren integración telefónica,
estimación 3–4 semanas adicionales.

### 6.3 Supervision (UC_SUP_01..03)

Dependen de acceso al estado activo de llamadas SIP. Sin integración PBX no
son implementables. UC_SUP_03 (Broadcast a agentes) es el más simple — es
un canal de mensajería que no requiere SIP — y podría implementarse sobre
InternalMailbox (UC_ALR_01 ya provee las bases) con 1 semana de esfuerzo.

----

## 7. Propuesta de FASE 6 — UCs con implementación existente

Estos 12 UCs tienen código ya escrito. El trabajo de FASE 6 es:
leer los CAs del corpus, escribir los tests TDD canónicos (Red),
corregir lo que no pase (Green), documentar hallazgos, y commitear.

### 7.1 Scope propuesto

| UC | CAs pendientes de validar | Esfuerzo |
|---|---|---|
| UC_AUTH_04 | CA-02: password actual incorrecto. CA-04: password reusado. CA-05: first_login=False post-cambio. CA-06: otras sesiones cerradas. | 2d |
| UC_AUTH_05 | CA-02: filtro por user_id + SESSIONS_VIEWED_FOR_USER. CA-07: SELF_BULK_CLOSE_FORBIDDEN. CA-11: InternalMessage notificación. | 2d |
| UC_USR_02 | CA-02: sin PII (CNST-026). CA-05: filtros seguros anti-SQLi. CA-08: cursor paginación estable. | 2d |
| UC_USR_03 | CA-02: state BLOCKED cierra Sessions. CA-04: SELF_STATE_CHANGE_FORBIDDEN. CA-08: transiciones inválidas. | 2d |
| UC_USR_04 | CA-01: ELIMINATED + Assignments REVOKED. CA-03: SELF_ELIMINATION_FORBIDDEN. CA-06: idempotencia NOOP. | 1d |
| UC_PERM_01 | CAs adicionales vs UC_ACC_04: preview SoD antes de confirmar. | 2d |
| UC_PERM_02 | CAs adicionales vs UC_ACC_02: 404 si AGR nunca asignado. | 1d |
| UC_PERM_05 | CA-02: code duplicado 409. CA-07: PREDEFINED_NOT_MUTABLE. CA-09: AccessGroup retirado no asignable. | 2d |
| UC_PERM_06 | CA-01: add functions exitoso + COMPOSITION_CHANGED. CA-02: remove. CA-04: función ya en AGR idempotente. | 2d |
| UC_PERM_07 | CA-02: revocación excepcional gana sobre AGR. CA-06: `origin` en response. Caché invalidación. | 3d |
| UC_PERM_08 | CA-03: función REVOKED no aparece. i18n locale. CA-15: cero AuditEvents. | 2d |
| UC_AUD_01 | Endpoint nuevo: `view_general_audit`, filtro `module`, meta-audit `GENERAL_AUDIT_QUERIED`. | 3d |

**Total estimado FASE 6:** 26 días de desarrollo individual.

### 7.2 Prerrequisitos de FASE 6

**P-6.1:** Añadir `view_general_audit` al catálogo (`AUD-005`) para UC_AUD_01.

**P-6.2:** Añadir `GENERAL_AUDIT_QUERIED` a `VALID_EVENT_TYPES`.

**P-6.3:** Corregir DT-SPECTACULAR-001 (`audit_event_export`) añadiendo
`operation_id` explícito a la ruta `/api/audit/export/`:
```python
path('export/', AuditEventExportView.as_view(), name='audit-export')
# + @extend_schema(operation_id='audit_export_legacy') en la URL, o
# crear AuditExportView separada con required_function='AUD-003' propio.
```

**P-6.4:** Implementar `DT-REQUIRED-FUNCTION-001`: test de regresión de
`required_function` que bloquee el CI si una vista usa un código inexistente.

**P-6.5 (recomendado):** Commitear los 4 documentos pendientes en IACT-docs
(H-M-001) para alinear la documentación normativa con el código.

----

## 8. Propuesta de FASE 7 — UCs de operator (estado de agente, sin PBX)

El subconjunto de UC_OPR que no requiere integración telefónica directa:

| UC | Descripción | Infraestructura requerida |
|---|---|---|
| UC_OPR_01 | Gestionar estado de agente | AgentSession model, REST + SSE |
| UC_OPR_08 | ACW post-llamada | AgentSession transitions |
| UC_OPR_09 | Break / Pausa con reason | AgentSession, BREAK_REASON catalog |
| UC_OPR_10 | Logout de agente | AgentSession, force-offline |

**Nuevas apps Django requeridas:**
- `apps/operator/` con `AgentSession`, `AgentStateTransition`, `BreakReason`
- Canal SSE (Django EventSourceResponse o Django Channels lite)

**Total estimado FASE 7:** 8–10 días.

----

## 9. Pendientes fuera de IACT-api

Los siguientes ítems están bloqueados o son dependencia de otros repositorios:

| Ítem | Repositorio | Estado |
|---|---|---|
| H-M-001: CNST-030/033 sin commit | IACT-docs | Pendiente commit en rama `develop` |
| STD-008 merge IACT-ui | IACT-ui | Branch `claude/project-analysis-N9IkV` pendiente merge |
| UC_CLI_01..05 | Vendor IVR externo | Requiere definición arquitectónica PBX |
| UC_OPR_02..07 | IACT-api + Vendor PBX | Requiere integración SIP/TelephonyClient |
| UC_SUP_01..02 | IACT-api + Vendor PBX | Requiere call leg SIP |
| UC_RPT_05/06 | IACT-docs | Sin corpus definido — requiere análisis de negocio |
| UC_ACC_06/07 | IACT-docs | Sin corpus definido — requiere análisis de negocio |

----

## 10. Resumen ejecutivo para planificación

```
Estado actual (develop @ cb235f3):
  56 UCs con TDD canónico completo (70 % del corpus)
  12 UCs implementados sin cobertura TDD canónica (15 %)
   1 UC pendiente de implementar (UC_AUD_01) (1 %)
  18 UCs fuera de scope actual por dependencias externas (23 %)

Deuda técnica pendiente:
  5 warnings drf-spectacular (1 regresión nueva — DT-SPECTACULAR-001)
  34 vistas sin serializer_class (DT-SPECTACULAR-006, bajo)
  DT-SEGMENT-001: SegmentResolver hardcodeado
  DT-REQUIRED-FUNCTION-001: test de regresión required_function
  H-M-001: 4 documentos IACT-docs sin commit

Propuesta de siguiente ciclo:
  FASE 6 — 12 UCs categoría A + UC_AUD_01 — ~26 días
  FASE 7 — UC_OPR_01/08/09/10 (sin PBX) — ~10 días
  FASE 8 — UC_OPR_02..07 + UC_SUP (requiere PBX) — TBD
```

----

*Documento generado con base en el estado del repositorio `IACT-api @ develop`
a fecha 2026-05-14. Cualquier commit posterior puede alterar el estado de los
ítems aquí descritos.*
