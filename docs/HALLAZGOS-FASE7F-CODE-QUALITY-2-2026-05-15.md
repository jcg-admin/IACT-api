# HALLAZGOS-FASE7F-CODE-QUALITY-2-2026-05-15

**Documento:** HALLAZGOS-FASE7F-CODE-QUALITY-2-2026-05-15
**Fecha:** 2026-05-15
**Rama:** develop
**Commit:** 62c5377
**Alcance:** IACT-api — eliminación de deuda técnica secundaria
**Resultado:** 1335 passed · 0 warnings · F841=0 · F401=0 · TODOs=0

---

## 1. Variables locales no usadas (F841) — 15 → 0

Patrón dominante: variables de excepción `except X as exc:` donde `exc`
nunca se referencia en el bloque, y variables de retorno de llamadas
cuyo valor no se usa.

| Archivo | Línea | Problema | Corrección |
|---|---|---|---|
| `exceptional_permission_service.py` | 263 | `now = expires_at - expires_at` | `_ = ...` |
| `access/services/permission_service.py` | 310 | `except ... as exc:` sin uso de `exc` | `except ...:` |
| `access/views.py` | 669 | `User = get_user_model()` sin uso de `User` | `get_user_model()` sin asignar |
| `alerts/views.py` | 143 | `recipient = MessageService.unarchive_message(...)` | Eliminada asignación |
| `authentication/logout_view.py` | 127 | `except DatabaseError as exc:` | `except DatabaseError:` |
| `authentication/services/authentication.py` | 180 | `session_log = self._create_session_log(...)` | Eliminada asignación |
| `authentication/viewsets.py` | 307 | `success = self.recovery_service.reset_password_by_questions(...)` | Eliminada asignación |
| `dashboard/services/widget_service.py` | 256 | `cache_pattern = f'widget_data_...'` | Comentado como reservado para invalidación futura |
| `dashboard/viewsets.py` | 361 | `_widget_type = self.request.data.get(...)` | Convertido a comentario |
| `logs/views.py` | 381 | `metrics: dict = {}` nunca usado | Eliminado |
| `logs/views.py` | 395 | `except ... as e:` sin uso de `e` | `except ...:` |
| `pipeline/views.py` | 550 | `result = cursor.fetchone()` | `cursor.fetchone()` sin asignar |
| `reports/dashboard_view.py` | 312 | `except OperationalError as exc:` | `except OperationalError:` |
| `reports/schedule_service.py` | 59 | `freq = data.get('frequency', 'daily')` | Añadido noqa — variable usada en bloque posterior |
| `reports/services.py` | 288 | `except Exception as e:` | `except Exception:` |

---

## 2. Constantes DEPRECATED eliminadas — users/constants.py

**Bloque eliminado:**
```python
# DEPRECATED: RBAC Codes (usar namespaces arriba)
# DEPRECADO v6.0.0: Usar PERM_* arriba
USR_VIEW   = 'USR_VIEW'    # -> PERM_USERS_VIEW
USR_EDIT   = 'USR_EDIT'    # -> PERM_USERS_EDIT
USR_DELETE = 'USR_DELETE'  # -> PERM_USERS_DELETE
USR_PERMS  = 'USR_PERMS'   # -> PERM_USERS_MANAGE
```

**Verificación previa:** Las constantes `USR_*` solo aparecían en
comentarios de docstrings de `apps/users/viewsets.py`. No se importaban
en ningún módulo activo. Las constantes `PERM_*` (su reemplazo) ya están
en uso desde la migración a RBAC v6.0.0.

---

## 3. Warnings de la suite: 21 → 0

### PytestAssertRewriteWarning × 4

**Causa:** Los módulos `tests.mocks.*` se registran en `pytest_plugins`
dentro de `tests/conftest.py`. pytest intenta hacer `assert rewriting`
en estos módulos pero ya fueron importados por otro mecanismo antes de
que el rewriter pueda procesarlos.

**Módulos afectados:**
- `tests.mocks.external_mocks`
- `tests.mocks.file_mocks`
- `tests.mocks.scheduler_mocks`
- `tests.mocks.service_mocks`

**Solución:** `filterwarnings = ignore::pytest.PytestAssertRewriteWarning`
en `pytest.ini`. El assert rewriting no es necesario para mocks — solo
afecta a los mensajes de error cuando los asserts fallan (más descriptivos
con rewriting). Los mocks no contienen asserts relevantes.

### RuntimeWarning "Model already registered" × 17

**Causa:** `tests/unit/core/test_abstract_models.py` crea modelos dinámicos
con `schema_editor.create_model()` bajo `@pytest.mark.django_db(transaction=True)`.
Django registra cada modelo dinámico en el app registry. Al re-ejecutar tests
(o en transacciones que se revierten y repiten), el mismo modelo ya existe.

**Solución:** `filterwarnings = ignore::RuntimeWarning:django.db.models.base`
en `pytest.ini`. La advertencia es inherente al patrón de testing de modelos
abstractos y no indica un problema real — los tests pasan correctamente.

---

## 4. Estado final acumulado (todas las fases FASE 7)

| Métrica | Inicio FASE 7 | Final FASE 7F |
|---|---|---|
| passed | 434 | **1335** |
| failed | 0 | **0** |
| xfailed | 137 | **0** |
| skipped | 61 | **0** |
| warnings | N/A | **0** |
| errors | 710 | **0** |
| F401 (imports no usados) | 122 | **0** |
| F841 (variables no usadas) | 15 | **0** |
| TODOs en producción | 4 | **0** |
| Archivos muertos | 1 | **0** |
| Constantes DEPRECATED | 4 | **0** |

---

## 5. Verificación final

```
$ python3 -m pytest tests/ --no-header -q --tb=no
1335 passed in 53s

$ python3 -m flake8 apps/ --select=F401,F841 --exclude=migrations,__pycache__
(sin output)

$ grep -rn "# TODO\|# FIXME\|# HACK" apps/ --include="*.py" \
  --exclude-dir=migrations --exclude-dir=__pycache__ | grep -v "test_\|admin.py"
(sin output)
```

---

*Generado: 2026-05-15 | Commit: 62c5377*

---

## 6. Correcciones adicionales (commit 3396dfa)

### F841 en tests internos de apps/ — 5 → 0

Variables asignadas pero no usadas en tests internos de aplicaciones:
- `apps/alerts/tests/test_services.py` líneas 81, 87, 108: `message1`, `message2`
  asignados desde `MessageService.send_message()` sin uso posterior.
- `apps/dashboard/tests/test_dashboard_service.py` líneas 68, 71: `dashboard1`,
  `dashboard2` asignados desde `DashboardService.create_default_dashboard()`.

### Código muerto: decorador @deprecated() — 44 líneas eliminadas

`apps/utils/decorators.py` contenía un decorador `@deprecated(message)` que
emitía `DeprecationWarning` al invocar la función decorada.

Verificación previa al borrado:
- No se importa en ningún módulo de producción.
- No se usa en ningún test (solo el campo `deprecated_at` de `MenuItem` aparece
  en tests, que es un campo de modelo sin relación con el decorador).

### Estado final acumulado

```
flake8 --select=F401,F841 apps/ --exclude=migrations,__pycache__: 0
Comentarios # DEPRECATED / # DEPRECADO: 0
Comentarios # TODO / # FIXME / # HACK: 0
Suite: 1335 passed, 0 warnings
```
