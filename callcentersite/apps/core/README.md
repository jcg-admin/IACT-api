# apps/core/

**Versión:** 1.0.0  
**Última actualización:** FASE 3  
**Tipo:** Infraestructura Base  

---

## 📋 DESCRIPCIÓN

`apps/core/` es el módulo de **infraestructura base** del sistema IACT. Proporciona componentes compartidos reutilizables por todas las demás apps.

**Principio SRP:** apps/core/ contiene **SOLO infraestructura**, NO lógica de negocio.

---

## 🎯 RESPONSABILIDADES

```yaml
✅ SÍ (Infraestructura):
  - Abstract models (TimeStampedModel, SoftDeleteMixin)
  - DRF Permissions genéricas
  - Middleware del sistema
  - Mixins reutilizables
  - Base services (clases abstractas)
  - Exception classes

❌ NO (Lógica de Negocio):
  - Services específicos de dominio
  - Modelos de negocio concretos
  - Viewsets de dominio
  - Serializers de dominio
```

---

## 📂 ESTRUCTURA

```
apps/core/
├── __init__.py
├── models.py                 # Abstract models
├── permissions.py            # DRF Permissions (7)
├── middleware/               # Middleware del sistema (4)
│   ├── healthcheck.py
│   ├── logging.py
│   ├── security.py
│   └── timezone.py
├── mixins.py                 # ViewSet mixins
├── services/
│   └── base_service.py       # BaseService (abstracto)
├── exceptions.py             # Business exceptions
├── context_processors.py     # Template context
└── navigation/               # Navigation builders
    ├── builders.py
    ├── urls.py
    └── views.py
```

---

## 🧱 ABSTRACT MODELS

### TimeStampedModel

**Propósito:** Agrega timestamps automáticos a cualquier modelo.

**Uso:**

```python
from apps.core.models import TimeStampedModel

class Report(TimeStampedModel):
    name = models.CharField(max_length=200)
    # created_at y updated_at se agregan automáticamente
```

**Campos:**
- `created_at` (DateTimeField): Auto-seteado al crear, inmutable
- `updated_at` (DateTimeField): Auto-actualizado al guardar

**Usado por:** 10+ models (UserProfile, UserSettings, SessionHistory, etc)

---

### SoftDeleteMixin

**Propósito:** Soft delete (eliminación lógica, no física).

**Uso:**

```python
from apps.core.models import SoftDeleteMixin

class Function(SoftDeleteMixin, models.Model):
    code = models.CharField(max_length=100)
    objects = ActiveRecordQuery()  # Manager especial
```

**Campos:**
- `is_deleted` (BooleanField): Default False
- `deleted_at` (DateTimeField): Null si no eliminado

**Métodos:**
- `delete()`: Marca is_deleted=True, setea deleted_at
- `hard_delete()`: Elimina físicamente de DB
- `restore()`: Restaura eliminado (is_deleted=False, deleted_at=None)

**Manager:**
- `Model.objects.all()`: Solo activos (is_deleted=False)
- `Model.objects.deleted()`: Solo eliminados
- `Model.objects.with_deleted()`: Todos
- `Model.objects.active()`: Alias de all()

**Usado por:** User, Function, y otros models críticos

---

## 🔐 DRF PERMISSIONS (7)

### 1. RequiresFunctionPermission (CRÍTICO)

**Propósito:** Verifica permisos RBAC basados en funciones.

**Uso en ViewSet:**

```python
from apps.core.permissions import RequiresFunctionPermission

class ReportViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, RequiresFunctionPermission]
    
    function_map = {
        'list': 'reports.view',
        'create': 'reports.create',
        'update': 'reports.edit',
        'destroy': 'reports.delete',
        'custom_action': 'reports.custom',
    }
```

**Flujo:**

```
1. Request llega a ViewSet action
   ↓
2. RequiresFunctionPermission.has_permission()
   ↓
3. Obtiene action del ViewSet (ej: 'list')
   ↓
4. Busca en function_map: 'list' → 'reports.view'
   ↓
5. Llama user.has_function('reports.view')
   ↓
6. User.has_function() consulta UserFunctionAssignment (apps/access)
   ↓
7. Retorna True/False
```

**Características:**
- Superusers SIEMPRE tienen acceso (bypass)
- Si action no está en function_map → 403 Forbidden
- Si user no autenticado → 401 Unauthorized

**Usado por:**
- apps/authentication (change_password, set_security_answers)
- apps/users (CRUD operations)
- apps/pipeline
- apps/reports

**Testing:** 100% cubierto en `tests/unit/core/test_permissions.py`

---

### 2. IsOwnerOrReadOnly

**Propósito:** Solo el owner puede editar, otros solo leen.

**Uso:**

```python
from apps.core.permissions import IsOwnerOrReadOnly

class DocumentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
```

**Requisitos:**
- Modelo debe tener campo `created_by` (ForeignKey a User)

**Comportamiento:**
- SAFE_METHODS (GET, HEAD, OPTIONS) → Todos
- Otros métodos (POST, PUT, DELETE) → Solo owner

---

### 3. IsSuperUserOrReadOnly

**Propósito:** Solo superusers pueden escribir.

**Uso:**

```python
from apps.core.permissions import IsSuperUserOrReadOnly

class SystemConfigViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsSuperUserOrReadOnly]
```

---

### 4. IsStaffOrReadOnly

**Propósito:** Solo staff/superusers pueden escribir.

**Uso:**

```python
from apps.core.permissions import IsStaffOrReadOnly

class AdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsStaffOrReadOnly]
```

---

### 5. HasServiceAccess

**Propósito:** Verifica acceso a servicios 800 específicos.

**Estado:** ⚠️ DEPRECADO (ver DT-005 en DEUDA_TECNICA.md)

**Nota:** Será reemplazado por RequiresFunctionPermission con Functions específicas para servicios.

---

### 6. AllowOptionsAuthentication

**Propósito:** Permite OPTIONS sin autenticación (CORS).

**Uso:**

```python
from apps.core.permissions import AllowOptionsAuthentication

class PublicAPIViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowOptionsAuthentication, IsAuthenticated]
```

---

## 🔧 MIDDLEWARE (4)

### HealthCheckHandler

**Propósito:** Endpoint /health/ para monitoring.

**Configuración:**

```python
# settings.py
MIDDLEWARE = [
    'apps.core.middleware.HealthCheckHandler',
    # ...
]
```

**Endpoint:**
- GET /health/ → 200 OK `{"status": "healthy"}`

---

### LoggingMiddleware

**Propósito:** Log de requests/responses.

**Logs:**
- Request: método, path, user
- Response: status code, tiempo de ejecución
- Errores: exceptions con traceback

---

### SecurityMiddleware

**Propósito:** Headers de seguridad.

**Headers agregados:**
- `X-Content-Type-Options: nosniff`
- `X-XSS-Protection: 1; mode=block`
- `X-Frame-Options: DENY`

---

### TimezoneMiddleware

**Propósito:** Activa timezone America/Mexico_City.

**Efecto:** Todas las operaciones de fecha/hora usan timezone correcto.

---

## 🎨 MIXINS

### SoftDeleteViewSetMixin

**Propósito:** Agrega endpoints restore/hard-delete.

**Uso:**

```python
from apps.core.mixins import SoftDeleteViewSetMixin

class ReportViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    pass
```

**Endpoints agregados:**
- `POST /api/reports/1/restore/` - Restaura eliminado
- `DELETE /api/reports/1/hard-delete/` - Elimina físicamente

---

### AuditMixin

**Propósito:** Log automático de create/update.

**Uso:**

```python
from apps.core.mixins import AuditMixin

class UserViewSet(AuditMixin, viewsets.ModelViewSet):
    pass
```

**Efecto:** Loggea acciones en perform_create/perform_update.

---

### ServiceFilterMixin

**Propósito:** Filtrado por servicio 800.

**Estado:** ⚠️ DEPRECADO (relacionado con UserServiceAccess)

---

### PaginationControlMixin

**Propósito:** Control de page_size vía query param.

**Uso:**

```python
from apps.core.mixins import PaginationControlMixin

class LargeDataViewSet(PaginationControlMixin, viewsets.ModelViewSet):
    pass
```

**Query param:** `?page_size=50`

---

### ExportMixin

**Propósito:** Endpoints de exportación CSV/Excel.

**Uso:**

```python
from apps.core.mixins import ExportMixin

class ReportViewSet(ExportMixin, viewsets.ModelViewSet):
    pass
```

**Endpoints:**
- `GET /api/reports/export/?format=csv`
- `GET /api/reports/export/?format=xlsx`

---

## 🏗️ BASE SERVICES

### BaseService

**Propósito:** Clase base abstracta para services.

**Uso:**

```python
from apps.core.services import BaseService

class UserService(BaseService):
    model = User
    
    @classmethod
    def create_user(cls, data):
        # Lógica de negocio
        user = cls.model.objects.create(**data)
        return user
```

**Nota:** Services específicos de dominio van en sus respectivas apps (ej: apps/users/services/).

---

## 🚨 EXCEPTIONS

### BusinessRuleError

**Propósito:** Exception para violaciones de reglas de negocio.

**Uso:**

```python
from apps.core.exceptions import BusinessRuleError

if user.is_deleted:
    raise BusinessRuleError("Cannot perform action on deleted user")
```

---

## 📊 TESTING

### Tests Disponibles

```bash
# Tests completos (67 tests)
pytest tests/unit/core/ -v

# Tests por archivo
pytest tests/unit/core/test_permissions.py -v       # 25 tests
pytest tests/unit/core/test_abstract_models.py -v   # 18 tests
pytest tests/unit/core/test_middleware.py -v        # 14 tests
pytest tests/unit/core/test_mixins.py -v            # 10 tests

# Coverage
pytest tests/unit/core/ --cov=apps/core --cov-report=html
```

### Coverage

```yaml
Objetivo: 90%+
  - Permissions: 95%+
  - Abstract models: 95%+
  - Middleware: 90%+
  - Mixins: 90%+
```

---

## 🔄 DEPENDENCIAS

### apps/core/ DEPENDE DE:

```yaml
✅ apps/utils/ (validators, helpers, formatters)
✅ Django (models, permissions)
✅ DRF (permissions, viewsets)
```

### DEPENDIENTES DE apps/core/:

```yaml
✅ apps/users/
✅ apps/access/
✅ apps/authentication/
✅ apps/pipeline/
✅ apps/reports/
✅ apps/alerts/
✅ apps/audit/
```

**Importante:** apps/core/ es nivel 2 en arquitectura (solo apps/utils/ es más bajo).

---

## 💡 BEST PRACTICES

### DO (✅)

```python
# Usar abstract models
class MyModel(TimeStampedModel, SoftDeleteMixin):
    pass

# Usar permissions en ViewSets
class MyViewSet(viewsets.ModelViewSet):
    permission_classes = [RequiresFunctionPermission]
    function_map = {'list': 'my.view'}

# Usar mixins cuando aplique
class MyViewSet(AuditMixin, SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    pass
```

### DON'T (❌)

```python
# NO agregar lógica de negocio a apps/core/
# Esto va en apps específicas

# NO crear services concretos en apps/core/
# Solo BaseService (abstracto)

# NO agregar models concretos
# Solo abstract models
```

---

## 🐛 TROUBLESHOOTING

### RequiresFunctionPermission retorna 403

```yaml
Problema: Permission denied aunque user tiene función

Verificar:
1. function_map está definido en ViewSet
2. action está en function_map
3. user.has_function() retorna True
4. UserFunctionAssignment existe en DB

Debug:
  print(view.action)  # Verificar action
  print(view.function_map)  # Verificar map
  print(user.has_function('code'))  # Verificar RBAC
```

### SoftDelete no funciona

```yaml
Problema: delete() elimina físicamente

Verificar:
1. Model hereda de SoftDeleteMixin
2. objects = ActiveRecordQuery() está definido
3. No se llama super().delete()

Correcto:
  class MyModel(SoftDeleteMixin, models.Model):
      objects = ActiveRecordQuery()  # ← Importante
```

### Timestamps no se actualizan

```yaml
Problema: updated_at no cambia

Verificar:
1. Model hereda de TimeStampedModel
2. Se usa .save() no .update()
3. auto_now=True está en field

Nota: QuerySet.update() NO actualiza updated_at
```

---

## 📚 VER TAMBIÉN

- [apps/utils/README.md](../utils/README.md) - Utilidades puras
- [INTEGRATION_GUIDE_CORE.md](../../docs/INTEGRATION_GUIDE_CORE.md) - Guía de integración
- [ANALISIS_RELACIONES_Y_SRP_v1.1.0.md](../../docs/architecture/ANALISIS_RELACIONES_Y_SRP_v1.1.0.md) - Arquitectura
- [DEUDA_TECNICA.md](../../docs/DEUDA_TECNICA.md) - Deuda técnica

---

## 📋 CHANGELOG

### v1.0.0 (FASE 3)
- ✅ Refactor: Services de negocio movidos a apps/pipeline/
- ✅ Tests: 67 tests creados (90%+ coverage)
- ✅ Docs: README completo
- ✅ SRP mejorado: 9/10

---

**Mantenido por:** IACT Development Team  
**Última actualización:** 2026-01-21 (FASE 3 PARTE 4)
