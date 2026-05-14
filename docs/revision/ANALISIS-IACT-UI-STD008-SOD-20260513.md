# Análisis IACT-ui — Hallazgos para plan de remediación STD_008

**Artefacto:** ANALISIS-IACT-UI-STD008-SOD-20260513
**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Rama analizada:** `claude/project-analysis-N9IkV`
**Repositorio:** `https://github.com/jcg-admin/IACT-ui`
**Complementa:** ANALISIS-DOCS-STD008-SOD-20260513

---

## Hallazgo principal

**IACT-ui ya usa `separation-rules/` como URL.** No usa `sod-rules/` en
ningún archivo de producción. El frontend y los documentos de requisitos
convergen en el mismo nombre. El backend de FASE 2 es el único artefacto
que usa `sod-rules/`, lo que convierte este cambio en una corrección de
integración, no solo en una corrección de naming.

---

## Inventario de archivos afectados

Los archivos de producción que referencian reglas de separación son:

```
src/services/accessGateway.js        — client HTTP de access
src/services/adminGateway.js         — client HTTP de admin
src/redux/slices/access.js           — state management
src/components/access/FunctionSelector.jsx
src/components/access/SeparationRulesValidator.jsx
src/pages/access/AssignFunctions.jsx
src/pages/access/AssignGroup.jsx
src/pages/access/SeparationRules.jsx
src/router/AppRouter.jsx
src/permissions/catalog.js
```

---

## URLs que IACT-ui llama al backend

Extraídas de `accessGateway.js` y `adminGateway.js`:

| Método | URL | Función |
|---|---|---|
| GET | `/access/separation-rules` | Listar reglas |
| POST | `/access/separation-rules` | Crear regla |
| PUT | `/access/separation-rules/{id}` | Actualizar regla |
| DELETE | `/access/separation-rules/{id}` | Eliminar regla |
| POST | `/access/separation-rules/validate` | Validar conflicto antes de asignar |
| GET/POST/PATCH | `/api/admin/separation-rules/` | Alias admin panel |

**Conclusión directa:** El frontend espera el endpoint `separation-rules/`.
Nuestro backend de FASE 2 expone `sod-rules/`. La integración está rota
en este momento. El Commit 3 del plan de remediación no es solo una mejora
de naming — es una corrección de bug de integración.

---

## Estado del Redux slice

`src/redux/slices/access.js` — los campos de estado son:

```javascript
separationRules:    [],   // lista de reglas — no sodRules
separationConflicts: [],  // conflictos detectados — no sodConflicts
```

Los selectores exportados:
```javascript
export const selectSeparationRules    = (state) => state.access.separationRules;
export const selectSeparationConflicts = (state) => state.access.separationConflicts;
```

**El frontend no tiene `sodConflicts` ni `sodRules`.** El análisis de la
vista legacy del backend (`apps/access/views.py`) que mencionaba
`accessSlice.sodConflicts` era una referencia desactualizada en un
comentario — no refleja el estado actual de IACT-ui.

---

## Error codes — ninguno hardcodeado en producción

El frontend no compara error codes de separación de funciones de forma
explícita en código de producción. La única referencia a `SOD_CONFLICT`
está en `src/mocks/mockInterceptor.js` (mock de desarrollo, no producción):

```javascript
// Línea 2553 en mockInterceptor.js
return { status: 400, data: {
    error: 'Conflicto SoD',
    code: 'SOD_CONFLICT',   // solo en mock, no en producción
    ...
}}
```

El `ErrorDisplay.jsx` muestra `error.code` genéricamente sin compararlo
con un string específico. Esto significa que el cambio de
`SEPARATION_RULE_VIOLATION` en el backend **no requiere ningún cambio en
el frontend** — el frontend ya maneja errores genéricamente.

---

## Permisos — `access:view_sod` en `catalog.js`

El catálogo de permisos del frontend usa codenames legacy que contienen `sod`:

```javascript
MANAGE_SEPARATION_RULES: 'access:view_sod',
CREATE_SEPARATION_RULE:  'adm:create_sod',
UPDATE_SEPARATION_RULE:  'access:update_sod',
DISABLE_SEPARATION_RULE: 'access:disable_sod',
```

**¿Esto viola STD_008?** Los valores `'access:view_sod'`, `'adm:create_sod'`
son codenames del sistema Django (`permission_django` en el modelo `Function`).
Son identificadores legacy que el backend emite en los tokens JWT y que el
frontend usa para verificar permisos. STD_008 aplica a código nuevo; estos
son codenames heredados del modelo RBAC v5.2.1. Su cambio requiere un ADR
separado porque afecta la estructura de los tokens JWT.

**No están en el alcance del presente plan.** Se documentan como deuda.

---

## Endpoint de validación — discrepancia de URL

| Componente | URL |
|---|---|
| Frontend espera | `POST /access/separation-rules/validate` |
| Backend legacy expone | `POST /access/validate-sod` |

Esta discrepancia preexiste a FASE 2. El endpoint legacy `validate-sod`
fue excluido del plan de remediación por backward compatibility, pero los
datos de IACT-ui muestran que el frontend ya no usa esa URL — usa
`/access/separation-rules/validate`.

**Consecuencia:** La exclusión del plan debe revisarse. El endpoint
`/access/validate-sod` no tiene consumidor activo en el frontend. El
frontend ya migró a `/access/separation-rules/validate`. Ambos pueden
coexistir temporalmente pero el backend necesita implementar el nuevo
endpoint o mapear la URL.

---

## Resumen de impacto para el plan de remediación

### Cambios que el plan ya cubre correctamente

| Cambio | Estado en IACT-ui |
|---|---|
| URL `sod-rules/` → `separation-rules/` | Ya usa `separation-rules/`. Cambio urgente. |
| Slice field `separationRules` | Ya tiene el nombre correcto. Sin cambio. |
| Slice field `separationConflicts` | Ya tiene el nombre correcto. Sin cambio. |
| Error codes `SOD_*` | No los maneja explícitamente. Sin cambio en UI. |

### Cambios que el frontend ya resolvió (sin acción requerida de IACT-api)

El frontend ya usa la nomenclatura correcta en sus componentes y slice.
No hay migración de naming pendiente en IACT-ui para los artefactos que
cubre el plan.

### Deuda adicional identificada (fuera del plan)

| Elemento | Estado |
|---|---|
| `catalog.js`: `'access:view_sod'` etc. | Codenames legacy en JWT. ADR necesario. |
| Endpoint `/access/validate-sod` legacy | Sin consumidor en UI. Puede deprecarse. |
| Endpoint `/access/separation-rules/validate` | Necesario en backend. No implementado en FASE 2. |

---

## Ajuste al plan de remediación

Con estos hallazgos, el plan se ajusta de la siguiente forma:

### Commit 3 — Prioridad ALTA (no solo STD_008, también bug de integración)

El cambio `sod-rules/` → `separation-rules/` deja de ser una mejora de
naming y pasa a ser una corrección de bug. La integración IACT-api /
IACT-ui está rota actualmente porque el backend expone `sod-rules/` pero
el frontend llama `separation-rules/`.

Este commit puede y debe hacerse de inmediato, sin coordinación adicional,
porque el frontend ya espera `separation-rules/`.

### Agregar al Commit 3 — endpoint de validación

Implementar `POST /api/access/separation-rules/validate` en el backend.
Este endpoint es lo que `accessGateway.validateSeparationRules()` llama.
El backend actualmente solo expone `POST /api/access/validate-sod`, que
el frontend no usa.

El contrato que el frontend espera:

```javascript
// accessGateway.js línea 97-108
async validateSeparationRules(userId, functionId) {
    const response = await fetch(
        `${API_BASE_URL}/access/separation-rules/validate`,
        { method: 'POST', body: JSON.stringify({ userId, functionId }) }
    );
    return response.json();
    // respuesta esperada: { conflicts: [...] }
}
```

### No cambia en IACT-ui — confirmado

Los archivos de producción del frontend no requieren cambios para el
plan de remediación STD_008. El frontend ya está alineado con STD_008
en su código de producción.

---

## Cronograma actualizado (definitivo)

```
DÍA 1 — Sin dependencias externas
  ├── Commit 1: renombres internos IACT-api              [30 min]
  ├── Commit 2: migración related_names                  [15 min]
  ├── Commit 3: contrato público + endpoint validate     [30 min]
  │    ├── sod-rules/ → separation-rules/  (fix de integración)
  │    ├── error codes SOD_* → SEPARATION_*
  │    ├── event types SOD_RULE_* → SEPARATION_RULE_*
  │    ├── campo response sod_rules_evaluated → separation_rules_evaluated
  │    └── implementar POST /api/access/separation-rules/validate
  └── Commit 4: IACT-docs — 9 UCs                        [2 h]

IACT-ui: sin cambios requeridos
```
