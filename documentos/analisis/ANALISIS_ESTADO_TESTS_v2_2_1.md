# ANÁLISIS DE ESTADO ACTUAL — Tests v2.2.1
## IACT API — Diagnóstico Completo
**Fecha:** 2026-03-21
**Branch:** claude/check-tools-ZDoAR
**Django check:** ✅ Sin problemas (0 silenced)
**Migraciones:** ✅ Todas aplicadas

---

## RESUMEN EJECUTIVO

| Categoría          | Cantidad | Impacto                              |
|--------------------|----------|--------------------------------------|
| Tests PASSED       | 119      | ✅ Funcionan correctamente           |
| Tests FAILED       | 59       | ❌ Falla en lógica/aserciones        |
| Errors de setup DB | 344      | 🔴 Permisos MariaDB para test DB     |
| Errors de colección| 20 archivos | 🔴 ImportError / ModuleNotFound   |
| Warnings           | 4        | ⚠️  Mocks ya importados              |
| **Tiempo de run**  | ~6.83s   | (con --continue-on-collection-errors)|

**El test runner se interrumpe sin `--continue-on-collection-errors`** porque
20 archivos no se pueden importar. Sin ese flag: `0 tests run`.

---

## CATEGORÍA 1 — ERRORES DE COLECCIÓN (20 archivos)

Los tests no se pueden ni importar. Son brechas entre lo que los tests
esperan y lo que el código realmente expone.

### 1.1 `'Role' from 'apps.access.models'` — RAÍZ DE CASCADA

**Error:**
```
ImportError: cannot import name 'Role' from 'apps.access.models'
```

**Origen del problema:**
```python
# tests/factories/access_factories.py:13
from apps.access.models import (Role, ...)   # 'Role' no existe
```

**Archivos afectados (9 — cascada por factories/__init__.py):**
```
tests/integration/authentication/test_auth_flow.py
tests/integration/authentication/test_recovery_flow.py
tests/integration/authentication/test_session_flow.py
tests/unit/authentication/test_models.py
tests/unit/authentication/test_services.py
tests/unit/authentication/test_views.py
tests/unit/core/test_core_etl_service.py  (también ivr_legacy)
tests/unit/core/test_core_models.py
tests/unit/authentication/test_services.py
```

**Causa:** `apps.access.models` tiene `Function`, `UserFunctionAssignment`,
`Module`, `UserModuleAccess` — pero NO `Role`. Los tests fueron escritos
cuando el modelo se llamaba `Role` (sistema anterior a RBAC v6.0.0).

---

### 1.2 `'HasModuleAccess' from 'apps.access.permissions'`

**Error:**
```
ImportError: cannot import name 'HasModuleAccess' from 'apps.access.permissions'
```
**Archivo:** `tests/unit/access/test_permissions.py:13`

**Causa:** La clase `HasModuleAccess` no está implementada o no está
exportada en `apps/access/permissions/__init__.py`.

---

### 1.3 `'CustomTokenObtainPairSerializer' from 'apps.authentication.serializers'`

**Error:**
```
ImportError: cannot import name 'CustomTokenObtainPairSerializer' from 'apps.authentication.serializers'
```
**Archivo:** `tests/unit/authentication/test_serializers.py:4`

**Causa:** El serializer JWT customizado no existe en la app `authentication`.
Puede haberse movido o nunca implementado.

---

### 1.4 `No module named 'apps.ivr_legacy'`

**Error:**
```
ModuleNotFoundError: No module named 'apps.ivr_legacy'
```

**Origen:**
```python
# apps/core/services/etl_service.py:15
from apps.ivr_legacy.adapters import IVRAdapter  # módulo no existe
```
**Archivo de test afectado:** `tests/unit/core/test_core_etl_service.py`

**Causa:** La app del módulo IVR se llama `apps.ivr` (no `apps.ivr_legacy`).
El `etl_service.py` importa un módulo con nombre incorrecto.

---

### 1.5 Modelos faltantes en `apps.core.models`

**Errores:**
```
ImportError: cannot import name 'CallRecord' from 'apps.core.models'
ImportError: cannot import name 'Service' from 'apps.core.models'
ImportError: cannot import name 'UserServiceAccess' from 'apps.core.models'
```

**Archivos afectados:**
```
tests/unit/core/test_core_models.py:10          → CallRecord
tests/unit/core/test_core_serializers.py:8      → CallRecord, Center, Service
tests/unit/core/test_core_serializers_OLD.py:8  → CallRecord, Center, Service
tests/unit/core/test_service_access.py:4        → Service, Center, UserServiceAccess, CallRecord
```

**Causa:** `apps.core.models` solo contiene abstract models
(`TimeStampedModel`, `SoftDeleteMixin`, etc.). Los modelos concretos
`CallRecord`, `Service`, `UserServiceAccess` están en otras apps
o nunca se crearon. `Center` existe en `apps.pipeline.models`.

---

### 1.6 `'LoggingMiddleware' from 'apps.core.middleware.logging'`

**Error:**
```
ImportError: cannot import name 'LoggingMiddleware' from 'apps.core.middleware.logging'
```
**Archivo:** `tests/unit/core/test_middleware.py:25`

**Causa:** La clase `LoggingMiddleware` no está implementada o no está
exportada en el módulo de middleware.

---

### 1.7 `'ServiceFilterMixin' from 'apps.core.mixins'`

**Error:**
```
ImportError: cannot import name 'ServiceFilterMixin' from 'apps.core.mixins'
```
**Archivo:** `tests/unit/core/test_mixins.py:24`

**Causa:** `ServiceFilterMixin` no existe en `apps/core/mixins.py`.

---

### 1.8 `'HasServiceAccess' from 'apps.core.permissions'`

**Error:**
```
ImportError: cannot import name 'HasServiceAccess' from 'apps.core.permissions'
```
**Archivo:** `tests/unit/core/test_permissions.py:25`

**Causa:** `HasServiceAccess` no existe en `apps/core/permissions.py`.

---

### 1.9 Serializers faltantes en `apps.users.serializers`

**Errores:**
```
ImportError: cannot import name 'LoginSerializer' from 'apps.users.serializers'
ImportError: cannot import name 'UserProfileSerializer' from 'apps.users.serializers'
```

**Archivos afectados:**
```
tests/unit/users/test_auth_serializers.py:11  → LoginSerializer
tests/unit/users/test_serializers.py:10       → UserProfileSerializer
```

**Causa:** `LoginSerializer` probablemente pertenece a `apps.authentication`
(no a `apps.users`). `UserProfileSerializer` puede llamarse
`ProfileSerializer` en la implementación actual.

---

### 1.10 `'format_phone' from 'apps.utils.formatters'`

**Error:**
```
ImportError: cannot import name 'format_phone' from 'apps.utils.formatters'
```
**Archivo:** `tests/unit/utils/test_formatters.py:20`

**Causa:** La función `format_phone` no está implementada o tiene
otro nombre en `apps/utils/formatters.py`.

---

### 1.11 `No module named 'apps.utils.network'`

**Error:**
```
ModuleNotFoundError: No module named 'apps.utils.network'
```
**Archivo:** `tests/unit/utils/test_utils_network.py:8`

**Causa:** El módulo `apps/utils/network.py` no existe.
Las funciones `get_client_ip`, `get_user_agent`, `get_request_metadata`
están en otro lugar o no implementadas.

---

## CATEGORÍA 2 — ERRORES DE SETUP DE BASE DE DATOS (344 errors)

### 2.1 Descripción del Error

```
MySQLdb.OperationalError: (1142,
  "ALTER command denied to user 'django_user'@'localhost'
   for table 'test_ivr_legacy'.'django_content_type'")
```

### 2.2 Causa Raíz

El usuario `django_user` en MariaDB tiene permisos `GRANT SELECT` (READ-ONLY,
CNST-003). Pero pytest-django necesita `CREATE`, `DROP` y `ALTER` para
crear/destruir la base de datos de test `test_ivr_legacy`.

**Síntomas adicionales:**
```
Got an error creating the test database: database "test_iact_analytics" already exists
Got an error creating the test database: (1007, "Can't create database 'test_ivr_legacy'; database exists")
```
Las bases de datos de test de una ejecución anterior quedaron sin limpiar.

### 2.3 Afectación

**344 tests** no pueden ejecutar su `setup` porque el fixture de BD falla.
Esto convierte tests que podrían pasar en errores de infraestructura.

### 2.4 Archivos principales afectados
```
tests/unit/ivr_legacy/test_ivr_app.py   → MySQLdb.OperationalError
(cualquier test que use @pytest.mark.django_db con la BD 'ivr')
```

---

## CATEGORÍA 3 — TESTS FAILED (59 tests)

### 3.1 Grupo A: Navigation Builders — 24 tests FAILED

**Archivo:** `tests/unit/core/test_navigation_builders.py`

**Error base:**
```python
AttributeError: type object 'MenuValidator' has no attribute 'validate_numeric_id'
AttributeError: type object 'MenuValidator' has no attribute 'validate_level1_id'
AttributeError: type object 'MenuValidator' has no attribute 'validate_level2_id'
AttributeError: type object 'MenuValidator' has no attribute 'validate_icon_path'
AttributeError: type object 'MenuValidator' has no attribute 'validate_menu_structure'
```

**Tests FAILED (24):**
```
TestMenuValidator::test_validate_numeric_id_valid
TestMenuValidator::test_validate_numeric_id_invalid_type
TestMenuValidator::test_validate_numeric_id_out_of_range
TestMenuValidator::test_validate_level1_id_valid
TestMenuValidator::test_validate_level1_id_invalid
TestMenuValidator::test_validate_level2_id_valid
TestMenuValidator::test_validate_level2_id_invalid
TestMenuValidator::test_validate_icon_path_exists
TestMenuValidator::test_validate_icon_path_not_exists
TestMenuValidator::test_validate_menu_structure_valid_level1
TestMenuValidator::test_validate_menu_structure_valid_level2
TestMenuValidator::test_validate_menu_structure_missing_required_fields
TestMenuValidator::test_validate_menu_structure_invalid_id_for_level
TestMenuBuilder::test_build_user_menu_all_permissions
TestMenuBuilder::test_build_user_menu_no_permissions
TestMenuBuilder::test_build_user_menu_with_permissions
TestMenuBuilder::test_filter_by_permissions_empty_required
TestMenuBuilder::test_filter_by_permissions_user_has_permission
TestMenuBuilder::test_filter_by_permissions_user_missing_permission
TestMenuBuilder::test_personalize_menu_avatar_url
TestMenuBuilder::test_personalize_menu_username
TestMenuBuilderIntegration::test_build_menu_multiple_apps
TestMenuBuilderIntegration::test_build_menu_ordered
TestMenuSerializer::test_serialize_menu_with_endpoint
```

**Causa:** La implementación de `MenuValidator` y `MenuBuilder` no tiene
los métodos que los tests esperan (`validate_numeric_id`, `validate_level1_id`,
etc.). Los tests anticipan una API que no está implementada.

---

### 3.2 Grupo B: Utils/Helpers — 9 tests FAILED

**Archivo:** `tests/unit/utils/test_helpers.py`

```
TestGenerateRandomToken::test_generates_token_default_length
TestGetClientIP::test_ip_none_when_no_headers
TestGetUserAgent::test_user_agent_missing
TestSafeGet::test_safe_get_deep_nested
TestSafeGet::test_safe_get_existing_key
TestSafeGet::test_safe_get_missing_key_returns_default
```

**Causa:** Funciones de `apps.utils.helpers` no implementadas o con
interfaz distinta a la esperada por los tests.

---

### 3.3 Grupo C: Utils/Misc — 16 tests FAILED

**Archivo:** `tests/unit/utils/test_utils_misc.py`

```
TestDateUtils::test_days_between
TestDateUtils::test_format_date
TestDateUtils::test_get_date_range
TestDateUtils::test_get_month_start_end
TestDateUtils::test_is_weekend
TestDateUtils::test_parse_date_string
TestDateUtils::test_parse_datetime_string
TestNumberUtils::test_clamp_number
TestNumberUtils::test_is_number
TestNumberUtils::test_parse_number_float
TestNumberUtils::test_parse_number_int
TestNumberUtils::test_percentage_change
TestStringUtils::test_capitalize_words
TestStringUtils::test_is_empty_or_whitespace
TestStringUtils::test_remove_accents
TestStringUtils::test_reverse_string
TestStringUtils::test_sanitize_string
TestStringUtils::test_word_count
```

**Causa:** Utilidades de fecha, número y string no implementadas o con
interfaz diferente.

---

### 3.4 Grupo D: Validators — 8 tests FAILED

**Archivo:** `tests/unit/utils/test_validators.py` + `tests/unit/utils_tests/test_validators.py`

```
TestValidatePhoneNumber::test_valid_landline_8_digits
TestValidateRut::test_valid_rut_with_dash
TestValidateRut::test_valid_rut_without_dash
TestValidateRut::test_valid_rut_with_k
TestValidateService800::test_valid_service_800
TestValidateCodigoCenter::test_invalid_codigo_too_short
TestValidateDateRange::test_invalid_start_after_end
TestValidateExportRowLimit::test_invalid_row_count_over_limit
TestPhoneValidator::test_valid_landline  (utils_tests/)
```

**Causa:** Validadores con lógica de validación incorrecta o umbrales
distintos a los esperados (ej: longitud mínima de códigos, formatos RUT).

---

### 3.5 Grupo E: IVR Legacy App — 1 test FAILED

```
tests/unit/ivr_legacy/test_ivr_app.py::test_ivr_legacy_app_importable
```

**Causa:** El test intenta importar `apps.ivr_legacy` que no existe
(la app se llama `apps.ivr`).

---

### 3.6 Grupo F: Fixtures — 1 test FAILED

```
tests/unit/test_fixtures.py::test_user_data_fixture
```

**Causa:** El fixture de datos de usuario no cumple las aserciones
esperadas por el test.

---

## CATEGORÍA 4 — WARNINGS (4)

```
PytestAssertRewriteWarning: Module already imported so cannot be rewritten:
  tests.mocks.service_mocks
  tests.mocks.file_mocks
  tests.mocks.scheduler_mocks
  tests.mocks.external_mocks
```

**Causa:** Los mocks se importan en `conftest.py` antes de que pytest
pueda reescribirlos para assertion introspection. No es crítico pero
reduce la calidad del output de fallos en tests que usen esos mocks.

---

## MAPA DE BRECHAS: Tests vs. Código Real

| Símbolo que busca el test            | Dónde busca           | Existe? | Ubicación real / Nota           |
|--------------------------------------|-----------------------|---------|---------------------------------|
| `Role`                               | `apps.access.models`  | ❌ NO   | Fue reemplazado por `Function` (RBAC v6.0.0) |
| `HasModuleAccess`                    | `apps.access.permissions` | ❌ NO | No implementado |
| `CustomTokenObtainPairSerializer`    | `apps.authentication.serializers` | ❌ NO | No implementado |
| `apps.ivr_legacy`                    | módulo Python         | ❌ NO   | La app se llama `apps.ivr` |
| `IVRAdapter`                         | `apps.ivr_legacy.adapters` | ❌ NO | Módulo inexistente |
| `CallRecord`                         | `apps.core.models`    | ❌ NO   | No en core (¿apps.ivr?) |
| `Service`                            | `apps.core.models`    | ❌ NO   | No existe |
| `UserServiceAccess`                  | `apps.core.models`    | ❌ NO   | No existe |
| `LoggingMiddleware`                  | `apps.core.middleware.logging` | ❌ NO | No implementado |
| `ServiceFilterMixin`                 | `apps.core.mixins`    | ❌ NO   | No implementado |
| `HasServiceAccess`                   | `apps.core.permissions` | ❌ NO | No implementado |
| `LoginSerializer`                    | `apps.users.serializers` | ❌ NO | ¿Está en `apps.authentication`? |
| `UserProfileSerializer`              | `apps.users.serializers` | ❌ NO | Puede ser `ProfileSerializer` |
| `format_phone`                       | `apps.utils.formatters` | ❌ NO | Función no implementada |
| `apps.utils.network`                 | módulo Python         | ❌ NO   | Módulo no existe |
| `MenuValidator.validate_numeric_id`  | `apps.core.navigation`| ❌ NO   | Método no implementado |
| `MenuValidator.validate_level1_id`   | `apps.core.navigation`| ❌ NO   | Método no implementado |
| `MenuBuilder.build_user_menu`        | `apps.core.navigation`| ❌ NO   | Método no implementado |

---

## DJANGO CHECK — Estado del Framework

```bash
python manage.py check
→ System check identified no issues (0 silenced)  ✅
```

---

## MIGRACIONES — Estado

```
access:         [X] 0001_initial  [X] 0002_initial        ✅
alerts:         [X] 0001_initial  [X] 0002_initial        ✅
audit:          [X] 0001_initial  [X] 0002_initial        ✅
authentication: [X] 0001_initial .. [X] 0004              ✅
dashboard:      [X] 0001_initial  [X] 0002_initial        ✅
ivr:            [X] 0001_initial                          ✅
pipeline:       [X] 0001_initial  [X] 0002_initial        ✅
reports:        [X] 0001_initial  [X] 0002_initial        ✅
users:          [X] 0001_initial                          ✅
core:           (no migrations — solo abstract models)    ✅
```
**Todas las migraciones aplicadas.**

---

## PRIORIDAD DE CORRECCIÓN

### 🔴 CRÍTICO — Desbloquea la mayor parte de los tests

1. **Corregir `tests/factories/access_factories.py`**
   - Reemplazar `Role` por `Function` / `UserFunctionAssignment`
   - Desbloquea 9 archivos en cascada (integration + authentication tests)

2. **Permisos MariaDB para test DB**
   - Otorgar permisos GRANT ALL en `test_ivr_legacy` al usuario `django_user`
   - O configurar `--reuse-db` / usar SQLite en settings/testing.py para la BD ivr
   - Desbloquea 344 errores de setup

### 🟠 ALTO — Brechas de implementación

3. **Implementar o actualizar `MenuValidator`/`MenuBuilder`**
   - Agregar métodos: `validate_numeric_id`, `validate_level1_id`,
     `validate_level2_id`, `validate_icon_path`, `validate_menu_structure`
   - Desbloquea 24 tests

4. **Renombrar import en `etl_service.py`**
   - `from apps.ivr_legacy.adapters import IVRAdapter`
     → `from apps.ivr.adapters import IVRAdapter` (o donde corresponda)

5. **Corregir imports de serializers**
   - `LoginSerializer` → mover a `apps.authentication.serializers`
   - `UserProfileSerializer` → verificar nombre real (`ProfileSerializer`)

### 🟡 MEDIO — Módulos/funciones faltantes

6. **Implementar `apps/utils/network.py`**
   - `get_client_ip`, `get_user_agent`, `get_request_metadata`

7. **Completar `apps/utils/formatters.py`**
   - Agregar `format_phone`

8. **Implementar en `apps.access.permissions`**
   - `HasModuleAccess`

9. **Implementar en `apps.core.permissions`**
   - `HasServiceAccess`

10. **Implementar en `apps.core.mixins`**
    - `ServiceFilterMixin`

11. **Implementar en `apps.core.middleware.logging`**
    - `LoggingMiddleware`

### 🟢 BAJO — Lógica de tests

12. **Validators** — Ajustar lógica en 8 tests (formatos RUT, teléfono, service 800)
13. **Utils helpers** — Completar `DateUtils`, `NumberUtils`, `StringUtils`
14. **Fixture de usuario** — Corregir `test_user_data_fixture`
15. **Warnings de mocks** — Reordenar imports en conftest.py

---

## TESTS QUE SÍ PASAN (119)

Los tests que funcionan correctamente cubren las áreas que sí están
implementadas y alineadas:

```
✅ tests/unit/core/test_navigation_views.py       (navigation API)
✅ tests/unit/users/test_user_model.py            (User model)
✅ tests/unit/users/test_avatar_api.py            (avatar upload/delete)
✅ tests/unit/users/test_profile_api.py           (profile endpoints)
✅ tests/unit/users/test_user_settings_api.py     (settings endpoints)
✅ tests/unit/users/test_user_viewset.py          (user CRUD)
✅ tests/unit/ivr_legacy/test_ivr_app.py          (parcialmente)
✅ tests/unit/utils/test_validators.py            (parcialmente)
✅ tests/unit/utils_tests/test_validators.py      (parcialmente)
```

*Nota: 119 passed / (119+59) = 67% de los tests que logran correr.*

---

*Documento generado: 2026-03-21*
*Análisis basado en: pytest --continue-on-collection-errors*
*Output raw: /tmp/TEST_COMPLETO_v2_2_1.txt*

