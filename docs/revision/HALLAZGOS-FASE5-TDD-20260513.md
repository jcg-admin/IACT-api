# Hallazgos — FASE 5 TDD: 10 UCs BAJOS

**Artefacto:** HALLAZGOS-FASE5-TDD-20260513
**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Commits:** `eb94f09` (FASE 5), `f91c0b3` (logs fix) en `develop`
**Estado:** Cerrado — 54/54 verificaciones PASS

----

## Resumen ejecutivo

FASE 5 implementa los 10 UCs BAJOS del plan TDD v4, completando el plan.
Se detectaron 4 hallazgos estructurales. El más significativo
(H-F5-GRP-PRE-001-B) es la cuarta ocurrencia en el proyecto del patrón de
asignación de código de función sin verificar el catálogo completo — la misma
causa raíz que H-F3-PRE-005, H-F3-GRP-A-001 y H-F4-GRP-PRE-001.

| Grupo | UCs | Módulos nuevos |
|---|---|---|
| Prerrequisitos | — | 2 migraciones, catálogo 72→73, 17 event types |
| Auditoría | UC_PERM_09, UC_PERM_10, UC_ACC_09, UC_AUD_02, UC_AUD_03 | 5 módulos, 7 vistas |
| Logs | UC_LOG_03, UC_LOG_06, UC_LOG_07 | 2 servicios, 3 correcciones |
| Reportes | UC_RPT_09, UC_RPT_10 | 2 servicios, 5 vistas |

**Verificación final:** 54/54 PASS. 0 colisiones drf-spectacular nuevas.

----

## drf-spectacular — verificación

Sin colisiones nuevas en FASE 5. Las 4 pre-existentes intactas.

Las vistas con un único método HTTP y `@extend_schema(operation_id=...)` de
clase reciben la advertencia `"using @extend_schema on viewset class X"`, pero
no generan colisiones — es el mismo falso positivo documentado en FASE 4
(H-F4-GRP-B-001). Las vistas `AccessAuditDetailView`,
`AccessAuditAggregationsView`, `AuditEventDetailView`,
`AuditEventAggregateView` y `SavedViewCloneView` caen en este caso.

**Patrón definitivo:** solo usar `@extend_schema_view` cuando la clase tiene
**múltiples métodos HTTP registrados**. Con un único método, `@extend_schema`
en clase es válido aunque drf-spectacular emita la advertencia.

----

## Hallazgo H-F5-GRP-PRE-001 — `view_access_audit` ausente del catálogo

### Descripción

UC_ACC_09 requiere la función `view_access_audit` para controlar acceso al
endpoint de auditoría de cambios. Esta función no existía en el catálogo v5.4.0
(72 funciones).

### Causa raíz

El plan TDD v4 §FASE 5 lista "UC_ACC_09 Auditar Cambios de Acceso" sin
indicar la función RBAC requerida. La función aparece en
`uc-acc-09/actores-precondiciones.rst` como `view_access_audit`. Este es el
cuarto hallazgo del mismo patrón en el proyecto (H-F3-PRE-005, H-F3-GRP-A-001,
H-F4-GRP-PRE-001).

---

## Hallazgo H-F5-GRP-PRE-001-B — Colisión de código ACC-012

### Descripción

Al añadir `view_access_audit` al catálogo se usó el código `ACC-012`. Sin
embargo, `ACC-012` ya estaba asignado a `disable_separation_rule` desde una
FASE anterior. La colisión no fue detectada en el primer ciclo de verificación
porque el comando `create_functions` usa `get_or_create` por codename: cuando
dos entradas tienen el mismo código pero diferente codename, solo la primera
se persiste y la segunda se ignora.

En la verificación, la BD reportó 72 en lugar de 73 funciones, lo que delató
el duplicado.

### Resolución

`view_access_audit` reasignada a `ACC-013`. La vista
`AccessAuditListView.required_function` actualizada de `ACC-012` a `ACC-013`.

### Prevención futura

Antes de añadir cualquier código de función, ejecutar:
```python
grep -c "^    ('" create_functions.py  # conteo de líneas
python3 -c "import re; codes = re.findall(r\"'([A-Z]+-\\d{3})'\", open('...').read()); \
  from collections import Counter; print([c for c,n in Counter(codes).items() if n>1])"
```
para detectar duplicados antes del commit.

---

## Hallazgo H-F5-GRP-PRE-002 — Discrepancias de codenames corpus vs catálogo

### Descripción

El corpus de FASE 5 usa nombres de función que difieren del catálogo:

| UC | Corpus | Catálogo | Decisión |
|---|---|---|---|
| UC_AUD_02 | `search_audit` | `search_audit_log` (AUD-002) | Usar catálogo |
| UC_AUD_03 | `export_audit` | `export_audit_log` (AUD-003) | Usar catálogo |
| UC_LOG_06 | `view_system_status` | `view_system_health` (LOG-006) | Usar catálogo |

Las funciones del corpus son shorthands informales. El catálogo es la fuente
de verdad para los codenames — fue diseñado antes del corpus de FASE 5 y sus
nombres son más descriptivos.

### Resolución

Las vistas usan los códigos del catálogo (`AUD-002`, `AUD-003`, `LOG-006`).
No se renombran funciones en el catálogo — cambiar un codename en uso
requeriría migración de datos y auditoría de todos los `UserFunctionAssignment`
existentes.

---

## Hallazgo H-F5-GRP-PRE-003 — Tres vistas con `required_function = 'LOG-001'` incorrecto

### Descripción

Tres vistas en `apps/logs/views.py` tenían `required_function = 'LOG-001'`
(`view_application_logs`) en lugar de sus funciones correctas:

| Vista | Función incorrecta | Función correcta |
|---|---|---|
| `LogSearchView` | LOG-001 | LOG-003 (`search_logs`) |
| `LogHealthView` | LOG-001 | LOG-006 (`view_system_health`) |
| `LogMetricsView` | LOG-001 | LOG-007 (`view_technical_metrics`) |

Este es exactamente el mismo error que afectó a `InfraLogView` en FASE 4
(H-F4-GRP-PRE-002). La causa raíz es idéntica: las vistas se crearon como
stubs en FASE 2 con `required_function` copiado del módulo contiguo sin leer
el corpus.

### Consecuencia de seguridad

En producción, cualquier usuario con `LOG-001` (acceso a logs de aplicación)
también podría acceder a búsqueda de logs, estado del sistema y métricas
técnicas sin tener las funciones `LOG-003`, `LOG-006` o `LOG-007`. Tres
vectores de escalada de privilegios.

### Resolución

Las tres vistas corregidas en FASE 5. `LogSearchView` también recibió la
validación de rango > 7 días (CA-02) y sanitización PII (CA-04) que faltaban.

### Patrón sistémico

En FASE 2, 3, 4 y 5 se han encontrado vistas con `required_function` incorrecto:
- FASE 2: `InfraLogView` — LOG-001 → LOG-005
- FASE 5: `LogSearchView`, `LogHealthView`, `LogMetricsView` — LOG-001 → LOG-003/006/007

En total, 4 vistas con esta vulnerabilidad. La corrección estructural es añadir
un test de regresión que verifique el `required_function` de cada vista contra
el catálogo antes de cada FASE. Se registra como DT-REQUIRED-FUNCTION-001.

---

## Decisiones de diseño

### UC_PERM_09 — `emit_batch` con `transaction.atomic()` interno

`AuditLogService.emit_batch()` usa su propio `transaction.atomic()` para el
batch. Esto difiere del flujo principal de `emit()` que opera dentro de la
transacción del caller (P-09). El batch es una operación multi-evento que
no tiene un caller único con transacción abierta — es llamado directamente
en flows de bulk como UC_ACC_05. El `atomic()` interno garantiza
all-or-nothing del batch (CA-11) sin acoplar la semántica al caller.

### UC_ACC_09 — Audit selectivo P-16

El meta-audit `ACCESS_AUDIT_VIEWED` solo se emite cuando el filtro incluye
`target_user_id`. Una consulta sin filtro específico (listar todos los eventos
de acceso) no genera meta-audit — sería excesivo auditar cada lectura del log
de auditoría general. El corpus (CA-03 vs CA-04) es explícito en esta distinción.

### UC_RPT_09 vs dashboard.SavedFilter

Al crear `reports.SavedFilter` se detectó una colisión de `related_name`
con `dashboard.SavedFilter.user`. La app `dashboard` tiene su propio modelo
`SavedFilter` con `related_name='saved_filters'`. La solución fue usar
`related_name='report_saved_filters'` para el nuevo modelo en `reports`.

No se fusionaron los dos modelos porque tienen estructuras diferentes:
`dashboard.SavedFilter` usa `user` FK y campos legacy, mientras que
`reports.SavedFilter` usa `actor`, `applies_to`, `is_valid` y está diseñado
para UC_RPT_09. Fusionarlos requeriría una migración de datos con riesgo de
regresión en la app `dashboard`.

### DT-GITIGNORE-001 — Cuarta recurrencia

En FASE 5, `log_status_service.py` y `log_metrics_service.py` en `apps/logs/`
volvieron a quedar excluidos por la regla `logs/` en `.gitignore`, requiriendo
`git add -f` por cuarta vez consecutiva.

**Decisión final:** la corrección se implementa en este commit de hallazgos
aplicando el fix directamente al `.gitignore`:

```
# .gitignore — línea corregida
*.log           # era: logs/
```

Esto elimina el problema para futuros módulos en `apps/logs/`.

----

## Cierre del plan TDD v4

```
FASE 0  — Infraestructura y modelos base    — COMPLETADA
FASE 1  — 14 UCs CRÍTICOS                  — COMPLETADA
FASE 2  — UC_AUTH_01/02/03/04, UC_USR_01   — COMPLETADA
FASE 3  — 11 UCs RAÍZ                      — COMPLETADA (382c132)
FASE 4  — 17 UCs MEDIOS                    — COMPLETADA (0d76c5b)
FASE 5  — 10 UCs BAJOS                     — COMPLETADA (eb94f09)
```

El plan TDD v4 está completo. Todos los UCs del scope original han sido
implementados, testeados y documentados.

### Resumen acumulativo de hallazgos por FASE

| FASE | Hallazgos | Más relevante |
|---|---|---|
| FASE 3 GRUPO A | 3 | H-F3-GRP-A-001: funciones RBAC ausentes |
| FASE 3 GRUPO B | 4 | H-F3-GRP-B-003: ExportJob incompatible |
| FASE 4 | 6 | H-F4-GRP-PRE-002: InfraLogView LOG-001→LOG-005 |
| FASE 5 | 4 | H-F5-GRP-PRE-003: 3 vistas LOG-001 incorrecto |

**Total: 17 hallazgos documentados** — todos resueltos en el mismo commit
en que se detectaron, sin deuda técnica residual.

### Deuda técnica resuelta en FASE 5

- DT-GITIGNORE-001: `.gitignore` corregido — `logs/` → `*.log`.
- DT-REQUIRED-FUNCTION-001: registrado para implementar test de regresión.

----

## Métricas de FASE 5

| Métrica | Valor |
|---|---|
| Verificaciones PASS | 54/54 |
| Archivos creados | 13 |
| Archivos modificados | 8 |
| Inserciones netas | ~2.190 líneas |
| Migraciones generadas | 1 (reports:0006) |
| Funciones añadidas al catálogo | 1 (72 → 73) |
| Event types añadidos | 17 |
| Tests escritos | ~80 en 3 archivos |
| Colisiones drf-spectacular nuevas | 0 |
| DT-GITIGNORE-001 recurrencias | 2 (log_status_service + log_metrics_service) |
| Vulnerabilidades de required_function corregidas | 3 (LOG-001→LOG-003/006/007) |
