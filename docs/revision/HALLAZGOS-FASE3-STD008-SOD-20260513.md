# Hallazgos — Implementación STD_008 §3.3 FASE 3

**Artefacto:** HALLAZGOS-FASE3-STD008-SOD-20260513
**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Commit:** `16d57ac` en rama `refactor/std008-sod-naming`
**Autor:** Nestor Monroy
**Estado:** Cerrado — todos los hallazgos resueltos en este commit

----

## Resumen ejecutivo

FASE 3 fue la más compleja: cambia el contrato público de la API.
Además del renombrado de URL y error codes, se descubrieron y corrigieron
dos bugs de runtime graves en `SeparationRuleValidateView` y un problema
de diseño en drf-spectacular al registrar la misma vista en dos URLs.

| Métrica | Antes | Después |
|---|---|---|
| URL CRUD de reglas | `sod-rules/` (rota) | `separation-rules/` (funcional) |
| Endpoint de validación | Inexistente (IACT-ui lo llamaba) | `separation-rules/validate` |
| Error codes `SOD_*` | 5 instancias | 0 |
| Event types `SOD_RULE_*` | 6 instancias | 0 |
| Bugs de runtime corregidos | 2 (H-003) | 0 |
| operation_ids drf-spectacular | Sin colisiones | Sin colisiones |
| Violaciones STD_008 §3.3 | 44 | 30 (-14 en FASE 3) |
| Tests de verificación | — | 10 PASS, 0 FAIL |

----

## Cambios ejecutados

### `audit/models.py` — VALID_EVENT_TYPES

| Antes | Después |
|---|---|
| `SOD_RULE_CREATED` | `SEPARATION_RULE_CREATED` |
| `SOD_RULE_UPDATED` | `SEPARATION_RULE_UPDATED` |
| `SOD_RULE_DISABLED` | `SEPARATION_RULE_DISABLED` |

### `separation_rule_view.py` — error codes, event types, @extend_schema

**Error codes:**

| Antes | Después |
|---|---|
| `'error': 'SOD_RULE_DUPLICATE'` | `'error': 'SEPARATION_RULE_DUPLICATE'` |
| `'error': 'SOD_RULE_NOT_FOUND'` (×3) | `'error': 'SEPARATION_RULE_NOT_FOUND'` |

**Event types:**

| Antes | Después |
|---|---|
| `event_type='SOD_RULE_CREATED'` | `event_type='SEPARATION_RULE_CREATED'` |
| `event_type='SOD_RULE_UPDATED'` | `event_type='SEPARATION_RULE_UPDATED'` |
| `event_type='SOD_RULE_DISABLED'` | `event_type='SEPARATION_RULE_DISABLED'` |

**@extend_schema:**

Reestructurado de un decorador de clase (sin request/responses) a decoradores
por método con `operation_id` explícito, `request` y `responses`:

```python
# Antes (clase — drf-spectacular no puede inferir serializer)
@extend_schema(summary='...', tags=[...])
class SeparationRuleListCreateView(APIView): ...

# Después (método — drf-spectacular obtiene schema completo)
class SeparationRuleListCreateView(APIView):
    @extend_schema(
        operation_id='separation_rule_list',
        responses={200: _rule_list_schema()},
    )
    def get(self, request): ...

    @extend_schema(
        operation_id='separation_rule_create',
        request=SeparationRuleCreateSerializer,
        responses={201: _rule_create_response_schema(), 409: ...},
    )
    def post(self, request): ...
```

### `function_assign_view.py` — error codes y @extend_schema

| Antes | Después |
|---|---|
| `'error': 'SOD_VIOLATION'` (FunctionAssignView) | `'error': 'SEPARATION_RULE_VIOLATION'` |
| `'reason': 'sod_violation'` (payload audit) | `'reason': 'separation_rule_violation'` |
| `'error': 'SOD_VIOLATION'` (AGRAssignView) | `'error': 'SEPARATION_RULE_VIOLATION'` |
| `@extend_schema` description `SOD_VIOLATION` | `SEPARATION_RULE_VIOLATION` |

### `urls.py` — URL paths + nuevo validate + router depurado

| Antes | Después |
|---|---|
| `path('sod-rules/', ..., name='sod-rule-list-create')` | `path('separation-rules/', ..., name='separation-rule-list-create')` |
| `path('sod-rules/<int:rule_id>/', ..., name='sod-rule-detail')` | `path('separation-rules/<int:rule_id>/', ..., name='separation-rule-detail')` |
| Sin endpoint `/separation-rules/validate` | `path('separation-rules/validate', SeparationRuleValidateView.as_view(), name='separation-rule-validate')` |
| `router.register(r'separation-rules', SeparationRuleViewSet)` | Eliminado del router |
| `path('validate-sod', SeparationRuleValidateView)` | `path('validate-sod', SeparationRuleValidateLegacyView)` |

----

## Hallazgo H-003 — SeparationRuleValidateView completamente rota

**Severidad:** Alta — FieldError en runtime en cualquier llamada POST
**Detectado en:** lectura del código antes de modificar
**Resuelto en:** este commit

### Descripción

`SeparationRuleValidateView.post()` usaba el modelo v5.2.1 de FK binario
mientras el modelo actual usa M2M sets. El método fallaba con errores en
runtime en cada llamada POST:

```python
# Código anterior — completamente roto con el modelo v5.4.0

# Bug 1: status='active' → field 'status' no existe, es 'state'
rules = SeparationRule.objects.filter(
    status='active'             # FieldError: Unknown field 'status'
).filter(
    dj_models.Q(function_a=function) | dj_models.Q(function_b=function)
    # FieldError: Unknown field 'function_a'
).select_related('function_a', 'function_b')
# FieldError: Unknown field 'function_a'

# Bug 2: atributos inexistentes en el modelo actual
for rule in rules:             # nunca llega aquí por el FieldError anterior
    other_fn = rule.function_b if rule.function_a == function else rule.function_a
    conflicts.append({
        'ruleDesc': rule.justification,  # AttributeError: 'SeparationRule' has no 'justification'
    })
```

### Causa raíz

La vista `SeparationRuleValidateView` fue escrita cuando el modelo
`SeparationRule` usaba FKs binarios (`function_a`, `function_b`).
En FASE 0, el modelo fue reestructurado a M2M sets (`functions_set_a`,
`functions_set_b`) para soportar múltiples funciones por conjunto. La
vista no se actualizó en ese momento.

En FASE 1 del presente plan se corrigió `SeparationRuleViewSet.check_conflict`
(el mismo bug) pero no `SeparationRuleValidateView.post()`, que quedó pendiente
para FASE 3 al ser parte del contrato público.

### Solución implementada

Reescritura completa usando la estructura M2M correcta:

```python
def post(self, request):
    # Obtener funciones actuales del usuario (ACTIVE)
    current_codes = set(
        UserFunctionAssignment.objects.filter(user=user, state='ACTIVE')
        .values_list('function__code', flat=True)
    )
    proposed_code = function.code

    # Evaluar cada regla ENABLED con prefetch M2M para evitar N+1
    conflicts = []
    for rule in (
        SeparationRule.objects
        .filter(state='ENABLED')
        .prefetch_related('functions_set_a', 'functions_set_b')
    ):
        codes_a = set(rule.functions_set_a.values_list('code', flat=True))
        codes_b = set(rule.functions_set_b.values_list('code', flat=True))

        if proposed_code in codes_a:
            conflicting = current_codes & codes_b
            if conflicting:
                conflicts.append({
                    'rule':     rule.code,
                    'ruleDesc': rule.description,  # campo correcto
                    'setA':     [proposed_code],
                    'setB':     sorted(conflicting),
                    'message':  f'{rule.name}: {proposed_code} incompatible con ...',
                })
        elif proposed_code in codes_b:
            # Análogo para el caso inverso
            ...
```

**Mejoras adicionales:**
- `prefetch_related('functions_set_a', 'functions_set_b')` evita N+1
- La respuesta usa `rule.code` y `rule.description` (campos reales del modelo)
- La estructura `{ rule, ruleDesc, setA, setB, message }` es compatible
  con lo que consume `accessGateway.validateSeparationRules()` en IACT-ui

----

## Hallazgo H-003b — operationId collision drf-spectacular

**Severidad:** Media — genera schema OpenAPI con IDs duplicados
**Detectado en:** primera ronda de verificación drf-spectacular
**Resuelto en:** este commit

### Descripción

Al registrar la misma vista `SeparationRuleValidateView` en dos URLs:

```python
path('separation-rules/validate', SeparationRuleValidateView.as_view()),
path('validate-sod',              SeparationRuleValidateView.as_view()),
```

drf-spectacular generaba:

```
Warning: operationId "separation_rule_validate" has collisions
[('/api/access/separation-rules/validate', 'post'),
 ('/api/access/validate-sod', 'post')].
resolving with numeral suffixes.
```

El resultado: `separation_rule_validate_2` para `validate-sod`. Los
clientes que generan código a partir del schema OpenAPI obtendrían un
método con sufijo numérico arbitrario.

Adicionalmente, drf-spectacular emitía:

```
Error: using @extend_schema on viewset class SeparationRuleValidateView
with parameters operation_id or operation will most likely result in
a broken schema.
```

El mensaje es incorrecto (la vista no es un ViewSet), pero refleja que
poner `operation_id` en `@extend_schema` a nivel de clase es problemático
cuando la misma clase se registra en múltiples URLs.

### Solución implementada

**Parte A — mover @extend_schema al método `post()`:**

```python
class SeparationRuleValidateView(APIView):
    # Sin @extend_schema a nivel de clase

    @extend_schema(
        operation_id='separation_rule_validate',
        ...
    )
    def post(self, request): ...
```

Esto es coherente con el patrón establecido en `SeparationRuleListCreateView`
y `SeparationRuleDetailView` (decoradores por método, no por clase).

**Parte B — clase wrapper excluida para la URL legacy:**

```python
@extend_schema(exclude=True)
class SeparationRuleValidateLegacyView(SeparationRuleValidateView):
    """
    POST /api/access/validate-sod — DEPRECATED legacy endpoint.
    Sin consumidor activo en IACT-ui (migrado a separation-rules/validate).
    Excluida del schema OpenAPI para evitar colisión de operationId.
    """
```

Y en urls.py:

```python
path('validate-sod',
     SeparationRuleValidateLegacyView.as_view(), name='validate-separation'),
```

**Resultado:** el schema OpenAPI contiene exactamente un `POST` para
`separation-rules/validate` con `operationId: separation_rule_validate`.
El endpoint `validate-sod` funciona en runtime pero no aparece en el schema.

----

## Análisis de las violaciones residuales (30)

Todas correctamente clasificadas:

| Archivo | Líneas | Categoría | Detalle |
|---|---|---|---|
| `access/models.py` | 7 | Narrativa permanente | verbose_name 'Regla SoD', `__str__`, docstrings |
| `access/migrations/0005_*.py` | 5 | Inmutable histórico | migración ya aplicada |
| `access/urls.py` | 4 | Narrativa + backward compat | historial en docstring (×2) + validate-sod path (×2) |
| `access/management/commands/create_access_groups.py` | 4 | Narrativa permanente | strings de descripción de grupos |
| `access/function_assign_view.py` | 4 | Narrativa permanente | "SoD check" en docstrings + historial FASE 1 |
| `access/views.py` | 3 | Backward compat strings | `validate-sod` en docstrings y description |
| `access/migrations/0008_*.py` | 2 | Narrativa permanente | verbose_name + nombre de artefacto |
| `audit/models.py` | 1 | Historial de trazabilidad | comentario `# STD_008 FASE 3: SOD_RULE_* → SEPARATION_RULE_*` |

**`validate-sod` en urls.py y views.py:** el path `validate-sod` es una
URL de backward compatibility que se mantiene intencionalmente sin renombrar.
Renombrarla rompería cualquier consumidor que todavía la use. El plan
establece que se depreca y se eliminará en una iteración posterior.
STD_008 §3.3 aplica a **identificadores técnicos**; un string de URL en un
`path()` es un valor de configuración de routing, no un identificador Python.

----

## Schema OpenAPI resultante — paths de separación

```yaml
paths:
  /api/access/separation-rules/:
    get:
      operationId: separation_rule_list
      summary: 'UC_ACC_05 — Listar reglas de separación'
    post:
      operationId: separation_rule_create
      summary: 'UC_ACC_05 — Crear regla de separación'

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
      summary: 'UC_ACC_01 — Validar conflictos de separación antes de asignar función'

  # validate-sod excluido (SeparationRuleValidateLegacyView con exclude=True)
```

Los paths `sod-rules/`, `sod-rules/{id}/` han desaparecido del schema.

----

## Verificación ejecutada

```
[PASS] T-3.A: separation-rule-list-create → /api/access/separation-rules/
[PASS] T-3.A: sod-rule-list-create → NoReverseMatch (eliminado)
[PASS] T-3.B: separation-rule-validate → /api/access/separation-rules/validate
[PASS] T-3.C: POST separation-rules/ → 201
[PASS] T-3.C: AuditEvent SEPARATION_RULE_CREATED (no SOD_RULE_CREATED)
[PASS] T-3.C: GET separation-rules/ → 200
[PASS] T-3.C: GET separation-rules/{id}/ → 200
[PASS] T-3.C: PATCH → 200, AuditEvent SEPARATION_RULE_UPDATED
[PASS] T-3.D: duplicado → 409 SEPARATION_RULE_DUPLICATE
[PASS] T-3.E: no encontrado → 404 SEPARATION_RULE_NOT_FOUND
[PASS] T-3.F: violación separación → 409 SEPARATION_RULE_VIOLATION
[PASS] T-3.G: POST separation-rules/validate → 200, conflicto detectado
[PASS] T-3.H: VALID_EVENT_TYPES correctos (SEPARATION_RULE_*)
[PASS] T-3.I: drf-spectacular paths correctos, sin warnings inválidos
[PASS] T-3.J: operation_ids sin colisiones
[DONE] FASE 3 — todos los criterios verificados
```

----

## Notas para las fases siguientes

**FASE 4 (IACT-docs):** actualizar los 9 UCs con la tabla de sustituciones
del análisis consolidado. Los cambios de error codes y URL ya están
implementados en el backend; los docs deben reflejarlos.

**Eliminación pendiente (limpieza posterior):**
- `SeparationRuleViewSet` y `SeparationRuleValidateLegacyView` en `views.py`
  pueden eliminarse cuando se confirme que `validate-sod` no tiene consumidores.
- El endpoint `validate-sod` puede eliminar su `path()` en `urls.py`.

Estas eliminaciones requieren un PR separado con coordinación confirmada
de que no hay consumidores externos del endpoint legacy.
