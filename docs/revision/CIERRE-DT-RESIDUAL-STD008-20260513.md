# Cierre de Ciclo — Remediación Deuda Técnica STD-008 §3.3/§3.5

**Artefacto:** CIERRE-DT-RESIDUAL-STD008-20260513
**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Autor:** Nestor Monroy
**Estado:** CERRADO — todos los criterios de aceptación globales PASS

----

## Origen del ciclo

**Documento de análisis:** `ANALISIS-DT-RESIDUAL-STD008-20260513.md`
**Documento de plan:** `PLAN-IMPL-DT-RESIDUAL-20260513.md`

El ciclo de remediación nació del análisis de tres ítems de deuda
técnica detectados en el commit `cb51b2e` (STD_008 §3.3 FASE 5):

- `DT-STD008-001` — CNST-033 desactualizado (nombre de clase incorrecto)
- `DT-STD008-002` — Codenames `sod` en `catalog.js` (IACT-ui)
- `DT-STD008-003` — `SeparationRuleViewSet` deprecated + test suite rota (CI BLOCKER)

El análisis previo a la implementación identificó dos ítems adicionales:
- `DT-URL-001` — Endpoints IVR en español (`menu-redirigidos`, `menu-centro`)
- `DT-CC-001` — Variables locales que violan Clean Code (`has_a`/`has_b`, `fn_a`/`fn_b`)

Y durante FASE 4 se identificó un ítem que escaló a una fase propia:
- `DT-CNST030-001` — CNST-030 describía mecanismo de enforcement inexistente

----

## Fases ejecutadas

| Fase | Descripción | Repositorio | Commit | Estado |
|---|---|---|---|---|
| FASE 1 | CI blocker + código muerto + naming | IACT-api | `c9cfae7` | COMPLETADA |
| FASE 2 | Endpoints IVR español → inglés | IACT-api | `4f19034` | COMPLETADA |
| FASE 3 | Codenames `sod` en catalog.js | IACT-ui | `885290f` | COMPLETADA |
| FASE 4 | CNST-033 v2.0.0 + modelo-rbac-iact.rst | IACT-docs | pendiente commit | COMPLETADA |
| FASE 5 | CNST-030 v3.0.0 — alineación con implementación | IACT-docs | pendiente commit | COMPLETADA |

**Nota commits IACT-docs:** El directorio de referencia de IACT-docs
no tiene repositorio git inicializado. Los cambios están aplicados en
los archivos. Los commits deben ejecutarse desde el working directory
real del proyecto IACT-docs.

----

## Hallazgos por fase — resumen

| Hallazgo | Fase | Tipo | Descripción |
|---|---|---|---|
| H-F1-001 | FASE 1 | Alcance ampliado | `test_separation_rule.py` también usaba campos v5.2.1 — no detectado en análisis inicial |
| H-F2-001 | FASE 2 | Sin hallazgos adicionales | Alcance exacto al plan |
| H-F3-001 | FASE 3 | Sin hallazgos adicionales | Alcance exacto al plan |
| H-F4-001 | FASE 4 | Infraestructura | IACT-docs sin git en referencia local — commit manual requerido |
| H-F4-002 | FASE 4 | Alcance ampliado | `adr-gob-009` también referenciaba `FunctionSeparationRule` — detectado en búsqueda transversal |
| H-F5-001 | FASE 5 | Análisis | CNST-030 describía signal `pre_save` sobre `UserGroup` — mecanismo nunca implementado |
| H-F5-002 | FASE 5 | Análisis | `SoDRule.find_conflict(user, group)` — firma incompatible con implementación real |
| H-F5-003 | FASE 5 | Análisis | `manage_sod` en catálogo SOD-003 — función inexistente |
| H-F5-004 | FASE 5 | Arquitectura | Enforcement SoD a nivel API (no DB) — brecha documentada en §5.1 de CNST-030 |

----

## Criterios de aceptación globales — resultados

Verificación ejecutada el 2026-05-13 contra los repositorios de referencia.

### C-01 — Sin código muerto de ViewSet/Serializer en `apps/`

```
grep -rn "class SeparationRuleViewSet|class SeparationRuleCheckSerializer|
          from.*import.*SeparationRuleViewSet|from.*import.*SeparationRuleCheckSerializer"
  IACT-api/callcentersite/apps/
```

**Resultado:** [PASS] 0 resultados de código activo

Nota: existen 2 referencias en comentarios y docstrings que documentan
la eliminación del ViewSet. Son referencias históricas intencionales,
no código activo.

---

### C-02 — Sin campos v5.2.1 en `SeparationRuleTestData`

```
function_a | function_b | status='active' | justification
  en código activo de SeparationRuleTestData
  (IACT-api/callcentersite/tests/test_data/access_test_data.py)
```

**Resultado:** [PASS] 0 campos v5.2.1 en código activo de la factory

Nota: la línea 162 del archivo menciona `function_a, function_b, justification`
dentro del docstring de la factory que documenta por qué fueron eliminados.
No es código activo.

---

### C-03 — Sin endpoints en español en `apps/`

```
grep -rn "menu-redirigidos|menu-centro"
  IACT-api/callcentersite/apps/
```

**Resultado:** [PASS] 0 resultados

---

### C-04 — Sin codenames `sod` en `IACT-ui/src/`

```
grep -rn "view_sod|create_sod|update_sod|disable_sod"
  IACT-ui/src/ (*.js, *.jsx, *.ts, *.tsx)
```

**Resultado:** [PASS] 0 resultados

---

### C-05 — Sin nombres incorrectos en `IACT-docs/source/`

```
SeparationOfDutiesRule  — fuera de historial de cambios
FunctionSeparationRule  — fuera de contexto histórico documentado
function_separation_rules — como tabla activa (no en SQL histórico)
```

**Resultado:** [PASS] 0 ocurrencias activas

Nota sobre F4-T4 en la verificación automatizada: la línea 2085 de
`modelo-rbac-iact.rst` contiene `FunctionSeparationRuleDetail` como
continuación de la oración del `Hallazgo F0-H-003:` en la línea 2084.
El script filtró la línea con `Hallazgo` pero no su continuación.
El contexto completo confirma que es un docstring histórico dentro de
la clase `SeparationRule`. No es una violación del criterio.

---

### C-06 — Verificación funcional

Suite de 41 verificaciones ejecutadas contra el entorno de testing:

| Grupo | Tests | PASS | FAIL |
|---|---|---|---|
| FASE 1 — CI blocker + naming | 9 | 9 | 0 |
| FASE 2 — URLs IVR | 4 | 4 | 0 |
| FASE 3 — catalog.js | 9 | 9 | 0 |
| FASE 4 — CNST-033 + modelo RST | 5 | 5 | 0 |
| FASE 5 — CNST-030 | 5 | 5 | 0 |
| drf-spectacular | 9 | 9 | 0 |
| **Total** | **41** | **41** | **0** |

**Resultado:** [PASS] 41/41

---

### C-07 — drf-spectacular: criterios específicos de STD-008

| Criterio | Resultado |
|---|---|
| Sin colisiones de `separation_rule` | PASS |
| Sin Field warnings nuevos introducidos por las 5 fases | PASS |
| `/api/access/separation-rules/` presente con 6 operation_ids canónicos | PASS |
| `/api/access/separation-rules/validate` presente | PASS |
| `/api/reports/ivr/menu-redirected/` presente | PASS |
| `/api/reports/ivr/menu-center/` presente | PASS |
| `/api/reports/ivr/menu-redirigidos/` ausente | PASS |
| `/api/reports/ivr/menu-centro/` ausente | PASS |

**Nota sobre warnings pre-existentes:** drf-spectacular reporta 4 colisiones
de `operationId` que no forman parte del scope de STD-008:
- `access_access_groups_retrieve` — colisión entre `access-groups/` (FASE 2 TDD)
  y `access-groups/{agr_id}/` (legacy ViewSet)
- `auth_change_password_create` — colisión entre `change-password/` y `change_password/`
- `users_partial_update` — colisión entre `users/{id}/` y `users/{user_id}/`
- `users_destroy` — ídem

Estas 4 colisiones son pre-existentes al ciclo de remediación STD-008.
No fueron introducidas por ninguna de las 5 fases. Son candidatas para
un ciclo de remediación propio bajo el plan TDD v3 (FASE 3 del plan TDD).

----

## Archivos modificados por fase

### IACT-api — rama `refactor/std008-sod-naming`

**FASE 1 — commit `c9cfae7` (9 archivos):**
- `tests/test_data/access_test_data.py` — SeparationRuleTestData reescrita
- `tests/unit/access/test_separation_rule.py` — reescrito para modelo v5.4.0
- `tests/unit/access/test_separation_rule_validate.py` — creado (8 tests)
- `tests/unit/access/test_separation_rule_viewset.py` — **eliminado**
- `apps/access/views.py` — SeparationRuleViewSet + 2 @extend_schema eliminados
- `apps/access/serializers/separation_rule_serializers.py` — SeparationRuleCheckSerializer eliminado
- `apps/access/serializers/__init__.py` — export limpiado
- `apps/access/models.py` — has_a/b → user_has_set_a/b; fn_a/b → conflict_from_set_a/b
- `apps/access/function_assign_view.py` — has_a/b → user_has_set_a/b; codes_a/b → codes_set_a/b

**FASE 2 — commit `4f19034` (3 archivos):**
- `apps/reports/urls.py` — 2 paths y 2 names renombrados
- `apps/reports/ivr_views.py` — 2 docstrings de clase actualizados
- `tests/integration/pipeline/test_ivr_endpoints.py` — 12 referencias + 2 clases + 1 método

### IACT-ui — rama `claude/project-analysis-N9IkV`

**FASE 3 — commit `885290f` (5 archivos):**
- `src/permissions/catalog.js` — 4 valores de constante
- `src/permissions/__tests__/catalog.test.js` — 2 expects
- `src/router/__tests__/AppRouter.test.jsx` — 2 referencias
- `src/mocks/mockInterceptor.js` — 4 campos codename
- `src/pages/admin/__tests__/FunctionCatalogPage.test.jsx` — 1 argumento

### IACT-docs — commits pendientes en repo real

**FASE 4 (3 archivos):**
- `source/normativa/restricciones/cnst-033-vocabulario-unificado-rbac.rst` — v2.0.0
- `source/arquitectura-tecnica/rbac/modelo-rbac-iact.rst` — 9 ubicaciones
- `source/normativa/gobernanza/adr-gob-009-rbac-modelo-conceptual.rst` — 1 línea

**FASE 5 (1 archivo):**
- `source/normativa/restricciones/cnst-030-reglas-de-separacion-de-funciones-sod.rst` — v3.0.0

----

## Deuda técnica residual documentada (no resuelta en este ciclo)

### DT-ENFORCEMENT-001 — Enforcement SoD a nivel API, no DB

**Detectada en:** FASE 5, H-F5-004
**Severidad:** Media
**Descripción:** `DutySeparationValidator` valida SoD en la capa DRF.
Las escrituras directas a BD (admin, scripts, ORM directo) no están
cubiertas. CNST-030 §5.1 documenta esta brecha explícitamente.
**Resolución requerida:** ADR que decida signal vs validador DRF +
implementación si se elige signal.

### DT-SPECTACULAR-001 — 4 colisiones pre-existentes en drf-spectacular

**Detectada en:** verificación de cierre
**Severidad:** Baja (no afectan funcionalidad, solo documentación OpenAPI)
**Colisiones:**
- `access_access_groups_retrieve`
- `auth_change_password_create`
- `users_partial_update` / `users_destroy`
**Resolución requerida:** consolidar rutas legacy vs FASE 2 TDD en
`access/urls.py` y `users/urls.py`. Candidato para FASE 3 del plan TDD.

### DT-IACT-DOCS-GIT-001 — IACT-docs sin git en referencia local

**Detectada en:** FASE 4, H-F4-001
**Severidad:** Operacional (no técnica)
**Descripción:** El directorio de referencia de IACT-docs no tiene
`.git`. Los commits de FASE 4 y FASE 5 deben ejecutarse manualmente.
**Acción pendiente:** ejecutar los dos commits en el working directory
real del proyecto IACT-docs (ver mensaje de commit recomendado en
HALLAZGOS-IMPL-FASE4 y HALLAZGOS-IMPL-FASE5).

----

## Versiones de documentos normativos post-ciclo

| Documento | Versión anterior | Versión actual | Fecha de cambio |
|---|---|---|---|
| CNST-030 | 2.0.0 | 3.0.0 | 2026-05-13 |
| CNST-033 | 1.0.0 | 2.0.0 | 2026-05-13 |
| modelo-rbac-iact.rst | sin control de versión | v5.4.0 documentado | 2026-05-13 |
| adr-gob-009 | sin versión explícita | actualizado | 2026-05-13 |

----

## Siguiente paso recomendado

Con el ciclo de remediación cerrado, el trabajo pendiente es la
continuación del plan TDD v3:

**FASE 3 del plan TDD** — 11 UCs ALTOS (RPT/ALR/PIP/LOG):

```
UC_RPT_02  Ver Métricas Tiempo Real   4d  (stub — CNST-003 sin SSE)
UC_RPT_03  Ver Reportes Históricos    4d  → req: UC_RPT_01 (done)
UC_RPT_04  Exportar Reporte           6d  → req: UC_RPT_01 (done)
UC_ALR_01  Configurar Umbrales        3d  → raíz
UC_ALR_02  Ver Alertas Activas        2d  → req: UC_ALR_01
UC_ALR_03  Reconocer Alerta           2d  → req: UC_ALR_02
UC_PIP_02  Consultar Errores ETL      2d  → req: UC_PIP_01 (done)
UC_PIP_03  Consultar Disponibilidad   2d  → req: UC_PIP_01 (done)
UC_PIP_04  Solicitar Reintento        3d  → req: UC_PIP_01, UC_PIP_02
UC_LOG_01  Ver Logs Aplicación        2d  → raíz
UC_LOG_02  Ver Logs ETL               2d  → req: UC_PIP_01 (done)
```

Raíces disponibles de inmediato: UC_ALR_01, UC_LOG_01, UC_RPT_02,
UC_RPT_03, UC_PIP_02, UC_PIP_03, UC_LOG_02.
