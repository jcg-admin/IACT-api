# Plan de Implementación — Remediación Deuda Técnica Residual

**Artefacto:** PLAN-IMPL-DT-RESIDUAL-20260513
**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Autor:** Nestor Monroy
**Fuente:** ANALISIS-DT-RESIDUAL-STD008-20260513.md + análisis de endpoints y naming

----

## Resumen de items a resolver

| ID | Descripción | Repositorio | Urgencia | Blocker CI |
|---|---|---|---|---|
| **T-DT-001** | Actualizar CNST-033 v2.0.0 + modelo-rbac-iact.rst | IACT-docs | Media | No |
| **T-DT-002** | Renombrar 4 codenames `sod` en catalog.js | IACT-ui | Alta (STD-008) | No |
| **T-DT-003** | Corregir test suite rota del ViewSet deprecated | IACT-api | **Urgente** | **Sí** |
| **T-DT-004** | Eliminar SeparationRuleViewSet + serializer muerto | IACT-api | Alta | No |
| **T-URL-001** | Renombrar endpoints en español a inglés | IACT-api | Alta (STD-008) | No |
| **T-CC-001** | Mejorar nombres de variables locales (Clean Code) | IACT-api | Media | No |

### Dependencias entre items

```
T-DT-003 ──┐
           ├── FASE 1 (mismo PR — misma área, mismo riesgo)
T-DT-004 ──┤
           │
T-CC-001 ──┘

T-URL-001 ─── FASE 2 (área diferente — reports module)

T-DT-002 ─── FASE 3 (repositorio diferente — IACT-ui)

T-DT-001 ─── FASE 4 (repositorio diferente — IACT-docs)
```

**T-DT-003 y T-DT-004 van en el mismo PR** porque:
- Corregir el test sin eliminar el ViewSet deja una clase inalcanzable y sus
  tests apuntan a ella — inconsistencia parcial.
- T-CC-001 se añade al mismo PR porque toca los mismos archivos del módulo
  `access` y el costo de revisión incremental es bajo.

----

## FASE 1 — IACT-api: CI blocker + código muerto + naming

**Rama:** `fix/dt-viewset-cleanup`
**Criterio de done:** `pytest` pasa al 100%, drf-spectacular sin advertencias
nuevas relacionadas con SeparationRule, sin referencia a `SeparationRuleViewSet`
en ningún archivo activo.

### T-1.1 — Corregir `SeparationRuleTestData` en `access_test_data.py`

**Archivo:** `tests/test_data/access_test_data.py`

**Estado actual:**
```python
class SeparationRuleTestData(DjangoModelFactory):
    function_a    = factory.SubFactory(FunctionTestData)   # campo no existe
    function_b    = factory.SubFactory(FunctionTestData)   # campo no existe
    status        = 'active'                               # campo no existe
    justification = ''                                     # campo no existe
```

**Estado objetivo:**
```python
class SeparationRuleTestData(DjangoModelFactory):
    """
    Factory de SeparationRule para tests.

    El modelo usa ManyToManyField (functions_set_a, functions_set_b).
    Los conjuntos se asignan mediante .set() post-creación, no como kwargs.
    """
    code  = factory.Sequence(lambda n: f'TEST-{n:03d}')
    name  = factory.Sequence(lambda n: f'test_separation_{n}')
    state = SeparationRule.STATE_ENABLED

    class Meta:
        model = SeparationRule
```

**Notas:**
- Los campos M2M no se pasan como kwargs en `DjangoModelFactory`.
  En cada test que necesite functions_set_a/b, se asignan con `.set()`
  después de crear la instancia.
- Eliminar todos los campos de la fábrica que no existen en el modelo actual.

### T-1.2 — Reescribir `test_separation_rule_viewset.py`

**Archivo actual:** `tests/unit/access/test_separation_rule_viewset.py`
**Archivo destino:** `tests/unit/access/test_separation_rule_validate.py`

El archivo actual prueba `GET /api/access/separation-rules/check/` que no
existe. Reescribir para probar el endpoint canónico
`POST /api/access/separation-rules/validate`.

**Estructura del nuevo archivo:**
```python
"""
tests/unit/access/test_separation_rule_validate.py

N-004 — Tests del endpoint de validación de separación.
POST /api/access/separation-rules/validate
"""
class TestSeparationRuleValidateEndpoint:

    def test_detecta_conflicto_cuando_regla_existe(self, client_with_view_permission):
        """Asignar función de set_b cuando ya se tiene función de set_a → conflicto."""
        fa = FunctionTestData()
        fb = FunctionTestData()
        rule = SeparationRuleTestData()
        rule.functions_set_a.set([fa])
        rule.functions_set_b.set([fb])
        # Crear una asignación activa de fa al usuario objetivo
        # POST /validate con functionId=fb → debe retornar conflicts

    def test_no_hay_conflicto_sin_regla(self, client_with_view_permission):
        """Sin SeparationRule, validate retorna lista vacía."""

    def test_detecta_conflicto_en_orden_inverso(self, client_with_view_permission):
        """Si la función propuesta está en set_b y el usuario tiene set_a → conflicto."""

    def test_regla_disabled_no_genera_conflicto(self, client_with_view_permission):
        """state=DISABLED → validate retorna lista vacía."""
```

**Eliminar:** el archivo original `test_separation_rule_viewset.py`.

### T-1.3 — Eliminar `SeparationRuleViewSet` de `views.py`

**Archivo:** `apps/access/views.py`

Eliminar:
1. Los dos bloques `@extend_schema_view(...)` sobre `SeparationRuleViewSet`
   (el primer bloque con summaries normales y el segundo con `[DEPRECATED]`).
2. La clase `SeparationRuleViewSet` completa (incluyendo el `@action check_conflict`).

**Verificar** que `views.py` sigue importando correctamente después de la
eliminación. El import de `SeparationRuleViewSet` en `urls.py` ya fue
eliminado en FASE 3 de STD_008.

### T-1.4 — Eliminar `SeparationRuleCheckSerializer` de `separation_rule_serializers.py`

**Archivo:** `apps/access/serializers/separation_rule_serializers.py`

Eliminar la clase `SeparationRuleCheckSerializer`. Esta clase retornaba
`tiene_conflicto`/`regla`/`conflicts` — estructura del endpoint `check/`
que ya no existe.

`SeparationRuleSerializer` permanece: sigue siendo usado por las views
canónicas en `separation_rule_view.py` (como serializer de request).

### T-1.5 — Limpiar `serializers/__init__.py`

**Archivo:** `apps/access/serializers/__init__.py`

Verificar si `SeparationRuleCheckSerializer` está exportado. Si lo está,
eliminarlo de `__all__` y del import.

### T-1.6 — Mejorar variables locales en `models.py`

**Archivo:** `apps/access/models.py`

**Método `is_violated_by`:**
```python
# Antes
codes_a = set(self.functions_set_a.values_list('code', flat=True))
codes_b = set(self.functions_set_b.values_list('code', flat=True))
has_a   = bool(function_codes & codes_a)
has_b   = bool(function_codes & codes_b)
return has_a and has_b

# Después
codes_set_a     = set(self.functions_set_a.values_list('code', flat=True))
codes_set_b     = set(self.functions_set_b.values_list('code', flat=True))
user_has_set_a  = bool(function_codes & codes_set_a)
user_has_set_b  = bool(function_codes & codes_set_b)
return user_has_set_a and user_has_set_b
```

**Método `find_conflict`:**
```python
# Antes
codes_a = set(self.functions_set_a.values_list('code', flat=True))
codes_b = set(self.functions_set_b.values_list('code', flat=True))
fn_a = next(iter(function_codes & codes_a))
fn_b = next(iter(function_codes & codes_b))
return (fn_a, fn_b)

# Después
codes_set_a         = set(self.functions_set_a.values_list('code', flat=True))
codes_set_b         = set(self.functions_set_b.values_list('code', flat=True))
conflict_from_set_a = next(iter(function_codes & codes_set_a))
conflict_from_set_b = next(iter(function_codes & codes_set_b))
return (conflict_from_set_a, conflict_from_set_b)
```

### T-1.7 — Mejorar variables locales en `function_assign_view.py`

**Archivo:** `apps/access/function_assign_view.py`

```python
# Antes
codes_a = set(rule.functions_set_a.values_list('code', flat=True))
codes_b = set(rule.functions_set_b.values_list('code', flat=True))
has_a   = bool(all_codes & codes_a)
has_b   = bool(all_codes & codes_b)
if has_a and has_b:

# Después
codes_set_a    = set(rule.functions_set_a.values_list('code', flat=True))
codes_set_b    = set(rule.functions_set_b.values_list('code', flat=True))
user_has_set_a = bool(all_codes & codes_set_a)
user_has_set_b = bool(all_codes & codes_set_b)
if user_has_set_a and user_has_set_b:
```

El campo `conflict_pair` en el payload conserva `[list(codes_set_a), list(codes_set_b)]`.

### T-1.8 — Verificación drf-spectacular post-eliminación

Ejecutar el generador de schema y confirmar:
- 0 warnings relacionados con `SeparationRuleViewSet` o `SeparationRuleCheckSerializer`.
- Los 6 `operationId` canónicos siguen presentes:
  `separation_rule_list`, `separation_rule_create`, `separation_rule_retrieve`,
  `separation_rule_partial_update`, `separation_rule_destroy`, `separation_rule_validate`.

### T-1.9 — Commit

```
fix(access): eliminar ViewSet deprecated + corregir test suite + mejorar naming

CI blocker corregido:
  SeparationRuleTestData: eliminar function_a/b/status/justification (campos v5.2.1)
  test_separation_rule_viewset.py → test_separation_rule_validate.py
  reverse('access:separationrule-check-conflict') reemplazado por
  reverse('access:separation-rule-validate')

Código muerto eliminado:
  SeparationRuleViewSet + @extend_schema_view decorators (2 bloques)
  SeparationRuleCheckSerializer
  Export de SeparationRuleCheckSerializer en serializers/__init__.py

drf-spectacular: sin advertencias nuevas; 6 operation_ids canónicos intactos.

Clean Code — variables locales de SeparationRule:
  has_a/has_b → user_has_set_a/user_has_set_b (models.py, function_assign_view.py)
  fn_a/fn_b → conflict_from_set_a/conflict_from_set_b (models.py)
```

----

## FASE 2 — IACT-api: Endpoints en español → inglés

**Rama:** `fix/std008-spanish-endpoints`
**Repositorio:** IACT-api únicamente (IACT-ui no llama a estos endpoints).
**Criterio de done:** `reverse('reports:ivr-menu-redirigidos')` lanza
`NoReverseMatch`; `reverse('reports:ivr-menu-redirected')` resuelve correctamente.

### T-2.1 — Renombrar paths en `reports/urls.py`

**Archivo:** `apps/reports/urls.py`

```python
# Antes
path('ivr/menu-redirigidos/', RedirectedMenusView.as_view(), name='ivr-menu-redirigidos'),
path('ivr/menu-centro/',      CenterMenuView.as_view(),      name='ivr-menu-centro'),

# Después
path('ivr/menu-redirected/',  RedirectedMenusView.as_view(), name='ivr-menu-redirected'),
path('ivr/menu-center/',      CenterMenuView.as_view(),      name='ivr-menu-center'),
```

### T-2.2 — Actualizar docstrings en `apps/reports/ivr_views.py`

Los docstrings de `RedirectedMenusView` y `CenterMenuView` mencionan la URL.
Actualizar las cadenas que dicen `ivr/menu-redirigidos/` e `ivr/menu-centro/`
por los nuevos paths.

El nombre del SP (`sp_rpt_menu_redirigidos`, `sp_rpt_menu_centro`) NO cambia —
es un contrato con MariaDB que está fuera del scope de STD-008 §3.5 (no son
Endpoints REST).

### T-2.3 — Actualizar las 12 referencias en `test_ivr_endpoints.py`

**Archivo:** `tests/integration/pipeline/test_ivr_endpoints.py`

Reemplazos:
- `reverse('reports:ivr-menu-redirigidos')` → `reverse('reports:ivr-menu-redirected')`
- `reverse('reports:ivr-menu-centro')` → `reverse('reports:ivr-menu-center')`
- Strings literales `'menu-redirigidos'` en parametrize → `'menu-redirected'`
- Strings literales `'menu-centro'` en parametrize → `'menu-center'`
- Nombres de métodos de test que contienen `redirigidos`/`centro` → actualizar

### T-2.4 — Verificación

```bash
python manage.py check --deploy  # sin errores de URL
pytest tests/integration/pipeline/test_ivr_endpoints.py -v
```

### T-2.5 — Commit

```
fix(reports): STD-008 §3.5 — endpoints IVR en español → inglés

  ivr/menu-redirigidos/ → ivr/menu-redirected/  (RedirectedMenusView)
  ivr/menu-centro/      → ivr/menu-center/       (CenterMenuView)

Afectados: reports/urls.py, ivr_views.py (docstrings),
  tests/integration/pipeline/test_ivr_endpoints.py (12 referencias)

Los SPs de MariaDB (sp_rpt_menu_redirigidos, sp_rpt_menu_centro)
no cambian — son contratos de base de datos fuera del scope de STD-008 §3.5.
IACT-ui no llama directamente a estos endpoints.
```

----

## FASE 3 — IACT-ui: Codenames `sod` en `catalog.js`

**Rama:** `fix/std008-catalog-codenames` en IACT-ui
**Repositorio:** IACT-ui únicamente.
**Criterio de done:** `grep -r "view_sod\|create_sod\|update_sod\|disable_sod" src/`
retorna 0 resultados fuera de comentarios.

### T-3.1 — Renombrar las 4 constantes en `catalog.js`

**Archivo:** `src/permissions/catalog.js`

```javascript
// Antes
MANAGE_SEPARATION_RULES: 'access:view_sod',
CREATE_SEPARATION_RULE:  'adm:create_sod',
UPDATE_SEPARATION_RULE:  'access:update_sod',
DISABLE_SEPARATION_RULE: 'access:disable_sod',

// Después
MANAGE_SEPARATION_RULES: 'access:view_separation_rules',
CREATE_SEPARATION_RULE:  'adm:create_separation_rule',
UPDATE_SEPARATION_RULE:  'access:update_separation_rule',
DISABLE_SEPARATION_RULE: 'access:disable_separation_rule',
```

**Nota de alineación futura:** cuando el endpoint
`/api/permisos/verificar/{userId}/capacidades/` se implemente, los
valores de catalog.js deberán coincidir con los `Function.permission_django`
del backend:
```
'access:view_separation_rules'   ↔  permission_django='view_separation_rules'   (ACC-005)
'adm:create_separation_rule'     ↔  permission_django='update_separation_rule'  (ACC-011)
'access:update_separation_rule'  ↔  permission_django='update_separation_rule'  (ACC-011)
'access:disable_separation_rule' ↔  permission_django='disable_separation_rule' (ACC-012)
```
El prefijo `adm:` vs `access:` es una convención de dominio del frontend
que deberá consolidarse cuando se implemente el servicio de capacidades.
Esto está fuera del scope de esta fase.

### T-3.2 — Actualizar `catalog.test.js`

**Archivo:** `src/permissions/__tests__/catalog.test.js`

```javascript
// Antes
expect(FunctionCatalog.UPDATE_SEPARATION_RULE).toBe('access:update_sod');
expect(FunctionCatalog.DISABLE_SEPARATION_RULE).toBe('access:disable_sod');

// Después
expect(FunctionCatalog.UPDATE_SEPARATION_RULE).toBe('access:update_separation_rule');
expect(FunctionCatalog.DISABLE_SEPARATION_RULE).toBe('access:disable_separation_rule');
```

### T-3.3 — Actualizar `AppRouter.test.jsx`

**Archivo:** `src/router/__tests__/AppRouter.test.jsx`

Reemplazar:
- `'adm:create_sod'` → `'adm:create_separation_rule'`
- `MANAGE_SEPARATION_RULES: 'access:view_sod'` → `MANAGE_SEPARATION_RULES: 'access:view_separation_rules'`

### T-3.4 — Actualizar `mockInterceptor.js`

**Archivo:** `src/mocks/mockInterceptor.js`

Solo cambian los valores de `codename`, no los valores de `name` (el `name`
es texto de UI en español que puede decir "Ver reglas SoD" — es narrativa,
no identificador técnico):

```javascript
// Antes
{ id: 10, codename: 'access:view_sod',    name: 'Ver reglas SoD', ... }
{ id: 28, codename: 'access:update_sod',  name: 'Actualizar regla de separación', ... }
{ id: 29, codename: 'access:disable_sod', name: 'Desactivar regla de separación', ... }
{ id: 67, codename: 'adm:create_sod',     name: 'Crear regla de separación', ... }

// Después
{ id: 10, codename: 'access:view_separation_rules',   name: 'Ver reglas SoD', ... }
{ id: 28, codename: 'access:update_separation_rule',  name: 'Actualizar regla de separación', ... }
{ id: 29, codename: 'access:disable_separation_rule', name: 'Desactivar regla de separación', ... }
{ id: 67, codename: 'adm:create_separation_rule',     name: 'Crear regla de separación', ... }
```

### T-3.5 — Actualizar `FunctionCatalogPage.test.jsx`

**Archivo:** `src/pages/admin/__tests__/FunctionCatalogPage.test.jsx`

```javascript
// Antes
fillAndSubmit('adm:create_sod')

// Después
fillAndSubmit('adm:create_separation_rule')
```

### T-3.6 — Verificación

```bash
grep -r "view_sod\|create_sod\|update_sod\|disable_sod" src/ | grep -v ".map\|.lock"
# debe retornar 0 líneas fuera de comentarios

npm test -- --coverage
```

### T-3.7 — Commit

```
fix(permissions): STD-008 §3.3 — renombrar codenames sod en catalog.js

  MANAGE_SEPARATION_RULES: 'access:view_sod'    → 'access:view_separation_rules'
  CREATE_SEPARATION_RULE:  'adm:create_sod'     → 'adm:create_separation_rule'
  UPDATE_SEPARATION_RULE:  'access:update_sod'  → 'access:update_separation_rule'
  DISABLE_SEPARATION_RULE: 'access:disable_sod' → 'access:disable_separation_rule'

Archivos: catalog.js, catalog.test.js, AppRouter.test.jsx,
  mockInterceptor.js (codename only), FunctionCatalogPage.test.jsx

Los valores name en mockInterceptor.js no cambian — son texto de UI
en español donde 'SoD' es término de dominio narrativo (STD-008 §3.3).
```

----

## FASE 4 — IACT-docs: Actualizar CNST-033 y modelo-rbac-iact.rst

**Rama:** `fix/std008-cnst033-update` en IACT-docs
**Repositorio:** IACT-docs únicamente.
**Criterio de done:** `grep -rn "SeparationOfDutiesRule\|FunctionSeparationRule" source/`
retorna 0 resultados; `grep -rn "function_separation_rules" source/` retorna 0.

### T-4.1 — Actualizar CNST-033 a v2.0.0

**Archivo:** `source/normativa/restricciones/cnst-033-vocabulario-unificado-rbac.rst`

**Cambios en el encabezado:**
```rst
:version: 2.0.0
:ultimo_cambio: 2026-05-13
```

**Cambio en la tabla de vocabulario:**
```rst
  * - Regla de Separación
    - SeparationRule
    - ``access_separation_rule``
    - (sin equivalente)
```

**Añadir entrada de historial de cambios:**
```rst
v2.0.0 (2026-05-13):
  SeparationOfDutiesRule → SeparationRule (alineación con implementación Django FASE 0).
  Tabla ``function_separation_rules`` → ``access_separation_rule`` (db_table real).
  Origen: ANALISIS-DT-RESIDUAL-STD008-20260513, DT-STD008-001.
```

### T-4.2 — Actualizar `modelo-rbac-iact.rst`

**Archivo:** `source/arquitectura-tecnica/rbac/modelo-rbac-iact.rst`

La clase `FunctionSeparationRule` con su `FunctionSeparationRuleDetail`
representa la arquitectura v5.2.1 (modelo binario de FK, ya reemplazado).
El documento debe actualizarse para reflejar el modelo v5.4.0 (M2M sets).

**Cambios mínimos necesarios:**
- Renombrar `FunctionSeparationRule` → `SeparationRule` en todas las
  referencias de clase y código pseudocode.
- Eliminar referencias a `FunctionSeparationRuleDetail` — el modelo M2M
  no usa una tabla de detalle, usa la tabla intermedia estándar de Django.
- Corregir `db_table = 'function_separation_rules'` → `db_table = 'access_separation_rule'`.
- Actualizar la lógica de validación para reflejar `functions_set_a`/
  `functions_set_b` (M2M) en lugar de `group_a`/`group_b` obtenidos
  desde `FunctionSeparationRuleDetail`.

### T-4.3 — Verificar referencias cruzadas

```bash
# Ningún archivo en source/ debe referenciar los nombres viejos
grep -rn "SeparationOfDutiesRule\|FunctionSeparationRule\|function_separation_rules" \
  source/ --include="*.rst"
```

### T-4.4 — Commit

```
docs(normativa): CNST-033 v2.0.0 + modelo-rbac-iact actualizado

CNST-033 v2.0.0:
  SeparationOfDutiesRule → SeparationRule (alineación con Django FASE 0)
  function_separation_rules → access_separation_rule (db_table real)

modelo-rbac-iact.rst:
  FunctionSeparationRule → SeparationRule
  FunctionSeparationRuleDetail eliminada (modelo M2M no usa tabla de detalle)
  Lógica de validación actualizada a functions_set_a/b M2M

Fuente: ANALISIS-DT-RESIDUAL-STD008-20260513 DT-STD008-001
```

----

## Orden de ejecución recomendado

```
FASE 1 (urgente — CI blocker)
  └─ branch: fix/dt-viewset-cleanup
  └─ PR a: develop (IACT-api)
  └─ Riesgo: Bajo (solo elimina código muerto + mejora nombres)
  └─ Tiempo estimado: 2-3 horas

FASE 2 (STD-008 §3.5 — IACT-api solo)
  └─ branch: fix/std008-spanish-endpoints
  └─ PR a: develop (IACT-api)
  └─ Riesgo: Bajo (IACT-ui no llama estos endpoints; solo tests internos)
  └─ Tiempo estimado: 1 hora

FASE 3 (STD-008 §3.3 — IACT-ui solo)
  └─ branch: fix/std008-catalog-codenames
  └─ PR a: develop (IACT-ui)
  └─ Riesgo: Bajo (no hay runtime real de estos codenames; solo tests)
  └─ Tiempo estimado: 1 hora

FASE 4 (documentación — IACT-docs solo)
  └─ branch: fix/cnst033-v2-update
  └─ PR a: develop (IACT-docs)
  └─ Riesgo: Ninguno (docs only)
  └─ Tiempo estimado: 1-2 horas
```

Las fases 2, 3 y 4 son independientes entre sí y pueden ejecutarse en
cualquier orden después de FASE 1.

----

## Criterios de aceptación globales

Cuando todas las fases están mergeadas:

```
grep -rn "SeparationRuleViewSet\|SeparationRuleCheckSerializer" \
  IACT-api/callcentersite/apps/ → 0 resultados

grep -rn "function_a\|function_b\|status.*active\|justification" \
  IACT-api/callcentersite/tests/test_data/access_test_data.py → 0 resultados
  (para los campos de SeparationRule)

grep -rn "menu-redirigidos\|menu-centro" \
  IACT-api/callcentersite/apps/ → 0 resultados

grep -rn "view_sod\|create_sod\|update_sod\|disable_sod" \
  IACT-ui/src/ → 0 resultados (fuera de comentarios)

grep -rn "SeparationOfDutiesRule\|FunctionSeparationRule\|function_separation_rules" \
  IACT-docs/source/ → 0 resultados

pytest IACT-api → 100% pass
npm test IACT-ui → 100% pass
```
