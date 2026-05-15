# Hallazgos — Implementación FASE 1: CI blocker + código muerto + naming

**Artefacto:** HALLAZGOS-IMPL-FASE1-DT-RESIDUAL-20260513
**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Commit:** `c9cfae7` en rama `refactor/std008-sod-naming`
**Autor:** Nestor Monroy
**Estado:** Cerrado — todos los hallazgos resueltos en este commit

----

## Resumen ejecutivo

FASE 1 se ejecutó sin deuda técnica residual. El plan original cubría
cuatro áreas. Durante la lectura previa a cualquier modificación se
identificó un hallazgo adicional crítico (H-F1-001) que amplió el
alcance: un segundo archivo de tests también estaba roto por los campos
del modelo v5.2.1.

| Métrica | Antes | Después |
|---|---|---|
| Archivos de test rotos con campos v5.2.1 | 2 (H-F1-001) | 0 |
| `SeparationRuleViewSet` en `views.py` | presente (inalcanzable) | eliminado |
| `SeparationRuleCheckSerializer` | presente (código muerto) | eliminado |
| Variables `has_a`/`has_b` en código activo | 4 instancias | 0 |
| Variables `fn_a`/`fn_b` en código activo | 2 instancias | 0 |
| Tests para `separation-rules/validate` | 0 | 8 |
| `drf-spectacular` Field warnings nuevos | — | 0 |
| `drf-spectacular` colisiones `separation_rule` | — | 0 |

----

## Hallazgo H-F1-001 — Alcance mayor al planeado: dos archivos de tests rotos

**Detectado en:** lectura de código antes de modificar nada
**Impacto:** el plan original identificó un solo archivo roto; al leer
el directorio completo se encontró un segundo
**Resuelto en:** este commit

### Descripción

El plan `PLAN-IMPL-DT-RESIDUAL-20260513` identificó en T-1.2:

> "Reescribir `test_separation_rule_viewset.py`"

Al leer el directorio `tests/unit/access/` se encontró que `test_separation_rule.py`
también estaba completamente roto:

```python
# test_separation_rule.py — estado ANTES (roto)

# Usando SeparationRuleTestData con campos inexistentes
SeparationRuleTestData(function_a=fn_a, function_b=fn_b)
# → TypeError: SeparationRule() got unexpected keyword arguments: 'function_a', 'function_b'

# Usando queries con campos inexistentes
SeparationRule.objects.filter(
    Q(function_a=fn_a, function_b=fn_b),
    status='active',
)
# → FieldError: Cannot resolve keyword 'function_a' into field.
```

Los campos `function_a`, `function_b` y `status` existían en el modelo
v5.2.1 (FKs binarios). Desde FASE 0, el modelo v5.4.0 usa M2M con
`functions_set_a`/`functions_set_b` y el campo de estado se llama `state`.

### Causa raíz

Cuando se reestructuró el modelo en FASE 0, se actualizó el código
de producción (`models.py`, `views.py`, etc.) pero NO los tests unitarios.
El test de modelo (`test_separation_rule.py`) quedó probando invariantes
del modelo antiguo (unicidad del par FK, queries con `Q(function_a=...)`).
No fue detectado hasta la lectura previa a esta implementación porque el
análisis de DT-STD008-003 en `ANALISIS-DT-RESIDUAL-STD008-20260513.md`
enfocó su diagnóstico en el test del ViewSet.

### Tests reescritos

`test_separation_rule.py` — versión nueva:

| Test original | Prueba | Test reemplazante | Prueba |
|---|---|---|---|
| `test_duplicate_pair_raises_integrity_error` | unique constraint en `(function_a, function_b)` | `test_duplicate_code_raises_integrity_error` | `unique=True` en `code` |
| `test_reversed_pair_is_distinct_constraint` | `(A,B)` y `(B,A)` son distintos en FK | `test_distinct_codes_coexist` | dos reglas con distinto `code` |
| `test_conflict_query_finds_direct_pair` | `Q(function_a=...)` | `test_violated_when_user_has_functions_from_both_sets` | `is_violated_by({fa.code, fb.code})` |
| `test_conflict_query_finds_reversed_pair` | `Q(function_a=fb, function_b=fa)` | `test_symmetric_detection` | `find_conflict()` bidireccional |
| `test_inactive_rule_not_found_by_active_filter` | `status='active'` | `test_not_violated_when_rule_disabled` | `state=DISABLED` |

Adicionalmente se añadieron:
- `test_not_violated_when_user_only_has_set_a` — cobertura del caso parcial
- `test_not_violated_when_user_only_has_set_b` — cobertura del caso parcial
- `test_not_violated_when_no_overlap` — función fuera de cualquier conjunto
- `test_returns_conflict_pair_when_violated` / `test_returns_none_*` — `find_conflict()`

----

## Eliminación de `SeparationRuleViewSet`

### Qué se eliminó

De `apps/access/views.py`:
- Bloque `# B-05: SeparationRule ViewSet` completo (comentario separador)
- Primer `@extend_schema_view` (summaries normales: lista, crear, detalle, etc.)
- Segundo `@extend_schema_view` (summaries `[DEPRECATED]`)
- Clase `SeparationRuleViewSet` con `queryset`, `function_map`, `perform_create`
- `@action check_conflict` dentro del ViewSet
- Total: 130 líneas eliminadas

De `apps/access/serializers/separation_rule_serializers.py`:
- Clase `SeparationRuleCheckSerializer` (18 líneas)
- Actualización del docstring del módulo — refleja el estado actual

De `apps/access/serializers/__init__.py`:
- Import `SeparationRuleCheckSerializer`
- `'SeparationRuleCheckSerializer'` de `__all__`

De `apps/access/views.py` (imports):
- `SeparationRuleSerializer` del import de serializers
- `SeparationRuleCheckSerializer` del import de serializers

### Por qué `SeparationRuleSerializer` se conserva

`SeparationRuleSerializer` continúa siendo importado en
`separation_rule_view.py` (vistas canónicas) como serializer de
validación de request. Eliminar el ViewSet no lo hace código muerto.

Su docstring fue actualizado para no hacer referencia al ViewSet eliminado.

### Verificación drf-spectacular post-eliminación

El schema generado antes y después de la eliminación tiene exactamente
los mismos `operationId` para las rutas de `separation-rules/`:

```
separation_rule_list          GET  /api/access/separation-rules/
separation_rule_create        POST /api/access/separation-rules/
separation_rule_retrieve      GET  /api/access/separation-rules/{rule_id}/
separation_rule_partial_update PATCH /api/access/separation-rules/{rule_id}/
separation_rule_destroy       DELETE /api/access/separation-rules/{rule_id}/
separation_rule_validate      POST /api/access/separation-rules/validate
```

Sin Field warnings nuevos. Sin colisiones de `operationId` relacionadas
con `SeparationRule`.

----

## Mejora de variables locales (Clean Code)

### `models.py` — `is_violated_by()`

| Antes | Después | Intención revelada |
|---|---|---|
| `codes_a` | `codes_set_a` | códigos del conjunto A de la regla |
| `codes_b` | `codes_set_b` | códigos del conjunto B de la regla |
| `has_a` | `user_has_set_a` | el usuario tiene al menos una función del conjunto A |
| `has_b` | `user_has_set_b` | el usuario tiene al menos una función del conjunto B |

`has_a` violaba Clean Code §2 porque la variable decía "tiene a" sin
especificar qué. `user_has_set_a` responde: "el usuario tiene funciones
del conjunto A de esta regla de separación."

### `models.py` — `find_conflict()`

| Antes | Después | Intención revelada |
|---|---|---|
| `codes_a` | `codes_set_a` | igual que arriba |
| `codes_b` | `codes_set_b` | igual que arriba |
| `fn_a` | `conflict_from_set_a` | el código de función que materializa el conflicto desde el conjunto A |
| `fn_b` | `conflict_from_set_b` | ídem desde el conjunto B |

`fn_a` era especialmente opaco: en el contexto de `find_conflict` la
variable representa no "una función de set_a" sino "la función específica
del set_a que está causando el conflicto". `conflict_from_set_a` lo dice.

### `function_assign_view.py` — `DutySeparationValidator.validate()`

Misma aplicación que en `models.py`. Los cuatro cambios:
- `codes_a` → `codes_set_a`
- `codes_b` → `codes_set_b`
- `has_a` → `user_has_set_a`
- `has_b` → `user_has_set_b`

El campo `conflict_pair` en el payload de respuesta también actualizado
para usar `[list(codes_set_a), list(codes_set_b)]`.

----

## Nuevo test suite `test_separation_rule_validate.py`

8 tests para `POST /api/access/separation-rules/validate`:

| Test | Escenario | Criterio |
|---|---|---|
| `test_detecta_conflicto_...set_a` | Usuario con set_a, propone set_b | `conflicts` no vacío, `rule == rule.code` |
| `test_detecta_conflicto_en_orden_inverso` | Usuario con set_b, propone set_a | `conflicts` no vacío |
| `test_sin_conflicto_cuando_no_hay_regla` | Sin SeparationRule en BD | `conflicts == []` |
| `test_regla_disabled_no_genera_conflicto` | `state=DISABLED` | `conflicts == []` |
| `test_sin_conflicto_cuando_usuario_no_tiene_funciones` | Usuario sin asignaciones | `conflicts == []` |
| `test_asignacion_revocada_no_participa` | Asignación REVOKED | `conflicts == []` |
| `test_requiere_userId_y_functionId` | Payload incompleto | `status == 400` |
| `test_usuario_inexistente_retorna_404` | `userId` no existe en BD | `status == 404` |
| `test_estructura_de_conflicto_...campos_requeridos` | Conflicto detectado | Presencia de `rule`, `ruleDesc`, `setA`, `setB`, `message` |

----

## Verificación ejecutada

```
[PASS] T-1.A: SeparationRuleTestData() → OK, pk=1, code=TST-SR-000
[PASS] T-1.B: SeparationRuleTestData(state=DISABLED) → OK
[PASS] T-1.C: separationrule-check-conflict → NoReverseMatch (eliminado)
[PASS] T-1.D: separation-rule-validate → /api/access/separation-rules/validate
[PASS] T-1.E: is_violated_by con user_has_set_a/b funcional
[PASS] T-1.F: find_conflict con conflict_from_set_a/b funcional
[PASS] T-1.G: DutySeparationValidator.validate con user_has_set_a/b funcional
[PASS] T-1.H: SeparationRuleCheckSerializer eliminado (ImportError)
[PASS] T-1.I: SeparationRuleSerializer sigue disponible
[PASS] T-1.J: drf-spectacular — schema limpio, 6 operation_ids correctos
[PASS] T-1.K: makemigrations access --check: sin cambios pendientes
[DONE] T-1.8 — todos los criterios PASS
```
