# Hallazgos — FASE 4 TDD: 17 UCs MEDIOS

**Artefacto:** HALLAZGOS-FASE4-TDD-20260513
**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Commits:** `4487ed4` (FASE 4), `7e1144c` (logs fix) en `develop`
**Estado:** Cerrado — 98/98 verificaciones PASS

----

## Resumen ejecutivo

FASE 4 implementa los 17 UCs MEDIOS del plan TDD v4. Se detectaron 6 hallazgos
estructurales, todos resueltos en el mismo commit. Los hallazgos se dividen en
dos categorías: errores de corpus (modelos y funciones que el plan no capturó)
y errores de drf-spectacular (patrón de `operation_id` en clase).

| Grupo | UCs | Nuevos módulos |
|---|---|---|
| Prerrequisitos | — | 5 migraciones, catálogo 65→72 funciones, 13 event types |
| A (standalone) | UC_AUTH_03, UC_LOG_05, UC_ALR_04 | 3 servicios, 3 vistas |
| B (dependencias) | UC_ACC_08, UC_PERM_03/04, UC_LOG_04, UC_ALR_05, UC_AUD_04 | 5 servicios, 6 vistas |
| C (analytics) | UC_RPT_07/08/11, UC_RPT_12..17 | 4 servicios, 12 vistas |

**Verificación final:** 98/98 PASS. 0 colisiones drf-spectacular nuevas.
Catálogo: 72 funciones. Tests escritos: 7 archivos, ~120 tests.

----

## drf-spectacular — verificación

### Colisión resuelta: `access_exceptional_list`

`ExceptionalGrantView` tenía `operation_id='access_exceptional_list'` en el
decorador de clase GET. El legacy `ExceptionalPermissionViewSet` del router
también registraba `GET /api/access/exceptional/` con el mismo `operationId`.

Resolución: `operation_id='access_exceptional_permissions_for_user'` en la
vista nueva.

### Vistas de un solo método con `@extend_schema(operation_id)`

`ExceptionalRevokeView` (solo DELETE) y `ExceptionalPreviewView` (solo GET)
reciben la advertencia de drf-spectacular `"using @extend_schema on viewset
class X with parameters operation_id"`. Esta advertencia es un falso positivo:
el problema solo ocurre cuando hay colisión entre múltiples métodos HTTP en la
misma clase. Con un único método no hay colisión y el schema se genera
correctamente. Las vistas no requieren `@extend_schema_view`.

Las 4 colisiones pre-existentes (DT-ROUTING-001..003) permanecen sin cambios.

----

## Hallazgo H-F4-GRP-PRE-001 — 7 funciones RBAC ausentes del catálogo

### Descripción

Al leer `actores-precondiciones.rst` de UC_RPT_12..17 antes de implementar,
se detectaron 7 funciones requeridas que no existían en el catálogo:

| Código | Función | UC | Detectada en |
|---|---|---|---|
| RPT-014 | `view_agent_reports` | UC_RPT_12 | actores.rst |
| RPT-015 | `view_agent_detail` | UC_RPT_12 CA-06 | criterios.rst |
| RPT-016 | `view_queue_reports` | UC_RPT_13 | actores.rst |
| RPT-017 | `view_campaign_reports` | UC_RPT_14 | actores.rst |
| RPT-018 | `view_transfer_reports` | UC_RPT_15 | actores.rst |
| RPT-019 | `view_ivr_reports` | UC_RPT_16 | actores.rst |
| RPT-020 | `view_unique_clients_reports` | UC_RPT_17 | actores.rst |

### Causa raíz

El plan TDD v4 listaba los UCs por nombre pero no pre-leía los
`actores-precondiciones.rst` de cada uno. Las funciones de lectura simple
(prefijo `view_`) son sistemáticamente subrepresentadas en el diseño inicial
porque no generan operaciones visibles en el modelado de casos de uso.

Este es el tercer hallazgo de este patrón (H-F3-PRE-005, H-F3-GRP-A-001).
La solución estructural sería leer todos los `actores-precondiciones.rst`
como paso cero antes de cualquier planificación.

### Resolución

Catálogo actualizado: 65 → 72 funciones. Total esperado actualizado.

---

## Hallazgo H-F4-GRP-PRE-002 — `InfraLogView.required_function` incorrecto

### Descripción

`InfraLogView` en `apps/logs/views.py` tenía `required_function = 'LOG-001'`
(`view_application_logs`) en lugar de `'LOG-005'` (`view_infrastructure_logs`).

El error viene de FASE 2, donde la vista se creó como stub sin leer el corpus
de UC_LOG_05. La función `LOG-001` controla acceso a logs de aplicación Django
(UC_LOG_01), no a logs de infraestructura.

Consecuencia práctica: cualquier usuario con `LOG-001` podría acceder a logs
de infraestructura sin tener la función `LOG-005`. En producción esto sería
una vulnerabilidad de control de acceso.

### Resolución

`InfraLogView.required_function = 'LOG-005'`. La vista también fue completada
con la query real a MariaDB y el filtro por `host` (CA-02).

---

## Hallazgo H-F4-GRP-PRE-003 — `ExceptionalPermission` incompatible con corpus

### Descripción

El modelo pre-FASE 4 tenía las siguientes discrepancias con
`uc-acc-08/datos-involucrados.rst § 7.4.1`:

| Campo | Pre-FASE 4 | Corpus UC_ACC_08 |
|---|---|---|
| Estado inicial | `pending` | `ACTIVE` |
| Nombre campo expiración | `valid_until` | `expires_at` |
| Nombre campo inicio | `valid_from` | `granted_at` |
| Mínimo justification | 50 chars | 20 chars |
| `ticket_reference` | ausente | requerido con política |
| `revoked_at` | ausente | obligatorio en UC_PERM_04 |
| `revoked_by` | ausente | FK a User en UC_PERM_04 CA-02 |
| `revoke_reason` | ausente | mínimo 20 chars CA-06 |

El estado `pending/approved` implicaba un flujo de aprobación que el corpus no
define — UC_ACC_08 otorga directamente (`state=ACTIVE`), sin aprobación previa.

### Resolución

Migración `0009_fase4_exceptionalpermisos_canonical.py`:
- Añade los campos canónicos del corpus.
- Mantiene `valid_from/valid_until` como backward compat nullable.
- `status` choices ampliado para incluir legacy `pending/approved`.
- Default cambiado de `pending` a `ACTIVE`.
- Mínimo de `justification` documentado como 20 chars (validado en servicio).

---

## Hallazgo H-F4-GRP-PRE-004 — `AlertSubscription` incompatible con corpus UC_ALR_05

### Descripción

`AlertSubscription` usaba `alert_configuration` FK a `AlertConfiguration`
(modelo de configuraciones de alerta legacy) y `is_active` boolean.

El corpus de UC_ALR_05 define el endpoint como
`POST /api/me/alert-subscriptions/` con `rule_id` (FK a `AlertRule`) y
un estado canónico `state ∈ {active, paused, cancelled, auto_paused}`.

`AlertRule` y `AlertConfiguration` son modelos diferentes — el primero es el
nuevo sistema FASE 3, el segundo es la configuración legacy. Una suscripción
al modelo nuevo no podía persistirse sin cambiar el modelo.

### Resolución

Migración `0005_fase4_alertsubscription_canonical.py`:
- Añade `rule` FK nullable a `AlertRule`.
- Añade `state` CharField canónico.
- Añade `severity_filter` CharField.
- Mantiene `alert_configuration` y `is_active` para registros legacy.
- La nueva vista `AlertSubscriptionListView` usa exclusivamente `rule` y `state`.

---

## Hallazgo H-F4-GRP-PRE-005 — `ScheduledReport` incompatible con corpus UC_RPT_07

### Descripción

`ScheduledReport` tenía FK CASCADE a `Report` (modelo legacy de reportes
pre-generados). El corpus de UC_RPT_07 define un modelo standalone similar a
`ExportJob`: `actor_id`, `report_type`, `frequency`, `status`, y métricas de
fiabilidad como `failure_count` y `auto_paused_at`.

Los campos de programación eran mínimos — solo `cron_expression` — sin soporte
para `daily/weekly/monthly` con `day_of_week/day_of_month`. El corpus define
CA-01..04 para cada frecuencia específica.

El status era `is_active` (boolean) en lugar de
`active/paused/auto_paused/deleted`, por lo que `auto_paused` (CA-10: 3 fallos
consecutivos) era imposible de representar.

### Resolución

Migración `0005_fase4_scheduledreport_canonical.py`:
- Añade `actor` FK nullable a User.
- Añade `frequency`, `day_of_week`, `day_of_month`, `run_at_hour`, `run_at_minute`.
- Añade `status` canónico (4 estados).
- Añade `failure_count`, `auto_paused_at`, `last_job` FK a ExportJob.
- Mantiene `report` FK SET_NULL y `is_active` para backward compat.
- `MAX_SCHEDULES_PER_USER = 10` como constante de clase (CA-07).

---

## Hallazgo H-F4-GRP-B-001 — Bug en `ScheduleValidator.validate_cron`

### Descripción

El validador de cron procesaba el wildcard `*` convirtiéndolo a `0` y luego
comprobaba si `0` estaba en el rango del campo. Para el campo 2 (day of month,
rango `[1, 31]`), el valor `0` generaba un `ValueError` falso positivo,
rechazando expresiones válidas como `'0 6 * * 1'` (lunes a las 6am).

El error se detectó en la primera ejecución de la verificación integral:
```
ValueError: cron '0 6 * * 1' inválido en campo 2: '*'
```

### Causa raíz

La lógica de normalización `token.replace('*', '0')` era demasiado agresiva.
El wildcard `*` en cualquier campo es siempre válido — significa "cualquier
valor" y no debe convertirse a un número concreto antes de la validación de
rango.

### Resolución

Reescritura del método `validate_cron` con manejo explícito de wildcards:
```python
if part == '*':
    continue  # wildcard puro siempre válido
```
El paso y el rango (`*/2`, `1-5`) se extraen antes del chequeo numérico. Los
tests `UT-01` (cron válido) y `UT-02` (cron inválido) cubren ambos caminos.

----

## Decisiones de diseño

### UC_AUD_04 — HMAC_SECRET desde variable de entorno

`HMACSigner` usa `os.environ.get('COMPLIANCE_HMAC_SECRET', 'iact-compliance-dev-secret')`.
El secret en producción se inyecta como variable de entorno. El valor de
desarrollo es predecible pero aceptable en tests. En producción se rota
periódicamente como parte de la política de secretos.

### UC_RPT_17 — `top_n_anonymized` con SHA-256 prefix

`DistinctClientCounter.top_n_anonymized` retorna los 8 primeros caracteres del
hash SHA-256 del `client_id`. Esto cumple CA-05 (top N sin client_id raw) y
CA-06 (sin PII en response). El prefix de 8 chars tiene una colisión esperada
de `1/(16^8) ≈ 1 en 4.3 mil millones` — suficiente para análisis de patrones
sin identificar individuos. En producción se usa un salt de tenant para evitar
precomputed rainbow tables.

### UC_ACC_08 — `mailbox HARD` dentro de `transaction.atomic()`

El mailbox HARD (CA-07) se implementa llamando `_notify()` dentro del bloque
`transaction.atomic()`. Si el mailbox lanza, la excepción se propaga y el
atomic hace rollback de todos los `ExceptionalPermission.create()`. Esto
garantiza que ningún permiso queda en BD sin su correspondiente notificación
al usuario, cumpliendo P-10 del corpus.

La vista captura cualquier excepción que escape del servicio y retorna
`500 MAILBOX_FAILED`. Los tests IT-07 y IT-09 verifican que el conteo de
`ExceptionalPermission` no aumenta cuando el mailbox falla.

### UC_RPT_12 — `AgentDetailView` con función adicional RPT-015

La vista de detalle de agente (`AgentDetailView`) requiere `RPT-015`
(`view_agent_detail`) en lugar de `RPT-014` (`view_agent_reports`). Esto
implementa el acceso privilegiado de CA-06: un usuario puede ver la lista de
agentes con `RPT-014` pero necesita `RPT-015` adicional para ver el detalle
completo. Las dos funciones modelan granularidades distintas de acceso al mismo
recurso.

### DT-GITIGNORE-001 — recurrencia en FASE 4

Los archivos `apps/logs/log_export_service.py` y `apps/logs/log_export_views.py`
volvieron a quedar excluidos por la regla `logs/` en `.gitignore`, requiriendo
`git add -f` nuevamente. La corrección pendiente sigue siendo reemplazar `logs/`
por `*.log` en el `.gitignore`. Este ciclo se repite en cada FASE porque la
causa raíz no se ha resuelto. Se eleva a prioridad en el próximo sprint de
limpieza de deuda técnica.

----

## Estado del plan TDD v4 tras FASE 4

```
FASE 3 — 11 UCs RAÍZ        — COMPLETADA (commits a31487f..382c132)
FASE 4 — 17 UCs MEDIOS      — COMPLETADA (commits 4487ed4, 7e1144c)
FASE 5 — 10 UCs BAJOS       — PENDIENTE
```

FASE 5 contiene: UC_ACC_09 (revocar assignment), UC_USR_05 (perfil usuario),
UC_PERM_05/06 (gestionar SoD), UC_LOG_06/07 (health/metrics logs),
UC_RPT_18/19 (exportar vistas guardadas), UC_AUD_05 (exportar auditoría),
y UC_AUTH_04 (cambiar contraseña forzado).

----

## Métricas de FASE 4

| Métrica | Valor |
|---|---|
| Verificaciones PASS | 98/98 |
| Archivos creados | 24 |
| Archivos modificados | 12 |
| Inserciones netas | ~3.960 líneas |
| Migraciones generadas | 4 (access:0009, alerts:0005, reports:0005 × 2) |
| Funciones añadidas al catálogo | 7 (65 → 72) |
| Event types añadidos | 13 |
| Tests escritos | ~120 en 7 archivos |
| Colisiones drf-spectacular nuevas | 1 → resuelta → 0 |
| DT-GITIGNORE-001 recurrencias | 2 (logs: log_export_service + log_export_views) |
