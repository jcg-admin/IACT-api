# Hallazgos — Implementación STD_008 §3.3 FASE 4

**Artefacto:** HALLAZGOS-FASE4-STD008-SOD-20260513
**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Repositorio:** IACT-docs (directorio `/tmp/references/IACT-docs/`)
**Autor:** Nestor Monroy
**Estado:** Cerrado — todos los hallazgos resueltos

----

## Resumen ejecutivo

FASE 4 actualiza los documentos de requisitos (UCs) que referenciaban
identificadores técnicos con la abreviatura `SoD`. Los documentos fueron
escritos antes de STD_008 (aprobado 2026-04-28) y no se actualizaron
cuando el backend implementó los nuevos nombres en FASES 1-3.

| Métrica | Valor |
|---|---|
| UCs procesados | 10 |
| Archivos RST modificados | 66 |
| Líneas modificadas | 275 |
| Residuos de identificadores SOD tras FASE 4 | 0 |
| IDs de artefacto SOD-NNN preservados | ✓ |
| Narrativa "SoD" libre preservada | ✓ |

----

## Hallazgo H-004 — Alcance mayor al planeado

**Detectado en:** verificación inicial del inventario
**Impacto:** Ampliación de scope de 9 a 10 UCs, de 237 a 275 líneas

### Descripción

El análisis original (ANALISIS-CONSOLIDADO-STD008-SOD-20260513) identificó
9 UCs con 237 líneas afectadas. Al ejecutar el inventario preciso antes de
modificar, se encontraron más archivos y UCs:

| UC | Líneas planeadas | Líneas reales |
|---|---|---|
| uc-acc-01 | 52 | 64 |
| uc-acc-03 | 11 | 16 |
| uc-acc-04 | 16 | 21 |
| uc-acc-05 | 127 | 127 |
| uc-acc-08 | 12 | 13 |
| uc-acc-09 | 7 | 7 |
| uc-perm-01 | **no estaba en plan** | 2 |
| uc-perm-03 | 1 | 3 |
| uc-perm-06 | 10 | 21 |
| uc-perm-09 | 1 | 1 |

**Causa:** el análisis inicial usó un patrón de búsqueda más restrictivo
que pasó por alto algunas referencias. El script de FASE 4 usó el inventario
exacto obtenido antes de ejecutar los cambios.

El UC nuevo (`uc-perm-01`) tiene solo 2 referencias a `SoDValidator`
en `implementacion-tecnica.rst` — ambas son identificadores de clase en
pseudocode, correctamente en scope.

----

## Hallazgo H-005 — Discrepancias terminológicas entre docs y backend

**Detectado en:** comparación de event types en docs vs VALID_EVENT_TYPES del backend
**Impacto:** Los docs dicen `SOD_RULE_MODIFIED`/`SOD_RULE_RETIRED`; el backend
implementó `SEPARATION_RULE_UPDATED`/`SEPARATION_RULE_DISABLED`

### Descripción

Los documentos de UC_ACC_05 usan verbos de dominio (`MODIFIED`, `RETIRED`)
mientras la implementación de FASE 3 usó verbos técnicos de estado del modelo
(`UPDATED`, `DISABLED`) para los event types:

| En los UCs (antes) | En el backend FASE 3 | En los UCs (después) |
|---|---|---|
| `SOD_RULE_MODIFIED` | `SEPARATION_RULE_UPDATED` | `SEPARATION_RULE_UPDATED` |
| `SOD_RULE_RETIRED` | `SEPARATION_RULE_DISABLED` | `SEPARATION_RULE_DISABLED` |

**Causa:** Los UCs se escribieron antes de la implementación y usaron el
lenguaje del negocio. La implementación en FASE 3 usó el vocabulario del
modelo Django (`UPDATED` para PATCH, `DISABLED` para baja lógica con
`state=DISABLED`).

**Decisión:** Alinear los docs con la implementación. Los event types son
valores que van al audit log real — la implementación es la fuente de verdad.
Los UCs deben reflejar lo que el sistema realmente emite, no la terminología
original del análisis.

**Archivos afectados por esta discrepancia:**

```
access/uc-acc-05/actores-precondiciones.rst  (×2)
access/uc-acc-05/criterios-aceptacion.rst    (×1 RETIRED)
access/uc-acc-05/datos-involucrados.rst      (×2)
access/uc-acc-05/flujo-principal.rst         (×2)
access/uc-acc-05/implementacion-tecnica.rst  (×1 RETIRED)
access/uc-acc-05/requisitos-no-funcionales.rst (×3)
access/uc-acc-05/testing.rst                 (×1 RETIRED)
access/uc-acc-09/datos-involucrados.rst      (×2)
```

----

## Tabla maestra de sustituciones aplicadas

### URLs

| Antes | Después |
|---|---|
| `/api/access/sod-rules/` | `/api/access/separation-rules/` |
| `sod-rules/` | `separation-rules/` |

### Error codes HTTP

| Antes | Después | UCs |
|---|---|---|
| `SOD_VIOLATION` | `SEPARATION_RULE_VIOLATION` | uc-acc-01, uc-acc-04, uc-acc-08, uc-perm-09 |
| `CASCADE_SOD_VIOLATION` | `CASCADE_SEPARATION_RULE_VIOLATION` | uc-perm-06 |
| `SOD_RULE_DUPLICATE` | `SEPARATION_RULE_DUPLICATE` | uc-acc-05 |
| `SOD_RULE_NOT_FOUND` | `SEPARATION_RULE_NOT_FOUND` | uc-acc-05 |
| `SOD_RULE_ALREADY_RETIRED` | `SEPARATION_RULE_ALREADY_RETIRED` | uc-acc-05 |
| `SOD_RULE_CREATE_FAILED` | `SEPARATION_RULE_CREATE_FAILED` | uc-acc-05 |

### Event types (audit)

| Antes | Después | Nota |
|---|---|---|
| `SOD_RULE_CREATED` | `SEPARATION_RULE_CREATED` | Implementado en FASE 3 |
| `SOD_RULE_MODIFIED` | `SEPARATION_RULE_UPDATED` | H-005: backend usa UPDATED |
| `SOD_RULE_RETIRED` | `SEPARATION_RULE_DISABLED` | H-005: backend usa DISABLED |
| `SOD_RULES_VIEWED` | `SEPARATION_RULES_VIEWED` | Consistente con patrón |
| `SOD_RULE_*` (wildcard) | `SEPARATION_RULE_*` | En listas y referencias |

### Nombres de clase / servicio (en pseudocode y contratos técnicos)

| Antes | Después |
|---|---|
| `SoDRule` | `SeparationRule` |
| `SoDRuleRepository` | `SeparationRuleRepository` |
| `SoDRuleService` | `SeparationRuleService` |
| `SoDRuleCache` | `SeparationRuleCache` |
| `SoDRuleRepo` | `SeparationRuleRepo` |
| `SoDValidator` | `DutySeparationValidator` |
| `CascadeSoDValidator` | `CascadeDutySeparationValidator` |
| `SoDRuleDuplicate` | `SeparationRuleDuplicate` |
| `SoDRuleNotFound` | `SeparationRuleNotFound` |
| `SoDRuleAlreadyRetired` | `SeparationRuleAlreadyRetired` |
| `SoDRuleAlreadyExists` | `SeparationRuleAlreadyExists` |
| `CreateSoDRuleOutput` | `CreateSeparationRuleOutput` |
| `CascadeSoDViolation` | `CascadeSeparationRuleViolation` |

### Nombres de procedimiento (en pseudocode)

| Antes | Después |
|---|---|
| `create_sod_rule(...)` | `create_separation_rule(...)` |
| `retire_sod_rule(...)` | `retire_separation_rule(...)` |

### Campos de response (en ejemplos JSON)

| Antes | Después |
|---|---|
| `"sod_rules_evaluated": 5` | `"separation_rules_evaluated": 5` |
| `sod_rules_evaluated_count` | `separation_rules_evaluated_count` |
| `sod_rules_count` | `separation_rules_count` |
| `sod_rules` (variable) | `separation_rules` |
| `sod_rule` (field) | `separation_rule` |

----

## Lo que NO cambió en FASE 4

### Narrativa libre con "SoD" (STD_008 §3.3 — permanente)

El texto narrativo que usa "SoD" como concepto de dominio se preservó
integralmente. Ejemplos de líneas que NO se modificaron:

```
testing.rst:125:  12.2.9 SoD bloquea total (CA-05, CA-06)
testing.rst:285:  12.3.8 SoD violation 409 (CA-05)
testing.rst:302:  GIVEN payload con 3 funciones, 1 viola SoD
testing.rst:384:  - nombre de la regla SoD
```

STD_008 §3.3 permite `SoD` en narrativa cuando está definido en el glosario
del proyecto (glosario.rst línea 99).

### IDs de artefacto SOD-NNN (STD_008 §2 — excluidos de forma permanente)

`SOD-001`, `SOD-002`, `SOD-003` no aparecen en los directorios de casos-uso
(están en `normativa/restricciones/` y `arquitectura-tecnica/rbac/`). No
requirieron protección especial en este script.

----

## Verificación post-ejecución

```
CRITERIO 1 — Residuos de identificadores SOD en UCs afectados: 0 líneas
CRITERIO 2 — IDs de artefacto SOD-NNN preservados: ✓ (0 en casos-uso)
CRITERIO 3 — Narrativa "SoD" libre preservada: ✓ (8+ líneas intactas)
```

----

## Estado final de la remediación STD_008 IACT-api

Con FASE 4, el estado del plan completo en IACT-api es:

| FASE | Commit | Violaciones antes | Violaciones después |
|---|---|---|---|
| FASE 1 | `d366f58` | 78 | 44 |
| FASE 2 | `bd3201e` | 44 | 44 (net neutral) |
| FASE 3 | `16d57ac` | 44 | 30 |
| Total IACT-api | — | 78 | 30 |

Las 30 violaciones residuales en IACT-api son todas narrativa, historial
de renombres, URLs legacy backward-compat, o migraciones inmutables.
Ninguna es un identificador técnico violador de STD_008 §3.3.

En IACT-docs, las 275 líneas modificadas en los 10 UCs quedan en 0
violaciones de identificadores.
