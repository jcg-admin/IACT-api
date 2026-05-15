# Hallazgos — Implementación FASE 3: codenames `sod` en catalog.js

**Artefacto:** HALLAZGOS-IMPL-FASE3-DT-RESIDUAL-20260513
**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Commit:** `885290f` en rama `claude/project-analysis-N9IkV` (IACT-ui)
**Autor:** Nestor Monroy
**Estado:** Cerrado — todos los hallazgos resueltos en este commit

----

## Resumen ejecutivo

FASE 3 se ejecutó exactamente en el alcance planeado. No se encontraron
hallazgos adicionales. 5 archivos, 13 líneas modificadas. El cambio es
un renombre puro de valores de constantes — sin impacto en la lógica
de la aplicación.

| Métrica | Antes | Después |
|---|---|---|
| Codenames con `sod` en catalog.js | 4 | 0 |
| Codenames con `sod` en mockInterceptor.js | 4 | 0 |
| Codenames con `sod` en tests | 4 | 0 |
| Total de constantes en FunctionCatalog | 66 | 66 (sin cambio) |
| Duplicados de valor en FunctionCatalog | 0 | 0 |
| Valores que violan regex `module:action` | 0 | 0 |

----

## drf-spectacular — no aplica en FASE 3

drf-spectacular es un generador de schema OpenAPI para Django REST Framework
(backend Python). FASE 3 modifica exclusivamente archivos de IACT-ui
(JavaScript/React). No hay ninguna interacción entre `catalog.js` y el
schema OpenAPI del backend.

----

## Cambios aplicados

### `src/permissions/catalog.js`

| Constante | Antes | Después |
|---|---|---|
| `MANAGE_SEPARATION_RULES` | `'access:view_sod'` | `'access:view_separation_rules'` |
| `CREATE_SEPARATION_RULE` | `'adm:create_sod'` | `'adm:create_separation_rule'` |
| `UPDATE_SEPARATION_RULE` | `'access:update_sod'` | `'access:update_separation_rule'` |
| `DISABLE_SEPARATION_RULE` | `'access:disable_sod'` | `'access:disable_separation_rule'` |

Los nombres de las constantes (claves del objeto) no cambiaron. Solo
cambiaron los valores.

### `src/permissions/__tests__/catalog.test.js`

Actualizados los 2 expects del bloque `MOD_Access extended constants`:

```javascript
// Antes
expect(FunctionCatalog.UPDATE_SEPARATION_RULE).toBe('access:update_sod');
expect(FunctionCatalog.DISABLE_SEPARATION_RULE).toBe('access:disable_sod');

// Después
expect(FunctionCatalog.UPDATE_SEPARATION_RULE).toBe('access:update_separation_rule');
expect(FunctionCatalog.DISABLE_SEPARATION_RULE).toBe('access:disable_separation_rule');
```

Los tests de `MANAGE_SEPARATION_RULES` y `CREATE_SEPARATION_RULE` no
tenían expects explícitos — están cubiertos implícitamente por el test
`it.each(entries)('%s follows module:action format')`.

### `src/router/__tests__/AppRouter.test.jsx`

Dos cambios:

1. `adminCapacidades` (array de permisos de un usuario admin de test):
```javascript
// Antes
'adm:manage_catalog', 'adm:create_sod', 'access:assign_to_group'
// Después
'adm:manage_catalog', 'adm:create_separation_rule', 'access:assign_to_group'
```

2. Objeto mock `FC` inline (réplica local del FunctionCatalog para tests):
```javascript
// Antes
MANAGE_SEPARATION_RULES: 'access:view_sod'
// Después
MANAGE_SEPARATION_RULES: 'access:view_separation_rules'
```

### `src/mocks/mockInterceptor.js`

4 campos `codename` actualizados. Los campos `name` no cambian (texto de
UI en español donde "SoD" es un término narrativo de dominio, permitido
por STD-008 §3.3 cuando el término está definido en el glosario):

| id | codename antes | codename después | name (sin cambio) |
|---|---|---|---|
| 10 | `access:view_sod` | `access:view_separation_rules` | `'Ver reglas SoD'` |
| 28 | `access:update_sod` | `access:update_separation_rule` | `'Actualizar regla de separación'` |
| 29 | `access:disable_sod` | `access:disable_separation_rule` | `'Desactivar regla de separación'` |
| 67 | `adm:create_sod` | `adm:create_separation_rule` | `'Crear regla de separación'` |

### `src/pages/admin/__tests__/FunctionCatalogPage.test.jsx`

```javascript
// Antes — test que verifica que 'adm:create_sod' pasa la validación de formato
fillAndSubmit('adm:create_sod')

// Después
fillAndSubmit('adm:create_separation_rule')
```

El test verifica que un codename con formato `modulo:accion` con underscores
pasa la validación del formulario de creación de función. El nuevo valor
`'adm:create_separation_rule'` también cumple `module:action` con underscores,
por lo que el test sigue siendo válido.

----

## Lo que NO cambió y por qué

### `src/router/AppRouter.jsx` (código de producción)

`AppRouter.jsx` usa las claves del catálogo, no los string literals:
```javascript
permission: FunctionCatalog.MANAGE_SEPARATION_RULES
permission: FunctionCatalog.CREATE_SEPARATION_RULE
```

Al cambiar el valor en `catalog.js`, `AppRouter.jsx` recoge el nuevo
valor automáticamente sin necesitar modificación. No hay hardcoding del
string `'access:view_sod'` en el código de producción.

### `name` fields en `mockInterceptor.js`

Los campos `name` como `'Ver reglas SoD'` y `'Crear regla de separación'`
son texto de interfaz de usuario. STD-008 §3.3 prohíbe `SoD/SOD/sod` en
identificadores técnicos; los valores de `name` son strings de presentación
en español donde "SoD" actúa como término narrativo de dominio, definido
en el glosario del proyecto. Estos campos no son identificadores técnicos.

----

## Nota sobre alineación futura con el backend

Cuando el endpoint `/api/permisos/verificar/{userId}/capacidades/` se
implemente en IACT-api, los valores de `catalog.js` deberán coincidir
con lo que ese endpoint retorne. Los `Function.permission_django` actuales
en el backend son:
```
ACC-005 → permission_django = 'view_separation_rules'
ACC-011 → permission_django = 'update_separation_rule'
ACC-012 → permission_django = 'disable_separation_rule'
```

Los nuevos valores en catalog.js (`access:view_separation_rules`,
`access:update_separation_rule`, `access:disable_separation_rule`)
son strings con prefijo de módulo (`access:`). La reconciliación exacta
entre el formato `module:action` de catalog.js y el campo
`permission_django` del backend quedará pendiente para cuando se
implemente el servicio de capacidades. Esta FASE 3 elimina la violación
STD-008 — la alineación completa es un trabajo separado.

----

## Verificación ejecutada

```
CRITERIO 1: grep sod en los 5 archivos modificados → 0 líneas
CRITERIO 2: Los 4 valores nuevos presentes en los 5 archivos → 13 líneas
CRITERIO 3: grep sod en todo IACT-ui/src → 0 líneas
catalog.js — Total constants: 66 (sin cambio)
catalog.js — Sin duplicados de valor
catalog.js — Todos los valores siguen regex module:action
catalog.js — Ninguna KEY contiene SOD
catalog.js — Ningún VALUE contiene sod
[DONE] FASE 3 — todos los criterios PASS
```
