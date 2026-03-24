## TARJETA: users.reset_password

Nombre para UI: Resetear Contrasena
Modulo: MOD_Users - Gestion de Usuarios
ID Caso de Uso: UC-009
Prioridad: ALTA
Frecuencia: Ocasional
Estado: Activo

### DESCRIPCION

Permite a un administrador o supervisor resetear la contrasena de un usuario, generando una nueva contrasena temporal. Esta funcion se usa cuando un usuario no puede recuperar su contrasena por el metodo normal (preguntas de seguridad) o cuando el administrador necesita restablecer el acceso. Todas las sesiones activas del usuario se invalidan automaticamente.

### PRECONDICIONES

- Usuario tiene sesion activa
- Usuario tiene funcion users.reset_password asignada
- Usuario objetivo existe en el sistema
- Usuario objetivo esta activo (is_active=true)

### FLUJO PRINCIPAL (13 PASOS)

1. Usuario navega a "Gestion de Usuarios"
2. Usuario busca y selecciona usuario al que resetear contrasena
3. Sistema muestra datos del usuario seleccionado
4. Usuario hace clic en "Resetear Contrasena"
5. Sistema muestra dialogo de confirmacion
6. Usuario ingresa justificacion del reset (minimo 20 caracteres)
7. Usuario confirma reset
8. Sistema valida justificacion
9. Sistema genera nueva contrasena temporal aleatoria
10. Sistema actualiza hash de contrasena en base de datos
11. Sistema invalida todas las sesiones activas del usuario
12. Sistema registra reset en AuditLog con justificacion
13. Sistema muestra contrasena temporal generada

### FLUJOS ALTERNATIVOS

**A1. Usuario cancela reset (paso 7)**

- Usuario hace clic en "Cancelar"
- Sistema cierra dialogo
- Contrasena sin cambios
- Caso de uso termina

**A2. Justificacion insuficiente (paso 8)**

- Sistema detecta justificacion menor a 20 caracteres
- Sistema muestra error: "Justificacion debe tener al menos 20 caracteres" (USR-013)
- Usuario permanece en dialogo
- Caso de uso puede reintentar desde paso 6

**A3. Usuario sin funcion users.reset_password**

- Sistema detecta que usuario no tiene funcion
- Sistema muestra error 403: "No tiene permisos para resetear contrasenas" (USR-015)
- Usuario es redirigido a pagina anterior
- Caso de uso termina

**A4. Usuario no encontrado (paso 3)**

- Sistema no encuentra usuario con ID especificado
- Sistema muestra error: "Usuario no encontrado" (USR-011)
- Usuario es redirigido a lista de usuarios
- Caso de uso termina

**A5. Usuario objetivo inactivo (paso 9)**

- Sistema detecta que usuario tiene is_active=false
- Sistema muestra error: "No puede resetear contrasena de usuario inactivo" (USR-016)
- Sistema rechaza operacion
- Caso de uso termina

### POSTCONDICIONES

Exito:

- Contrasena del usuario reseteada
- Nueva contrasena temporal generada
- Todas las sesiones invalidadas
- Reset registrado en AuditLog
- Contrasena temporal mostrada al administrador

Fallo:

- Contrasena sin cambios
- Sesiones permanecen activas
- Usuario puede reintentar

### REGLAS DE NEGOCIO

- RN-050: Justificacion obligatoria minimo 20 caracteres
- RN-051: Contrasena temporal generada aleatoriamente (8 caracteres)
- RN-052: Todas las sesiones activas se invalidan
- RN-053: Contrasena temporal cumple politica (CNST-003)
- RN-054: Usuario debe cambiar contrasena temporal en proximo login
- RN-055: Contrasena temporal se muestra UNA sola vez
- RN-056: Reset NO puede hacerse en usuario inactivo

### RESTRICCIONES TECNICAS

- CNST-003: Politica de contrasena
  - Minimo 8 caracteres
  - Incluir mayusculas, minusculas, numeros y simbolos
  - No estar en lista de contrasenas comunes
  - No coincidir con ultimas 3 contrasenas

### REGLAS SoD

SoD 2 - user_audit_separation:

- INCOMPATIBLE con: audit.view, audit.search
- Razon: Quien resetea contrasenas NO debe auditar sus propias acciones

### MENSAJES DEL SISTEMA

Errores:

- USR-011: "Usuario no encontrado" (ID no existe)
- USR-013: "Justificacion debe tener al menos 20 caracteres" (justificacion corta)
- USR-015: "No tiene permisos para resetear contrasenas" (sin funcion users.reset_password)
- USR-016: "No puede resetear contrasena de usuario inactivo" (usuario eliminado)

Confirmacion:

- OK-009: "Contrasena reseteada exitosamente" (reset exitoso)

Advertencias:

- WARN-003: "Todas las sesiones activas del usuario seran invalidadas" (confirmacion)
- WARN-004: "La contrasena temporal se mostrara una sola vez. Guardela de forma segura" (advertencia)

Informativos:

- INFO-015: "Nueva contrasena temporal: {password}" (muestra contrasena)
- INFO-016: "El usuario debe cambiar esta contrasena en su proximo inicio de sesion" (recordatorio)

### IMPLEMENTACION TECNICA

**Resetear contrasena de usuario**

Endpoint: POST /api/v1/users/{user_id}/reset-password

Request:

```json
{
  "justification": "Usuario olvido contrasena y no puede responder preguntas de seguridad. Solicitado por ticket soporte HELP-2024-0789."
}
```

Response Exitosa (200 OK):

```json
{
  "success": true,
  "message": "Contrasena reseteada exitosamente",
  "user": {
    "id": 150,
    "username": "plopez",
    "email": "pedro.lopez@empresa.com",
    "first_name": "Pedro Antonio",
    "last_name": "Lopez Garcia"
  },
  "temporary_password": "Xy9z!Kb2",
  "sessions_invalidated": 2,
  "warnings": [
    "Contrasena temporal se muestra una sola vez",
    "Usuario debe cambiarla en proximo login",
    "Comunique la contrasena de forma segura"
  ]
}
```

Response - Justificacion insuficiente (400 Bad Request):

```json
{
  "success": false,
  "error_code": "USR-013",
  "message": "Justificacion debe tener al menos 20 caracteres",
  "current_length": 15,
  "required_length": 20
}
```

Response - Usuario inactivo (400 Bad Request):

```json
{
  "success": false,
  "error_code": "USR-016",
  "message": "No puede resetear contrasena de usuario inactivo",
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
  "error_code": "USR-015",
  "message": "No tiene permisos para resetear contrasenas"
}
```

Codigos HTTP:

- 200 OK: Contrasena reseteada exitosamente
- 400 Bad Request: Justificacion invalida o usuario inactivo
- 403 Forbidden: Sin funcion users.reset_password
- 404 Not Found: Usuario no existe
- 500 Internal Server Error: Error del servidor

### VALIDACIONES

Validacion de Usuario:

- Usuario objetivo existe en base de datos
- Usuario objetivo tiene is_active=true
- Usuario objetivo NO esta bloqueado temporalmente

Validacion de Justificacion:

- Obligatoria
- Minimo 20 caracteres
- Maximo 500 caracteres
- Debe explicar razon del reset

Generacion de Contrasena Temporal:

- Longitud: 8 caracteres
- Incluye: mayusculas (2), minusculas (3), numeros (2), simbolos (1)
- Cumple politica CNST-003
- Aleatoria y segura
- NO predecible

Proceso de Reset:

1. Generar contrasena temporal aleatoria
2. Hash con PBKDF2
3. Actualizar password_hash en User
4. Invalidar todas las sesiones activas
5. Marcar require_password_change = true
6. Registrar en AuditLog

### AUDITORIA

Se registra en AuditLog:

- Accion: reset_password
- Usuario: user_id (quien resetea)
- Timestamp: hora exacta
- IP Address: IP desde donde resetea
- User Agent: navegador y dispositivo
- Detalles: ID del usuario reseteado, username, justificacion, sesiones invalidadas, contrasena temporal (hash)

Ejemplo de log:

```json
{
  "timestamp": "2026-02-25T14:30:00Z",
  "action": "reset_password",
  "user_id": 123,
  "target_user_id": 150,
  "ip_address": "192.168.1.100",
  "user_agent": "Chrome/120.0",
  "result": "success",
  "details": {
    "reset_username": "plopez",
    "reset_email": "pedro.lopez@empresa.com",
    "justification": "Usuario olvido contrasena y no puede responder preguntas de seguridad. Solicitado por ticket soporte HELP-2024-0789.",
    "sessions_invalidated": 2,
    "temporary_password_hash": "$2b$12$...",
    "require_password_change": true
  }
}
```

### SEGURIDAD

Protecciones Implementadas:

- Justificacion obligatoria (trazabilidad)
- Contrasena temporal generada de forma segura
- Contrasena temporal cumple politica de seguridad
- Todas las sesiones invalidadas automaticamente
- Contrasena temporal se muestra UNA sola vez
- Contrasena temporal hasheada antes de almacenar
- Usuario obligado a cambiar contrasena temporal
- Reset completamente auditado
- SoD 2 previene que quien resetea contrasenas audite sus propias acciones

Generacion Segura:

- Contrasena aleatoria con entropia alta
- Incluye todos los tipos de caracteres requeridos
- NO basada en datos del usuario
- NO predecible
- NO reutilizable

Acciones Automaticas al Resetear:

1. Nueva contrasena generada aleatoriamente
2. Password hasheado con PBKDF2
3. Todas las sesiones invalidadas
4. require_password_change = true
5. Registro en AuditLog

### NOTAS IMPORTANTES

- Contrasena temporal se genera aleatoriamente (8 caracteres)
- Contrasena temporal cumple politica de seguridad (CNST-003)
- Contrasena temporal se muestra UNA sola vez al resetear
- Todas las sesiones activas se invalidan automaticamente
- Usuario DEBE cambiar contrasena temporal en proximo login
- Justificacion obligatoria minimo 20 caracteres
- NO puede resetear contrasena de usuario inactivo

Violacion SoD 2:

- Usuario con users.reset_password NO puede tener audit.view
- Usuario con users.reset_password NO puede tener audit.search
- Razon: Prevenir que quien resetea contrasenas audite sus propias acciones

Diferencia entre Reset y Recuperacion:

- users.reset_password (por administrador): requiere funcion asignada, administrador genera contrasena temporal, requiere justificacion obligatoria, todas las sesiones invalidadas, completamente auditado
- auth.recover_password (por usuario): no requiere funcion especial, usuario responde preguntas de seguridad, usuario crea su propia contrasena, todas las sesiones invalidadas, auto-servicio

Comunicacion de Contrasena Temporal:

- NO enviar por email (CNST-001)
- Comunicar de forma segura: en persona, mensaje interno del sistema, llamada telefonica verificada, canal seguro aprobado

Casos de Uso Tipicos:

- Usuario no puede responder preguntas de seguridad
- Usuario nuevo que necesita acceso inmediato
- Sospecha de compromiso de cuenta
- Solicitud urgente de acceso
- Usuario bloqueado por olvido de credenciales

Contrasena Temporal:

- Se muestra UNA sola vez
- NO se puede recuperar despues
- Usuario debe cambiarla en proximo login
- Sistema fuerza cambio (require_password_change=true)
- NO se almacena en texto plano, solo hash PBKDF2
- NO se envia por email

---

Sistema IACT - Analisis IVR
Version: 1.0.0 | Fecha documento: 2026-03-14 | Modelo RBAC: v7.0.0
