# apps/users - User Management Module

**Versión:** 2.0.0  
**Estado:** ✅ Producción  
**FASE 2:** Completada  

---

## 📋 DESCRIPCIÓN

Módulo completo de gestión de usuarios para IACT Call Center Platform.

Incluye:
- ✅ Gestión CRUD de usuarios
- ✅ Perfiles extendidos (bio, department)
- ✅ Configuraciones personales (language, notifications)
- ✅ Gestión de avatares (upload, remove)
- ✅ Cambio de password
- ✅ Historial de sesiones (auditoría)
- ✅ Sistema de permissions RBAC
- ✅ Soft delete

---

## 🏗️ ARQUITECTURA

### Estructura

```
apps/users/
├── models.py                   # 4 models
│   ├── User (custom AbstractUser)
│   ├── UserProfile
│   ├── UserSettings
│   └── SessionHistory
│
├── managers.py                 # Custom managers
│   ├── ActiveUserManager
│   └── SoftDeleteMixin
│
├── validators.py               # 3 validators
│   ├── validate_username()
│   ├── validate_avatar_file()
│   └── validate_password_strength()
│
├── constants.py                # Choices + namespaces
│
├── services/                   # Business logic (4 services)
│   ├── user_service.py
│   ├── profile_service.py
│   ├── password_service.py
│   └── authentication_service.py
│
├── serializers/                # API serializers (11 total)
│   ├── user_serializer.py      # 5 serializers
│   ├── profile_serializer.py   # 3 serializers
│   ├── auth_serializer.py      # 2 serializers
│   └── session_serializer.py   # 1 serializer
│
├── viewsets/                   # API endpoints (4 viewsets)
│   ├── user_viewset.py
│   ├── profile_viewset.py
│   ├── auth_viewset.py
│   └── session_viewset.py
│
├── urls.py                     # DRF routers (18 endpoints)
│
└── signals.py                  # Auto-create profile/settings
```

### Modelos

**User (Custom AbstractUser)**
- Username, email, password
- Phone (México format)
- Position (14 choices)
- Avatar
- SoftDelete support
- RBAC integration

**UserProfile**
- Bio
- Department (8 choices)
- avatar_url (property)

**UserSettings**
- Language (es, en)
- notifications_enabled

**SessionHistory**
- Login/logout tracking
- IP address, user agent
- Duration calculation
- Auditoría completa

---

## 📡 API ENDPOINTS

### User Management (RBAC protected)

```yaml
GET    /api/users/                  # List users (users.view)
POST   /api/users/                  # Create user (users.create)
GET    /api/users/{id}/             # User detail (users.view)
PUT    /api/users/{id}/             # Update full (users.edit)
PATCH  /api/users/{id}/             # Update partial (users.edit)
DELETE /api/users/{id}/             # Soft delete (users.delete)
POST   /api/users/{id}/activate/    # Activate (users.edit)
POST   /api/users/{id}/deactivate/  # Deactivate (users.edit)
```

### Profile Management (own profile, no RBAC)

```yaml
GET    /api/profile/me/             # View profile
PUT    /api/profile/me/             # Update profile full
PATCH  /api/profile/me/             # Update profile partial
GET    /api/profile/me/settings/    # View settings
PUT    /api/profile/me/settings/    # Update settings full
PATCH  /api/profile/me/settings/    # Update settings partial
POST   /api/profile/me/avatar/      # Upload avatar
DELETE /api/profile/me/avatar/      # Remove avatar
```

### Authentication (own password, no RBAC)

```yaml
POST   /api/auth/change-password/   # Change password
```

### Session History (RBAC protected)

```yaml
GET    /api/sessions/               # List sessions (sessions.view)
GET    /api/sessions/{id}/          # Session detail (sessions.view)
```

**Total:** 18 endpoints

---

## 🔒 SISTEMA DE PERMISSIONS

### Namespaces Django

```python
# apps/users/constants.py

PERM_USERS_VIEW = 'users.view'       # Ver usuarios
PERM_USERS_CREATE = 'users.create'   # Crear usuarios
PERM_USERS_EDIT = 'users.edit'       # Editar usuarios
PERM_USERS_DELETE = 'users.delete'   # Eliminar usuarios
PERM_SESSIONS_VIEW = 'sessions.view' # Ver sesiones
```

### Uso en ViewSets

```python
# apps/users/viewsets/user_viewset.py

class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, RequiresFunctionPermission]
    
    function_map = {
        'list': PERM_USERS_VIEW,     # 'users.view'
        'create': PERM_USERS_CREATE, # 'users.create'
        'update': PERM_USERS_EDIT,   # 'users.edit'
        'destroy': PERM_USERS_DELETE # 'users.delete'
    }
```

### Verificación

```python
# En User model
def has_function(self, function_id):
    """Verifica si user tiene permission namespace."""
    if self.is_superuser:
        return True
    
    from apps.access.models import UserFunctionAssignment
    return UserFunctionAssignment.objects.filter(
        user=self,
        function__code=function_id,
        is_active=True
    ).exists()
```

---

## 🚀 USO

### Crear Usuario

```python
from apps.users.services.user_service import UserService

user = UserService().create_user(
    username='jdoe',
    email='jdoe@company.com',
    password='SecurePass123!',
    first_name='John',
    last_name='Doe',
    phone='+52 55 1234 5678',
    position='ANALYST'
)
```

### Actualizar Perfil

```python
from apps.users.services.profile_service import ProfileService

ProfileService().update_profile(
    user_id=user.id,
    bio='Python Developer',
    department='DEVELOPMENT'
)
```

### Cambiar Password

```python
from apps.users.services.password_service import PasswordService

PasswordService().change_password(
    user=user,
    old_password='OldPass123!',
    new_password='NewPass456!'
)
```

### Activar/Desactivar Usuario

```python
from apps.users.services.user_service import UserService

service = UserService()
service.deactivate_user(user.id)
service.activate_user(user.id)
```

---

## 🧪 TESTING

### Unit Tests (49 tests)

```bash
pytest tests/unit/users/ -v
```

**Coverage:** ~90%

### Integration Tests (35+ tests)

```bash
pytest tests/integration/users/ -v
```

**Coverage:** ~95%

### Factories

```python
from tests.factories.user_factory import (
    UserFactory,
    AdminUserFactory,
    UserProfileFactory,
    UserSettingsFactory,
    SessionHistoryFactory
)

# Crear usuario de prueba
user = UserFactory()

# Crear admin
admin = AdminUserFactory()

# Crear con profile
user = UserFactory()
profile = UserProfileFactory(user=user)
```

---

## 📊 STATISTICS

```yaml
Models: 4
Services: 4 (1,511 lines)
Serializers: 11
ViewSets: 4
Endpoints: 18

Validators: 3
Constants: 5 namespaces

Unit Tests: 49
Integration Tests: 35+
Total Coverage: ~95%

Líneas de código: ~5,000
```

---

## 🔗 INTEGRACIÓN

### Con apps/access/ (RBAC)

```python
# apps/users/ lee permissions (NO gestiona)
permissions = user.get_functions()  # Lee de apps/access
has_perm = user.has_function('users.view')

# apps/access/ gestiona RBAC
from apps.access.models import UserFunctionAssignment
UserFunctionAssignment.objects.create(
    user=user,
    function=function,  # function.code = 'users.view'
    is_active=True
)
```

### Con apps/authentication/ (Login/Logout)

```python
# apps/authentication/ maneja login/logout
# apps/users/ maneja solo password change
```

---

## 📝 CONVENCIONES

### Naming

```python
# Modelos: PascalCase
User, UserProfile, UserSettings

# Servicios: PascalCase + Service
UserService, ProfileService

# Serializers: PascalCase + Serializer
UserSerializer, UserCreateSerializer

# ViewSets: PascalCase + ViewSet
UserViewSet, ProfileViewSet

# Permissions: UPPER_SNAKE_CASE
PERM_USERS_VIEW, PERM_USERS_CREATE
```

### Código

```python
# Docstrings: Google style
def create_user(self, username, email, password):
    """
    Crea nuevo usuario.
    
    Args:
        username: Username único
        email: Email único
        password: Password (será hasheado)
    
    Returns:
        User: Usuario creado
    """

# Type hints cuando posible
def get_user(user_id: int) -> User:
    pass

# Constants en mayúsculas
MAX_AVATAR_SIZE_MB = 2
DEFAULT_LANGUAGE = 'es'
```

---

## 🐛 TROUBLESHOOTING

### User no tiene profile

**Problema:** `user.profile` no existe

**Solución:** Profile se auto-crea via signal. Si no existe:

```python
from apps.users.models import UserProfile
UserProfile.objects.create(user=user)
```

### Permission denied en endpoints

**Problema:** 403 Forbidden

**Solución:** Verificar que user tiene permission namespace:

```python
# Verificar
user.has_function('users.view')  # debe retornar True

# Asignar (en apps/access/)
from apps.access.models import UserFunctionAssignment, Function
function = Function.objects.get(code='users.view')
UserFunctionAssignment.objects.create(
    user=user,
    function=function,
    is_active=True
)
```

### Avatar upload falla

**Problema:** Error al subir avatar

**Solución:** Verificar formato y tamaño:

```python
# Formatos permitidos: jpg, jpeg, png, gif
# Tamaño máximo: 2MB

from apps.users.validators import validate_avatar_file
validate_avatar_file(file)  # Lanza error si inválido
```

---

## 📚 DOCUMENTACIÓN ADICIONAL

- **API Documentation:** [API_DOCUMENTATION.md](../../../docs/API_DOCUMENTATION_USERS.md)
- **Integration Guide:** [INTEGRATION_GUIDE_USERS.md](../../../docs/INTEGRATION_GUIDE_USERS.md)
- **Changelog:** [CHANGELOG.md](./CHANGELOG.md)

---

## 👥 MANTAINERS

- **Equipo:** IACT Development Team
- **Contacto:** dev@iact.com
- **FASE 2:** 2026-01-21

---

## 📄 LICENSE

Propietario - IACT © 2026
