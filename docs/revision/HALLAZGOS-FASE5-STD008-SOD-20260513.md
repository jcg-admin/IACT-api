# Hallazgos — Implementación STD_008 §3.3 FASE 5

**Artefacto:** HALLAZGOS-FASE5-STD008-SOD-20260513
**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Commit de cierre:** `cb51b2e` en rama `refactor/std008-sod-naming`
**Autor:** Nestor Monroy
**Estado:** Cerrado — remediación STD_008 §3.3 completada

----

## Resumen ejecutivo

FASE 5 ejecuta la verificación final de la remediación completa. Todos los
criterios de Done del plan se cumplen sin excepciones. No se encontró
deuda técnica nueva durante la verificación.

| Criterio | Resultado |
|---|---|
| Violaciones IACT-api (identificadores) | 30 residuales — todas clasificadas |
| Violaciones IACT-docs (identificadores) | 0 |
| URL `separation-rules/` canónica | Activa y funcional |
| URL `sod-rules/` | Eliminada (NoReverseMatch) |
| URL `separation-rules/validate` | Implementada y funcional |
| Error codes `SEPARATION_RULE_*` | Correctos en todos los endpoints |
| Event types `SEPARATION_RULE_*` | Correctos en VALID_EVENT_TYPES |
| `related_name separation_rules_as_set_a/b` | Accesibles via ORM |
| `related_name sod_rules_as_set_a/b` | Eliminados (AttributeError) |
| `makemigrations access --check` | Sin cambios pendientes |
| drf-spectacular — `Field name` warnings | 0 |
| drf-spectacular — colisiones `separation_rule_*` | 0 |
| Test e2e completo (10 criterios) | 10/10 PASS |

----

## T-5.1 — Verificación automática IACT-api

**Resultado: 30 líneas residuales — todas correctamente clasificadas**

Las 30 líneas que permanecen en IACT-api no son violaciones de STD_008 §3.3
sino referencias en categorías excluidas:

| Archivo | Líneas | Categoría | Justificación |
|---|---|---|---|
| `access/models.py` | 7 | Narrativa permanente | verbose_name `'Regla SoD'`, `__str__` "SoD {code}", docstrings de método |
| `access/migrations/0005_fase0_schema_canonico.py` | 5 | Inmutable histórico | Migración aplicada: nunca se edita. Los `related_name` son superados por 0008 |
| `access/urls.py` | 4 | Historial + backward compat | Módulo docstring historial (×2) + `validate-sod` path backward compat (×2) |
| `access/management/commands/create_access_groups.py` | 4 | Narrativa permanente | Strings de descripción de grupos AGR: "SoD: sin AUD." |
| `access/function_assign_view.py` | 4 | Narrativa permanente | Docstrings de módulo y clase: "SoD check", historial de renombre FASE 1 |
| `access/views.py` | 3 | Backward compat strings | Docstrings de `validate-sod` legacy |
| `access/migrations/0008_std008_fase2_related_names.py` | 2 | Narrativa en migración | verbose_name + nombre de artefacto documental |
| `audit/models.py` | 1 | Historial de trazabilidad | Comentario `# STD_008 FASE 3: SOD_RULE_* → SEPARATION_RULE_*` |

**Aplicabilidad de STD_008 §3.3:**

> "Las abreviaturas pueden usarse en narrativa **solo cuando estén definidas
> previamente en el glosario del proyecto**."

`SoD` figura en `glosario.rst` línea 99. Las 30 referencias residuales son
narrativa o artefactos inmutables — ninguna es un identificador técnico activo.

----

## T-5.2 — Verificación automática IACT-docs

**Resultado: 0 violaciones**

```bash
$ grep -rn "SOD_VIOLATION|SOD_RULE_|CASCADE_SOD|SoDRule|sod_rule|SoDValidator|
             sod-rules|sod_rules_evaluated|CascadeSoD" \
    source/requisitos/casos-uso/ --include="*.rst" \
    | grep -v "SOD-00[0-9]" | wc -l
0
```

----

## T-5.3 — Test de regresión funcional end-to-end

**Resultado: 10/10 PASS**

```
[PASS] T-5.3.A: URL canónica → /api/access/separation-rules/
[PASS] T-5.3.A: sod-rules/ → NoReverseMatch (eliminada correctamente)
[PASS] T-5.3.B: POST separation-rules/ → 201
[PASS] T-5.3.B: AuditEvent SEPARATION_RULE_CREATED (no SOD_RULE_CREATED)
[PASS] T-5.3.B: GET  separation-rules/ → 200
[PASS] T-5.3.B: GET  separation-rules/{id}/ → 200
[PASS] T-5.3.B: PATCH → 200, AuditEvent SEPARATION_RULE_UPDATED
[PASS] T-5.3.C: duplicado → 409 SEPARATION_RULE_DUPLICATE
[PASS] T-5.3.C: no encontrado → 404 SEPARATION_RULE_NOT_FOUND
[PASS] T-5.3.D: violación separación → 409 SEPARATION_RULE_VIOLATION
[PASS] T-5.3.E: separation-rules/validate → 200, conflicto detectado
[PASS] T-5.3.E: validate-sod legacy → 200 (mismo resultado)
[PASS] T-5.3.F: VALID_EVENT_TYPES correctos (SEPARATION_RULE_*)
[PASS] T-5.3.G: related_name separation_rules_as_set_a/b funcional
[PASS] T-5.3.H: makemigrations access --check: sin cambios pendientes
[PASS] T-5.3.I: drf-spectacular schema limpio
[PASS] T-5.3.J: DELETE → 200 DISABLED, AuditEvent SEPARATION_RULE_DISABLED
[DONE] T-5.3 — Test e2e FASE 5 completo. Todos los criterios pasan.
```

### Schema OpenAPI resultante (paths de separación)

```yaml
paths:
  /api/access/separation-rules/:
    get:
      operationId: separation_rule_list
    post:
      operationId: separation_rule_create

  /api/access/separation-rules/{rule_id}/:
    get:
      operationId: separation_rule_retrieve
    patch:
      operationId: separation_rule_partial_update
    delete:
      operationId: separation_rule_destroy

  /api/access/separation-rules/validate:
    post:
      operationId: separation_rule_validate
```

- `sod-rules/` no aparece en el schema.
- `validate-sod` no aparece en el schema (excluido con `@extend_schema(exclude=True)`).
- Sin colisiones de `operationId`.
- Sin warnings de `Field name`.

----

## T-5.4 — Deuda técnica residual documentada

Las siguientes piezas de trabajo se documentan pero NO bloquean la
finalización de la remediación STD_008 §3.3.

### DT-STD008-001 — Inconsistencia de nombre de clase entre artefactos canónicos

CNST-033, modelo-rbac-iact.rst y el modelo Django definen el nombre de
la clase con tres valores distintos:

| Fuente | Nombre |
|---|---|
| CNST-033 | `SeparationOfDutiesRule` |
| modelo-rbac-iact.rst | `FunctionSeparationRule` |
| Django actual | `SeparationRule` |

`SeparationRule` no viola STD_008 §3.3 (no contiene la abreviatura `SoD`),
por lo que no fue en scope de esta remediación. La unificación entre los
tres artefactos requiere un ADR formal y `RenameModel` en Django.

**Registrar en:** `risks-technical-debt/deuda-tecnica-rebuild.rst`

### DT-STD008-002 — Codenames legacy con `sod` en tokens JWT

`catalog.js` de IACT-ui usa `'access:view_sod'`, `'adm:create_sod'`,
`'access:update_sod'`, `'access:disable_sod'` como codenames de permiso.
Estos son los `permission_django` del modelo `Function` emitidos en los
tokens JWT.

Cambiarlos requiere:
- ADR formal (afecta autenticación de todos los usuarios)
- Rotación de tokens activos
- Actualización coordinada de IACT-api + IACT-ui

**Registrar en:** `risks-technical-debt/deuda-tecnica-rebuild.rst`

### DT-STD008-003 — Endpoint y clase legacy pendientes de eliminación

`SeparationRuleViewSet` y `SeparationRuleValidateLegacyView` en `views.py`
pueden eliminarse cuando se confirme que `validate-sod` no tiene consumidores
externos. La clase ViewSet está marcada `deprecated=True` en el schema.

**Acción requerida:** confirmar ausencia de consumidores, entonces PR de limpieza.

----

## Resumen completo de la remediación STD_008 §3.3

### Commits en `refactor/std008-sod-naming`

| Commit | Tipo | Descripción |
|---|---|---|
| `d366f58` | refactor | FASE 1 — renombres internos SoD (78 → 44 violaciones) |
| `bd3201e` | refactor | FASE 2 — migración related_names (44 → 44, net neutral) |
| `16d57ac` | fix | FASE 3 — contrato público + bugs integración (44 → 30) |
| `cb51b2e` | docs | FASE 5 — verificación y cierre + documentación serie |

### Violaciones por fase

| Fase | Antes | Después | Delta |
|---|---|---|---|
| Baseline IACT-api | 78 | — | — |
| FASE 1 | 78 | 44 | −34 |
| FASE 2 | 44 | 44 | 0 (net) |
| FASE 3 | 44 | 30 | −14 |
| IACT-docs FASE 4 | 275 | 0 | −275 |

### Hallazgos descubiertos durante la implementación

| ID | Fase | Descripción | Resolución |
|---|---|---|---|
| H-001 | 1 | `SeparationRuleViewSet` + `SeparationRuleSerializer` rotos en runtime (campos v5.2.1) | Corregido en FASE 1 |
| H-002 | 2 | 22 cambios de modelo sin migración (`help_text`, `verbose_name`) | Consolidados en migración 0008 |
| H-003 | 3 | `SeparationRuleValidateView.post()` usa campos inexistentes → FieldError en runtime | Reescrita con lógica M2M |
| H-003b | 3 | Colisión `operationId separation_rule_validate` al registrar vista en dos URLs | `SeparationRuleValidateLegacyView(exclude=True)` |
| H-004 | 4 | Alcance mayor al planeado (9 → 10 UCs, 237 → 275 líneas) | Procesados todos |
| H-005 | 4 | `SOD_RULE_MODIFIED/RETIRED` en docs vs `SEPARATION_RULE_UPDATED/DISABLED` en backend | Docs alineados con backend |
