# DICCIONARIO DE FLUJOS - TARJETAS DETALLADAS

Sistema IACT - Analisis IVR
Version: 1.0.0
Fecha: 2026-03-14
Modelo RBAC: v7.0.0
Formato: Tarjetas Individuales por Funcion

---

## INFORMACION GENERAL

Este diccionario documenta los flujos de cada funcion atomica del sistema IACT mediante tarjetas detalladas. Cada tarjeta describe el comportamiento completo de una funcion: flujo principal, flujos alternativos, validaciones, mensajes, implementacion tecnica y auditoria.

Estado actual: 2 de 46 funciones documentadas (4.3%)

---

## MODULOS

- MOD_Auth - Autenticacion (1/4 funciones documentadas)
- MOD_Users - Gestion de Usuarios (0/9 funciones documentadas)
- MOD_Access - Gestion de Permisos (0/3 funciones documentadas)
- MOD_Reports - Reportes y Analisis (0/6 funciones documentadas)
- MOD_Audit - Auditoria y Compliance (0/3 funciones documentadas)

---

## INDICE DE FUNCIONES DOCUMENTADAS

### MOD_Auth - Autenticacion

1. auth.login - Iniciar Sesion
2. auth.manage_sessions - Gestionar Sesiones

---

## ESTRUCTURA DE CADA TARJETA

Cada tarjeta incluye:

- Nombre para UI, Modulo, ID Caso de Uso, Prioridad, Frecuencia, Estado
- Descripcion
- Precondiciones
- Flujo Principal (pasos numerados)
- Flujos Alternativos
- Postcondiciones
- Reglas de Negocio
- Restricciones Tecnicas
- Reglas SoD (si aplica)
- Mensajes del Sistema
- Implementacion Tecnica (endpoint, request/response JSON, codigos HTTP)
- Validaciones
- Auditoria (con ejemplo JSON)
- Seguridad
- Notas Importantes

---

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
- Si contador < 5: muestra mensaje con intentos restantes
- Si contador = 5: bloquea cuenta por 15 minutos y muestra mensaje de bloqueo
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

- Sistema detecta que first_login = true (campo en User)
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
- El campo first_login en la respuesta indica si es la primera vez que el usuario inicia sesion
- La sesion de Django expira a la hora (SESSION_TIMEOUT_SECONDS = 3600)
- El endpoint no requiere autenticacion (AllowAny); cualquier cliente puede intentar login
- La recuperacion de contrasena NO usa email, usa preguntas de seguridad (5 preguntas obligatorias, CNST-001)

---

## TARJETA: auth.manage_sessions

Nombre para UI: Gestionar Sesiones
Modulo: MOD_Auth - Autenticacion
ID Caso de Uso: No documentado en E1
Prioridad: MEDIA
Frecuencia: Ocasional
Estado: Activo

### DESCRIPCION

Permite al usuario ver todas sus sesiones activas en diferentes dispositivos y cerrar sesiones especificas de forma remota. Esto es util para controlar el acceso a la cuenta desde multiples dispositivos y cerrar sesiones olvidadas o no reconocidas.

### PRECONDICIONES

- Usuario tiene sesion activa
- Usuario esta autenticado

### FLUJO PRINCIPAL (10 PASOS)

1. Usuario navega a seccion "Gestionar Sesiones" o "Dispositivos Activos"
2. Sistema carga todas las sesiones activas del usuario
3. Sistema muestra lista de sesiones con detalles
4. Usuario revisa sesiones activas
5. Usuario identifica sesion a cerrar
6. Usuario hace clic en boton "Cerrar Sesion" junto a la sesion especifica
7. Sistema muestra confirmacion: "Desea cerrar esta sesion?"
8. Usuario confirma
9. Sistema invalida la sesion seleccionada
10. Sistema actualiza lista de sesiones activas

### FLUJOS ALTERNATIVOS

**A1. Usuario cancela cierre (paso 8)**

- Usuario hace clic en "Cancelar"
- Sistema cierra dialogo
- Lista de sesiones permanece sin cambios
- Caso de uso termina

**A2. Cerrar todas las demas sesiones (desde paso 4)**

- Usuario hace clic en "Cerrar Todas las Demas Sesiones"
- Sistema muestra confirmacion: "Desea cerrar todas las sesiones excepto la actual?"
- Usuario confirma
- Sistema invalida todas las sesiones excepto la actual
- Sistema actualiza lista mostrando solo sesion actual
- Caso de uso termina

**A3. No hay otras sesiones activas (paso 3)**

- Sistema detecta que solo hay sesion actual
- Sistema muestra mensaje: "Solo tiene una sesion activa (esta sesion)"
- No muestra opciones de cerrar otras sesiones
- Caso de uso termina

**A4. Sesion ya expirada (paso 9)**

- Sistema detecta que sesion seleccionada ya expiro
- Sistema la marca como inactiva
- Sistema actualiza lista automaticamente
- Sistema muestra mensaje: "Sesion ya expirada"
- Caso de uso continua

**A5. Intentar cerrar sesion actual (paso 6)**

- Usuario intenta cerrar su sesion actual
- Sistema detecta que es la sesion actual
- Sistema muestra advertencia: "Esta es su sesion actual. Use 'Cerrar Sesion' del menu principal"
- Sistema NO permite cerrar sesion actual desde gestion
- Caso de uso continua

### POSTCONDICIONES

Exito:

- Sesion(es) seleccionada(s) invalidada(s)
- Lista de sesiones actualizada
- Usuario permanece autenticado en sesion actual

Fallo:

- Si hay error tecnico, sesion actual permanece activa
- Usuario puede reintentar operacion

### REGLAS DE NEGOCIO

- RN-020: Usuario puede tener maximo 5 sesiones simultaneas
- RN-021: Al crear sesion numero 6, se invalida automaticamente la mas antigua
- RN-022: Usuario NO puede cerrar su sesion actual desde gestion de sesiones
- RN-023: Usuario puede ver todas sus sesiones activas
- RN-024: Usuario solo puede cerrar sus propias sesiones
- RN-025: Cerrar sesion es irreversible (requiere nuevo login)

### RESTRICCIONES TECNICAS

- CNST-002: Sesiones almacenadas en base de datos PostgreSQL
  - Tabla: UserSession
  - Timeout: 8 horas absoluto
  - Maximo 5 sesiones concurrentes

### REGLAS SoD

Ninguna

### MENSAJES DEL SISTEMA

Confirmacion:

- SES-005: "Sesion cerrada exitosamente" (sesion remota cerrada)
- SES-006: "Todas las demas sesiones han sido cerradas" (cierre masivo)

Errores:

- SES-004: "Ha alcanzado el limite de sesiones simultaneas" (al intentar crear sesion numero 6)
- SES-007: "No puede cerrar su sesion actual desde aqui" (intenta cerrar sesion actual)

Informativos:

- INFO-005: "Solo tiene una sesion activa (esta sesion)" (sin otras sesiones)
- INFO-006: "Sesion ya expirada" (sesion seleccionada expiro)

### IMPLEMENTACION TECNICA

**Listar sesiones activas**

Endpoint: GET /api/v1/auth/sessions

Response (200 OK):

```json
{
  "success": true,
  "sessions": [
    {
      "session_id": "abc123xyz",
      "is_current": true,
      "device": "Chrome en Windows",
      "ip_address": "192.168.1.100",
      "location": "Guadalajara, Mexico",
      "created_at": "2026-02-24T10:30:00Z",
      "last_activity": "2026-02-24T15:45:00Z",
      "expires_at": "2026-02-24T18:30:00Z"
    },
    {
      "session_id": "def456uvw",
      "is_current": false,
      "device": "Safari en iPhone",
      "ip_address": "192.168.1.105",
      "location": "Guadalajara, Mexico",
      "created_at": "2026-02-23T08:15:00Z",
      "last_activity": "2026-02-24T12:20:00Z",
      "expires_at": "2026-02-24T16:15:00Z"
    },
    {
      "session_id": "ghi789rst",
      "is_current": false,
      "device": "Firefox en Linux",
      "ip_address": "201.123.45.67",
      "location": "Ciudad de Mexico, Mexico",
      "created_at": "2026-02-22T14:00:00Z",
      "last_activity": "2026-02-24T09:30:00Z",
      "expires_at": "2026-02-24T22:00:00Z"
    }
  ],
  "total_sessions": 3,
  "max_sessions": 5
}
```

**Cerrar sesion especifica**

Endpoint: DELETE /api/v1/auth/sessions/{session_id}

Request:

```
DELETE /api/v1/auth/sessions/def456uvw
```

Response Exitosa (200 OK):

```json
{
  "success": true,
  "message": "Sesion cerrada exitosamente",
  "session_id": "def456uvw",
  "sessions_remaining": 2
}
```

Response - Intentar cerrar sesion actual (400 Bad Request):

```json
{
  "success": false,
  "error_code": "SES-007",
  "message": "No puede cerrar su sesion actual desde aqui"
}
```

Response - Sesion no existe (404 Not Found):

```json
{
  "success": false,
  "error_code": "SES-008",
  "message": "Sesion no encontrada o ya expirada"
}
```

**Cerrar todas las demas sesiones**

Endpoint: DELETE /api/v1/auth/sessions/others

Response Exitosa (200 OK):

```json
{
  "success": true,
  "message": "Todas las demas sesiones han sido cerradas",
  "sessions_closed": 4,
  "sessions_remaining": 1
}
```

Response - Sin otras sesiones (200 OK):

```json
{
  "success": true,
  "message": "No hay otras sesiones activas para cerrar",
  "sessions_closed": 0,
  "sessions_remaining": 1
}
```

Codigos HTTP:

- 200 OK: Operacion exitosa
- 400 Bad Request: Intento de cerrar sesion actual
- 404 Not Found: Sesion no existe
- 500 Internal Server Error: Error del servidor

### VALIDACIONES

Validacion de Sesion:

- Sesion existe en base de datos
- Sesion pertenece al usuario autenticado
- Sesion NO es la sesion actual (para cierre individual)

Validacion de Propiedad:

- Usuario solo puede ver y cerrar sus propias sesiones
- No puede acceder a sesiones de otros usuarios

Limite de Sesiones:

- Sistema mantiene maximo 5 sesiones activas
- Al crear sesion numero 6, invalida automaticamente la mas antigua

### AUDITORIA

Se registra en AuditLog:

- Accion: close_remote_session
- Usuario: user_id
- Timestamp: hora exacta
- IP Address: IP desde donde se solicita cierre
- User Agent: navegador y dispositivo
- Detalles: session_id cerrado, IP de la sesion cerrada, dispositivo de la sesion cerrada, si fue cierre individual o masivo

Ejemplo de log - Cerrar sesion individual:

```json
{
  "timestamp": "2026-02-24T15:45:00Z",
  "action": "close_remote_session",
  "user_id": 123,
  "ip_address": "192.168.1.100",
  "user_agent": "Chrome/120.0",
  "result": "success",
  "details": {
    "closed_session_id": "def456uvw",
    "closed_session_ip": "192.168.1.105",
    "closed_session_device": "Safari en iPhone",
    "closure_type": "individual"
  }
}
```

Ejemplo de log - Cerrar todas las demas:

```json
{
  "timestamp": "2026-02-24T15:50:00Z",
  "action": "close_all_other_sessions",
  "user_id": 123,
  "ip_address": "192.168.1.100",
  "user_agent": "Chrome/120.0",
  "result": "success",
  "details": {
    "sessions_closed": 4,
    "session_ids": ["def456uvw", "ghi789rst", "jkl012mno", "pqr345stu"],
    "closure_type": "bulk"
  }
}
```

### SEGURIDAD

Protecciones Implementadas:

- Usuario solo ve sus propias sesiones
- Usuario solo puede cerrar sus propias sesiones
- Sesion actual no puede cerrarse desde gestion (previene cierre accidental)
- Todas las acciones son auditadas
- Informacion de ubicacion basada en IP (aproximada)

Informacion Mostrada por Sesion:

- Dispositivo y navegador (del User-Agent)
- IP Address
- Ubicacion aproximada (basada en IP)
- Fecha y hora de creacion
- Ultima actividad
- Fecha y hora de expiracion
- Si es la sesion actual

### NOTAS IMPORTANTES

- Usuario puede tener maximo 5 sesiones simultaneas
- Cuando se crea sesion numero 6, automaticamente se cierra la mas antigua
- Sesion actual NO puede cerrarse desde gestion de sesiones
- Para cerrar sesion actual, usar opcion "Cerrar Sesion" del menu principal
- Cerrar sesion remota es irreversible, requiere nuevo login en ese dispositivo
- Lista de sesiones se actualiza automaticamente cada 30 segundos
- Sesiones expiradas se muestran durante 24 horas y luego se eliminan automaticamente
- Ubicacion es aproximada basada en IP (no siempre precisa)
- Usuario puede cerrar todas las demas sesiones con un solo clic

Casos de Uso Tipicos:

- Olvido cerrar sesion en computadora publica
- Cambio de dispositivo y quiere cerrar sesion anterior
- Sospecha de acceso no autorizado
- Limpieza periodica de sesiones antiguas

Timeouts:

- Timeout absoluto: 8 horas desde login
- Timeout por inactividad: 2 horas sin actividad
- Sesion numero 6 invalida automaticamente la mas antigua

---

Documento: DICCIONARIO DE FLUJOS - TARJETAS DETALLADAS
Sistema IACT - Analisis IVR
Version: 1.0.0 | Fecha documento: 2026-03-14 | Modelo RBAC: v7.0.0
