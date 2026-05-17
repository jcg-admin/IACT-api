# Hallazgos — Implementación STD_008 §3.3 FASE 1

**Artefacto:** HALLAZGOS-FASE1-STD008-SOD-20260513
**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Commit:** `d366f58` en rama `refactor/std008-sod-naming`
**Autor:** Nestor Monroy
**Estado:** Cerrado — todos los hallazgos resueltos en este commit

----

## Resumen ejecutivo

FASE 1 se ejecutó sin deuda técnica residual. El scope original fue de
34 violaciones en 4 archivos. Durante la ejecución se descubrió y corrigió
un hallazgo adicional estructural (H-001) que afectaba al ViewSet legacy y
al serializer asociado, produciendo errores de runtime y warnings en
drf-spectacular.

| Métrica | Antes | Después |
|---|---|---|
| Violaciones STD_008 §3.3 en `.py` | 78 | 44 |
| Resueltas en FASE 1 | — | 34 |
| Archivos modificados | — | 6 |
| Tests de verificación | — | 9 PASS, 0 FAIL |
| Errores de runtime (H-001) | 2 | 0 |
| Warnings drf-spectacular | 1 | 0 |

----

## Cambios ejecutados

### Renombres de archivo

| Archivo anterior | Archivo nuevo | Mecanismo |
|---|---|---|
| `apps/access/sod_rule_view.py` | `apps/access/separation_rule_view.py` | `git mv` |
| `apps/access/management/commands/create_sod_rules.py` | `apps/access/management/commands/create_separation_rules.py` | `git mv` |

### Renombres de identificadores Python

| Identificador anterior | Identificador nuevo | Archivo |
|---|---|---|
| `class SoDRuleCreateSerializer` | `class SeparationRuleCreateSerializer` | `separation_rule_view.py` |
| `class SoDRulePatchSerializer` | `class SeparationRulePatchSerializer` | `separation_rule_view.py` |
| `class SoDRuleRetireSerializer` | `class SeparationRuleRetireSerializer` | `separation_rule_view.py` |
| `class SoDRuleListCreateView` | `class SeparationRuleListCreateView` | `separation_rule_view.py` |
| `class SoDRuleDetailView` | `class SeparationRuleDetailView` | `separation_rule_view.py` |
| `class SoDValidator` | `class DutySeparationValidator` | `function_assign_view.py` |
| `SOD_RULES_V540` | `SEPARATION_RULES_V540` | `create_separation_rules.py` |

### Actualizaciones derivadas

| Qué | Dónde | Por qué |
|---|---|---|
| Import `from .sod_rule_view import SoDRule*` | `urls.py` línea 22 | módulo renombrado |
| `SoDRuleListCreateView.as_view()` en `path()` | `urls.py` línea 79 | clase renombrada |
| `SoDRuleDetailView.as_view()` en `path()` | `urls.py` línea 81 | clase renombrada |
| `SoDValidator.validate(...)` ×2 | `function_assign_view.py` líneas 148, 373 | clase renombrada |
| `SoDRuleCreateSerializer(...)` en `post()` | `separation_rule_view.py` | clase renombrada |
| `SoDRulePatchSerializer(...)` en `patch()` | `separation_rule_view.py` | clase renombrada |
| `SoDRuleRetireSerializer(...)` en `delete()` | `separation_rule_view.py` | clase renombrada |
| `help` del `Command` | `create_separation_rules.py` | texto descriptivo del comando |
| `for ... in SOD_RULES_V540:` | `create_separation_rules.py` | constante renombrada |

----

## Lo que no cambió en FASE 1 — y por qué

### Contrato público (FASE 3)

Estos identificadores se mantienen idénticos porque son parte del contrato
HTTP de la API. Cambiarlos ahora sin sincronizar con los consumidores
(audit, tests, IACT-ui) crearía una rotura de contrato sin coordinación.

| Identificador | Archivo | Descripción |
|---|---|---|
| `'sod-rules/'` | `urls.py` | URL path — FASE 3 |
| `name='sod-rule-list-create'` | `urls.py` | URL name — FASE 3 |
| `name='sod-rule-detail'` | `urls.py` | URL name — FASE 3 |
| `path('validate-sod', ...)` | `urls.py` | URL legacy — FASE 3 |
| `'error': 'SOD_RULE_DUPLICATE'` | `separation_rule_view.py` | error code — FASE 3 |
| `'error': 'SOD_RULE_NOT_FOUND'` | `separation_rule_view.py` (×3) | error code — FASE 3 |
| `event_type='SOD_RULE_CREATED'` | `separation_rule_view.py` | event type — FASE 3 |
| `event_type='SOD_RULE_UPDATED'` | `separation_rule_view.py` | event type — FASE 3 |
| `event_type='SOD_RULE_DISABLED'` | `separation_rule_view.py` | event type — FASE 3 |
| `'error': 'SOD_VIOLATION'` (×2) | `function_assign_view.py` | error code — FASE 3 |
| `'reason': 'sod_violation'` | `function_assign_view.py` | payload field — FASE 3 |
| `SOD_RULE_CREATED/UPDATED/DISABLED` | `audit/models.py` VALID_EVENT_TYPES | event type — FASE 3 |

### IDs de artefacto (STD_008 §2 — excluidos de forma permanente)

`SOD-001`, `SOD-002`, `SOD-003` en `SEPARATION_RULES_V540` no cambian
nunca. STD_008 §2 los excluye explícitamente: "NO aplica a IDs de
artefactos de documentación".

### Migración de BD (FASE 2)

`related_name='sod_rules_as_set_a'` y `related_name='sod_rules_as_set_b'`
en `models.py` requieren migración `AlterField`. Se tocan en FASE 2.

La migración `0005_fase0_schema_canonico.py` es inmutable por convención
de Django — nunca se edita una migración aplicada.

### Narrativa permitida (STD_008 §3.3 — permanente)

STD_008 §3.3 establece: "Las abreviaturas pueden usarse en narrativa
solo cuando estén definidas previamente en el glosario del proyecto."
`SoD` figura en `glosario.rst` línea 99.

Los siguientes elementos son narrativa y **no cambian en ninguna fase**:

| Dónde | Texto | Tipo |
|---|---|---|
| `function_assign_view.py` docstring módulo | `"con SoD check"` | narrativa |
| `function_assign_view.py` comment | `# CA-05/06: validar SoD` | narrativa |
| `function_assign_view.py` `@extend_schema` | `"validación SoD (BR-007)"` | narrativa de contrato actual |
| `create_access_groups.py` ×4 | `"SoD: sin AUD."` etc. | descripción de grupos en string |
| `models.py` verbose_name | `'Regla SoD'`, `'Reglas SoD'` | verbose_name Django (UI) |
| `models.py` docstrings | referencias a "SoD" | narrativa técnica |

### drf-spectacular — @extend_schema summaries (FASE 3)

Los `summary` de `@extend_schema` en `separation_rule_view.py` que dicen
"reglas SoD" son narrativa de la documentación del endpoint — se actualizan
en FASE 3 cuando cambie la URL para mantener coherencia con el nuevo path.

----

## Hallazgo H-001 — Descubierto durante T-1.6

**Severidad:** Alta (errores de runtime, no solo naming)
**Archivo afectado:** `separation_rule_serializers.py`, `views.py`
**Resuelto en:** este mismo commit (dentro de FASE 1)

### Descripción

Al ejecutar la verificación de drf-spectacular en T-1.6, se detectó:

```
Field name `function_a` is not valid for model `SeparationRule`.
```

La investigación reveló que `SeparationRuleSerializer` y
`SeparationRuleViewSet` en el código legacy (`views.py`) referenciaban
campos del modelo v5.2.1 que ya no existen en `SeparationRule` v5.4.0:

| Campo referenciado | Situación en modelo v5.4.0 |
|---|---|
| `function_a` | No existe — era FK binario de v5.2.1 |
| `function_b` | No existe — era FK binario de v5.2.1 |
| `justification` | No existe en el modelo actual |
| `status` | No existe — el campo correcto es `state` |

Prueba de impacto en runtime:

```python
# FieldError al evaluar el queryset:
SeparationRule.objects.select_related('function_a', 'function_b').all()
# → FieldError: Invalid field name(s) given in select_related: 'function_b', 'function_a'.

# ImproperlyConfigured al instanciar el serializer:
SeparationRuleSerializer(rule).data
# → ImproperlyConfigured: Field name `function_a` is not valid for model `SeparationRule`.
```

Esto significa que cualquier llamada a `GET /api/access/separation-rules/`
vía el ViewSet legacy fallaba con 500 Internal Server Error.

### Causa raíz

El modelo `SeparationRule` fue reestructurado en FASE 0 del proyecto
(de ForeignKeys binarios a ManyToManyField con `functions_set_a` /
`functions_set_b`). El serializer y el ViewSet asociados no se actualizaron
en ese momento — quedaron desincronizados con el modelo.

### Corrección aplicada

**`separation_rule_serializers.py` — SeparationRuleSerializer:**

- Eliminados: `function_a`, `function_b`, `function_a_code`, `function_b_code`,
  `function_a_name`, `function_b_name`, `justification`, `status`
- Agregados: `functions_set_a_codes` y `functions_set_b_codes` como
  `SerializerMethodField` que devuelven `list[str]` de códigos
- Actualizado `Meta.fields` con los campos reales del modelo:
  `id, code, name, description, state, functions_set_a_codes,
  functions_set_b_codes, created_by, created_at`
- Documentado en docstring con referencia al hallazgo H-001

**`views.py` — SeparationRuleViewSet:**

- `queryset`: `select_related('function_a', 'function_b')` →
  `prefetch_related('functions_set_a', 'functions_set_b').select_related('created_by')`
- `check_conflict`: reescrito para usar `functions_set_a` / `functions_set_b`
  y `state='ENABLED'` en lugar de `status='active'`
- Agregado `@extend_schema_view` con `deprecated=True` en todas las
  operaciones: el ViewSet está supersedido por las vistas FASE 2 y se
  eliminará en FASE 3
- Agregado `@extend_schema` con `OpenApiParameter` en `check_conflict`
  para documentar los query params correctamente en el schema OpenAPI

### Resultado post-corrección

```
[PASS] H-001-A: queryset con prefetch_related evalúa sin FieldError
[PASS] H-001-B: serializer retorna campos: ['id', 'code', 'name',
       'description', 'state', 'functions_set_a_codes',
       'functions_set_b_codes', 'created_by', 'created_at']
[PASS] H-001-C: drf-spectacular sin warnings de campos inválidos
```

El schema OpenAPI generado marca correctamente el ViewSet como deprecated:

```yaml
/api/access/separation-rules/:
  get:
    summary: '[DEPRECATED] Listar reglas de separación — usar /access/sod-rules/'
    deprecated: true
```

----

## Violaciones residuales (44) — clasificadas

Las 44 violaciones que permanecen después de FASE 1 están correctamente
clasificadas por la fase en que se resolverán:

| Archivo | Líneas | Fase que las resuelve | Tipo |
|---|---|---|---|
| `access/function_assign_view.py` | 12 | FASE 3 + narrativa | error codes + @extend_schema description |
| `access/models.py` | 9 | FASE 2 (×2) + narrativa (×7) | related_names + docstrings/verbose_names |
| `access/views.py` | 7 | FASE 3 + narrativa | validate-sod legacy + comentarios |
| `access/migrations/0005_*.py` | 5 | Inmutable (×2 historial) + narrativa (×3) | archivo de migración ya aplicado |
| `access/urls.py` | 4 | FASE 3 | path sod-rules/, names sod-rule-*, validate-sod |
| `access/management/commands/create_access_groups.py` | 4 | Permanente | strings narrativos de descripción de grupos |
| `audit/models.py` | 3 | FASE 3 | VALID_EVENT_TYPES SOD_RULE_* |

**Sin deuda técnica:** cada línea residual tiene una razón documentada
y una fase o categoría asignada.

----

## Efectos en drf-spectacular

### Schema OpenAPI antes de FASE 1

Antes de la corrección, el schema tenía:
- Componente `SoDRuleCreate` (de `SoDRuleCreateSerializer`)
- Componente `SoDRulePatch` (de `SoDRulePatchSerializer`)
- Componente `SoDRuleRetire` (de `SoDRuleRetireSerializer`)
- Warning de campo inválido: `function_a` no existe en `SeparationRule`
- `SeparationRuleViewSet` funcional solo en schema, roto en runtime

### Schema OpenAPI después de FASE 1

Los componentes de serializer en el schema ahora son:

```
SeparationRuleCreateSerializer  → componente SeparationRuleCreate
SeparationRulePatchSerializer   → componente SeparationRulePatch
SeparationRuleRetireSerializer  → componente SeparationRuleRetire
```

Verificado con `drf_spectacular.generators.SchemaGenerator`:

```
PaginatedSeparationRuleList
PatchedSeparationRuleRequest
SeparationRule
SeparationRuleRequest
SeparationRuleStateEnum
SeparationValidateRequestRequest
SeparationValidateResponse
```

- Sin warnings de campos inválidos
- ViewSet legacy marcado como `deprecated: true` en todas las operaciones
- URL `sod-rules/` sigue apareciendo en el schema (FASE 3 la renombrará)

### Implicaciones para clientes del schema

Los nombres de componente de los serializers cambiaron. Si hubiera clientes
que consumen el schema OpenAPI y generan código a partir de los nombres de
componente (e.g., clientes TypeScript generados automáticamente), necesitarían
regenerar. IACT-ui usa fetch manual y no tiene esta dependencia.

----

## Verificación ejecutada (T-1.6)

```
[PASS] T-1.2: 5 clases de separation_rule_view importan correctamente
[PASS] T-1.3: DutySeparationValidator importa correctamente
[PASS] T-1.4: SEPARATION_RULES_V540 con 3 reglas, IDs SOD-001/2/3 intactos
[PASS] T-1.3: SoDValidator eliminado — no importable
[PASS] T-1.2: SoDRuleListCreateView eliminada — no importable
[PASS] T-1.5: sod-rule-list-create → /api/access/sod-rules/
[PASS] T-1.3: DutySeparationValidator.validate() ejecuta y retorna list
[PASS] FASE 3: event types SOD_RULE_* intactos en VALID_EVENT_TYPES
[PASS] drf-spectacular: schema OK, sin warnings de campos inválidos
[DONE] FASE 1 completa — todas las verificaciones pasan
```
