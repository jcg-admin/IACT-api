## TARJETA: users.view

Nombre para UI: Ver Usuarios
Modulo: MOD_Users - Gestion de Usuarios
ID Caso de Uso: UC-006
Prioridad: ALTA
Frecuencia: Diaria
Estado: Activo

### DESCRIPCION

Permite consultar la lista de usuarios del sistema con sus datos basicos. Los usuarios se muestran con informacion general como username, email, nombre completo, estado de la cuenta y ultima actividad. La vista puede filtrarse por diferentes criterios.

### PRECONDICIONES

- Usuario tiene sesion activa
- Usuario tiene funcion users.view asignada

### FLUJO PRINCIPAL (8 PASOS)

1. Usuario navega a seccion "Usuarios" o "Gestion de Usuarios"
2. Sistema carga lista de usuarios
3. Sistema aplica filtros por objeto segun area del usuario (si aplica)
4. Sistema muestra lista paginada de usuarios
5. Usuario puede ordenar por columna (username, email, fecha creacion)
6. Usuario puede filtrar por estado (activo, inactivo, bloqueado)
7. Usuario puede buscar por texto (username, email, nombre)
8. Sistema actualiza lista segun filtros aplicados

### FLUJOS ALTERNATIVOS

**A1. Sin usuarios encontrados (paso 4)**

- Sistema no encuentra usuarios con los filtros aplicados
- Sistema muestra mensaje: "No se encontraron usuarios"
- Usuario puede limpiar filtros o cambiar criterios
- Caso de uso termina

**A2. Usuario sin funcion users.view (paso 2)**

- Sistema detecta que usuario no tiene funcion
- Sistema muestra error 403: "No tiene permisos para ver usuarios"
- Usuario es redirigido a pagina anterior
- Caso de uso termina

**A3. Exportar lista (desde paso 4)**

- Usuario hace clic en "Exportar"
- Sistema verifica si usuario tiene users.export
- Si NO tiene: muestra error "Requiere funcion users.export"
- Si SI tiene: genera archivo CSV con usuarios
- Caso de uso continua

### POSTCONDICIONES

Exito:

- Lista de usuarios mostrada
- Filtros aplicados correctamente
- Usuario puede ver datos basicos de usuarios

Fallo:

- Si no tiene permisos, no accede a la lista
- Si hay error tecnico, muestra mensaje de error

### REGLAS DE NEGOCIO

- RN-026: Usuario solo ve usuarios de su area (si aplica filtro por objeto)
- RN-027: Administradores ven todos los usuarios
- RN-028: Lista paginada de 25 usuarios por pagina
- RN-029: Datos sensibles (telefono, direccion) no se muestran sin funcion adicional

### RESTRICCIONES TECNICAS

- CNST-011: Username unico, alfanumerico, 3-30 caracteres
- CNST-012: Email unico, formato valido
- CNST-013: Usuario inactivo tras 90 dias sin login

### REGLAS SoD

Ninguna

### MENSAJES DEL SISTEMA

Errores:

- USR-001: "No tiene permisos para ver usuarios" (sin funcion users.view)
- USR-002: "Requiere funcion users.export para exportar" (sin funcion export)

Informativos:

- INFO-007: "No se encontraron usuarios" (sin resultados)
- INFO-008: "Mostrando X de Y usuarios" (paginacion)

### IMPLEMENTACION TECNICA

**Ver lista de usuarios**

Endpoint: GET /api/v1/users

Query Parameters:

```
?page=1
&page_size=25
&search=juan
&status=active
&order_by=username
&order=asc
&area=Comercial
```

Response Exitosa (200 OK):

```json
{
  "success": true,
  "users": [
    {
      "id": 1,
      "username": "juanperez",
      "email": "juan.perez@empresa.com",
      "first_name": "Juan",
      "last_name": "Perez",
      "is_active": true,
      "is_locked": false,
      "locked_until": null,
      "last_login": "2026-02-24T10:30:00Z",
      "date_joined": "2025-01-15T08:00:00Z",
      "area": "Comercial",
      "functions_count": 12
    },
    {
      "id": 2,
      "username": "mgarcia",
      "email": "maria.garcia@empresa.com",
      "first_name": "Maria",
      "last_name": "Garcia",
      "is_active": true,
      "is_locked": false,
      "locked_until": null,
      "last_login": "2026-02-23T16:45:00Z",
      "date_joined": "2025-02-01T09:00:00Z",
      "area": "Soporte",
      "functions_count": 8
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 25,
    "total_users": 47,
    "total_pages": 2
  },
  "filters_applied": {
    "search": "juan",
    "status": "active",
    "area": null
  }
}
```

Response - Sin permisos (403 Forbidden):

```json
{
  "success": false,
  "error_code": "USR-001",
  "message": "No tiene permisos para ver usuarios"
}
```

Response - Sin resultados (200 OK):

```json
{
  "success": true,
  "users": [],
  "pagination": {
    "page": 1,
    "page_size": 25,
    "total_users": 0,
    "total_pages": 0
  },
  "message": "No se encontraron usuarios"
}
```

Codigos HTTP:

- 200 OK: Consulta exitosa (incluso sin resultados)
- 403 Forbidden: Sin funcion users.view
- 500 Internal Server Error: Error del servidor

### VALIDACIONES

Validacion de Funcion:

- Usuario debe tener users.view asignada

Validacion de Filtros:

- page: Entero positivo, minimo 1
- page_size: Entero positivo, maximo 100
- status: valores permitidos: active, inactive, locked, all
- order_by: valores permitidos: username, email, last_login, date_joined
- order: valores permitidos: asc, desc

Filtrado por Objeto:

- Si usuario NO tiene access.assign (no es admin): filtrar usuarios por area del usuario, solo ve usuarios de su area
- Si usuario SI tiene access.assign: ve todos los usuarios del sistema

### AUDITORIA

Se registra en AuditLog:

- Accion: view_users
- Usuario: user_id
- Timestamp: hora exacta
- IP Address: IP desde donde consulta
- User Agent: navegador y dispositivo
- Detalles: filtros aplicados, numero de resultados, pagina consultada

Ejemplo de log:

```json
{
  "timestamp": "2026-02-24T15:00:00Z",
  "action": "view_users",
  "user_id": 123,
  "ip_address": "192.168.1.100",
  "user_agent": "Chrome/120.0",
  "result": "success",
  "details": {
    "filters": {
      "search": "juan",
      "status": "active",
      "area": "Comercial"
    },
    "results_count": 3,
    "page": 1
  }
}
```

### SEGURIDAD

Protecciones Implementadas:

- Usuario solo ve usuarios segun su nivel de acceso
- Datos sensibles no se exponen sin funcion adicional
- Lista filtrada por area (si no es administrador)
- Todas las consultas auditadas

Informacion Mostrada:

- Username
- Email
- Nombre completo
- Estado (activo/inactivo/bloqueado)
- Ultima conexion
- Fecha de creacion
- Area asignada
- Cantidad de funciones asignadas

Informacion NO Mostrada (sin funcion adicional):

- Telefono personal
- Direccion
- Funciones especificas asignadas
- Historial de contrasenas
- Detalles de auditoria

### NOTAS IMPORTANTES

- Lista paginada de 25 usuarios por defecto
- Puede ajustarse hasta 100 usuarios por pagina
- Usuario NO administrador solo ve usuarios de su area
- Administradores (con access.assign) ven todos los usuarios
- Para exportar lista requiere funcion users.export adicional
- Para ver funciones asignadas de un usuario requiere access.view
- Usuarios inactivos se muestran con indicador visual
- Usuarios bloqueados se muestran con indicador y tiempo restante
- Ultima conexion muestra tiempo relativo (hace 2 horas, hace 3 dias)
- Lista se actualiza en tiempo real al cambiar filtros

Campos de Busqueda:

- Username (parcial, case-insensitive)
- Email (parcial, case-insensitive)
- Nombre completo (parcial, case-insensitive)

Filtros Disponibles:

- Estado: Activo, Inactivo, Bloqueado, Todos
- Area: Lista de areas disponibles
- Ordenar por: Username, Email, Ultima conexion, Fecha creacion
- Orden: Ascendente, Descendente

---

Sistema IACT - Analisis IVR
Version: 1.0.0 | Fecha documento: 2026-03-14 | Modelo RBAC: v7.0.0
