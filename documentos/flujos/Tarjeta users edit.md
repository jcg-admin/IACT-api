## TARJETA: users.edit

Nombre para UI: Editar Usuarios
Modulo: MOD_Users - Gestion de Usuarios
ID Caso de Uso: UC-007
Prioridad: ALTA
Frecuencia: Semanal
Estado: Activo

### DESCRIPCION

Permite modificar datos de usuarios existentes en el sistema. Se pueden actualizar datos como email, nombre completo, area asignada y estado de la cuenta. El username NO puede modificarse una vez creado. La modificacion de funciones asignadas requiere la funcion access.assign adicional.

### PRECONDICIONES

- Usuario tiene sesion activa
- Usuario tiene funcion users.edit asignada
- Usuario objetivo existe en el sistema

### FLUJO PRINCIPAL (12 PASOS)

1. Usuario navega a "Gestion de Usuarios"
2. Usuario busca y selecciona usuario a editar
3. Sistema carga datos actuales del usuario
4. Sistema muestra formulario de edicion con datos precargados
5. Usuario modifica campos permitidos (email, nombre, apellido, area)
6. Usuario hace clic en "Guardar Cambios"
7. Sistema valida formato de email (si cambio)
8. Sistema valida que email sea unico (si cambio)
9. Sistema valida que nombres no esten vacios
10. Sistema actualiza registro en base de datos
11. Sistema registra cambio en AuditLog
12. Sistema muestra confirmacion: "Usuario actualizado exitosamente"

### FLUJOS ALTERNATIVOS

**A1. Email ya existe (paso 8)**

- Sistema detecta email duplicado
- Sistema muestra error: "El email ya esta registrado en otro usuario" (USR-004)
- Usuario permanece en formulario
- Caso de uso puede reintentar desde paso 5

**A2. Email con formato invalido (paso 7)**

- Sistema detecta formato invalido de email
- Sistema muestra error: "Email invalido" (USR-007)
- Usuario permanece en formulario
- Caso de uso puede reintentar desde paso 5

**A3. Nombres vacios (paso 9)**

- Sistema detecta nombres vacios
- Sistema muestra error: "Nombre y apellido son obligatorios" (USR-009)
- Usuario permanece en formulario
- Caso de uso puede reintentar desde paso 5

**A4. Usuario intenta cambiar username (paso 5)**

- Campo username esta deshabilitado
- Sistema muestra mensaje informativo: "Username no puede modificarse" (INFO-011)
- Usuario puede modificar otros campos
- Caso de uso continua

**A5. Usuario sin funcion users.edit**

- Sistema detecta que usuario no tiene funcion
- Sistema muestra error 403: "No tiene permisos para editar usuarios" (USR-010)
- Usuario es redirigido a pagina anterior
- Caso de uso termina

**A6. Usuario no encontrado (paso 3)**

- Sistema no encuentra usuario con ID especificado
- Sistema muestra error: "Usuario no encontrado" (USR-011)
- Usuario es redirigido a lista de usuarios
- Caso de uso termina

### POSTCONDICIONES

Exito:

- Datos de usuario actualizados
- Cambios registrados en AuditLog
- Usuario puede ver cambios reflejados

Fallo:

- Datos no modificados
- Usuario permanece con datos anteriores
- Usuario puede reintentar

### REGLAS DE NEGOCIO

- RN-037: Username NO puede modificarse despues de creacion
- RN-038: Email debe ser unico (excepto el del mismo usuario)
- RN-039: Cambio de email requiere validacion de formato
- RN-040: Nombres (first_name, last_name) son obligatorios
- RN-041: Modificar funciones requiere access.assign adicional
- RN-042: Cambios son auditados automaticamente

### RESTRICCIONES TECNICAS

- CNST-012: Email unico, formato valido
  - Formato: usuario@dominio.ext
  - Unico en toda la base de datos (excepto usuario actual)
  - Case-insensitive para validacion

### REGLAS SoD

SoD 2 - user_audit_separation:

- INCOMPATIBLE con: audit.view, audit.search
- Razon: Quien edita usuarios NO debe auditar sus propias acciones

### MENSAJES DEL SISTEMA

Errores:

- USR-004: "El email ya esta registrado en otro usuario" (email duplicado)
- USR-007: "Email invalido" (formato email incorrecto)
- USR-009: "Nombre y apellido son obligatorios" (campos vacios)
- USR-010: "No tiene permisos para editar usuarios" (sin funcion users.edit)
- USR-011: "Usuario no encontrado" (ID no existe)

Confirmacion:

- OK-007: "Usuario actualizado exitosamente" (edicion exitosa)

Informativos:

- INFO-011: "Username no puede modificarse" (campo deshabilitado)
- INFO-012: "Para modificar funciones use Asignar Funciones" (requiere access.assign)

### IMPLEMENTACION TECNICA

**Editar usuario**

Endpoint: PATCH /api/v1/users/{user_id}

Request:

```json
{
  "email": "pedro.lopez.nuevo@empresa.com",
  "first_name": "Pedro Antonio",
  "last_name": "Lopez Garcia",
  "area": "Finanzas"
}
```

Response Exitosa (200 OK):

```json
{
  "success": true,
  "message": "Usuario actualizado exitosamente",
  "user": {
    "id": 150,
    "username": "plopez",
    "email": "pedro.lopez.nuevo@empresa.com",
    "first_name": "Pedro Antonio",
    "last_name": "Lopez Garcia",
    "is_active": true,
    "is_locked": false,
    "area": "Finanzas",
    "date_joined": "2026-02-24T16:00:00Z",
    "last_login": "2026-02-25T08:30:00Z",
    "functions_count": 5
  },
  "changes_made": [
    {
      "field": "email",
      "old_value": "pedro.lopez@empresa.com",
      "new_value": "pedro.lopez.nuevo@empresa.com"
    },
    {
      "field": "first_name",
      "old_value": "Pedro",
      "new_value": "Pedro Antonio"
    },
    {
      "field": "area",
      "old_value": "Soporte",
      "new_value": "Finanzas"
    }
  ]
}
```

Response - Email duplicado (400 Bad Request):

```json
{
  "success": false,
  "error_code": "USR-004",
  "message": "El email ya esta registrado en otro usuario",
  "field": "email",
  "conflicting_user_id": 42
}
```

Response - Email invalido (400 Bad Request):

```json
{
  "success": false,
  "error_code": "USR-007",
  "message": "Email invalido",
  "field": "email",
  "invalid_value": "pedro@invalido"
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
  "error_code": "USR-010",
  "message": "No tiene permisos para editar usuarios"
}
```

Codigos HTTP:

- 200 OK: Usuario actualizado exitosamente
- 400 Bad Request: Datos invalidos o duplicados
- 403 Forbidden: Sin funcion users.edit
- 404 Not Found: Usuario no existe
- 500 Internal Server Error: Error del servidor

### VALIDACIONES

Validacion de Email:

- Formato valido: usuario@dominio.ext
- No puede contener espacios
- Debe tener arroba y dominio valido
- Case-insensitive para comparacion de unicidad
- Unico en base de datos (excepto usuario actual)

Validacion de Nombres:

- first_name: Obligatorio, minimo 2 caracteres, maximo 50
- last_name: Obligatorio, minimo 2 caracteres, maximo 50
- Pueden contener letras, espacios, acentos
- No pueden estar vacios

Validacion de Area:

- Debe ser un area valida del sistema
- Valores permitidos: Comercial, Soporte, Finanzas, Operaciones, RRHH

Campos NO Modificables:

- username (inmutable)
- id (inmutable)
- date_joined (inmutable)
- is_active (requiere users.lock/users.unlock)
- is_locked (requiere users.lock/users.unlock)
- funciones asignadas (requiere access.assign)

Campos Modificables:

- email
- first_name
- last_name
- area

### AUDITORIA

Se registra en AuditLog:

- Accion: edit_user
- Usuario: user_id (quien edita)
- Timestamp: hora exacta
- IP Address: IP desde donde edita
- User Agent: navegador y dispositivo
- Detalles: ID del usuario editado, campos modificados, valores anteriores, valores nuevos

Ejemplo de log:

```json
{
  "timestamp": "2026-02-25T10:15:00Z",
  "action": "edit_user",
  "user_id": 123,
  "target_user_id": 150,
  "ip_address": "192.168.1.100",
  "user_agent": "Chrome/120.0",
  "result": "success",
  "details": {
    "edited_username": "plopez",
    "changes": [
      {
        "field": "email",
        "old_value": "pedro.lopez@empresa.com",
        "new_value": "pedro.lopez.nuevo@empresa.com"
      },
      {
        "field": "first_name",
        "old_value": "Pedro",
        "new_value": "Pedro Antonio"
      },
      {
        "field": "area",
        "old_value": "Soporte",
        "new_value": "Finanzas"
      }
    ]
  }
}
```

### SEGURIDAD

Protecciones Implementadas:

- Validacion estricta de formato de email
- Unicidad garantizada en base de datos
- Username inmutable (previene suplantacion)
- Solo campos permitidos pueden modificarse
- Todas las ediciones auditadas con valores anteriores y nuevos
- SoD 2 previene que quien edita usuarios audite sus propias acciones

Campos Protegidos:

- username: Inmutable, no puede cambiarse
- is_active: Requiere users.lock/users.unlock
- is_locked: Requiere users.lock/users.unlock
- funciones: Requiere access.assign

Informacion Auditada:

- Todos los cambios registrados
- Valores anteriores preservados
- Quien hizo el cambio
- Cuando se hizo el cambio
- Desde que IP

### NOTAS IMPORTANTES

- Username NO puede modificarse una vez creado
- Email SI puede modificarse (debe ser unico)
- Para cambiar estado (activo/inactivo) usar users.lock/users.unlock
- Para modificar funciones usar access.assign
- Todos los cambios son auditados con valores anteriores y nuevos
- Sistema registra quien hizo cada cambio

Violacion SoD 2:

- Usuario con users.edit NO puede tener audit.view
- Usuario con users.edit NO puede tener audit.search
- Razon: Prevenir que quien edita usuarios audite sus propias acciones

Campos Inmutables:

- username (nunca puede cambiar)
- id (nunca puede cambiar)
- date_joined (fecha de creacion, inmutable)

Campos que Requieren Funcion Adicional:

- is_active: users.lock / users.unlock
- is_locked: users.lock / users.unlock
- funciones asignadas: access.assign / access.revoke

Diferencia entre users.edit y access.assign:

- users.edit: Modifica datos personales (email, nombre, area)
- access.assign: Modifica funciones de acceso al sistema

---

Sistema IACT - Analisis IVR
Version: 1.0.0 | Fecha documento: 2026-03-14 | Modelo RBAC: v7.0.0
