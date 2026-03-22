## TARJETA: audit.search

Nombre para UI: Buscar en Auditoria
Modulo: MOD_Audit - Auditoria y Compliance
ID Caso de Uso: UC-024
Prioridad: MEDIA
Frecuencia: Ocasional
Estado: Activo

### DESCRIPCION

Permite busqueda avanzada en los registros de auditoria SIN limite temporal (acceso al historico completo). Soporta busqueda en campos JSON de detalles de cada log. Maximo 10,000 resultados por consulta. Complementa audit.view que tiene limite de 90 dias. Esta funcion es incompatible con gestion de usuarios por SoD 2.

### PRECONDICIONES

- Usuario tiene sesion activa
- Usuario tiene funcion audit.search asignada
- El usuario NO tiene users.create, users.edit ni users.delete (SoD 2)

### FLUJO PRINCIPAL (10 PASOS)

1. Usuario navega a seccion "Buscar en Auditoria"
2. Sistema muestra formulario de busqueda avanzada
3. Usuario ingresa criterios de busqueda (texto libre, filtros, rango de fechas sin limite)
4. Usuario puede buscar dentro de los campos JSON de detalles
5. Usuario selecciona ordenamiento (timestamp, usuario, accion)
6. Usuario hace clic en "Buscar"
7. Sistema valida los criterios ingresados
8. Sistema ejecuta busqueda en historico completo de auditoria
9. Sistema muestra resultados paginados (maximo 10,000 registros)
10. Usuario puede exportar resultados (si tiene reports.export)

### FLUJOS ALTERNATIVOS

**A1. Sin criterios de busqueda (paso 7)**

- Sistema detecta que no se ingreso ningun criterio
- Sistema muestra error: "Ingrese al menos un criterio de busqueda" (AUD-003)
- Usuario permanece en formulario
- Caso de uso puede reintentar desde paso 3

**A2. Limite de 10,000 resultados alcanzado (paso 9)**

- La busqueda retorna mas de 10,000 registros
- Sistema muestra los primeros 10,000 y advierte: "Se muestran los primeros 10,000 resultados. Refine la busqueda para mayor precision" (INFO-038)
- Usuario puede refinar criterios para obtener resultados mas especificos

**A3. Sin resultados (paso 9)**

- No se encuentran registros que coincidan con los criterios
- Sistema muestra mensaje: "No se encontraron registros de auditoria con esos criterios" (INFO-039)
- Usuario puede limpiar filtros o cambiar criterios
- Caso de uso puede reintentar

**A4. Busqueda en JSON (paso 4)**

- Usuario ingresa texto para buscar dentro del campo details (JSON)
- Sistema ejecuta busqueda full-text o JSON path en los detalles de cada log
- Ejemplo: buscar todos los logs donde details contiene "plopez" o "Cola_Ventas"
- Sistema retorna registros donde el JSON de detalles contiene el texto buscado

**A5. Usuario sin funcion audit.search**

- Sistema detecta que usuario no tiene funcion
- Sistema muestra error 403: "No tiene permisos para buscar en auditoria" (AUD-002)
- Usuario es redirigido a pagina anterior
- Caso de uso termina

### POSTCONDICIONES

Exito:

- Resultados de busqueda mostrados (hasta 10,000 registros)
- Solo lectura: no se modifica ningun registro
- Si hay mas de 10,000: advertencia de truncamiento

Fallo:

- Sin resultados
- Usuario puede refinar criterios

### REGLAS DE NEGOCIO

- RN-109: Sin limite temporal: acceso al historico completo (desde el inicio del sistema)
- RN-110: Maximo 10,000 resultados por busqueda
- RN-111: Soporte de busqueda dentro de campos JSON de detalles
- RN-112: Logs son INMUTABLES: solo lectura
- RN-113: Logs se preservan minimo 7 anos (CNST-015)
- RN-114: Quien tiene audit.search NO puede tener users.create, users.edit ni users.delete (SoD 2)

### RESTRICCIONES TECNICAS

- CNST-015: Retencion minima 7 anos
- CNST-029: Consulta READ-ONLY
- CNST-031: Sin limite temporal (diferencia clave con audit.view)
- CNST-032: Maximo 10,000 resultados por busqueda
- CNST-033: Timeout de consulta: 60 segundos (puede ser lenta por historico completo)

### REGLAS SoD

- SoD 2 - user_audit_separation (Grupo AUDIT)
- INCOMPATIBLE con: users.create, users.edit, users.delete
- Razon: Quien gestiona usuarios NO debe auditar sus propias acciones

### MENSAJES DEL SISTEMA

Errores:

- AUD-002: "No tiene permisos para buscar en auditoria"
- AUD-003: "Ingrese al menos un criterio de busqueda"

Advertencias:

- WARN-020: "Se muestran los primeros 10,000 resultados. Refine la busqueda para mayor precision"

Informativos:

- INFO-038: "Busqueda completada en X segundos. X registros encontrados (mostrando primeros 10,000)"
- INFO-039: "No se encontraron registros de auditoria con esos criterios"

### IMPLEMENTACION TECNICA

**Buscar en auditoria**

Endpoint: GET /api/v1/audit/search

Query Parameters:
```
?q=plopez
&user_id=123
&username=jperez
&action=login_attempt
&result=failed
&ip_address=192.168.1.100
&date_from=2019-01-01
&date_to=2026-03-22
&details_contains=Cola_Ventas
&page=1
&page_size=50
&order_by=timestamp
&order=desc
```

Parametros especiales:
- q: Busqueda de texto libre en todos los campos principales
- details_contains: Busqueda dentro del campo JSON de detalles
- date_from y date_to: Opcionales (sin limite temporal si se omiten)

Response Exitosa (200 OK):

```json
{
  "success": true,
  "query": {
    "q": "plopez",
    "action": "login_attempt",
    "result": "failed",
    "date_from": null,
    "date_to": null,
    "historical_search": true
  },
  "logs": [
    {
      "id": 45678,
      "timestamp": "2025-06-15T08:23:00Z",
      "action": "login_attempt",
      "user_id": 150,
      "username": "plopez",
      "ip_address": "10.0.0.50",
      "user_agent": "Mozilla/5.0 Firefox/118.0",
      "result": "failed",
      "details": {
        "reason": "invalid_credentials",
        "failed_attempts": 2,
        "remaining_attempts": 3
      }
    },
    {
      "id": 45679,
      "timestamp": "2025-06-15T08:24:00Z",
      "action": "login_attempt",
      "user_id": 150,
      "username": "plopez",
      "ip_address": "10.0.0.50",
      "user_agent": "Mozilla/5.0 Firefox/118.0",
      "result": "account_locked",
      "details": {
        "reason": "automatic_lock_after_failed_attempts",
        "failed_attempts": 5,
        "locked_until": "2025-06-15T08:39:00Z"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_found": 23,
    "total_pages": 1,
    "truncated": false,
    "max_results": 10000
  },
  "performance": {
    "search_time_ms": 1250,
    "oldest_record_searched": "2025-01-01T00:00:00Z"
  }
}
```

Response - Sin criterios (400 Bad Request):

```json
{
  "success": false,
  "error_code": "AUD-003",
  "message": "Ingrese al menos un criterio de busqueda"
}
```

Response - Resultados truncados (200 OK con advertencia):

```json
{
  "success": true,
  "warning": "Se muestran los primeros 10,000 resultados. Refine la busqueda para mayor precision",
  "logs": [...],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_found": 10000,
    "total_pages": 200,
    "truncated": true,
    "actual_matches": "mas de 10,000"
  }
}
```

Response - Sin permisos (403 Forbidden):

```json
{
  "success": false,
  "error_code": "AUD-002",
  "message": "No tiene permisos para buscar en auditoria"
}
```

Codigos HTTP:

- 200 OK: Busqueda completada (incluso si no hay resultados)
- 400 Bad Request: Sin criterios de busqueda
- 403 Forbidden: Sin funcion audit.search
- 504 Gateway Timeout: Busqueda excede 60 segundos
- 500 Internal Server Error: Error del servidor

### VALIDACIONES

Validacion de Criterios:

- Al menos uno de: q, user_id, username, action, result, ip_address, date_from, date_to, details_contains
- q: Minimo 2 caracteres si se proporciona

Validacion de Fechas (opcionales):

- Si se proporcionan: formato YYYY-MM-DD
- Si date_from sin date_to: busca desde esa fecha hasta hoy
- Si date_to sin date_from: busca hasta esa fecha desde el inicio del historico

Validacion de Filtros:

- action: Debe ser accion valida del sistema (si se proporciona)
- result: Valores permitidos: success, failed, error, pending (si se proporciona)
- page_size: 1-100 registros por pagina

### AUDITORIA

Se registra en AuditLog:

- Accion: search_audit
- Usuario: user_id (quien busca en auditoria)
- Timestamp: hora exacta
- Detalles: criterios de busqueda, cantidad de resultados, tiempo de busqueda

Ejemplo de log:

```json
{
  "timestamp": "2026-03-22T10:30:00Z",
  "action": "search_audit",
  "user_id": 200,
  "ip_address": "192.168.1.101",
  "user_agent": "Chrome/120.0",
  "result": "success",
  "details": {
    "search_criteria": {
      "q": "plopez",
      "action": "login_attempt",
      "result": "failed",
      "historical": true
    },
    "records_found": 23,
    "truncated": false,
    "search_time_ms": 1250
  }
}
```

### SEGURIDAD

Protecciones Implementadas:

- Registros son READ-ONLY: no se pueden modificar via esta funcion
- Limite de 10,000 resultados previene extraccion masiva de historico
- Timeout 60 segundos protege la base de datos de consultas excesivas
- Consulta de auditoria tambien auditada (meta-auditoria)
- SoD 2: quien gestiona usuarios no puede auditar sus propias acciones

Diferencia con audit.view:

- audit.view: Limite 90 dias, consulta rapida (timeout 30s), para uso cotidiano
- audit.search: Sin limite temporal, busqueda en JSON, timeout 60s, para investigacion

### NOTAS IMPORTANTES

- Sin limite temporal: puede buscar en TODA la historia del sistema
- Limite de 10,000 resultados: si se excede, se muestran los mas recientes con advertencia
- Busqueda en JSON de detalles (details_contains): util para investigaciones especificas
- Puede ser mas lenta que audit.view por el historico completo
- Quien tiene audit.search NO puede tener users.create, users.edit ni users.delete (SoD 2)
- Complementa audit.view: usar view para consultas cotidianas, search para investigaciones

---

Sistema IACT - Analisis IVR
Version: 1.0.0 | Fecha documento: 2026-03-22 | Modelo RBAC: v7.0.0
