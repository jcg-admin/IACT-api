# Hallazgos — Prerequisitos FASE 3 TDD (P-3.1..P-3.4)

**Artefacto:** HALLAZGOS-FASE3-PREREQS-TDD-20260513
**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Commits:** `6580263` (prerequisitos) en `develop`
**Estado:** Cerrado — 21/21 verificaciones PASS

----

## Resumen ejecutivo

Los prerequisitos FASE 3 son correcciones de deuda técnica que deben
existir antes de que cualquier UC de FASE 3 pueda implementarse con tests
que pasen. Se identificaron 4 prerequisitos en el plan y se detectaron
2 hallazgos adicionales durante la implementación.

| ID | Descripción | Estado |
|---|---|---|
| P-3.1 | `required_function` canónico en pipeline | Resuelto |
| P-3.2 | `ETLLogTailView.required_function` corregido | Resuelto |
| P-3.3 | Modelos `AlertRule`, `AlertRuleHistory`, `Alert` | Resuelto |
| P-3.4 | Stub UC_RPT_02 con URL registrada | Resuelto |
| H-F3-PRE-005 | `view_realtime_metrics` ausente del catálogo | Resuelto |
| H-F3-PRE-006 | `SeparationRuleAdmin` con campos v5.2.1 | Resuelto |

----

## drf-spectacular — verificación

Sin colisiones nuevas de `operationId` introducidas por los prerequisitos.
`/api/reports/realtime/` aparece en el schema con `operationId`
`reports_realtime_retrieve` sin colisiones. Las 4 colisiones pre-existentes
(DT-ROUTING-001..003) permanecen sin cambios.

----

## P-3.1 — `required_function` canónico en `pipeline/views.py`

### Problema detectado

`etl_errors` y `etl_data_availability` tenían verificaciones inline con
`request.user.has_function('pipeline.*')` — formato legacy de namespace
(`namespace.action`). Estas verificaciones:
1. No son el mecanismo canónico (CNST-010 requiere `HasFunction` con atributo)
2. Usan strings que no corresponden a ningún código `MOD-NNN` del catálogo v5.4.0
3. `HasFunction` también estaba en `@permission_classes` pero sin `required_function`
   asignado — retornaba `True` sin verificar (el atributo faltante hace bypass)

`etl_retry` no tenía verificación de función en absoluto.

### Corrección aplicada

```python
# Antes (etl_errors):
if not (request.user.is_superuser or
        request.user.has_function('pipeline.view_errors')):
    return Response({'error': 'Function pipeline.view_errors required.'}, status=403)

# Después: verificación eliminada — HasFunction lee el atributo
etl_errors.required_function           = 'PIP-002'  # view_pipeline_errors
etl_data_availability.required_function = 'PIP-003'  # view_data_availability
etl_retry.required_function            = 'PIP-004'  # request_pipeline_retry
```

Los tres atributos se asignan al final del módulo `pipeline/views.py`,
después de la definición de las funciones decoradas con `@api_view`.
`HasFunction` usa `getattr(view, 'required_function', None)` para
leer el atributo en las funciones wrapper de `@api_view`.

### Impacto de seguridad

Antes de esta corrección, cualquier usuario autenticado (sin importar
sus funciones RBAC) podía acceder a los errores ETL y a la disponibilidad
de datos. `HasFunction` estaba en `@permission_classes` pero sin el atributo
`required_function`, lo que hacía que retornara `True` incondicionalmente
(ver código de `HasFunction`: "4. Sin restricción si no se define").

---

## P-3.2 — `ETLLogTailView.required_function` corregido

### Problema

`ETLLogTailView` implementa UC_LOG_02 (logs del pipeline ETL) pero tenía
`required_function = 'LOG-001'` (`view_application_logs`). El código
canónico para UC_LOG_02 es `LOG-004` (`view_etl_logs`).

Esto permitía que cualquier usuario con `LOG-001` (supervisores, auditores,
operadores con acceso a logs de aplicación) también pudiera ver los logs
ETL sin tener `LOG-004`.

### Corrección

```python
class ETLLogTailView(APIView):
    required_function = 'LOG-004'  # view_etl_logs
```

### Nota sobre `.gitignore`

El directorio `callcentersite/apps/logs/` está listado en `.gitignore`
como `logs/` (regla demasiado amplia). El archivo `logs/views.py` estaba
previamente tracked por git, por lo que el warning de `.gitignore` fue
informativo y el cambio quedó incluido en el commit `6580263`. La regla
`.gitignore` es candidata para ser más específica (excluir `*.log` en lugar
de directorios completos), pero está fuera del scope de esta fase.

---

## P-3.3 — Modelos `AlertRule`, `AlertRuleHistory`, `Alert`

### Por qué `AlertConfiguration` no sirve para UC_ALR_01

El módulo `alerts` ya tenía `AlertConfiguration` (para el sistema de
alertas automáticas de APScheduler) pero su estructura no coincide con
el contrato de UC_ALR_01:

| Campo del corpus (uc-alr-01) | `AlertConfiguration` | `AlertRule` (nuevo) |
|---|---|---|
| `metric` (enum) | `condition` (JSON general) | `metric` CharField |
| `scope` (JSON segmento) | no existe | `scope` JSONField |
| `condition` (op + threshold) | `condition` (distinto schema) | `condition` JSONField |
| `window_minutes` | no existe | `window_minutes` PositiveIntegerField |
| `severity` (enum) | `priority` (diferente enum) | `severity` CharField |
| `actions` (lista) | no existe | `actions` JSONField |
| `cooldown_minutes` | no existe | `cooldown_minutes` PositiveIntegerField |
| `status` (active/paused) | `is_active` (bool) | `status` CharField |
| `version` (por update) | no existe | `version` PositiveIntegerField |

Son modelos para dominios distintos. `AlertConfiguration` es para el
motor de evaluación del sistema; `AlertRule` es para las reglas definibles
por el usuario final (UC_ALR_01/02/03).

### Estructura de los 3 modelos creados

**`AlertRule`** (db_table: `alerts_alert_rule`):
- `id`: UUID PK (`uuid4`)
- `actor`: FK User PROTECT — propietario de la regla
- `name`, `metric`, `scope`, `condition`, `window_minutes`
- `severity`: `info | warning | error | critical`
- `actions`: JSONField (lista)
- `cooldown_minutes`: default 60 (CA-09)
- `status`: `active | paused` — BR-009: nunca DELETE
- `version`: incrementado por update (CA-05)
- Índices: `idx_alr_actor`, `idx_alr_status_ver`

**`AlertRuleHistory`** (db_table: `alerts_alert_rule_history`):
- Snapshot inmutable por cada update (CA-10 auditoría)
- `unique_together = ('rule', 'version')` — garantía de no-duplicados
- BR-009: no DELETE — los snapshots son evidencia de cambios de configuración

**`Alert`** (db_table: `alerts_alert`):
- `id`: UUID PK (`uuid4`)
- `rule`: FK AlertRule PROTECT (la regla puede no borrarse)
- Snapshots inmutables al momento del disparo: `rule_name`, `metric`, `scope`,
  `severity`, `threshold`
- `state`: `firing | acknowledged | resolved | closed`
- `fired_at`, `acknowledged_by`, `acknowledged_at`, `acknowledged_note`,
  `resolved_at`, `current_value`
- Índices: `idx_alert_state_sev` (UC_ALR_02 — orden por severity DESC),
  `idx_alert_rule`

### Migración generada

`0004_fase3_prereq_alert_rule_and_alert.py` incluye además:
- `Alter field owner on internalmailbox` — pendiente pre-existente
- `Alter field sender on mailboxmessage` — pendiente pre-existente

Estas alteraciones son `help_text`/`verbose_name` sin cambio de esquema de BD.

---

## P-3.4 — Stub UC_RPT_02

### Implementación

`apps/reports/realtime_view.py` → `RealtimeMetricsView` (APIView).

- `GET /api/reports/realtime/` → `503 FEATURE_NOT_AVAILABLE`
- `required_function = 'RPT-012'` (view_realtime_metrics)
- `permission_classes = [IsAuthenticated, HasFunction]` (CNST-010 explícito)
- Incluye en el body: `contract`, `function`, `topics_required`

El body de 503 es documentación ejecutable: un cliente que llame al endpoint
obtiene exactamente qué infraestructura falta y cuáles tópicos de pub/sub
necesita el sistema.

---

## H-F3-PRE-005 — `view_realtime_metrics` ausente del catálogo v5.4.0

### Detección

Al implementar P-3.4, se verificó que el catálogo v5.4.0 no contenía
ninguna función `view_realtime_metrics`. El corpus (uc-rpt-02/actores)
requiere explícitamente esta función para el actor que abre el stream.

`RPT-002` en el catálogo era `view_dashboard` — las 11 slots RPT-001..011
estaban todos ocupados.

### Resolución

Función añadida como `RPT-012` en `create_functions.py`:
```python
('RPT-012', 'view_realtime_metrics', 'MOD_RPT',
 'Ver métricas en tiempo real vía SSE (UC_RPT_02). Requiere infraestructura ASGI.')
```

El catálogo pasa de 61 a 62 funciones. El total de funciones en el sistema
cambia de 61 a 62.

---

## H-F3-PRE-006 — `SeparationRuleAdmin` con campos del modelo v5.2.1

### Detección

Al ejecutar `makemigrations` para P-3.3, Django levantó un `SystemCheckError`:

```
SeparationRuleAdmin: (admin.E002) 'raw_id_fields[0]' refers to 'function_a'
                     which is not a field of 'access.SeparationRule'
SeparationRuleAdmin: (admin.E108) 'list_display[1]' refers to 'function_a'
SeparationRuleAdmin: (admin.E108) 'list_display[2]' refers to 'function_b'
SeparationRuleAdmin: (admin.E108) 'list_display[3]' refers to 'status'
SeparationRuleAdmin: (admin.E116) 'list_filter[0]' refers to 'status'
```

`SeparationRuleAdmin` en `access/admin.py` usaba `function_a`, `function_b`
y `status` — campos del modelo v5.2.1 eliminados en FASE 0. Este error
bloqueaba cualquier llamada a `makemigrations` o `migrate`.

### Causa raíz

El archivo `admin.py` no fue incluido en el ciclo de remediación STD-008
(que se centró en `views.py`, `models.py`, `urls.py`, serializers y tests).
El admin de Django no participa en el schema drf-spectacular ni en los
tests unitarios, por lo que el error pasó desapercibido en todas las
verificaciones previas.

### Corrección

```python
# Antes (campos v5.2.1)
class SeparationRuleAdmin(admin.ModelAdmin):
    list_display  = ['name', 'function_a', 'function_b', 'status', 'created_by']
    list_filter   = ['status']
    search_fields = ['name', 'function_a__code', 'function_b__code']
    raw_id_fields = ['function_a', 'function_b', 'created_by']

# Después (campos v5.4.0)
class SeparationRuleAdmin(admin.ModelAdmin):
    list_display  = ['code', 'name', 'state', 'created_by']
    list_filter   = ['state']
    search_fields = ['code', 'name']
    raw_id_fields = ['created_by']
    filter_horizontal = []
```

---

## Verificación ejecutada

```
[PASS] P-3.1: etl_errors.required_function = PIP-002
[PASS] P-3.1: etl_data_availability.required_function = PIP-003
[PASS] P-3.1: etl_retry.required_function = PIP-004
[PASS] P-3.1: has_function pipeline.view_errors eliminado
[PASS] P-3.1: has_function pipeline.view_data_availability eliminado
[PASS] P-3.2: ETLLogTailView.required_function = LOG-004
[PASS] P-3.3: AlertRule importable
[PASS] P-3.3: AlertRule.STATUS_ACTIVE existe
[PASS] P-3.3: AlertRule.version field
[PASS] P-3.3: AlertRuleHistory.unique_together (rule, version)  ← Django: tupla de tuplas
[PASS] P-3.3: Alert.STATE_FIRING existe
[PASS] P-3.3: Alert.acknowledged_note field
[PASS] P-3.3: db_table AlertRule = alerts_alert_rule
[PASS] P-3.3: db_table Alert = alerts_alert
[PASS] P-3.4: RealtimeMetricsView importable
[PASS] P-3.4: required_function = RPT-012
[PASS] P-3.4: URL realtime-metrics = /api/reports/realtime/
[PASS] P-3.4: RPT-012 view_realtime_metrics en catálogo
[PASS] H-F3-PRE-006: SeparationRuleAdmin sin campos v5.2.1
[PASS] drf-spectacular: /api/reports/realtime/ en schema
[PASS] drf-spectacular: sin nuevas colisiones separation_rule
[DONE] 21/21 PASS
```

Nota: la verificación de `unique_together` en el script usó comparación de
listas contra tuplas de tuplas. El modelo es correcto —
`(('rule', 'version'),)` es la estructura de Django. El FAIL inicial fue
un error del script de verificación, no del modelo.
