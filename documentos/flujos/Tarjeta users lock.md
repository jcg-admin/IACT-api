## TARJETA: users.lock

Nombre para UI: Bloquear Usuario
Modulo: MOD_Users - Gestion de Usuarios
ID Caso de Uso: UC-010
Prioridad: ALTA
Frecuencia: Ocasional
Estado: Activo

### DESCRIPCION

Permite bloquear temporalmente una cuenta de usuario impidiendo que inicie sesion en el sistema. El bloqueo es temporal con duracion configurable (por defecto 15 minutos) y puede extenderse segun necesidad. Las sesiones activas NO se invalidan automaticamente, pero el usuario no podra iniciar nuevas sesiones mientras este bloqueado.

### PRECONDICIONES

- Usuario tiene sesion activa
- Usuario tiene funcion users.lock asignada
- Usuario objetivo existe en el sistema
- Usuario objetivo esta activo (is_active=true)
- Usuario objetivo NO esta bloqueado actualmente

### FLUJO PRINCIPAL (12 PASOS)

1. Usuario navega a "Gestion de Usuarios"
2. Usuario busca y selecciona usuario a bloquear
3. Sistema muestra datos del usuario seleccionado
4. Usuario hace clic en "Bloquear Usuario"
5. Sistema muestra dialogo de bloqueo
6. Usuario selecciona duracion del bloqueo (15 min, 1 hora, 24 horas, indefinido)
7. Usuario ingresa razon del bloqueo (minimo 20 caracteres)
8. Usuario confirma bloqueo
9. Sistema valida razon del bloqueo
10. Sistema marca usuario como bloqueado (is_locked=true, locked_until=timestamp)
11. Sistema registra bloqueo en AuditLog
12. Sistema muestra confirmacion: "Usuario bloqueado exitosamente"

### FLUJOS ALTERNATIVOS

**A1. Usuario cancela bloqueo (paso 8)**

- Usuario hace clic en "Cancelar"
- Sistema cierra dialogo
- Usuario sin cambios
- Caso de uso termina

**A2. Razon insuficiente (paso 9)**

- Sistema detecta razon menor a 20 caracteres
- Sistema muestra error: "Razon debe tener al menos 20 caracteres" (USR-017)
- Usuario permanece en dialogo
- Caso de uso puede reintentar desde paso 7

**A3. Usuario sin funcion users.lock**

- Sistema detecta que usuario no tiene funcion
- Sistema muestra error 403: "No tiene permisos para bloquear usuarios" (USR-018)
- Usuario es redirigido a pagina anterior
- Caso de uso termina

**A4. Usuario no encontrado (paso 3)**

- Sistema no encuentra usuario con ID especificado
- Sistema muestra error: "Usuario no encontrado" (USR-011)
- Usuario es redirigido a lista de usuarios
- Caso de uso termina

**A5. Usuario ya esta bloqueado (paso 10)**

- Sistema detecta que usuario ya tiene is_locked=true
- Sistema muestra mensaje: "Usuario ya esta bloqueado hasta {locked_until}" (INFO-017)
- Sistema ofrece opcion de extender bloqueo
- Caso de uso termina

**A6. Usuario objetivo inactivo (paso 10)**

- Sistema detecta que usuario tiene is_active=false
- Sistema muestra error: "No puede bloquear usuario inactivo" (USR-019)
- Sistema rechaza operacion
- Caso de uso termina

### POSTCONDICIONES

Exito:

- Usuario marcado como bloqueado (is_locked=true)
- locked_until registrado con timestamp de fin
- Bloqueo registrado en AuditLog
- Usuario no puede iniciar nuevas sesiones

Fallo:

- Usuario sin cambios
- Usuario puede reintentar

### REGLAS DE NEGOCIO

- RN-057: Razon del bloqueo obligatoria minimo 20 caracteres
- RN-058: Duracion por defecto: 15 minutos
- RN-059: Duraciones permitidas: 15 min, 1 hora, 24 horas, indefinido
- RN-060: Bloqueo indefinido requiere desbloqueo manual
- RN-061: Sesiones activas NO se invalidan automaticamente
- RN-062: Usuario bloqueado NO puede iniciar nuevas sesiones
- RN-063: Bloqueo automatico se libera al llegar a locked_until

### RESTRICCIONES TECNICAS

Ninguna restriccion tecnica especifica (usa campos estandar del modelo User)

### REGLAS SoD

Ninguna

### MENSAJES DEL SISTEMA

Errores:

- USR-011: "Usuario no encontrado" (ID no existe)
- USR-017: "Razon debe tener al menos 20 caracteres" (razon corta)
- USR-018: "No tiene permisos para bloquear usuarios" (sin funcion users.lock)
- USR-019: "No puede bloquear usuario inactivo" (usuario eliminado)

Confirmacion:

- OK-010: "Usuario bloqueado exitosamente" (bloqueo exitoso)

Advertencias:

- WARN-005: "Sesiones activas del usuario NO se cerraran automaticamente" (informacion)
- WARN-006: "Usuario no podra iniciar sesion hasta {locked_until}" (confirmacion)

Informativos:

- INFO-017: "Usuario ya esta bloqueado hasta {locked_until}" (ya bloqueado)
- INFO-018: "El bloqueo se liberara automaticamente en {duration}" (recordatorio)

### IMPLEMENTACION TECNICA

**Bloquear usuario**

Endpoint: POST /api/v1/users/{user_id}/lock

Request:

```json
{
  "duration_minutes": 15,
  "reason": "Actividad sospechosa detectada. Revision de seguridad pendiente. Ticket SEC-2024-0123."
}
```

Opciones de duration_minutes:

- 15: 15 minutos
- 60: 1 hora
- 1440: 24 horas
- 0: Indefinido (requiere desbloqueo manual)

Response Exitosa (200 OK):

```json
{
  "success": true,
  "message": "Usuario bloqueado exitosamente",
  "user": {
    "id": 150,
    "username": "plopez",
    "email": "pedro.lopez@empresa.com",
    "first_name": "Pedro Antonio",
    "last_name": "Lopez Garcia",
    "is_active": true,
    "is_locked": true,
    "locked_until": "2026-02-25T15:00:00Z"
  },
  "lock_details": {
    "locked_at": "2026-02-25T14:45:00Z",
    "locked_by": 123,
    "duration_minutes": 15,
    "reason": "Actividad sospechosa detectada. Revision de seguridad pendiente. Ticket SEC-2024-0123.",
    "unlock_automatic": true
  }
}
```

Response - Razon insuficiente (400 Bad Request):

```json
{
  "success": false,
  "error_code": "USR-017",
  "message": "Razon debe tener al menos 20 caracteres",
  "current_length": 15,
  "required_length": 20
}
```

Response - Usuario ya bloqueado (400 Bad Request):

```json
{
  "success": false,
  "error_code": "INFO-017",
  "message": "Usuario ya esta bloqueado hasta 2026-02-25T15:00:00Z",
  "locked_until": "2026-02-25T15:00:00Z",
  "can_extend": true
}
```

Response - Usuario inactivo (400 Bad Request):

```json
{
  "success": false,
  "error_code": "USR-019",
  "message": "No puede bloquear usuario inactivo",
  "user_id": 150,
  "user_status": "inactive"
}
```

Response - Usuario no encontrado (404 Not Found):

```json
{
  "success": false,
  "error_code": "USR-011",
  "message": "Usuario no encontrado",
  "user_id": 999
}
```

Response - Sin permisos (403 Forbidden):

```json
{
  "success": false,
  "error_code": "USR-018",
  "message": "No tiene permisos para bloquear usuarios"
}
```

Codigos HTTP:

- 200 OK: Usuario bloqueado exitosamente
- 400 Bad Request: Razon invalida, usuario ya bloqueado, o usuario inactivo
- 403 Forbidden: Sin funcion users.lock
- 404 Not Found: Usuario no existe
- 500 Internal Server Error: Error del servidor

### VALIDACIONES

Validacion de Usuario:

- Usuario objetivo existe en base de datos
- Usuario objetivo tiene is_active=true
- Usuario objetivo NO tiene is_locked=true (no ya bloqueado)

Validacion de Razon:

- Obligatoria
- Minimo 20 caracteres
- Maximo 500 caracteres
- Debe explicar razon del bloqueo

Validacion de Duracion:

- Valores permitidos: 15, 60, 1440, 0 (minutos)
- Por defecto: 15 minutos si no se especifica
- 0 = indefinido (requiere desbloqueo manual)

Proceso de Bloqueo:

1. Marcar is_locked = true
2. Calcular locked_until = NOW() + duration_minutes
3. Registrar locked_by = user_id del ejecutor
4. Registrar lock_reason = razon ingresada
5. Registrar en AuditLog

### AUDITORIA

Se registra en AuditLog:

- Accion: lock_user
- Usuario: user_id (quien bloquea)
- Timestamp: hora exacta
- IP Address: IP desde donde bloquea
- User Agent: navegador y dispositivo
- Detalles: ID del usuario bloqueado, username, razon, duracion, locked_until, si es indefinido

Ejemplo de log:

```json
{
  "timestamp": "2026-02-25T14:45:00Z",
  "action": "lock_user",
  "user_id": 123,
  "target_user_id": 150,
  "ip_address": "192.168.1.100",
  "user_agent": "Chrome/120.0",
  "result": "success",
  "details": {
    "locked_username": "plopez",
    "locked_email": "pedro.lopez@empresa.com",
    "reason": "Actividad sospechosa detectada. Revision de seguridad pendiente. Ticket SEC-2024-0123.",
    "duration_minutes": 15,
    "locked_until": "2026-02-25T15:00:00Z",
    "indefinite": false
  }
}
```

### SEGURIDAD

Protecciones Implementadas:

- Razon obligatoria (trazabilidad)
- Bloqueo temporal por defecto (previene bloqueos permanentes accidentales)
- Usuario NO puede iniciar nuevas sesiones mientras bloqueado
- Bloqueo completamente auditado
- Desbloqueo automatico al expirar (si no es indefinido)

Comportamiento Durante Bloqueo:

- Usuario bloqueado NO puede hacer login
- Sesiones activas continuan funcionando
- Sistema muestra mensaje de cuenta bloqueada al intentar login
- Muestra tiempo restante de bloqueo

Diferencia entre Bloqueo y Eliminacion:

- users.lock (bloqueo temporal): is_locked=true, temporal con locked_until, sesiones activas continuan, NO puede iniciar nuevas sesiones, desbloqueo automatico o manual
- users.delete (soft delete): is_active=false, permanente hasta restauracion, todas las sesiones invalidadas, todas las funciones revocadas, requiere restauracion manual

### NOTAS IMPORTANTES

- Bloqueo por defecto: 15 minutos
- Sesiones activas NO se cierran automaticamente
- Usuario NO puede iniciar nuevas sesiones mientras bloqueado
- Bloqueo temporal se libera automaticamente al llegar a locked_until
- Bloqueo indefinido requiere desbloqueo manual con users.unlock
- Razon del bloqueo obligatoria minimo 20 caracteres

Duraciones Disponibles:

- 15 minutos: Bloqueo breve (por defecto)
- 1 hora: Bloqueo medio
- 24 horas: Bloqueo extendido
- Indefinido: Requiere desbloqueo manual

Diferencia entre Bloqueo Automatico y Manual:

- Bloqueo automatico (por intentos fallidos): 5 intentos fallidos de login, 15 minutos fijos, sin funcion users.lock requerida, registrado automaticamente
- Bloqueo manual (users.lock): requiere funcion users.lock, duracion configurable, razon obligatoria, decision administrativa

Sesiones Activas:

- NO se invalidan al bloquear usuario
- Continuan funcionando normalmente
- Para cerrar sesiones usar auth.manage_sessions
- O combinar users.lock con invalidacion manual de sesiones

Desbloqueo:

- Automatico: Al llegar a locked_until
- Manual: Con funcion users.unlock

Casos de Uso Tipicos:

- Actividad sospechosa detectada
- Multiples intentos fallidos manuales
- Investigacion de seguridad en curso
- Solicitud del usuario (autoexclusion temporal)
- Violacion de politicas de uso

---

Sistema IACT - Analisis IVR
Version: 1.0.0 | Fecha documento: 2026-03-14 | Modelo RBAC: v7.0.0
