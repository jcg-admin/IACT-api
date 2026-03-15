## TARJETA: auth.login

Nombre para UI: Iniciar Sesion
Modulo: MOD_Auth - Autenticacion
ID Caso de Uso: No documentado en E1
Prioridad: CRITICA
Frecuencia: Muy Alta
Estado: Activo

### DESCRIPCION

Permite al usuario autenticarse en el sistema ingresando su nombre de usuario y contrasena. El sistema valida las credenciales, verifica el estado de la cuenta, registra el intento de acceso y genera un token de sesion. Incluye proteccion contra ataques de fuerza bruta mediante bloqueo temporal despues de multiples intentos fallidos.

### PRECONDICIONES

- Usuario no tiene sesion activa (endpoint es publico)
- Usuario existe en el sistema

### FLUJO PRINCIPAL (9 PASOS)

1. Usuario navega a pantalla de login
2. Usuario ingresa username y contrasena
3. Sistema valida que los campos no esten vacios
4. Sistema verifica que la cuenta no este bloqueada temporalmente
5. Sistema autentica las credenciales contra la base de datos
6. Sistema verifica que el usuario este activo (is_active = true)
7. Sistema crea sesion de Django y genera token DRF
8. Sistema registra intento exitoso en LoginAttempt y crea SessionLog
9. Sistema resetea contador de intentos fallidos y retorna datos de sesion

### FLUJOS ALTERNATIVOS

**A1. Credenciales invalidas (paso 5)**

- Sistema no puede autenticar las credenciales
- Sistema registra intento fallido en LoginAttempt
- Sistema incrementa contador en LoginLockout
- Si intentos restantes > 0: retorna INVALID_CREDENTIALS con details.attempts_remaining = N
- Si intentos restantes = 0 (5to intento): bloquea cuenta y retorna ACCOUNT_LOCKED con details = {} (sin locked_minutes, el bloqueo acaba de crearse)
- Caso de uso termina

**A2. Cuenta bloqueada (paso 4)**

- Sistema detecta que locked_until > ahora
- Sistema registra intento en LoginAttempt (success = false)
- Sistema retorna error con tiempo restante de bloqueo
- No se realizan mas validaciones
- Caso de uso termina

**A3. Usuario inactivo (paso 6)**

- Sistema autentica credenciales correctamente
- Sistema detecta que is_active = false
- Sistema registra intento fallido en LoginAttempt
- Sistema retorna error indicando cuenta inactiva
- Caso de uso termina

**A4. Campos vacios (paso 3)**

- Serializer detecta campo username o password vacio
- Sistema retorna error de validacion 400
- No se realiza ninguna consulta a base de datos
- Caso de uso termina

**A5. Primera vez que inicia sesion (paso 9)**

- Sistema detecta que first_login = true contando LoginAttempts exitosos anteriores (no es campo del modelo User, se calcula dinamicamente)
- Si LoginAttempt(user, success=True).count() <= 1, es el primer login
- Respuesta incluye first_login: true
- Frontend puede mostrar pantalla de bienvenida o configuracion inicial
- Caso de uso termina normalmente

### POSTCONDICIONES

Exito:

- Sesion de Django creada
- Token DRF generado o recuperado
- LoginAttempt registrado con success = true
- SessionLog creado con is_active = true
- Contador de intentos fallidos reseteado en LoginLockout

Fallo:

- LoginAttempt registrado con success = false
- Contador de intentos fallidos incrementado
- Si se alcanzo el limite: LoginLockout.locked_until establecido

### REGLAS DE NEGOCIO

- RN-001: Maximo 5 intentos fallidos consecutivos antes de bloqueo
- RN-002: Bloqueo temporal dura 15 minutos
- RN-003: Ventana de conteo de intentos: 15 minutos
- RN-004: Bloqueo se levanta automaticamente al expirar locked_until
- RN-005: Inicio de sesion exitoso resetea el contador de intentos fallidos
- RN-006: Usuario inactivo (is_active = false) no puede iniciar sesion aunque las credenciales sean correctas
- RN-007: El sistema devuelve el mismo mensaje de error para usuario inexistente y contrasena incorrecta (previene enumeracion de usuarios)
- RN-008: Token DRF se reutiliza si ya existe (get_or_create), no se genera uno nuevo en cada login

### RESTRICCIONES TECNICAS

- CNST-005: Contrasena hasheada con PBKDF2, minimo 8 caracteres, maximo 128
- CNST-005: Maximo 5 intentos, bloqueo 15 minutos
- CNST-010: LoginLockout almacenado en PostgreSQL (sin Redis ni cache)
- CNST-002: SessionLog almacenado en PostgreSQL
- Endpoint publico: AllowAny (no requiere autenticacion previa)

### REGLAS SoD

Ninguna

### MENSAJES DEL SISTEMA

Exito:

- AUTH-001: "Login exitoso"

Errores:

- INVALID_CREDENTIALS: "Credenciales invalidas. Te quedan X intentos." (credenciales incorrectas)
- ACCOUNT_LOCKED: "Cuenta bloqueada. Intenta en 15 minutos." (cuenta bloqueada)
- USER_INACTIVE: "Usuario inactivo. Contacte al administrador." (usuario desactivado)

Validacion:

- 400 Bad Request: "Este campo es requerido." (username o password vacios)

### IMPLEMENTACION TECNICA

**Iniciar sesion**

Endpoint: POST /api/v1/auth/login/

Request:

```json
{
  "username": "john.doe",
  "password": "micontrasena123"
}
```

Response Exitosa (200 OK):

```json
{
  "success": true,
  "message": "Login exitoso",
  "data": {
    "user": {
      "id": 123,
      "username": "john.doe",
      "email": "john.doe@empresa.com",
      "first_name": "John",
      "last_name": "Doe"
    },
    "token": "abc123def456xyz789...",
    "session_key": "abcdef1234567890abcdef1234567890",
    "first_login": false
  }
}
```

Response - Credenciales invalidas (401 Unauthorized):

```json
{
  "success": false,
  "error": {
    "error_code": "INVALID_CREDENTIALS",
    "message": "Credenciales invalidas. Te quedan 3 intentos.",
    "details": {
      "attempts_remaining": 3
    },
    "status_code": 401
  }
}
```

Response - Cuenta bloqueada (403 Forbidden):

```json
{
  "success": false,
  "error": {
    "error_code": "ACCOUNT_LOCKED",
    "message": "Cuenta bloqueada. Intenta en 15 minutos.",
    "details": {
      "locked_minutes": 15
    },
    "status_code": 403
  }
}
```

Response - Usuario inactivo (403 Forbidden):

```json
{
  "success": false,
  "error": {
    "error_code": "USER_INACTIVE",
    "message": "Usuario 'john.doe' inactivo. Contacte al administrador.",
    "details": {},
    "status_code": 403
  }
}
```

Codigos HTTP:

- 200 OK: Login exitoso
- 400 Bad Request: Campos vacios o formato invalido
- 401 Unauthorized: Credenciales invalidas
- 403 Forbidden: Cuenta bloqueada o usuario inactivo
- 500 Internal Server Error: Error del servidor

### VALIDACIONES

Validacion de Entrada (LoginSerializer):

- username: requerido, max 150 caracteres, no puede ser solo espacios (se aplica strip)
- password: requerido, write_only, no puede estar vacio

Validacion de Negocio (AuthenticationService):

- Cuenta no esta bloqueada (LoginLockout.is_locked())
- Credenciales correctas (Django authenticate())
- Usuario activo (user.is_active = true)

### AUDITORIA

Se registra en LoginAttempt (tabla: tbl_intentos_login):

- user: FK al usuario (null si el username no existe)
- username: username intentado
- success: true o false
- ip_address: IP desde donde se realizo el intento
- user_agent: navegador y dispositivo
- created_at: timestamp exacto del intento

Ejemplo de log - Login exitoso:

```json
{
  "table": "tbl_intentos_login",
  "user_id": 123,
  "username": "john.doe",
  "success": true,
  "ip_address": "192.168.1.100",
  "user_agent": "Chrome/120.0",
  "created_at": "2026-02-24T10:30:00Z"
}
```

Ejemplo de log - Intento fallido:

```json
{
  "table": "tbl_intentos_login",
  "user_id": null,
  "username": "john.doe",
  "success": false,
  "ip_address": "201.123.45.67",
  "user_agent": "Firefox/118.0",
  "created_at": "2026-02-24T10:31:00Z"
}
```

### SEGURIDAD

Protecciones Implementadas:

- Bloqueo temporal tras 5 intentos fallidos (CNST-005)
- Mismo mensaje de error para usuario inexistente y contrasena incorrecta (previene enumeracion)
- Contrasenas hasheadas con PBKDF2 (no almacenadas en texto plano)
- Todo intento (exitoso o fallido) queda registrado en LoginAttempt
- IP y User-Agent registrados en cada intento
- Bloqueo almacenado en PostgreSQL (persiste entre reinicios del servidor)

### NOTAS IMPORTANTES

- El token DRF se reutiliza si ya existe para el usuario (get_or_create); no se genera uno nuevo en cada login
- El bloqueo se maneja por username, no por IP
- Contador de intentos fallidos se resetea completamente tras login exitoso
- SessionLog registra el inicio de sesion con is_active = true; se actualiza al hacer logout
- El campo first_login en la respuesta se calcula dinamicamente contando LoginAttempts exitosos; no es un campo del modelo User
- details.locked_minutes solo aparece cuando la cuenta ya estaba bloqueada (intento posterior al lockout); al alcanzar el 5to intento fallido se retorna ACCOUNT_LOCKED con details vacio
- La sesion de Django expira a la hora (SESSION_TIMEOUT_SECONDS = 3600)
- El endpoint no requiere autenticacion (AllowAny); cualquier cliente puede intentar login
- La recuperacion de contrasena NO usa email, usa preguntas de seguridad (5 preguntas obligatorias, CNST-001)

---

Sistema IACT - Analisis IVR
Version: 1.1.0 | Fecha documento: 2026-03-15 | Modelo RBAC: v7.0.0
