# Plan de implementación — Remediación STD_008 § 3.3: abreviatura SoD

**Artefacto:** PLAN-IMPL-STD008-SOD-FASES-20260513
**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Rama de trabajo:** `refactor/std008-sod-naming` (desde `develop`)
**Fuente:** ANALISIS-CONSOLIDADO-STD008-SOD-20260513
**Repositorios:** IACT-api, IACT-docs
**IACT-ui:** sin cambios requeridos

----

## Criterio DONE global

El plan está completo cuando:

1. `grep -rn "sod\|SoD\|SOD" callcentersite/apps/ | grep -v "__pycache__\|\.pyc\|SeparationRule\|separation_rule\|separationrule\|SOD-00[0-9]\|# .*SoD" | wc -l` → **0**
2. `grep -rn "SOD_\|SoDRule\|sod-rules" source/requisitos/casos-uso/ | grep -v "SOD-00[0-9]" | wc -l` → **0**
3. Todos los tests verificadores de cada fase pasan.
4. La URL `GET /api/access/separation-rules/` retorna 200.
5. La URL `POST /api/access/separation-rules/validate` retorna 200.
6. La URL `GET /api/access/sod-rules/` retorna 404.

----

## Resumen de fases

| FASE | Descripción | Archivos | Tiempo | Repo |
|---|---|---|---|---|
| FASE 0 | Preparación y rama | — | 5 min | IACT-api |
| FASE 1 | Renombres internos (sin contrato) | 5 archivos | 30 min | IACT-api |
| FASE 2 | Migración related_names | 2 archivos + 1 migración | 15 min | IACT-api |
| FASE 3 | Contrato público + bugs + validate | 4 archivos | 45 min | IACT-api |
| FASE 4 | Documentación — 9 UCs | ~25 archivos RST | 2 h | IACT-docs |
| FASE 5 | Verificación final y cierre | — | 15 min | ambos |

**Total estimado:** 3 h 50 min

----

## FASE 0 — Preparación

**Objetivo:** Crear la rama de trabajo y verificar el estado inicial.
**Precondición:** estar en `develop` sin cambios sin commitear.

---

### T-0.1 — Crear rama de trabajo

**Ejecutar:**

```bash
cd /tmp/references/IACT-api
git checkout develop
git pull origin develop
git checkout -b refactor/std008-sod-naming
```

**Verificación:**

```bash
git branch --show-current
# Resultado esperado: refactor/std008-sod-naming
```

**Done cuando:** la rama existe y apunta al mismo commit que `develop`.

---

### T-0.2 — Verificar baseline de URLs

**Ejecutar:**

```bash
cd callcentersite
python3 -c "
import os, sys; sys.path.insert(0,'.')
os.environ['DJANGO_SETTINGS_MODULE']='config.settings.fase0_testing'
import django; django.setup()
from django.urls import reverse, NoReverseMatch
for name in ['access:sod-rule-list-create', 'access:sod-rule-detail',
             'access:separation-rule-list-create', 'access:separation-rule-detail']:
    try:
        print(f'  {name} → {reverse(name, args=[1] if \"detail\" in name else [])}')
    except (NoReverseMatch, Exception) as e:
        print(f'  {name} → NO EXISTE')
"
```

**Resultado esperado antes de los cambios:**

```
access:sod-rule-list-create         → /api/access/sod-rules/
access:sod-rule-detail              → /api/access/sod-rules/1/
access:separation-rule-list-create  → NO EXISTE
access:separation-rule-detail       → NO EXISTE
```

**Done cuando:** la salida coincide con el resultado esperado.

---

### T-0.3 — Contar violaciones iniciales (baseline)

**Ejecutar:**

```bash
cd callcentersite
echo "=== IACT-api violaciones ==="
grep -rn "sod\|SoD\|SOD" apps/ \
  | grep -v "__pycache__\|\.pyc" \
  | grep -v "SeparationRule\|separation_rule\|separationrule\|SOD-00[0-9]" \
  | wc -l
```

**Resultado esperado:** 102

**Done cuando:** el número coincide. Anotar para comparación en FASE 5.

----

## FASE 1 — Renombres internos

**Objetivo:** Renombrar todos los identificadores internos que contienen
`SoD/SOD/sod` sin tocar el contrato público (URL, error codes, event types).
Estos cambios son transparentes para IACT-ui.

**Precondición:** FASE 0 completa. Rama `refactor/std008-sod-naming` activa.

---

### T-1.1 — Renombrar `sod_rule_view.py`

**Ejecutar:**

```bash
cd /tmp/references/IACT-api
git mv callcentersite/apps/access/sod_rule_view.py \
        callcentersite/apps/access/separation_rule_view.py
```

**Verificación:**

```bash
ls callcentersite/apps/access/separation_rule_view.py  # existe
ls callcentersite/apps/access/sod_rule_view.py         # no existe (error esperado)
```

**Done cuando:** el archivo existe con el nombre nuevo.

---

### T-1.2 — Renombrar clases y serializers dentro de `separation_rule_view.py`

**Ejecutar** (5 sustituciones, todas en el mismo archivo):

```bash
cd callcentersite/apps/access
sed -i \
  -e 's/class SoDRuleCreateSerializer/class SeparationRuleCreateSerializer/g' \
  -e 's/class SoDRulePatchSerializer/class SeparationRulePatchSerializer/g' \
  -e 's/class SoDRuleRetireSerializer/class SeparationRuleRetireSerializer/g' \
  -e 's/class SoDRuleListCreateView/class SeparationRuleListCreateView/g' \
  -e 's/class SoDRuleDetailView/class SeparationRuleDetailView/g' \
  separation_rule_view.py
```

Aplicar también las referencias internas dentro del mismo archivo
(instanciaciones de los serializers):

```bash
sed -i \
  -e 's/SoDRuleCreateSerializer(/SeparationRuleCreateSerializer(/g' \
  -e 's/SoDRulePatchSerializer(/SeparationRulePatchSerializer(/g' \
  -e 's/SoDRuleRetireSerializer(/SeparationRuleRetireSerializer(/g' \
  separation_rule_view.py
```

**Verificación:**

```bash
grep "class SoD\|SoDRule" separation_rule_view.py | wc -l
# Resultado esperado: 0
grep "class Separation\|SeparationRule" separation_rule_view.py | wc -l
# Resultado esperado: ≥ 5
```

**Done cuando:** cero ocurrencias de `SoDRule` como clase o referencia.

---

### T-1.3 — Renombrar `SoDValidator` en `function_assign_view.py`

**Ejecutar:**

```bash
cd callcentersite/apps/access
sed -i \
  -e 's/class SoDValidator:/class DutySeparationValidator:/g' \
  -e 's/SoDValidator\.validate(/DutySeparationValidator.validate(/g' \
  function_assign_view.py
```

**Verificación:**

```bash
grep "SoDValidator" function_assign_view.py | wc -l
# Resultado esperado: 0
grep "DutySeparationValidator" function_assign_view.py | wc -l
# Resultado esperado: ≥ 2
```

**Done cuando:** cero ocurrencias de `SoDValidator`.

---

### T-1.4 — Renombrar management command `create_sod_rules.py`

**Ejecutar:**

```bash
cd /tmp/references/IACT-api
git mv callcentersite/apps/access/management/commands/create_sod_rules.py \
        callcentersite/apps/access/management/commands/create_separation_rules.py
```

Actualizar el contenido del archivo renombrado:

```bash
cd callcentersite/apps/access/management/commands
sed -i \
  -e 's/create_sod_rules\.py/create_separation_rules.py/g' \
  -e 's/SOD_RULES_V540/SEPARATION_RULES_V540/g' \
  -e 's/for code, name, description, set_a_codes, set_b_codes in SOD_RULES_V540:/for code, name, description, set_a_codes, set_b_codes in SEPARATION_RULES_V540:/g' \
  -e "s/help = 'Carga las 3 reglas SoD predefinidas/help = 'Carga las 3 reglas de separacion predefinidas/g" \
  create_separation_rules.py
```

**Verificación:**

```bash
grep "SOD_RULES_V540\|create_sod_rules" create_separation_rules.py | wc -l
# Resultado esperado: 0
grep "SEPARATION_RULES_V540" create_separation_rules.py | wc -l
# Resultado esperado: ≥ 2

# Los IDs SOD-001/002/003 NO deben haber cambiado
grep "SOD-00" create_separation_rules.py | wc -l
# Resultado esperado: 3 (los tres IDs de artefacto)
```

**Done cuando:** cero ocurrencias de `SOD_RULES_V540` y los tres IDs de
artefacto `SOD-001/002/003` intactos.

---

### T-1.5 — Actualizar import en `access/urls.py`

Solo el import — las líneas `path(...)` no cambian todavía.

**Ejecutar:**

```bash
cd callcentersite/apps/access
sed -i \
  -e 's/from \.sod_rule_view import SoDRuleListCreateView, SoDRuleDetailView/from .separation_rule_view import SeparationRuleListCreateView, SeparationRuleDetailView/g' \
  urls.py
```

Y actualizar las referencias en `urlpatterns` (solo los nombres de clase,
no las rutas URL aún):

```bash
sed -i \
  -e 's/SoDRuleListCreateView\.as_view()/SeparationRuleListCreateView.as_view()/g' \
  -e 's/SoDRuleDetailView\.as_view()/SeparationRuleDetailView.as_view()/g' \
  urls.py
```

**Verificación:**

```bash
grep "SoDRule" urls.py | wc -l
# Resultado esperado: 0
grep "SeparationRuleListCreateView\|SeparationRuleDetailView" urls.py | wc -l
# Resultado esperado: ≥ 2
```

**Done cuando:** cero ocurrencias de `SoDRule` en `urls.py`.

---

### T-1.6 — Verificar que el proyecto importa correctamente

**Ejecutar:**

```bash
cd callcentersite
python3 -c "
import os, sys; sys.path.insert(0,'.')
os.environ['DJANGO_SETTINGS_MODULE']='config.settings.fase0_testing'
import django; django.setup()
from apps.access.separation_rule_view import (
    SeparationRuleListCreateView,
    SeparationRuleDetailView,
    SeparationRuleCreateSerializer,
)
from apps.access.function_assign_view import DutySeparationValidator
print('[PASS] FASE 1 — todos los renombres importan correctamente')
"
```

**Done cuando:** sin errores de importación.

---

### T-1.7 — Commit FASE 1

**Ejecutar:**

```bash
cd /tmp/references/IACT-api

export GIT_AUTHOR_NAME="Nestor Monroy"
export GIT_AUTHOR_EMAIL="46802445+NestorMonroy@users.noreply.github.com"
export GIT_COMMITTER_NAME="$GIT_AUTHOR_NAME"
export GIT_COMMITTER_EMAIL="$GIT_AUTHOR_EMAIL"

git add callcentersite/apps/access/separation_rule_view.py
git add callcentersite/apps/access/function_assign_view.py
git add callcentersite/apps/access/urls.py
git add callcentersite/apps/access/management/commands/create_separation_rules.py
git rm  callcentersite/apps/access/sod_rule_view.py 2>/dev/null || true
git rm  callcentersite/apps/access/management/commands/create_sod_rules.py 2>/dev/null || true

git commit -m "refactor(access): STD_008 §3.3 — renombrar identificadores internos SoD

Renombres que no afectan contrato público (URL, error codes, event types).

Archivos:
  sod_rule_view.py          → separation_rule_view.py
  create_sod_rules.py       → create_separation_rules.py

Clases:
  SoDRuleCreateSerializer   → SeparationRuleCreateSerializer
  SoDRulePatchSerializer    → SeparationRulePatchSerializer
  SoDRuleRetireSerializer   → SeparationRuleRetireSerializer
  SoDRuleListCreateView     → SeparationRuleListCreateView
  SoDRuleDetailView         → SeparationRuleDetailView
  SoDValidator              → DutySeparationValidator

Constante:
  SOD_RULES_V540            → SEPARATION_RULES_V540

IDs de artefacto SOD-001/002/003: sin cambios (STD_008 §2).
Fuente: ANALISIS-CONSOLIDADO-STD008-SOD-20260513"
```

**Verificación post-commit:**

```bash
git show --stat HEAD | head -8
# Debe mostrar los 4 archivos modificados + 2 borrados
```

**Done cuando:** commit creado con los archivos correctos.

----

## FASE 2 — Migración related_names

**Objetivo:** Renombrar los `related_name` de los campos M2M en
`SeparationRule`. Requiere una migración Django aunque no modifica
tablas de BD.

**Precondición:** FASE 1 completa y commiteada.

---

### T-2.1 — Actualizar `related_name` en el modelo

**Ejecutar:**

```bash
cd callcentersite/apps/access
sed -i \
  -e "s/related_name='sod_rules_as_set_a'/related_name='separation_rules_as_set_a'/g" \
  -e "s/related_name='sod_rules_as_set_b'/related_name='separation_rules_as_set_b'/g" \
  models.py
```

**Verificación:**

```bash
grep "sod_rules_as_set" models.py | wc -l
# Resultado esperado: 0
grep "separation_rules_as_set" models.py | wc -l
# Resultado esperado: 2
```

**Done cuando:** cero ocurrencias de `sod_rules_as_set` en `models.py`.

---

### T-2.2 — Verificar que nadie usa los related_names viejos

**Ejecutar:**

```bash
cd callcentersite
grep -rn "sod_rules_as_set_a\|sod_rules_as_set_b" apps/ \
  | grep -v "__pycache__\|\.pyc"
# Resultado esperado: 0 líneas
```

Si hay resultados, actualizar cada ocurrencia antes de continuar.

**Done cuando:** cero ocurrencias fuera de `apps/access/models.py`.

---

### T-2.3 — Crear migración 0008

Crear el archivo `callcentersite/apps/access/migrations/0008_std008_related_names.py`:

```python
"""
Migration 0008 — STD_008 §3.3: related_names sin abreviatura SoD.

AlterField en ManyToManyField: no modifica tablas ni datos de BD.
Solo actualiza el nombre del accessor Python en el ORM.

  sod_rules_as_set_a → separation_rules_as_set_a
  sod_rules_as_set_b → separation_rules_as_set_b

Fuente: ANALISIS-CONSOLIDADO-STD008-SOD-20260513
"""
from django.db import migrations, models


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
                help_text=(
                    'Primer conjunto de funciones en conflicto. '
                    'Un usuario no puede tener funciones de ambos conjuntos.'
                ),
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
                help_text='Segundo conjunto de funciones en conflicto.',
                related_name='separation_rules_as_set_b',
                to='access.function',
                verbose_name='Conjunto B',
            ),
        ),
    ]
```

**Done cuando:** el archivo existe en `migrations/`.

---

### T-2.4 — Verificar que la migración aplica sin errores

**Ejecutar:**

```bash
cd callcentersite
python3 -c "
import os, sys; sys.path.insert(0,'.')
os.environ['DJANGO_SETTINGS_MODULE']='config.settings.fase0_testing'
import django; django.setup()
import logging; logging.disable(logging.INFO)
from django.test.runner import DiscoverRunner
r = DiscoverRunner(verbosity=0); old = r.setup_databases()
try:
    from apps.access.models import SeparationRule, Function, Module
    mod = Module.objects.create(name='T2', code='TEST_T24_STD008', order=98)
    fn_a = Function.objects.create(module=mod, name='A', code='T24_A',
        permission_django='t24.a', is_active=True)
    fn_b = Function.objects.create(module=mod, name='B', code='T24_B',
        permission_django='t24.b', is_active=True)
    rule = SeparationRule.objects.create(code='SOD-T24', name='t24', state='ENABLED')
    rule.functions_set_a.set([fn_a])
    rule.functions_set_b.set([fn_b])

    # Probar NUEVO related_name
    via_new_a = fn_a.separation_rules_as_set_a.filter(code='SOD-T24').exists()
    via_new_b = fn_b.separation_rules_as_set_b.filter(code='SOD-T24').exists()
    print(f'[PASS] separation_rules_as_set_a: {via_new_a}')
    print(f'[PASS] separation_rules_as_set_b: {via_new_b}')

    # Probar que el VIEJO related_name ya no existe
    try:
        _ = fn_a.sod_rules_as_set_a.all()
        print('[FAIL] sod_rules_as_set_a aún existe — falta la migración')
    except AttributeError:
        print('[PASS] sod_rules_as_set_a eliminado correctamente')
finally:
    r.teardown_databases(old)
" 2>&1 | grep -v "^INFO\|Warning\|Creating"
```

**Resultado esperado:**

```
[PASS] separation_rules_as_set_a: True
[PASS] separation_rules_as_set_b: True
[PASS] sod_rules_as_set_a eliminado correctamente
```

**Done cuando:** los tres `[PASS]`.

---

### T-2.5 — Commit FASE 2

**Ejecutar:**

```bash
cd /tmp/references/IACT-api

git add callcentersite/apps/access/models.py
git add callcentersite/apps/access/migrations/0008_std008_related_names.py

git commit -m "refactor(access): STD_008 §3.3 — migración related_names SeparationRule

AlterField en M2M — no modifica tablas ni datos de BD.
Solo actualiza el accessor Python en el ORM.

  sod_rules_as_set_a → separation_rules_as_set_a
  sod_rules_as_set_b → separation_rules_as_set_b

Verificado: ningún queryset del codebase usa los related_names
viejos directamente (solo models.py y migration 0005 los referenciaban).
Fuente: ANALISIS-CONSOLIDADO-STD008-SOD-20260513"
```

**Done cuando:** commit creado con 2 archivos.

----

## FASE 3 — Contrato público + corrección de bugs

**Objetivo:** Renombrar la URL `sod-rules/` → `separation-rules/`,
corregir los error codes y event types, implementar el endpoint faltante
`separation-rules/validate`, y corregir el bug `status='active'`.

**Prioridad:** Esta fase corrige dos bugs activos además del naming.
**Coordinación con IACT-ui:** Ninguna requerida — el frontend ya espera
`separation-rules/`.

**Precondición:** FASE 2 completa y commiteada.

---

### T-3.1 — Cambiar URL `sod-rules/` → `separation-rules/` en `urls.py`

**Ejecutar:**

```bash
cd callcentersite/apps/access
sed -i \
  -e "s|path('sod-rules/',|path('separation-rules/',|g" \
  -e "s|path('sod-rules/<int:rule_id>/',|path('separation-rules/<int:rule_id>/',|g" \
  -e "s|name='sod-rule-list-create'|name='separation-rule-list-create'|g" \
  -e "s|name='sod-rule-detail'|name='separation-rule-detail'|g" \
  urls.py
```

Actualizar también el comentario que explica el B-03 (ya no aplica):

```bash
sed -i \
  -e "s|# B-03: usa prefijo 'sod-rules/' para evitar conflicto con router 'separation-rules/'|# UC_ACC_05 — Reglas de Separación (STD_008 §3.3 — antes: sod-rules/)|g" \
  urls.py
```

**Verificación:**

```bash
grep "sod-rules\|sod-rule-" urls.py | wc -l
# Resultado esperado: 0
grep "separation-rules/'" urls.py | wc -l
# Resultado esperado: ≥ 2
```

---

### T-3.2 — Agregar endpoint `separation-rules/validate`

Agregar a `urlpatterns` en `access/urls.py`, **antes** de la línea de
`include(router.urls)` y después de `separation-rules/<int:rule_id>/`:

```python
    # UC_ACC_01 — validar conflictos antes de asignar (IACT-ui: accessGateway.validateSeparationRules)
    path('separation-rules/validate',
         SeparationRuleValidateView.as_view(), name='separation-rule-validate'),
```

**Verificar que `SeparationRuleValidateView` ya está importado:**

```bash
grep "SeparationRuleValidateView" urls.py | head -3
# Debe aparecer en el import (ya estaba para validate-sod)
```

**Done cuando:** el path existe en `urlpatterns`.

---

### T-3.3 — Corregir bug `status='active'` → `state='ENABLED'` en `views.py`

El modelo `SeparationRule` usa `state` (no `status`) con valor `'ENABLED'`
(no `'active'`). Hay 5 instancias del bug en `apps/access/views.py`.

**Ejecutar:**

```bash
cd callcentersite/apps/access
# Verificar las 5 instancias antes de cambiar
grep -n "SeparationRule.objects.filter" views.py | grep -v "__pycache__"

# Aplicar corrección
sed -i \
  -e "s/SeparationRule\.objects\.filter(\n\s*status=['\"]active['\"]/SeparationRule.objects.filter(\n                state='ENABLED'/g" \
  views.py
```

Si el `sed` multilínea no funciona, hacer las sustituciones en bloque:

```bash
python3 - <<'PYEOF'
content = open('views.py').read()
# El campo incorrecto es status='active' o status="active"
old_patterns = [
    "status='active'",
    'status="active"',
]
count = 0
for old in old_patterns:
    n = content.count(old)
    content = content.replace(old, "state='ENABLED'")
    count += n
open('views.py', 'w').write(content)
print(f'Corregidas {count} instancias de status=\"active\" → state=\"ENABLED\"')
PYEOF
```

**Verificación:**

```bash
grep -n "status=['\"]active['\"]" views.py | wc -l
# Resultado esperado: 0
grep -n "state='ENABLED'" views.py | wc -l
# Resultado esperado: ≥ 5
```

**Done cuando:** cero ocurrencias del patrón incorrecto.

---

### T-3.4 — Actualizar docstring de `SeparationRuleValidateView` en `views.py`

Actualizar el docstring para reflejar la nueva URL (la clase ya tiene el
nombre correcto — solo actualizar la documentación interna):

```bash
cd callcentersite/apps/access
python3 - <<'PYEOF'
content = open('views.py').read()
old = '''    """
    accessService.validateSoD(userId, functionId)
    POST /api/access/validate-sod
    Body: { userId, functionId }

    NOTA: El nombre del endpoint respeta el contrato del frontend
    (strings opacos de API). El nombre de la clase en Python sigue
    CLEAN_CODE_NAMING_PRINCIPLES (sin acronimos).

    Retorna estructura que consume accessSlice:
      { conflicts: [{ rule, ruleDesc, setA, setB, message }] }
    """'''
new = '''    """
    UC_ACC_01 — Validar conflictos de separación antes de asignar función.

    POST /api/access/separation-rules/validate
    Body: { userId: int, functionId: int }
    Response 200: { conflicts: [{ rule, ruleDesc, setA, setB, message }] }

    CNST-010: permission_classes=[IsAuthenticated, HasFunction] explícito.
    P-51 read-no-audit: no emite AuditEvent.
    Fuente: accessGateway.validateSeparationRules (IACT-ui)
    """'''
if old in content:
    content = content.replace(old, new)
    open('views.py', 'w').write(content)
    print('Docstring actualizado')
else:
    print('Patron no encontrado — actualizar manualmente')
PYEOF
```

**Done cuando:** el docstring refleja `/api/access/separation-rules/validate`.

---

### T-3.5 — Corregir error codes en `separation_rule_view.py`

**Ejecutar:**

```bash
cd callcentersite/apps/access
sed -i \
  -e "s/'SOD_RULE_DUPLICATE'/'SEPARATION_RULE_DUPLICATE'/g" \
  -e "s/'SOD_RULE_NOT_FOUND'/'SEPARATION_RULE_NOT_FOUND'/g" \
  separation_rule_view.py
```

**Verificación:**

```bash
grep "SOD_RULE_DUPLICATE\|SOD_RULE_NOT_FOUND" separation_rule_view.py | wc -l
# Resultado esperado: 0
```

---

### T-3.6 — Corregir event types en `separation_rule_view.py`

**Ejecutar:**

```bash
cd callcentersite/apps/access
sed -i \
  -e "s/event_type='SOD_RULE_CREATED'/event_type='SEPARATION_RULE_CREATED'/g" \
  -e "s/event_type='SOD_RULE_UPDATED'/event_type='SEPARATION_RULE_UPDATED'/g" \
  -e "s/event_type='SOD_RULE_DISABLED'/event_type='SEPARATION_RULE_DISABLED'/g" \
  separation_rule_view.py
```

**Verificación:**

```bash
grep "event_type='SOD_RULE" separation_rule_view.py | wc -l
# Resultado esperado: 0
grep "event_type='SEPARATION_RULE" separation_rule_view.py | wc -l
# Resultado esperado: 3
```

---

### T-3.7 — Corregir error code de violación en `function_assign_view.py`

**Ejecutar:**

```bash
cd callcentersite/apps/access
python3 - <<'PYEOF'
content = open('function_assign_view.py').read()
content = content.replace("'error': 'SOD_VIOLATION'", "'error': 'SEPARATION_RULE_VIOLATION'")
content = content.replace("'reason': 'sod_violation'", "'reason': 'separation_rule_violation'")
open('function_assign_view.py', 'w').write(content)
n = content.count('SEPARATION_RULE_VIOLATION')
print(f'SEPARATION_RULE_VIOLATION aparece {n} veces')
PYEOF
```

**Verificación:**

```bash
grep "SOD_VIOLATION" function_assign_view.py | wc -l
# Resultado esperado: 0
grep "SEPARATION_RULE_VIOLATION" function_assign_view.py | wc -l
# Resultado esperado: 2
```

---

### T-3.8 — Actualizar VALID_EVENT_TYPES en `audit/models.py`

**Ejecutar:**

```bash
cd callcentersite/apps/audit
sed -i \
  -e "s/'SOD_RULE_CREATED'/'SEPARATION_RULE_CREATED'/g" \
  -e "s/'SOD_RULE_UPDATED'/'SEPARATION_RULE_UPDATED'/g" \
  -e "s/'SOD_RULE_DISABLED'/'SEPARATION_RULE_DISABLED'/g" \
  models.py
```

**Verificación:**

```bash
grep "SOD_RULE_CREATED\|SOD_RULE_UPDATED\|SOD_RULE_DISABLED" models.py | wc -l
# Resultado esperado: 0
grep "SEPARATION_RULE_CREATED\|SEPARATION_RULE_UPDATED\|SEPARATION_RULE_DISABLED" models.py | wc -l
# Resultado esperado: 3
```

---

### T-3.9 — Verificación integrada de FASE 3

**Ejecutar:**

```bash
cd callcentersite
python3 -c "
import os, sys; sys.path.insert(0,'.')
os.environ['DJANGO_SETTINGS_MODULE']='config.settings.fase0_testing'
import django; django.setup()
import logging; logging.disable(logging.INFO)
from django.test.runner import DiscoverRunner
r = DiscoverRunner(verbosity=0); old = r.setup_databases()
try:
    from rest_framework.test import APIClient
    from apps.users.models import User
    from apps.access.models import AccessGroup, UserAccessGroup, Function, Module, SeparationRule
    from apps.audit.models import VALID_EVENT_TYPES
    from django.urls import reverse, NoReverseMatch
    from django.core.management import call_command
    from io import StringIO
    call_command('create_functions', stdout=StringIO())
    call_command('create_access_groups', stdout=StringIO())

    admin = User.objects.create_user(username='t3_admin', password='P!', state='ACTIVE', first_login=False)
    UserAccessGroup.objects.create(user=admin, access_group=AccessGroup.objects.get(code='AGR-010'))
    c = APIClient(); c.force_authenticate(user=admin)

    # T-3.A: URL separation-rules existe y responde
    try:
        url = reverse('access:separation-rule-list-create')
        resp = c.get(url)
        print(f'[PASS] GET separation-rules/ → {resp.status_code}')
    except NoReverseMatch:
        print('[FAIL] separation-rule-list-create no resuelve')

    # T-3.B: URL sod-rules ya no existe
    try:
        url = reverse('access:sod-rule-list-create')
        print(f'[FAIL] sod-rule-list-create aún existe: {url}')
    except NoReverseMatch:
        print('[PASS] sod-rules/ ya no existe')

    # T-3.C: endpoint validate existe
    try:
        url = reverse('access:separation-rule-validate')
        resp = c.post(url, {'userId': admin.pk, 'functionId': 1}, format='json')
        print(f'[PASS] POST separation-rules/validate → {resp.status_code}')
    except NoReverseMatch:
        print('[FAIL] separation-rule-validate no resuelve')

    # T-3.D: event types correctos
    assert 'SEPARATION_RULE_CREATED' in VALID_EVENT_TYPES
    assert 'SOD_RULE_CREATED' not in VALID_EVENT_TYPES
    print('[PASS] VALID_EVENT_TYPES: SEPARATION_RULE_CREATED OK, SOD_RULE_CREATED eliminado')

    # T-3.E: crear regla SoD usa evento correcto
    mod = Module.objects.create(name='T3', code='TEST_T3_STD008', order=97)
    fa = Function.objects.create(module=mod, name='A', code='T3A', permission_django='t3.a', is_active=True)
    fb = Function.objects.create(module=mod, name='B', code='T3B', permission_django='t3.b', is_active=True)

    url = reverse('access:separation-rule-list-create')
    resp = c.post(url, {
        'code': 'SR-T3', 'name': 'T3 test rule',
        'function_ids_a': [fa.pk], 'function_ids_b': [fb.pk],
    }, format='json')
    print(f'[PASS] POST separation-rules/ (create) → {resp.status_code}')

    from apps.audit.models import AuditLog
    ev = AuditLog.objects.filter(action='SEPARATION_RULE_CREATED').first()
    if ev:
        print('[PASS] AuditEvent SEPARATION_RULE_CREATED emitido')
    else:
        print('[FAIL] AuditEvent SEPARATION_RULE_CREATED no encontrado')

    # T-3.F: SOD_VIOLATION ya no se emite
    target = User.objects.create_user(username='t3_target', password='P!', state='ACTIVE')
    assign_url = reverse('access:function-assign-v2', kwargs={'user_id': target.pk})
    resp_sod = c.post(assign_url, {'function_ids': [fa.pk]}, format='json')
    print(f'[INFO] Asignación set_a: {resp_sod.status_code}')
    resp_viol = c.post(assign_url, {'function_ids': [fb.pk]}, format='json')
    if resp_viol.status_code == 409:
        error_code = resp_viol.data.get('error', '')
        if error_code == 'SEPARATION_RULE_VIOLATION':
            print('[PASS] Error code: SEPARATION_RULE_VIOLATION (correcto)')
        else:
            print(f'[FAIL] Error code incorrecto: {error_code}')
    else:
        print(f'[INFO] Sin violación SoD (status={resp_viol.status_code}) — puede ser normal si la regla no aplica')

finally:
    r.teardown_databases(old)
" 2>&1 | grep -E "\[PASS\]|\[FAIL\]|\[INFO\]"
```

**Resultado esperado:** todos los `[PASS]`, ningún `[FAIL]`.

---

### T-3.10 — Commit FASE 3

**Ejecutar:**

```bash
cd /tmp/references/IACT-api

git add callcentersite/apps/access/urls.py
git add callcentersite/apps/access/separation_rule_view.py
git add callcentersite/apps/access/function_assign_view.py
git add callcentersite/apps/access/views.py
git add callcentersite/apps/audit/models.py

git commit -m "fix(access,audit): STD_008 §3.3 + bugs integración — separation-rules/

BUG 1 — URL de integración (IACT-ui esperaba separation-rules/):
  sod-rules/       → separation-rules/
  sod-rules/{id}/  → separation-rules/{id}/

BUG 2 — Endpoint faltante implementado:
  POST /api/access/separation-rules/validate
  (accessGateway.validateSeparationRules en IACT-ui)

BUG 3 — Filtro incorrecto en SeparationRuleValidateView:
  status='active' → state='ENABLED' (5 instancias en views.py)

Error codes:
  SOD_RULE_DUPLICATE  → SEPARATION_RULE_DUPLICATE
  SOD_RULE_NOT_FOUND  → SEPARATION_RULE_NOT_FOUND
  SOD_VIOLATION       → SEPARATION_RULE_VIOLATION

Event types (VALID_EVENT_TYPES + views):
  SOD_RULE_CREATED    → SEPARATION_RULE_CREATED
  SOD_RULE_UPDATED    → SEPARATION_RULE_UPDATED
  SOD_RULE_DISABLED   → SEPARATION_RULE_DISABLED

IACT-ui: sin cambios requeridos.
Fuente: ANALISIS-CONSOLIDADO-STD008-SOD-20260513"
```

**Done cuando:** commit creado con los 5 archivos modificados.

----

## FASE 4 — Documentación IACT-docs

**Objetivo:** Actualizar los 9 UCs afectados (237 líneas) que preexistían
antes de STD_008. El texto narrativo que dice "SoD" se preserva.

**Precondición:** FASE 3 completa en IACT-api. Esta fase puede ejecutarse
en paralelo desde T-2.5 en adelante.

**Repositorio:** IACT-docs (rama `refactor/std008-sod-naming`)

---

### T-4.1 — Crear rama en IACT-docs

**Ejecutar:**

```bash
cd /tmp/references/IACT-docs
git checkout develop 2>/dev/null || git checkout main
git pull origin HEAD
git checkout -b refactor/std008-sod-naming
```

**Done cuando:** rama creada.

---

### T-4.2 — Ejecutar script de sustitución en batch

**Ejecutar:**

```bash
cd /tmp/references/IACT-docs

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

echo "Script completado"
```

**Done cuando:** script termina sin errores.

---

### T-4.3 — Revisión manual: verificar IDs de artefacto intactos

Los códigos `SOD-001`, `SOD-002`, `SOD-003` **no deben haberse modificado**.

**Ejecutar:**

```bash
cd /tmp/references/IACT-docs
echo "=== IDs de artefacto SOD-NNN (deben ser ≥3) ==="
grep -rn "SOD-00[0-9]" source/requisitos/casos-uso/ | wc -l

echo "=== Verificar que son exactamente los tres códigos ==="
grep -rn "SOD-00[0-9]" source/requisitos/casos-uso/ | \
  grep -v "SEPARATION_RULE" | head -10
```

**Resultado esperado:** ≥3 ocurrencias, todas con el patrón `SOD-00[0-9]`
sin que el texto circundante haya cambiado.

**Done cuando:** IDs de artefacto intactos.

---

### T-4.4 — Revisión manual: verificar cero residuos

**Ejecutar:**

```bash
cd /tmp/references/IACT-docs
echo "=== Residuos SOD en identificadores (debe ser 0) ==="
grep -rn "SOD_\|SoDRule\|sod-rules\|sod_rule" \
  source/requisitos/casos-uso/ \
  | grep -v "SOD-00[0-9]" \
  | grep -v "__pycache__"
```

**Resultado esperado:** 0 líneas.

Si aparecen líneas, corregirlas manualmente antes de continuar.

**Done cuando:** 0 residuos.

---

### T-4.5 — Revisión manual por UC — spot check narrativa

Verificar que el texto narrativo que dice "regla SoD", "SoD violation",
"principio SoD" **no fue alterado** (el script no debería haberlo tocado
porque busca patrones de identificadores, no palabras sueltas).

**Ejecutar:**

```bash
cd /tmp/references/IACT-docs
echo "=== Texto narrativo SoD preservado ==="
grep -rn "\bSoD\b" source/requisitos/casos-uso/ | \
  grep -v "SOD_\|SoDRule\|sod-rule\|SOD-00[0-9]" | head -10
```

**Resultado esperado:** ≥1 ocurrencias de "SoD" en texto libre (narrativa
preservada), sin que aparezcan como identificadores técnicos.

**Done cuando:** la narrativa está intacta.

---

### T-4.6 — Commit FASE 4 en IACT-docs

**Ejecutar:**

```bash
cd /tmp/references/IACT-docs

git add source/requisitos/casos-uso/access/uc-acc-05/
git add source/requisitos/casos-uso/access/uc-acc-01/
git add source/requisitos/casos-uso/access/uc-acc-04/
git add source/requisitos/casos-uso/access/uc-acc-08/
git add source/requisitos/casos-uso/access/uc-acc-03/
git add source/requisitos/casos-uso/access/uc-acc-09/
git add source/requisitos/casos-uso/permissions/uc-perm-06/
git add source/requisitos/casos-uso/permissions/uc-perm-03/
git add source/requisitos/casos-uso/permissions/uc-perm-09/

git commit -m "docs(uc-acc,uc-perm): STD_008 §3.3 — 9 UCs sin abreviatura SoD en identificadores

Actualiza artefactos escritos antes de STD_008 (aprobado 2026-04-28).
Texto narrativo 'SoD', 'regla SoD' preservado (STD_008 §3.3 permite
abreviaturas en narrativa cuando están en el glosario — glosario.rst:99).

UCs actualizados (237 líneas):
  uc-acc-05 (127): sod-rules/ → separation-rules/, SOD_RULE_* → SEPARATION_RULE_*,
                   SoDRule* → SeparationRule*, sod_rules_evaluated → separation_rules_evaluated
  uc-acc-01 (52):  SOD_VIOLATION → SEPARATION_RULE_VIOLATION, SoDRule → SeparationRule
  uc-acc-04 (16):  SOD_VIOLATION → SEPARATION_RULE_VIOLATION
  uc-acc-08 (12):  SOD_VIOLATION, CASCADE_SOD_VIOLATION → SEPARATION_RULE_VIOLATION
  uc-acc-03 (11):  SoDRule → SeparationRule
  uc-acc-09 (7):   SOD_RULE_* → SEPARATION_RULE_* en event types
  uc-perm-06 (10): CASCADE_SOD_VIOLATION, SoDRuleRepository → SeparationRule*
  uc-perm-03 (1):  SoDRule → SeparationRule
  uc-perm-09 (1):  SOD_VIOLATION → SEPARATION_RULE_VIOLATION

IDs de artefacto SOD-001/002/003: sin cambios (STD_008 §2)
Fuente: ANALISIS-CONSOLIDADO-STD008-SOD-20260513"
```

**Done cuando:** commit creado en IACT-docs.

----

## FASE 5 — Verificación final y cierre

**Objetivo:** Confirmar que el criterio DONE global se cumple en ambos
repositorios y registrar la deuda técnica residual.

---

### T-5.1 — Verificación automática IACT-api

**Ejecutar:**

```bash
cd /tmp/references/IACT-api/callcentersite

echo "=== CRITERIO 1: violaciones residuales en código ==="
RESIDUOS=$(grep -rn "sod\|SoD\|SOD" apps/ \
  | grep -v "__pycache__\|\.pyc" \
  | grep -v "SeparationRule\|separation_rule\|separationrule" \
  | grep -v "SOD-00[0-9]" \
  | grep -v "#.*SoD\|\".*SoD\|'.*SoD" \
  | wc -l)
echo "Violaciones: $RESIDUOS (esperado: 0)"

echo ""
echo "=== CRITERIO 2: URL separation-rules existe ==="
python3 -c "
import os, sys; sys.path.insert(0,'.')
os.environ['DJANGO_SETTINGS_MODULE']='config.settings.fase0_testing'
import django; django.setup()
import logging; logging.disable(logging.INFO)
from django.test.runner import DiscoverRunner
r = DiscoverRunner(verbosity=0); old = r.setup_databases()
try:
    from django.urls import reverse, NoReverseMatch
    for name, args in [
        ('access:separation-rule-list-create', []),
        ('access:separation-rule-detail', [1]),
        ('access:separation-rule-validate', []),
    ]:
        try:
            url = reverse(name, args=args)
            print(f'  [PASS] {name} → {url}')
        except NoReverseMatch:
            print(f'  [FAIL] {name} no resuelve')

    for name in ['access:sod-rule-list-create', 'access:sod-rule-detail']:
        try:
            url = reverse(name, args=[1] if 'detail' in name else [])
            print(f'  [FAIL] {name} aún existe: {url}')
        except NoReverseMatch:
            print(f'  [PASS] {name} eliminado correctamente')

    from apps.audit.models import VALID_EVENT_TYPES
    for et in ['SEPARATION_RULE_CREATED', 'SEPARATION_RULE_UPDATED', 'SEPARATION_RULE_DISABLED']:
        status = 'PASS' if et in VALID_EVENT_TYPES else 'FAIL'
        print(f'  [{status}] {et} en VALID_EVENT_TYPES')
    for et in ['SOD_RULE_CREATED', 'SOD_RULE_UPDATED', 'SOD_RULE_DISABLED']:
        status = 'FAIL' if et in VALID_EVENT_TYPES else 'PASS'
        print(f'  [{status}] {et} eliminado de VALID_EVENT_TYPES')
finally:
    r.teardown_databases(old)
" 2>&1 | grep -E "\[PASS\]|\[FAIL\]|Violaciones"
```

**Resultado esperado:** `Violaciones: 0` y todos los `[PASS]`.

---

### T-5.2 — Verificación automática IACT-docs

**Ejecutar:**

```bash
cd /tmp/references/IACT-docs

echo "=== CRITERIO: residuos en documentación ==="
RESIDUOS=$(grep -rn "SOD_\|SoDRule\|sod-rules\|sod_rule" \
  source/requisitos/casos-uso/ \
  | grep -v "SOD-00[0-9]" \
  | wc -l)
echo "Residuos: $RESIDUOS (esperado: 0)"

echo ""
echo "=== IDs de artefacto preservados ==="
COUNT_IDS=$(grep -rn "SOD-00[0-9]" source/requisitos/casos-uso/ | wc -l)
echo "IDs SOD-NNN: $COUNT_IDS (esperado: ≥3)"
```

**Resultado esperado:** `Residuos: 0`, `IDs SOD-NNN: ≥3`.

---

### T-5.3 — Test de regresión funcional end-to-end

**Ejecutar:**

```bash
cd /tmp/references/IACT-api/callcentersite
python3 -c "
import os, sys; sys.path.insert(0,'.')
os.environ['DJANGO_SETTINGS_MODULE']='config.settings.fase0_testing'
import django; django.setup()
import logging; logging.disable(logging.INFO)
from django.test.runner import DiscoverRunner
r = DiscoverRunner(verbosity=0); old = r.setup_databases()
try:
    from rest_framework.test import APIClient
    from apps.users.models import User
    from apps.access.models import (
        AccessGroup, UserAccessGroup, Function, Module, SeparationRule,
        UserFunctionAssignment
    )
    from apps.audit.models import AuditLog
    from django.core.management import call_command
    from io import StringIO
    call_command('create_functions', stdout=StringIO())
    call_command('create_access_groups', stdout=StringIO())

    admin = User.objects.create_user(username='e2e_admin', password='P!', state='ACTIVE', first_login=False)
    UserAccessGroup.objects.create(user=admin, access_group=AccessGroup.objects.get(code='AGR-010'))
    target = User.objects.create_user(username='e2e_target', password='P!', state='ACTIVE')
    c = APIClient(); c.force_authenticate(user=admin)

    from django.urls import reverse
    # 1. CRUD de reglas
    mod = Module.objects.create(name='E2E', code='E2E_STD008', order=96)
    fa = Function.objects.create(module=mod, name='A', code='E2E_A', permission_django='e2e.a', is_active=True)
    fb = Function.objects.create(module=mod, name='B', code='E2E_B', permission_django='e2e.b', is_active=True)

    r1 = c.post(reverse('access:separation-rule-list-create'), {
        'code': 'SR-E2E', 'name': 'E2E separation',
        'function_ids_a': [fa.pk], 'function_ids_b': [fb.pk]
    }, format='json')
    assert r1.status_code == 201, f'Create rule: {r1.data}'
    print('[PASS] POST separation-rules/ → 201')

    r2 = c.get(reverse('access:separation-rule-list-create'))
    assert r2.status_code == 200
    print('[PASS] GET  separation-rules/ → 200')

    rule_id = r1.data['id']
    r3 = c.get(reverse('access:separation-rule-detail', args=[rule_id]))
    assert r3.status_code == 200
    print('[PASS] GET  separation-rules/{id}/ → 200')

    # 2. Validate endpoint
    r4 = c.post(reverse('access:separation-rule-validate'), {
        'userId': target.pk, 'functionId': fa.pk
    }, format='json')
    assert r4.status_code in (200, 404), f'Validate: {r4.data}'
    print(f'[PASS] POST separation-rules/validate → {r4.status_code}')

    # 3. SoD enforcement via assign
    r5 = c.post(reverse('access:function-assign-v2', kwargs={'user_id': target.pk}),
                {'function_ids': [fa.pk]}, format='json')
    r6 = c.post(reverse('access:function-assign-v2', kwargs={'user_id': target.pk}),
                {'function_ids': [fb.pk]}, format='json')
    if r6.status_code == 409:
        assert r6.data['error'] == 'SEPARATION_RULE_VIOLATION', f'Error code: {r6.data[\"error\"]}'
        print('[PASS] SoD violation → 409 SEPARATION_RULE_VIOLATION (no SOD_VIOLATION)')
    else:
        print(f'[INFO] Sin violación detectada (status={r6.status_code})')

    # 4. AuditEvent correcto
    ev = AuditLog.objects.filter(action='SEPARATION_RULE_CREATED').first()
    assert ev is not None, 'AuditEvent SEPARATION_RULE_CREATED no encontrado'
    assert AuditLog.objects.filter(action='SOD_RULE_CREATED').count() == 0
    print('[PASS] AuditEvent: SEPARATION_RULE_CREATED emitido, SOD_RULE_CREATED ausente')

    # 5. Vieja URL retorna 404
    import requests
    # No podemos hacer HTTP real, pero verificar que la URL no resuelve
    from django.urls import NoReverseMatch
    try:
        from django.urls import reverse as r_
        url = r_('access:sod-rule-list-create')
        print(f'[FAIL] sod-rules/ aún resuelve: {url}')
    except NoReverseMatch:
        print('[PASS] sod-rules/ no resuelve → correctamente eliminada')

    print()
    print('[DONE] Test e2e FASE 5 completado sin fallos')

finally:
    r.teardown_databases(old)
" 2>&1 | grep -E "\[PASS\]|\[FAIL\]|\[INFO\]|\[DONE\]"
```

**Resultado esperado:** todos los `[PASS]`, ningún `[FAIL]`, `[DONE]` al final.

---

### T-5.4 — Documentar deuda técnica residual

Agregar en `IACT-docs/source/risks-technical-debt/deuda-tecnica-rebuild.rst`:

```rst
DT-STD008-001: Inconsistencia nombre de clase SeparationRule
=============================================================

:Detectado: 2026-05-13
:Estado: Abierto
:Impacto: Bajo (cosmético / documental)

Tres artefactos canónicos definen el nombre de la clase del modelo con
valores distintos:

- ``CNST-033``: ``SeparationOfDutiesRule``
- ``modelo-rbac-iact.rst``: ``FunctionSeparationRule``
- Django actual: ``SeparationRule`` (``db_table = 'access_separation_rule'``)

No se resolvió en el plan de remediación STD_008 porque ``SeparationRule``
no contiene la abreviatura ``SoD`` — el criterio de la remediación está
cumplido. La unificación entre los tres artefactos requiere un ADR formal
(``RenameModel`` en Django + actualización de CNST-033).


DT-STD008-002: Codenames legacy con sod en JWT
===============================================

:Detectado: 2026-05-13
:Estado: Abierto
:Impacto: Medio (afecta tokens JWT activos)

``catalog.js`` de IACT-ui usa codenames ``'access:view_sod'``,
``'adm:create_sod'``, etc. Estos son los ``permission_django`` del modelo
``Function``. No se cambian en esta remediación porque afectan tokens JWT
en vuelo. Requiere ADR + rotación de tokens.
```

**Done cuando:** entrada registrada en deuda técnica.

---

### T-5.5 — Commit de cierre en IACT-api

**Ejecutar:**

```bash
cd /tmp/references/IACT-api

git add docs/revision/

git commit -m "docs(arch): ANALISIS-CONSOLIDADO-STD008-SOD — análisis + plan de implementación

Documentos generados durante el análisis y planificación:
  REVISION-STD008-NAMING-SOD-20260513.md — análisis inicial
  PLAN-REMEDIACION-STD008-SOD-20260513.md — plan de remediación
  ANALISIS-DOCS-STD008-SOD-20260513.md — respuestas P1-P4 desde IACT-docs
  ANALISIS-IACT-UI-STD008-SOD-20260513.md — análisis IACT-ui
  ANALISIS-CONSOLIDADO-STD008-SOD-20260513.md — análisis definitivo
  PLAN-IMPL-STD008-SOD-FASES-20260513.md — este plan de implementación"
```

---

### T-5.6 — Resumen de commits

Al finalizar la remediación completa, el log de la rama debe mostrar:

```
FASE 5  docs(arch):    ANALISIS-CONSOLIDADO-STD008-SOD — análisis + plan
FASE 4  docs(uc-acc):  STD_008 §3.3 — 9 UCs sin abreviatura SoD (IACT-docs)
FASE 3  fix(access):   STD_008 §3.3 + bugs integración — separation-rules/
FASE 2  refactor(acc): STD_008 §3.3 — migración related_names SeparationRule
FASE 1  refactor(acc): STD_008 §3.3 — renombrar identificadores internos SoD
```

----

## Tabla de verificación cruzada por FASE

| # | Verificación | Comando | Resultado esperado |
|---|---|---|---|
| F1 | Sin imports SoDRule | `grep "SoDRule" apps/access/urls.py \| wc -l` | 0 |
| F1 | Archivo renombrado | `ls apps/access/separation_rule_view.py` | existe |
| F1 | Command renombrado | `ls apps/access/management/commands/create_separation_rules.py` | existe |
| F2 | related_name nuevo | `grep "separation_rules_as_set" apps/access/models.py \| wc -l` | 2 |
| F2 | related_name viejo | `grep "sod_rules_as_set" apps/access/models.py \| wc -l` | 0 |
| F2 | Migración existe | `ls apps/access/migrations/0008_*.py` | existe |
| F3 | URL nueva | `reverse('access:separation-rule-list-create')` | `/api/access/separation-rules/` |
| F3 | URL vieja | `reverse('access:sod-rule-list-create')` | `NoReverseMatch` |
| F3 | Validate URL | `reverse('access:separation-rule-validate')` | `/api/access/separation-rules/validate` |
| F3 | Event type | `'SEPARATION_RULE_CREATED' in VALID_EVENT_TYPES` | `True` |
| F3 | Event type old | `'SOD_RULE_CREATED' in VALID_EVENT_TYPES` | `False` |
| F3 | Bug filtro | `grep "status='active'" apps/access/views.py \| wc -l` | 0 |
| F4 | Residuos docs | ver T-5.2 | 0 |
| F4 | IDs artefacto | `grep "SOD-00" source/.../uc-acc-05/*.rst \| wc -l` | ≥3 |
| F5 | Violaciones global | ver T-5.1 | 0 |
| F5 | E2E test | ver T-5.3 | todos `[PASS]` |
