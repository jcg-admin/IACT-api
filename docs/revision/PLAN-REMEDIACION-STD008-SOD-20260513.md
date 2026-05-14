# Plan de remediación — STD_008 § 3.3: abreviatura SoD en identificadores técnicos

**Artefacto:** PLAN-REMEDIACION-STD008-SOD-20260513
**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Depende de:** REVISION-STD008-NAMING-SOD-20260513 (aprobada por Coatl)
**Rama de trabajo:** `refactor/std008-sod-naming` (desde `develop`)
**Repositorios afectados:** IACT-api, IACT-docs

----

## 1. Decisiones de diseño adoptadas

Este plan asume que la revisión fue aprobada con las siguientes decisiones:

| Decisión | Valor acordado |
|---|---|
| Nombre canónico del concepto | `SeparationRule` (ya existe en el modelo Django desde FASE 0) |
| URL canónica | `/api/access/separation-rules/` |
| Error code de conflicto | `DUTY_SEPARATION_VIOLATION` |
| Error code de duplicado | `SEPARATION_RULE_DUPLICATE` |
| Error code de no encontrado | `SEPARATION_RULE_NOT_FOUND` |
| Event type de creación | `SEPARATION_RULE_CREATED` |
| Event type de actualización | `SEPARATION_RULE_UPDATED` |
| Event type de deshabilitación | `SEPARATION_RULE_DISABLED` |
| Clase de validación | `DutySeparationValidator` |

**Justificación:** El modelo Django ya se llama `SeparationRule` y la tabla
`access_separation_rule` desde FASE 0. No se introduce vocabulario nuevo.
La URL `separation-rules/` elimina además la duplicación con el router legacy.

----

## 2. Perimetro del plan

### 2.1 Qué cambia

Los identificadores técnicos en código y en documentos de requisitos que
contienen la abreviatura de dominio `SoD` en cualquier capitalización:
`sod`, `SoD`, `SOD`.

### 2.2 Qué NO cambia

Los siguientes elementos están **fuera del alcance** de este plan por
razones documentadas:

| Elemento | Razón de exclusión |
|---|---|
| Códigos `SOD-001`, `SOD-002`, `SOD-003` | Son IDs de artefacto, excluidos por STD_008 § 2 |
| Texto narrativo "regla SoD", "SoD violation" en documentación | STD_008 § 3.3 permite abreviaturas en narrativa cuando están en el glosario. `SoD` figura en `glosario.rst` línea 99. |
| URL legacy `validate-sod` y `accessService.validateSoD()` | Backward compatibility con IACT-ui. Decisión de deprecación separada. |
| Endpoint legacy del router `separation-rules/` (SeparationRuleViewSet) | Ya tiene nombre correcto. Se elimina al unificar con el canónico. |

----

## 3. Estructura de commits

El trabajo se organiza en **4 commits atómicos** ejecutables en orden.
Los primeros dos no requieren coordinación con IACT-ui. Los últimos dos sí.

```
COMMIT 1  refactor(access): STD_008 — renombrar identificadores internos
COMMIT 2  refactor(access): STD_008 — migración related_names SeparationRule
COMMIT 3  refactor(access,audit): STD_008 — contrato público URL + error codes + event types
COMMIT 4  docs(uc-acc,uc-perm): STD_008 — actualizar 9 UCs en IACT-docs
```

Los commits 1 y 2 pueden hacerse antes de que IACT-ui esté actualizado.
El commit 3 debe ir sincronizado con el PR de IACT-ui.

----

## 4. Commit 1 — Identificadores internos (sin coordinación)

**Rama:** `refactor/std008-sod-naming`
**Archivos:** 4 archivos Python, sin migración, sin cambio de URL ni de contrato.

### 4.1 Renombrar archivo

```bash
git mv apps/access/sod_rule_view.py apps/access/separation_rule_view.py
```

### 4.2 Dentro de `separation_rule_view.py` (ex `sod_rule_view.py`)

Sustituciones línea a línea:

| Antes | Después |
|---|---|
| `class SoDRuleCreateSerializer` | `class SeparationRuleCreateSerializer` |
| `class SoDRulePatchSerializer` | `class SeparationRulePatchSerializer` |
| `class SoDRuleRetireSerializer` | `class SeparationRuleRetireSerializer` |
| `class SoDRuleListCreateView(APIView)` | `class SeparationRuleListCreateView(APIView)` |
| `class SoDRuleDetailView(APIView)` | `class SeparationRuleDetailView(APIView)` |
| Todas las referencias internas (`SoDRuleCreateSerializer(...)`, etc.) | Idem con prefijo `SeparationRule` |

El docstring de la vista puede mantener "SoD" en narrativa:
`"""GET/POST /api/access/separation-rules/ — UC_ACC_05 Reglas SoD."""`

### 4.3 Dentro de `function_assign_view.py`

| Antes | Después |
|---|---|
| `class SoDValidator:` | `class DutySeparationValidator:` |
| `violations = SoDValidator.validate(...)` (×2 ocurrencias) | `violations = DutySeparationValidator.validate(...)` |
| Comentario `# CA-05/06: validar SoD` | Se mantiene (es narrativa, no identificador) |

### 4.4 Renombrar management command

```bash
git mv apps/access/management/commands/create_sod_rules.py \
       apps/access/management/commands/create_separation_rules.py
```

Dentro del archivo renombrado:

| Antes | Después |
|---|---|
| `SOD_RULES_V540 = [...]` | `SEPARATION_RULES_V540 = [...]` |
| `for code, name, ... in SOD_RULES_V540:` | `for code, name, ... in SEPARATION_RULES_V540:` |
| `help = 'Carga las 3 reglas SoD predefinidas...'` | `help = 'Carga las 3 reglas de separación predefinidas del catálogo RBAC v5.4.0'` |
| docstring `create_sod_rules` | `create_separation_rules` |

Nota: los valores `'SOD-001'`, `'SOD-002'`, `'SOD-003'` dentro de la lista
**no cambian** — son IDs de artefacto (excluidos por STD_008 § 2).

### 4.5 Actualizar `access/urls.py` — solo los imports

```python
# Antes
from .sod_rule_view import SoDRuleListCreateView, SoDRuleDetailView

# Después
from .separation_rule_view import SeparationRuleListCreateView, SeparationRuleDetailView
```

Las líneas `path('sod-rules/', ...)` en `urlpatterns` **no cambian** en este commit
(son Tipo B, van en el Commit 3).

### 4.6 Mensaje de commit

```
refactor(access): STD_008 § 3.3 — renombrar identificadores internos SoD

Renombres que no afectan el contrato público de la API (URL, error codes,
event types). Aplica STD_008 § 3.3: abreviaturas de dominio de negocio
no deben aparecer en identificadores técnicos.

Archivo:
  sod_rule_view.py → separation_rule_view.py

Clases:
  SoDRuleCreateSerializer  → SeparationRuleCreateSerializer
  SoDRulePatchSerializer   → SeparationRulePatchSerializer
  SoDRuleRetireSerializer  → SeparationRuleRetireSerializer
  SoDRuleListCreateView    → SeparationRuleListCreateView
  SoDRuleDetailView        → SeparationRuleDetailView
  SoDValidator             → DutySeparationValidator

Management command:
  create_sod_rules.py → create_separation_rules.py
  SOD_RULES_V540      → SEPARATION_RULES_V540

Fuera de alcance (IDs de artefacto — STD_008 § 2):
  SOD-001, SOD-002, SOD-003 no cambian
```

----

## 5. Commit 2 — Migración related_names (requiere migracion de BD)

**Rama:** `refactor/std008-sod-naming` (continúa)
**Archivo:** `apps/access/models.py` + nueva migración `0008_std008_related_names.py`

### 5.1 Contexto

Los `related_name` en Django son identificadores Python que generan
métodos de acceso en el ORM (p.ej. `function.sod_rules_as_set_a.all()`).
Están en el modelo `SeparationRule` y son identificadores técnicos directos.

Django requiere una migración `AlterField` para cambiar `related_name`
aunque el cambio no modifica la BD — Django lo registra igualmente.

### 5.2 Cambios en `access/models.py`

```python
# Antes
functions_set_a = models.ManyToManyField(
    Function,
    related_name='sod_rules_as_set_a',
    ...
)
functions_set_b = models.ManyToManyField(
    Function,
    related_name='sod_rules_as_set_b',
    ...
)

# Después
functions_set_a = models.ManyToManyField(
    Function,
    related_name='separation_rules_as_set_a',
    ...
)
functions_set_b = models.ManyToManyField(
    Function,
    related_name='separation_rules_as_set_b',
    ...
)
```

### 5.3 Nueva migración

Archivo: `apps/access/migrations/0008_std008_related_names.py`

```python
"""
Migration 0008 — STD_008: renombrar related_names SoD → SeparationRule.

AlterField en ManyToManyField no modifica tablas intermedias existentes.
Solo actualiza el nombre del accessor Python en el ORM.

Fuente: STD_008 § 3.3 — abreviatura SoD prohibida en identificadores técnicos.
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('access', '0007_fase2_access_group_and_function_menu'),
    ]

    operations = [
        migrations.AlterField(
            model_name='separationrule',
            name='functions_set_a',
            field=models.ManyToManyField(
                blank=True,
                help_text='Primer conjunto de funciones. Un usuario no puede '
                          'tener funciones de AMBOS conjuntos simultáneamente.',
                related_name='separation_rules_as_set_a',
                to='access.function',
                verbose_name='Conjunto A',
            ),
        ),
        migrations.AlterField(
            model_name='separationrule',
            name='functions_set_b',
            field=models.ManyToManyField(
                blank=True,
                help_text='Segundo conjunto de funciones.',
                related_name='separation_rules_as_set_b',
                to='access.function',
                verbose_name='Conjunto B',
            ),
        ),
    ]
```

### 5.4 Verificar que nadie usa los related_names viejos

Antes de hacer el commit, buscar en todo el codebase:

```bash
grep -rn "sod_rules_as_set" callcentersite/
# Resultado esperado: 0 ocurrencias fuera de models.py y migrations/
```

El resultado del inventario hecho antes de este plan confirma que los
`related_name` solo aparecen en `models.py` y en la migración `0005`.
No hay querysets en el código que los usen directamente.

### 5.5 Mensaje de commit

```
refactor(access): STD_008 § 3.3 — related_names SeparationRule sin SoD

Migración 0008: AlterField related_name en los dos ManyToManyField
de SeparationRule. No modifica tablas de BD — solo cambia el accessor
Python del ORM.

  sod_rules_as_set_a → separation_rules_as_set_a
  sod_rules_as_set_b → separation_rules_as_set_b

Verificado: ningún queryset en el código usa estos related_names
directamente (solo models.py y migration 0005 los referenciaban).
```

----

## 6. Commit 3 — Contrato público (sincronizado con IACT-ui)

**Rama:** `refactor/std008-sod-naming` (continúa)
**Prerequisito:** PR de IACT-ui aprobado y mergeado en su rama correspondiente.
**Archivos:** `access/urls.py`, `access/separation_rule_view.py`,
`access/function_assign_view.py`, `audit/models.py`

Este commit **es un breaking change** para cualquier cliente que consuma
la URL `sod-rules/` o los error codes `SOD_*` directamente.
El deploy debe coordinarse con el deploy de IACT-ui.

### 6.1 `access/urls.py` — URL paths y URL names

```python
# Antes
path('sod-rules/',
     SeparationRuleListCreateView.as_view(), name='sod-rule-list-create'),
path('sod-rules/<int:rule_id>/',
     SeparationRuleDetailView.as_view(), name='sod-rule-detail'),

# Después
path('separation-rules/',
     SeparationRuleListCreateView.as_view(), name='separation-rule-list-create'),
path('separation-rules/<int:rule_id>/',
     SeparationRuleDetailView.as_view(), name='separation-rule-detail'),
```

Con este cambio, la URL `separation-rules/` del router legacy (que registraba
`SeparationRuleViewSet`) queda **superpuesta** por la ruta explícita
(declarada antes del `include(router.urls)`). El `SeparationRuleViewSet`
legacy queda inaccesible. Se puede eliminar el registro del router en el
mismo commit o en un commit posterior de limpieza.

Actualizar también el comentario:

```python
# Antes (comentario incorrecto)
# B-03: usa prefijo 'sod-rules/' para evitar conflicto con router 'separation-rules/'

# Después
# UC_ACC_05 — Gestionar Reglas de Separación de Deberes (STD_008 § 3.3)
```

### 6.2 `separation_rule_view.py` — error codes y event types

| Antes | Después |
|---|---|
| `'error': 'SOD_RULE_DUPLICATE'` | `'error': 'SEPARATION_RULE_DUPLICATE'` |
| `'error': 'SOD_RULE_NOT_FOUND'` (×3) | `'error': 'SEPARATION_RULE_NOT_FOUND'` |
| `event_type='SOD_RULE_CREATED'` | `event_type='SEPARATION_RULE_CREATED'` |
| `event_type='SOD_RULE_UPDATED'` | `event_type='SEPARATION_RULE_UPDATED'` |
| `event_type='SOD_RULE_DISABLED'` | `event_type='SEPARATION_RULE_DISABLED'` |

### 6.3 `function_assign_view.py` — error code SOD_VIOLATION

| Antes | Después |
|---|---|
| `'error': 'SOD_VIOLATION'` (×2) | `'error': 'DUTY_SEPARATION_VIOLATION'` |
| `'reason': 'sod_violation'` | `'reason': 'duty_separation_violation'` |

### 6.4 `audit/models.py` — VALID_EVENT_TYPES

```python
# Antes (en el bloque Access — FASE 2)
'SOD_RULE_CREATED',
'SOD_RULE_UPDATED',
'SOD_RULE_DISABLED',

# Después
'SEPARATION_RULE_CREATED',
'SEPARATION_RULE_UPDATED',
'SEPARATION_RULE_DISABLED',
```

### 6.5 `@extend_schema` en las vistas — actualizar los description strings

Los strings de description en `@extend_schema` que citan los error codes
deben actualizarse para reflejar los nuevos valores, p.ej.:

```python
# Antes
'**CA-05**: SoD violation → 409 SOD_VIOLATION, rollback total.\n'

# Después
'**CA-05**: conflict violation → 409 DUTY_SEPARATION_VIOLATION, rollback total.\n'
```

Los strings que dicen "SoD" en narrativa (sin estar en código) se mantienen.

### 6.6 Cambios en IACT-ui (coordinado — fuera del scope de IACT-api)

El PR de IACT-ui debe actualizar:

| Archivo | Qué cambia |
|---|---|
| `accessService.js` | URL `sod-rules/` → `separation-rules/` |
| `accessSlice.js` | Cualquier comparación con `'SOD_VIOLATION'` → `'DUTY_SEPARATION_VIOLATION'` |
| Constantes de error en el frontend | Mismas sustituciones |

### 6.7 Mensaje de commit

```
refactor(access,audit): STD_008 § 3.3 — contrato público sin abreviatura SoD

BREAKING CHANGE: URL, error codes y event types cambian.
Requiere deploy coordinado con IACT-ui.

URL:
  /api/access/sod-rules/         → /api/access/separation-rules/
  /api/access/sod-rules/{id}/    → /api/access/separation-rules/{id}/

Error codes:
  SOD_VIOLATION          → DUTY_SEPARATION_VIOLATION
  SOD_RULE_DUPLICATE     → SEPARATION_RULE_DUPLICATE
  SOD_RULE_NOT_FOUND     → SEPARATION_RULE_NOT_FOUND

Event types (VALID_EVENT_TYPES + audit/models.py):
  SOD_RULE_CREATED   → SEPARATION_RULE_CREATED
  SOD_RULE_UPDATED   → SEPARATION_RULE_UPDATED
  SOD_RULE_DISABLED  → SEPARATION_RULE_DISABLED

El router legacy 'separation-rules/' queda superpuesto por la ruta
explícita. SeparationRuleViewSet puede eliminarse en limpieza posterior.

Fuente: STD_008 § 3.3, aprobado 2026-04-28
Revisión previa: REVISION-STD008-NAMING-SOD-20260513
```

----

## 7. Commit 4 — Documentación IACT-docs (9 UCs)

**Repositorio:** IACT-docs
**Rama:** `refactor/std008-sod-naming` (rama paralela en IACT-docs)
**Archivos afectados:** ~25 archivos RST en 9 UCs

Este commit actualiza los documentos de requisitos que preexistían antes
de la aprobación de STD_008 (2026-04-28) y que por eso usaban la
abreviatura `SoD` en identificadores técnicos.

### 7.1 Tabla maestra de sustituciones en documentación

Las sustituciones se aplican **solo en identificadores técnicos** (bloques
`.. code-block::`, literales `` ``código`` ``, contratos pseudocódigo).
El texto narrativo que dice "SoD" **no se modifica**.

| Identificador antes | Identificador después | UCs |
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
| `SoDRule` (en contratos técnicos) | `SeparationRule` | uc-acc-01, uc-acc-05, uc-perm-06 |
| `SoDRuleRepository` | `SeparationRuleRepository` | uc-acc-01, uc-acc-05 |
| `SoDRuleCache` | `SeparationRuleCache` | uc-acc-05 |
| `SoDRuleService` | `SeparationRuleService` | uc-acc-05 |
| `SoDRuleDuplicate` (excepción) | `SeparationRuleDuplicate` | uc-acc-05 |
| `SoDRuleNotFound` (excepción) | `SeparationRuleNotFound` | uc-acc-05 |
| `SoDRuleAlreadyRetired` (excepción) | `SeparationRuleAlreadyRetired` | uc-acc-05 |
| `sod_rules_evaluated` (campo de response) | `separation_rules_evaluated` | uc-acc-01, uc-acc-08 |

### 7.2 UCs y archivos a modificar

**uc-acc-05** (127 ocurrencias — mayor volumen):
- `datos-involucrados.rst` — URL, modelo SoDRule, event types, SoDRuleCache
- `criterios-aceptacion.rst` — SOD_RULE_DUPLICATE, SOD_RULE_ALREADY_RETIRED
- `implementacion-tecnica.rst` — SoDRuleService, SoDRuleRepository, SoDRuleCache
- `flujo-principal.rst` — referencias a SoDRule
- `testing.rst` — AuditEvent SOD_RULE_*, SoDRuleCache
- `patrones-diseno.rst` — SoDRuleCache
- `requisitos-no-funcionales.rst` — event types SOD_RULE_*

**uc-acc-01** (52 ocurrencias):
- `datos-involucrados.rst` — SOD_VIOLATION, sod_rules_evaluated
- `criterios-aceptacion.rst` — SOD_VIOLATION
- `excepciones.rst` — SOD_VIOLATION
- `flujo-principal.rst` — SoDRuleRepo, sod_rules
- `implementacion-tecnica.rst` — SoDRule, SoDRuleRepository, sod_rules_evaluated
- `diagramas-uml.rst` — SOD_VIOLATION
- `actores-precondiciones.rst` — SoDRules

**uc-acc-04** (16 ocurrencias):
- Archivos con referencia a SOD_VIOLATION en excepciones y criterios

**uc-acc-08** (12 ocurrencias):
- `criterios-aceptacion.rst` — SOD_VIOLATION
- `excepciones.rst` — SOD_VIOLATION
- `diagramas-uml.rst` — SOD_VIOLATION

**uc-acc-03** (11 ocurrencias):
- Referencias a SoDRule en precondiciones y datos involucrados

**uc-perm-06** (10 ocurrencias):
- `criterios-aceptacion.rst` — CASCADE_SOD_VIOLATION
- `excepciones.rst` — CASCADE_SOD_VIOLATION
- `implementacion-tecnica.rst` — SoDRuleRepository

**uc-acc-09** (7 ocurrencias):
- `datos-involucrados.rst` — SOD_RULE_* en lista de event types

**uc-perm-03** (1 ocurrencia):
- `patrones-diseno.rst` — referencia a SoDRule

**uc-perm-09** (1 ocurrencia):
- `informacion-general.rst` — SOD_VIOLATION en tabla de eventos monitoreados

### 7.3 Estrategia de ejecución para 25 archivos

Dado el volumen, el script de sustitución usa `sed` con múltiples patrones
en un solo pase por archivo:

```bash
#!/bin/bash
# Ejecutar desde la raíz de IACT-docs
# Aplica todas las sustituciones de identificadores en bloque
# Solo dentro de bloques de código RST (no en narrativa libre)

AFFECTED_UCS=(
  "source/requisitos/casos-uso/access/uc-acc-05"
  "source/requisitos/casos-uso/access/uc-acc-01"
  "source/requisitos/casos-uso/access/uc-acc-04"
  "source/requisitos/casos-uso/access/uc-acc-08"
  "source/requisitos/casos-uso/access/uc-acc-03"
  "source/requisitos/casos-uso/access/uc-acc-09"
  "source/requisitos/casos-uso/permissions/uc-perm-06"
  "source/requisitos/casos-uso/permissions/uc-perm-03"
  "source/requisitos/casos-uso/permissions/uc-perm-09"
)

for DIR in "${AFFECTED_UCS[@]}"; do
  find "$DIR" -name "*.rst" | while read -r FILE; do
    sed -i \
      -e 's|/api/access/sod-rules/|/api/access/separation-rules/|g' \
      -e 's|SOD_VIOLATION|DUTY_SEPARATION_VIOLATION|g' \
      -e 's|CASCADE_SOD_VIOLATION|CASCADE_DUTY_SEPARATION_VIOLATION|g' \
      -e 's|SOD_RULE_CREATED|SEPARATION_RULE_CREATED|g' \
      -e 's|SOD_RULE_MODIFIED|SEPARATION_RULE_MODIFIED|g' \
      -e 's|SOD_RULE_RETIRED|SEPARATION_RULE_RETIRED|g' \
      -e 's|SOD_RULES_VIEWED|SEPARATION_RULES_VIEWED|g' \
      -e 's|SOD_RULE_DUPLICATE|SEPARATION_RULE_DUPLICATE|g' \
      -e 's|SOD_RULE_ALREADY_RETIRED|SEPARATION_RULE_ALREADY_RETIRED|g' \
      -e 's|SoDRuleRepository|SeparationRuleRepository|g' \
      -e 's|SoDRuleService|SeparationRuleService|g' \
      -e 's|SoDRuleCache|SeparationRuleCache|g' \
      -e 's|SoDRuleDuplicate|SeparationRuleDuplicate|g' \
      -e 's|SoDRuleNotFound|SeparationRuleNotFound|g' \
      -e 's|SoDRuleAlreadyRetired|SeparationRuleAlreadyRetired|g' \
      -e 's|\bSoDRule\b|SeparationRule|g' \
      -e 's|sod_rules_evaluated|separation_rules_evaluated|g' \
      "$FILE"
  done
done
```

**Revisión manual posterior obligatoria:** El script toca todos los contextos.
Antes del commit, revisar con `git diff` que:

1. Las sustituciones en texto narrativo (fuera de code-blocks) no alteran
   el significado de la frase.
2. Los IDs `SOD-001`, `SOD-002`, `SOD-003` no fueron tocados (el patrón
   `SOD_RULE_*` no coincide con `SOD-00*`).

### 7.4 Mensaje de commit en IACT-docs

```
docs(uc-acc,uc-perm): STD_008 § 3.3 — actualizar 9 UCs sin abreviatura SoD

Actualiza los documentos de requisitos escritos antes de la aprobación de
STD_008 (2026-04-28) que usaban la abreviatura SoD en identificadores
técnicos. El texto narrativo que dice "SoD" se preserva.

UCs actualizados:
  uc-acc-01 (52 líneas) — SOD_VIOLATION → DUTY_SEPARATION_VIOLATION
  uc-acc-03 (11 líneas) — SoDRule → SeparationRule
  uc-acc-04 (16 líneas) — SOD_VIOLATION → DUTY_SEPARATION_VIOLATION
  uc-acc-05 (127 líneas) — URL, SOD_RULE_*, SoDRuleRepository/Cache/Service
  uc-acc-08 (12 líneas) — SOD_VIOLATION, CASCADE_SOD_VIOLATION
  uc-acc-09 (7 líneas)  — SOD_RULE_* en event types
  uc-perm-03 (1 línea)  — SoDRule → SeparationRule
  uc-perm-06 (10 líneas)— CASCADE_SOD_VIOLATION, SoDRuleRepository
  uc-perm-09 (1 línea)  — SOD_VIOLATION en eventos monitoreados

Fuera de alcance (excluidos por STD_008 § 2): SOD-001, SOD-002, SOD-003
Fuera de alcance (texto narrativo): frases "regla SoD", "violación SoD"
```

----

## 8. Verificación post-remediación

Ejecutar después del Commit 3 para confirmar cero violaciones residuales:

```bash
# Desde la raíz de IACT-api
echo "=== Violaciones residuales en código ==="
grep -rn "sod\|SoD\|SOD" callcentersite/apps/ \
  --include="*.py" \
  | grep -v "__pycache__" \
  | grep -v "separation_rule\|SeparationRule\|separationrule" \
  | grep -v "SOD-00[0-9]" \   # IDs de artefacto — permitidos
  | grep -v "# .*SoD\|\".*SoD\|'.*SoD" \   # narrativa en strings — permitida
  | wc -l
# Resultado esperado: 0
```

```bash
# Desde la raíz de IACT-docs (post Commit 4)
echo "=== Violaciones residuales en documentación ==="
grep -rn "SOD_\|SoDRule\|sod-rules" \
  source/requisitos/casos-uso/ \
  | grep -v "SOD-00[0-9]" \
  | wc -l
# Resultado esperado: 0
```

----

## 9. Cronograma y dependencias

```
DÍA 1
  ├── Commit 1: identificadores internos         [Nestor o Coatl, ~30 min]
  └── Commit 2: migración related_names          [Nestor o Coatl, ~15 min]

DÍA 1-N (paralelo — mientras IACT-ui se actualiza)
  └── Commit 4: documentación IACT-docs          [Coatl, ~2 h con script]

DÍA N (coordinado)
  ├── Merge PR IACT-ui en develop-ui
  └── Commit 3: contrato público IACT-api        [Nestor, ~20 min]
       └── Deploy coordinado IACT-api + IACT-ui
```

Los commits 1, 2 y 4 son seguros en cualquier momento.
El commit 3 es el único con riesgo de ruptura — requiere deploy coordinado.

----

## 10. Resumen de cambios por repositorio

| Repositorio | Commits | Archivos | Líneas | Coordinación |
|---|---|---|---|---|
| IACT-api | 3 (Commits 1-3) | ~8 archivos | ~115 líneas | Commit 3 coordinado |
| IACT-docs | 1 (Commit 4) | ~25 archivos | ~237 líneas | Independiente |
| IACT-ui | 1 (externo) | 2-4 archivos | desconocido | Prerequisito de Commit 3 |

Esfuerzo total estimado: **medio día de trabajo coordinado** entre Nestor y Coatl.
