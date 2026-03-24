## TARJETA: audit.view

Nombre para UI: Ver Auditoria
Modulo: MOD_Audit - Auditoria y Compliance
ID Caso de Uso: UC-023
Prioridad: ALTA
Frecuencia: Semanal
Estado: Activo

### DESCRIPCION

Permite consultar registros del log de auditoria del sistema. Rango maximo de consulta: 90 dias. Los logs son de solo lectura: no se pueden modificar ni eliminar mediante esta funcion (la eliminacion requiere audit.delete). Los logs se preservan minimo 7 anos (CNST-015). Esta funcion es incompatible con gestion de usuarios por SoD 2.

### PRECONDICIONES

- Usuario tiene sesion activa
- Usuario tiene funcion audit.view asignada
- El usuario NO tiene users.create, users.edit ni users.delete (SoD 2)

### FLUJO PRINCIPAL (9 PASOS)

1. Usuario navega a seccion "Auditoria"
2. Sistema muestra formulario de consulta con filtros basicos
3. Usuario selecciona rango de fechas (maximo 90 dias)
4. Usuario selecciona filtros adicionales (usuario, accion, resultado)
5. Usuario hace clic en "Ver Registros"
6. Sistema valida que el rango no exceda 90 dias
7. Sistema ejecuta consulta en log de auditoria (READ-ONLY)
8. Sistema muestra lista paginada de registros de auditoria
9. Usuario puede ver el detalle de cada registro individual

### FLUJOS ALTERNATIVOS

**A1. Rango mayor a 90 dias (paso 6)**

- Sistema detecta que el rango excede 90 dias
- Sistema muestra error: "El rango maximo para ver auditoria es 90 dias. Use audit.search para busqueda historica sin limite" (AUD-001)
- Caso de uso puede reintentar desde paso 3
- Nota: Para busqueda sin limite temporal usar audit.search

**A2. Sin resultados (paso 8)**

- Sistema no encuentra registros con los filtros aplicados
- Sistema muestra mensaje: "No hay registros de auditoria para los criterios seleccionados" (INFO-035)
- Usuario puede limpiar filtros o cambiar el rango
- Caso de uso puede reintentar

**A3. Ver detalle de registro (paso 9)**

- Usuario hace clic en un registro especifico
- Sistema muestra todos los campos del log: timestamp, accion, usuario, IP, user_agent, resultado, detalles JSON
- Usuario puede copiar el JSON de detalles para analisis

**A4. Usuario sin funcion audit.view**

- Sistema detecta que usuario no tiene funcion
- Sistema muestra error 403: "No tiene permisos para ver auditoria" (AUD-002)
- Usuario es redirigido a pagina anterior
- Caso de uso termina

**A5. Exportar auditoria**

- Usuario hace clic en "Exportar"
- Requiere reports.export adicionalmente
- Si NO tiene: muestra error (RPT-004)
- Si SI tiene: genera CSV con los registros de auditoria del filtro actual

### POSTCONDICIONES

Exito:

- Registros de auditoria mostrados
- Solo lectura: no se modifica ningun registro

Fallo:

- Sin registros mostrados
- Si no tiene permisos, no accede a la auditoria

### REGLAS DE NEGOCIO

- RN-104: Rango maximo 90 dias para consulta
- RN-105: Logs son INMUTABLES: solo lectura
- RN-106: Logs se preservan minimo 7 anos (CNST-015)
- RN-107: Resultados paginados de 50 registros por pagina
- RN-108: Quien tiene audit.view NO puede tener users.create, users.edit ni users.delete (SoD 2)

### RESTRICCIONES TECNICAS

- CNST-015: Retencion minima 7 anos
- CNST-029: Consulta READ-ONLY: no permite modificar registros
- CNST-030: Rango maximo 90 dias para audit.view (sin limite en audit.search)

### REGLAS SoD

- SoD 2 - user_audit_separation (Grupo AUDIT)
- INCOMPATIBLE con: users.create, users.edit, users.delete
- Razon: Quien gestiona usuarios NO debe auditar sus propias acciones

### MENSAJES DEL SISTEMA

Errores:

- AUD-001: "El rango maximo para ver auditoria es 90 dias. Use audit.search para busqueda historica sin limite"
- AUD-002: "No tiene permisos para ver auditoria"
- RPT-004: "Requiere funcion reports.export para exportar"

Informativos:

- INFO-035: "No hay registros de auditoria para los criterios seleccionados"
- INFO-036: "Mostrando X de Y registros"
- INFO-037: "Los registros de auditoria son de solo lectura"

### IMPLEMENTACION TECNICA

**Consultar registros de auditoria**

Endpoint: GET /api/v1/audit/logs

Query Parameters:
```
?date_from=2026-03-01
&date_to=2026-03-22
&user_id=123
&username=jperez
&action=login_attempt
&result=success
&ip_address=192.168.1.100
&page=1
&page_size=50
&order_by=timestamp
&order=desc
```

Acciones disponibles para filtro:
- login_attempt, logout, create_user, edit_user, delete_user
- reset_password, lock_user, unlock_user
- assign_functions, revoke_functions
- view_users, search_users, export_users
- view_basic_report, view_advanced_report, export_report
- request_data_modification, approve_modification, reject_modification
- schedule_report, view_audit, search_audit, delete_audit_logs

Response Exitosa (200 OK):

```json
{
  "success": true,
  "logs": [
    {
      "id": 98765,
      "timestamp": "2026-03-22T10:30:00Z",
      "action": "login_attempt",
      "user_id": 123,
      "username": "jperez",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0 Chrome/120.0",
      "result": "success",
      "details": {
        "login_method": "username",
        "session_id": "abc123xyz789"
      }
    },
    {
      "id": 98766,
      "timestamp": "2026-03-22T09:15:00Z",
      "action": "view_users",
      "user_id": 123,
      "username": "jperez",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0 Chrome/120.0",
      "result": "success",
      "details": {
        "filters": {"status": "active"},
        "results_count": 47
      }
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_records": 1253,
    "total_pages": 26
  },
  "query": {
    "date_from": "2026-03-01",
    "date_to": "2026-03-22",
    "days_range": 22
  }
}
```

Response - Rango excedido (400 Bad Request):

```json
{
  "success": false,
  "error_code": "AUD-001",
  "message": "El rango maximo para ver auditoria es 90 dias. Use audit.search para busqueda historica sin limite",
  "requested_days": 120,
  "max_days": 90
}
```

Response - Sin permisos (403 Forbidden):

```json
{
  "success": false,
  "error_code": "AUD-002",
  "message": "No tiene permisos para ver auditoria"
}
```

Codigos HTTP:

- 200 OK: Registros de auditoria cargados
- 400 Bad Request: Rango excedido, filtros invalidos
- 403 Forbidden: Sin funcion audit.view
- 500 Internal Server Error: Error del servidor

### VALIDACIONES

Validacion de Rango:

- date_from y date_to: Fechas validas formato YYYY-MM-DD
- date_from <= date_to
- (date_to - date_from) <= 90 dias
- date_to: No puede ser fecha futura (se permite dia actual)

Validacion de Filtros:

- action: Debe ser una accion valida del sistema
- result: Valores permitidos: success, failed, error, pending
- page: Entero positivo, minimo 1
- page_size: 1-100 registros por pagina

### AUDITORIA

Se registra en AuditLog:

- Accion: view_audit
- Usuario: user_id (quien consulta la auditoria)
- Timestamp: hora exacta
- Detalles: filtros aplicados, cantidad de registros retornados

Ejemplo de log:

```json
{
  "timestamp": "2026-03-22T10:30:00Z",
  "action": "view_audit",
  "user_id": 200,
  "ip_address": "192.168.1.101",
  "user_agent": "Chrome/120.0",
  "result": "success",
  "details": {
    "filters": {
      "date_from": "2026-03-01",
      "date_to": "2026-03-22",
      "user_id": 123,
      "action": "login_attempt"
    },
    "records_returned": 50,
    "total_records": 1253,
    "page": 1
  }
}
```

### SEGURIDAD

Protecciones Implementadas:

- Registros son READ-ONLY: no se pueden modificar via esta funcion
- Rango maximo 90 dias previene extraccion masiva de historico
- Consulta de la propia auditoria tambien auditada (meta-auditoria)
- SoD 2: quien gestiona usuarios no puede ver auditoria de esas acciones

Regla SoD 2 (user_audit_separation):

- Objetivo: Quien crea, edita o elimina usuarios NO puede auditar sus propias acciones
- Garantiza independencia del auditor respecto del administrador de usuarios
- Administradores de usuarios (users.create/edit/delete) requieren auditor externo

### NOTAS IMPORTANTES

- Limite de 90 dias: para consultas historicas sin limite usar audit.search
- Los registros de auditoria son INMUTABLES (solo lectura)
- Para eliminar registros (casos excepcionales legales): usar audit.delete
- Quien tiene audit.view NO puede tener users.create, users.edit ni users.delete (SoD 2)
- La propia consulta de auditoria queda registrada en el log (meta-auditoria)
- Logs se preservan minimo 7 anos por compliance (CNST-015)

---

Sistema IACT - Analisis IVR
Version: 1.0.0 | Fecha documento: 2026-03-22 | Modelo RBAC: v7.0.0
