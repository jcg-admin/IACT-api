# Hallazgos — Merge STD-008 §3.3/§3.5 → develop

**Artefacto:** HALLAZGOS-MERGE-STD008-20260513
**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Commit merge IACT-api:** `9f41e85` (develop)
**Estado:** Cerrado — 27/27 verificaciones PASS

----

## Resumen ejecutivo

El merge de `refactor/std008-sod-naming` → `develop` (IACT-api) se ejecutó
sin conflictos automáticos (`git merge-tree` retornó 0). IACT-ui no requirió
merge: el trabajo STD-008 FASE 3 (`885290f`) se commitió directamente sobre
la única rama local del repositorio.

| Repositorio | Acción | Commit | Estado |
|---|---|---|---|
| IACT-api | `merge --no-ff` | `9f41e85` | Completado |
| IACT-ui | Sin merge necesario | `885290f` ya activo | Completado |
| IACT-docs | Pendiente commit manual | (H-M-001) | Pendiente |

----

## Hallazgo H-M-001 — IACT-docs no tiene repositorio git en la referencia

**Tipo:** Infraestructura
**Impacto:** Los cambios de FASES 4 y 5 (CNST-033 v2.0.0, CNST-030 v3.0.0,
modelo-rbac-iact.rst) están aplicados en los archivos RST pero sin commit.

**Acción requerida** (en el working directory real del proyecto IACT-docs):
```bash
git add source/normativa/restricciones/cnst-033-vocabulario-unificado-rbac.rst
git add source/normativa/restricciones/cnst-030-reglas-de-separacion-de-funciones-sod.rst
git add source/arquitectura-tecnica/rbac/modelo-rbac-iact.rst
git add source/normativa/gobernanza/adr-gob-009-rbac-modelo-conceptual.rst
git commit -m "docs(normativa): STD-008 FASES 4-5 — CNST-033 v2.0.0 + CNST-030 v3.0.0 + modelo v5.4.0"
```

----

## Hallazgo H-M-002 — IACT-ui ya tenía el STD-008 integrado (sin merge)

**Tipo:** Arquitectura de ramas
**Descripción:** IACT-ui (`/tmp/references/IACT-ui`) no tiene una rama
`develop` local. Todo el trabajo TDD y el STD-008 FASE 3 viven en la misma
rama `claude/project-analysis-N9IkV`. El commit `885290f` (STD-008 FASE 3)
está directamente encima del trabajo TDD de FASE 2. No existe divergencia
de ramas a resolver.

**Verificación realizada:**

```
catalog.js post-885290f:
  MANAGE_SEPARATION_RULES: 'access:view_separation_rules'  ✓
  CREATE_SEPARATION_RULE:  'adm:create_separation_rule'    ✓
  UPDATE_SEPARATION_RULE:  'access:update_separation_rule' ✓
  DISABLE_SEPARATION_RULE: 'access:disable_separation_rule'✓
```

No hay acción requerida para IACT-ui.

----

## Hallazgo H-M-003 — `validate-sod` legacy endpoint sin consumidor

**Tipo:** Deuda técnica conocida (pre-existente en STD-008)
**Descripción:** Post-merge, el endpoint `POST /api/access/validate-sod`
sigue registrado en `urls.py` y respondido por `SeparationRuleValidateLegacyView`
(que delega a `SeparationRuleValidateView`). El endpoint fue creado en FASE 0
como punto de integración con `accessService.js` de IACT-ui.

Post-STD-008, IACT-ui ya no llama a `validate-sod`. El endpoint canónico
es `POST /api/access/separation-rules/validate`. `SeparationRuleValidateLegacyView`
está excluida del schema OpenAPI (`@extend_schema(exclude=True)`) para evitar
colisión de `operationId`.

**Acción:** Candidato para eliminación en un ciclo de limpieza posterior
a FASE 3 TDD. No bloquea ninguna FASE. Registrado como DT-ROUTING-005.

----

## Hallazgo H-M-004 — `create_sod_rules.py` renombrado correctamente por el merge

**Tipo:** Observación positiva
**Descripción:** Git rastreó el rename de
`create_sod_rules.py` → `create_separation_rules.py` correctamente
durante el merge (aparece como `rename` en el stat del commit, no como
delete+create). El comando `create_sod_rules` ya no existe; el nuevo
comando `create_separation_rules` está disponible y funcional.

----

## Hallazgo H-M-005 — `related_name` migrado sin cambio de esquema de BD

**Tipo:** Técnico — validación de migración
**Descripción:** La migración `0008_std008_fase2_related_names` aplica
`AlterField` a `functions_set_a` y `functions_set_b` de `SeparationRule`
para cambiar los `related_name` de `sod_rules_as_set_a/b` a
`separation_rules_as_set_a/b`. Como documenta el docstring de la migración:
los `related_name` son accessors Python del ORM y no modifican las tablas
intermedias de BD (`access_separation_rule_functions_set_a`,
`access_separation_rule_functions_set_b`). El `AlterField` no emite
ningún SQL de ALTER TABLE — solo actualiza el estado interno de Django.

**Verificación:**
```python
fn = Function.objects.first()
hasattr(fn, 'separation_rules_as_set_a')  → True  [PASS]
hasattr(fn, 'sod_rules_as_set_a')         → False [PASS]
```

----

## Cambios integrados por el merge (28 archivos)

### Eliminados

| Archivo | Razón |
|---|---|
| `apps/access/sod_rule_view.py` | Renombrado a `separation_rule_view.py` |
| `tests/unit/access/test_separation_rule_viewset.py` | Reemplazado por `test_separation_rule_validate.py` |

### Creados

| Archivo | Contenido |
|---|---|
| `apps/access/separation_rule_view.py` | UC_ACC_05 con nomenclatura canónica |
| `apps/access/migrations/0008_std008_fase2_related_names.py` | AlterField related_names |
| `tests/unit/access/test_separation_rule_validate.py` | 8 tests endpoint canónico |
| `docs/revision/PLAN-IMPL-STD008-SOD-FASES-20260513.md` | Plan original STD-008 |
| `docs/revision/HALLAZGOS-FASE1..4-STD008-SOD-20260513.md` | Hallazgos por fase |
| `docs/revision/ANALISIS-*.md` | Documentos de análisis STD-008 |

### Modificados (selección)

| Archivo | Cambio principal |
|---|---|
| `apps/access/urls.py` | `sod-rules/` → `separation-rules/`, router limpiado |
| `apps/access/views.py` | `SeparationRuleViewSet` eliminado, `SeparationRuleValidateLegacyView` añadida |
| `apps/access/models.py` | `related_name sod_rules_as_*` → `separation_rules_as_*` |
| `apps/audit/models.py` | `SOD_RULE_*` → `SEPARATION_RULE_*` en `VALID_EVENT_TYPES` |
| `apps/access/function_assign_view.py` | `has_a/b` → `user_has_set_a/b`, `codes_a/b` → `codes_set_a/b` |
| `apps/access/serializers/separation_rule_serializers.py` | `SeparationRuleCheckSerializer` eliminado |
| `tests/test_data/access_test_data.py` | `SeparationRuleTestData` actualizada para v5.4.0 |
| `tests/unit/access/test_separation_rule.py` | Reescrito para modelo v5.4.0 |
| `apps/reports/urls.py` | `menu-redirigidos/` → `menu-redirected/`, `menu-centro/` → `menu-center/` |
| `tests/integration/pipeline/test_ivr_endpoints.py` | 12 referencias + 2 clases + 1 método |

----

## Verificación funcional post-merge

27 verificaciones ejecutadas. Resultado: 27/27 PASS.

| Grupo | Verificaciones | Resultado |
|---|---|---|
| URLs canónicas nuevas (`separation-rule-*`) | 3 | PASS |
| URLs legacy eliminadas (`sod-rule-*`) | 2 | PASS |
| URLs IVR en inglés | 2 | PASS |
| URLs IVR en español eliminadas | 2 | PASS |
| `VALID_EVENT_TYPES` en audit | 4 | PASS |
| `related_name` correctos | 2 | PASS |
| `SeparationRuleTestData` | 1 | PASS |
| `DutySeparationValidator` | 1 | PASS |
| drf-spectacular — colisiones | 2 | PASS |
| drf-spectacular — schema paths | 3 | PASS |
| drf-spectacular — 6 operation_ids | 1 | PASS |
| `create_separation_rules` command | 1 | PASS |
| migración 0008 aplicada | 1 | PASS |
| **Total** | **27** | **27/27 PASS** |

### Warnings drf-spectacular pre-existentes (no introducidos por el merge)

Los siguientes 4 warnings existían antes del merge y permanecen:

```
operationId "access_access_groups_retrieve" → colisión (DT-ROUTING-001)
operationId "auth_change_password_create" → colisión (DT-ROUTING-002)
operationId "users_partial_update" → colisión (DT-ROUTING-003)
operationId "users_destroy" → colisión (DT-ROUTING-003)
```

----

## Deuda técnica post-merge

### DT-ROUTING-005 — `validate-sod` legacy sin consumidor activo

`POST /api/access/validate-sod` → `SeparationRuleValidateLegacyView`.
Excluida del schema. Ningún cliente la llama post-STD-008. Candidata para
eliminación en limpieza de routing posterior a FASE 3 TDD.

### H-M-001 (activo) — Commits IACT-docs pendientes

Los cambios de CNST-030 v3.0.0 y CNST-033 v2.0.0 están en los archivos
RST pero no commiteados. Ver H-M-001 para el comando exacto.

----

## Estado final post-merge

```
develop (IACT-api):
  commit 9f41e85 — merge STD-008 completo
  27/27 verificaciones PASS
  drf-spectacular: 4 colisiones pre-existentes, 0 nuevas

IACT-ui (claude/project-analysis-N9IkV):
  commit 885290f — STD-008 FASE 3 ya integrado
  catalog.js: 4 codenames correctos

IACT-docs:
  Archivos RST actualizados, commit pendiente (H-M-001)

Próximo paso: iniciar FASE 3 TDD desde develop post-merge
  Referencia: PLAN-IMPLEMENTACION-TDD-v4-20260513.md § FASE 3
```
