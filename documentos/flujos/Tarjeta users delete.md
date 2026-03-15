## TARJETA: users.delete

Nombre para UI: Eliminar Usuarios
Modulo: MOD_Users - Gestion de Usuarios
ID Caso de Uso: UC-008
Prioridad: ALTA
Frecuencia: Ocasional
Estado: Activo

### DESCRIPCION

Permite eliminar usuarios del sistema mediante soft delete. El usuario no se elimina fisicamente de la base de datos, sino que se marca como inactivo (is_active=false) y se invalidan todas sus sesiones activas. Los datos del usuario se preservan para auditoria y cumplimiento regulatorio. La eliminacion fisica esta prohibida.

### PRECONDICIONES

- Usuario tiene sesion activa
- Usuario tiene funcion users.delete asignada
- Usuario objetivo existe en el sistema
- Usuario objetivo NO es el mismo que ejecuta la accion

### FLUJO PRINCIPAL (14 PASOS)

1. Usuario navega a "Gestion de Usuarios"
2. Usuario busca y selecciona usuario a eliminar
3. Sistema muestra datos del usuario seleccionado
4. Usuario hace clic en "Eliminar Usuario"
5. Sistema muestra dialogo de confirmacion con advertencia
6. Sistema muestra informacion del usuario a eliminar
7. Usuario ingresa justificacion de eliminacion (minimo 20 caracteres)
8. Usuario confirma eliminacion
9. Sistema valida que usuario objetivo no sea el mismo usuario
10. Sistema marca usuario como inactivo (is_active=false)
11. Sistema invalida todas las sesiones activas del usuario
12. Sistema revoca todas las funciones asignadas
13. Sistema registra eliminacion en AuditLog con justificacion
14. Sistema muestra confirmacion: "Usuario eliminado exitosamente"

### FLUJOS ALTERNATIVOS

**A1. Usuario cancela eliminacion (paso 8)**

- Usuario hace clic en "Cancelar"
- Sistema cierra dialogo
- Usuario permanece activo sin cambios
- Caso de uso termina

**A2. Intento de auto-eliminacion (paso 9)**

- Sistema detecta que usuario objetivo es el mismo que ejecuta
- Sistema muestra error: "No puede eliminar su propia cuenta" (USR-012)
- Sistema rechaza operacion
- Caso de uso termina

**A3. Justificacion insuficiente (paso 7)**

- Sistema detecta justificacion menor a 20 caracteres
- Sistema muestra error: "Justificacion debe tener al menos 20 caracteres" (USR-013)
- Usuario permanece en dialogo
- Caso de uso puede reintentar desde paso 7

**A4. Usuario sin funcion users.delete**

- Sistema detecta que usuario no tiene funcion
- Sistema muestra error 403: "No tiene permisos para eliminar usuarios" (USR-014)
- Usuario es redirigido a pagina anterior
- Caso de uso termina

**A5. Usuario no encontrado (paso 3)**

- Sistema no encuentra usuario con ID especificado
- Sistema muestra error: "Usuario no encontrado" (USR-011)
- Usuario es redirigido a lista de usuarios
- Caso de uso termina

**A6. Usuario ya esta eliminado (paso 10)**

- Sistema detecta que usuario ya tiene is_active=false
- Sistema muestra advertencia: "Usuario ya esta inactivo" (INFO-013)
- Sistema ofrece opcion de restaurar
- Caso de uso termina

### POSTCONDICIONES

Exito:

- Usuario marcado como inactivo (is_active=false)
- Todas las sesiones invalidadas
- Todas las funciones revocadas
- Datos preservados en base de datos
- Eliminacion registrada en AuditLog

Fallo:

- Usuario permanece activo
- Sesiones y funciones sin cambios
- Usuario puede reintentar

### REGLAS DE NEGOCIO

- RN-043: Soft delete obligatorio (NO eliminacion fisica)
- RN-044: Usuario NO puede eliminar su propia cuenta
- RN-045: Justificacion obligatoria minimo 20 caracteres
- RN-046: Todas las sesiones del usuario se invalidan
- RN-047: Todas las funciones del usuario se revocan
- RN-048: Datos se preservan para auditoria (CNST-014)
- RN-049: Eliminacion es reversible con funcion de restauracion

### RESTRICCIONES TECNICAS

- CNST-014: Soft delete obligatorio
  - Campo: is_active = false
  - Datos NO se eliminan fisicamente
  - Usuario preservado para auditoria
  - Cumplimiento regulatorio (retencion 7 anos)

### REGLAS SoD

SoD 2 - user_audit_separation:

- INCOMPATIBLE con: audit.view, audit.search
- Razon: Quien elimina usuarios NO debe auditar sus propias acciones

### MENSAJES DEL SISTEMA

Errores:

- USR-011: "Usuario no encontrado" (ID no existe)
- USR-012: "No puede eliminar su propia cuenta" (auto-eliminacion)
- USR-013: "Justificacion debe tener al menos 20 caracteres" (justificacion corta)
- USR-014: "No tiene permisos para eliminar usuarios" (sin funcion users.delete)

Confirmacion:

- OK-008: "Usuario eliminado exitosamente" (eliminacion exitosa)

Advertencias:

- WARN-001: "Esta accion marcara al usuario como inactivo. Sus datos se preservaran para auditoria" (confirmacion)
- WARN-002: "Todas las sesiones y funciones del usuario seran revocadas" (advertencia)

Informativos:

- INFO-013: "Usuario ya esta inactivo" (ya eliminado)
- INFO-014: "Puede restaurar este usuario con la funcion de restauracion" (reversible)

### IMPLEMENTACION TECNICA

**Eliminar usuario**

Endpoint: DELETE /api/v1/users/{user_id}

Request:

```json
{
  "justification": "Usuario solicito baja voluntaria del sistema. Ticket RRHH-2024-0156."
}
```

Response Exitosa (200 OK):

```json
{
  "success": true,
  "message": "Usuario eliminado exitosamente",
  "user": {
    "id": 150,
    "username": "plopez",
    "email": "pedro.lopez@empresa.com",
    "first_name": "Pedro Antonio",
    "last_name": "Lopez Garcia",
    "is_active": false,
    "deleted_at": "2026-02-25T11:00:00Z",
    "deleted_by": 123
  },
  "actions_performed": {
    "sessions_invalidated": 2,
    "functions_revoked": 5
  }
}
```

Response - Auto-eliminacion (400 Bad Request):

```json
{
  "success": false,
  "error_code": "USR-012",
  "message": "No puede eliminar su propia cuenta"
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
  "error_code": "USR-014",
  "message": "No tiene permisos para eliminar usuarios"
}
```

Codigos HTTP:

- 200 OK: Usuario eliminado exitosamente (soft delete)
- 400 Bad Request: Auto-eliminacion o justificacion invalida
- 403 Forbidden: Sin funcion users.delete
- 404 Not Found: Usuario no existe
- 500 Internal Server Error: Error del servidor

### VALIDACIONES

Validacion de Usuario:

- Usuario objetivo existe en base de datos
- Usuario objetivo NO es el mismo que ejecuta
- Usuario objetivo tiene is_active=true (no ya eliminado)

Validacion de Justificacion:

- Obligatoria
- Minimo 20 caracteres
- Maximo 500 caracteres
- Debe explicar razon de eliminacion

Proceso de Soft Delete:

1. Marcar is_active = false
2. Registrar deleted_at = NOW()
3. Registrar deleted_by = user_id del ejecutor
4. Invalidar todas las sesiones
5. Revocar todas las funciones
6. Registrar en AuditLog

### AUDITORIA

Se registra en AuditLog:

- Accion: delete_user
- Usuario: user_id (quien elimina)
- Timestamp: hora exacta
- IP Address: IP desde donde elimina
- User Agent: navegador y dispositivo
- Detalles: ID del usuario eliminado, username, justificacion, sesiones invalidadas, funciones revocadas

Ejemplo de log:

```json
{
  "timestamp": "2026-02-25T11:00:00Z",
  "action": "delete_user",
  "user_id": 123,
  "target_user_id": 150,
  "ip_address": "192.168.1.100",
  "user_agent": "Chrome/120.0",
  "result": "success",
  "details": {
    "deleted_username": "plopez",
    "deleted_email": "pedro.lopez@empresa.com",
    "justification": "Usuario solicito baja voluntaria del sistema. Ticket RRHH-2024-0156.",
    "sessions_invalidated": 2,
    "functions_revoked": 5,
    "user_data_preserved": true
  }
}
```

### SEGURIDAD

Protecciones Implementadas:

- Soft delete obligatorio (datos preservados)
- Usuario NO puede eliminar su propia cuenta
- Justificacion obligatoria (trazabilidad)
- Todas las sesiones invalidadas automaticamente
- Todas las funciones revocadas automaticamente
- Eliminacion completamente auditada
- SoD 2 previene que quien elimina usuarios audite sus propias acciones

Datos Preservados:

- Todos los datos del usuario
- Historial de funciones
- Historial de sesiones
- Logs de auditoria
- Retencion por 7 anos (cumplimiento regulatorio)

Acciones Automaticas al Eliminar:

1. is_active = false
2. Todas las sesiones invalidadas
3. Todas las funciones revocadas
4. UserFunctionAssignment marcado con revoked_at
5. Registro en AuditLog

### NOTAS IMPORTANTES

- Eliminacion es SOFT DELETE (no fisica)
- Datos del usuario se preservan en base de datos
- Usuario NO puede eliminar su propia cuenta
- Justificacion obligatoria minimo 20 caracteres
- Todas las sesiones activas se invalidan automaticamente
- Todas las funciones se revocan automaticamente
- Eliminacion es REVERSIBLE (puede restaurarse)

Violacion SoD 2:

- Usuario con users.delete NO puede tener audit.view
- Usuario con users.delete NO puede tener audit.search
- Razon: Prevenir que quien elimina usuarios audite sus propias acciones

Diferencia entre Eliminar y Bloquear:

- users.delete (soft delete): is_active=false, sesiones invalidadas, funciones revocadas, permanente hasta restauracion
- users.lock (bloqueo temporal): is_locked=true, locked_until=15 minutos, sesiones activas continuan, funciones se mantienen, automatico tras desbloqueo

Restauracion:

- Requiere funcion de restauracion (fuera del alcance de users.delete)
- Restaurar establece is_active = true
- Funciones NO se restauran automaticamente
- Requiere nueva asignacion de funciones

Casos de Uso Tipicos:

- Empleado renuncia o es despedido
- Usuario solicita baja voluntaria
- Cuenta duplicada o de prueba
- Cumplimiento de derecho al olvido (con proceso especial)

Retencion de Datos:

- CNST-014: Soft delete obligatorio
- Datos preservados 7 anos minimo
- Cumplimiento regulatorio
- Auditoria completa disponible

---

Sistema IACT - Analisis IVR
Version: 1.0.0 | Fecha documento: 2026-03-14 | Modelo RBAC: v7.0.0
