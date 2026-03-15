# ANÁLISIS DE BRECHAS — auth.login
## Diseño vs Implementación Actual

**Documento:** ANALISIS_BRECHAS_AUTH_LOGIN_15032026
**Fecha:** 2026-03-15
**Módulo:** MOD_Auth — Autenticación
**Función:** auth.login
**Versión tarjeta:** v2.0.0
**Versión código:** v3.0.1

---

## RESUMEN EJECUTIVO

La función `auth.login` está implementada y operativa. El flujo principal (login con username/password, bloqueo por intentos fallidos, registro de auditoría, creación de sesión) funciona correctamente. Sin embargo, existen **9 brechas** entre el diseño documentado en la tarjeta y la implementación actual, clasificadas en tres niveles de impacto: seguridad, experiencia de usuario y estructura técnica.

| Categoría | Brechas | Críticas | Medias | Bajas |
|---|---|---|---|---|
| Seguridad | 2 | 1 | 1 | 0 |
| Experiencia de usuario | 4 | 0 | 2 | 2 |
| Estructura técnica | 3 | 0 | 1 | 2 |
| **Total** | **9** | **1** | **4** | **4** |

---

## 1. MECANISMO DE TOKEN: JWT vs DRF Token

### Clasificación
- **Impacto:** CRÍTICO — Seguridad
- **Estado:** Pendiente de implementación

### Situación actual

El endpoint retorna un **DRF Token** (clave estática):

```python
# apps/authentication/services/authentication.py:168
token, created = Token.objects.get_or_create(user=user)
```

```json
// Response actual
{
  "data": {
    "token": "abc123def456xyz789..."
  }
}
```

El token no expira. Una vez generado, es válido indefinidamente hasta que se elimine manualmente de la base de datos.

### Diseño esperado

**JWT con access token de corta vida y refresh token:**

```json
// Response diseñado
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

| Atributo | Access Token | Refresh Token |
|---|---|---|
| Vida útil | 15 minutos | 7 días |
| Propósito | Autenticar requests | Renovar access token |
| Almacenamiento cliente | Memoria (no localStorage) | HttpOnly Cookie |
| Rotación | En cada uso de refresh | Sí (ROTATE_REFRESH_TOKENS=True) |
| Revocación | Expira solo | Blacklist en BD |

### Diferencia técnica fundamental

```
DRF Token:
  Cliente → [Token abc123] → Servidor
  Servidor → BD: SELECT * FROM authtoken WHERE key='abc123'  ← query en cada request
  Token vive hasta borrado manual

JWT:
  Cliente → [Bearer eyJ...] → Servidor
  Servidor → verifica firma criptográfica (sin BD)
  Token expira por tiempo (exp claim)
```

### Impacto de la brecha

| Escenario | DRF Token (actual) | JWT (diseño) |
|---|---|---|
| Token robado | Acceso indefinido hasta revocación manual | Acceso máximo 15 minutos |
| Logout | Se puede o no borrar el token | Refresh va a blacklist; access expira solo |
| Cambio de contraseña | Token sigue válido | Todos los tokens quedan inválidos |
| Múltiples dispositivos | Un solo token para todos | Un refresh por dispositivo |
| Performance | Query a BD en cada request | Sin BD (verificación criptográfica) |

### Cambios necesarios para implementar

1. Instalar y configurar `rest_framework_simplejwt` (ya instalado, `requirements/base.txt:djangorestframework-simplejwt==5.3.1`)
2. Activar `JWTAuthentication` en `DEFAULT_AUTHENTICATION_CLASSES` (revertir cambio de 2026-03-15)
3. Reemplazar `Token.objects.get_or_create` por `RefreshToken.for_user(user)` en `AuthenticationService.login_user`
4. Actualizar response del viewset para retornar `access` y `refresh`
5. Agregar endpoint `/auth/token/refresh/` para renovar access token
6. Agregar endpoint `/auth/token/blacklist/` para logout con invalidación
7. Actualizar `conftest.py` a JWT Bearer (revertir cambio de 2026-03-15)
8. Actualizar los 22 tests de `test_views.py` para usar Bearer token

---

## 2. CAMPO `is_locked` EN USER vs TABLA SEPARADA `LoginLockout`

### Clasificación
- **Impacto:** MEDIO — Seguridad y administración
- **Estado:** Pendiente de implementación

### Situación actual

El bloqueo de cuenta se gestiona en una tabla separada `LoginLockout`:

```python
# apps/authentication/models.py (inferido de services/lockout.py)
class LoginLockout(Model):
    username        = CharField()     # no FK a User
    failed_attempts = IntegerField()
    locked_until    = DateTimeField(null=True)
    last_attempt_at = DateTimeField()
```

Para saber si un usuario está bloqueado hay que hacer:

```python
LoginLockout.objects.get(username=username).is_locked()
```

El modelo `User` no tiene campos `is_locked` ni `locked_until`.

### Diseño esperado

El bloqueo como atributo del usuario:

```python
class User(AbstractUser):
    is_locked    = BooleanField(default=False)
    locked_until = DateTimeField(null=True, blank=True)
    locked_reason = CharField(max_length=500, blank=True)
    locked_by    = ForeignKey('self', null=True)   # admin que bloqueó
```

Esto unifica **bloqueo automático** (por intentos fallidos) y **bloqueo manual** (`users.lock`) en el mismo campo del usuario.

### Impacto de la brecha

| Escenario | LoginLockout (actual) | is_locked en User (diseño) |
|---|---|---|
| Ver usuarios bloqueados | Query a otra tabla | `User.objects.filter(is_locked=True)` |
| Panel de administración | No visible en lista de usuarios | Campo visible directamente |
| Bloqueo manual (users.lock) | Mecanismo distinto al automático | Mismo campo `is_locked=True` |
| Referencia por FK | Basado en username (string) | FK a User (integridad referencial) |
| Usuario renombrado | LoginLockout queda huérfano | FK sigue apuntando al mismo registro |

### Cambios necesarios para implementar

1. Agregar migración con campos `is_locked`, `locked_until`, `locked_reason`, `locked_by` al modelo User
2. Refactorizar `LockoutService` para usar `user.is_locked` en lugar de `LoginLockout`
3. Mantener `LoginLockout` como historial o eliminarla
4. Actualizar `users.lock` y `users.unlock` para que usen el mismo campo
5. Actualizar API de usuarios para exponer `is_locked` en el serializer

---

## 3. THROTTLING POR IP (429) vs BLOQUEO POR USERNAME (403)

### Clasificación
- **Impacto:** MEDIO — Seguridad
- **Estado:** Pendiente de implementación

### Situación actual

El sistema bloquea **por username** después de 5 intentos fallidos:

```python
# apps/authentication/services/authentication.py:133
attempts = self.lockout_service.record_failed_attempt(username)
remaining = self.lockout_service.max_attempts - attempts
```

Respuesta al 5° intento:

```json
HTTP 403 Forbidden
{
  "error": {
    "error_code": "ACCOUNT_LOCKED",
    "details": { "locked_minutes": 15 }
  }
}
```

**Vulnerabilidad:** Un atacante puede hacer fuerza bruta sobre usuarios distintos sin ser bloqueado.

```
Intento 1: username=juan, password=test1   → 401 (4 intentos restantes para juan)
Intento 2: username=maria, password=test1  → 401 (4 intentos restantes para maria)
Intento 3: username=pedro, password=test1  → 401 (4 intentos restantes para pedro)
... sin límite por IP
```

### Diseño esperado

**Dos capas de protección:**

```
Capa 1 — Throttling por IP (LoginRateThrottle):
  Scope: 'login'
  Rate: '5/minute'
  Respuesta: HTTP 429 Too Many Requests

Capa 2 — Bloqueo por cuenta (LockoutService):
  Trigger: 5 intentos fallidos consecutivos por username
  Respuesta: HTTP 403 Forbidden
```

```json
// HTTP 429 — Throttling por IP
{
  "success": false,
  "error_code": "AUTH-005",
  "message": "Demasiados intentos. Espere 15 minutos",
  "retry_after": 900,
  "blocked_until": "2026-03-15T10:45:00Z"
}
```

### Comparativa de protección

| Vector de ataque | Sin throttling IP (actual) | Con throttling IP (diseño) |
|---|---|---|
| Fuerza bruta en una cuenta | Bloqueado en 5 intentos | Bloqueado en 5 intentos |
| Fuerza bruta en múltiples cuentas | Sin límite | Bloqueado en 5 requests/min |
| Enumeración de usernames | Sin límite | Bloqueado en 5 requests/min |
| Ataque distribuido (múltiples IPs) | Sin límite | Limitado por IP individual |

### Cambios necesarios para implementar

1. Crear `LoginRateThrottle` en `apps/authentication/throttles.py`

```python
class LoginRateThrottle(AnonRateThrottle):
    scope = 'login'
    rate = '5/minute'
```

2. Agregar en `REST_FRAMEWORK` settings:

```python
'DEFAULT_THROTTLE_RATES': {
    'login': '5/minute',
}
```

3. Aplicar al action `login` en `AuthViewSet`:

```python
@action(throttle_classes=[LoginRateThrottle], ...)
def login(self, request):
```

4. Agregar manejo del `Throttled` exception en el viewset para retornar formato consistente con `retry_after` y `blocked_until`

---

## 4. `UserActionLog` vs MODELO `LoginAttempt`

### Clasificación
- **Impacto:** MEDIO — Arquitectura de auditoría
- **Estado:** Pendiente de implementación

### Situación actual

Existe un modelo `LoginAttempt` específico para intentos de login:

```python
# apps/authentication/models.py
class LoginAttempt(Model):
    user       = ForeignKey(User, null=True)
    username   = CharField()
    success    = BooleanField()
    ip_address = GenericIPAddressField()
    user_agent = TextField()
    created_at = DateTimeField(auto_now_add=True)
```

Para registrar otras acciones (cambio de contraseña, creación de usuario, etc.) se necesitarían modelos separados o la tabla de auditoría genérica de `apps/audit`.

### Diseño esperado

Un modelo centralizado `UserActionLog` con campo `details` JSON:

```python
class UserActionLog(Model):
    user       = ForeignKey(User, null=True)
    action     = CharField()          # 'login', 'logout', 'change_password', ...
    resource   = CharField()          # recurso afectado
    result     = CharField()          # 'success', 'failed', 'blocked'
    ip_address = GenericIPAddressField()
    user_agent = TextField()
    timestamp  = DateTimeField(auto_now_add=True)
    details    = JSONField(default=dict)   # contexto específico de cada acción
```

### Comparativa

| Aspecto | LoginAttempt (actual) | UserActionLog (diseño) |
|---|---|---|
| Scope | Solo intentos de login | Cualquier acción del sistema |
| Contexto adicional | Sin campo flexible | `details` JSON |
| Centralización | Tabla por tipo de evento | Una tabla para todo |
| Consulta cross-action | Query en múltiples tablas | Una sola tabla |
| Ejemplo de query | `LoginAttempt.filter(user=u)` | `UserActionLog.filter(user=u)` |

### Cambios necesarios para implementar

1. Crear modelo `UserActionLog` en `apps/audit` o `apps/authentication`
2. Agregar `details` JSON con campos específicos por acción
3. Migrar registros existentes de `LoginAttempt` a `UserActionLog`
4. Actualizar `AuthenticationService._record_attempt()` para usar `UserActionLog`
5. Actualizar endpoints de auditoría si los hay
6. Mantener `LoginAttempt` como legacy o eliminar tras migración

---

## 5. WRAPPER `data` EN RESPONSE

### Clasificación
- **Impacto:** BAJO — Estructura técnica / contrato de API
- **Estado:** Diferencia de diseño

### Situación actual

Todos los responses de éxito anidan los datos bajo `data`:

```json
{
  "success": true,
  "message": "Login exitoso",
  "data": {
    "user": { "id": 123, "username": "..." },
    "token": "abc123",
    "session_key": "xyz",
    "first_login": false
  }
}
```

### Diseño esperado

Datos al mismo nivel que `success` y `message`:

```json
{
  "success": true,
  "message": "Bienvenido, Juan Pérez",
  "access": "eyJ...",
  "refresh": "eyJ...",
  "user": { "id": 123 },
  "session": { "session_key": "abc", "expire_date": "..." }
}
```

### Análisis

El wrapper `data` tiene ventajas arquitectónicas:

- **Consistencia:** errores y éxitos tienen la misma estructura base (`success`, `message`/`error`, `data`)
- **Metadatos futuros:** fácil agregar `pagination`, `warnings`, `meta` sin romper el contrato
- **Parsing uniforme:** el frontend siempre busca `response.data` para los datos reales

**Recomendación:** Mantener el wrapper `data` (implementación actual) y actualizar la tarjeta para reflejar esta decisión. Cambiar el contrato de API en esta etapa requeriría actualizar todos los clientes.

---

## 6. CAMPOS FALTANTES EN USER RESPONSE

### Clasificación
- **Impacto:** BAJO — Experiencia de usuario (frontend)
- **Estado:** Pendiente de implementación

### Situación actual

El response de login retorna:

```json
"user": {
  "id": 123,
  "username": "juan.perez",
  "email": "juan.perez@empresa.com",
  "first_name": "Juan",
  "last_name": "Pérez"
}
```

### Diseño esperado

```json
"user": {
  "id": 123,
  "username": "juan.perez",
  "email": "juan.perez@empresa.com",
  "full_name": "Juan Pérez",
  "first_name": "Juan",
  "last_name": "Pérez",
  "is_active": true,
  "is_locked": false,
  "last_login": "2026-03-15T10:30:00Z",
  "date_joined": "2025-01-15T08:00:00Z"
}
```

### Impacto por campo

| Campo | Uso en frontend | Costo de implementación |
|---|---|---|
| `full_name` | Saludo "Bienvenido, Juan Pérez", avatar, menú de usuario | Muy bajo — concatenar en serializer |
| `is_locked` | Mostrar advertencia de cuenta bloqueada | Medio — requiere brecha #2 (is_locked en User) |
| `last_login` | "Último acceso: ayer 10:30" (alerta de seguridad) | Bajo — campo ya existe en Django User |
| `date_joined` | "Miembro desde enero 2025" | Muy bajo — campo ya existe en Django User |

### Campos que pueden agregarse hoy (sin otras brechas)

`full_name`, `last_login` y `date_joined` están disponibles en el modelo `User` de Django. Solo requieren actualizarse en el viewset:

```python
# apps/authentication/viewsets.py:101 — hoy
'user': {
    'id': result['user'].id,
    'username': result['user'].username,
    'email': result['user'].email,
    'first_name': result['user'].first_name,
    'last_name': result['user'].last_name,
}

# Agregando los campos disponibles hoy
'user': {
    'id': result['user'].id,
    'username': result['user'].username,
    'email': result['user'].email,
    'first_name': result['user'].first_name,
    'last_name': result['user'].last_name,
    'full_name': f"{result['user'].first_name} {result['user'].last_name}".strip(),
    'last_login': result['user'].last_login,
    'date_joined': result['user'].date_joined,
}
```

`is_locked` requiere la brecha #2 implementada primero.

---

## 7. `locked_until` TIMESTAMP vs `locked_minutes` ENTERO

### Clasificación
- **Impacto:** BAJO — Experiencia de usuario (frontend)
- **Estado:** Pendiente de implementación

### Situación actual

El error de cuenta bloqueada retorna minutos enteros:

```python
# apps/authentication/services/authentication.py:106
minutes = int(time_remaining.total_seconds() / 60) if time_remaining else 15

raise AccountLockedError(
    detail=f"Cuenta bloqueada. Intenta en {minutes} minutos.",
    details={'locked_minutes': minutes}
)
```

```json
{
  "error": {
    "error_code": "ACCOUNT_LOCKED",
    "details": { "locked_minutes": 14 }
  }
}
```

### Diseño esperado

Timestamp exacto de desbloqueo:

```json
{
  "error": {
    "error_code": "AUTH-003",
    "details": {
      "locked_until": "2026-03-15T10:45:00Z",
      "locked_minutes": 14
    }
  }
}
```

### Impacto

| Comportamiento | locked_minutes (actual) | locked_until (diseño) |
|---|---|---|
| Cuenta regresiva exacta | No — solo minutos enteros | Sí — segundos precisos |
| Recarga de página | Sigue mostrando 14 min aunque queden 13:45 | Calcula tiempo exacto en cada render |
| Sincronización cliente-servidor | Puede desincronizarse | Siempre exacto (timestamp absoluto) |

### Cambios necesarios

Exponer `locked_until` desde `LockoutService` y pasarlo como detalle de la excepción:

```python
# apps/authentication/services/authentication.py
time_remaining = self.lockout_service.get_lockout_time_remaining(username)
locked_until = timezone.now() + time_remaining if time_remaining else None

raise AccountLockedError(
    detail=f"Cuenta bloqueada. Intenta en {minutes} minutos.",
    details={
        'locked_minutes': minutes,
        'locked_until': locked_until.isoformat() if locked_until else None
    }
)
```

---

## 8. CUENTA INACTIVA AUTOMÁTICA TRAS 90 DÍAS

### Clasificación
- **Impacto:** MEDIO — Seguridad y política de acceso
- **Estado:** NO implementado

### Situación actual

No existe ningún mecanismo que desactive cuentas automáticamente por inactividad. `is_active=False` solo se puede establecer manualmente mediante `users.lock` o `users.delete`.

### Diseño esperado

- **RN-007:** Cuenta inactiva automáticamente si `last_login` tiene más de 90 días
- Un proceso programado (tarea diaria) marca `is_active=False` a las cuentas inactivas
- El usuario ve: "Cuenta inactiva. Contacte al administrador" (AUTH-004) al intentar login

### Cambios necesarios para implementar

1. Crear tarea programada `deactivate_inactive_accounts` en `apps/authentication/tasks.py`
2. Configurar ejecución diaria via APScheduler (ya en uso en el proyecto)
3. La tarea ejecuta: `User.objects.filter(last_login__lt=90_days_ago).update(is_active=False)`
4. Registrar desactivaciones en auditoría
5. Agregar campo `AUTH-004` al manejo de errores de `UserInactiveError` con `inactive_since`

---

## 9. DETECCIÓN DE SESIÓN DUPLICADA (FLUJO A5)

### Clasificación
- **Impacto:** BAJO — Experiencia de usuario
- **Estado:** NO implementado

### Situación actual

Si un usuario hace login con una sesión ya activa, el sistema crea una segunda sesión sin preguntar. El usuario puede tener múltiples sesiones simultáneas.

### Diseño esperado (Flujo A5)

1. Sistema detecta sesión activa para el usuario
2. Retorna `AUTH-006`: "Ya tiene una sesión activa. ¿Desea cerrarla?"
3. Frontend muestra confirmación al usuario
4. Si acepta: invalida sesión anterior y crea nueva
5. Si cancela: mantiene sesión anterior, login no procede

### Cambios necesarios para implementar

1. En `AuthenticationService.login_user()`, verificar `SessionLog.objects.filter(user=user, is_active=True).exists()` antes de crear nueva sesión
2. Retornar código especial `SESSION_CONFLICT` si existe sesión activa
3. Agregar parámetro `force=true` al request de login para que el frontend confirme
4. Si `force=true`: invalidar sesiones activas anteriores y proceder
5. Agregar tests para ambos paths (conflict + force)

---

## TABLA RESUMEN DE BRECHAS

| # | Brecha | Impacto | Esfuerzo | Dependencias | Prioridad |
|---|---|---|---|---|---|
| 1 | JWT vs DRF Token | CRÍTICO — Seguridad | Alto | Ninguna | 1 |
| 2 | is_locked en User vs LoginLockout | MEDIO — Administración | Medio | Ninguna | 2 |
| 3 | Throttling por IP (429) | MEDIO — Seguridad | Bajo | Ninguna | 3 |
| 4 | UserActionLog vs LoginAttempt | MEDIO — Arquitectura | Alto | Ninguna | 4 |
| 5 | Wrapper `data` en response | BAJO — Estructura | Bajo | Ninguna | No cambiar (*) |
| 6a | `full_name`, `last_login`, `date_joined` | BAJO — Frontend | Muy bajo | Ninguna | 5 |
| 6b | `is_locked` en user response | BAJO — Frontend | Bajo | Brecha #2 | 6 |
| 7 | `locked_until` timestamp | BAJO — Frontend | Muy bajo | Ninguna | 7 |
| 8 | Inactividad automática 90 días | MEDIO — Seguridad | Medio | Ninguna | 8 |
| 9 | Detección sesión duplicada | BAJO — UX | Medio | Ninguna | 9 |

(*) Se recomienda mantener el wrapper `data` de la implementación actual y actualizar la tarjeta.

---

## ORDEN DE IMPLEMENTACIÓN RECOMENDADO

```
FASE 1 — Seguridad crítica
  ├── Brecha #3: Throttling por IP        (bajo esfuerzo, alto impacto)
  ├── Brecha #1: JWT access + refresh     (alto esfuerzo, máximo impacto)
  └── Brecha #8: Inactividad 90 días      (medio esfuerzo, medio impacto)

FASE 2 — Modelo de datos
  ├── Brecha #2: is_locked en User        (habilita brecha #6b)
  └── Brecha #4: UserActionLog            (centraliza auditoría)

FASE 3 — Respuesta API (bajo costo, mejora inmediata)
  ├── Brecha #6a: full_name, last_login, date_joined
  ├── Brecha #7: locked_until timestamp
  └── Brecha #9: Sesión duplicada

FASE 4 — Actualización tarjeta
  └── Brecha #5: Confirmar wrapper data como estándar del sistema
```

---

## LO QUE FUNCIONA CORRECTAMENTE HOY

| Característica | Implementación | Verificado en |
|---|---|---|
| Login con username + password | `AuthViewSet.login` → `AuthenticationService.login_user` | `test_views.py:test_login_exitoso_retorna_200` |
| Bloqueo tras 5 intentos fallidos | `LockoutService.record_failed_attempt` → `LoginLockout` | `test_auth_flow.py:test_account_lockout_after_5_failed_attempts` |
| Desbloqueo automático al expirar | `LockoutService.is_locked()` limpia lockout expirado | `test_services.py:test_unlock_account` |
| Cuenta inactiva bloquea login | `UserInactiveError` en `authenticate_user` | `test_views.py:test_usuario_inactivo_retorna_403` |
| Registro de intentos (audit) | `LoginAttempt` en cada intento | `test_views.py:test_login_exitoso_crea_login_attempt_exitoso` |
| Creación de SessionLog | `_create_session_log` en login exitoso | `test_views.py:test_login_exitoso_crea_session_log` |
| Detección de first_login | `_is_first_login` cuenta LoginAttempts exitosos | `test_views.py:test_login_exitoso_retorna_first_login_true` |
| Token DRF get_or_create | Un token por usuario, reutilizable | `test_views.py:test_login_exitoso_retorna_token` |
| Reset de contador tras login exitoso | `LockoutService.reset_failed_attempts` | `test_auth_flow.py:test_complete_authentication_flow` |
| Persistencia en PostgreSQL | Sin Redis/cache (CNST-010) | `LockoutService.__init__` |

---

Sistema IACT — Análisis IVR
Versión: 1.0.0 | Fecha: 2026-03-15 | Autor: Análisis automatizado Claude
