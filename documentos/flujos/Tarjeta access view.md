## TARJETA: access.view

Nombre para UI: Ver Funciones Asignadas
Modulo: MOD_Access - Gestion de Permisos
ID Caso de Uso: UC-014
Prioridad: ALTA
Frecuencia: Diaria
Estado: Activo

### DESCRIPCION

Permite consultar las funciones atomicas asignadas a un usuario especifico: cuales funciones tiene activas, cuando fueron asignadas, quien las asigno, y si alguna fue revocada (historial). Esta funcion es de solo lectura y no modifica los permisos. Fundamental para auditoria de permisos y verificacion de accesos.

### PRECONDICIONES

- Usuario tiene sesion activa
- Usuario tiene funcion access.view asignada
- El usuario objetivo existe en el sistema

### FLUJO PRINCIPAL (8 PASOS)

1. Usuario navega a seccion "Ver Funciones" o al perfil de un usuario especifico
2. Sistema solicita identificador del usuario objetivo (user_id o username)
3. Sistema verifica que el usuario objetivo existe
4. Sistema carga las funciones asignadas al usuario objetivo
5. Sistema muestra funciones activas (assigned_at, assigned_by)
6. Sistema muestra historial de funciones revocadas (revoked_at, revoked_by) si aplica
7. Sistema muestra reglas SoD que aplican al usuario
8. Usuario puede filtrar por modulo o estado (activa/revocada)

### FLUJOS ALTERNATIVOS

**A1. Usuario objetivo no existe (paso 3)**

- Sistema no encuentra el usuario con el ID o username proporcionado
- Sistema muestra error: "Usuario no encontrado" (ACC-001)
- Caso de uso termina

**A2. Usuario sin funcion access.view**

- Sistema detecta que usuario no tiene funcion
- Sistema muestra error 403: "No tiene permisos para ver funciones asignadas" (ACC-002)
- Usuario es redirigido a pagina anterior
- Caso de uso termina

**A3. Usuario objetivo sin funciones asignadas (paso 4)**

- Sistema no encuentra funciones para el usuario
- Sistema muestra mensaje: "Este usuario no tiene funciones asignadas" (INFO-017)
- Se muestra perfil del usuario con lista vacia
- Caso de uso termina exitosamente

**A4. Ver propio perfil**

- Usuario consulta sus propias funciones asignadas (siempre permitido)
- No requiere funcion access.view para ver las propias funciones
- Sistema muestra solo funciones activas propias

### POSTCONDICIONES

Exito:

- Lista de funciones asignadas mostrada
- Historial de revocaciones mostrado (si aplica)
- Reglas SoD del usuario identificadas

Fallo:

- Si no tiene permisos, no accede a la vista
- Si usuario no existe, error claro al usuario

### REGLAS DE NEGOCIO

- RN-050: access.view es solo lectura, NO modifica permisos
- RN-051: Se muestran funciones activas e historial de revocaciones
- RN-052: Cada funcion muestra: nombre, modulo, fecha asignacion, quien asigno
- RN-053: Funciones revocadas muestran: fecha revocacion, quien revoco, justificacion
- RN-054: Se identifican y muestran las reglas SoD aplicables al usuario

### RESTRICCIONES TECNICAS

- CNST-019: Solo lectura (GET), no permite modificaciones
- Tiempo de respuesta esperado: < 500ms

### REGLAS SoD

Ninguna

### MENSAJES DEL SISTEMA

Errores:

- ACC-001: "Usuario no encontrado"
- ACC-002: "No tiene permisos para ver funciones asignadas"

Informativos:

- INFO-017: "Este usuario no tiene funciones asignadas"
- INFO-018: "Mostrando X funciones activas y Y revocadas"

### IMPLEMENTACION TECNICA

**Ver funciones de un usuario**

Endpoint: GET /api/v1/users/{user_id}/functions

Response Exitosa (200 OK):

```json
{
  "success": true,
  "user": {
    "id": 150,
    "username": "plopez",
    "email": "pedro.lopez@empresa.com",
    "full_name": "Pedro Lopez"
  },
  "functions": {
    "active": [
      {
        "function_code": "users.view",
        "function_name": "Ver Usuarios",
        "module": "MOD_Users",
        "assigned_at": "2026-01-15T10:00:00Z",
        "assigned_by": {
          "id": 100,
          "username": "admin_asignador"
        },
        "justification": "Acceso basico para analista de soporte. Aprobado por gerencia.",
        "sod_groups": []
      },
      {
        "function_code": "reports.view_basic",
        "function_name": "Ver Reportes Basicos",
        "module": "MOD_Reports",
        "assigned_at": "2026-01-15T10:00:00Z",
        "assigned_by": {
          "id": 100,
          "username": "admin_asignador"
        },
        "justification": "Acceso basico para analista de soporte. Aprobado por gerencia.",
        "sod_groups": []
      }
    ],
    "revoked": [
      {
        "function_code": "users.create",
        "function_name": "Crear Usuarios",
        "module": "MOD_Users",
        "assigned_at": "2025-10-01T09:00:00Z",
        "assigned_by": {
          "id": 100,
          "username": "admin_asignador"
        },
        "revoked_at": "2026-01-10T14:00:00Z",
        "revoked_by": {
          "id": 101,
          "username": "admin_revocador"
        },
        "revocation_justification": "Cambio de rol. Ya no requiere crear usuarios."
      }
    ]
  },
  "sod_rules_applicable": [
    {
      "rule": "SoD 3 - report_data_separation",
      "description": "Si se asigna reports.modify_data, no puede tener reports.approve",
      "currently_violated": false
    }
  ],
  "summary": {
    "active_count": 2,
    "revoked_count": 1,
    "total_assigned_ever": 3
  }
}
```

Response - Usuario no encontrado (404 Not Found):

```json
{
  "success": false,
  "error_code": "ACC-001",
  "message": "Usuario no encontrado"
}
```

Response - Sin permisos (403 Forbidden):

```json
{
  "success": false,
  "error_code": "ACC-002",
  "message": "No tiene permisos para ver funciones asignadas"
}
```

Codigos HTTP:

- 200 OK: Consulta exitosa
- 403 Forbidden: Sin funcion access.view
- 404 Not Found: Usuario no existe
- 500 Internal Server Error: Error del servidor

### VALIDACIONES

- user_id: Entero positivo, debe existir en base de datos
- Verificacion de que el usuario objetivo existe antes de cargar funciones

### AUDITORIA

Se registra en AuditLog:

- Accion: view_user_functions
- Usuario: user_id (quien consulta)
- Target: user_id del usuario consultado
- Timestamp: hora exacta
- Detalles: cuantas funciones activas y revocadas se mostraron

Ejemplo de log:

```json
{
  "timestamp": "2026-03-22T10:30:00Z",
  "action": "view_user_functions",
  "user_id": 123,
  "target_user_id": 150,
  "ip_address": "192.168.1.100",
  "user_agent": "Chrome/120.0",
  "result": "success",
  "details": {
    "active_functions_shown": 2,
    "revoked_functions_shown": 1
  }
}
```

### SEGURIDAD

Protecciones Implementadas:

- Solo lectura, no permite modificar permisos
- Requiere funcion access.view para ver permisos de otros usuarios
- Usuario siempre puede ver sus propias funciones
- Todas las consultas auditadas

### NOTAS IMPORTANTES

- Esta funcion es SOLO LECTURA, no modifica ningun permiso
- Para asignar funciones usar access.assign
- Para revocar funciones usar access.revoke
- Un usuario siempre puede consultar sus propias funciones asignadas
- El historial de revocaciones queda visible para trazabilidad
- Las reglas SoD se muestran como informacion adicional para el administrador

---

Sistema IACT - Analisis IVR
Version: 1.0.0 | Fecha documento: 2026-03-22 | Modelo RBAC: v7.0.0
