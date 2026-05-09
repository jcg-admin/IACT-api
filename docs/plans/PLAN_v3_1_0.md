# Plan de implementación v3.1.0 — IACT API

**Versión:** 3.1.0
**Fecha:** 2026-05-08
**Prerrequisito:** Plan v3.0.0 completado
**Scope:** MenuItem (CNST-032 v5.6.x) + resolución de skips heredados

---

## Contexto

Este plan cierra la deuda de navegación del sistema IACT.
El módulo de permisos RBAC fue simplificado en v6.0.0 eliminando
`ServiceFilterMixin`, `ServiceAccessService` y `UserServiceAccess`.
Esa simplificación dejó:

- 17 tests en skip sin decisión explícita documentada (DT-002).
- El modelo `MenuItem` del spec v5.6.x sin implementar — el API usa
  `Module` (modelo legacy).
- `ModuleAccessService` mencionado en 2 tests como no implementado.

---

## Distinción fundamental: MenuItem vs menú IVR

**`MenuItem`** es el árbol de navegación UX del sistema IACT:
el menú que el usuario autenticado ve en la interfaz, estructurado
como `Domain → Section → Action`. Definido por `CNST-032` y `UC_PERM_08`.

**Menú IVR** es el campo `cMenu` en los datos de llamadas telefónicas.
Es completamente distinto — pertenece al plan v3.0.0.

No confundir estos dos conceptos.

---

## Estado de partida esperado

```
tests/unit/         >= 645 passed, 0 failed (post v3.0.0)
tests/integration/  >= 17 passed
Django check:       0 issues
```

---

## Restricciones técnicas aplicables

| ID | Restricción | Impacto |
|----|-------------|---------|
| CNST-032 v2.0.0 | `MenuItem` es wrapper UX 1:1 sobre `Function` — NO es fuente de capability | La regla de acceso vive en `Function`; `MenuItem` solo tiene metadata visual |
| ADR-BACK-008 | MenuItem lifecycle con state machine | DRAFT→ACTIVE→DEPRECATED→ARCHIVED, transiciones validadas |

---

## Tareas

### T-101 — Fix skip injustificado en `utils/test_utils_network.py`

**Causa raíz:** `tests/unit/utils/test_utils_network.py` importa desde
`apps.utils.network` y el archivo `network.py` existe y funciona.
El `pytestmark = pytest.mark.skip` no tiene razón documentada.

**Verificación previa:**
```bash
python -m pytest tests/unit/utils/test_utils_network.py --tb=no -q
# Resultado sin el skip: todos los tests pasan
```

**Acción:** Eliminar la línea `pytestmark = pytest.mark.skip(...)` del archivo.

**Archivos a modificar:**
```
tests/unit/utils/test_utils_network.py
```

**Sin prerequisito.** Es la tarea más pequeña de los tres planes.

---

### T-102 — Implementar modelo `MenuItem` (UC_ADM_04)

**Causa raíz:** El spec v5.6.x (`CNST-032`, `domain-model/menu-item.rst`)
define `MenuItem` como wrapper UX 1:1 sobre `Function` con metadata
visual y lifecycle propio. No existe como modelo Django. El API usa
`Module` (modelo anterior con distinta semántica).

**Campos requeridos** (del spec `domain-model/menu-item.rst`):
```python
class MenuItem(models.Model):
    function      = models.OneToOneField(
                        'access.Function',
                        on_delete=models.PROTECT,
                        related_name='menu_item',
                    )
    display_label = models.CharField(max_length=100)
    icon          = models.CharField(max_length=100, blank=True, default='')
    route         = models.CharField(max_length=200, blank=True, default='')
    order         = models.PositiveSmallIntegerField(default=0)
    parent        = models.ForeignKey(
                        'self',
                        null=True, blank=True,
                        on_delete=models.SET_NULL,
                        related_name='children',
                    )
    status        = models.CharField(
                        max_length=20,
                        choices=[
                            ('DRAFT', 'Draft'),
                            ('ACTIVE', 'Active'),
                            ('DEPRECATED', 'Deprecated'),
                            ('ARCHIVED', 'Archived'),
                        ],
                        default='DRAFT',
                    )
    deprecated_at = models.DateTimeField(null=True, blank=True)
    archived_at   = models.DateTimeField(null=True, blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'access'
        ordering  = ['order']
```

**Invariante I-1 del spec:** 1 `Function` = 0..1 `MenuItem`.
La relación `OneToOneField` lo garantiza a nivel de BD.

**Archivos a crear o modificar:**
```
apps/access/models.py           — agregar clase MenuItem
apps/access/migrations/         — migración nueva
apps/access/serializers/        — MenuItemSerializer
apps/access/views.py            — MenuItemViewSet (CRUD con manage_menu_catalog)
apps/access/urls.py             — registrar router
```

**Prerequisito:** Ninguno. `Function` ya existe en `apps/access/models.py`.

---

### T-103 — Resolución de DT-002 (17 tests en skip)

**Causa raíz:** La simplificación RBAC v6.0.0 eliminó `ServiceFilterMixin`,
`ServiceAccessService` y `UserServiceAccess`. Los tests que cubrían estas
clases quedaron en skip con la marca `DT-002` pero sin decisión registrada.

**Inventario de los 17 skips:**

| Archivo | Clase | Tests | Razón skip |
|---------|-------|-------|-----------|
| `core/test_mixins.py` | `TestServiceFilterMixin` | 2 | `ServiceFilterMixin` eliminado — DT-002 |
| `core/test_permissions.py` | `TestHasServiceAccess` | 5 | `HasServiceAccess` eliminado — DT-002 |
| `core/test_service_access.py` (no existe como archivo individual) | `TestUserServiceAccess`, `TestServiceAccessService`, `TestServiceFilterMixin` | 10 | `UserServiceAccess`/`ServiceAccessService` eliminados — DT-002 |

**Decisión requerida:**

Opción A — eliminar los tests:
`ServiceFilterMixin` y las clases asociadas fueron eliminadas intencionalmente
en la simplificación RBAC. Los tests documentan funcionalidad que ya no existe.
Eliminarlos limpia la deuda.

Opción B — marcarlos como `xfail` con razón explícita:
Mantenerlos como documentación de la arquitectura anterior, con
`@pytest.mark.xfail(reason="Eliminado en RBAC v6.0.0 — DT-002", strict=True)`.

La opción A es la recomendada. Los tests de funcionalidad eliminada no
aportan valor y generan confusión en el informe de suite.

**Acción recomendada:**
```bash
# Verificar que el comportamiento anterior no existe en el codebase
grep -rn "ServiceFilterMixin\|ServiceAccessService\|UserServiceAccess" \
    apps/ --include="*.py" | grep -v "test_\|__pycache__"
# Si resultado vacío → eliminar los tests
```

**Nota sobre `ModuleAccessService` (2 skips adicionales en `access/test_services.py`):**
`ModuleAccessService` no fue eliminado sino simplificado. La decisión
de implementarlo o no es independiente de DT-002.

---

### T-104 — Implementar `MenuLifecycleService` (UC_ADM_05)

**Causa raíz:** El spec (`domain-model/menu-lifecycle-service.rst`) define
una state machine para el lifecycle de `MenuItem`. Sin ella, los campos
`deprecated_at`, `archived_at` y `status` de `MenuItem` no tienen
comportamiento controlado.

**Prerequisito:** T-102 (`MenuItem` debe existir).

**Transiciones válidas:**
```
DRAFT → ACTIVE → DEPRECATED → ARCHIVED
             ↑_________________________|  (no permitida)
```

**Responsabilidades del servicio:**
- Validar transiciones (solo las permitidas arriba).
- Setear `deprecated_at` cuando pasa a DEPRECATED.
- Setear `archived_at` cuando pasa a ARCHIVED.
- Gestionar `block_auto_archive` para items que no deben archivarse
  automáticamente (requiere `block_reason`).
- Job `auto_archive_menu_items`: archivar items en DEPRECATED con
  más de 90 días (UC_ADM_05 FA-04).

**Archivos a crear o modificar:**
```
apps/access/services/menu_lifecycle_service.py   — service nuevo
apps/access/views.py                              — endpoint para cambios de estado
```

---

### T-105 — Tests para MenuItem y MenuLifecycleService

**Archivos a crear:**
```
tests/unit/access/test_menu_item_model.py
tests/unit/access/test_menu_lifecycle_service.py
tests/unit/access/test_menu_item_viewset.py
```

**Prerequisito:** T-102 y T-104.

---

## Dependencias entre tareas

```
T-101  sin prerequisito
T-102  sin prerequisito  (Function ya existe)
T-103  sin prerequisito  (solo decisión + acción)
T-104  depende de T-102  (MenuItem debe existir)
T-105  depende de T-102 y T-104
```

T-101 y T-103 pueden ejecutarse en cualquier momento, incluso
en paralelo con el plan v3.0.0.

---

## Criterio de cierre

```bash
# 1. Tests unitarios — 0 failed, 0 skips relacionados con MenuItem/DT-002
python -m pytest tests/unit/ --tb=no -q
# Resultado esperado: >= 660 passed, 0 failed, <= 2 skipped (solo ModuleAccessService)

# 2. MenuItem importa y tiene migración aplicada
python manage.py shell -c "
from apps.access.models import MenuItem
print('campos:', [f.name for f in MenuItem._meta.fields])
"

# 3. Endpoint MenuItem existe
python -c "
from django.urls import reverse
print(reverse('access:menuitem-list'))
"

# 4. MenuLifecycleService valida transiciones
python manage.py shell -c "
from apps.access.services.menu_lifecycle_service import MenuLifecycleService
print('transiciones:', MenuLifecycleService.VALID_TRANSITIONS)
"

# 5. Django check limpio
python manage.py check
```
