## TARJETA: users.search

Nombre para UI: Buscar Usuarios
Modulo: MOD_Users - Gestion de Usuarios
ID Caso de Uso: UC-012
Prioridad: MEDIA
Frecuencia: Diaria
Estado: Activo

### DESCRIPCION

Permite buscar usuarios con criterios avanzados: username, email, nombre completo, area, estado de cuenta y rango de fechas de creacion o ultimo acceso. Complementa a users.view con capacidades de busqueda mas especificas. Retorna lista paginada de usuarios que coinciden con los criterios.

### PRECONDICIONES

- Usuario tiene sesion activa
- Usuario tiene funcion users.search asignada
- (O bien tiene users.view, ya que users.view incluye busqueda basica)

### FLUJO PRINCIPAL (10 PASOS)

1. Usuario navega a seccion "Buscar Usuarios"
2. Sistema muestra formulario de busqueda avanzada
3. Usuario ingresa criterios de busqueda (uno o mas campos)
4. Usuario selecciona filtros adicionales (estado, area, rango de fechas)
5. Usuario hace clic en "Buscar"
6. Sistema valida los criterios ingresados
7. Sistema ejecuta busqueda en base de datos
8. Sistema aplica filtros por objeto segun area del usuario (si aplica)
9. Sistema muestra lista paginada de resultados
10. Usuario puede ordenar, paginar o refinar resultados

### FLUJOS ALTERNATIVOS

**A1. Sin resultados (paso 9)**

- Sistema no encuentra usuarios con los criterios ingresados
- Sistema muestra mensaje: "No se encontraron usuarios con esos criterios" (INFO-011)
- Usuario puede limpiar filtros o cambiar criterios de busqueda
- Caso de uso puede reintentar desde paso 3

**A2. Criterio de busqueda muy corto (paso 6)**

- Sistema detecta texto de busqueda con menos de 2 caracteres
- Sistema muestra error: "Ingrese al menos 2 caracteres para buscar" (USR-010)
- Usuario permanece en formulario
- Caso de uso puede reintentar desde paso 3

**A3. Rango de fechas invalido (paso 6)**

- Sistema detecta fecha_inicio mayor que fecha_fin
- Sistema muestra error: "La fecha de inicio debe ser anterior a la fecha de fin" (USR-011)
- Usuario permanece en formulario
- Caso de uso puede reintentar desde paso 4

**A4. Usuario sin funcion users.search**

- Sistema detecta que usuario no tiene funcion
- Sistema muestra error 403: "No tiene permisos para buscar usuarios" (USR-001)
- Usuario es redirigido a pagina anterior
- Caso de uso termina

**A5. Exportar resultados (desde paso 9)**

- Usuario hace clic en "Exportar resultados"
- Sistema verifica si usuario tiene users.export
- Si NO tiene: muestra error "Requiere funcion users.export" (USR-002)
- Si SI tiene: genera archivo CSV con los resultados actuales

### POSTCONDICIONES

Exito:

- Lista de usuarios que coinciden con criterios mostrada
- Filtros aplicados correctamente
- Paginacion disponible

Fallo:

- Si no tiene permisos, no accede a la busqueda
- Si criterios invalidos, usuario puede corregir

### REGLAS DE NEGOCIO

- RN-037: Busqueda requiere al menos un criterio (texto o filtro)
- RN-038: Texto minimo 2 caracteres para busqueda por username/email/nombre
- RN-039: Busqueda de texto es case-insensitive
- RN-040: Rango de fechas: fecha_inicio <= fecha_fin
- RN-041: Resultados paginados de 25 usuarios por pagina
- RN-042: Usuario solo ve usuarios de su area (si aplica filtro por objeto)
- RN-043: Maximo 500 resultados por busqueda (paginados)

### RESTRICCIONES TECNICAS

- CNST-011: Username alfanumerico, 3-30 caracteres
- CNST-012: Email formato valido
- CNST-016: Busqueda con timeout de 10 segundos

### REGLAS SoD

Ninguna

### MENSAJES DEL SISTEMA

Errores:

- USR-001: "No tiene permisos para buscar usuarios" (sin funcion users.search)
- USR-002: "Requiere funcion users.export para exportar" (sin funcion de exportacion)
- USR-010: "Ingrese al menos 2 caracteres para buscar" (texto muy corto)
- USR-011: "La fecha de inicio debe ser anterior a la fecha de fin" (rango invalido)

Informativos:

- INFO-011: "No se encontraron usuarios con esos criterios"
- INFO-012: "Mostrando X de Y resultados"
- INFO-013: "Busqueda completada en X ms"

### IMPLEMENTACION TECNICA

**Buscar usuarios**

Endpoint: GET /api/v1/users/search

Query Parameters:
```
?q=juan
&username=juan.perez
&email=juan@empresa.com
&first_name=Juan
&last_name=Perez
&area=Comercial
&status=active
&created_from=2025-01-01
&created_to=2026-01-01
&last_login_from=2026-01-01
&last_login_to=2026-03-22
&page=1
&page_size=25
&order_by=username
&order=asc
```

Response Exitosa (200 OK):

```json
{
  "success": true,
  "query": {
    "q": "juan",
    "status": "active",
    "area": "Comercial"
  },
  "users": [
    {
      "id": 123,
      "username": "jperez",
      "email": "juan.perez@empresa.com",
      "first_name": "Juan",
      "last_name": "Perez",
      "is_active": true,
      "is_locked": false,
      "area": "Comercial",
      "last_login": "2026-03-15T10:30:00Z",
      "date_joined": "2025-01-15T08:00:00Z",
      "functions_count": 8
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 25,
    "total_results": 3,
    "total_pages": 1
  }
}
```

Response - Sin resultados (200 OK):

```json
{
  "success": true,
  "query": {
    "q": "xyz_no_existe"
  },
  "users": [],
  "pagination": {
    "page": 1,
    "page_size": 25,
    "total_results": 0,
    "total_pages": 0
  },
  "message": "No se encontraron usuarios con esos criterios"
}
```

Response - Sin permisos (403 Forbidden):

```json
{
  "success": false,
  "error_code": "USR-001",
  "message": "No tiene permisos para buscar usuarios"
}
```

Response - Criterio invalido (400 Bad Request):

```json
{
  "success": false,
  "error_code": "USR-010",
  "message": "Ingrese al menos 2 caracteres para buscar",
  "field": "q"
}
```

Codigos HTTP:

- 200 OK: Busqueda exitosa (incluso si no hay resultados)
- 400 Bad Request: Criterios invalidos
- 403 Forbidden: Sin funcion users.search
- 500 Internal Server Error: Error del servidor

### VALIDACIONES

Validacion de Texto:

- q: Minimo 2 caracteres si se proporciona
- Busqueda parcial (LIKE %texto%)
- Case-insensitive
- Se busca en: username, email, first_name, last_name

Validacion de Filtros:

- status: valores permitidos: active, inactive, locked, all
- area: debe ser area valida del sistema
- order_by: valores permitidos: username, email, last_login, date_joined
- page: entero positivo, minimo 1
- page_size: entero positivo, maximo 100

Validacion de Fechas:

- Formato ISO 8601: YYYY-MM-DD
- created_from <= created_to (si ambos se proporcionan)
- last_login_from <= last_login_to (si ambos se proporcionan)
- Fechas no pueden ser futuras

### AUDITORIA

Se registra en AuditLog:

- Accion: search_users
- Usuario: user_id (quien busca)
- Timestamp: hora exacta
- IP Address: IP desde donde busca
- Detalles: criterios de busqueda, cantidad de resultados

Ejemplo de log:

```json
{
  "timestamp": "2026-03-15T10:30:00Z",
  "action": "search_users",
  "user_id": 123,
  "ip_address": "192.168.1.100",
  "user_agent": "Chrome/120.0",
  "result": "success",
  "details": {
    "query": {"q": "juan", "status": "active", "area": "Comercial"},
    "results_count": 3,
    "page": 1
  }
}
```

### SEGURIDAD

Protecciones Implementadas:

- Resultados filtrados por area del usuario (si aplica)
- Criterios minimos evitan busquedas excesivamente amplias
- Resultados limitados a 500 por consulta
- Todas las busquedas auditadas
- No expone datos sensibles (contrasena, tokens)

### NOTAS IMPORTANTES

- users.search complementa users.view con busqueda avanzada por fechas y criterios multiples
- users.view ya incluye busqueda basica por texto; users.search agrega busqueda por rangos de fecha
- El parametro q busca en username, email, first_name y last_name simultáneamente
- Los resultados respetan el filtro por objeto del usuario que busca

---

Sistema IACT - Analisis IVR
Version: 1.0.0 | Fecha documento: 2026-03-22 | Modelo RBAC: v7.0.0
