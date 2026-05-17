# Hallazgos — Implementación FASE 5: Análisis y corrección CNST-030

**Artefacto:** HALLAZGOS-IMPL-FASE5-DT-RESIDUAL-20260513
**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Repositorio:** IACT-docs (sin git en referencia local — commit pendiente)
**Autor:** Nestor Monroy
**Estado:** Cerrado — cambios aplicados

----

## Resumen ejecutivo

FASE 5 nace del hallazgo documentado en FASE 4: CNST-030 usaba `SoDRule`
como nombre de clase en su pseudocode. Al leer el documento completo
se identificaron cinco desviaciones, no una. El documento describía
un mecanismo de enforcement que nunca existió en producción — un signal
Django `pre_save` sobre un modelo `UserGroup` que tampoco existe. La
corrección actualiza la clase, los campos, el mecanismo de enforcement,
y añade una nota arquitectónica sobre la garantía real del sistema.

| Métrica | Antes | Después |
|---|---|---|
| CNST-030 versión | 2.0.0 | 3.0.0 |
| `:ultimo_cambio:` | 2026-04-28 | 2026-05-13 |
| Nombres de clase incorrectos | 4 ocurrencias de `SoDRule` | 0 |
| Campos de modelo incorrectos | `group_a`, `group_b`, `rationale` | `functions_set_a`, `functions_set_b`, `description` |
| Mecanismo de enforcement incorrecto | signal `pre_save` sobre `UserGroup` | `DutySeparationValidator` en capa DRF |
| Clase de modelo inexistente | `UserGroup` | (eliminada de la spec) |
| Función incorrecta en catálogo | `manage_sod` (SOD-003) | `manage_separation_rules` |
| Nota arquitectónica de enforcement | ausente | §5.1 — capa API vs DB |
| Herramienta de verificación §7.2 | "Test del signal" | `test_separation_rule_validate.py` |

----

## drf-spectacular — no aplica en FASE 5

FASE 5 modifica exclusivamente archivos RST de IACT-docs. No hay
interacción con drf-spectacular.

----

## Análisis de las cinco desviaciones identificadas

### Desviación 1 — Nomenclatura: `SoDRule` no existe

CNST-030 §2.1, §2.3, §3.1 y §5.1 usaban `SoDRule` como nombre de clase.
La clase Django de producción es `SeparationRule` desde la implementación
inicial (FASE 0). `SoDRule` no es un alias, no es una clase abstracta, no
es una versión anterior — nunca existió en producción. Es un nombre
inventado que solo vivía en CNST-030.

### Desviación 2 — Campos del modelo: `group_a`, `group_b`, `rationale` no existen

§2.1 decía: `Modelo SoDRule con campos group_a, group_b, rationale`.
Los campos reales del modelo `SeparationRule` v5.4.0 son:
- `functions_set_a` (ManyToManyField) — no `group_a`
- `functions_set_b` (ManyToManyField) — no `group_b`
- `description` (TextField) — no `rationale`

En ninguna versión del modelo existió un campo llamado `rationale`.
Los campos v5.2.1 (modelo FK binario) eran `restriction_id`, `reason`,
`cnst_reference`, `active` — tampoco coinciden con lo que CNST-030 describía.

### Desviación 3 — Mecanismo de enforcement: signal inexistente

Esta es la desviación más grave porque afecta la garantía que la
restricción documenta.

CNST-030 decía: "Validacion en signal `pre_save` de `UserGroup`".

**Lo que esto implica:** un Django signal `pre_save` dispara ante
cualquier escritura al modelo `UserGroup`, independientemente del
path de escritura (API, Django admin, scripts de migración, ORM directo).
Es un enforcement al nivel de base de datos.

**Lo que realmente existe:** `DutySeparationValidator.validate()`,
llamado desde `FunctionAssignView.post()` y `AGRAssignView.post()`.
Esto es enforcement a nivel de capa DRF — solo protege las peticiones
que pasan por los endpoints canónicos de la API. Las escrituras directas
a la base de datos no están cubiertas.

Esta diferencia no es meramente nomenclatural. Un lector del CNST que
confíe en la descripción del signal puede asumir que SoD es imposible
de bypassear. La descripción real implica que scripts de migración,
Django admin, o fixtures mal construidos pueden violar SoD sin
que el sistema lo detecte en tiempo de escritura.

### Desviación 4 — Modelo `UserGroup` no existe

El signal referenciaba `sender=UserGroup` y accedía a `instance.user`
e `instance.group`. No existe ningún modelo llamado `UserGroup` en
la app `access`. Los modelos relacionados son `UserAccessGroup` (asignación
de grupos al usuario) y `UserFunctionAssignment` (asignación directa
de funciones). El signal también usaba `SoDRule.find_conflict(instance.user, instance.group)` — pero el método `find_conflict` real en `SeparationRule` tiene
la firma `find_conflict(self, function_codes: set[str])`, no `(user, group)`.

### Desviación 5 — Catálogo SOD-003: `manage_sod` no existe

La tabla de funciones del catálogo listaba `manage_sod` como función
del Grupo A de SOD-003 "access_audit_separation". El nombre canónico
de producción es `manage_separation_rules` (función ACC-005 en
`FunctionCatalog.MANAGE_SEPARATION_RULES`). `manage_sod` nunca existió
como codename en ninguna versión del sistema.

----

## Cambios aplicados

### `cnst-030-reglas-de-separacion-de-funciones-sod.rst` — v3.0.0

**Metadata:** `:version: 3.0.0`, `:ultimo_cambio: 2026-05-13`

**§2.1 "Descripcion Detallada":**
```rst
# Antes
- Modelo ``SoDRule`` con campos ``group_a``, ``group_b``, ``rationale``.
- Validacion en signal ``pre_save`` de ``UserGroup``

# Después
- Modelo ``SeparationRule`` con campos ``functions_set_a``, ``functions_set_b``,
  ``description``, ``state`` (ENABLED/DISABLED). db_table = 'access_separation_rule'.
- Validacion en ``DutySeparationValidator.validate(user, new_function_codes)``
  invocado desde ``FunctionAssignView`` y ``AGRAssignView`` (capa API).
```

**§2.1 Catálogo:** `(modelo v5.2.1)` → `(modelo v5.4.0)`

**§2.1 SOD-003 Grupo A:** `manage_sod` → `manage_separation_rules`

**§2.3 Tecnologias:**
```rst
# Antes
- Modelo SoDRule
- Signal pre_save de UserGroup

# Después
- Modelo ``SeparationRule`` (``apps.access.models``)
- ``DutySeparationValidator`` (``apps.access.function_assign_view``)
```

**§3.1 Modulos Afectados:**
```rst
# Antes
- Implementa SoDRule + signal de validacion

# Después
- Implementa ``SeparationRule`` + ``DutySeparationValidator``
```

**§5.1 Codigo de Referencia:** reemplazado completamente.

Antes — signal inexistente sobre `UserGroup`:
```python
def on_user_group_save(sender, instance, **kwargs):
    conflicting = SoDRule.find_conflict(instance.user, instance.group)
    if conflicting:
        raise ValidationError(f"SoD: conflict with {conflicting}")
```

Después — `DutySeparationValidator` real con nota arquitectónica:
```python
violations = DutySeparationValidator.validate(target_user, new_function_codes)
if violations:
    return Response({'sod_violations': violations}, status=400)
```

Con `.. note::` explicitando que el enforcement es en capa API (no DB)
y que las escrituras directas a BD no están cubiertas por este mecanismo.

**§7.2 Metodo de Verificacion:**
```rst
# Antes
- Herramienta: Test del signal + reporte SQL de violaciones existentes

# Después
- Herramienta: Tests de integracion en test_separation_rule_validate.py
  (endpoint POST /api/access/separation-rules/validate) + reporte SQL
  de violaciones existentes
```

**§9 Historial de Cambios:** entrada v3.0.0 añadida documentando las 5
correcciones y la nota arquitectónica.

----

## Nota sobre deuda arquitectónica residual (no corregida en FASE 5)

La corrección de FASE 5 documenta honestamente que el enforcement es
a nivel de API (no DB). Esto deja visible una brecha arquitectónica
que estaba oculta:

**Brecha identificada:** Las escrituras directas a la base de datos —
Django admin, scripts de seed, fixtures, ORM directo — pueden crear
asignaciones que violan SoD sin que el sistema lo detecte en tiempo
de escritura.

**No se corrige en FASE 5** porque resolver esta brecha requiere:
1. Un ADR formal que decida si se quiere enforcement al nivel de signal
   (garantía más fuerte, acoplamiento mayor) o se acepta la garantía
   de capa API con controles compensatorios.
2. Implementación en IACT-api si se decide agregar el signal.
3. Actualización de CNST-030 una vez tomada esa decisión.

Esto es trabajo de una iteración futura con su propio ADR. FASE 5
cumple su objetivo: el documento describe fielmente lo que existe, no
lo que alguna vez se planeó.

----

## Verificación

```
CRITERIO 1: Sin residuos activos de nombres incorrectos
  HISTORICO (ok): SoDRule → SeparationRule (changelog v3.0.0)
  HISTORICO (ok): group_a/group_b/rationale → (changelog v3.0.0)
  HISTORICO (ok): UserGroup → UserAccessGroup (changelog v3.0.0)
  HISTORICO (ok): Signal pre_save eliminado (changelog v3.0.0)
  HISTORICO (ok): modelo v5.2.1 → v5.4.0 (changelog v3.0.0)
  HISTORICO (ok): manage_sod → manage_separation_rules (changelog v3.0.0)
  [PASS] Sin residuos activos

CRITERIO 2: Nombres correctos (14 ocurrencias de SeparationRule/DutySeparationValidator/
            functions_set_a/manage_separation_rules)
  [PASS]

CRITERIO 3: Nota arquitectónica presente en §5.1
  "Nivel de enforcement — capa API (no DB)."
  "La validacion se realiza en la capa DRF, no mediante un signal Django."
  [PASS]

CRITERIO 4: :version: 3.0.0 | :ultimo_cambio: 2026-05-13
  [PASS]
```

----

## Commit recomendado

```
docs(normativa): STD-008 FASE 5 — CNST-030 v3.0.0 — alineacion con implementacion real

Cinco desviaciones corregidas:

1. SoDRule → SeparationRule (la clase nunca existio como SoDRule)
2. group_a/group_b/rationale → functions_set_a/functions_set_b/description
3. Signal pre_save sobre UserGroup eliminado — mecanismo real:
   DutySeparationValidator en FunctionAssignView + AGRAssignView (capa DRF)
4. UserGroup eliminado — no existe; enforcement no es via signal de modelo
5. manage_sod → manage_separation_rules (SOD-003 catalogo)

Nota arquitectonica añadida en §5.1:
  Enforcement a nivel de capa API, no de senhal Django.
  Escrituras directas a BD no cubiertas por DutySeparationValidator.

§7.2: Test del signal → test_separation_rule_validate.py
Catalogo: modelo v5.2.1 → v5.4.0

Deuda arquitectonica residual documentada (no corregida — requiere ADR):
  Brecha entre garantia de enforcement documentada (DB-level signal)
  y garantia real (API-layer validation).
```
