## TARJETA: users.unlock

Nombre para UI: Desbloquear Usuario
Modulo: MOD_Users - Gestion de Usuarios
ID Caso de Uso: UC-011
Prioridad: ALTA
Frecuencia: Ocasional
Estado: Activo

### DESCRIPCION

Permite desbloquear manualmente una cuenta de usuario que esta bloqueada, ya sea por bloqueo manual previo o por bloqueo automatico por intentos fallidos. El desbloqueo elimina la restriccion de inicio de sesion y permite al usuario acceder nuevamente al sistema inmediatamente.

### PRECONDICIONES

- Usuario tiene sesion activa
- Usuario tiene funcion users.unlock asignada
- Usuario objetivo existe en el sistema
- Usuario objetivo esta bloqueado (is_locked=true)

### FLUJO PRINCIPAL (12 PASOS)

1. Usuario navega a "Gestion de Usuarios"
2. Usuario busca y selecciona usuario bloqueado
3. Sistema muestra datos del usuario con indicador de bloqueo
4. Sistema muestra informacion del bloqueo (razon, duracion, tiempo restante)
5. Usuario hace clic en "Desbloquear Usuario"
6. Sistema muestra dialogo de desbloqueo
7. Usuario ingresa razon del desbloqueo (minimo 20 caracteres)
8. Usuario confirma desbloqueo
9. Sistema valida razon del desbloqueo
10. Sistema marca usuario como desbloqueado (is_locked=false, locked_until=null)
11. Sistema registra desbloqueo en AuditLog
12. Sistema muestra confirmacion: "Usuario desbloqueado exitosamente"

### FLUJOS ALTERNATIVOS

**A1. Usuario cancela desbloqueo (paso 8)**

- Usuario hace clic en "Cancelar"
- Sistema cierra dialogo
- Usuario permanece bloqueado
- Caso de uso termina

**A2. Razon insuficiente (paso 9)**

- Sistema detecta razon menor a 20 caracteres
- Sistema muestra error: "Razon debe tener al menos 20 caracteres" (USR-017)
- Usuario permanece en dialogo
- Caso de uso puede reintentar desde paso 7

**A3. Usuario sin funcion users.unlock**

- Sistema detecta que usuario no tiene funcion
- Sistema muestra error 403: "No tiene permisos para desbloquear usuarios" (USR-020)
- Usuario es redirigido a pagina anterior
- Caso de uso termina

**A4. Usuario no encontrado (paso 3)**

- Sistema no encuentra usuario con ID especificado
- Sistema muestra error: "Usuario no encontrado" (USR-011)
- Usuario es redirigido a lista de usuarios
- Caso de uso termina

**A5. Usuario NO esta bloqueado (paso 10)**

- Sistema detecta que usuario tiene is_locked=false
- Sistema muestra mensaje: "Usuario no esta bloqueado" (INFO-019)
- Sistema rechaza operacion
- Caso de uso termina

### POSTCONDICIONES

Exito:

- Usuario marcado como desbloqueado (is_locked=false)
- locked_until establecido a null
- Desbloqueo registrado en AuditLog
- Usuario puede iniciar sesion inmediatamente

Fallo:

- Usuario permanece bloqueado
- Usuario puede reintentar

### REGLAS DE NEGOCIO

- RN-064: Razon del desbloqueo obligatoria minimo 20 caracteres
- RN-065: Solo puede desbloquear usuarios actualmente bloqueados
- RN-066: Desbloqueo es inmediato y permanente
- RN-067: Usuario puede iniciar sesion inmediatamente despues
- RN-068: Contador de intentos fallidos NO se resetea automaticamente

### RESTRICCIONES TECNICAS

Ninguna restriccion tecnica especifica (usa campos estandar del modelo User)

### REGLAS SoD

Ninguna

### MENSAJES DEL SISTEMA

Errores:

- USR-011: "Usuario no encontrado" (ID no existe)
- USR-017: "Razon debe tener al menos 20 caracteres" (razon corta)
- USR-020: "No tiene permisos para desbloquear usuarios" (sin funcion users.unlock)

Confirmacion:

- OK-011: "Usuario desbloqueado exitosamente" (desbloqueo exitoso)

Advertencias:

- WARN-007: "El usuario podra iniciar sesion inmediatamente" (confirmacion)

Informativos:

- INFO-019: "Usuario no esta bloqueado" (no bloqueado actualmente)
- INFO-020: "Desbloqueo manual realizado antes de expiracion automatica" (si aplica)

### IMPLEMENTACION TECNICA

**Desbloquear usuario**

Endpoint: POST /api/v1/users/{user_id}/unlock

Request:

```json
{
  "reason": "Revision de seguridad completada. Usuario verificado. Ticket SEC-2024-0123 resuelto."
}
```

Response Exitosa (200 OK):

```json
{
  "success": true,
  "message": "Usuario desbloqueado exitosamente",
  "user": {
    "id": 150,
    "username": "plopez",
    "email": "pedro.lopez@empresa.com",
    "first_name": "Pedro Antonio",
    "last_name": "Lopez Garcia",
    "is_active": true,
    "is_locked": false,
    "locked_until": null
  },
  "unlock_details": {
    "unlocked_at": "2026-02-25T14:55:00Z",
    "unlocked_by": 123,
    "reason": "Revision de seguridad completada. Usuario verificado. Ticket SEC-2024-0123 resuelto.",
    "was_locked_until": "2026-02-25T15:00:00Z",
    "time_saved_minutes": 5
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

Response - Usuario NO bloqueado (400 Bad Request):

```json
{
  "success": false,
  "error_code": "INFO-019",
  "message": "Usuario no esta bloqueado",
  "user_id": 150,
  "is_locked": false
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
  "error_code": "USR-020",
  "message": "No tiene permisos para desbloquear usuarios"
}
```

Codigos HTTP:

- 200 OK: Usuario desbloqueado exitosamente
- 400 Bad Request: Razon invalida o usuario no bloqueado
- 403 Forbidden: Sin funcion users.unlock
- 404 Not Found: Usuario no existe
- 500 Internal Server Error: Error del servidor

### VALIDACIONES

Validacion de Usuario:

- Usuario objetivo existe en base de datos
- Usuario objetivo tiene is_locked=true
- Usuario objetivo tiene is_active=true

Validacion de Razon:

- Obligatoria
- Minimo 20 caracteres
- Maximo 500 caracteres
- Debe explicar razon del desbloqueo

Proceso de Desbloqueo:

1. Marcar is_locked = false
2. Establecer locked_until = null
3. Registrar unlocked_by = user_id del ejecutor
4. Registrar unlock_reason = razon ingresada
5. Registrar en AuditLog
6. NO resetear failed_login_attempts (se mantiene)

### AUDITORIA

Se registra en AuditLog:

- Accion: unlock_user
- Usuario: user_id (quien desbloquea)
- Timestamp: hora exacta
- IP Address: IP desde donde desbloquea
- User Agent: navegador y dispositivo
- Detalles: ID del usuario desbloqueado, username, razon, locked_until original, tiempo ahorrado, razon original del bloqueo

Ejemplo de log:

```json
{
  "timestamp": "2026-02-25T14:55:00Z",
  "action": "unlock_user",
  "user_id": 123,
  "target_user_id": 150,
  "ip_address": "192.168.1.100",
  "user_agent": "Chrome/120.0",
  "result": "success",
  "details": {
    "unlocked_username": "plopez",
    "unlocked_email": "pedro.lopez@empresa.com",
    "reason": "Revision de seguridad completada. Usuario verificado. Ticket SEC-2024-0123 resuelto.",
    "was_locked_until": "2026-02-25T15:00:00Z",
    "time_saved_minutes": 5,
    "original_lock_reason": "Actividad sospechosa detectada",
    "manual_unlock": true
  }
}
```

### SEGURIDAD

Protecciones Implementadas:

- Razon obligatoria (trazabilidad)
- Solo puede desbloquear usuarios actualmente bloqueados
- Desbloqueo completamente auditado
- Registra razon original del bloqueo
- Registra tiempo ahorrado por desbloqueo manual

Comportamiento Despues de Desbloqueo:

- Usuario puede iniciar sesion inmediatamente
- Contador de intentos fallidos se mantiene
- Sesiones activas (si las hay) continuan funcionando
- Sin restricciones de acceso

Informacion Auditada:

- Quien desbloqueo
- Cuando desbloqueo
- Por que desbloqueo
- Cuando iba a expirar el bloqueo original
- Tiempo ahorrado por desbloqueo manual
- Razon original del bloqueo

### NOTAS IMPORTANTES

- Desbloqueo es inmediato y permanente
- Usuario puede iniciar sesion inmediatamente
- Contador de intentos fallidos NO se resetea automaticamente
- Razon del desbloqueo obligatoria minimo 20 caracteres
- Solo puede desbloquear usuarios actualmente bloqueados

Diferencia entre Desbloqueo Manual y Automatico:

- Desbloqueo automatico: al llegar a locked_until, sin funcion users.unlock requerida, sin razon documentada, tarea programada del sistema
- Desbloqueo manual (users.unlock): requiere funcion users.unlock, razon obligatoria, antes de expiracion automatica, decision administrativa

Contador de Intentos Fallidos:

- NO se resetea al desbloquear
- Si usuario falla login nuevamente tras desbloqueo, se bloqueara inmediatamente
- Para resetear contador se requiere funcion adicional

Bloqueos que Pueden Desbloquearse:

- Bloqueo manual por users.lock
- Bloqueo automatico por 5 intentos fallidos
- Bloqueo indefinido
- Bloqueo temporal antes de expiracion

Escenario Tipico Completo:

1. Usuario bloqueado por intentos fallidos (automatico)
2. Usuario contacta soporte
3. Soporte verifica identidad
4. Soporte desbloquea con users.unlock
5. Soporte resetea contrasena con users.reset_password (si aplica)
6. Usuario puede acceder con nueva contrasena

Casos de Uso Tipicos:

- Investigacion de seguridad completada (todo normal)
- Bloqueo por error o malentendido
- Usuario urgentemente necesita acceso
- Bloqueo por intentos fallidos (usuario verificado)
- Solicitud del usuario (verificada)

---

Sistema IACT - Analisis IVR
Version: 1.0.0 | Fecha documento: 2026-03-14 | Modelo RBAC: v7.0.0
