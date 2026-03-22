## TARJETA: users.export

Nombre para UI: Exportar Usuarios
Modulo: MOD_Users - Gestion de Usuarios
ID Caso de Uso: UC-013
Prioridad: MEDIA
Frecuencia: Semanal
Estado: Activo

### DESCRIPCION

Permite exportar la lista de usuarios del sistema a un archivo CSV. La exportacion incluye los datos basicos de cada usuario. Limitada a un maximo de 10,000 registros por operacion (CNST-010). El usuario puede aplicar los mismos filtros disponibles en users.view antes de exportar.

### PRECONDICIONES

- Usuario tiene sesion activa
- Usuario tiene funcion users.export asignada
- Sistema tiene usuarios disponibles para exportar

### FLUJO PRINCIPAL (10 PASOS)

1. Usuario navega a seccion "Exportar Usuarios"
2. Sistema muestra formulario con filtros opcionales
3. Usuario aplica filtros (estado, area, rango de fechas) si desea
4. Usuario selecciona formato de exportacion (CSV)
5. Usuario hace clic en "Exportar"
6. Sistema valida los filtros ingresados
7. Sistema cuenta usuarios que coinciden con filtros
8. Sistema valida que el conteo no supere 10,000 registros (CNST-010)
9. Sistema genera archivo CSV con los datos de usuarios
10. Sistema descarga el archivo al cliente

### FLUJOS ALTERNATIVOS

**A1. Demasiados registros (paso 8)**

- Sistema detecta que la consulta retornaria mas de 10,000 usuarios
- Sistema muestra error: "La exportacion supera el limite de 10,000 registros. Aplique filtros para reducir los resultados" (USR-012)
- Usuario permanece en formulario
- Caso de uso puede reintentar desde paso 3 con filtros mas restrictivos

**A2. Sin resultados (paso 7)**

- Sistema detecta 0 usuarios con los filtros aplicados
- Sistema muestra mensaje: "No hay usuarios para exportar con esos filtros" (INFO-014)
- Usuario puede limpiar filtros o cambiar criterios
- Caso de uso puede reintentar desde paso 3

**A3. Error al generar archivo (paso 9)**

- Sistema falla al generar el CSV (error de servidor)
- Sistema muestra error: "Error al generar el archivo. Intente nuevamente" (USR-013)
- Caso de uso termina con fallo

**A4. Usuario sin funcion users.export**

- Sistema detecta que usuario no tiene funcion
- Sistema muestra error 403: "No tiene permisos para exportar usuarios" (USR-001)
- Usuario es redirigido a pagina anterior
- Caso de uso termina

### POSTCONDICIONES

Exito:

- Archivo CSV descargado al cliente
- Registro de auditoria creado con la operacion de exportacion

Fallo:

- Sin archivo generado
- Usuario puede reintentar con filtros diferentes

### REGLAS DE NEGOCIO

- RN-044: Exportacion limitada a 10,000 registros (CNST-010)
- RN-045: El archivo CSV incluye: id, username, email, first_name, last_name, is_active, is_locked, area, date_joined, last_login, functions_count
- RN-046: NO se exportan datos sensibles (contrasena, tokens, pregunta de seguridad)
- RN-047: Nombre del archivo: usuarios_YYYY-MM-DD_HH-MM-SS.csv
- RN-048: Encoding del CSV: UTF-8 con BOM para compatibilidad con Excel
- RN-049: Usuario solo puede exportar usuarios de su area (si aplica filtro por objeto)

### RESTRICCIONES TECNICAS

- CNST-010: Exportacion maxima 10,000 registros por operacion
- CNST-017: Timeout de generacion de CSV: 30 segundos
- CNST-018: Separador CSV: coma (,), texto entre comillas dobles si contiene comas

### REGLAS SoD

Ninguna

### MENSAJES DEL SISTEMA

Errores:

- USR-001: "No tiene permisos para exportar usuarios" (sin funcion users.export)
- USR-012: "La exportacion supera el limite de 10,000 registros. Aplique filtros para reducir los resultados"
- USR-013: "Error al generar el archivo. Intente nuevamente"

Informativos:

- INFO-014: "No hay usuarios para exportar con esos filtros"
- INFO-015: "Generando archivo CSV con X usuarios..."
- INFO-016: "Exportacion completada: X usuarios exportados"

### IMPLEMENTACION TECNICA

**Exportar usuarios**

Endpoint: GET /api/v1/users/export

Query Parameters:
```
?format=csv
&status=active
&area=Comercial
&created_from=2025-01-01
&created_to=2026-01-01
&order_by=username
&order=asc
```

Response Exitosa (200 OK):

- Content-Type: text/csv; charset=utf-8
- Content-Disposition: attachment; filename="usuarios_2026-03-22_10-30-00.csv"
- Body: archivo CSV

Contenido del CSV:
```
id,username,email,first_name,last_name,is_active,is_locked,area,date_joined,last_login,functions_count
123,jperez,juan.perez@empresa.com,Juan,Perez,true,false,Comercial,2025-01-15T08:00:00Z,2026-03-15T10:30:00Z,8
124,mgarcia,maria.garcia@empresa.com,Maria,Garcia,true,false,Soporte,2025-02-20T09:00:00Z,2026-03-14T15:00:00Z,5
```

Response - Limite excedido (400 Bad Request):

```json
{
  "success": false,
  "error_code": "USR-012",
  "message": "La exportacion supera el limite de 10,000 registros. Aplique filtros para reducir los resultados",
  "total_records": 15423,
  "max_allowed": 10000
}
```

Response - Sin permisos (403 Forbidden):

```json
{
  "success": false,
  "error_code": "USR-001",
  "message": "No tiene permisos para exportar usuarios"
}
```

Codigos HTTP:

- 200 OK: Archivo CSV generado y descargado
- 400 Bad Request: Filtros invalidos o limite excedido
- 403 Forbidden: Sin funcion users.export
- 500 Internal Server Error: Error al generar archivo

### VALIDACIONES

Validacion de Filtros:

- status: valores permitidos: active, inactive, locked, all
- area: debe ser area valida del sistema
- created_from, created_to: fechas en formato YYYY-MM-DD
- created_from <= created_to (si ambos se proporcionan)

Validacion de Limite:

- COUNT(*) con los filtros aplicados
- Si COUNT > 10,000: rechazar y pedir filtros mas restrictivos
- Validacion previa a generacion del archivo

### AUDITORIA

Se registra en AuditLog:

- Accion: export_users
- Usuario: user_id (quien exporta)
- Timestamp: hora exacta
- IP Address: IP desde donde exporta
- Detalles: filtros aplicados, cantidad de registros exportados, nombre del archivo

Ejemplo de log:

```json
{
  "timestamp": "2026-03-22T10:30:00Z",
  "action": "export_users",
  "user_id": 123,
  "ip_address": "192.168.1.100",
  "user_agent": "Chrome/120.0",
  "result": "success",
  "details": {
    "filters": {"status": "active", "area": "Comercial"},
    "records_exported": 47,
    "filename": "usuarios_2026-03-22_10-30-00.csv",
    "format": "csv"
  }
}
```

### SEGURIDAD

Protecciones Implementadas:

- Datos sensibles NO incluidos en exportacion (contrasena, tokens)
- Limite de 10,000 registros previene extraccion masiva
- Resultados filtrados por area del usuario (si aplica)
- Todas las exportaciones auditadas con detalle de registros exportados
- Archivo generado en servidor y descargado de forma segura

Informacion NO Exportada:

- Contrasenas (ni en texto plano ni en hash)
- Tokens JWT o de refresco
- Preguntas de seguridad o respuestas
- Datos internos del sistema

### NOTAS IMPORTANTES

- El limite de 10,000 registros es por operacion (CNST-010)
- Si se necesita exportar mas, aplicar filtros por area, estado o fecha
- El archivo CSV usa encoding UTF-8 con BOM para compatibilidad con Microsoft Excel
- La exportacion respeta el filtro por objeto del usuario (solo exporta su area si aplica)
- Datos de contrasena NUNCA se incluyen en la exportacion

---

Sistema IACT - Analisis IVR
Version: 1.0.0 | Fecha documento: 2026-03-22 | Modelo RBAC: v7.0.0
