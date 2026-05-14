# Plan de Implementación TDD — IACT-api v4.0.0

**Versión:** 4.0.0
**Fecha:** 2026-05-13
**Reemplaza:** `PLAN-IMPLEMENTACION-TDD-v3-20260513220000.md` (deprecado)
**Metodología:** Red → Green → Refactor por CA
**Fuente:** IACT-docs `source/requisitos/` y `source/arquitectura-tecnica/`

----

## Por qué existe v4.0.0

El plan v3.0.0 fue escrito antes del ciclo de remediación de deuda técnica
STD-008 §3.3/§3.5. Ese ciclo produjo cinco fases de cambios que afectan
directamente el routing, los nombres de clase, los event types de auditoría,
las constantes de IACT-ui y la documentación normativa.

El plan v3 asumía que `sod-rules/` era el prefijo canónico de UC_ACC_05,
que `SoDRule*` era la nomenclatura vigente, y que `SeparationRuleViewSet`
seguía en el router. Ninguna de esas tres premisas es válida después
de STD-008.

### Cambios estructurales introducidos por STD-008

| Área | Antes (v3) | Después (v4) |
|---|---|---|
| Archivo UC_ACC_05 | `sod_rule_view.py` | `separation_rule_view.py` |
| Clases UC_ACC_05 | `SoDRuleListCreateView`, `SoDRuleDetailView` | `SeparationRuleListCreateView`, `SeparationRuleDetailView` |
| Serializers UC_ACC_05 | `SoDRuleCreateSerializer`, `SoDRulePatchSerializer` | `SeparationRuleCreateSerializer`, `SeparationRulePatchSerializer` |
| URL CRUD | `/api/access/sod-rules/` | `/api/access/separation-rules/` |
| URL validate | `/api/access/validate-sod` | `/api/access/separation-rules/validate` |
| Event types auditoría | `SOD_RULE_CREATED/UPDATED/DISABLED` | `SEPARATION_RULE_CREATED/UPDATED/DISABLED` |
| Error codes | `SOD_RULE_DUPLICATE`, `SOD_RULE_NOT_FOUND` | `SEPARATION_RULE_DUPLICATE`, `SEPARATION_RULE_NOT_FOUND` |
| Router | `SeparationRuleViewSet` registrado | `SeparationRuleViewSet` eliminado del router |
| Test eliminado | `test_separation_rule_viewset.py` | `test_separation_rule_validate.py` (8 tests) |
| Test reescrito | `test_separation_rule.py` (campos v5.2.1) | `test_separation_rule.py` (modelo v5.4.0) |
| Variables modelos | `has_a/has_b`, `fn_a/fn_b` | `user_has_set_a/b`, `conflict_from_set_a/b` |
| IVR endpoints | `menu-redirigidos`, `menu-centro` | `menu-redirected`, `menu-center` |
| Codenames IACT-ui | `view_sod`, `create_sod`, `update_sod`, `disable_sod` | `view_separation_rules`, `create_separation_rule`, `update_separation_rule`, `disable_separation_rule` |
| CNST-033 | v1.0.0 (`SeparationOfDutiesRule`) | v2.0.0 (`SeparationRule`) |
| CNST-030 | v2.0.0 (signal `pre_save`, `SoDRule`) | v3.0.0 (`DutySeparationValidator`, enforcement capa API) |

----

## Estado de las ramas — prerrequisito de FASE 3

**Situación actual:**

```
develop                        refactor/std008-sod-naming
    │                                    │
c07f666 (FASE 2 TDD)          4f19034 (STD-008 FASE 2 IACT-api)
73834ba (FASE 2 TDD)          c9cfae7 (STD-008 FASE 1)
    │                                    │
    └──────── base común ────────────────┘
              (cb51b2e)
```

```
IACT-ui:
    claude/project-analysis-N9IkV
    └── 885290f (STD-008 FASE 3 — codenames catalog.js)
```

**Acción requerida ANTES de iniciar FASE 3 TDD:**

```bash
# IACT-api
git checkout develop
git merge refactor/std008-sod-naming --no-ff \
  -m "merge(std008): FASES 1-2 remediación STD-008 §3.3/§3.5 → develop"

# IACT-ui
git checkout develop
git merge claude/project-analysis-N9IkV --no-ff \
  -m "merge(std008): FASE 3 remediación STD-008 §3.3 — codenames → develop"

# IACT-docs
# Los cambios de FASES 4-5 están aplicados en los archivos RST
# pero sin commit (H-F4-001). Commitear antes del merge:
git add source/normativa/restricciones/cnst-030-reglas-de-separacion-de-funciones-sod.rst
git add source/normativa/restricciones/cnst-033-vocabulario-unificado-rbac.rst
git add source/arquitectura-tecnica/rbac/modelo-rbac-iact.rst
git add source/normativa/gobernanza/adr-gob-009-rbac-modelo-conceptual.rst
git commit -m "docs(normativa): STD-008 FASES 4-5 — CNST-033 v2.0.0 + CNST-030 v3.0.0 + modelo v5.4.0"
```

**Verificación post-merge (IACT-api):**

```bash
python manage.py check --deploy
python -c "
from django.urls import reverse
print(reverse('access:separation-rule-list-create'))  # /api/access/separation-rules/
print(reverse('access:separation-rule-validate'))     # /api/access/separation-rules/validate
try:
    reverse('access:sod-rule-list-create')
    print('FAIL: sod-rule-list-create aún existe')
except:
    print('PASS: sod-rule-list-create eliminado')
"
```

----

## FASE 0 — Infraestructura transversal [COMPLETADA]

**Commits:** `270f8af` → `5f66da9` en `develop`
**Estado:** Sin cambios respecto al plan v3.

Completada: F0-T1 (schema canónico), F0-T2 (catálogo RBAC v5.4.0 —
61 funciones + 10 AGRs + 3 SoD), F0-T3 (5 funciones SQL PostgreSQL),
F0-T4 (InternalMailbox), F0-T5 (AuditEvent), F0-T6 (DB router).

----

## FASE 1 — 8 UCs CRÍTICOS [COMPLETADA]

**Commits:** `69e83e1` → `9f6bea6` en `develop`
**Estado:** Sin cambios respecto al plan v3.

Completada: UC_AUTH_01, UC_PERM_07, UC_USR_02, UC_ACC_03,
UC_PIP_01, UC_AUD_01, UC_AUTH_04, UC_RPT_01.

----

## FASE 2 — 15 UCs ALTOS AUTH/USR/ACC/PERM [COMPLETADA con correcciones]

**Commits:** `8969f71` → `c07f666` en `develop`
**Correcciones STD-008 pendientes de merge:** ver tabla de cambios arriba.

### Correcciones que aplica el merge de STD-008

**UC_ACC_05 — Gestionar Reglas de Separación:**

| Elemento | Estado post-FASE 2 TDD (develop) | Estado post-merge STD-008 |
|---|---|---|
| Archivo | `sod_rule_view.py` | `separation_rule_view.py` |
| Clases | `SoDRuleListCreateView`, `SoDRuleDetailView` | `SeparationRuleListCreateView`, `SeparationRuleDetailView` |
| URL | `/api/access/sod-rules/` | `/api/access/separation-rules/` |
| Event type crear | `SOD_RULE_CREATED` | `SEPARATION_RULE_CREATED` |
| Event type modificar | `SOD_RULE_UPDATED` | `SEPARATION_RULE_UPDATED` |
| Event type retirar | `SOD_RULE_DISABLED` | `SEPARATION_RULE_DISABLED` |
| Error code duplicado | `SOD_RULE_DUPLICATE` | `SEPARATION_RULE_DUPLICATE` |
| Error code no encontrado | `SOD_RULE_NOT_FOUND` | `SEPARATION_RULE_NOT_FOUND` |

**Tests de UC_ACC_05 afectados:**

Los tests en `tests/unit/fase2/` que llaman a `reverse('access:sod-rule-*')`
deben actualizarse a `reverse('access:separation-rule-*')`. Esta actualización
es parte del merge o inmediatamente posterior.

**Endpoint validate:**

`validate-sod` → `separation-rules/validate`. Los tests que usaban
`reverse('access:validate-separation')` deben usar
`reverse('access:separation-rule-validate')`.

**UC_ACC_01/02 — Asignar/Revocar funciones:**

`DutySeparationValidator` usa `user_has_set_a/b` (no `has_a/has_b`) y
`codes_set_a/b` (no `codes_a/b`) post-merge. Los tests que verifican
el comportamiento del validador no cambian — solo los nombres de variable
internos.

### Tests nuevos de STD-008 que pasan a develop post-merge

- `tests/unit/access/test_separation_rule.py` — reescrito para v5.4.0
- `tests/unit/access/test_separation_rule_validate.py` — 8 tests nuevos
- `tests/integration/pipeline/test_ivr_endpoints.py` — clases y URLs actualizadas

### Deuda técnica resuelta por el merge

- `test_separation_rule_viewset.py` — eliminado (ya no hay ViewSet)
- `SeparationRuleCheckSerializer` — eliminado (código muerto)
- `SeparationRuleViewSet` eliminado del router — sin colisión operationId

----

## FASE 3 — 11 UCs ALTOS RPT/ALR/PIP/LOG [PENDIENTE]

**Rama:** `feat/fase3-tdd` (nueva, desde `develop` post-merge STD-008)
**Documento de detalle:** `PLAN-IMPLEMENTACION-FASE3-TDD-20260513.md`

### Prerequisitos de FASE 3 identificados en lectura de código

Estos problemas existen en `develop` Y en la rama STD-008 (no los corrige
el merge). Deben resolverse al inicio de FASE 3:

**P-3.1 — `etl_errors`, `etl_data_availability`, `etl_retry` sin
`required_function` canónico (pipeline/views.py)**

Las tres vistas tienen `@permission_classes([IsAuthenticated, HasFunction])`
pero sin `required_function` asignado como atributo. `HasFunction` retorna
`True` sin verificar nada cuando el atributo no existe. Las verificaciones
inline con `has_function('pipeline.view_errors')` usan formato legacy.

```python
# Corrección:
etl_errors.required_function           = 'PIP-002'  # view_pipeline_errors
etl_data_availability.required_function = 'PIP-003'  # view_data_availability
etl_retry.required_function            = 'PIP-004'  # request_pipeline_retry
# + eliminar las verificaciones inline has_function('pipeline.*')
```

**P-3.2 — `ETLLogTailView.required_function = 'LOG-001'` debería ser `'LOG-004'`**

```python
class ETLLogTailView(APIView):
    required_function = 'LOG-004'  # view_etl_logs — no LOG-001
```

**P-3.3 — `AlertRule`, `AlertRuleHistory`, `Alert` no existen**

El módulo `alerts` tiene `AlertConfiguration` (estructura diferente del corpus)
pero no los modelos definidos en uc-alr-01/uc-alr-02. Requiere migración nueva.

**P-3.4 — UC_RPT_02 requiere infraestructura SSE/ASGI no disponible**

Django WSGI no soporta SSE nativo. Se implementa como stub documentado
que retorna 503 con el contrato completo en el docstring.

### Orden de implementación FASE 3

```
PREREQUISITOS P-3.1..P-3.4
  └─ commit: fix(fase3-prereqs)

GRUPO A — Raíces (sin dependencias internas):
  UC_PIP_02  Consultar Errores ETL       2d
  UC_PIP_03  Consultar Disponibilidad    2d
  UC_ALR_01  Configurar Umbrales         3d
  UC_LOG_01  Ver Logs Aplicación         2d
  UC_LOG_02  Ver Logs ETL                1d
  UC_RPT_02  Ver Métricas Tiempo Real    0.5d (stub)
  UC_RPT_03  Ver Reportes Históricos     4d

GRUPO B — Dependencias de GRUPO A:
  UC_PIP_04  Solicitar Reintento         2d  → UC_PIP_02
  UC_ALR_02  Ver Alertas Activas         2d  → UC_ALR_01
  UC_RPT_04  Exportar Reporte            6d  → UC_RPT_03

GRUPO C — Dependencia de GRUPO B:
  UC_ALR_03  Reconocer Alerta            2d  → UC_ALR_02

Total: 26.5 días
```

### Restricciones cross-cutting STD-008 que aplican a FASE 3

Derivadas del análisis de CNST-030 v3.0.0 (post STD-008 FASE 5):

- El enforcement SoD es a **nivel de API** (no DB). Los tests de FASE 3
  que involucren asignación de funciones (`UC_PIP_04` — ninguno, pero
  `UC_ALR_01` crea reglas SoD) no esperan enforcement automático en
  escrituras directas a BD.
- `SeparationRule` (no `SoDRule`) es el nombre de clase. `AlertRule` es
  un modelo diferente para UC_ALR_01 — no confundir con `SeparationRule`.
- `DutySeparationValidator.validate()` es el punto de entrada para
  verificar SoD antes de asignar funciones — no existe un signal Django.

----

## FASE 4 — 17 UCs MEDIOS [PENDIENTE]

**Sin cambios respecto al plan v3.** Las correcciones STD-008 no afectan
el scope de FASE 4. Ver plan v3 §FASE 4 para la lista de UCs y estimaciones.

```
UC_ACC_08  Permiso Temporal Excepcional   3d
UC_RPT_07  Programar Reporte             3d
UC_RPT_08  Ver Reportes Programados      2d
UC_RPT_11  Compartir Reporte             3d
UC_RPT_12..14 Reportes variantes         2d c/u
UC_RPT_15..17 Reportes IVR SPs           2d c/u
UC_ALR_04  Ver Historial Alertas         2d
UC_ALR_05  Gestionar Suscripciones       4d
UC_AUD_04  Generar Reporte Compliance    5d
UC_LOG_04  Exportar Logs                 3d
UC_LOG_05  Ver Logs Infraestructura      2d
UC_PERM_03 Conceder Permiso Excepcional  3d
UC_PERM_04 Revocar Permiso Excepcional   1d
UC_AUTH_03 Recuperar Contraseña         3d
```

**Nota para FASE 4:** `UC_AUTH_03` usa `InternalMailbox` (no email externo,
CNST-001). El modelo `InternalMailbox` existe desde FASE 0 y fue usado en
`UC_USR_01` y `UC_AUTH_03` en FASE 2. Sin cambios por STD-008.

----

## FASE 5 — 10 UCs BAJOS [PENDIENTE]

**Sin cambios respecto al plan v3.** Ver plan v3 §FASE 5.

```
UC_ACC_09  Auditar Cambios de Acceso     2d
UC_RPT_09  Configurar Filtros            2d
UC_RPT_10  Guardar Vista                 2d
UC_PERM_09 Auditar Acceso               1d
UC_PERM_10 Consultar Auditoría Permisos  2d
UC_LOG_06  Ver Estado del Sistema        2d
UC_LOG_07  Ver Métricas Técnicas         3d
UC_LOG_03  Buscar Logs                   3d
UC_AUD_02  Buscar Auditoría              3d
UC_AUD_03  Exportar Auditoría            3d
```

----

## Deuda técnica conocida post-STD-008

### DT-ROUTING-001 — `access-groups/` vs `groups/` (drf-spectacular)

`access-groups/` (FASE 2 TDD canónico) y el router `groups/` (legacy)
generan la colisión `access_access_groups_retrieve` en drf-spectacular.
Esta colisión no fue introducida por STD-008 — existía antes. Candidato
para un ciclo de limpieza de routing al finalizar FASE 3.

### DT-ROUTING-002 — `users/{id}/` vs `users/{user_id}/` (drf-spectacular)

Colisión similar entre las rutas FASE 2 TDD y las legacy del router para
`users_partial_update` y `users_destroy`. Misma categoría que DT-ROUTING-001.

### DT-ROUTING-003 — `change-password/` vs `change_password/` (drf-spectacular)

Colisión entre rutas de autenticación FASE 1 TDD y legacy del router.

### DT-ENFORCEMENT-001 — Enforcement SoD a nivel API, no DB

Documentado en CNST-030 §5.1 v3.0.0. El ADR que decida si agregar
un signal Django está pendiente. No bloquea ninguna FASE.

### DT-SPECTACULAR-004 — `sod-rule-*` names en router de develop

Antes del merge de STD-008, el `develop` tiene URLs con nombre
`sod-rule-list-create`, `sod-rule-detail`. Post-merge pasan a
`separation-rule-list-create`, `separation-rule-detail`. Cualquier
test que haga `reverse('access:sod-rule-*')` fallará post-merge
y debe actualizarse en el mismo commit de merge.

----

## Criterios de DONE globales (heredados del plan v3 + correcciones STD-008)

1. Cada CA documentado en `Parte 9` del UC tiene un test
2. `required_function` usa código `MOD-NNN` del catálogo v5.4.0
3. `permission_classes` explícito en cada view (CNST-010)
4. AuditEvent emitido en escrituras — event types usan formato `SEPARATION_RULE_*`
   (no `SOD_RULE_*`) para los eventos de UC_ACC_05
5. Sin email externo (CNST-001) — `SMTP` no llamado
6. BR-009 en todos los modelos con ciclo de vida
7. Sin PII en AuditEvent (CNST-026)
8. `SeparationRule` (no `SoDRule`) en cualquier referencia de documentación o código
9. Endpoints de IACT-ui usan codenames `*_separation_rule` (no `*_sod`)
10. Hallazgos documentados en `docs/architecture/HALLAZGOS-FASEXX-TDD-*.md`

----

## Tabla de volumen y estimaciones (actualizada)

| Fase | Descripción | UCs | Días | Estado |
|---|---|---|---|---|
| Merge STD-008 | Convergencia de ramas | — | 0.5 | Pendiente |
| FASE 0 | Infraestructura transversal | — | 8 | Completada |
| FASE 1 | 8 UCs CRÍTICOS | 8 | 29 | Completada |
| FASE 2 | 15 UCs ALTOS + correcciones STD-008 | 15 | 39+1 | Completada (merge pendiente) |
| FASE 3 | 11 UCs ALTOS RPT/ALR/PIP/LOG | 11 | 27 | Pendiente |
| FASE 4 | 17 UCs MEDIOS | 17 | 38 | Pendiente |
| FASE 5 | 10 UCs BAJOS | 10 | 21 | Pendiente |
| **Total** | **61 UCs** | **61** | **163.5** | |

----

## Tests existentes incorrectos — actualización respecto al plan v3

El plan v3 listaba estos tests como incorrectos. Se añaden las
correcciones STD-008 que ya resolvieron algunos:

| Archivo | Problema | Estado |
|---|---|---|
| `test_separation_rule_viewset.py` | URL inexistente + factory rota | **RESUELTO** — eliminado, reemplazado por `test_separation_rule_validate.py` |
| `test_separation_rule.py` | Campos v5.2.1 (`function_a`, `function_b`) | **RESUELTO** — reescrito para v5.4.0 |
| `test_views.py` (authentication) | No cubre CA-02 (BR-005), CA-03, CA-04 | Pendiente FASE 1 (ya implementado) |
| `test_permissions.py` (access) | `HasFunction` sin `PermissionService` | Pendiente FASE 1 |
| `test_views.py` (pipeline) | `required_function='pipeline.view_status'` | **RESUELTO** en FASE 1 F1-H-004 |
| `test_api.py` (audit) | No verifica inmutabilidad BR-010 | Pendiente FASE 0-T5 |
| Endpoints con `required_function` legacy | Strings pre-v5.4.0 | Parcialmente resuelto — pipeline pendiente (P-3.1) |
| Tests UC_ACC_05 con `sod-rule-*` URLs | Post-merge STD-008 fallarán | Actualizar en commit de merge |
