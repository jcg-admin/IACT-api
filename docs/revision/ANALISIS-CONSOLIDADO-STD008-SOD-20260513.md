# Análisis consolidado — Remediación STD_008 § 3.3: abreviatura SoD

**Artefacto:** ANALISIS-CONSOLIDADO-STD008-SOD-20260513
**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Autor:** Claude — para revisión Nestor Monroy + Coatl (2-Coatl)
**Estado:** Listo para ejecutar
**Reemplaza:** REVISION, ANALISIS-DOCS, ANALISIS-IACT-UI (documentos previos)

----

## 1. Qué se analizó

| Fuente | Resultado |
|---|---|
| `STD_008 § 3.3` | Norma violada: prohíbe `SoD` en identificadores técnicos |
| `CNST-030, CNST-033, STD-007` | Vocabulario canónico del proyecto para el concepto |
| `modelo-rbac-iact.rst` | Nombre de clase de referencia en arquitectura |
| `uc-acc-01, uc-acc-05` y 7 UCs más | Contratos de API escritos antes de STD_008 |
| `IACT-api develop` | Estado exacto del código backend FASE 2 |
| `IACT-ui claude/project-analysis-N9IkV` | Estado real del frontend |

----

## 2. El problema en una sola oración

En FASE 2 usamos `sod-rules/` como URL y `SOD_*` como error codes.
El frontend ya espera `separation-rules/` y `SEPARATION_*`. La integración
está rota ahora mismo.

----

## 3. Inventario de violaciones — qué existe hoy en cada repositorio

### 3.1 IACT-api (`develop`)

**102 líneas con la abreviatura `SoD/SOD/sod` en dos apps:**

| Categoría | Identificador actual | Archivo |
|---|---|---|
| Nombre de archivo | `sod_rule_view.py` | `apps/access/` |
| Clases de vista | `SoDRuleListCreateView` `SoDRuleDetailView` | `sod_rule_view.py` |
| Serializers | `SoDRuleCreateSerializer` `SoDRulePatchSerializer` `SoDRuleRetireSerializer` | `sod_rule_view.py` |
| Clase de servicio | `SoDValidator` | `function_assign_view.py` |
| Management command | `create_sod_rules.py` | `apps/access/management/commands/` |
| Constante global | `SOD_RULES_V540` | `create_sod_rules.py` |
| Related names | `sod_rules_as_set_a` `sod_rules_as_set_b` | `apps/access/models.py` |
| URL path (FASE 2) | `sod-rules/` `sod-rules/<int:rule_id>/` | `apps/access/urls.py` |
| URL names | `sod-rule-list-create` `sod-rule-detail` | `apps/access/urls.py` |
| Error codes | `SOD_RULE_DUPLICATE` `SOD_RULE_NOT_FOUND` `SOD_VIOLATION` | `sod_rule_view.py` `function_assign_view.py` |
| Event types | `SOD_RULE_CREATED` `SOD_RULE_UPDATED` `SOD_RULE_DISABLED` | `audit/models.py` |
| Campo de response | `sod_rules_evaluated` | `function_assign_view.py` |

**Fuera del alcance — no cambian (justificación en § 8):**

| Elemento | Razón |
|---|---|
| `SOD-001` `SOD-002` `SOD-003` | IDs de artefacto — STD_008 § 2 los excluye explícitamente |
| URL `validate-sod` (legacy) | Reemplazada por nueva URL — se depreca, no se renombra |
| `'access:view_sod'` en JWT | Codename heredado en tokens — requiere ADR separado |
| `class SeparationRule` | Ya tiene el nombre correcto; la inconsistencia con CNST-033 es deuda independiente |

### 3.2 IACT-docs — 9 UCs con 237 líneas afectadas

Los UCs se escribieron antes de STD_008 (aprobado 2026-04-28).

| UC | Líneas | Qué usa |
|---|---|---|
| `uc-acc-05` | 127 | URL `sod-rules/`, `SOD_RULE_*`, `SoDRule`, `SoDRuleRepository/Cache/Service` |
| `uc-acc-01` | 52 | `SOD_VIOLATION`, `sod_rules_evaluated`, `SoDRule` |
| `uc-acc-04` | 16 | `SOD_VIOLATION` |
| `uc-acc-08` | 12 | `SOD_VIOLATION`, `CASCADE_SOD_VIOLATION` |
| `uc-acc-03` | 11 | referencias a `SoDRule` |
| `uc-perm-06` | 10 | `CASCADE_SOD_VIOLATION`, `SoDRuleRepository` |
| `uc-acc-09` | 7 | `SOD_RULE_*` en event types |
| `uc-perm-03` | 1 | `SoDRule` |
| `uc-perm-09` | 1 | `SOD_VIOLATION` |

### 3.3 IACT-ui — sin violaciones en código de producción

El frontend ya usa los identificadores correctos:

| Identificador | Valor en IACT-ui |
|---|---|
| URL para CRUD de reglas | `/access/separation-rules` |
| URL para CRUD admin | `/api/admin/separation-rules/` |
| URL para validación | `/access/separation-rules/validate` |
| Redux state field | `separationRules`, `separationConflicts` |
| Componentes | `SeparationRulesValidator.jsx` |
| Thunks | `fetchSeparationRules`, `validateSeparationRules` |

**IACT-ui no requiere ningún cambio de naming.** Las únicas referencias a
`sod` en el frontend están en codenames de permisos legacy (`'access:view_sod'`)
que son strings heredados emitidos por el backend JWT — fuera de alcance.

----

## 4. El nombre canónico correcto — decisión informada por tres fuentes

Las tres fuentes normativas del proyecto convergen en `separation`:

**STD-007 § naming de reglas:**

> Nombres de reglas SoD — Inglés con sufijo `_separation`
> Ejemplo: `pipeline_audit_separation`

**modelo-rbac-iact.rst — clase de referencia:**

```python
class FunctionSeparationRule(models.Model):
    db_table = 'function_separation_rules'
```

**Router legacy de IACT-api — ya registrado así:**

```python
router.register(r'separation-rules', SeparationRuleViewSet, ...)
```

**Conclusión:** `separation-rules/` es el nombre correcto tanto por
normativa como por coherencia con lo que el propio backend ya exponía
(vía router legacy) y con lo que IACT-ui ya consume.

### 4.1 Error codes — por qué `SEPARATION_RULE_VIOLATION` y no `DUTY_SEPARATION_VIOLATION`

`DUTY` es parte de la expansión de `SoD` (Separation of **Duties**).
Incluirlo introduce la mitad del acrónimo que queremos eliminar.
Ningún documento normativo del proyecto usa el término `duty` en
identificadores técnicos. El vocabulario canónico usa exclusivamente
`separation`. El código correcto es `SEPARATION_RULE_VIOLATION`.

----

## 5. Bug de integración descubierto

Al analizar IACT-ui se encontró que el problema va más allá del naming.
Existe un bug de integración activo:

| Capa | URL expuesta / esperada |
|---|---|
| IACT-api FASE 2 expone | `POST /api/access/sod-rules/` |
| IACT-ui llama | `POST /api/access/separation-rules` |
| IACT-api FASE 2 expone | `GET /api/access/sod-rules/` |
| IACT-ui llama | `GET /api/access/separation-rules` |

**El frontend nunca podrá conectar con los endpoints de FASE 2 hasta que
se corrija la URL.** Esto eleva la prioridad del Commit 3 de mejora de
calidad a corrección de bug.

### 5.1 Segundo bug — endpoint de validación no implementado

| Componente | URL |
|---|---|
| IACT-ui llama | `POST /api/access/separation-rules/validate` |
| IACT-api expone (legacy) | `POST /api/access/validate-sod` |
| IACT-api FASE 2 | No implementado |

El endpoint de validación que el frontend llama (`separation-rules/validate`)
no existe en el backend. El legacy `validate-sod` tiene la lógica correcta
pero en la URL incorrecta — y además tiene un bug adicional: filtra por
`status='active'` sobre el campo `status` que no existe en el modelo
`SeparationRule` actual (el modelo usa `state='ENABLED'`).

**Contrato que el frontend espera:**

```
POST /api/access/separation-rules/validate
Body: { userId: int, functionId: int }
Response 200: { conflicts: [ { rule, ruleDesc, setA, setB, message } ] }
Response 400: si faltan parámetros
```

----

## 6. Plan de remediación — 4 commits ordenados

### Commit 1 — Identificadores internos (sin coordinación)

**Rama:** `refactor/std008-sod-naming`
**Riesgo:** Nulo — solo renombres internos, sin cambio de contrato.
**Tiempo estimado:** 30 minutos

Cambios:

```bash
# Renombrar archivo
git mv apps/access/sod_rule_view.py apps/access/separation_rule_view.py

# Renombrar management command
git mv apps/access/management/commands/create_sod_rules.py \
       apps/access/management/commands/create_separation_rules.py
```

Dentro de los archivos renombrados:

| Antes | Después |
|---|---|
| `class SoDRuleCreateSerializer` | `class SeparationRuleCreateSerializer` |
| `class SoDRulePatchSerializer` | `class SeparationRulePatchSerializer` |
| `class SoDRuleRetireSerializer` | `class SeparationRuleRetireSerializer` |
| `class SoDRuleListCreateView` | `class SeparationRuleListCreateView` |
| `class SoDRuleDetailView` | `class SeparationRuleDetailView` |
| `class SoDValidator` (en `function_assign_view.py`) | `class DutySeparationValidator` |
| `SOD_RULES_V540` (en `create_separation_rules.py`) | `SEPARATION_RULES_V540` |

En `access/urls.py` — solo el import:
```python
# Antes
from .sod_rule_view import SoDRuleListCreateView, SoDRuleDetailView
# Después
from .separation_rule_view import SeparationRuleListCreateView, SeparationRuleDetailView
```
Las líneas `path('sod-rules/', ...)` aún no cambian — van en el Commit 3.

**Nota:** Los valores `'SOD-001'`, `'SOD-002'`, `'SOD-003'` dentro de
`SEPARATION_RULES_V540` **no cambian** — son IDs de artefacto excluidos
por STD_008 § 2.

**Mensaje de commit:**

```
refactor(access): STD_008 § 3.3 — renombrar identificadores internos SoD

sod_rule_view.py → separation_rule_view.py
create_sod_rules.py → create_separation_rules.py
SoDRule* → SeparationRule* (clases y serializers)
SoDValidator → DutySeparationValidator
SOD_RULES_V540 → SEPARATION_RULES_V540

Sin cambio de contrato público (URL, error codes, event types).
IDs de artefacto SOD-001/002/003 preservados (STD_008 § 2).
```

---

### Commit 2 — Migración related_names (requiere migración Django)

**Riesgo:** Bajo — `AlterField` en M2M no toca tablas intermedias.
**Tiempo estimado:** 15 minutos

En `apps/access/models.py`:

```python
# Antes
functions_set_a = models.ManyToManyField(
    Function, related_name='sod_rules_as_set_a', ...)
functions_set_b = models.ManyToManyField(
    Function, related_name='sod_rules_as_set_b', ...)

# Después
functions_set_a = models.ManyToManyField(
    Function, related_name='separation_rules_as_set_a', ...)
functions_set_b = models.ManyToManyField(
    Function, related_name='separation_rules_as_set_b', ...)
```

Nueva migración `apps/access/migrations/0008_std008_related_names.py`:

```python
"""Migration 0008 — STD_008 § 3.3: related_names sin abreviatura SoD."""
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('access', '0007_fase2_access_group_and_function_menu')]
    operations = [
        migrations.AlterField(
            model_name='separationrule', name='functions_set_a',
            field=models.ManyToManyField(
                blank=True, to='access.function',
                related_name='separation_rules_as_set_a',
                verbose_name='Conjunto A'),
        ),
        migrations.AlterField(
            model_name='separationrule', name='functions_set_b',
            field=models.ManyToManyField(
                blank=True, to='access.function',
                related_name='separation_rules_as_set_b',
                verbose_name='Conjunto B'),
        ),
    ]
```

Verificación previa obligatoria:

```bash
grep -rn "sod_rules_as_set" callcentersite/
# Resultado esperado: solo models.py y migration 0005 — ningún queryset los usa
```

**Mensaje de commit:**

```
refactor(access): STD_008 § 3.3 — migración related_names SeparationRule

AlterField en ManyToManyField. No modifica tablas de BD.
  sod_rules_as_set_a → separation_rules_as_set_a
  sod_rules_as_set_b → separation_rules_as_set_b
```

---

### Commit 3 — Contrato público + bug de integración + endpoint faltante

**Prioridad:** Alta — es corrección de bug activo, no solo STD_008.
**Riesgo:** Nulo respecto a IACT-ui (el frontend ya espera `separation-rules/`).
**Coordinación requerida:** Ninguna — el frontend ya está alineado.
**Tiempo estimado:** 45 minutos

#### 3.a URL paths en `access/urls.py`

```python
# Antes
# B-03: usa prefijo 'sod-rules/' para evitar conflicto con router 'separation-rules/'
path('sod-rules/',
     SeparationRuleListCreateView.as_view(), name='sod-rule-list-create'),
path('sod-rules/<int:rule_id>/',
     SeparationRuleDetailView.as_view(), name='sod-rule-detail'),

# Después
# UC_ACC_05 — Reglas de Separación (STD_008 § 3.3 — antes: sod-rules/)
path('separation-rules/',
     SeparationRuleListCreateView.as_view(), name='separation-rule-list-create'),
path('separation-rules/<int:rule_id>/',
     SeparationRuleDetailView.as_view(), name='separation-rule-detail'),
```

Con este cambio, el router legacy (`SeparationRuleViewSet` registrado en
`separation-rules/`) queda superpuesto por la ruta explícita. El
`SeparationRuleViewSet` puede eliminarse del router en un commit de
limpieza posterior.

#### 3.b Implementar el endpoint de validación faltante

Agregar a `access/urls.py`:

```python
path('separation-rules/validate',
     SeparationRuleValidateView.as_view(), name='separation-rule-validate'),
```

Corregir `SeparationRuleValidateView` en `views.py`: el filtro actual usa
`status='active'` que no existe en el modelo — el campo correcto es
`state='ENABLED'`:

```python
# Antes (bug)
rules = SeparationRule.objects.filter(status='active').filter(...)

# Después
rules = SeparationRule.objects.filter(state='ENABLED').filter(...)
```

Actualizar también el docstring para reflejar la nueva URL:

```python
class SeparationRuleValidateView(APIView):
    """
    UC_ACC_01 — Validar conflictos de separación antes de asignar función.
    POST /api/access/separation-rules/validate
    Body: { userId: int, functionId: int }
    Response: { conflicts: [{ rule, ruleDesc, setA, setB, message }] }
    CNST-010: permission_classes explícito — ACC-005.
    """
```

#### 3.c Error codes en `separation_rule_view.py`

| Antes | Después |
|---|---|
| `'SOD_RULE_DUPLICATE'` | `'SEPARATION_RULE_DUPLICATE'` |
| `'SOD_RULE_NOT_FOUND'` (×3) | `'SEPARATION_RULE_NOT_FOUND'` |

#### 3.d Event types en `separation_rule_view.py`

| Antes | Después |
|---|---|
| `event_type='SOD_RULE_CREATED'` | `event_type='SEPARATION_RULE_CREATED'` |
| `event_type='SOD_RULE_UPDATED'` | `event_type='SEPARATION_RULE_UPDATED'` |
| `event_type='SOD_RULE_DISABLED'` | `event_type='SEPARATION_RULE_DISABLED'` |

#### 3.e Error code de violación en `function_assign_view.py`

| Antes | Después |
|---|---|
| `'error': 'SOD_VIOLATION'` (×2) | `'error': 'SEPARATION_RULE_VIOLATION'` |
| `'reason': 'sod_violation'` | `'reason': 'separation_rule_violation'` |

#### 3.f Campo de response en `function_assign_view.py`

| Antes | Después |
|---|---|
| `sod_rules_evaluated` | `separation_rules_evaluated` |

#### 3.g VALID_EVENT_TYPES en `audit/models.py`

```python
# Antes
'SOD_RULE_CREATED',
'SOD_RULE_UPDATED',
'SOD_RULE_DISABLED',

# Después
'SEPARATION_RULE_CREATED',
'SEPARATION_RULE_UPDATED',
'SEPARATION_RULE_DISABLED',
```

**Mensaje de commit:**

```
fix(access,audit): STD_008 § 3.3 + bug integración — separation-rules/

Corrección de bug de integración (IACT-ui esperaba separation-rules/):
  sod-rules/          → separation-rules/
  sod-rules/{id}/     → separation-rules/{id}/
  name sod-rule-*     → separation-rule-*

Endpoint faltante implementado:
  POST /api/access/separation-rules/validate
  Corrige también filtro legacy status='active' → state='ENABLED'

Error codes:
  SOD_RULE_DUPLICATE  → SEPARATION_RULE_DUPLICATE
  SOD_RULE_NOT_FOUND  → SEPARATION_RULE_NOT_FOUND
  SOD_VIOLATION       → SEPARATION_RULE_VIOLATION

Event types (VALID_EVENT_TYPES + views):
  SOD_RULE_CREATED    → SEPARATION_RULE_CREATED
  SOD_RULE_UPDATED    → SEPARATION_RULE_UPDATED
  SOD_RULE_DISABLED   → SEPARATION_RULE_DISABLED

Campo response:
  sod_rules_evaluated → separation_rules_evaluated

IACT-ui no requiere cambios: ya usa separation-rules/ y
separationConflicts en producción.
```

---

### Commit 4 — IACT-docs (9 UCs, 237 líneas)

**Repositorio:** IACT-docs
**Rama:** `refactor/std008-sod-naming` (rama paralela)
**Tiempo estimado:** 2 horas (con script + revisión manual)

#### Script de sustitución

```bash
#!/bin/bash
# Ejecutar desde la raíz de IACT-docs
UUCS=(
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

for DIR in "${UUCS[@]}"; do
  find "$DIR" -name "*.rst" | while read -r FILE; do
    sed -i \
      -e 's|/api/access/sod-rules/|/api/access/separation-rules/|g' \
      -e 's|SOD_VIOLATION|SEPARATION_RULE_VIOLATION|g' \
      -e 's|CASCADE_SOD_VIOLATION|CASCADE_SEPARATION_RULE_VIOLATION|g' \
      -e 's|SOD_RULE_CREATED|SEPARATION_RULE_CREATED|g' \
      -e 's|SOD_RULE_MODIFIED|SEPARATION_RULE_MODIFIED|g' \
      -e 's|SOD_RULE_RETIRED|SEPARATION_RULE_RETIRED|g' \
      -e 's|SOD_RULES_VIEWED|SEPARATION_RULES_VIEWED|g' \
      -e 's|SOD_RULE_DUPLICATE|SEPARATION_RULE_DUPLICATE|g' \
      -e 's|SOD_RULE_ALREADY_RETIRED|SEPARATION_RULE_ALREADY_RETIRED|g' \
      -e 's|SOD_RULE_NOT_FOUND|SEPARATION_RULE_NOT_FOUND|g' \
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

**Revisión manual obligatoria después del script:**

```bash
# Verificar que SOD-001/002/003 no fueron tocados
grep -rn "SOD-00[0-9]" source/requisitos/casos-uso/ | wc -l
# Debe ser el mismo número que antes

# Verificar que no quedaron ocurrencias residuales
grep -rn "SOD_\|SoDRule\|sod-rules" source/requisitos/casos-uso/ \
  | grep -v "SOD-00[0-9]" | wc -l
# Resultado esperado: 0
```

**Mensaje de commit:**

```
docs(uc-acc,uc-perm): STD_008 § 3.3 — 9 UCs sin abreviatura SoD

Actualiza artefactos escritos antes de STD_008 (2026-04-28).
Texto narrativo con "SoD" preservado (STD_008 § 3.3 permite
abreviaturas en narrativa cuando están en el glosario).

UCs actualizados (237 líneas):
  uc-acc-05 (127): URL, SOD_RULE_*, SoDRule*, sod_rules_evaluated
  uc-acc-01 (52):  SOD_VIOLATION, sod_rules_evaluated, SoDRule
  uc-acc-04 (16):  SOD_VIOLATION
  uc-acc-08 (12):  SOD_VIOLATION, CASCADE_SOD_VIOLATION
  uc-acc-03 (11):  SoDRule
  uc-acc-09 (7):   SOD_RULE_* en event types
  uc-perm-06 (10): CASCADE_SOD_VIOLATION, SoDRuleRepository
  uc-perm-03 (1):  SoDRule
  uc-perm-09 (1):  SOD_VIOLATION

IDs de artefacto SOD-001/002/003: sin cambios (STD_008 § 2)
```

----

## 7. Cronograma (un solo día, sin dependencias externas)

```
DÍA 1 — todos los commits son independientes

IACT-api:
  09:00  Commit 1 — renombres internos         [30 min]
  09:30  Commit 2 — migración related_names    [15 min]
  09:45  Commit 3 — contrato + bug + validate  [45 min]
  10:30  Verificación automática (§ 7.1)       [10 min]

IACT-docs (paralelo o a continuación):
  11:00  Commit 4 — script + revisión manual   [2 h]

IACT-ui:
  Sin cambios requeridos
```

### 7.1 Verificación automática post-remediación

```bash
# En IACT-api — resultado esperado: 0
grep -rn "sod\|SoD\|SOD" callcentersite/apps/ \
  | grep -v "__pycache__\|\.pyc" \
  | grep -v "separation_rule\|SeparationRule\|separationrule" \
  | grep -v "SOD-00[0-9]" \
  | grep -v "# .*SoD\|\".*SoD\|'.*SoD" \
  | wc -l

# En IACT-docs — resultado esperado: 0
grep -rn "SOD_\|SoDRule\|sod-rules" \
  source/requisitos/casos-uso/ \
  | grep -v "SOD-00[0-9]" \
  | wc -l
```

----

## 8. Qué NO cambia y por qué

| Elemento | Razón |
|---|---|
| `SOD-001`, `SOD-002`, `SOD-003` | STD_008 § 2: "NO aplica a IDs de artefactos de documentación" |
| Texto narrativo "regla SoD", "violación SoD" | STD_008 § 3.3: permitido en narrativa cuando el término está en el glosario. `SoD` figura en `glosario.rst` línea 99 |
| URL `validate-sod` (legacy) | Sin consumidor activo en IACT-ui — se depreca sin renombrar |
| `'access:view_sod'` en `catalog.js` | Codename en tokens JWT — cambio requiere ADR y migración de tokens |
| `class SeparationRule` (modelo Django) | Ya tiene nombre correcto; la inconsistencia con CNST-033 (`SeparationOfDutiesRule`) es deuda independiente |
| `class SeparationRuleValidateView` | Ya tiene nombre correcto; solo cambia su URL y se corrige su filtro |

----

## 9. Deuda técnica identificada — fuera del presente plan

Dos elementos que exceden el alcance de este plan pero quedan registrados
para no perderse:

**DT-001: Inconsistencia de nombre de clase entre artefactos canónicos**

Tres artefactos definen el nombre de la clase del modelo con valores distintos:

| Fuente | Nombre |
|---|---|
| `CNST-033` | `SeparationOfDutiesRule` |
| `modelo-rbac-iact.rst` | `FunctionSeparationRule` |
| Django actual | `SeparationRule` |

Requiere ADR para unificar. El cambio implicaría `RenameModel` en Django.

**DT-002: Codenames legacy con `sod` en tokens JWT**

`catalog.js` de IACT-ui usa `'access:view_sod'`, `'adm:create_sod'` etc.
Estos son los `permission_django` del modelo `Function`. Cambiarlos afecta
los JWT emitidos — requiere rotación de tokens y ADR.

----

## 10. Resumen final

| Dimensión | Estado antes | Estado después |
|---|---|---|
| URL CRUD de reglas | `sod-rules/` | `separation-rules/` — alineado con UI |
| URL de validación | Solo `validate-sod` (sin consumidor) | `separation-rules/validate` (con consumidor) |
| Nombres de clases | `SoDRule*`, `SoDValidator` | `SeparationRule*`, `DutySeparationValidator` |
| Error codes | `SOD_VIOLATION`, `SOD_RULE_*` | `SEPARATION_RULE_VIOLATION`, `SEPARATION_RULE_*` |
| Event types | `SOD_RULE_*` | `SEPARATION_RULE_*` |
| Related names | `sod_rules_as_set_a/b` | `separation_rules_as_set_a/b` |
| Documentación UCs | 237 líneas con `SoD/SOD` | 0 líneas con abreviatura en identificadores |
| IACT-ui | Sin cambios necesarios | Sin cambios necesarios |
| Bug de integración | Activo (sod-rules vs separation-rules) | Resuelto |
| Endpoint faltante | `separation-rules/validate` inexistente | Implementado |
| STD_008 cumplimiento | Violado | Conforme |
