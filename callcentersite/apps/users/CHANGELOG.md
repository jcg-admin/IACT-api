# Changelog - apps/users

Todos los cambios notables en este módulo serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/).

---

## [2.0.0] - 2026-01-21

### ✨ FASE 2 COMPLETADA

Refactorización completa del módulo de usuarios con arquitectura limpia y RBAC.

### Added

#### Models
- Custom User model extendido de AbstractUser
- UserProfile model (bio, department, avatar_url)
- UserSettings model (language, notifications_enabled)
- SessionHistory model (auditoría de sesiones)
- SoftDeleteMixin para User

#### Validators
- `validate_username()` - Validación de username (alphanumeric, 3-150 chars)
- `validate_avatar_file()` - Validación de avatares (jpg/png/gif, 2MB max)
- `validate_password_strength()` - Password fuerte (8 chars, mayús/minús/número/especial)

#### Services (4)
- UserService - CRUD de usuarios
- ProfileService - Gestión de perfiles y avatares
- PasswordService - Cambio de password
- AuthenticationService - Autenticación

#### Serializers (11)
- UserSerializer - Básico para uso general
- UserListSerializer - Lightweight para listados
- UserDetailSerializer - Completo con relaciones + permissions
- UserCreateSerializer - Crear con validación password
- UserUpdateSerializer - Actualizar campos editables
- ProfileSerializer - Perfil extendido
- UserSettingsSerializer - Configuraciones personales
- AvatarUploadSerializer - Subir avatar
- PasswordChangeSerializer - Cambiar password
- UserActivationSerializer - Activar/desactivar
- SessionHistorySerializer - Auditoría de sesiones

#### ViewSets (4)
- UserViewSet - CRUD usuarios con RBAC (8 endpoints)
- ProfileViewSet - Gestión perfil propio (7 endpoints)
- AuthViewSet - Cambio password (1 endpoint)
- SessionHistoryViewSet - Auditoría sesiones (2 endpoints)

#### Endpoints (18 total)
- CRUD usuarios completo
- Activate/deactivate usuarios
- Gestión perfil propio (/me/)
- Settings personales
- Avatar upload/remove
- Password change
- Historial de sesiones

#### Permissions RBAC
- Integración con apps/access via namespaces Django
- function_map en ViewSets
- Namespaces: users.view, users.create, users.edit, users.delete, sessions.view

#### Tests
- 49 tests unitarios (~90% coverage)
- 35+ tests de integración (~95% coverage)
- 5 factories (User, Admin, Profile, Settings, Session)

#### Signals
- Auto-creación de UserProfile al crear User
- Auto-creación de UserSettings al crear User

#### Documentation
- README.md completo
- INTEGRATION_GUIDE_USERS.md
- API documentation inline
- Este CHANGELOG.md

### Changed

#### Models
- User ahora extiende AbstractUser (no usar django.contrib.auth.models.User)
- Phone field obligatorio con validación México
- Position field con 14 choices
- Avatar opcional con validación
- Removed: employee_id field
- Removed: theme, timezone, email_notifications de UserSettings

#### Permissions
- Sistema basado en namespaces Django (NO códigos duros)
- function_map en ViewSets
- RequiresFunctionPermission de apps/core

#### Architecture
- Separación clara User management (apps/users) vs RBAC management (apps/access)
- Services para lógica de negocio
- Serializers delegan a services
- ViewSets delegan a serializers

### Removed

- UserFunctionAssignmentSerializer (movido a apps/access)
- UserModuleAccessSerializer (movido a apps/access)
- Login/Logout endpoints (están en apps/authentication)
- employee_id field del User model
- theme, timezone, email_notifications de UserSettings

### Fixed

- Circular imports con apps/access (imports lazy en métodos)
- N+1 queries en list endpoints (select_related)
- Password expuesto en responses (write_only en serializers)

### Security

- Password strength validation
- Password hasheado en DB (pbkdf2_sha256)
- Password nunca expuesto en API responses
- Soft delete en vez de hard delete
- Session history para auditoría

---

## [1.0.0] - 2025-12-XX

### FASE 1 - Versión Inicial

#### Added
- User model básico
- Login/Logout básico
- Profile básico
- Tests básicos

---

## Tipos de Cambios

- **Added** - Nuevas características
- **Changed** - Cambios en funcionalidad existente
- **Deprecated** - Características que serán removidas
- **Removed** - Características removidas
- **Fixed** - Bug fixes
- **Security** - Cambios de seguridad

---

## Versionado

Este proyecto sigue [Semantic Versioning](https://semver.org/):

- **MAJOR.MINOR.PATCH**
- MAJOR: Cambios incompatibles en API
- MINOR: Nueva funcionalidad compatible
- PATCH: Bug fixes compatibles

---

**Última actualización:** 2026-01-21  
**Versión actual:** 2.0.0
