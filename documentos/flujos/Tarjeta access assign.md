## TARJETA: access.assign

Nombre para UI: Asignar Funciones
Modulo: MOD_Access - Gestion de Permisos
ID Caso de Uso: UC-015
Prioridad: CRITICA
Frecuencia: Semanal
Estado: Activo

### DESCRIPCION

Permite asignar una o varias funciones atomicas a un usuario del sistema. El sistema valida las reglas SoD antes de confirmar la asignacion: si alguna funcion a asignar viola una regla SoD con funciones ya existentes del usuario, se rechaza la operacion completa (atomica). Requiere justificacion obligatoria minimo 20 caracteres.

### PRECONDICIONES

- Usuario tiene sesion activa
- Usuario tiene funcion access.assign asignada
- El usuario objetivo existe en el sistema
- Las funciones a asignar existen en el catalogo del sistema
- Justificacion disponible (minimo 20 caracteres)

### FLUJO PRINCIPAL (14 PASOS)

1. Usuario navega a seccion "Asignar Funciones" o al perfil del usuario objetivo
2. Sistema muestra funciones actuales del usuario objetivo
3. Sistema muestra catalogo completo de funciones disponibles
4. Usuario selecciona una o varias funciones a asignar
5. Sistema muestra preview de SoD: que funciones conflictan (informativo)
6. Usuario ingresa justificacion (minimo 20 caracteres)
7. Usuario hace clic en "Asignar Funciones"
8. Sistema valida que el usuario objetivo existe
9. Sistema valida que las funciones seleccionadas existen en catalogo
10. Sistema valida reglas SoD: verifica funciones ya asignadas + nuevas
11. Si hay violacion SoD: sistema rechaza TODA la operacion (atomico)
12. Si no hay violacion: sistema asigna todas las funciones seleccionadas
13. Sistema registra cada asignacion con: assigned_at, assigned_by, justification
14. Sistema muestra confirmacion con lista de funciones asignadas

### FLUJOS ALTERNATIVOS

**A1. Violacion de SoD (paso 10-11)**

- Sistema detecta que alguna funcion a asignar viola una regla SoD con funciones existentes
- Sistema rechaza TODA la operacion (no se asigna ninguna funcion del lote)
- Sistema muestra detalle de la violacion: que regla, que funciones conflictan
- Sistema muestra mensaje con codigo ACC-004
- Usuario puede modificar la seleccion y reintentar
- Caso de uso puede reintentar desde paso 4

**A2. Funcion ya asignada al usuario (paso 9)**

- Sistema detecta que una o mas funciones del lote ya estan asignadas al usuario
- Sistema muestra advertencia: "X funcion(es) ya estan asignadas al usuario" (ACC-005)
- Sistema puede omitir las ya asignadas y continuar con las nuevas
- Usuario confirma si desea continuar

**A3. Usuario objetivo no existe (paso 8)**

- Sistema no encuentra el usuario con el ID proporcionado
- Sistema muestra error: "Usuario no encontrado" (ACC-001)
- Caso de uso termina

**A4. Justificacion insuficiente (paso 9)**

- Sistema detecta justificacion con menos de 20 caracteres
- Sistema muestra error: "La justificacion debe tener al menos 20 caracteres" (ACC-006)
- Usuario permanece en formulario
- Caso de uso puede reintentar desde paso 6

**A5. Sin funciones seleccionadas (paso 7)**

- Sistema detecta que no hay funciones seleccionadas
- Sistema muestra error: "Seleccione al menos una funcion para asignar" (ACC-007)
- Usuario permanece en formulario
- Caso de uso puede reintentar desde paso 4

**A6. Usuario sin funcion access.assign**

- Sistema detecta que el usuario que opera no tiene funcion
- Sistema muestra error 403: "No tiene permisos para asignar funciones" (ACC-002)
- Usuario es redirigido a pagina anterior
- Caso de uso termina

### POSTCONDICIONES

Exito:

- Todas las funciones seleccionadas asignadas al usuario objetivo
- Registros de asignacion creados con: assigned_at, assigned_by, justification
- Registro de auditoria creado
- Usuario objetivo puede ejercer las nuevas funciones inmediatamente

Fallo (violacion SoD):

- Ninguna funcion asignada (operacion atomica)
- Sin cambios en permisos del usuario
- Detalle de violacion mostrado

### REGLAS DE NEGOCIO

- RN-055: Operacion atomica: todas las funciones del lote se asignan o ninguna
- RN-056: Justificacion obligatoria minimo 20 caracteres
- RN-057: Validacion SoD obligatoria antes de asignar
- RN-058: Las funciones asignadas aplican inmediatamente (sin espera)
- RN-059: Si funcion ya asignada, se puede ignorar o retornar advertencia
- RN-060: Usuario asignador no puede asignarse funciones a si mismo (CNST-020)

### RESTRICCIONES TECNICAS

- CNST-020: Usuario asignador no puede modificar sus propias funciones
- Operacion transaccional: si falla alguna asignacion, se hace rollback completo

### REGLAS SoD

- SoD 1 (function_assignment_control)
- INCOMPATIBLE con: access.revoke
- Razon: Quien asigna funciones NO puede revocarlas (separacion de poderes)

### MENSAJES DEL SISTEMA

Errores:

- ACC-001: "Usuario no encontrado"
- ACC-002: "No tiene permisos para asignar funciones"
- ACC-004: "Violacion de regla SoD: [nombre_regla]. La asignacion fue rechazada"
- ACC-005: "X funcion(es) ya estan asignadas al usuario"
- ACC-006: "La justificacion debe tener al menos 20 caracteres"
- ACC-007: "Seleccione al menos una funcion para asignar"
- ACC-008: "No puede modificar sus propias funciones"

Confirmacion:

- OK-014: "Funciones asignadas exitosamente"

Informativos:

- INFO-019: "Asignando X funcion(es) al usuario Y"
- INFO-020: "Verificando reglas SoD..."

### IMPLEMENTACION TECNICA

**Asignar funciones a un usuario**

Endpoint: POST /api/v1/users/{user_id}/functions/assign

Request:

```json
{
  "function_codes": ["users.view", "users.search", "reports.view_basic"],
  "justification": "Nuevo analista de datos. Requiere acceso a usuarios y reportes basicos. Aprobado por gerente RRHH ticket HR-2024-0456."
}
```

Response Exitosa (201 Created):

```json
{
  "success": true,
  "message": "Funciones asignadas exitosamente",
  "assigned": [
    {
      "function_code": "users.view",
      "function_name": "Ver Usuarios",
      "assigned_at": "2026-03-22T10:30:00Z",
      "assigned_by": "admin_asignador"
    },
    {
      "function_code": "users.search",
      "function_name": "Buscar Usuarios",
      "assigned_at": "2026-03-22T10:30:00Z",
      "assigned_by": "admin_asignador"
    },
    {
      "function_code": "reports.view_basic",
      "function_name": "Ver Reportes Basicos",
      "assigned_at": "2026-03-22T10:30:00Z",
      "assigned_by": "admin_asignador"
    }
  ],
  "skipped": [],
  "user": {
    "id": 150,
    "username": "plopez",
    "total_active_functions": 3
  }
}
```

Response - Violacion SoD (400 Bad Request):

```json
{
  "success": false,
  "error_code": "ACC-004",
  "message": "Violacion de regla SoD: user_audit_separation. La asignacion fue rechazada",
  "details": {
    "rule_violated": "SoD 2 - user_audit_separation",
    "description": "Quien gestiona usuarios NO debe auditar sus propias acciones",
    "incompatible_pairs": [
      {
        "attempting_to_assign": "users.create",
        "conflicts_with_existing": "audit.view",
        "reason": "Quien crea usuarios NO puede ver auditoria"
      }
    ],
    "assigned_nothing": true,
    "note": "Ninguna funcion fue asignada (operacion atomica)"
  }
}
```

Response - Sin permisos (403 Forbidden):

```json
{
  "success": false,
  "error_code": "ACC-002",
  "message": "No tiene permisos para asignar funciones"
}
```

Response - Justificacion insuficiente (400 Bad Request):

```json
{
  "success": false,
  "error_code": "ACC-006",
  "message": "La justificacion debe tener al menos 20 caracteres",
  "current_length": 12,
  "required_length": 20
}
```

Codigos HTTP:

- 201 Created: Funciones asignadas exitosamente
- 400 Bad Request: Violacion SoD, justificacion invalida, sin funciones seleccionadas
- 403 Forbidden: Sin funcion access.assign o intento de modificar propias funciones
- 404 Not Found: Usuario objetivo no encontrado
- 500 Internal Server Error: Error del servidor

### VALIDACIONES

Validacion de Usuario Objetivo:

- user_id: Entero positivo, debe existir en base de datos
- Usuario objetivo debe estar activo (is_active=true)

Validacion de Funciones:

- function_codes: Lista no vacia
- Cada codigo debe existir en el catalogo de funciones
- Verificar cuales ya estan asignadas (retornar en "skipped")

Validacion de Justificacion:

- Obligatoria
- Minimo 20 caracteres
- Recomendado: referencia a ticket o aprobacion

Validacion de SoD (para cada funcion nueva):

- SoD 1: access.assign INCOMPATIBLE con access.revoke
- SoD 2: users.create/edit/delete INCOMPATIBLE con audit.view/search
- SoD 3: reports.modify_data INCOMPATIBLE con reports.approve
- Verificar funciones EXISTENTES del usuario + funciones NUEVAS del lote entre si

### AUDITORIA

Se registra en AuditLog:

- Accion: assign_functions
- Usuario: user_id (quien asigna)
- Target: user_id del usuario objetivo
- Timestamp: hora exacta
- Detalles: funciones asignadas, justificacion, validacion SoD

Ejemplo de log:

```json
{
  "timestamp": "2026-03-22T10:30:00Z",
  "action": "assign_functions",
  "user_id": 100,
  "target_user_id": 150,
  "ip_address": "192.168.1.100",
  "user_agent": "Chrome/120.0",
  "result": "success",
  "details": {
    "functions_assigned": ["users.view", "users.search", "reports.view_basic"],
    "functions_skipped": [],
    "justification": "Nuevo analista de datos...",
    "sod_validation": "passed"
  }
}
```

Ejemplo de log - Fallo por SoD:

```json
{
  "timestamp": "2026-03-22T10:31:00Z",
  "action": "assign_functions",
  "user_id": 100,
  "target_user_id": 150,
  "result": "failed_sod",
  "details": {
    "functions_attempted": ["users.create", "audit.view"],
    "sod_rule_violated": "SoD 2 - user_audit_separation",
    "functions_assigned": 0
  }
}
```

### SEGURIDAD

Protecciones Implementadas:

- Validacion SoD obligatoria antes de asignar (no se puede omitir)
- Operacion atomica: no hay asignaciones parciales
- Justificacion obligatoria para trazabilidad
- Usuario no puede modificar sus propias funciones (CNST-020)
- SoD 1: quien asigna no puede revocar (separacion de poderes)
- Todas las asignaciones auditadas con detalle

Reglas SoD Validadas Automaticamente:

- SoD 1: access.assign <-> access.revoke
- SoD 2: users.create/edit/delete <-> audit.view/search
- SoD 3: reports.modify_data <-> reports.approve

### NOTAS IMPORTANTES

- Operacion ATOMICA: si una funcion del lote viola SoD, se rechaza TODO el lote
- Las funciones aplican INMEDIATAMENTE despues de asignar
- El asignador no puede asignarse funciones a si mismo
- El asignador no puede tener access.revoke (SoD 1)
- Siempre registrar en la justificacion el ticket o aprobacion formal
- Para ver las funciones actuales del usuario: usar access.view primero

---

Sistema IACT - Analisis IVR
Version: 1.0.0 | Fecha documento: 2026-03-22 | Modelo RBAC: v7.0.0
