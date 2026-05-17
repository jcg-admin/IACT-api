# Hallazgos — Implementación FASE 4: CNST-033 v2.0.0 + modelo-rbac-iact.rst

**Artefacto:** HALLAZGOS-IMPL-FASE4-DT-RESIDUAL-20260513
**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Repositorio:** IACT-docs (sin git en referencia local — commit pendiente en rama develop)
**Autor:** Nestor Monroy
**Estado:** Cerrado — cambios aplicados; commit requiere acceso al repositorio real

----

## Resumen ejecutivo

FASE 4 afecta tres archivos RST. No se encontraron hallazgos funcionales
adicionales al plan. Se encontró un hallazgo de naturaleza técnica:
el directorio de referencia de IACT-docs no tiene repositorio git
inicializado, por lo que el commit formal debe ejecutarse desde el
working directory real del proyecto.

| Métrica | Antes | Después |
|---|---|---|
| CNST-033 versión | 1.0.0 | 2.0.0 |
| CNST-033 `:ultimo_cambio:` | 2026-04-29 | 2026-05-13 |
| `SeparationOfDutiesRule` en docs activos | 1 | 0 |
| `FunctionSeparationRule` en pseudocode activo | 4 | 0 |
| `FunctionSeparationRuleDetail` en pseudocode activo | 3 | 0 |
| `function_separation_rules` como tabla actual | 3 (DDL) | 0 |
| `function_separation_rule_details` como tabla actual | 2 (DDL) | 0 |
| `access_separation_rule` en DDL | 0 | 1 |
| Tablas M2M documentadas | 0 | 2 |
| Archivos RST modificados | 0 | 3 |

----

## drf-spectacular — no aplica en FASE 4

FASE 4 modifica exclusivamente archivos RST de IACT-docs. No hay
generación de schema OpenAPI ni interacción con drf-spectacular.

----

## Hallazgo H-F4-001 — IACT-docs sin repositorio git en referencia local

**Detectado en:** ejecución del commit al final de los cambios
**Impacto:** el commit formal no puede ejecutarse desde `/tmp/references/IACT-docs`
**Causa:** el directorio de referencia es un snapshot del contenido,
no un working tree git. IACT-api e IACT-ui sí tienen `.git` en sus
referencias; IACT-docs no.
**Resolución:** los cambios están aplicados en los tres archivos RST.
El commit debe ejecutarse desde el directorio real del proyecto
IACT-docs en la máquina de desarrollo:

```bash
cd <ruta-real-IACT-docs>
git add source/normativa/restricciones/cnst-033-vocabulario-unificado-rbac.rst
git add source/arquitectura-tecnica/rbac/modelo-rbac-iact.rst
git add source/normativa/gobernanza/adr-gob-009-rbac-modelo-conceptual.rst
git commit -m "docs(normativa): STD-008 DT-STD008-001 FASE 4 — CNST-033 v2.0.0 + modelo v5.4.0"
```

----

## Cambios aplicados

### `cnst-033-vocabulario-unificado-rbac.rst` — v2.0.0

**Metadata actualizada:**
```rst
:version: 2.0.0
:ultimo_cambio: 2026-05-13
```

**Tabla §2.1 — fila "Regla SoD" corregida:**

| Campo | Antes | Después |
|---|---|---|
| Término canónico (docs) | Regla SoD | Regla de Separacion |
| Término en código | `SeparationOfDutiesRule` | `SeparationRule` |
| Término legacy v5.2.1 | `function_separation_rules` | `access_separation_rule` |

`SeparationOfDutiesRule` era incorrecto desde la FASE 0: la clase Django
real siempre se llamó `SeparationRule`. `function_separation_rules` era
el nombre de la tabla v5.2.1; el `db_table` real desde v5.4.0 es
`access_separation_rule`.

**Historial §9 — entrada v2.0.0 añadida:**
```rst
* - 2.0.0
  - 2026-05-13
  - NestorMonroy
  - Alineacion con implementacion Django FASE 0 (modelo v5.4.0).
    SeparationOfDutiesRule → SeparationRule
    function_separation_rules → access_separation_rule
    Origen: ANALISIS-DT-RESIDUAL-STD008-20260513 item DT-STD008-001.
```

---

### `modelo-rbac-iact.rst` — 9 ubicaciones

**§ Lista de tablas (antes del §8):**

Antes:
```
6. **``function_separation_rules``** - 3 reglas SoD
7. **``function_separation_rule_details``** - Detalle SoD (grupos A/B)
```

Después:
```
6. **``access_separation_rule``** - 3 reglas SoD (M2M sets v5.4.0)
```

La línea de `function_separation_rule_details` fue eliminada porque
la tabla de detalle no existe en v5.4.0. El modelo M2M usa tablas
intermedias auto-gestionadas por Django.

**§8.6 — CREATE TABLE (reescrita para v5.4.0):**

Antes: `CREATE TABLE function_separation_rules` con columnas v5.2.1
(`restriction_id`, `active`, `cnst_reference`, `reason`).

Después: `CREATE TABLE access_separation_rule` con columnas v5.4.0
(`code`, `state`, `created_by_id`, `created_at`, `updated_at`).

**§8.7 — Tablas M2M (completamente nueva):**

La sección `8.7 Tabla function_separation_rule_details` fue reemplazada
por `8.7 Tablas M2M de conjuntos de funciones (v5.4.0)`. Se documenta
el esquema de las dos tablas intermedias auto-generadas por Django:
`access_separation_rule_functions_set_a` y
`access_separation_rule_functions_set_b`.

**§8.8 INSERT datos iniciales:**

`INSERT INTO function_separation_rules ... (restriction_id, reason, cnst_reference)`
fue reemplazado por `INSERT INTO access_separation_rule (code, name, description, state)`.
Los tres bloques `INSERT INTO function_separation_rule_details` fueron
eliminados. Una nota indica que los conjuntos M2M se cargan via
`manage.py create_separation_rules`.

**§9.1 Models — pseudocode Python:**

`FunctionSeparationRule` (con campos `restriction_id`, `active`, `reason`,
`cnst_reference`) y `FunctionSeparationRuleDetail` (FK a `FunctionSeparationRule`,
`rule_group`) fueron reemplazados por `SeparationRule` con campos
`code`, `state`, `functions_set_a`/`functions_set_b` (M2M), `created_by`,
`created_at`, `updated_at`. El `db_table` dice `access_separation_rule`.

El docstring de `SeparationRule` incluye una nota Hallazgo F0-H-003
que referencia `FunctionSeparationRule` y `FunctionSeparationRuleDetail`
en contexto histórico. Esto es documentación de por qué se reestructuró
el modelo, no un nombre activo.

**§9.2 Service — imports:**

```python
# Antes
from .models import (
    ...
    FunctionSeparationRule,
    FunctionSeparationRuleDetail,
)

# Después
from .models import (
    ...
    SeparationRule,
)
```

**§9.2 Service — `validate_separation_rules`:**

El patrón de validación v5.2.1 iteraba sobre `FunctionSeparationRuleDetail`
con `d.rule_group == 'A'` para construir `group_a`/`group_b`. El patrón
v5.4.0 usa `rule.functions_set_a.values_list('code', flat=True)` directamente.

```python
# Antes (v5.2.1)
active_rules = FunctionSeparationRule.objects.filter(active=True)
for rule in active_rules:
    details = FunctionSeparationRuleDetail.objects.filter(rule=rule)
    group_a = set(d.function.function_id for d in details if d.rule_group == 'A')
    group_b = set(d.function.function_id for d in details if d.rule_group == 'B')

# Después (v5.4.0)
active_rules = SeparationRule.objects.filter(state=SeparationRule.STATE_ENABLED)
for rule in active_rules:
    codes_set_a = set(rule.functions_set_a.values_list('code', flat=True))
    codes_set_b = set(rule.functions_set_b.values_list('code', flat=True))
```

**§11.2 Migration — nota histórica añadida:**

Los tres `UPDATE function_separation_rules` son parte del script de
migración v5.2.0 → v5.2.1 (renombrar campos del español al inglés).
Se añadió un bloque de comentarios SQL antes de ellos que explicita:
- Estos UPDATE son históricos (script v5.2.0→v5.2.1)
- La tabla fue reemplazada por `access_separation_rule` en v5.4.0
- La migración v5.2.1→v5.4.0 la gestionan las migraciones Django de IACT-api

El `ALTER TABLE function_separation_rule_details` fue comentado con nota
explicativa. Los `ALTER TABLE` para `user_function_assignments` y
`user_function_group_assignments` permanecen activos (esas tablas sí existen).

---

### `adr-gob-009-rbac-modelo-conceptual.rst`

Sección §2.2 "Vocabulario canónico (CNST-033)":
```rst
# Antes
- **"FunctionSeparationRule"** — regla SoD entre funciones.

# Después
- **"SeparationRule"** — regla SoD entre funciones (modelo v5.4.0 M2M).
```

----

## Lo que NO cambió y por qué

### `gestion/evidencia/rbac-historia/` (dos archivos)

Los documentos de evidencia histórica tienen `:estado: Aprobado` y
pertenecen al directorio de archivos históricos. CNST-033 §6.1 establece:
"Documentos históricos/archivados — no se reescribe el pasado."
Las referencias a `function_separation_rules` y
`function_separation_rule_details` en estos archivos son correctas para
el momento en que fueron escritos (v5.2.1).

### `cnst-030-reglas-de-separacion-de-funciones-sod.rst`

CNST-030 usa `SoDRule` como nombre de clase en su pseudocode de ejemplo
(línea 73: `Modelo SoDRule con campos group_a, group_b, rationale`).
Este nombre no coincide ni con `FunctionSeparationRule` ni con
`SeparationRule` — es un nombre simbólico propio del pseudocode de CNST-030
que describe el concepto, no la implementación. No es una violación de
nomenclatura.

----

## Verificación de referencias cruzadas

Búsqueda exhaustiva en todos los RST de `source/` (excluida `rbac-historia/`):

```bash
grep -rn "SeparationOfDutiesRule" source/ --include="*.rst"
# → 0 resultados fuera de cnst-033 §9 (changelog que documenta el rename)

grep -rn "FunctionSeparationRule\b" source/ --include="*.rst"
# → modelo-rbac-iact.rst:2084 (docstring histórico Hallazgo F0-H-003) — intencional
# → adr-gob-009.rst:109 → CAMBIADO a SeparationRule

grep -rn "function_separation_rules" source/ --include="*.rst"
# → modelo-rbac-iact.rst: solo en comentarios históricos SQL y notas v5.4.0
```

----

## Commit recomendado

```
docs(normativa): STD-008 DT-STD008-001 FASE 4 — CNST-033 v2.0.0 + modelo v5.4.0

CNST-033 v2.0.0:
  SeparationOfDutiesRule → SeparationRule (clase Django real)
  function_separation_rules → access_separation_rule (db_table real)

modelo-rbac-iact.rst:
  §8.6 SQL DDL: access_separation_rule (v5.4.0)
  §8.7 SQL DDL: tablas M2M functions_set_a/functions_set_b
  §8.8 INSERT: access_separation_rule (código/state)
  §9.1 Models: SeparationRule con M2M (elimina FunctionSeparationRule/Detail)
  §9.2 Service: SeparationRule.STATE_ENABLED + M2M values_list pattern

adr-gob-009: FunctionSeparationRule → SeparationRule

No modificados (CNST-033 §6.1): gestion/evidencia/rbac-historia/
CNST-030: usa SoDRule simbólico propio — no afectado
drf-spectacular: no aplica (solo docs RST)
```
