# Análisis IACT-docs — Respuestas a las preguntas de revisión STD_008

**Artefacto:** ANALISIS-DOCS-STD008-SOD-20260513
**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Complementa:** REVISION-STD008-NAMING-SOD-20260513
**Actualiza:** PLAN-REMEDIACION-STD008-SOD-20260513

---

## Resumen ejecutivo

El análisis de `/tmp/references/IACT-docs/source` responde las cuatro
preguntas planteadas en la revisión y revela un **hallazgo adicional
de primer orden**: el nombre de clase del modelo en código —
`SeparationRule` — no es el término canónico establecido por CNST-033.

---

## Pregunta P1 — ¿Se aprueba la Opción A?

**Respuesta: Parcialmente. La URL es correcta. El error code no.**

### P1.a — La URL `separation-rules/` está confirmada por tres fuentes

**Fuente 1 — STD-007 § naming de reglas SoD:**

```
Nombres de reglas SoD: Inglés con sufijo _separation
Ejemplo: pipeline_audit_separation
```

STD-007 establece que el concepto se nombra con `_separation`. En URL
REST, kebab-case, esto se convierte en `separation-rules/`. Correcto.

**Fuente 2 — modelo-rbac-iact.rst:** La tabla de BD se llama
`function_separation_rules` y la clase del modelo de referencia es
`FunctionSeparationRule`. El segmento `separation` es el canónico.

**Fuente 3 — Router legacy existente:** El router ya registra
`separation-rules/` para `SeparationRuleViewSet`. El nombre que elegimos
con el prefijo `sod-rules/` en FASE 2 violaba incluso la convención de la
URL legacy. Al cambiar a `separation-rules/`, el endpoint FASE 2 y el
legacy unifican en la misma ruta.

### P1.b — `DUTY_SEPARATION_VIOLATION` no es el código correcto

**Problema:** `DUTY` es parte de "Separation of **Duties**", que es la
expansión literal de la abreviatura `SoD`. Incluir `DUTY` en el código de
error introduce la mitad de la abreviatura que queremos eliminar.

CNST-033 y STD-007 usan consistentemente `separation` como el término
canónico, sin mencionar `duty` en ningún identificador técnico.

**Código correcto:** `SEPARATION_RULE_VIOLATION`

Tabla de error codes actualizada:

| Error code anterior | Error code correcto |
|---|---|
| `SOD_VIOLATION` | `SEPARATION_RULE_VIOLATION` |
| `CASCADE_SOD_VIOLATION` | `CASCADE_SEPARATION_RULE_VIOLATION` |
| `SOD_RULE_DUPLICATE` | `SEPARATION_RULE_DUPLICATE` |
| `SOD_RULE_NOT_FOUND` | `SEPARATION_RULE_NOT_FOUND` |

---

## Pregunta P2 — ¿IACT-ui ya referencia SOD_VIOLATION o sod-rules/?

**Respuesta: Sí para `validate-sod` y `sodConflicts`. No para `sod-rules/`.**

El análisis del endpoint legacy en `apps/access/views.py` revela:

```python
class SeparationRuleValidateView(APIView):
    """
    accessService.validateSoD(userId, functionId)
    POST /api/access/validate-sod
    Body: { userId, functionId }

    Retorna estructura que consume accessSlice:
      { conflicts: [{ rule, ruleDesc, setA, setB, message }] }
    """
```

Esto confirma que IACT-ui tiene:
- Un método `accessService.validateSoD()` que llama `POST /api/access/validate-sod`
- Un campo de estado Redux `accessSlice.sodConflicts`

**Consecuencia directa:** La URL `validate-sod` y el campo Redux `sodConflicts`
son **contratos existentes activos con IACT-ui**. No están en el alcance
del plan de remediación STD_008 (están marcados como excluidos por backward
compatibility en el plan). Esta decisión queda confirmada.

**Respecto a `sod-rules/` (FASE 2):** Este endpoint es nuevo en FASE 2 y
**no ha sido integrado en IACT-ui**. No existe código frontend que lo
consuma actualmente. Esto significa que cambiar `sod-rules/` →
`separation-rules/` en el commit de FASE 2 **no rompe ningún cliente real**.
Es un cambio seguro sin necesidad de coordinación con IACT-ui.

**Consecuencia para el plan:** El Commit 3 del plan original marcaba los
cambios de URL, error codes y event types como "requieren coordinación con
IACT-ui". Esta restricción se levanta para todos los cambios de FASE 2
(la UI no los consume todavía). Solo se mantiene para `validate-sod` y
`sodConflicts`, que permanecen excluidos del plan.

---

## Pregunta P3 — ¿Docs en el mismo PR o PR separado?

**Respuesta: Mismo PR (o PR estrictamente coordinado).**

El `checklist-cambios-documentales.rst` establece que todo cambio requiere
actualización de trazabilidad. El `proc-dev-001-pipeline-trabajo-iact.rst`
establece que los cambios de refactoring usan rama `refactor/descripcion`
y que los tests deben seguir pasando.

El principio de fondo del proyecto es que los documentos de requisitos son
la fuente de verdad. El código debe conformar a los documentos, no a la
inversa. Esto implica:

**Regla:** los cambios de identificadores que modifican el contrato de la
API (URL, error codes, event types) deben ir acompañados de la actualización
de los documentos de requisitos en el mismo PR o en un PR previo.

Un PR que cambia `SOD_VIOLATION` → `SEPARATION_RULE_VIOLATION` en código,
pero deja los CAs de `uc-acc-01` diciendo `error == 'SOD_VIOLATION'`,
produce un estado donde el código y los docs son inconsistentes. Eso es
exactamente la situación que CNST-033 fue creado para evitar.

**Conclusión:** Los 4 commits del plan deben ir en el mismo PR o, si van
en PRs separados, el PR de IACT-docs debe preceder o coincidir con el
Commit 3 de IACT-api.

---

## Pregunta P4 — ¿El campo `sod_rules_evaluated` del response cambia?

**Respuesta: Sí cambia. Es un identificador técnico dentro del alcance STD_008.**

El campo `sod_rules_evaluated` aparece en:
- `uc-acc-01/datos-involucrados.rst` línea 74: dentro de un bloque
  `.. code-block:: json` que representa el response body
- `uc-acc-01/implementacion-tecnica.rst`: como campo de un contrato de servicio

STD-008 § 2 establece que el estándar aplica a "identificadores citados en
la documentación en bloques code-block, literal, code:". Un campo de
response JSON dentro de un `code-block` es un identificador técnico.

**Campo correcto:** `separation_rules_evaluated`

**¿Es un breaking change?** No en este momento. El endpoint
`/api/access/users/{id}/functions/assign/` es nuevo de FASE 2 y IACT-ui
no lo consume todavía. El cambio es seguro.

---

## Hallazgo adicional — CNST-033 establece un nombre de clase distinto

**Severidad: Media (inconsistencia entre artefactos canónicos)**

Al leer CNST-033 para responder P1, se encuentra que el estándar
establece:

| Término canónico en docs | Término canónico en código |
|---|---|
| Regla SoD | `SeparationOfDutiesRule` |

Sin embargo:
- Nuestro modelo Django actual: `SeparationRule`
- El modelo de referencia en `modelo-rbac-iact.rst`: `FunctionSeparationRule`
- CNST-033: `SeparationOfDutiesRule`

Los tres documentos difieren. Esta inconsistencia es **preexistente** y
no fue introducida por FASE 2. El modelo Django se llamó `SeparationRule`
desde FASE 0 y ese nombre no estaba documentado en CNST-033 cuando se
creó.

**¿Qué hacer?**

Renombrar el modelo Django de `SeparationRule` a `SeparationOfDutiesRule`
o `FunctionSeparationRule` requeriría:
- Migración de BD con `RenameModel`
- Actualización de todas las referencias en el codebase
- Una decisión entre dos nombres que los propios docs no unifican

Este hallazgo **excede el alcance del presente plan de remediación**. La
remediación STD_008 ataca los identificadores que contienen la abreviatura
`SoD`. El nombre `SeparationRule` no contiene la abreviatura. Es un
problema de inconsistencia entre artefactos, que requiere un ADR separado
para resolverlo.

**Acción propuesta:** Documentar como deuda técnica en
`risks-technical-debt/deuda-tecnica-rebuild.rst` y programar resolución
en una iteración posterior.

---

## Plan de remediación actualizado

Los hallazgos anteriores producen los siguientes cambios al plan original:

### Cambio 1 — Error code corregido

| Plan original | Plan actualizado |
|---|---|
| `SOD_VIOLATION` → `DUTY_SEPARATION_VIOLATION` | `SOD_VIOLATION` → `SEPARATION_RULE_VIOLATION` |
| `CASCADE_SOD_VIOLATION` → `CASCADE_DUTY_SEPARATION_VIOLATION` | `CASCADE_SOD_VIOLATION` → `CASCADE_SEPARATION_RULE_VIOLATION` |

### Cambio 2 — El Commit 3 ya no requiere coordinación con IACT-ui

Los endpoints de FASE 2 (`sod-rules/`, error codes asociados) no son
consumidos por IACT-ui. El Commit 3 puede ejecutarse libremente sin
sincronizar con el frontend.

El único elemento que sí requiere coordinación (excluido del plan) es
`validate-sod` / `accessSlice.sodConflicts`, que permanece sin cambios.

### Cambio 3 — Campo de response añadido al alcance

El campo `sod_rules_evaluated` → `separation_rules_evaluated` se agrega al
Commit 3 (en el cuerpo del response de `FunctionAssignView`) y al Commit 4
(en los documentos de uc-acc-01).

### Cambio 4 — Cronograma simplificado

```
DÍA 1
  ├── Commit 1: identificadores internos         [~30 min]
  ├── Commit 2: migración related_names          [~15 min]
  └── Commit 3: contrato público                 [~20 min]  ← ya no requiere esperar IACT-ui
       ├── URL sod-rules/ → separation-rules/
       ├── Error codes SOD_* → SEPARATION_*
       ├── Event types SOD_RULE_* → SEPARATION_RULE_*
       └── Campo response sod_rules_evaluated → separation_rules_evaluated

DÍA 1-N (paralelo o justo después)
  └── Commit 4: IACT-docs — 9 UCs               [~2 h con script sed]
```

Los 4 commits pueden hacerse el mismo día. No hay dependencia bloqueante
con IACT-ui.

### Cambio 5 — Tabla maestra de sustituciones en documentación (actualizada)

Añadir al Commit 4:

| Antes | Después | UCs |
|---|---|---|
| `SOD_VIOLATION` | `SEPARATION_RULE_VIOLATION` | uc-acc-01, uc-acc-04, uc-acc-08, uc-perm-06, uc-perm-09 |
| `CASCADE_SOD_VIOLATION` | `CASCADE_SEPARATION_RULE_VIOLATION` | uc-perm-06 |
| `sod_rules_evaluated` | `separation_rules_evaluated` | uc-acc-01, uc-acc-08 |

(El resto de la tabla del plan original permanece sin cambios.)

---

## Deuda técnica identificada (fuera del plan)

**DT-STD008-001:** Inconsistencia entre CNST-033 (`SeparationOfDutiesRule`),
modelo-rbac-iact.rst (`FunctionSeparationRule`) y el modelo Django actual
(`SeparationRule`). Requiere ADR para unificar. No bloquea el presente plan.

Registrar en: `risks-technical-debt/deuda-tecnica-rebuild.rst`
