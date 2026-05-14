# Revisión STD_008 — Abreviatura SoD en identificadores técnicos

**Documento:** REVISION-STD008-NAMING-SOD-20260513
**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Para revisión de:** Nestor Monroy + Coatl (2-Coatl)
**Rama afectada:** `develop`
**Estado:** Pendiente de decisión antes de proceder

---

## 1. Contexto del problema

Durante la implementación de FASE 2, el endpoint de reglas de separación
de deberes se nombró `sod-rules/`. En la revisión posterior, se identificó
que este identificador viola el estándar normativo **STD_008** vigente.

El documento de referencia es:

```
IACT-docs/source/normativa/estandares/std-008-naming-identificadores.rst
Versión: 1.1.0
Estado:  Aprobado
Fecha:   2026-04-28
```

El análisis que sigue documenta el alcance exacto de la violación, la
decisión de diseño que debe tomarse, y el inventario de cambios requeridos
tanto en el código como en los documentos de requisitos.

---

## 2. Norma violada

**STD_008 § 3.3 — Sin Abreviaturas de Dominio en Identificadores**

Transcripción literal de la regla:

> **Regla obligatoria:** las abreviaturas de dominio de negocio o de
> framework (`SoD`, `RBAC`, `ETL`, `PII`, `KPI`, `RTM`, etc.) **NO
> deben aparecer en identificadores técnicos**.
>
> La razón: una abreviatura en un identificador obliga al lector a conocer
> el dominio del cual proviene la abreviatura para entender qué hace el
> código. Esto es un acoplamiento de conocimiento implícito que rompe el
> principio de autoexplicativo (sección 3.2).

El estándar da el contraejemplo exactamente aplicable a este caso:

| Correcto | Incorrecto |
|---|---|
| `validateRoleConflict(...)` | `validateSoD(...)` — SoD es abreviatura de dominio |

**STD_008 § 3.5** incluye los endpoints REST dentro del alcance:

> Los identificadores técnicos del proyecto IACT se escriben en inglés.
> Esto incluye: [...] **Endpoints REST**.

`sod-rules/` es un endpoint REST → está dentro del alcance.

---

## 3. Magnitud de la violación

La violación no es solo del endpoint. El prefijo `SoD` se propagó
sistemáticamente a través de tres niveles independientes:

### 3.1 En el código IACT-api (rama develop, FASE 2)

**102 líneas afectadas** en dos apps:

```
apps/access  —  99 líneas
apps/audit   —   3 líneas
```

Inventario exacto por categoría:

| Categoría | Identificador actual | Cantidad |
|---|---|---|
| Nombre de archivo | `sod_rule_view.py` | 1 |
| Clases de vista | `SoDRuleListCreateView`, `SoDRuleDetailView` | 2 |
| Serializers | `SoDRuleCreateSerializer`, `SoDRulePatchSerializer`, `SoDRuleRetireSerializer` | 3 |
| Clase de servicio | `SoDValidator` | 1 |
| URL path | `sod-rules/`, `sod-rules/<int:rule_id>/` | 2 |
| URL names | `sod-rule-list-create`, `sod-rule-detail` | 2 |
| Import en urls.py | `from .sod_rule_view import SoDRuleListCreateView, SoDRuleDetailView` | 1 |
| Error codes en responses | `SOD_RULE_DUPLICATE`, `SOD_RULE_NOT_FOUND`, `SOD_VIOLATION` | 3 |
| Event types en VALID_EVENT_TYPES | `SOD_RULE_CREATED`, `SOD_RULE_UPDATED`, `SOD_RULE_DISABLED` | 3 |

### 3.2 En los documentos de requisitos IACT-docs

**237 líneas afectadas** en 9 UCs distintos:

| UC | Líneas | Qué usa |
|---|---|---|
| `uc-acc-05` | 127 | URL `/api/access/sod-rules/`, `SOD_RULE_*`, `SoDRule`, `SoDRuleRepository`, `SoDRuleCache` |
| `uc-acc-01` | 52 | `SOD_VIOLATION`, `SoDRule`, `sod_rules_evaluated` |
| `uc-acc-04` | 16 | `SOD_VIOLATION`, referencia a `SoDRule` |
| `uc-acc-08` | 12 | `SOD_VIOLATION`, `CASCADE_SOD_VIOLATION` |
| `uc-acc-03` | 11 | Referencias a `SoDRule` |
| `uc-perm-06` | 10 | `CASCADE_SOD_VIOLATION`, `SoDRuleRepository` |
| `uc-acc-09` | 7 | `SOD_RULE_*` en audit events |
| `uc-perm-03` | 1 | `SoDRule` |
| `uc-perm-09` | 1 | `SOD_VIOLATION` |

**Causa raíz del conflicto:** Los documentos de requisitos se redactaron
**antes** de la aprobación de STD_008 (los UCs son anteriores a
2026-04-28). El estándar no existía cuando se escribieron los contratos.
Esto no es un error de los autores de los UCs — es una deuda de
sincronización acumulada al aprobar STD_008 sin revisar los artefactos
existentes.

---

## 4. El problema de decisión

Esta revisión no puede resolverse unilateralmente porque involucra
**un cambio de contrato de API pública**. El problema tiene dos
dimensiones:

### 4.1 Dimensión técnica

Los identificadores que deben cambiar son de dos tipos con consecuencias
distintas:

**Tipo A — Identificadores internos** (bajo riesgo):
Nombres de archivos, clases, serializers, variables. Solo afectan al
código del backend. Se renombran con un commit, sin efecto externo.

```
sod_rule_view.py         → separation_rule_view.py
SoDRuleListCreateView    → SeparationRuleListCreateView
SoDRuleDetailView        → SeparationRuleDetailView
SoDRuleCreateSerializer  → SeparationRuleCreateSerializer
SoDValidator             → DutySeparationValidator
```

**Tipo B — Identificadores de contrato público** (requieren coordinación):
URL paths, nombres de url, error codes, event types. Cualquier cliente
que consuma la API (IACT-ui) depende de estos valores.

```
Endpoint:   /api/access/sod-rules/     → /api/access/separation-rules/
Error code: SOD_VIOLATION              → ?
Error code: SOD_RULE_DUPLICATE         → ?
Event type: SOD_RULE_CREATED           → ?
```

Para los identificadores de Tipo B, el cambio necesita:
1. Decidir los nombres correctos según STD_008
2. Actualizar IACT-ui (`accessService.js`, `accessSlice.js`, cualquier
   constante que use estos valores)
3. Actualizar los documentos de requisitos en IACT-docs (los 9 UCs
   listados en § 3.2)
4. Actualizar el backend en IACT-api

El trabajo es coordinado — no puede hacerse solo en el backend.

### 4.2 Dimensión conceptual: ¿cuál es el nombre correcto?

STD_008 prohíbe `SoD` pero no prescribe el reemplazo. Hay que decidir
cuál es el nombre que "revela intención" (STD_008 § 3.1) para este concepto.

El concepto que `SoD` abrevia es: **"una regla que prohíbe que un mismo
usuario tenga dos conjuntos de funciones que juntos crean un conflicto de
interés operativo"**.

Opciones evaluadas:

| Opción | URL | Error | Pros | Contras |
|---|---|---|---|---|
| A | `separation-rules/` | `DUTY_SEPARATION_VIOLATION` | Traduce literalmente "Separation of Duties" | "Duty" puede no ser obvio en contexto de software |
| B | `role-conflict-rules/` | `ROLE_CONFLICT_VIOLATION` | Describe el problema técnico real | Introduce "role" cuando el sistema usa "function" |
| C | `function-conflict-rules/` | `FUNCTION_CONFLICT_VIOLATION` | Coherente con el vocabulario del dominio (Function, Assignment) | Más largo |
| D | `access-conflict-rules/` | `ACCESS_CONFLICT_VIOLATION` | Genérico, orientado al efecto | Demasiado genérico |

**Observación importante:** El modelo Django ya se llama `SeparationRule`
(definido en FASE 0, antes de STD_008). La tabla en BD se llama
`access_separation_rule`. La URL legacy del router ya es `separation-rules/`.

Esto hace que la **Opción A** sea la más consistente con lo que ya existe
en la capa de datos: no introduce un nuevo vocabulario, solo expone
consistentemente el nombre que el modelo ya tiene.

---

## 5. Propuesta de cambios — si se aprueba Opción A

Si se decide proceder con `separation-rules/` y `DUTY_SEPARATION_VIOLATION`,
el trabajo se organiza en dos commits coordinados entre IACT-api e IACT-docs.

### 5.1 Cambios en IACT-api

**Tipo A (solo código, sin coordinación):**

```python
# Renombrar archivo
sod_rule_view.py  →  separation_rule_view.py

# Renombrar clases (mismo archivo)
SoDRuleListCreateView    →  SeparationRuleListCreateView
SoDRuleDetailView        →  SeparationRuleDetailView
SoDRuleCreateSerializer  →  SeparationRuleCreateSerializer
SoDRulePatchSerializer   →  SeparationRulePatchSerializer
SoDRuleRetireSerializer  →  SeparationRuleRetireSerializer

# En function_assign_view.py
SoDValidator  →  DutySeparationValidator
```

**Tipo B (requieren coordinación con IACT-ui y IACT-docs):**

```python
# URLs en access/urls.py
'sod-rules/'              →  'separation-rules/'
'sod-rules/<int:rule_id>/'→  'separation-rules/<int:rule_id>/'
name='sod-rule-list-create'→ name='separation-rule-list-create'
name='sod-rule-detail'     →  name='separation-rule-detail'

# Error codes en responses (sod_rule_view.py y function_assign_view.py)
'SOD_VIOLATION'       →  'DUTY_SEPARATION_VIOLATION'
'SOD_RULE_DUPLICATE'  →  'SEPARATION_RULE_DUPLICATE'
'SOD_RULE_NOT_FOUND'  →  'SEPARATION_RULE_NOT_FOUND'

# Event types en audit/models.py VALID_EVENT_TYPES
'SOD_RULE_CREATED'   →  'SEPARATION_RULE_CREATED'
'SOD_RULE_UPDATED'   →  'SEPARATION_RULE_UPDATED'
'SOD_RULE_DISABLED'  →  'SEPARATION_RULE_DISABLED'
```

**Beneficio adicional:** Al renombrar la URL a `separation-rules/`, el
endpoint FASE 2 puede unificarse con la ruta legacy del router
(`SeparationRuleViewSet` en `separation-rules/`). El router legacy puede
eliminarse. Se resuelve la duplicación de rutas introducida en FASE 2.

### 5.2 Cambios en IACT-docs

Los 9 UCs afectados requieren actualización en sus archivos
`datos-involucrados.rst`, `criterios-aceptacion.rst`, `excepciones.rst`,
`flujo-principal.rst` e `implementacion-tecnica.rst` según corresponda.

Tabla de sustituciones en documentación:

| Identificador actual | Identificador correcto | UCs que lo usan |
|---|---|---|
| `/api/access/sod-rules/` | `/api/access/separation-rules/` | uc-acc-05 |
| `SOD_VIOLATION` | `DUTY_SEPARATION_VIOLATION` | uc-acc-01, uc-acc-04, uc-acc-08, uc-perm-06, uc-perm-09 |
| `CASCADE_SOD_VIOLATION` | `CASCADE_DUTY_SEPARATION_VIOLATION` | uc-perm-06 |
| `SOD_RULE_CREATED` | `SEPARATION_RULE_CREATED` | uc-acc-05, uc-acc-09 |
| `SOD_RULE_MODIFIED` | `SEPARATION_RULE_MODIFIED` | uc-acc-05, uc-acc-09 |
| `SOD_RULE_RETIRED` | `SEPARATION_RULE_RETIRED` | uc-acc-05, uc-acc-09 |
| `SOD_RULES_VIEWED` | `SEPARATION_RULES_VIEWED` | uc-acc-05, uc-acc-09 |
| `SOD_RULE_DUPLICATE` | `SEPARATION_RULE_DUPLICATE` | uc-acc-05 |
| `SOD_RULE_ALREADY_RETIRED` | `SEPARATION_RULE_ALREADY_RETIRED` | uc-acc-05 |
| `SoDRule` (clase/contrato) | `SeparationRule` | todos |
| `SoDRuleRepository` | `SeparationRuleRepository` | uc-acc-01, uc-acc-05, uc-perm-06 |
| `SoDRuleCache` | `SeparationRuleCache` | uc-acc-05 |
| `SoDRuleService` | `SeparationRuleService` | uc-acc-05 |
| `SoDRuleDuplicate` | `SeparationRuleDuplicate` | uc-acc-05 |
| `SoDRuleNotFound` | `SeparationRuleNotFound` | uc-acc-05 |
| `SoDRuleAlreadyRetired` | `SeparationRuleAlreadyRetired` | uc-acc-05 |
| `sod_rules_evaluated` | `separation_rules_evaluated` | uc-acc-01, uc-acc-08 |

---

## 6. Preguntas para Coatl

Antes de proceder, se necesita alineación en los siguientes puntos:

**P1 — Opción de nombre:**
¿Se aprueba la Opción A (`separation-rules/`, `DUTY_SEPARATION_VIOLATION`)?
¿O se prefiere otra de las opciones evaluadas en § 4.2?

**P2 — Estado de IACT-ui:**
¿`accessService.js` o algún componente de IACT-ui ya referencia las
constantes `SOD_VIOLATION` o el endpoint `sod-rules/`?
Si es así, el cambio de contrato requiere un PR coordinado.

**P3 — Alcance de la actualización documental:**
¿Se actualiza la documentación de los 9 UCs afectados en el mismo PR,
o se registra como deuda técnica y se hace en un PR separado de IACT-docs?

**P4 — Identificadores en el response body:**
En `uc-acc-01/datos-involucrados.rst § 7.3` el campo
`"sod_rules_evaluated": 5` aparece en el response JSON. Este campo
también está en el contrato del frontend. ¿Lo cambiamos a
`"separation_rules_evaluated": 5` o lo dejamos como está por
backward compatibility?

---

## 7. Lo que NO cambia

Para acotar el alcance: los siguientes identificadores **no** están
en el alcance de esta revisión aunque contengan conceptos relacionados:

- El modelo Django `SeparationRule` — ya tiene el nombre correcto.
- La tabla de BD `access_separation_rule` — ya tiene el nombre correcto.
- El nombre del ViewSet legacy `SeparationRuleViewSet` — ya tiene el
  nombre correcto.
- Los códigos de función RBAC `ACC-011 update_separation_rule`,
  `ACC-012 disable_separation_rule` — son IDs de artefactos, no
  identificadores técnicos (STD_008 § 2: "NO aplica a IDs de artefactos").
- El texto narrativo en documentación que dice "regla SoD" o "SoD violation"
  — el estándar prohíbe abreviaturas en **identificadores**, no en narrativa
  (§ 3.3: "Las abreviaturas pueden usarse en narrativa **solo cuando estén
  definidas previamente en el glosario del proyecto**").

---

## 8. Esfuerzo estimado

| Tarea | Archivos | Líneas | Responsable |
|---|---|---|---|
| Renombrar Tipo A en IACT-api | 3 archivos | ~40 líneas | Cualquiera |
| Renombrar Tipo B en IACT-api | 4 archivos | ~60 líneas | Requiere acuerdo P1 |
| Actualizar IACT-docs 9 UCs | ~25 archivos | ~237 líneas | Coatl o Nestor |
| Verificar IACT-ui | 2-4 archivos | desconocido | Nestor |
| **Total estimado** | **~34 archivos** | **~340 líneas** | |

Los cambios de Tipo A pueden hacerse inmediatamente como un commit limpio.
Los cambios de Tipo B deben esperar respuesta a P1-P4.

---

## 9. Referencia de normas

- STD_008 § 3.2 — Autoexplicativo
- STD_008 § 3.3 — Sin Abreviaturas de Dominio
- STD_008 § 3.5 — Coherencia de Idioma (incluye Endpoints REST)
- STD_008 § 6.1 — "entra en vigor para todo código nuevo desde su aprobación"
