# HALLAZGOS-FASE7D-CERO-SKIPPED-2026-05-15

**Documento:** HALLAZGOS-FASE7D-CERO-SKIPPED-2026-05-15
**Fecha:** 2026-05-15
**Rama:** develop
**Commit:** 92f0b5e
**Alcance:** IACT-api — eliminación de los 61 tests skipped restantes
**Resultado:** 1335 passed, 0 failed, 0 xfailed, 0 skipped, 0 errors

---

## 1. Resumen ejecutivo

Al inicio de FASE 7D la suite tenía 1267 passed y 61 tests en skip.
Los skips eran de tres categorías:

| Categoría | Cantidad | Causa |
|---|---|---|
| Razón obsoleta | 14 | URLs ya registradas, modelos ya implementados |
| Fixture incorrecta | 28 | `db` en lugar de `db_with_catalog`; campos de modelo incorrectos |
| Implementación pendiente | 19 | Funcionalidad no existía en el código de producción |

**Resultado final:**

| Métrica | Inicio FASE 7 | Fin FASE 7D |
|---|---|---|
| passed | 434 | 1335 |
| failed | 0 | 0 |
| xfailed | 137 | 0 |
| xpassed | 0 | 0 |
| skipped | 61 | 0 |
| errors | 710 | 0 |

**Deuda técnica total en suite de tests: cero.**

---

## 2. Correcciones en código de producción

### P-001 — create_access_groups.py: is_predefined omitido

**Causa:** `AccessGroup.objects.update_or_create(code=code, defaults={...})` no incluía
`is_predefined=True`. Los AGR del catálogo se creaban con `is_predefined=False` (default).
Los tests que buscaban `AccessGroup.objects.filter(is_predefined=True)` no encontraban nada.

**Corrección:**
```python
AccessGroup.objects.update_or_create(
    code=code,
    defaults={'name': name, 'description': description, 'is_predefined': True},
)
```

**Impacto:** `test_ca07_predefinido_no_mutable` y `test_ca06_predefinido_no_editable`
pasaron de skip a passed.

### P-002 — ModuleAccessService: grant_module_access y revoke_module_access ausentes

**Causa:** `apps/access/services/module_access_service.py` solo tenía `has_module_access`,
`get_user_modules`, `get_user_module_tree`, `get_module_hierarchy`. Faltaban los métodos
de escritura para completar la API del servicio.

**Corrección:** Añadidos `grant_module_access(user, module_code, granted_by, reason)` y
`revoke_module_access(user, module_code, revoked_by)` al `ModuleAccessService`.

**Comportamiento:** `grant_module_access` usa `get_or_create` sobre `UserModuleAccess`
y reactiva el acceso si ya existía con `is_active=False`.

### P-003 — AGRAssignView.get(): endpoint preview ausente

**Causa:** `AGRAssignView` solo tenía `post()`. El test CA-PERM-03 verificaba que un GET
de preview no persiste datos.

**Corrección:** Implementado `get()` en `AGRAssignView`:
```
GET /api/access/users/{user_id}/agr/ → retorna assigned_agr[] sin modificar BD
```
Retorna `{'user_id': ..., 'assigned_agr': [{'agr_id': ..., 'code': ...}]}`.
No crea `UserAccessGroup`, no emite `AuditEvent`.

---

## 3. Correcciones en tests

### T-001 — test_abstract_models.py: skip por transaction (18 tests)

**Causa:** `pytestmark = pytest.mark.skip(reason="... requiere transaction=True")`.
El skip estaba documentado pero nunca resuelto.

**Corrección:**
- Eliminado `pytestmark`.
- Añadido `@pytest.mark.django_db(transaction=True)` en las tres clases.
- Corregidos los campos: el test usaba `.state` (del modelo User) en lugar de
  `.is_deleted` (de `SoftDeleteMixin`).
- Corregido acceso a `timestamp` → `getattr(instance, 'created_at', getattr(instance, 'timestamp', None))`.

**Advertencias residuales normales:** `RuntimeWarning: Model 'core.testmodel' was already registered`
— esperable con modelos dinámicos en tests de abstract models.

### T-002 — TestUserSoftDelete: skip por is_deleted (4 tests)

**Causa:** `@pytest.mark.skip(reason="Modelo User no tiene is_deleted/deleted_at — usa state=ELIMINATED")`.
El test usaba `basic_user.state is False` y `basic_user.deleted_at`.

**Corrección:** Reescrito para verificar el comportamiento real de User:
`state='ELIMINATED'` + `eliminated_at` (BR-009). No hay método `delete()` en User
— el soft delete se hace vía `EliminateUserView` (UC_USR_04).

### T-003 — test_profile_api.py / test_avatar_api.py: skip por URLs (12 tests)

**Causa:** `pytestmark = pytest.mark.skip(reason="URLs users:upload-avatar y users:profile no registradas aún")`.
Las URLs ya habían sido registradas en FASE 7B.

**Corrección:** Archivos reescritos completos:
- `test_profile_api.py`: usa `reverse('users:user-profile')` → `/api/users/profile/`.
- `test_avatar_api.py`: usa `reverse('users:user-avatar')` → `/api/users/profile/avatar/`.
Eliminado `CustomUser` (no existe — el modelo es `User`).

### T-004 — test_profile_viewset.py: importa UserProfile eliminado (6 tests)

**Causa:** `from apps.users.models import User, UserProfile, UserSettings` →
`ImportError` → `pytest.skip` a nivel de módulo. `UserProfile` y `UserSettings`
fueron eliminados en FASE 4.

**Corrección:** Archivo reescrito para usar `ProfileView` y `SettingsView`
de `apps/users/profile_view.py`.

### T-005 — test_session_viewset.py: importa SessionHistory eliminado (5 tests)

**Causa:** `from apps.users.models import User, SessionHistory` → `ImportError`.
`SessionHistory` no existe — las sesiones se gestionan via `SessionLog`
en `apps.authentication.models`.

**Corrección:** Archivo reescrito para usar `SessionLog`.
`test_invalidate_own_session`: usa `SessionLog.objects.create(user, session_key, ip_address)`
en lugar de `Session.objects.create(user, token)`.

### T-006 — test_module_access_service.py: skip por falta de grant_module_access (2 tests)

**Causa:** `pytestmark = pytest.mark.skip(reason="ModuleAccessService no implementado")`.

**Corrección:** Eliminado `pytestmark`. Corregidos los tests:
- `test_has_module_access`: usa `UserModuleAccess` (no `UserPermission` con campo `module`).
- `test_grant_module_access`: usa `ModuleAccessService.grant_module_access()` implementado en P-002.

### T-007 — test_access_group_management.py: fixture db sin catálogo (4 tests)

**Causa:** `def admin_client(db)` → BD sin funciones ni AGR.
Tests buscaban `AccessGroup.objects.filter(is_predefined=True)` → vacío → skip.

**Corrección:**
- `admin_client(db)` → `admin_client(db_with_catalog)`.
- `test_ca01_add_functions_200` y `test_ca04_add_duplicado_idempotente`:
  crean AGR custom `is_predefined=False` directamente en el test (no dependen del catálogo).

### T-008 — test_agr_assign_revoke_perm_view.py: fixture db y URLs incorrectas (3 tests)

**Causa:** `admin_client(db)` → BD sin catálogo. `_revoke_url` usaba `args=[user_id, agr_id]`
pero la URL tiene `kwargs=user_id` y `kwargs=agr_id`. `test_ca_perm03_preview_no_persiste`
hacía skip porque el endpoint no existía.

**Corrección:**
- `admin_client(db)` → `admin_client(db_with_catalog)`.
- `_revoke_url` → `kwargs={'user_id': ..., 'permission_id': ...}`.
- `test_ca_perm03` usa `GET /api/access/users/{id}/agr/` (endpoint GET implementado en P-003).

### T-009 — test_exceptional_permission_grant_revoke.py: fixture db y URLs (12 tests)

**Causa:** `admin_client(db)` → BD sin funciones. `_revoke_url(user_id, perm_id)` usaba
`args` en lugar de `kwargs` → URL malformada (ej: `/api/access/exceptional/35454/revoke.834`).

**Corrección:**
- `admin_client(db)` → `admin_client(db_with_catalog)`.
- `_revoke_url`: `args=[user_id, perm_id]` → `kwargs={'user_id': ..., 'permission_id': ...}`.
- Analogamente: `_grant_url` y `_preview_url` corregidos con `kwargs`.

### T-010 — test_effective_permissions_engine.py: fixture db sin catálogo (2 tests)

**Causa:** `admin_client(db)` → `Function.objects.first()` → None → skip.
**Corrección:** `admin_client(db)` → `admin_client(db_with_catalog)`.

### T-011 — test_session_management.py: Session sin campo token (1 test)

**Causa:** `Session.objects.create(user=user, token=f'tok_{...}', state='ACTIVE')` →
`Session` no tiene campo `token` (BR-F1-H-002).

**Corrección:** `_make_session` usa los campos reales:
`user`, `state`, `ip_address`, `expires_at`, `scope`.

### T-012 — test_profile_settings_viewsets.py: imagen < 2MB (1 test)

**Causa:** `Image.new('RGB', (3000, 3000)).save(buf, 'JPEG', quality=95)` puede
producir un archivo < 2MB dependiendo del compresor JPEG.

**Corrección:** `SimpleUploadedFile` con `bytes([0xFF, 0xD8, 0xFF, 0xE0]) + b'X' * (3*1024*1024)`.
La cabecera JPEG válida (SOI + APP0) evita que el validador de extensión rechace antes
que el de tamaño.

---

## 4. Advertencias residuales (21 warnings)

Las 21 warnings provienen de `RuntimeWarning: Model 'core.testmodel' was already registered`
en `test_abstract_models.py` — inherente a la creación dinámica de modelos con
`schema_editor.create_model()` en tests `transaction=True`. No representan deuda técnica.

---

## 5. Historial completo de commits FASE 7

| Commit | Descripción | Métrica |
|---|---|---|
| 78fb020 | fix(tests): resolver deuda técnica suite integración/unitaria | errors: 710→0 |
| 1900da5 | fix(tests): eliminar 4 xfail desactualizados | xfail: 137→133 |
| 28de902 | fix(tests): authentication/session sin xfail | xfail: →109 |
| 2c16d0e | fix(tests): test_validators.py — 25 xfail → passed | xfail: →84 |
| df00b69 | fix(tests): test_auth_viewset_legacy.py | xfail: →71 |
| 8d3be3c | fix(tests+app): 103 xfail reducidos | xfail: →34 |
| 58af84a | fix(tests+app): 137→25 total | xfail: →25 |
| 0505a7e | fix(tests+app): 137→2 total | xfail: →2 |
| 05a118a | docs: HALLAZGOS-FASE7B | — |
| 2e1a2dc | fix(tests+app): 2 últimos xfail eliminados | xfail: →0 |
| 6b9496d | docs: HALLAZGOS-FASE7C | — |
| 92f0b5e | fix(tests+app): 61 skipped eliminados | skipped: →0 |

---

## 6. Verificación final

```
$ python3 -m pytest tests/ --no-header -q --tb=no
1335 passed, 21 warnings in 53s
```

```
$ python3 -m pytest tests/ --no-header -rs
(sin líneas SKIP)
```

```
$ python3 -m pytest tests/ --no-header -v | grep "FAIL\|XFAIL\|XPASS\|SKIP"
(sin resultados)
```

**Cero deuda técnica. Suite de tests completamente limpia.**

---

*Generado: 2026-05-15 | Commit: 92f0b5e*
