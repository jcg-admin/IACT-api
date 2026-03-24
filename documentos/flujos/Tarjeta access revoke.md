## TARJETA: access.revoke

Nombre para UI: Revocar Funciones
Modulo: MOD_Access - Gestion de Permisos
ID Caso de Uso: UC-016
Prioridad: CRITICA
Frecuencia: Ocasional
Estado: Activo

### DESCRIPCION

Permite revocar funciones asignadas a un usuario. La revocacion es un soft delete: el registro de asignacion queda marcado con revoked_at y revoked_by, preservando el historial para auditoria. Las funciones revocadas tienen efecto inmediato. Requiere justificacion obligatoria minimo 20 caracteres.

### PRECONDICIONES

- Usuario tiene sesion activa
- Usuario tiene funcion access.revoke asignada
- El usuario objetivo existe en el sistema
- El usuario objetivo tiene las funciones a revocar asignadas
- Justificacion disponible (minimo 20 caracteres)

### FLUJO PRINCIPAL (12 PASOS)

1. Usuario navega a seccion "Revocar Funciones" o al perfil del usuario objetivo
2. Sistema muestra funciones actualmente activas del usuario objetivo
3. Usuario selecciona una o varias funciones a revocar
4. Sistema muestra advertencia: las funciones se revocan inmediatamente
5. Usuario ingresa justificacion (minimo 20 caracteres)
6. Usuario hace clic en "Revocar Funciones"
7. Sistema valida que el usuario objetivo existe
8. Sistema valida que las funciones seleccionadas estan asignadas al usuario
9. Sistema valida justificacion (minimo 20 caracteres)
10. Sistema marca las funciones como revocadas (revoked_at, revoked_by, justification)
11. Sistema invalida tokens o sesiones activas que dependan de esas funciones (si aplica)
12. Sistema muestra confirmacion con lista de funciones revocadas

### FLUJOS ALTERNATIVOS

**A1. Funcion no asignada al usuario (paso 8)**

- Sistema detecta que alguna funcion no esta activa en el usuario
- Sistema muestra error: "La funcion X no esta asignada al usuario" (ACC-009)
- Sistema puede omitir esas funciones y continuar con las que si estan asignadas
- Usuario confirma si desea continuar con las funciones validas

**A2. Usuario objetivo no existe (paso 7)**

- Sistema no encuentra el usuario
- Sistema muestra error: "Usuario no encontrado" (ACC-001)
- Caso de uso termina

**A3. Justificacion insuficiente (paso 9)**

- Sistema detecta justificacion con menos de 20 caracteres
- Sistema muestra error: "La justificacion debe tener al menos 20 caracteres" (ACC-006)
- Usuario permanece en formulario
- Caso de uso puede reintentar desde paso 5

**A4. Sin funciones seleccionadas (paso 6)**

- Sistema detecta que no hay funciones seleccionadas
- Sistema muestra error: "Seleccione al menos una funcion para revocar" (ACC-010)
- Usuario permanece en formulario
- Caso de uso puede reintentar desde paso 3

**A5. Usuario sin funcion access.revoke**

- Sistema detecta que el usuario que opera no tiene funcion
- Sistema muestra error 403: "No tiene permisos para revocar funciones" (ACC-002)
- Usuario es redirigido a pagina anterior
- Caso de uso termina

**A6. Revocar propia funcion (paso 3)**

- Sistema detecta que usuario intenta revocar sus propias funciones
- Sistema muestra error: "No puede modificar sus propias funciones" (ACC-008)
- Caso de uso termina

### POSTCONDICIONES

Exito:

- Funciones seleccionadas marcadas como revocadas (soft delete)
- Historial preservado: revoked_at, revoked_by, justification
- Efecto inmediato: usuario objetivo pierde acceso a esas funciones
- Registro de auditoria creado

Fallo:

- Funciones sin cambios
- Usuario puede reintentar con datos correctos

### REGLAS DE NEGOCIO

- RN-061: Soft delete obligatorio: NO se elimina el registro, se marca como revocado
- RN-062: Justificacion obligatoria minimo 20 caracteres
- RN-063: La revocacion tiene efecto INMEDIATO
- RN-064: Usuario revocador no puede revocar sus propias funciones (CNST-020)
- RN-065: El historial de revocaciones es permanente y auditable
- RN-066: Si se revocan todas las funciones, el usuario queda sin accesos pero sigue existiendo

### RESTRICCIONES TECNICAS

- CNST-020: Usuario revocador no puede modificar sus propias funciones
- Soft delete: campo revoked_at != null indica funcion revocada

### REGLAS SoD

- SoD 1 (function_assignment_control)
- INCOMPATIBLE con: access.assign
- Razon: Quien revoca funciones NO puede asignarlas (separacion de poderes)

### MENSAJES DEL SISTEMA

Errores:

- ACC-001: "Usuario no encontrado"
- ACC-002: "No tiene permisos para revocar funciones"
- ACC-006: "La justificacion debe tener al menos 20 caracteres"
- ACC-008: "No puede modificar sus propias funciones"
- ACC-009: "La funcion X no esta asignada al usuario"
- ACC-010: "Seleccione al menos una funcion para revocar"

Confirmacion:

- OK-015: "Funciones revocadas exitosamente"

Advertencias:

- WARN-018: "Las funciones se revocan inmediatamente y el usuario perdera acceso"
- WARN-019: "El usuario quedara sin funciones activas si continua"

### IMPLEMENTACION TECNICA

**Revocar funciones de un usuario**

Endpoint: POST /api/v1/users/{user_id}/functions/revoke

Request:

```json
{
  "function_codes": ["users.create", "users.edit"],
  "justification": "Cambio de rol. El analista pasa a solo lectura. Aprobado por RRHH ticket HR-2026-0234."
}
```

Response Exitosa (200 OK):

```json
{
  "success": true,
  "message": "Funciones revocadas exitosamente",
  "revoked": [
    {
      "function_code": "users.create",
      "function_name": "Crear Usuarios",
      "revoked_at": "2026-03-22T10:30:00Z",
      "revoked_by": "admin_revocador"
    },
    {
      "function_code": "users.edit",
      "function_name": "Editar Usuarios",
      "revoked_at": "2026-03-22T10:30:00Z",
      "revoked_by": "admin_revocador"
    }
  ],
  "skipped": [],
  "user": {
    "id": 150,
    "username": "plopez",
    "remaining_active_functions": 2
  }
}
```

Response - Funcion no asignada (400 Bad Request):

```json
{
  "success": false,
  "error_code": "ACC-009",
  "message": "La funcion users.delete no esta asignada al usuario",
  "function_code": "users.delete"
}
```

Response - Sin permisos (403 Forbidden):

```json
{
  "success": false,
  "error_code": "ACC-002",
  "message": "No tiene permisos para revocar funciones"
}
```

Response - Justificacion insuficiente (400 Bad Request):

```json
{
  "success": false,
  "error_code": "ACC-006",
  "message": "La justificacion debe tener al menos 20 caracteres",
  "current_length": 10,
  "required_length": 20
}
```

Codigos HTTP:

- 200 OK: Funciones revocadas exitosamente
- 400 Bad Request: Justificacion invalida, funcion no asignada, sin funciones seleccionadas
- 403 Forbidden: Sin funcion access.revoke o intento de modificar propias funciones
- 404 Not Found: Usuario objetivo no encontrado
- 500 Internal Server Error: Error del servidor

### VALIDACIONES

Validacion de Usuario Objetivo:

- user_id: Entero positivo, debe existir en base de datos

Validacion de Funciones:

- function_codes: Lista no vacia
- Cada codigo debe existir en el catalogo de funciones
- Cada funcion debe estar actualmente asignada al usuario (revoked_at IS NULL)

Validacion de Justificacion:

- Obligatoria
- Minimo 20 caracteres
- Recomendado: referencia a ticket o aprobacion formal

### AUDITORIA

Se registra en AuditLog:

- Accion: revoke_functions
- Usuario: user_id (quien revoca)
- Target: user_id del usuario objetivo
- Timestamp: hora exacta
- Detalles: funciones revocadas, justificacion

Ejemplo de log:

```json
{
  "timestamp": "2026-03-22T10:30:00Z",
  "action": "revoke_functions",
  "user_id": 101,
  "target_user_id": 150,
  "ip_address": "192.168.1.100",
  "user_agent": "Chrome/120.0",
  "result": "success",
  "details": {
    "functions_revoked": ["users.create", "users.edit"],
    "justification": "Cambio de rol...",
    "remaining_functions": 2
  }
}
```

### SEGURIDAD

Protecciones Implementadas:

- Soft delete obligatorio: historial preservado permanentemente
- Justificacion obligatoria para trazabilidad
- Efecto inmediato: usuario pierde acceso instantaneamente
- Usuario no puede revocar sus propias funciones (CNST-020)
- SoD 1: quien revoca no puede asignar (separacion de poderes)
- Todas las revocaciones auditadas con detalle y justificacion

### NOTAS IMPORTANTES

- Revocacion con efecto INMEDIATO: el usuario objetivo pierde acceso en el siguiente request
- Soft delete: el historial siempre queda visible en access.view
- El revocador NO puede tener access.assign (SoD 1)
- El revocador no puede modificar sus propias funciones
- Si quedan 0 funciones activas, el usuario sigue existiendo pero sin ningun acceso funcional
- La justificacion debe ser clara y referencias tickets formales cuando sea posible

---

Sistema IACT - Analisis IVR
Version: 1.0.0 | Fecha documento: 2026-03-22 | Modelo RBAC: v7.0.0
