# Análisis — Deuda técnica residual STD_008 §3.3

**Artefacto:** ANALISIS-DT-RESIDUAL-STD008-20260513
**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Autor:** Nestor Monroy
**Fuentes consultadas:** CNST-033, modelo-rbac-iact.rst, modelo-dominio-iact.rst,
  views.py, catalog.js, usePermisos.ts, permisos-client.ts, api.config.ts,
  test_separation_rule_viewset.py, access_test_data.py

----

## Resumen ejecutivo

El análisis confirma que las tres descripciones de DT-STD008-001,
DT-STD008-002 y DT-STD008-003 en el documento de cierre (HALLAZGOS-FASE5)
son parcialmente inexactas. Tras leer las fuentes primarias se identifican:

| Item | Clasificación original | Clasificación real |
|---|---|---|
| DT-STD008-001 | Inconsistencia de nombre de clase | **Correcto, pero la causa está en CNST-033 desactualizado — la norma es la que falla, no el modelo** |
| DT-STD008-002 | Codenames JWT legacy | **Incorrecto: no hay JWT. El sistema usa DRF token. El problema es más simple y no requiere rotación de tokens.** |
| DT-STD008-003 | Clase deprecated pendiente | **Subestimado: hay un test suite roto que causa fallas en CI.** |

----

## DT-STD008-001 — Inconsistencia de nombre de clase

### Estado real

Cuatro fuentes definen el nombre de la clase con valores distintos:

| Fuente | Nombre de clase | Tabla de BD |
|---|---|---|
| CNST-033 v1.0.0 (Vigente) | `SeparationOfDutiesRule` | `function_separation_rules` |
| modelo-rbac-iact.rst | `FunctionSeparationRule` | `function_separation_rules` |
| modelo-dominio-iact.rst | `SeparationRule` | — |
| Django implementation | `SeparationRule` | `access_separation_rule` |

El modelo Django y el modelo de dominio coinciden en `SeparationRule`.
Los documentos de arquitectura (modelo-rbac-iact.rst) y la normativa
CNST-033 divergen de la implementación.

### Por qué el nombre CNST-033 es peor que el actual

CNST-033 define `SeparationOfDutiesRule`. Este nombre:

1. Expande semánticamente la abreviatura `SoD` ("Separation of Duties").
   Aunque no es la abreviatura en sí (y por tanto no viola STD_008 §3.3
   en su letra), compromete la intención de STD_008 §3.3 al anclar el
   nombre del dominio a la expansión de la sigla prohibida.

2. Es más largo que `SeparationRule` sin añadir expresividad. El
   concepto "of duties" es redundante cuando el contexto de la clase
   (módulo `access`, campo `SeparationRule.code = 'SOD-001'`) ya establece
   que se trata de separación de funciones de negocio.

3. Diverge del vocabulario que usa el resto del sistema: el modelo de
   dominio, las vistas FASE 2/3, los serializers, los tests y los docs
   FASE 4 ya usan `SeparationRule`.

### Causa raíz

CNST-033 fue redactado antes de que el modelo Django se estabilizara en
FASE 0. El nombre `SeparationOfDutiesRule` era el candidato conceptual;
la implementación eligió `SeparationRule` por brevedad y expresividad.
CNST-033 nunca se actualizó tras ese cambio.

La tabla de BD también diverge: CNST-033 dice `function_separation_rules`,
el modelo Django tiene `db_table = 'access_separation_rule'`.

### Acción requerida

CNST-033 debe actualizarse a v2.0.0 con la siguiente corrección:

```
ANTES:
  * - Regla SoD
    - SeparationOfDutiesRule
    - ``function_separation_rules``
    - (sin equivalente)

DESPUÉS:
  * - Regla de Separación
    - SeparationRule
    - ``access_separation_rule``
    - (sin equivalente)
```

**No se requiere `RenameModel` en Django.** El modelo Django ya usa
el nombre correcto. Solo se actualiza la normativa CNST-033 y el
documento arquitectónico modelo-rbac-iact.rst para que reflejen la
implementación real.

**Alcance:** CNST-033, modelo-rbac-iact.rst.
**No requiere ADR separado:** es una corrección de documentación que
elimina la inconsistencia, no un cambio de decisión arquitectónica.
**Prioridad:** Media — no causa fallos en runtime ni en tests.

----

## DT-STD008-002 — Codenames con `sod` en catalog.js (IACT-ui)

### Estado real — la descripción original era inexacta

La descripción en HALLAZGOS-FASE5 decía "requieren ADR + rotación de
tokens". Esto es incorrecto. Tras leer el código:

**El sistema NO usa JWT.** Usa DRF token authentication (cabecera
`Authorization: Token <token>`). No hay tokens JWT que rotar.

### Los cuatro codenames afectados

```javascript
// src/permissions/catalog.js
MANAGE_SEPARATION_RULES: 'access:view_sod',
CREATE_SEPARATION_RULE:  'adm:create_sod',
UPDATE_SEPARATION_RULE:  'access:update_sod',
DISABLE_SEPARATION_RULE: 'access:disable_sod',
```

### Cómo se usan actualmente — flujo completo

**Ruta A — Filtro del menú de navegación (`usePermisos` + `hasPermission`):**

```
AppRouter.jsx
  → usePermisos()
    → PermisosClient.getCapacidades(userId)
      → GET /api/permisos/verificar/{userId}/capacidades/
```

Este endpoint **no existe en el backend actual**. El backend no tiene
ninguna ruta registrada en `/api/permisos/verificar/`. Resultado: la
llamada falla silenciosamente, `capacidades = []`, todos los items del
menú se filtran como si el usuario no tuviera permisos. El sistema de
filtrado de menú no funciona en producción.

**Ruta B — `ProtectedRoute` (guard de ruta):**

```jsx
// ProtectedRoute.jsx — implementación actual
function ProtectedRoute({ children }) {
  const isAuthenticated = useSelector(selectIsAuthenticated);
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return children;
}
```

`ProtectedRoute` **ignora completamente** el prop `permission`. Solo
verifica si el usuario está autenticado. Los valores `'access:view_sod'`
pasados como `permission=` en AppRouter.jsx no se evalúan en ningún
momento.

**Conclusión:** los codenames `sod` en catalog.js no causan fallos en
runtime. El filtrado de menú está roto por un motivo diferente (endpoint
inexistente), y la protección de rutas solo verifica autenticación.

### El problema real de los codenames

Los valores `'access:view_sod'`, `'adm:create_sod'`, etc. son:

1. **Violaciones de STD_008 §3.3** — contienen `sod` en identificadores
   técnicos JavaScript (claves de objeto y valores de string que funcionan
   como constantes de permisos).

2. **Desconectados del backend.** Los `Function.permission_django` reales son:
   ```
   ACC-005 → permission_django = 'view_separation_rules'
   ACC-011 → permission_django = 'update_separation_rule'
   ACC-012 → permission_django = 'disable_separation_rule'
   ```
   Los valores de catalog.js no coinciden con ningún campo del backend.
   Cuando el endpoint `/api/permisos/verificar/` se implemente, necesitará
   retornar alguno de estos campos (probablemente `Function.permission_django`
   o `Function.code`) y catalog.js tendrá que estar alineado.

3. **Hardcodeados en tests y mocks:**
   ```
   // test_separation_rule_viewset.py
   fn = FunctionTestData(code='access.view_separation_rules', ...)
   
   // AppRouter.test.jsx
   MANAGE_SEPARATION_RULES: 'access:view_sod'
   
   // mockInterceptor.js
   { id: 10, codename: 'access:view_sod', name: 'Ver reglas SoD' }
   ```

### Acción requerida — mucho más simple que lo documentado

No se requiere ADR. No se requiere rotación de tokens. Se requiere:

**A. Actualizar `catalog.js`** — renombrar los 4 valores:

```javascript
// ANTES                                  → DESPUÉS
MANAGE_SEPARATION_RULES: 'access:view_sod'   → 'access:view_separation_rules'
CREATE_SEPARATION_RULE:  'adm:create_sod'    → 'adm:create_separation_rule'
UPDATE_SEPARATION_RULE:  'access:update_sod' → 'access:update_separation_rule'
DISABLE_SEPARATION_RULE: 'access:disable_sod'→ 'access:disable_separation_rule'
```

**B. Propagar el cambio a los archivos que hardcodean los valores:**
- `AppRouter.test.jsx` — mock de catalog
- `mockInterceptor.js` — fixtures de funciones
- `FunctionCatalogPage.test.jsx` — `fillAndSubmit('adm:create_sod')`
- `catalog.test.js` — expects hardcodeados

**C. Documentar la convención:** cuando el endpoint `/api/permisos/verificar/`
se implemente, sus valores deberán ser `Function.permission_django` del backend
(`'view_separation_rules'`, `'update_separation_rule'`, `'disable_separation_rule'`).
Los valores en catalog.js deben coincidir con lo que ese endpoint retorne.

**Prioridad:** Alta desde STD_008 §3.3. Baja desde impacto funcional
(los codenames no se evalúan en runtime en producción). Sin riesgo de
regresión si se hace correctamente (solo renombre de constantes).

**Alcance de archivos:**
```
src/permissions/catalog.js
src/permissions/__tests__/catalog.test.js
src/router/AppRouter.test.jsx
src/mocks/mockInterceptor.js
src/pages/admin/__tests__/FunctionCatalogPage.test.jsx
```

----

## DT-STD008-003 — SeparationRuleViewSet deprecated

### Estado real — más grave de lo documentado

La descripción original decía "pendiente de eliminación formal tras
confirmar ausencia de consumidores". Tras leer el código hay tres
problemas activos, no uno:

### Problema A — Test suite roto (CI blocker)

`tests/unit/access/test_separation_rule_viewset.py` tiene **dos errores
que causan fallo de CI**:

**Error 1 — URL inexistente:**
```python
url = reverse('access:separationrule-check-conflict')
# → NoReverseMatch: el ViewSet fue removido del router en FASE 3
```

**Error 2 — Factory con campos del modelo viejo:**
```python
# tests/test_data/access_test_data.py
class SeparationRuleTestData(DjangoModelFactory):
    function_a = factory.SubFactory(FunctionTestData)   # campo no existe
    function_b = factory.SubFactory(FunctionTestData)   # campo no existe
    status     = 'active'                               # campo no existe
```
→ `TypeError: SeparationRule() got unexpected keyword arguments: 'function_a', 'function_b', 'status'`

Estos errores se confirmaron mediante ejecución directa:
```
NoReverseMatch: Reverse for 'separationrule-check-conflict' not found.
SeparationRuleTestData() → TypeError: unexpected keyword arguments: 'function_a', 'function_b', 'justification', 'status'
```

**El test file completo es inejectable y bloquea el pipeline de CI.**

### Problema B — SeparationRuleViewSet es inalcanzable

El ViewSet fue removido del router en FASE 3 para eliminar la colisión
de `operationId` en drf-spectacular. Consecuencias:

- Ninguna URL resuelve a ningún método del ViewSet
- `SeparationRuleCheckSerializer` (en `separation_rule_serializers.py`)
  es código muerto — retorna `tiene_conflicto`/`regla`, que no coincide
  con la estructura actual del endpoint canónico `separation-rules/validate`
- Los dos `@extend_schema_view` sobre el ViewSet (uno con summaries normales,
  uno con `[DEPRECATED]`) son código muerto

### Problema C — Docstring incorrecto en el ViewSet

El ViewSet dice:

```python
"""
...
Se eliminará en FASE 3 de remediación.
"""
```

No fue eliminado en FASE 3. El docstring contiene una promesa incumplida.

### Acción requerida — prioridad Alta (CI blocker)

**Paso 1 (urgente, CI blocker):**
Eliminar `tests/unit/access/test_separation_rule_viewset.py` o reescribirlo
para probar el endpoint canónico:
- Reemplazar `reverse('access:separationrule-check-conflict')` por
  `reverse('access:separation-rule-validate')`
- Reemplazar `SeparationRuleTestData(function_a=..., ...)` por el patrón
  correcto con `functions_set_a`, `functions_set_b`
- Actualizar assertions: `tiene_conflicto`/`regla` → `conflicts`

**Paso 2 (urgente, CI blocker):**
Actualizar `SeparationRuleTestData` en `access_test_data.py` para eliminar
los campos del modelo viejo (`function_a`, `function_b`, `status`, `justification`).

**Paso 3 (en el mismo PR):**
Eliminar de `views.py`:
- `class SeparationRuleViewSet` (90 líneas)
- Los dos `@extend_schema_view` redundantes sobre el ViewSet
- El `@action check_conflict` dentro del ViewSet

Eliminar de `separation_rule_serializers.py`:
- `class SeparationRuleCheckSerializer` (código muerto)

Eliminar de `serializers/__init__.py`:
- `SeparationRuleSerializer` de las exportaciones

Verificar antes del PR que drf-spectacular no genera nuevas advertencias
tras la eliminación.

----

## Tabla consolidada de acciones requeridas

| Item | Prioridad | Requiere ADR | Blocker CI | Archivos afectados |
|---|---|---|---|---|
| DT-001 — Actualizar CNST-033 | Media | No | No | CNST-033, modelo-rbac-iact.rst |
| DT-002 — Renombrar codenames catalog.js | Alta (STD_008) / Baja (funcional) | No | No | catalog.js + 4 archivos de test/mock |
| DT-003 — Eliminar test roto | **Urgente** | No | **Sí** | test_separation_rule_viewset.py, access_test_data.py |
| DT-003 — Eliminar código muerto | Alta | No | No | views.py, separation_rule_serializers.py, serializers/__init__.py |

----

## Correcciones a HALLAZGOS-FASE5

La descripción en HALLAZGOS-FASE5-STD008-SOD-20260513.md debe actualizarse:

**DT-STD008-002 (was):**
> "requieren ADR + rotación de tokens"

**DT-STD008-002 (corrected):**
> Requieren renombre de 4 constantes en catalog.js y propagación a 4
> archivos de test/mock en IACT-ui. Sin ADR. Sin rotación de tokens
> (el sistema usa DRF token auth, no JWT).

**DT-STD008-003 (was):**
> "pendiente de eliminación formal tras confirmar ausencia de consumidores"

**DT-STD008-003 (corrected):**
> Blocker de CI activo: `test_separation_rule_viewset.py` falla en runtime
> por URL inexistente y factory con campos del modelo v5.2.1 ya eliminados.
> Requiere corrección urgente antes de mergear la rama a `develop`.
