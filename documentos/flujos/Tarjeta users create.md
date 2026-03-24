## TARJETA: users.create

Nombre para UI: Crear Usuarios
Modulo: MOD_Users - Gestion de Usuarios
ID Caso de Uso: UC-006
Prioridad: ALTA
Frecuencia: Semanal
Estado: Activo

### DESCRIPCION

Permite crear nuevas cuentas de usuario en el sistema especificando datos basicos requeridos: username, email, nombre completo. El usuario creado se genera con estado activo por defecto y sin funciones asignadas. La asignacion de funciones requiere la funcion access.assign adicional.

### PRECONDICIONES

- Usuario tiene sesion activa
- Usuario tiene funcion users.create asignada
- Datos del nuevo usuario disponibles (username, email, nombre)

### FLUJO PRINCIPAL (15 PASOS)

1. Usuario navega a seccion "Crear Usuario"
2. Sistema muestra formulario de creacion
3. Usuario ingresa username (3-30 caracteres alfanumericos)
4. Usuario ingresa email (formato valido)
5. Usuario ingresa nombre (first_name)
6. Usuario ingresa apellido (last_name)
7. Usuario selecciona area asignada
8. Usuario hace clic en "Crear Usuario"
9. Sistema valida formato de username (CNST-011)
10. Sistema valida que username sea unico
11. Sistema valida formato de email (CNST-012)
12. Sistema valida que email sea unico
13. Sistema genera contrasena temporal aleatoria
14. Sistema crea cuenta con estado activo
15. Sistema muestra confirmacion con username y contrasena temporal

### FLUJOS ALTERNATIVOS

**A1. Username ya existe (paso 10)**

- Sistema detecta username duplicado
- Sistema muestra error: "El username ya esta en uso" (USR-003)
- Usuario permanece en formulario
- Caso de uso puede reintentar desde paso 3

**A2. Email ya existe (paso 12)**

- Sistema detecta email duplicado
- Sistema muestra error: "El email ya esta registrado" (USR-004)
- Usuario permanece en formulario
- Caso de uso puede reintentar desde paso 4

**A3. Username con formato invalido (paso 9)**

- Sistema detecta formato invalido
- Sistema muestra errores especificos:
  - USR-005: "Username debe tener entre 3 y 30 caracteres"
  - USR-006: "Username solo puede contener letras, numeros y guion bajo"
- Usuario permanece en formulario
- Caso de uso puede reintentar desde paso 3

**A4. Email con formato invalido (paso 11)**

- Sistema detecta formato invalido de email
- Sistema muestra error: "Email invalido" (USR-007)
- Usuario permanece en formulario
- Caso de uso puede reintentar desde paso 4

**A5. Usuario sin funcion users.create**

- Sistema detecta que usuario no tiene funcion
- Sistema muestra error 403: "No tiene permisos para crear usuarios" (USR-001)
- Usuario es redirigido a pagina anterior
- Caso de uso termina

### POSTCONDICIONES

Exito:

- Usuario creado con estado activo
- Contrasena temporal generada
- Usuario sin funciones asignadas
- Registro en AuditLog

Fallo:

- Usuario no creado
- Datos no guardados
- Usuario puede reintentar

### REGLAS DE NEGOCIO

- RN-030: Username debe ser unico en todo el sistema
- RN-031: Email debe ser unico en todo el sistema
- RN-032: Contrasena temporal generada aleatoriamente (8 caracteres)
- RN-033: Usuario creado NO tiene funciones asignadas
- RN-034: Para asignar funciones se requiere access.assign adicional
- RN-035: Usuario creado con estado is_active=true por defecto
- RN-036: Username NO puede modificarse despues de creacion

### RESTRICCIONES TECNICAS

- CNST-011: Username unico, alfanumerico, 3-30 caracteres
  - Solo letras (a-z, A-Z)
  - Numeros (0-9)
  - Guion bajo (_)
  - Case-sensitive
- CNST-012: Email unico, formato valido
  - Formato: usuario@dominio.ext
  - Unico en toda la base de datos
  - Case-insensitive para validacion
- CNST-013: Usuario se marca inactivo tras 90 dias sin login

### REGLAS SoD

SoD 2 - user_audit_separation:

- INCOMPATIBLE con: audit.view, audit.search
- Razon: Quien crea usuarios NO debe auditar sus propias acciones

### MENSAJES DEL SISTEMA

Errores:

- USR-001: "No tiene permisos para crear usuarios" (sin funcion users.create)
- USR-003: "El username ya esta en uso" (username duplicado)
- USR-004: "El email ya esta registrado" (email duplicado)
- USR-005: "Username debe tener entre 3 y 30 caracteres" (longitud invalida)
- USR-006: "Username solo puede contener letras, numeros y guion bajo" (caracteres invalidos)
- USR-007: "Email invalido" (formato email incorrecto)
- USR-008: "Todos los campos son obligatorios" (campos vacios)

Confirmacion:

- OK-006: "Usuario creado exitosamente" (creacion exitosa)

Informativos:

- INFO-009: "Contrasena temporal: {password}. El usuario debe cambiarla en su primer inicio de sesion" (muestra contrasena temporal)
- INFO-010: "Usuario creado sin funciones asignadas. Use Asignar Funciones para otorgar permisos" (recordatorio)

### IMPLEMENTACION TECNICA

**Crear usuario**

Endpoint: POST /api/v1/users

Request:

```json
{
  "username": "plopez",
  "email": "pedro.lopez@empresa.com",
  "first_name": "Pedro",
  "last_name": "Lopez",
  "area": "Soporte"
}
```

Response Exitosa (201 Created):

```json
{
  "success": true,
  "message": "Usuario creado exitosamente",
  "user": {
    "id": 150,
    "username": "plopez",
    "email": "pedro.lopez@empresa.com",
    "first_name": "Pedro",
    "last_name": "Lopez",
    "is_active": true,
    "is_locked": false,
    "area": "Soporte",
    "date_joined": "2026-02-24T16:00:00Z",
    "last_login": null,
    "functions_count": 0
  },
  "temporary_password": "Abc123XyZ",
  "next_steps": [
    "Asignar funciones al usuario (requiere access.assign)",
    "Configurar preguntas de seguridad",
    "Notificar al usuario sus credenciales"
  ]
}
```

Response - Username duplicado (400 Bad Request):

```json
{
  "success": false,
  "error_code": "USR-003",
  "message": "El username ya esta en uso",
  "field": "username"
}
```

Response - Email duplicado (400 Bad Request):

```json
{
  "success": false,
  "error_code": "USR-004",
  "message": "El email ya esta registrado",
  "field": "email"
}
```

Response - Username invalido (400 Bad Request):

```json
{
  "success": false,
  "error_code": "USR-006",
  "message": "Username solo puede contener letras, numeros y guion bajo",
  "field": "username",
  "invalid_value": "pedro.lopez"
}
```

Response - Sin permisos (403 Forbidden):

```json
{
  "success": false,
  "error_code": "USR-001",
  "message": "No tiene permisos para crear usuarios"
}
```

Codigos HTTP:

- 201 Created: Usuario creado exitosamente
- 400 Bad Request: Datos invalidos o duplicados
- 403 Forbidden: Sin funcion users.create
- 500 Internal Server Error: Error del servidor

### VALIDACIONES

Validacion de Username:

- Longitud: 3-30 caracteres
- Caracteres permitidos: a-z, A-Z, 0-9, _ (guion bajo)
- No puede contener espacios
- No puede contener caracteres especiales (excepto _)
- Case-sensitive
- Unico en base de datos

Validacion de Email:

- Formato valido: usuario@dominio.ext
- No puede contener espacios
- Debe tener arroba y dominio valido
- Case-insensitive para comparacion de unicidad
- Unico en base de datos

Validacion de Nombres:

- first_name: Obligatorio, minimo 2 caracteres, maximo 50
- last_name: Obligatorio, minimo 2 caracteres, maximo 50
- Pueden contener letras, espacios, acentos

Validacion de Area:

- Debe ser un area valida del sistema
- Valores permitidos: Comercial, Soporte, Finanzas, Operaciones, RRHH

Generacion de Contrasena Temporal:

- Longitud: 8 caracteres
- Incluye: mayusculas, minusculas, numeros
- Cumple politica CNST-003
- Aleatoria y segura

### AUDITORIA

Se registra en AuditLog:

- Accion: create_user
- Usuario: user_id (quien crea)
- Timestamp: hora exacta
- IP Address: IP desde donde crea
- User Agent: navegador y dispositivo
- Detalles: username del usuario creado, email, area asignada, contrasena temporal (hash)

Ejemplo de log:

```json
{
  "timestamp": "2026-02-24T16:00:00Z",
  "action": "create_user",
  "user_id": 123,
  "target_user_id": 150,
  "ip_address": "192.168.1.100",
  "user_agent": "Chrome/120.0",
  "result": "success",
  "details": {
    "created_username": "plopez",
    "created_email": "pedro.lopez@empresa.com",
    "area": "Soporte",
    "temporary_password_hash": "bcrypt_hash...",
    "functions_assigned": 0
  }
}
```

### SEGURIDAD

Protecciones Implementadas:

- Validacion estricta de formato de username y email
- Unicidad garantizada en base de datos
- Contrasena temporal generada de forma segura
- Contrasena temporal hasheada antes de almacenar
- Usuario creado sin funciones (requiere asignacion explicita)
- Todas las creaciones auditadas
- SoD 2 previene que quien crea usuarios audite sus propias acciones

Informacion NO Expuesta:

- Contrasena temporal solo se muestra UNA vez al crear
- Contrasena no se almacena en texto plano
- Contrasena no se envia por email (CNST-001)

### NOTAS IMPORTANTES

- Usuario creado NO tiene funciones asignadas
- Para asignar funciones se requiere access.assign
- Contrasena temporal se muestra SOLO UNA VEZ al crear
- Contrasena temporal debe comunicarse al usuario de forma segura
- Usuario debe cambiar contrasena temporal en primer login
- Username NO puede modificarse despues de creacion
- Email SI puede modificarse con users.edit
- Usuario se crea con is_active=true
- Usuario se crea con is_locked=false
- Usuario NO se marca como inactivo hasta 90 dias sin login (CNST-013)

Violacion SoD 2:

- Usuario con users.create NO puede tener audit.view
- Usuario con users.create NO puede tener audit.search
- Razon: Prevenir que quien crea usuarios audite sus propias acciones

Proximos Pasos Despues de Crear:

1. Asignar funciones (requiere access.assign)
2. Configurar preguntas de seguridad del usuario
3. Notificar al usuario sus credenciales de forma segura
4. Usuario debe cambiar contrasena en primer login

Contrasena Temporal:

- Generada aleatoriamente
- 8 caracteres minimo
- Incluye mayusculas, minusculas, numeros
- Cumple politica de contrasena (CNST-003)
- Usuario debe cambiarla en primer login
- NO se envia por email (cumple CNST-001)

---

Sistema IACT - Analisis IVR
Version: 1.0.0 | Fecha documento: 2026-03-14 | Modelo RBAC: v7.0.0
