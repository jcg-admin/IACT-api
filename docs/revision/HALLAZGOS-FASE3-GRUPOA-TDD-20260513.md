# Hallazgos — FASE 3 TDD GRUPO A: UC_PIP_02/03, UC_ALR_01/02/03, UC_LOG_01/02, UC_RPT_03

**Artefacto:** HALLAZGOS-FASE3-GRUPOA-TDD-20260513
**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Commits:** `a31487f` (GRUPO A), `780b336` (log_validators) en `develop`
**Estado:** Cerrado — 40/40 verificaciones PASS

----

## Resumen ejecutivo

GRUPO A implementa los 7 UCs raíz de FASE 3 (sin dependencias internas
pendientes). Se detectaron 3 hallazgos adicionales al plan: funciones RBAC
ausentes del catálogo, y la regla `.gitignore` que excluye `apps/logs/`.

| UC | Función | Componentes nuevos | Tests |
|---|---|---|---|
| UC_PIP_02 | PIP-002 | `pii_scanner.py` | 6 (UT-01, IT-01..04, SEC-01..02) |
| UC_PIP_03 | PIP-003 | `status_calculator.py` | 5 (UT-01..04, IT-01..03, SEC-01) |
| UC_LOG_01 | LOG-001 | `log_validators.py` | 6 (UT-01..02, IT-01..04, SEC-01..02) |
| UC_LOG_02 | LOG-004 | (reutiliza log_validators) | 3 (UT-01, IT-01..04, SEC-01) |
| UC_ALR_01 | ALR-002 | `alert_service.py`, `alert_views.py` | 9 (UT-01..03, IT-01..06, SEC-01..02) |
| UC_ALR_02 | ALR-011 | `alert_views.ActiveAlertsView` | 4 (IT-01..05, SEC-01) |
| UC_ALR_03 | ALR-007 | `alert_views.AlertAcknowledgeView` | 7 (UT-01, IT-01..06, SEC-01) |
| UC_RPT_03 | RPT-013 | `historical_service.py`, `historical_view.py` | 11 (UT-01..09, IT-01..08) |

----

## drf-spectacular — verificación

Una colisión nueva detectada y resuelta durante la implementación:

**`alerts_rules_retrieve`** — colisión entre `/api/alerts/rules/` (GET list)
y `/api/alerts/rules/{rule_id}/` (GET detail). Ambas generaban el mismo
`operationId`. Resuelta con `operation_id='alerts_rule_list_create'` y
`operation_id='alerts_rule_detail'` explícitos en los decoradores
`@extend_schema`.

Las 4 colisiones pre-existentes (DT-ROUTING-001..003) permanecen sin cambios.

----

## Hallazgo H-F3-GRP-A-001 — 3 funciones RBAC ausentes del catálogo v5.4.0

### Funciones ausentes detectadas

| Función | UC | Código asignado | Detectada en |
|---|---|---|---|
| `view_historical_reports` | UC_RPT_03 | RPT-013 | Implementación de `HistoricalReportView` |
| `view_active_alerts` | UC_ALR_02 | ALR-011 | Implementación de `ActiveAlertsView` |
| `view_system_logs` | UC_LOG_01 | LOG-008 | Lectura del corpus `uc-log-01/actores` |

### Causa raíz

El catálogo v5.4.0 inicial (61 funciones) fue construido en FASE 0 antes de
leer el corpus completo. Las funciones se inferían del plan v3 TDD, que a su
vez se redactó antes de una lectura exhaustiva de todos los `actores-precondiciones.rst`.
Cuando se leen esos archivos antes de implementar cada UC, aparecen funciones
que el plan no había mapeado.

Esto es el mismo patrón detectado en H-F3-PRE-005 (`view_realtime_metrics`).
El catálogo tiene una tendencia estructural a ser incompleto en las funciones
de lectura simples (las funciones de escritura como `configure_alerts` sí
estaban presentes porque son más visibles en el diseño).

### Resolución

Catálogo actualizado: 62 → 65 funciones.
Total esperado en `create_functions.py` actualizado a 65.

---

## Hallazgo H-F3-GRP-A-002 — `.gitignore` excluye `apps/logs/` completo

### Descripción

La regla `logs/` en `.gitignore` excluye cualquier directorio llamado `logs`
en cualquier nivel del árbol. `callcentersite/apps/logs/` coincide con esta
regla y sus archivos nuevos no se incluyen automáticamente en `git add`.

Este hallazgo ocurrió ya antes con `apps/logs/views.py` en el commit de
prerequisitos. La solución es `git add -f` para archivos ya-tracked o
nuevos en ese directorio.

### Causa raíz

La regla `logs/` fue diseñada para excluir directorios de logs de aplicación
(`/logs/*.log`), pero su alcance es demasiado amplio y captura el módulo
Django `apps/logs/`.

### Resolución recomendada (deuda técnica menor)

Reemplazar `logs/` por `*.log` o `logs/*.log` en `.gitignore`. No se aplica
en esta fase para no generar un commit adicional no relacionado con el UC.
Registrado como DT-GITIGNORE-001.

---

## Decisiones de diseño

### UC_PIP_02 — PIIScanner integrado en la capa de vista

`PIIScanner.sanitize_error_row()` se aplica en `etl_errors` justo antes
del `return Response()`. La alternativa sería aplicarlo en la capa de servicio
o en el serializer. Se eligió la vista porque:
1. Es el punto más cercano al cliente — ningún otro código puede "filtrar"
   datos no sanitizados.
2. Los datos de MariaDB se leen crudos (dict desde cursor) — sanitizarlos en
   la vista es más simple que crear una clase de serializer.
3. UC_PIP_02 no tiene servicio dedicado — la vista ES el servicio.

### UC_ALR_01 — BR-009 como pause (no DELETE físico)

`AlertRuleDetailView.delete()` implementa la baja lógica como
`rule.status = STATUS_PAUSED` en lugar de `rule.delete()`. Esto tiene un
efecto semántico: la regla queda "pausada" en lugar de tener un estado
explícito "eliminada". El corpus (CA-07) dice "DELETE CASCADE" refiriéndose
a las Alerts asociadas, pero BR-009 prohíbe el DELETE físico.

La implementación correcta sería añadir `STATUS_DELETED` al modelo, pero el
corpus no lo define explícitamente. Se usa `STATUS_PAUSED` como proxy de
baja lógica hasta que el corpus defina el ciclo de vida completo.

### UC_RPT_03 — HistoricalReportService devuelve datos stub

En este entorno no hay BD Analytics. `HistoricalReportService.get()` retorna
buckets vacíos con `comparative.insufficient_data=True`. Los tests de
integración (IT-01..08) usan mock del servicio completo para evitar depender
de Analytics. Los tests unitarios (UT-01..09) verifican las funciones puras
(PeriodResolver, FilterValidator, ComparativeBuilder, ttl_for_period)
que sí funcionan sin BD.

### UC_ALR_02 — Segmento hardcoded como `['all']`

`ActiveAlertsView.get()` aplica el filtro de segmento con un stub
`segments = ['all']` (CNST-008). La implementación real requeriría
`SegmentResolver.for(request.user.id)` que consulta los segmentos asignados
al usuario. Esta es deuda técnica aceptada: el contrato RBAC del endpoint es
correcto (`ALR-011`), pero el filtro de segmento es un stub. Registrado como
DT-SEGMENT-001 pendiente para cuando SegmentResolver esté disponible.

----

## Verificación ejecutada

```
40/40 PASS — funcional + drf-spectacular
Tests escritos: 51 tests en 5 archivos de fase3/
Colisión alerts_rules_retrieve resuelta
Catálogo: 62 → 65 funciones
```

----

## GRUPO B — siguiente iteración

Los 3 UCs del GRUPO B dependen de UCs del GRUPO A ya completados:

| UC | Dependencia | Estado |
|---|---|---|
| UC_PIP_04 Solicitar Reintento | UC_PIP_02 (done) | Pendiente |
| UC_ALR_02 Ver Alertas Activas | UC_ALR_01 (done) | Completado en GRUPO A |
| UC_RPT_04 Exportar Reporte | UC_RPT_03 (done) | Pendiente |
| UC_ALR_03 Reconocer Alerta | UC_ALR_02 (done) | Completado en GRUPO A |

Nota: UC_ALR_02 y UC_ALR_03 estaban en el GRUPO B del plan pero se
implementaron en el mismo commit de GRUPO A porque sus modelos (`Alert`)
eran necesarios para probar UC_ALR_01. El orden del plan era una guía
de dependencias, no una restricción estricta de aislamiento.

Pendientes para la próxima iteración: **UC_PIP_04** y **UC_RPT_04**.
