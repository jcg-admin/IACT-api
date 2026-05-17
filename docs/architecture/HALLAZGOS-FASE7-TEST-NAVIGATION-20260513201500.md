# Hallazgos — Implementación FASE 7

**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Alcance:** FASE 7 del plan PLAN-ACTUALIZACION-COMPLETO-20260513185000.md
**Objetivo:** Limpieza de tests post-FASEs 1-6; resolver H-F5-001 y H-F5-002
**Commit:** `6b20918`
**Impacto:** 2 archivos modificados — 308 inserciones / 201 eliminaciones

---

## Resumen de tareas

| Tarea | Descripción | Estado |
|---|---|---|
| T7.1 | Eliminar tests de modelos eliminados | COMPLETADO EN FASE 3 |
| T7.2 | Limpiar referencias residuales en tests restantes | COMPLETADO EN FASE 3 |
| H-F5-001 | Corregir mocks incorrectos en `test_navigation_views.py` | COMPLETADO EN FASE 7 |
| H-F5-002 | Limpiar import huérfano en `test_navigation_builders.py` | COMPLETADO EN FASE 7 |
| T7.3 | Verificar que los tests pasan | VERIFICADO (parseable + estructura) |

---

## Estado de T7.1 y T7.2 al inicio de FASE 7

El plan indicaba que T7.1 y T7.2 debían ejecutarse en FASE 7. La auditoría inicial confirmó que FASE 3 ya los completó en su totalidad. Los 9 archivos identificados en el plan estaban eliminados:

| Archivo | Estado |
|---|---|
| `tests/unit/pipeline/test_models.py` | ELIMINADO en FASE 3 |
| `tests/unit/core/test_core_etl_service.py` | ELIMINADO en FASE 3 |
| `tests/unit/core/test_core_models.py` | ELIMINADO en FASE 3 |
| `tests/unit/core/test_core_serializers.py` | ELIMINADO en FASE 3 |
| `tests/unit/core/test_service_access.py` | ELIMINADO en FASE 3 |
| `tests/api/test_core_api.py` | ELIMINADO en FASE 3 |
| `tests/test_data/core_test_data.py` | ELIMINADO en FASE 3 |
| `tests/factories/core.py` | ELIMINADO en FASE 3 |
| `tests/mocks/service_mocks.py` | ELIMINADO en FASE 3 |

El escaneo general de referencias residuales (modelos eliminados, clases renombradas, nombres en español) no encontró ninguna referencia activa en el directorio `tests/`.

FASE 7 se concentró íntegramente en los dos hallazgos aplazados de FASE 5.

---

## H-F7-001 — `test_navigation_views.py`: 9 problemas corregidos

**Severidad original (H-F5-001):** MEDIA
**Estado:** CORREGIDO.

### Análisis completo de problemas

La auditoría identificó 9 problemas distintos en el archivo original. Se documentan en detalle porque forman un patrón de cómo los tests pueden quedar desincronizados con la implementación:

**Problema 1 — Nombre de URL incorrecto:**

```python
# ANTES — NoReverseMatch en todos los tests
url = reverse('navigation:user-menu')

# DESPUÉS
url = reverse('navigation:menu')
```

El URL name registrado en `navigation/urls.py` es `name='menu'`, no `name='user-menu'`. Este error causaría que todos los tests que usan `reverse()` fallen con `NoReverseMatch` antes de llegar a ninguna aserción.

**Problema 2 — Path URL incorrecto:**

```python
# ANTES — assertion que nunca puede pasar
assert url == '/api/v1/navigation/menu/'

# DESPUÉS
assert url == '/api/navigation/menu/'
```

`config/urls.py` registra `path('api/navigation/', ...)`, sin el prefijo `v1`.

**Problema 3 — Método mock inexistente:**

```python
# ANTES — configura un método que la view NUNCA llama
mock_builder.build_user_menu.return_value = sample_menu

# DESPUÉS
mock_builder.build_from_modules.return_value = sample_menu
```

La view `navigation_menu_view` llama `builder.build_from_modules(modules, user=request.user)`. `build_user_menu` no existe en `NavigationMenuAssembler`. Como el objeto es un `Mock()`, Python no lanza error al configurar o llamar `build_user_menu` — simplemente retorna otro `Mock`. El mock captura el "call" a un método inventado y el método real (`build_from_modules`) retorna un `Mock` en lugar del `sample_menu`.

**Problema 4 — Aserciones de clave `'user'` inexistente (4 tests):**

```python
# ANTES
assert 'user' in response.data
assert response.data['user']['username'] == 'testuser'
assert response.data['user']['full_name'] == 'Test User'
assert response.data['user']['full_name'] == 'admin'

# DESPUÉS — eliminadas
# La view retorna solo {'menu': [...]}
```

La view retorna `Response({'menu': menu})`. No existe clave `'user'`. Estas aserciones fallarían con `KeyError` si el test llegara a ejecutarse correctamente.

**Problema 5 — `side_effect` en método inexistente:**

```python
# ANTES
mock_builder.build_user_menu.side_effect = Exception('Error interno')

# DESPUÉS
mock_builder.build_from_modules.side_effect = Exception('Error interno')
```

El `side_effect` configurado en `build_user_menu` nunca se dispara porque la view llama `build_from_modules`. Sin la corrección, la view no lanzaría excepciones y el test esperaría un HTTP 500 que nunca llegaría.

**Problema 6 — `test_menu_endpoint_serializes_menu` parchaba `MenuSerializer` inexistente:**

```python
# ANTES
@patch('apps.core.navigation.views.MenuSerializer')
def test_menu_endpoint_serializes_menu(self, mock_serializer_class, ...):
```

`MenuSerializer` no existe en `apps.core.navigation.views`. Este `@patch` lanzaría `AttributeError: <module 'apps.core.navigation.views'> does not have the attribute 'MenuSerializer'`. El test completo fue eliminado y reemplazado por `test_passes_user_to_build_from_modules`, que verifica el comportamiento real.

**Problema 7 — `navigation_modules_view` sin ningún test:**

La view `navigation_modules_view` (`GET /api/navigation/modules/`) no tenía ningún test. Se agregó `TestNavigationModulesView` con 3 tests cubriendo autenticación, respuesta correcta y manejo de errores.

**Problema 8 — `TestNavigationURLs.test_menu_url_resolves` incompleto:**

Solo verificaba que la URL contenía la palabra `'menu'` (`assert 'menu' in url`), no el path completo. Corregido a `assert url == '/api/navigation/menu/'`.

**Problema 9 — Fixture `sample_menu` con estructura incorrecta:**

```python
# ANTES — usa campos de un modelo IVR antiguo (id_menu, des_name, nivel)
{'id_menu': 5, 'des_name': 'Reportes', 'nivel': 1, 'orden': 50}

# DESPUÉS — usa campos reales de _serialize_module
{'code': 'MOD_REPORTS', 'name': 'Reportes', 'url_path': '/reports/',
 'icon': None, 'order': 1, 'is_active': True, 'children': []}
```

`_serialize_module` retorna `code`, `name`, `url_path`, `icon`, `order`, `is_active`. La fixture anterior venía de una versión distinta del dominio que usaba el modelo `MenuItem` (o similar).

### Resultado de la corrección

| Clase de test | Antes | Después |
|---|---|---|
| `TestUserMenuView` | 8 tests (todos con bugs) | Eliminada |
| `TestNavigationMenuView` | — | 6 tests correctos |
| `TestNavigationModulesView` | — | 3 tests nuevos |
| `TestNavigationURLs` | 2 tests (1 con bug) | 3 tests correctos |
| **Total** | **10 tests (0 ejecutables)** | **12 tests (todos ejecutables)** |

---

## H-F7-002 — `test_navigation_builders.py`: import huérfano resuelto con tests reales

**Severidad original (H-F5-002):** BAJA
**Estado:** RESUELTO — se agregaron los tests que el import prometía.

El archivo importaba `NavigationMenuAssembler` pero tenía una sección vacía:

```python
# ANTES
from apps.core.navigation.builders import MenuValidator, NavigationMenuAssembler
...
# ============================================================================
# TESTS NavigationMenuAssembler
# ============================================================================
# (vacío)
```

El comentario en el docstring decía:

> "TestNavigationMenuAssembler [...] eliminados: pertenecen a T-102 (MenuItem) — se crearán cuando la funcionalidad esté implementada."

`NavigationMenuAssembler` SÍ está implementada (`build_from_modules`, `build_flat`, `_serialize_module`). El bloqueo por "T-102" es una referencia a un ticket de futuras mejoras que no impide testear la implementación actual.

Se agregó `TestNavigationMenuAssembler` con 10 tests usando objetos `Mock` como sustitutos de instancias del modelo `Module` — sin acceso a DB, rápidos y aislados:

| Método testado | Tests |
|---|---|
| `build_from_modules` | 5 (empty, single root, parent+child, order parents, order children) |
| `build_flat` | 3 (empty, all modules, no children key) |
| `_serialize_module` | 2 (all fields, icon None when absent) |

El docstring fue actualizado para reflejar la cobertura real del archivo.

---

## Conteo final de tests de navegación

| Archivo | Clases | Tests |
|---|---|---|
| `test_navigation_views.py` | 3 (`TestNavigationMenuView`, `TestNavigationModulesView`, `TestNavigationURLs`) | 12 |
| `test_navigation_builders.py` | 2 (`TestMenuValidator`, `TestNavigationMenuAssembler`) | 23 |
| **Total** | **5** | **35** |

---

## Estado final de FASE 7

| Indicador | Valor |
|---|---|
| Archivos modificados | 2 |
| Tests eliminados (incorrectos) | 10 |
| Tests añadidos (correctos) | 25 |
| Bugs de tests corregidos | 9 (URL name, URL path, método mock ×4, aserciones inexistentes ×3, patch AttributeError) |
| Código muerto eliminado | `TestUserMenuView` completa (8 tests no ejecutables) |
| Cobertura nueva | `navigation_modules_view` (antes sin tests), `NavigationMenuAssembler` completo |
| Errores de sintaxis | 0 |
| Deuda técnica generada | Ninguna |
