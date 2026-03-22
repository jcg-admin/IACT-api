## TARJETA: reports.schedule

Nombre para UI: Programar Reportes
Modulo: MOD_Reports - Reportes y Analisis
ID Caso de Uso: UC-022
Prioridad: MEDIA
Frecuencia: Ocasional
Estado: Activo

### DESCRIPCION

Permite programar la generacion automatica de reportes IVR con frecuencia diaria, semanal o mensual. Los reportes generados se entregan por mensaje interno a los destinatarios especificados. Maximo 10 reportes activos por usuario simultaneamente. No requiere presencia del usuario para ejecutarse.

### PRECONDICIONES

- Usuario tiene sesion activa
- Usuario tiene funcion reports.schedule asignada
- Usuario tiene reports.view_basic o reports.view_advanced (para el tipo de reporte a programar)
- Usuario tiene menos de 10 reportes activos programados

### FLUJO PRINCIPAL (12 PASOS)

1. Usuario navega a seccion "Programar Reportes"
2. Sistema muestra lista de reportes actualmente programados por el usuario
3. Usuario hace clic en "Nuevo Reporte Programado"
4. Sistema muestra formulario de configuracion
5. Usuario selecciona tipo de reporte y configuracion
6. Usuario selecciona frecuencia: diaria, semanal o mensual
7. Usuario selecciona rango relativo de datos: last_7_days, last_30_days, last_week, last_month
8. Usuario agrega destinatarios (usernames del sistema)
9. Usuario da nombre descriptivo al reporte programado
10. Usuario hace clic en "Programar Reporte"
11. Sistema valida la configuracion
12. Sistema activa el reporte programado y muestra confirmacion con proxima ejecucion

### FLUJOS ALTERNATIVOS

**A1. Limite de 10 reportes activos alcanzado (paso 3)**

- Sistema detecta que el usuario ya tiene 10 reportes activos
- Sistema muestra error: "Ha alcanzado el limite de 10 reportes programados activos. Desactive alguno para crear uno nuevo" (RPT-019)
- Sistema muestra lista de reportes activos para que el usuario gestione
- Caso de uso termina

**A2. Destinatario no existe (paso 11)**

- Sistema detecta que uno o mas usernames de destinatarios no existen
- Sistema muestra error: "El usuario '{username}' no existe en el sistema" (RPT-020)
- Usuario permanece en formulario
- Caso de uso puede reintentar desde paso 8

**A3. Sin destinatarios (paso 11)**

- Sistema detecta que no hay destinatarios especificados
- Sistema muestra error: "Especifique al menos un destinatario" (RPT-021)
- Usuario permanece en formulario

**A4. Desactivar reporte programado**

- Usuario selecciona un reporte activo de su lista
- Usuario hace clic en "Desactivar"
- Sistema cambia estado a inactivo
- Reporte ya no se ejecuta automaticamente
- Historial de ejecuciones previas se conserva

**A5. Editar reporte programado**

- Usuario selecciona un reporte activo
- Sistema muestra configuracion actual editable
- Usuario modifica frecuencia, destinatarios o nombre
- Sistema guarda cambios y recalcula proxima ejecucion

**A6. Usuario sin funcion reports.schedule**

- Sistema detecta que usuario no tiene funcion
- Sistema muestra error 403: "No tiene permisos para programar reportes" (RPT-005)
- Usuario es redirigido a pagina anterior
- Caso de uso termina

### POSTCONDICIONES

Exito:

- Reporte programado creado y activado
- Proxima fecha/hora de ejecucion calculada y mostrada
- Los destinatarios recibiran el reporte automaticamente

Fallo:

- Sin reporte programado creado
- Usuario puede corregir y reintentar

### REGLAS DE NEGOCIO

- RN-097: Maximo 10 reportes activos por usuario
- RN-098: Frecuencias disponibles: daily, weekly, monthly
- RN-099: Rangos relativos disponibles: last_7_days, last_30_days, last_week, last_month
- RN-100: Los reportes se generan y entregan a destinatarios por mensaje interno
- RN-101: El usuario puede desactivar cualquier reporte programado propio
- RN-102: Los reportes programados se ejecutan con los permisos del usuario que los creo
- RN-103: Si el usuario que creo el reporte pierde permisos, los reportes se desactivan automaticamente

### RESTRICCIONES TECNICAS

- CNST-027: Maximo 10 reportes activos por usuario
- CNST-028: Entrega por mensaje interno (NO por email, cumple CNST-001)
- CNST-003: Reportes programados usan acceso READ-ONLY a base IVR

### REGLAS SoD

Ninguna

### MENSAJES DEL SISTEMA

Errores:

- RPT-005: "No tiene permisos para programar reportes"
- RPT-019: "Ha alcanzado el limite de 10 reportes programados activos"
- RPT-020: "El usuario '{username}' no existe en el sistema"
- RPT-021: "Especifique al menos un destinatario"

Confirmacion:

- OK-022: "Reporte programado activado. Proxima ejecucion: {fecha_hora}"

Informativos:

- INFO-033: "Reportes activos: X/10"
- INFO-034: "El reporte se entregara por mensaje interno a los destinatarios"

### IMPLEMENTACION TECNICA

**Crear reporte programado**

Endpoint: POST /api/v1/reports/schedule

Request:

```json
{
  "name": "Resumen Semanal Cola Ventas",
  "report_type": "calls_by_queue",
  "frequency": "weekly",
  "data_range": "last_7_days",
  "filters": {
    "queue": "Cola_Ventas"
  },
  "recipients": ["jperez", "mgarcia", "supervisor_ventas"],
  "active": true
}
```

Response Exitosa (201 Created):

```json
{
  "success": true,
  "message": "Reporte programado activado",
  "scheduled_report": {
    "id": "SCH-2026-03-22-001",
    "name": "Resumen Semanal Cola Ventas",
    "report_type": "calls_by_queue",
    "frequency": "weekly",
    "data_range": "last_7_days",
    "filters": {"queue": "Cola_Ventas"},
    "recipients": ["jperez", "mgarcia", "supervisor_ventas"],
    "status": "active",
    "created_by": "jperez",
    "created_at": "2026-03-22T10:30:00Z",
    "next_execution": "2026-03-29T06:00:00Z",
    "total_active_reports": 3
  }
}
```

Response - Limite alcanzado (400 Bad Request):

```json
{
  "success": false,
  "error_code": "RPT-019",
  "message": "Ha alcanzado el limite de 10 reportes programados activos",
  "current_active": 10,
  "max_allowed": 10,
  "suggestion": "Desactive algun reporte activo para crear uno nuevo"
}
```

**Listar reportes programados**

Endpoint: GET /api/v1/reports/schedule

Response:

```json
{
  "success": true,
  "scheduled_reports": [
    {
      "id": "SCH-2026-03-22-001",
      "name": "Resumen Semanal Cola Ventas",
      "frequency": "weekly",
      "data_range": "last_7_days",
      "status": "active",
      "last_executed": "2026-03-22T06:00:00Z",
      "next_execution": "2026-03-29T06:00:00Z",
      "recipients_count": 3
    }
  ],
  "summary": {
    "active": 3,
    "inactive": 1,
    "total": 4,
    "max_allowed": 10
  }
}
```

**Desactivar reporte programado**

Endpoint: PATCH /api/v1/reports/schedule/{schedule_id}

Request:

```json
{
  "active": false
}
```

Codigos HTTP:

- 201 Created: Reporte programado creado exitosamente
- 200 OK: Reporte actualizado o listado exitosamente
- 400 Bad Request: Limite alcanzado, destinatario invalido
- 403 Forbidden: Sin funcion reports.schedule
- 404 Not Found: Reporte programado no encontrado
- 500 Internal Server Error: Error del servidor

### VALIDACIONES

Validacion de Frecuencia:

- frequency: Valores permitidos: daily, weekly, monthly

Validacion de Rango:

- data_range: Valores permitidos: last_7_days, last_30_days, last_week, last_month

Validacion de Destinatarios:

- recipients: Lista no vacia
- Cada username debe existir en el sistema
- Se recomienda incluir al menos al creador del reporte

Validacion de Limite:

- Verificar que el usuario tiene menos de 10 reportes activos antes de crear

### AUDITORIA

Se registra en AuditLog:

- Accion: schedule_report, update_schedule, deactivate_schedule
- Usuario: user_id (quien programa)
- Timestamp: hora exacta
- Detalles: configuracion del reporte, frecuencia, destinatarios

Ejemplo de log:

```json
{
  "timestamp": "2026-03-22T10:30:00Z",
  "action": "schedule_report",
  "user_id": 123,
  "ip_address": "192.168.1.100",
  "user_agent": "Chrome/120.0",
  "result": "success",
  "details": {
    "schedule_id": "SCH-2026-03-22-001",
    "report_type": "calls_by_queue",
    "frequency": "weekly",
    "data_range": "last_7_days",
    "recipients_count": 3,
    "next_execution": "2026-03-29T06:00:00Z"
  }
}
```

### SEGURIDAD

Protecciones Implementadas:

- Maximo 10 reportes activos previene sobrecarga del sistema
- Los reportes usan permisos del usuario creador (READ-ONLY en IVR)
- Si usuario pierde permisos, reportes se desactivan automaticamente
- Entrega por mensaje interno (no expone datos fuera del sistema)
- Todas las programaciones auditadas

Nota sobre CNST-001:

- Los reportes NO se envian por email (CNST-001: sin comunicaciones externas)
- La entrega es exclusivamente por mensaje interno del sistema IACT

### NOTAS IMPORTANTES

- Maximo 10 reportes activos simultaneamente por usuario
- Los reportes se ejecutan automaticamente sin presencia del usuario
- Entrega exclusivamente por mensaje interno (NUNCA por email)
- Si el usuario que creo el reporte pierde las funciones necesarias, los reportes se desactivan
- Rangos relativos (last_7_days, etc.) calculados al momento de ejecucion, no al momento de programacion
- Los reportes programados respetan el filtro por objeto del usuario creador

---

Sistema IACT - Analisis IVR
Version: 1.0.0 | Fecha documento: 2026-03-22 | Modelo RBAC: v7.0.0
