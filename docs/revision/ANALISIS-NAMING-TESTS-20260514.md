# Análisis de Violaciones de Clean Code — Nomenclatura de Tests

**Artefacto:** ANALISIS-NAMING-TESTS-20260514
**Versión:** 1.0.0
**Fecha:** 2026-05-14
**Base:** `develop` @ `2b1b9b3`
**Alcance:** Directorio `callcentersite/tests/` completo + plan TDD v5

----

## 1. Principio violado

Clean Code §12 (Nombres): "El nombre de un módulo debe revelar su intención.
Un nombre como `test_models.py` no dice nada sobre qué modelos ni qué aspectos
de su comportamiento se prueban. Un nombre como `fase3/test_uc_pip_02_errors.py`
expone detalles de implementación del plan de trabajo (ciclo, número de UC)
que no tienen ningún valor para quien lee el test por primera vez."

Dos reglas concretas que este proyecto viola sistemáticamente:

**Regla A — Directorios por fase de desarrollo:** Un directorio `fase3/`
organiza los tests según cuándo fueron escritos, no según qué comportamiento
describen. Si alguien busca los tests de alertas, debe conocer de antemano que
las alertas se implementaron en FASE 3. Esa es información accidental, no
esencial.

**Regla B — Nombres con código de UC:** `test_uc_alr_04.py` solo es
descifrable con el glosario del proyecto. "ALR-04" no dice "historial de
alertas". El nombre correcto es `test_alert_history.py` — legible por cualquier
desarrollador sin contexto previo.

----

## 2. Inventario completo de violaciones

### 2.1 Directorios con nombre `fase*` — 6 violaciones

Estos directorios agrupan tests por ciclo de desarrollo en lugar de por dominio
funcional. Un test de login en `fase1/` y un test de login mejorado en `fase4/`
deberían estar juntos en `authentication/`, no separados por el número de
iteración en que se escribieron.

| Directorio violador | Tests que contiene | Directorio correcto |
|---|---|---|
| `tests/unit/fase0/` | DB router (infraestructura) | `tests/unit/infrastructure/` |
| `tests/unit/fase1/` | Login, session model, user model fields | `tests/unit/authentication/` (ya existe) |
| `tests/unit/fase2/` | Logout | `tests/unit/authentication/` (ya existe) |
| `tests/unit/fase3/` | Alertas, logs, pipeline, reportes | directorios de dominio ya existentes |
| `tests/unit/fase4/` | Permisos excepcionales, historial alertas, logs export, reportes | directorios de dominio ya existentes |
| `tests/unit/fase5/` | Auditoría, logs, permisos, reportes | directorios de dominio ya existentes |

### 2.2 Archivos con código de UC en el nombre — 15 violaciones

El patrón `test_uc_<dominio>_<número>.py` mezcla dos problemas: el prefijo
`uc_` expone el sistema de numeración interno del corpus, y el número no aporta
información sobre el comportamiento testeado.

| Archivo actual | Ubicación | Nombre descriptivo propuesto | Directorio destino |
|---|---|---|---|
| `test_uc_auth_01_login.py` | `fase1/` | `test_login_jwt.py` | `authentication/` |
| `test_uc_auth_02_logout.py` | `fase2/` | `test_logout_token_blacklist.py` | `authentication/` |
| `test_uc_auth_03.py` | `fase4/` | `test_password_reset.py` | `authentication/` |
| `test_uc_alr_01_02_03.py` | `fase3/` | `test_alert_rules_and_acknowledgement.py` | `alerts/` |
| `test_uc_alr_04.py` | `fase4/` | `test_alert_history.py` | `alerts/` |
| `test_uc_log_01_02.py` | `fase3/` | `test_log_tail_views.py` | `logs/` |
| `test_uc_log_04_alr05_aud04.py` | `fase4/` | `test_log_export_and_subscriptions.py` | `logs/` |
| `test_uc_log_05.py` | `fase4/` | `test_infrastructure_logs.py` | `logs/` |
| `test_uc_pip_02_errors.py` | `fase3/` | `test_pipeline_error_query.py` | `pipeline/` |
| `test_uc_pip_03_availability.py` | `fase3/` | `test_pipeline_data_availability.py` | `pipeline/` |
| `test_uc_pip_04_retry.py` | `fase3/` | `test_pipeline_retry.py` | `pipeline/` |
| `test_uc_rpt_03_historical.py` | `fase3/` | `test_historical_reports.py` | `reports/` |
| `test_uc_rpt_04_export.py` | `fase3/` | `test_report_export_async.py` | `reports/` |
| `test_uc_rpt_07_08_11.py` | `fase4/` | `test_scheduled_reports_and_sharing.py` | `reports/` |
| `test_uc_rpt_12_17.py` | `fase4/` | `test_analytics_reports.py` | `reports/` |

### 2.3 Archivos con código de fase en el nombre — 2 violaciones

| Archivo actual | Ubicación | Problema | Nombre propuesto | Directorio destino |
|---|---|---|---|---|
| `test_f0_t6_db_router.py` | `fase0/` | Expone "F0-T6" — código de tarea interna | `test_multi_database_router.py` | `infrastructure/` (nuevo) |
| `test_fase1_models.py` | `users/` | Expone "fase1" — ciclo de desarrollo | `test_user_core_model.py` | `users/` (mismo) |

### 2.4 Archivos con nombre genérico sin información de dominio — 18 violaciones

`test_models.py`, `test_views.py` y similares dicen únicamente el tipo de
artefacto que testean, no el comportamiento. Cualquier app tiene modelos y
vistas; el nombre no filtra nada.

| Archivo actual | Ubicación | Clases/dominio que contiene | Nombre descriptivo propuesto |
|---|---|---|---|
| `test_models.py` | `access/` | `TestModule`, `TestFunction`, `TestUserPermission` | `test_function_catalog_models.py` |
| `test_services.py` | `access/` | `TestModuleAccessService` | `test_module_access_service.py` |
| `test_views.py` | `access/` | `TestMyModulesView` | `test_my_modules_view.py` |
| `test_api.py` | `audit/` | `TestAuditLogAPI` | `test_audit_log_api.py` |
| `test_models.py` | `audit/` | `TestAuditLog` | `test_audit_log_model.py` |
| `test_models.py` | `authentication/` | JWT, session, blacklist | `test_auth_models.py` |
| `test_serializers.py` | `authentication/` | `TestCustomTokenObtainPairSerializer`, `TestPasswordResetRequestSerializer` | `test_auth_serializers.py` |
| `test_services.py` | `authentication/` | Auth services | `test_auth_services.py` |
| `test_views.py` | `authentication/` | `TestAuthViewSet` — login endpoint | `test_auth_viewset.py` |
| `test_views.py` | `pipeline/` | `TestETLStatusView` | `test_etl_status_view.py` |
| `test_models.py` | `reports/` | `Report`, `ExportJob` | `test_report_export_models.py` |
| `test_serializers.py` | `reports/` | Report serializers | `test_report_serializers.py` |
| `test_services.py` | `reports/` | Report services | `test_report_services.py` |
| `test_views.py` | `reports/` | Report views | `test_report_views.py` |
| `test_factories.py` | `unit/` | Factory functions | `test_test_factories.py` → mover a `tests/` raíz |
| `test_fixtures.py` | `unit/` | Fixture validation | `test_test_fixtures.py` → mover a `tests/` raíz |
| `test_serializers.py` | `users/` | User serializers | `test_user_serializers.py` |
| `test_views.py` | `users/` | `TestUserViewSet` | `test_user_viewset_ext.py`* |

> *`test_user_viewset.py` ya existe en `users/`. El nuevo nombre evita colisión
> hasta que se consoliden.

### 2.5 Archivos del plan TDD v5 que propagan las mismas violaciones — 22 referencias

El plan `PLAN-IMPLEMENTACION-TDD-v5-20260514.md` propone 22 artefactos nuevos
con los mismos patrones incorrectos (`tests/unit/fase6/test_uc_*.py`,
`tests/unit/fase7/test_uc_*.py`). Todos deben corregirse antes de que el plan
se ejecute.

| Propuesto en plan v5 | Corrección requerida |
|---|---|
| `tests/unit/fase6/test_uc_auth_04.py` | `tests/unit/authentication/test_change_password.py` |
| `tests/unit/fase6/test_uc_auth_05.py` | `tests/unit/authentication/test_session_management.py` |
| `tests/unit/fase6/test_uc_usr_02.py` | `tests/unit/users/test_user_list_search.py` |
| `tests/unit/fase6/test_uc_usr_03_04.py` | `tests/unit/users/test_user_modify_eliminate.py` |
| `tests/unit/fase6/test_uc_perm_07.py` | `tests/unit/access/test_effective_permissions_engine.py` |
| `tests/unit/fase6/test_uc_perm_05_06.py` | `tests/unit/access/test_access_group_management.py` |
| `tests/unit/fase6/test_uc_perm_01_02.py` | `tests/unit/access/test_agr_assign_revoke_perm_view.py` |
| `tests/unit/fase6/test_uc_perm_08.py` | `tests/unit/authentication/test_dynamic_menu.py` |
| `tests/unit/fase6/test_uc_aud_01.py` | `tests/unit/audit/test_general_audit_timeline.py` |
| `tests/unit/fase7/test_uc_opr_01.py` | `tests/unit/operator/test_agent_state_transitions.py` |
| `tests/unit/fase7/test_uc_opr_08_09_10.py` | `tests/unit/operator/test_agent_acw_break_logout.py` |
| `tests/unit/fase8/test_uc_sup_03.py` | `tests/unit/operator/test_agent_broadcast.py` |

----

## 3. Resumen cuantitativo

| Categoría | Violaciones actuales | Violaciones en plan v5 | Total |
|---|---|---|---|
| Directorios `fase*` | 6 | 3 (fase6, fase7, fase8 propuestos) | 9 |
| Archivos con código UC | 15 | 12 (plan v5) | 27 |
| Archivos con código de fase | 2 | 0 | 2 |
| Archivos genéricos sin dominio | 18 | 0 | 18 |
| **Total** | **41** | **15** | **56** |

----

## 4. Estructura de directorios correcta

La organización correcta es **por dominio funcional**, no por ciclo de
desarrollo. Todos los tests de autenticación van juntos, independientemente
de cuándo se escribieron:

```
tests/
├── unit/
│   ├── access/          # Funciones, AGRs, SoD, permisos efectivos, menú
│   ├── alerts/          # Reglas, alertas activas, historial, suscripciones
│   ├── audit/           # AuditLog, servicio de auditoría, timeline
│   ├── authentication/  # Login, logout, reseteo, cambio de password, sesiones, menú
│   ├── config/          # Regresiones de configuración (required_function, spectacular)
│   ├── core/            # Abstracciones, middleware, navegación
│   ├── dashboard/       # KPIs, segmentos
│   ├── infrastructure/  # DB router, migrations, configuración multi-BD
│   ├── logs/            # Tail, búsqueda, exportación, infraestructura, health, métricas
│   ├── operator/        # Estado de agente, ACW, break, logout, broadcast  [FASE 7/8]
│   ├── pipeline/        # Estado ETL, errores, disponibilidad, reintento
│   ├── reports/         # Históricos, exportación, programados, analíticos, filtros, vistas
│   └── users/           # Creación, listado, modificación, eliminación
├── integration/
│   ├── authentication/
│   ├── pipeline/
│   └── users/
└── ...
```

Los directorios `fase0/` a `fase5/` desaparecen. Sus archivos se mueven a
sus directorios de dominio correspondientes.

----

## 5. Casos especiales

### 5.1 Archivos que cubren múltiples dominios

Algunos archivos en `fase3/` y `fase4/` mezclan UCs de distintos dominios en
un solo archivo (`test_uc_log_04_alr05_aud04.py` cubre logs + alertas + audit).
Estas mezclas son el resultado de agrupar por FASE en lugar de por dominio.

Al renombrar, estas mezclas deben **separarse**:

```
test_uc_log_04_alr05_aud04.py
    → tests/unit/logs/test_log_export_async.py   (UC_LOG_04)
    → tests/unit/alerts/test_alert_subscriptions.py  (UC_ALR_05)
    → tests/unit/audit/test_compliance_report.py  (UC_AUD_04)
```

Esta separación es una **refactorización de tests**, no de código de
producción. El comportamiento testeado no cambia.

### 5.2 Archivos en `fase3/` cuyo dominio ya tiene directorio

`fase3/test_uc_alr_01_02_03.py` → `tests/unit/alerts/` ya existe.
`fase3/test_uc_log_01_02.py` → `tests/unit/logs/` no existe aún.
`fase3/test_uc_pip_02_errors.py` → `tests/unit/pipeline/` ya existe.

La migración es directa para los que tienen directorio. Para `logs/` hay que
crear el directorio.

### 5.3 El directorio `tests/unit/utils_tests/`

`utils_tests/` es un nombre redundante (ya está dentro de `unit/`). Debe
fusionarse en `tests/unit/utils/` que también ya existe. Son dos directorios
paralelos que testean el mismo dominio.

### 5.4 `test_factories.py` y `test_fixtures.py` en `tests/unit/`

Estos dos archivos testean la infraestructura de testing (factories y fixtures),
no el código de producción. Deben moverse a `tests/` (raíz) y renombrarse:
- `test_factories.py` → `tests/test_factory_integrity.py`
- `test_fixtures.py` → `tests/test_fixture_integrity.py`

----

## 6. Impacto del cambio

El renombrado es una operación de refactorización pura:

- **Sin cambios de código de producción.** Ningún archivo en `apps/` se modifica.
- **Sin cambios de lógica de tests.** El contenido de cada archivo de test no cambia (excepto la separación de los mixtos, §5.1).
- **Actualización de imports.** Los `conftest.py` que importen desde paths relativos deben actualizarse.
- **Actualización del plan TDD v5.** Las 15 referencias con rutas incorrectas deben corregirse.

El riesgo es bajo porque pytest descubre tests por convención (`test_*.py`)
independientemente del directorio. No hay referencias a rutas de tests en el
código de producción.

----

## 7. Violaciones detectadas en el plan TDD v5

El plan `PLAN-IMPLEMENTACION-TDD-v5-20260514.md` propaga sistemáticamente el
patrón incorrecto en todas sus tareas. Necesita ser revisado para que cada
tarea que proponga un nuevo archivo de test use la nomenclatura y estructura
correctas según §4 de este análisis.

El plan actual dice, por ejemplo:

```
Crear tests/unit/fase6/__init__.py y tests/unit/fase6/test_uc_auth_04.py
```

Debe decir:

```
Crear tests/unit/authentication/test_change_password.py
```

Este cambio afecta a **22 referencias de artefactos** y **10 referencias de
criterios de completitud** dentro del plan v5.

----

## 8. Próximo paso recomendado

Antes de ejecutar cualquier tarea del plan TDD v5, crear un commit de
remediación que:

1. Cree los directorios de dominio faltantes (`infrastructure/`, `logs/`,
   `operator/`).
2. Mueva y renombre todos los archivos existentes según la tabla del §2.2.
3. Separe los archivos que mezclan dominios (§5.1).
4. Actualice el plan TDD v5 con las rutas y nombres correctos.
5. Verifique que la suite completa sigue pasando tras el movimiento.
