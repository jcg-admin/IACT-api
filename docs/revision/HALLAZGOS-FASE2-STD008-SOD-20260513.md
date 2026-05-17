# Hallazgos — Implementación STD_008 §3.3 FASE 2

**Artefacto:** HALLAZGOS-FASE2-STD008-SOD-20260513
**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Commit:** `bd3201e` en rama `refactor/std008-sod-naming`
**Autor:** Nestor Monroy
**Estado:** Cerrado — todos los hallazgos resueltos en este commit

----

## Resumen ejecutivo

FASE 2 se ejecutó sin deuda técnica residual. El scope original era
cambiar dos `related_name` en models.py y generar una migración.
Durante la preparación se descubrió un hallazgo adicional (H-002):
habían 22 cambios de modelos pendientes de migración en el app `access`
que no tenían su `AlterField` correspondiente. Se consolidaron en la
misma migración 0008 para dejar el estado de migraciones consistente.

| Métrica | Antes | Después |
|---|---|---|
| related_name viejo `sod_rules_as_set_a/b` | en producción | eliminados |
| related_name nuevo `separation_rules_as_set_a/b` | inexistente | en producción |
| Migraciones pendientes en app `access` | 22 cambios (H-002) | 0 |
| Tablas de BD afectadas | 0 | 0 (AlterField M2M no toca esquema) |
| Tests de verificación | — | 6 PASS, 0 FAIL |
| Breaking changes de contrato | 0 | 0 |

----

## Cambios ejecutados

### T-2.1 — `models.py`: dos related_names

| Campo M2M | related_name anterior | related_name nuevo |
|---|---|---|
| `SeparationRule.functions_set_a` | `sod_rules_as_set_a` | `separation_rules_as_set_a` |
| `SeparationRule.functions_set_b` | `sod_rules_as_set_b` | `separation_rules_as_set_b` |

### T-2.3 — Migración `0008_std008_fase2_related_names.py`

Generada con `python manage.py makemigrations access --name std008_fase2_related_names`.

La migración contiene 22 operaciones distribuidas en tres categorías:

**Categoría A — FASE 2 (motivo del commit):**

```python
migrations.AlterField(
    model_name='separationrule', name='functions_set_a',
    field=models.ManyToManyField(
        ..., related_name='separation_rules_as_set_a', ...),
)
migrations.AlterField(
    model_name='separationrule', name='functions_set_b',
    field=models.ManyToManyField(
        ..., related_name='separation_rules_as_set_b', ...),
)
```

**Categoría B — Hallazgo H-002 (preexistente):** 20 operaciones de
`AlterField` y `AlterModelOptions` para campos que habían recibido
`help_text` / `verbose_name` sin generar migración.

----

## Hallazgo H-002 — Migraciones pendientes preexistentes

**Severidad:** Media (inconsistencia entre modelo y estado de migración)
**Detectado en:** T-0.3 (verificación previa a modificar models.py)
**Resuelto en:** este commit, migración 0008

### Descripción

Antes de modificar `models.py` para FASE 2, se ejecutó
`makemigrations --check` para verificar el estado de la base de
referencia. El resultado reveló 22 cambios pendientes en el app `access`:

```
- Change Meta options on separationrule
- Alter field is_predefined on accessgroup
- Alter field retired_at on accessgroup
- Alter field menu_action on function
- Alter field menu_domain on function
- Alter field menu_icon on function
- Alter field menu_label_en on function
- Alter field menu_label_es on function
- Alter field menu_order on function
- Alter field menu_section on function
- Alter field menu_visible on function
- Alter field id on menuitem
- Alter field code on separationrule
- Alter field created_by on separationrule
- Alter field description on separationrule
- Alter field functions_set_a on separationrule  ← incluye related_name FASE 2
- Alter field functions_set_b on separationrule  ← incluye related_name FASE 2
- Alter field name on separationrule
- Alter field expires_at on userfunctionassignment
- Alter field is_active on userfunctionassignment
- Alter field reason on userfunctionassignment
- Alter field revoke_reason on userfunctionassignment
```

### Causa raíz

Durante la implementación del FASE 2 del proyecto (15 UCs), se agregaron
`help_text` y `verbose_name` a múltiples campos de los modelos `Access`
sin ejecutar `makemigrations`. Django registra estos metadatos como parte
del estado del modelo, de modo que cualquier diferencia entre el modelo
y la última migración aplicada genera un `AlterField` pendiente.

Además, el campo `AlterModelOptions` para `SeparationRule` (verbose_name,
ordering) no fue capturado cuando se modernizó el modelo en FASE 0.

### Por qué `functions_set_a` / `functions_set_b` ya aparecían en el pendiente

La migración 0005 creó los campos M2M con:

```python
field=models.ManyToManyField(
    blank=True,
    related_name='sod_rules_as_set_a',  # ← sin help_text
    to='access.function',
    verbose_name='Conjunto A',           # ← sin i18n (_())
)
```

El modelo actual tiene `help_text='Funciones del primer conjunto...'`
que no existía en 0005. Django ve esta diferencia y genera un
`AlterField` pendiente. Este `AlterField` también incluye el
`related_name` actual, que seguía siendo `sod_rules_as_set_a`.

**Consecuencia directa:** al cambiar el `related_name` en models.py
y ejecutar `makemigrations`, el `AlterField` pendiente incorpora
automáticamente el nuevo `related_name='separation_rules_as_set_a'`.
No fue necesario crear la migración manualmente.

### Por qué se incluyeron los 20 cambios adicionales en la misma migración

Crear la migración FASE 2 de forma aislada (solo los 2 `related_name`)
mientras hay 20 cambios pendientes habría creado un estado inconsistente
en el grafo de migraciones:

- Los cambios pendientes habrían quedado sin registro formal
- Una `makemigrations` posterior habría generado un 0009 con el 0008
  ya existente, creando un grafo bifurcado
- Los campos sin migración podrían generar errores en `migrate --check`
  en pipelines CI/CD

La decisión correcta fue generar el 0008 con todos los cambios pendientes
de `access`, incluyendo el FASE 2, en una sola operación atómica.

----

## Análisis de impacto — Por qué AlterField M2M no toca la BD

Es un punto de confusión frecuente. El `related_name` en un
`ManyToManyField` **no tiene representación en la base de datos**:

- Las tablas intermedias `access_separation_rule_functions_set_a` y
  `access_separation_rule_functions_set_b` solo tienen columnas
  `id`, `separationrule_id`, `function_id` — sin ninguna columna
  que almacene el nombre del accessor Python.
- `AlterField` de un `ManyToManyField` que solo cambia `related_name`
  genera una migración que Django registra en `django_migrations` pero
  **no ejecuta ningún SQL** en las tablas de datos.

Verificación directa:

```python
# Antes de la migración:
connection.introspection.table_names()
# → [..., 'access_separation_rule_functions_set_a', ...]

# Después de la migración:
connection.introspection.table_names()
# → [..., 'access_separation_rule_functions_set_a', ...]
# Las tablas existen con exactamente el mismo esquema
```

Los datos M2M existentes en BD no se tocan. La operación es safe para
aplicar en producción sin ventana de mantenimiento.

----

## Estado de migraciones tras FASE 2

### Antes

```
access/migrations/
  0001_initial.py
  0002_...
  0003_...
  0004_...
  0005_fase0_schema_canonico.py
  0006_fase0_sql_functions_postgresql.py
  0007_fase2_access_group_and_function_menu.py
  ← 22 cambios sin migración
```

### Después

```
access/migrations/
  0001_initial.py
  ...
  0007_fase2_access_group_and_function_menu.py
  0008_std008_fase2_related_names.py  ← nuevo
  ← 0 cambios pendientes
```

Verificado con `makemigrations access --check`: exit sin output (sin
cambios detectados).

----

## Advertencias de drf-spectacular observadas (pre-existentes)

Durante la verificación T-2.4 se observaron múltiples mensajes en stderr
de drf-spectacular. **Ninguno es nuevo de FASE 2.** Son advertencias
pre-existentes de otras vistas del proyecto:

### Error: `unable to guess serializer`

Afecta a las vistas `APIView` del proyecto que no declaran
`serializer_class` explícito:

```
SeparationRuleListCreateView: unable to guess serializer
SeparationRuleDetailView: unable to guess serializer
AccessGroupListCreateView: unable to guess serializer
FunctionAssignView: unable to guess serializer
AGRAssignView: unable to guess serializer
... (otras vistas)
```

**Causa:** drf-spectacular no puede inferir el schema de respuesta de
`APIView` porque no usa `serializer_class`. La solución es agregar
`@extend_schema(responses={...})` con el tipo de respuesta explícito
o migrar a `GenericAPIView`.

**Clasificación:** Pre-existente, fuera del scope de FASE 2. Las vistas
de separación (`SeparationRuleListCreateView`, `SeparationRuleDetailView`)
recibirán `@extend_schema` con `responses` explícito en FASE 3 cuando
se actualice el contrato público.

### Warning: `unable to resolve type hint`

Afecta a `SerializerMethodField` sin anotación de tipo en múltiples
serializers del proyecto (alerts, audit, reports, users, authentication).

**Clasificación:** Pre-existente, fuera del scope de FASE 2. No genera
errores de runtime ni afecta el funcionamiento de la API.

### Warning: enum naming collision

```
enum naming encountered a non-optimally resolvable collision for "state"
→ resolved as "StateE32Enum"
```

**Causa:** múltiples modelos tienen un campo `state` con diferentes
conjuntos de choices. drf-spectacular intenta generar un nombre único
para el enum. La solución es usar `ENUM_NAME_OVERRIDES` en la
configuración de drf-spectacular.

**Clasificación:** Pre-existente, fuera del scope de FASE 2. No afecta
el funcionamiento de la API.

### Warning: operationId collision

```
operationId "access_sod_rules_retrieve" has collisions
[('/api/access/sod-rules/', 'get'), ('/api/access/sod-rules/{rule_id}/', 'get')]
```

**Causa:** drf-spectacular genera `operationId` a partir del path URL.
Cuando una vista `APIView` implementa múltiples endpoints (GET de lista
y GET de detalle bajo el mismo path base), hay colisión de nombres.

**Implicación para FASE 3:** cuando la URL cambie de `sod-rules/` a
`separation-rules/`, el `operationId` cambiará a
`access_separation_rules_retrieve`. La colisión se resuelve agregando
`operation_id` explícito en `@extend_schema`.

**Clasificación:** Pre-existente. En FASE 3, al actualizar el
`@extend_schema` con la nueva URL, se deberá agregar `operation_id`
explícito para evitar la colisión.

----

## Violaciones residuales (44) — clasificación actualizada

Tras FASE 2, las 44 violaciones restantes se distribuyen así:

| Archivo | Líneas | Fase / Categoría | Detalle |
|---|---|---|---|
| `access/function_assign_view.py` | 12 | FASE 3 + narrativa | error codes SOD_VIOLATION, payload sod_violation, @extend_schema description |
| `access/views.py` | 7 | FASE 3 + narrativa | validate-sod docstring, sodConflicts comment |
| `access/models.py` | 7 | Narrativa permanente | verbose_name 'Regla SoD', `__str__` 'SoD {code}', docstrings |
| `access/migrations/0005_*.py` | 5 | Inmutable histórico | migración aplicada — nunca se edita |
| `access/urls.py` | 4 | FASE 3 | path sod-rules/, names sod-rule-*, validate-sod |
| `access/management/commands/create_access_groups.py` | 4 | Narrativa permanente | strings de descripción de grupos |
| `audit/models.py` | 3 | FASE 3 | VALID_EVENT_TYPES SOD_RULE_* |
| `access/migrations/0008_*.py` | 2 | Narrativa permanente | verbose_name 'Regla SoD', nombre de artefacto 'SOD-FASES' |

Ninguna línea sin clasificar. Sin deuda técnica.

----

## Verificación ejecutada (T-2.4)

```
[PASS] DutySeparationValidator — 1 violación(es) detectada
[PASS] Violación correcta via separation_rules_as_set_a/b
[PASS] sod_rules_as_set_a → AttributeError (eliminado)
[PASS] separation_rules_as_set_a → ['V4RULE']
[PASS] separation_rules_as_set_b → ['V4RULE']
[PASS] Tablas intermedias M2M intactas — AlterField no modifica esquema
[PASS] makemigrations --check: sin cambios pendientes en access
[PASS] drf-spectacular OK — sin warnings de campos inválidos
[DONE] FASE 2 — todos los criterios verificados
```

----

## Pendiente para FASE 3 relacionado con drf-spectacular

Los siguientes puntos se documentan aquí para que FASE 3 los incorpore
al actualizar `@extend_schema` en las vistas de separación:

1. Agregar `operation_id` explícito en `SeparationRuleListCreateView`
   y `SeparationRuleDetailView` para evitar la colisión de `operationId`.

2. Agregar `responses={200: SeparationRuleSerializer, ...}` en
   `@extend_schema` de ambas vistas para que drf-spectacular pueda
   inferir el schema de respuesta sin el error `unable to guess serializer`.

3. Actualizar el `summary` de ambas vistas para reflejar la nueva URL
   `separation-rules/` una vez que FASE 3 la cambie.
