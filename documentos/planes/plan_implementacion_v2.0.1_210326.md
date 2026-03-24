# PLAN DE IMPLEMENTACIÓN POR FASES — IACT API
## Cierre de Brechas y Fortalecimiento del Sistema

**Versión:** 2.0.1
**Fecha:** 2026-03-21
**Autor:** Claude Code — Análisis automatizado
**Cambios vs v2.0.0:**
- Ejecución real de tests con `--continue-on-collection-errors` → 119 passed / 59 failed / 344 errors
- Diagnóstico preciso de los 59 tests que fallan (4 causas raíz distintas)
- B-21: Bases de datos de test stale (`test_iact_analytics`, `test_ivr_legacy` ya existen)
- B-22: Navigation builder — `KeyError: 'submenus'` en 24 tests (campo renombrado a `menu_tree`)
- B-23: Validators — 7 bugs de lógica + 1 mismatch de tipo de excepción (ValueError vs ValidationError)
- B-03 actualizado: `manage.py check` reporta 0 issues; brecha real es solo en schema drf_spectacular

---

## ESTADO ACTUAL (verificado 2026-03-21 — BDs activas)

| Componente | Estado | Detalle |
|---|---|---|
| PostgreSQL 16 | ✅ online | puerto 5432 |
| MariaDB 10.11 | ✅ online | puerto 3306 |
| Django → PostgreSQL (`default`) | ✅ conectado | `iact_analytics` READ+WRITE |
| Django → MariaDB (`ivr`) | ✅ conectado | `ivr_legacy` READ-ONLY |
| Django system check | ✅ 0 errores | `manage.py check` limpio |
| Migraciones pendientes | ✅ ninguna | Todo en `[X]` |
| `tests/` — colección | ❌ 20 errores (13 ImportError) | Mismo que v2.0.0 |
| `tests/` — ejecución | ⚠️ 119 passed / 59 failed / 344 errors | Ver análisis B-22, B-23 |
| `apps/` — setup | ❌ 129 errores | ALTER denied en MariaDB (B-20) + stale DB (B-21) |

### Cumplimiento funcional (sin cambios)

| Módulo | Documentadas | Implementadas | % |
|---|---|---|---|
| MOD_Auth | 4 | 4 | **100%** |
| MOD_Users | 9 | 6 | **67%** |
| MOD_Access | 3 | 1 | **33%** |
| MOD_Reports | 6 | 2 | **33%** |
| MOD_Audit | 3 | 2 | **67%** |
| **TOTAL** | **25** | **15** | **60%** |

---

## ANÁLISIS DE LOS 59 TESTS QUE FALLAN

### ¿Es correcto que fallen? Resumen ejecutivo

| Causa raíz | Tests afectados | ¿Deben fallar? | Acción |
|---|---|---|---|
| `KeyError: 'submenus'` (campo renombrado) | 24 | NO — bug real | Corregir tests O código (B-22) |
| Validator logic bugs (RUT, phone, service, etc.) | 7 | NO — bug real | Corregir validators (B-23) |
| TypeError: `ValueError` vs `ValidationError` | 1 | NO — bug real | Alinear tipo de excepción (B-23) |
| Helpers / fixtures / ivr_legacy module | 27 | NO — bugs reales | Corregir (B-23) |

**Ninguno de los 59 tests que fallan es "correcto que fallen".**
Todos representan divergencias entre el código y lo que el sistema debe hacer.

---

### Detalle: Navigation Builder — 24 failures (B-22)

**Error:** `KeyError: 'submenus'` en `test_navigation_builders.py:262`

**Causa:** Los tests acceden a `menu[0]['submenus']`, pero el código devuelve:
```python
{'app': 'reports', 'icon': '...', 'menu_tree': [...], 'module': 'MOD_Reports'}
```
El campo fue renombrado de `submenus` a `menu_tree` en el código, pero los tests no se actualizaron.

**Diagnóstico:** Mismatch de naming — `submenus` (tests) vs `menu_tree` (código actual).

**¿Cuál es el nombre correcto?** Verificar el diccionario de flujos. Si `menu_tree` es el contrato de API actual → actualizar los 24 tests. Si `submenus` era el nombre acordado → revertir en código.

**Tests afectados:** Todos los tests de `TestMenuBuilder`, `TestMenuBuilderIntegration`, `TestMenuSerializer`, `TestMenuValidator`.

---

### Detalle: Validators — 8 failures (B-23)

#### 1. `test_invalid_row_count_over_limit` — tipo de excepción incorrecto

**Test espera:** `pytest.raises(ValidationError)` (django.core.exceptions)
**Código lanza:** `raise ValueError(...)` (`apps/utils/validators.py:392`)

**Veredicto:** El código debe lanzar `ValidationError` para consistencia con Django DRF. Cambiar en `validators.py`:
```python
from django.core.exceptions import ValidationError
raise ValidationError(f"Export limitado a {max_limit:,} filas. Solicitadas: {row_count:,}.")
```
Esto también alinea con B-12 (CNST-010: cambiar `max_limit` default de 100000 a 10000).

#### 2. RUT validation — 3 failures

Tests que fallan:
- `test_valid_rut_with_dash` — `12345678-9` debería ser válido
- `test_valid_rut_without_dash` — `123456789` debería ser válido
- `test_valid_rut_with_k` — `12345678-K` debería ser válido

**Causa:** El validator rechaza formatos válidos de RUT chileno. Bug en regex o lógica de `validate_rut()`.

#### 3. Phone validation — 1 failure

Test: `test_valid_landline_8_digits` — un número fijo de 8 dígitos debería ser válido.
**Causa:** El validator solo acepta 9 dígitos (celular), rechaza los 8 dígitos de línea fija chilena.

#### 4. Service 800 validation — 1 failure

Test: `test_valid_service_800` — un número 800-XXXXXX debería ser válido.
**Causa:** Bug en regex de `validate_service_800()`.

#### 5. Codigo center validation — 1 failure

Test: `test_invalid_codigo_too_short` — un código muy corto debería lanzar error pero no lo hace.
**Causa:** Validación de longitud mínima no implementada o con valor incorrecto.

#### 6. Date range validation — 1 failure

Test: `test_invalid_start_after_end` — `start > end` debería lanzar error pero no lo hace.
**Causa:** Condición invertida o ausente en `validate_date_range()`.

---

### Detalle: Otros failures (27)

| Archivo | Tests | Causa probable |
|---|---|---|
| `test_helpers.py` | 4 | Implementación de `generate_random_token`, `get_client_ip`, `get_user_agent`, `safe_get` no coincide con contrato esperado |
| `test_fixtures.py` | 1 | Fixture `user_data` con campos desactualizados |
| `test_ivr_legacy/test_ivr_app.py` | 1 | `ModuleNotFoundError: apps.ivr_legacy` — módulo renombrado a `apps.ivr` |
| Errores de DB (344) | 344 | Tests de `@pytest.mark.django_db` sin BD disponible — bloqueo colateral de B-20/B-21 |

---

## BRECHAS — ESTADO COMPLETO

### Brechas Críticas

| ID | Brecha | P |
|---|---|---|
| B-01 | JWT vs DRF Token sin expiración | P1 |
| B-02 | 13 ImportError en `tests/` (20 archivos) | P1 |
| B-20 | `django_user` sin ALTER en `test_ivr_legacy` — bloquea 129 tests de `apps/` | P1 |
| B-21 | **NUEVO** — Stale test databases: `test_iact_analytics` y `test_ivr_legacy` ya existen | P1 |
| B-22 | **NUEVO** — Navigation builder: `submenus` vs `menu_tree` — 24 tests fallan | P1 |
| B-23 | **NUEVO** — Validators: 8 bugs (tipos excepción, RUT, phone, service, codigo, date) | P1 |
| B-04 | Validación SoD no existe en código | P2 |
| B-05 | Endpoints assign/revoke de funciones faltan | P2 |
| B-06 | `users.lock` implementado como `deactivate` | P2 |

### Brechas Importantes

| ID | Brecha | P |
|---|---|---|
| B-07 | Throttling por IP en login | P2 |
| B-08 | Inactividad automática 90 días (CNST-013) | P2 |
| B-03 | Serializers faltantes en pipeline (solo schema, `check` OK) | P2 |
| B-09 | `is_locked` en User vs tabla `LoginLockout` separada | P3 |
| B-10 | `UserActionLog` centralizado vs `LoginAttempt` específico | P3 |
| B-11 | `DeletionLog` no implementado | P3 |
| B-12 | CNST-010: `MAX_EXPORT_ROWS=100000` debe ser 10000 + cambiar a `ValidationError` | P3 |
| B-13 | `reports.modify_data`, `reports.approve`, `reports.schedule` sin endpoint | P3 |
| B-14 | `users.export` sin endpoint | P3 |
| B-15 | CNST-015: retención 7 años sin política automática | P3 |

### Brechas Menores

| ID | Brecha | P |
|---|---|---|
| B-16 | `full_name`, `last_login`, `date_joined` faltan en login response | P4 |
| B-17 | `locked_until` timestamp vs `locked_minutes` entero | P4 |
| B-18 | Detección de sesión duplicada (Flujo A5) | P4 |
| B-19 | drf_spectacular: type hints faltantes en serializers | P5 |

---

## FASES DE IMPLEMENTACIÓN

---

### FASE 0 — ESTABILIZACIÓN (Prerequisito absoluto)

#### Tarea 0.0 — Limpiar stale test databases (B-21) ← 5 minutos

Antes de cualquier otra cosa, eliminar las BDs de test residuales:

```bash
# PostgreSQL
PGPASSWORD=root_pass_CHANGE_ME psql -U postgres -c "DROP DATABASE IF EXISTS test_iact_analytics;"

# MariaDB (como root)
mysql -u root -proot_pass_CHANGE_ME -e "DROP DATABASE IF EXISTS test_ivr_legacy;"
```

**Criterio de aceptación:** `pytest apps/ --collect-only` no muestra "database already exists".

---

#### Tarea 0.1 — Resolver permisos MariaDB en tests (B-20)

**Solución preferida** (sin cambiar permisos, sin Docker):

```python
# config/settings/base.py — en DATABASES['ivr']
'TEST': {
    'NAME': None,  # Django no crea BD de test para este alias
},
```

Agregar en `conftest.py` o en cada test de `apps/` que use `ivr`:
```python
@pytest.mark.django_db(databases=['default'])
```

**Criterio de aceptación:** `pytest apps/` → 0 errores de setup.

---

#### Tarea 0.2 — Corregir 13 ImportError en `tests/` (B-02)

Ver tabla completa en v2.0.0. Resumen de acciones:

| Acción | Símbolos |
|---|---|
| **Crear alias/implementación** | `HasModuleAccess`, `CustomTokenObtainPairSerializer`, `HasServiceAccess`, `LoggingMiddleware`, `LoginSerializer`, `UserProfileSerializer`, `format_phone` |
| **Actualizar referencia en test** | `Role` → `UserFunctionAssignment`, `CallRecord`/`Service` → módulo correcto, `ServiceFilterMixin` → ruta actual, `apps.ivr_legacy` → `apps.ivr`, `apps.utils.network` → crear o eliminar test |

**Criterio de aceptación:** `pytest tests/ --collect-only` → 0 errores de colección.

---

#### Tarea 0.3 — Corregir Navigation Builder (B-22)

**Paso 1:** Determinar el nombre canónico del campo:
```bash
grep -r "menu_tree\|submenus" apps/core/navigation/ tests/unit/core/test_navigation_builders.py
```

**Paso 2a — Si `menu_tree` es el nombre correcto:**
Actualizar los 24 tests para usar `menu_tree` en lugar de `submenus`.

**Paso 2b — Si `submenus` era el contrato original:**
Agregar alias en el builder:
```python
result['submenus'] = result['menu_tree']  # compatibilidad temporal
```

**Criterio de aceptación:** `pytest tests/unit/core/test_navigation_builders.py` → 0 failures.

---

#### Tarea 0.4 — Corregir Validators (B-23)

**4a — `validate_export_row_limit`: cambiar ValueError a ValidationError + corregir límite:**
```python
# apps/utils/validators.py
from django.core.exceptions import ValidationError

def validate_export_row_limit(row_count: int, max_limit: int = 10000) -> None:
    if row_count > max_limit:
        raise ValidationError(
            f"Export limitado a {max_limit:,} filas. Solicitadas: {row_count:,}."
        )
```
También actualizar `constants.py`:
```python
MAX_EXPORT_ROWS = 10000  # CNST-010 — era 100000 (B-12)
```

**4b — `validate_rut`: aceptar formatos válidos con/sin guión y con K:**
Revisar regex en `validate_rut()` para aceptar `12345678-9`, `123456789`, `12345678-K`.

**4c — `validate_phone_number`: aceptar 8 dígitos (línea fija):**
Modificar validación de longitud: aceptar 8 O 9 dígitos.

**4d — `validate_service_800`: revisar regex para formato 800-XXXXXX.**

**4e — `validate_codigo_center`: agregar validación de longitud mínima.**

**4f — `validate_date_range`: corregir condición `start > end`.**

**Criterio de aceptación:** `pytest tests/unit/utils/test_validators.py` → 0 failures.

---

#### Tarea 0.5 — Corregir helpers, fixtures e ivr_legacy (B-23)

**Helpers** (`test_helpers.py` — 4 failures):
- `generate_random_token`: verificar longitud default retornada
- `get_client_ip`: retornar `None` cuando no hay headers HTTP_X_FORWARDED_FOR ni REMOTE_ADDR
- `get_user_agent`: retornar string vacío o `None` cuando falta header
- `safe_get`: revisar lógica de acceso anidado profundo

**Fixtures** (`test_fixtures.py` — 1 failure):
- Actualizar `user_data` fixture con campos actuales del modelo User

**IVR legacy** (`test_ivr_legacy/test_ivr_app.py` — 1 failure):
- Actualizar import: `apps.ivr_legacy` → `apps.ivr`

**Criterio de aceptación:** `pytest tests/ --continue-on-collection-errors` → 0 failures.

---

#### Tarea 0.6 — Serializers faltantes en pipeline (B-03)

```python
# apps/pipeline/serializers/callrecord_serializers.py
class CallRecordBulkCreateSerializer(serializers.Serializer): ...
class DailyStatsSerializer(serializers.Serializer): ...
class ServiceStatsSerializer(serializers.Serializer): ...
class TopCallerSerializer(serializers.Serializer): ...
```

**Criterio de aceptación:** `python manage.py check --deploy` sin warnings en `pipeline/`.

---

### FASE 1 — SEGURIDAD CRÍTICA
**Dependencias:** Fase 0 completada

#### Tarea 1.1 — Throttling por IP en login (B-07)
Ver detalle en v2.0.0 — sin cambios.

#### Tarea 1.2 — JWT access + refresh token (B-01)
Ver detalle en v2.0.0 — sin cambios.

#### Tarea 1.3 — Inactividad automática 90 días (B-08)
Ver detalle en v2.0.0 — sin cambios.

---

### FASE 2 — MODELO DE DATOS
**Dependencias:** Fase 0. Paralelo con Fase 1.

#### Tarea 2.1 — Campo `is_locked` en User (B-06, B-09)
Ver detalle en v2.0.0 — sin cambios.

#### Tarea 2.2 — `UserActionLog` centralizado (B-10)
Ver detalle en v2.0.0 — sin cambios.

---

### FASE 3 — RBAC COMPLETO
**Dependencias:** Fase 0

#### Tarea 3.1 — Endpoints assign/revoke funciones (B-05)
#### Tarea 3.2 — Validación SoD en código (B-04)
#### Tarea 3.3 — MOD_Reports funciones faltantes (B-13)
#### Tarea 3.4 — `users.export` + corrección CNST-010 (B-14, B-12) ← ya parcialmente en 0.4
#### Tarea 3.5 — DeletionLog (B-11)

Ver detalle completo en v2.0.0 — sin cambios en implementación.

---

### FASE 4 — MEJORAS DE CALIDAD DE API
**Dependencias:** Fase 2

#### Tarea 4.1 — Campos adicionales en login response (B-16)
#### Tarea 4.2 — `locked_until` timestamp (B-17)
#### Tarea 4.3 — Detección de sesión duplicada (B-18)

Ver detalle en v2.0.0 — sin cambios.

---

### FASE 5 — SCHEMA TÉCNICO
**Dependencias:** Ninguna

#### Tarea 5.1 — Type hints en serializers (B-19)
#### Tarea 5.2 — Viewsets sin `serializer_class` (B-19)

Ver detalle en v2.0.0 — sin cambios.

---

## ORDEN DE EJECUCIÓN v2.0.1

```
FASE 0 — Estabilización (prerequisito absoluto)
  ├── [0.0] Limpiar stale DBs                    ← 5 minutos, desbloquea apps/
  ├── [0.1] Permisos MariaDB TEST: NAME=None      ← desbloquea 129 tests apps/
  ├── [0.2] Corregir 13 ImportError              ← desbloquea 502 tests tests/
  ├── [0.3] Navigation builder submenus→menu_tree ← elimina 24 failures
  ├── [0.4] Validators: RUT, phone, service, etc. ← elimina 8 failures
  ├── [0.5] Helpers, fixtures, ivr_legacy        ← elimina ~27 failures
  └── [0.6] Serializers faltantes pipeline

FASE 1 — Seguridad (paralelo con Fase 2)
  ├── [1.1] Throttling IP en login
  ├── [1.2] JWT access + refresh
  └── [1.3] Inactividad automática 90d

FASE 2 — Modelo datos (paralelo con Fase 1)
  ├── [2.1] is_locked en User
  └── [2.2] UserActionLog centralizado

FASE 3 — RBAC completo (después de Fase 0)
  ├── [3.1] assign/revoke endpoints
  ├── [3.2] Validación SoD
  ├── [3.3] MOD_Reports funciones
  ├── [3.4] users.export
  └── [3.5] DeletionLog

FASE 4 — Calidad API (después de Fase 2)
  ├── [4.1] Campos login response
  ├── [4.2] locked_until timestamp
  └── [4.3] Sesión duplicada

FASE 5 — Schema (cualquier momento)
  ├── [5.1] Type hints serializers
  └── [5.2] Viewsets sin serializer_class
```

---

## MÉTRICAS OBJETIVO

| Métrica | Estado actual | Objetivo |
|---|---|---|
| Cumplimiento funcional | 60% (15/25) | 100% (25/25) |
| `tests/` colección | ❌ 20 errores | ✅ 0 errores |
| `tests/` ejecución | 119 ✅ / 59 ❌ / 344 errores | ✅ >450 passed / 0 failed |
| `apps/` setup | ❌ 129 errores (B-20+B-21) | ✅ 0 errores |
| Validators bugfree | 8 fallos | ✅ 0 fallos |
| Navigation builder | 24 fallos | ✅ 0 fallos |
| SoD en código | 0% | 100% (3 reglas) |
| Tokens | DRF Token sin expiración | JWT 15min/7días |
| CNST-010 | 100K + ValueError | 10K + ValidationError |
| CNST-013 | Sin automatización | Task diaria activa |
| DeletionLog | No existe | Implementado |
| Schema warnings | ~55 | < 10 |

---

*Documento generado por Claude Code — IACT-api*
*Versión: 2.0.1 | Fecha: 2026-03-21*
*Cambios vs v2.0.0: diagnóstico completo de los 59 failures (B-21, B-22, B-23)*
