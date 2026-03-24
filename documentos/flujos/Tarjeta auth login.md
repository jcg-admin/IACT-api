## TARJETA: auth.login

**Nombre para UI:** Iniciar Sesión
**Módulo:** MOD_Auth - Autenticación
**ID Caso de Uso:** UC-001
**Prioridad:** CRÍTICA
**Frecuencia:** Diaria
**Estado:** Activo

---

## DESCRIPCIÓN

Permite a un usuario autenticarse en el sistema IACT mediante username/email y contraseña. Al autenticarse exitosamente, el sistema genera un token JWT de acceso (15 minutos) y un token de refresco (7 días), y crea una sesión en la base de datos PostgreSQL. Esta función es el punto de entrada principal al sistema y habilita todas las demás funciones.

---

## PRECONDICIONES

- Usuario debe estar registrado en el sistema
- Usuario debe tener cuenta activa (is_active=true)
- Usuario NO debe estar bloqueado (is_locked=false)
- Usuario debe estar en la página de login
- Sistema debe estar operativo

---

## FLUJO PRINCIPAL (10 PASOS)

1. Usuario accede a la página de login (`/auth/login`)
2. Sistema muestra formulario con campos: username/email y contraseña
3. Usuario ingresa sus credenciales (username/email + contraseña)
4. Usuario hace clic en botón "Iniciar Sesión"
5. Sistema valida formato de credenciales (CNST-005)
6. Sistema verifica credenciales contra base de datos Analytics (PostgreSQL)
7. Sistema valida que cuenta esté activa y no bloqueada
8. Sistema genera token JWT de acceso (15 min) y refresco (7 días)
9. Sistema crea registro de sesión en tabla `django_session` (CNST-002)
10. Sistema redirige al usuario al dashboard principal

---

## FLUJOS ALTERNATIVOS

**A1. Credenciales inválidas (paso 6)**

- Sistema no encuentra usuario o contraseña incorrecta
- Sistema incrementa contador de intentos fallidos
- Sistema muestra mensaje: "Credenciales inválidas" (AUTH-002)
- Sistema registra intento fallido en log de auditoría (CNST-009)
- Sistema aplica throttling: máximo 5 intentos por minuto (CNST-005)
- Caso de uso termina

**A2. Cuenta bloqueada (paso 7)**

- Sistema detecta que usuario tiene is_locked=true
- Sistema muestra mensaje: "Cuenta bloqueada. Contacte al administrador" (AUTH-003)
- Sistema muestra tiempo restante si bloqueo es temporal
- Sistema registra intento en auditoría con resultado "CUENTA_BLOQUEADA"
- Caso de uso termina

**A3. Cuenta inactiva (paso 7)**

- Sistema detecta que usuario tiene is_active=false
- Sistema muestra mensaje: "Cuenta inactiva. Contacte al administrador" (AUTH-004)
- Sistema registra intento en auditoría
- Caso de uso termina

**A4. Demasiados intentos fallidos (paso 5)**

- Sistema detecta más de 5 intentos en último minuto (throttling)
- Sistema bloquea temporalmente IP por 15 minutos
- Sistema muestra mensaje: "Demasiados intentos. Espere 15 minutos" (AUTH-005)
- Sistema registra evento de seguridad en auditoría
- Caso de uso termina

**A5. Sesión ya activa (paso 8)**

- Sistema detecta que usuario ya tiene sesión activa
- Sistema muestra opción: "¿Cerrar sesión anterior y continuar?" (AUTH-006)
- Si usuario acepta: invalida sesión anterior y continúa
- Si usuario cancela: mantiene sesión anterior y termina
- Caso de uso continúa o termina según elección

**A6. Bloqueo automático por intentos fallidos (paso 6)**

- Sistema detecta 5 intentos fallidos consecutivos
- Sistema bloquea cuenta automáticamente por 15 minutos
- Sistema marca is_locked=true, establece locked_until
- Sistema muestra mensaje: "Cuenta bloqueada por múltiples intentos fallidos" (AUTH-003)
- Sistema registra bloqueo automático en auditoría
- Caso de uso termina

---

## POSTCONDICIONES

**Éxito:**

- Usuario autenticado exitosamente
- Token JWT generado y almacenado en cliente
- Sesión creada en BD PostgreSQL
- Registro de auditoría creado con acción "LOGIN_SUCCESS"
- Usuario redirigido al dashboard
- Contador de intentos fallidos reseteado a 0
- last_login actualizado con timestamp actual

**Fallo:**

- Usuario no autenticado
- No se genera token JWT
- No se crea sesión en BD
- Registro de auditoría creado con acción "LOGIN_FAILED"
- Usuario permanece en página de login
- Contador de intentos fallidos incrementado
- Si alcanza 5 intentos: cuenta bloqueada automáticamente

---

## REGLAS DE NEGOCIO

- **RN-001:** Username/email obligatorio (3-150 caracteres)
- **RN-002:** Contraseña obligatoria (mínimo 8 caracteres)
- **RN-003:** Máximo 5 intentos de login por minuto por IP (throttling)
- **RN-004:** Sesión expira después de 15 minutos de inactividad (access token)
- **RN-005:** Token de refresco válido por 7 días
- **RN-006:** Usuario con 5 intentos fallidos consecutivos se bloquea automáticamente por 15 minutos
- **RN-007:** Cuenta inactiva después de 90 días sin login (is_active=false)
- **RN-008:** Solo una sesión simultánea permitida por usuario (configurable)
- **RN-009:** Último acceso (last_login) se actualiza solo en login exitoso

---

## RESTRICCIONES TÉCNICAS

- **CNST-002:** Sesión almacenada en PostgreSQL (tabla `django_session`), NO en Redis/Memcached
  - Backend: `django.contrib.sessions.backends.db`
  - Session Engine: Base de datos PostgreSQL
  - Cookie-based session ID enviado al cliente

- **CNST-005:** Autenticación JWT obligatoria con `rest_framework_simplejwt`
  - ACCESS_TOKEN_LIFETIME: 15 minutos
  - REFRESH_TOKEN_LIFETIME: 7 días
  - ROTATE_REFRESH_TOKENS: True
  - BLACKLIST_AFTER_ROTATION: True
  - ALGORITHM: HS256

- **CNST-005:** Throttling aplicado: LoginRateThrottle 5 intentos/minuto
  - Scope: 'login'
  - Rate: '5/minute' por IP

- **CNST-009:** Todos los intentos de login registrados en UserActionLog (inmutable)
  - Incluye: username, IP, timestamp, resultado, user_agent
  - Logs nunca se modifican ni eliminan
  - Retención: 90 días para logs de seguridad

---

## REGLAS SoD

**SoD-1: Segregación Usuario-Administrador**

- Un usuario NO puede tener simultáneamente:
  - `auth.login` (usuario normal)
  - `users.create` + `access.assign` (administrador total)
- Justificación: Prevenir que usuario normal se auto-otorgue permisos administrativos
- Nota: auth.login es función pública, pero SoD aplica al conjunto de funciones asignadas

---

## MENSAJES DEL SISTEMA

**Éxito:**

- **AUTH-001:** "Bienvenido, [nombre_usuario]" (login exitoso)

**Errores:**

- **AUTH-002:** "Credenciales inválidas" (usuario/contraseña incorrectos)
- **AUTH-003:** "Cuenta bloqueada. Contacte al administrador" (cuenta bloqueada)
- **AUTH-004:** "Cuenta inactiva. Contacte al administrador" (90+ días sin login)
- **AUTH-005:** "Demasiados intentos. Espere 15 minutos" (throttling)
- **AUTH-006:** "Ya tiene una sesión activa. ¿Desea cerrarla?" (sesión duplicada)
- **AUTH-007:** "Error del sistema. Intente más tarde" (error técnico)

**Informativos:**

- **AUTH-008:** "Último acceso: [fecha_hora]" (mostrado después de login exitoso)
- **AUTH-009:** "Su cuenta será bloqueada tras [X] intentos más" (advertencia preventiva)

---

## IMPLEMENTACIÓN TÉCNICA

**Endpoint:**

```
POST /api/v1/auth/login/
```

**Request:**

```json
{
  "username": "juan.perez",
  "password": "mySecurePassword123"
}
```

**Alternativa con email:**

```json
{
  "email": "juan.perez@empresa.com",
  "password": "mySecurePassword123"
}
```

**Response Exitosa (200 OK):**

```json
{
  "success": true,
  "message": "Bienvenido, Juan Pérez",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
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
  },
  "session": {
    "session_key": "abc123xyz789",
    "expire_date": "2026-03-15T10:45:00Z"
  }
}
```

**Response - Credenciales inválidas (401 Unauthorized):**

```json
{
  "success": false,
  "error_code": "AUTH-002",
  "message": "Credenciales inválidas",
  "attempts_remaining": 3,
  "locked_after": 5
}
```

**Response - Cuenta bloqueada (403 Forbidden):**

```json
{
  "success": false,
  "error_code": "AUTH-003",
  "message": "Cuenta bloqueada. Contacte al administrador",
  "locked_until": "2026-03-15T11:00:00Z",
  "reason": "Múltiples intentos fallidos de inicio de sesión"
}
```

**Response - Cuenta inactiva (403 Forbidden):**

```json
{
  "success": false,
  "error_code": "AUTH-004",
  "message": "Cuenta inactiva. Contacte al administrador",
  "last_login": "2025-10-15T10:30:00Z",
  "inactive_since": "2026-01-13T10:30:00Z"
}
```

**Response - Throttling (429 Too Many Requests):**

```json
{
  "success": false,
  "error_code": "AUTH-005",
  "message": "Demasiados intentos. Espere 15 minutos",
  "retry_after": 900,
  "blocked_until": "2026-03-15T10:45:00Z"
}
```

**Códigos HTTP:**

- **200 OK:** Login exitoso
- **401 Unauthorized:** Credenciales inválidas
- **403 Forbidden:** Cuenta bloqueada o inactiva
- **429 Too Many Requests:** Throttling por demasiados intentos
- **500 Internal Server Error:** Error del servidor

---

## VALIDACIONES

**Validación de Credenciales:**

- Username/email obligatorio
- Contraseña obligatoria
- Formato de email válido (si se usa email)
- Username: 3-150 caracteres alfanuméricos y guiones
- Contraseña: mínimo 8 caracteres

**Validación de Usuario:**

- Usuario existe en base de datos
- Usuario tiene is_active=true
- Usuario tiene is_locked=false
- Si is_locked=true: verificar locked_until para desbloqueo automático

**Validación de Contraseña:**

- Hash de contraseña coincide con registro en BD
- Usa PBKDF2 con SHA256
- Salt único por contraseña
- Comparación segura (timing-attack resistant)

**Validación de Throttling:**

- Verificar intentos en última hora por IP
- Máximo 5 intentos por minuto por IP
- Contador global de intentos fallidos por usuario
- Bloqueo automático tras 5 intentos fallidos consecutivos

**Proceso de Autenticación:**

1. Recibir credenciales
2. Validar formato
3. Aplicar throttling
4. Buscar usuario en BD
5. Verificar estado de cuenta (activa, no bloqueada)
6. Verificar contraseña
7. Generar tokens JWT
8. Crear sesión en BD
9. Actualizar last_login
10. Resetear contador de intentos fallidos
11. Registrar en auditoría

---

## AUDITORÍA

**Se registra en UserActionLog:**

- **Acción:** login_attempt
- **Usuario:** user_id (si existe, null si no encontrado)
- **Timestamp:** hora exacta
- **IP Address:** IP desde donde se intenta login
- **User Agent:** navegador y dispositivo
- **Resultado:** success / invalid_credentials / account_locked / account_inactive / throttled
- **Detalles:**
  - Username/email ingresado
  - Resultado del intento
  - Intentos fallidos consecutivos
  - Si fue bloqueado automáticamente

**Ejemplo de log - Login exitoso:**

```json
{
  "id": 98765,
  "timestamp": "2026-03-15T10:30:00Z",
  "action": "login_attempt",
  "user_id": 123,
  "username": "juan.perez",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0 Chrome/120.0",
  "result": "success",
  "details": {
    "login_method": "username",
    "session_id": "abc123xyz789",
    "access_token_expires": "2026-03-15T10:45:00Z",
    "refresh_token_expires": "2026-03-22T10:30:00Z",
    "failed_attempts_reset": true,
    "previous_last_login": "2026-03-14T09:00:00Z"
  }
}
```

**Ejemplo de log - Credenciales inválidas:**

```json
{
  "id": 98766,
  "timestamp": "2026-03-15T10:31:00Z",
  "action": "login_attempt",
  "user_id": null,
  "username": "juan.perez",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0 Chrome/120.0",
  "result": "invalid_credentials",
  "details": {
    "login_method": "username",
    "reason": "password_mismatch",
    "failed_attempts": 1,
    "remaining_attempts": 4,
    "will_lock_after": 5
  }
}
```

**Ejemplo de log - Bloqueo automático:**

```json
{
  "id": 98770,
  "timestamp": "2026-03-15T10:35:00Z",
  "action": "login_attempt",
  "user_id": 123,
  "username": "juan.perez",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0 Chrome/120.0",
  "result": "account_locked",
  "details": {
    "login_method": "username",
    "reason": "automatic_lock_after_failed_attempts",
    "failed_attempts": 5,
    "locked_until": "2026-03-15T10:50:00Z",
    "lock_duration_minutes": 15,
    "automatic": true
  }
}
```

---

## SEGURIDAD

**Protecciones Implementadas:**

1. **Contraseña nunca se almacena en texto plano**
   - Django usa PBKDF2 con SHA256 para hash de contraseñas
   - Salt único por contraseña (generado automáticamente)
   - 260,000 iteraciones de PBKDF2 (configuración Django 4.2+)
   - Comparación resistente a timing attacks

2. **Protección contra ataques de fuerza bruta**
   - Throttling: 5 intentos/minuto por IP (CNST-005: LoginRateThrottle)
   - Bloqueo automático después de 5 intentos fallidos consecutivos
   - Bloqueo temporal de cuenta por 15 minutos
   - Bloqueo de IP por 15 minutos si excede rate limit
   - Contador de intentos fallidos por usuario

3. **Tokens JWT firmados y verificados**
   - Algoritmo HS256 (HMAC con SHA-256)
   - Secret key almacenada en variable de entorno
   - Token de refresco rotado después de cada uso (ROTATE_REFRESH_TOKENS=True)
   - Tokens antiguos agregados a blacklist automáticamente
   - Verificación de firma en cada request

4. **Auditoría completa e inmutable**
   - Todos los intentos registrados en UserActionLog (CNST-009)
   - Registros incluyen: username, IP, timestamp, resultado, user_agent
   - Logs nunca se modifican ni eliminan
   - Retención de 90 días para logs de seguridad

5. **Sin comunicaciones externas**
   - NO se envían emails de notificación de login (CNST-001)
   - NO se envían SMS de autenticación (CNST-001)
   - NO se usan servicios externos de autenticación

6. **Sesiones seguras**
   - Sesiones almacenadas en PostgreSQL (CNST-002)
   - Session ID generado aleatoriamente
   - Cookie HttpOnly para prevenir XSS
   - Cookie Secure en producción (HTTPS)
   - Cookie SameSite=Lax para prevenir CSRF

7. **Validación de cuenta**
   - Verificación de is_active=true
   - Verificación de is_locked=false
   - Desbloqueo automático si locked_until ha expirado
   - Detección de cuenta inactiva (90+ días sin login)

---

## INTERACCIONES CON OTRAS FUNCIONES

**Requiere:**

- Ninguna (función pública, no requiere autenticación previa)

**Habilita:**

- Todas las demás funciones del sistema (auth.login es el punto de entrada)

**Relacionadas:**

- `auth.logout` - Cerrar sesión activa
- `auth.recover_password` - Recuperar contraseña si usuario no recuerda
- `auth.manage_sessions` - Ver/administrar sesiones activas del usuario
- `users.lock` - Bloquear cuenta manualmente (administrador)
- `users.unlock` - Desbloquear cuenta bloqueada
- `users.reset_password` - Resetear contraseña (administrador)

---

## NOTAS IMPORTANTES

- Login debe completarse en menos de 2 segundos
- Tokens de refresco se rotan después de cada uso
- Solo una sesión simultánea por usuario (configurable)
- Bloqueo de cuenta: automático (5 intentos) es temporal (15 min); manual (users.lock) puede ser indefinido
- Mensajes de error genéricos — no revelar si el username existe
- Cuenta inactiva tras 90 días sin login (is_active=false), requiere reactivación por administrador

---

## ESTADO DE IMPLEMENTACIÓN

> **Esta sección documenta las diferencias entre el diseño (tarjeta) y el código actual.**

| Característica | Tarjeta (diseño) | Código actual | Estado |
|---|---|---|---|
| Mecanismo de token | JWT (access + refresh) | DRF Token (clave fija) | ⚠️ PENDIENTE |
| Login con email | username o email | Solo username | ⚠️ PENDIENTE |
| Campo `is_locked` en User | Campo en modelo User | Tabla separada `LoginLockout` | ⚠️ PENDIENTE |
| Throttling por IP (429) | `LoginRateThrottle` por IP | Bloqueo por username vía `LoginLockout` (403) | ⚠️ PENDIENTE |
| Cuenta inactiva 90 días | Automático | NO implementado | ⚠️ PENDIENTE |
| Sesion duplicada (A5) | Opcion de cerrar anterior | NO implementado | ⚠️ PENDIENTE |
| Modelo de auditoria | `UserActionLog` | `LoginAttempt` | ⚠️ Nombre diferente |
| Wrapper de response | Sin `data` wrapper | `{"success": true, "data": {...}}` | ⚠️ Diferente |
| Campos en user response | `full_name`, `is_locked`, `last_login`, `date_joined` | Solo `id`, `username`, `email`, `first_name`, `last_name` | ⚠️ PENDIENTE |
| `locked_until` en 403 | `locked_until` timestamp | `locked_minutes` entero | ⚠️ Diferente |
| `first_login` en response | NO documentado | Implementado (calculo dinamico) | ✅ Extra implementado |
| Bloqueo base | Por username (5 intentos) | Por username (5 intentos) | ✅ Correcto |
| Duracion bloqueo | 15 minutos | 15 minutos | ✅ Correcto |
| Registro de auditoria | Todos los intentos | Todos los intentos (`LoginAttempt`) | ✅ Correcto |
| PostgreSQL para sesion | `django_session` | `SessionLog` tabla custom | ✅ Correcto |

**Implementacion actual del response (lo que retorna hoy el codigo):**

```json
{
  "success": true,
  "message": "Login exitoso",
  "data": {
    "user": {
      "id": 123,
      "username": "juan.perez",
      "email": "juan.perez@empresa.com",
      "first_name": "Juan",
      "last_name": "Pérez"
    },
    "token": "abc123def456...",
    "session_key": "abcdef1234567890",
    "first_login": false
  }
}
```

**Error actual (lo que retorna hoy el codigo):**

```json
{
  "success": false,
  "error": {
    "error_code": "INVALID_CREDENTIALS",
    "message": "Credenciales inválidas. Te quedan 3 intentos.",
    "details": { "attempts_remaining": 3 },
    "status_code": 401
  }
}
```

---

Sistema IACT - Análisis IVR
Version: 2.0.0 | Fecha documento: 2026-03-15 | Modelo RBAC: v7.0.0
