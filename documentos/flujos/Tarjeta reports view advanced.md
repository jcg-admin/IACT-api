## TARJETA: reports.view_advanced

Nombre para UI: Ver Reportes Avanzados
Modulo: MOD_Reports - Reportes y Analisis
ID Caso de Uso: UC-018
Prioridad: ALTA
Frecuencia: Semanal
Estado: Activo

### DESCRIPCION

Permite consultar reportes avanzados del sistema IVR con datos detallados por llamada individual. Sin limite de rango de fechas. Incluye capacidad de drill-down para analisis profundo. Timeout extendido de 60 segundos. Acceso READ-ONLY a la base IVR (CNST-003). Requiere reports.view_basic como prerequisito funcional implicito (es una extension avanzada).

### PRECONDICIONES

- Usuario tiene sesion activa
- Usuario tiene funcion reports.view_advanced asignada
- Base de datos IVR disponible (READ-ONLY)

### FLUJO PRINCIPAL (11 PASOS)

1. Usuario navega a seccion "Reportes" y selecciona "Reportes Avanzados"
2. Sistema muestra catalogo de tipos de reportes avanzados disponibles
3. Usuario selecciona el tipo de reporte
4. Usuario selecciona rango de fechas (sin limite)
5. Usuario selecciona filtros avanzados (cola, agente, IVR option, resultado)
6. Usuario configura agrupacion y nivel de detalle
7. Usuario hace clic en "Ver Reporte"
8. Sistema valida parametros
9. Sistema ejecuta consulta READ-ONLY en base IVR (timeout 60 seg)
10. Sistema muestra reporte con datos por llamada individual y drill-down disponible
11. Usuario puede navegar por el drill-down, cambiar filtros o exportar

### FLUJOS ALTERNATIVOS

**A1. Timeout de consulta (paso 9)**

- Consulta excede 60 segundos sin respuesta
- Sistema cancela la consulta
- Sistema muestra error: "La consulta tardo demasiado. Reduzca el rango de fechas, aplique mas filtros o use reportes basicos" (RPT-006)
- Caso de uso puede reintentar desde paso 4

**A2. Sin datos para el periodo (paso 10)**

- Base IVR no tiene registros para el rango y filtros seleccionados
- Sistema muestra mensaje: "No hay datos para el periodo y filtros seleccionados" (INFO-024)
- Se muestra reporte vacio con estructura correcta
- Caso de uso termina exitosamente

**A3. Base IVR no disponible (paso 9)**

- Sistema no puede conectar a base IVR
- Sistema muestra error: "La base de datos IVR no esta disponible. Intente mas tarde" (RPT-003)
- Caso de uso termina

**A4. Resultado excesivo sin filtros (paso 9)**

- Sistema detecta que la consulta retornaria mas de 100,000 registros
- Sistema muestra advertencia: "La consulta retornaria demasiados registros. Aplique filtros adicionales" (RPT-007)
- Sistema puede truncar a 100,000 o rechazar la consulta segun configuracion
- Caso de uso puede reintentar desde paso 5

**A5. Drill-down (paso 11)**

- Usuario hace clic en un punto del reporte para ver detalle
- Sistema carga datos de nivel inferior (por llamada individual)
- Sistema muestra detalle especifico del elemento seleccionado
- Usuario puede continuar navegando el drill-down o volver al nivel superior

**A6. Exportar reporte (paso 11)**

- Usuario hace clic en "Exportar"
- Sistema verifica si usuario tiene reports.export
- Si NO tiene: muestra error "Requiere funcion reports.export" (RPT-004)
- Si SI tiene: genera archivo con datos del reporte (limite 10,000 registros)

**A7. Usuario sin funcion reports.view_advanced**

- Sistema detecta que usuario no tiene funcion
- Sistema muestra error 403: "No tiene permisos para ver reportes avanzados" (RPT-008)
- Usuario es redirigido a pagina de reportes basicos (si tiene reports.view_basic)
- Caso de uso termina

### POSTCONDICIONES

Exito:

- Reporte avanzado mostrado con datos detallados
- Drill-down disponible para el usuario
- Datos por llamada individual visibles

Fallo:

- Sin datos mostrados
- Usuario puede reintentar con parametros diferentes o usar reportes basicos

### REGLAS DE NEGOCIO

- RN-072: Sin limite de rango de fechas (a diferencia de reports.view_basic)
- RN-073: Datos por llamada individual (no solo agregados)
- RN-074: Drill-down disponible hasta nivel de llamada individual
- RN-075: Timeout 60 segundos (doble que reportes basicos)
- RN-076: Base IVR es READ-ONLY (nunca INSERT/UPDATE/DELETE)
- RN-077: Limite de 100,000 registros en resultados (con advertencia)

### RESTRICCIONES TECNICAS

- CNST-003: Base IVR es READ-ONLY (solo SELECT en MariaDB IVR)
- CNST-022: Timeout 60 segundos para reportes avanzados
- CNST-023: Sin limite de rango de fechas pero con limite de 100,000 resultados

### REGLAS SoD

Ninguna

### MENSAJES DEL SISTEMA

Errores:

- RPT-003: "La base de datos IVR no esta disponible. Intente mas tarde"
- RPT-004: "Requiere funcion reports.export para exportar"
- RPT-006: "La consulta tardo demasiado. Reduzca el rango de fechas, aplique mas filtros o use reportes basicos"
- RPT-007: "La consulta retornaria demasiados registros. Aplique filtros adicionales"
- RPT-008: "No tiene permisos para ver reportes avanzados"

Informativos:

- INFO-024: "No hay datos para el periodo y filtros seleccionados"
- INFO-025: "Cargando reporte avanzado..."
- INFO-026: "Reporte generado en X segundos. Mostrando X registros de Y totales"

### IMPLEMENTACION TECNICA

**Ver reporte avanzado**

Endpoint: GET /api/v1/reports/advanced/{report_type}

Tipos de reportes disponibles:
- call_detail: Detalle por llamada individual
- agent_performance: Desempeno por agente individual
- ivr_path_analysis: Analisis de recorridos IVR
- abandoned_call_detail: Detalle de llamadas abandonadas
- transfer_analysis: Analisis de transferencias

Query Parameters:
```
?date_from=2026-01-01
&date_to=2026-03-22
&queue=Cola_Ventas
&agent_id=456
&ivr_option=1
&result=answered
&page=1
&page_size=100
&order_by=call_date
&order=desc
```

Response Exitosa (200 OK) - call_detail:

```json
{
  "success": true,
  "report": {
    "type": "call_detail",
    "title": "Detalle de Llamadas",
    "period": {
      "date_from": "2026-01-01",
      "date_to": "2026-03-22",
      "days": 81
    },
    "generated_at": "2026-03-22T10:30:00Z",
    "response_time_ms": 3420,
    "data": [
      {
        "call_id": "IVR-20260322-001234",
        "call_date": "2026-03-22T09:15:00Z",
        "queue": "Cola_Ventas",
        "agent_id": 456,
        "agent_name": "Ana Gomez",
        "duration_seconds": 247,
        "wait_time_seconds": 32,
        "result": "answered",
        "ivr_path": ["1", "2", "1"],
        "transfer_count": 0,
        "recording_available": true
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 100,
      "total_records": 15234,
      "total_pages": 153
    },
    "drill_down_available": true
  }
}
```

Response - Timeout (504 Gateway Timeout):

```json
{
  "success": false,
  "error_code": "RPT-006",
  "message": "La consulta tardo demasiado. Reduzca el rango de fechas, aplique mas filtros o use reportes basicos",
  "timeout_seconds": 60,
  "suggestion": "Reduzca el rango a 31 dias o menos, o agregue filtros de cola o agente"
}
```

Response - Sin permisos (403 Forbidden):

```json
{
  "success": false,
  "error_code": "RPT-008",
  "message": "No tiene permisos para ver reportes avanzados",
  "suggestion": "Use reports.view_basic para reportes con datos agregados"
}
```

Codigos HTTP:

- 200 OK: Reporte generado exitosamente
- 400 Bad Request: Parametros invalidos
- 403 Forbidden: Sin funcion reports.view_advanced
- 503 Service Unavailable: Base IVR no disponible
- 504 Gateway Timeout: Timeout de consulta (60 segundos)

### VALIDACIONES

Validacion de Parametros:

- report_type: Debe ser uno de los tipos avanzados disponibles
- date_from: Fecha valida, formato YYYY-MM-DD
- date_to: Fecha valida, formato YYYY-MM-DD
- date_from <= date_to
- page: Entero positivo
- page_size: 1-500 registros por pagina

### AUDITORIA

Se registra en AuditLog:

- Accion: view_advanced_report
- Usuario: user_id (quien consulta)
- Timestamp: hora exacta
- Detalles: tipo de reporte, rango de fechas, filtros, tiempo de respuesta

Ejemplo de log:

```json
{
  "timestamp": "2026-03-22T10:30:00Z",
  "action": "view_advanced_report",
  "user_id": 123,
  "ip_address": "192.168.1.100",
  "user_agent": "Chrome/120.0",
  "result": "success",
  "details": {
    "report_type": "call_detail",
    "date_from": "2026-01-01",
    "date_to": "2026-03-22",
    "filters": {"queue": "Cola_Ventas"},
    "response_time_ms": 3420,
    "rows_returned": 100,
    "total_rows": 15234
  }
}
```

### SEGURIDAD

Protecciones Implementadas:

- Base IVR es READ-ONLY: absolutamente prohibido modificar datos
- Limite de 100,000 registros por consulta
- Timeout 60 segundos protege la base de datos
- Paginacion evita transferencia masiva de datos
- Todas las consultas auditadas

Separacion de Bases de Datos:

- IVR (MariaDB): Solo lectura, datos originales de llamadas individuales
- Analytics (PostgreSQL): Escritura, metricas procesadas
- Los reportes avanzados leen de IVR directamente

### NOTAS IMPORTANTES

- NUNCA se modifica la base IVR: READ-ONLY absoluto (CNST-003)
- Sin limite de rango de fechas, pero consultas largas pueden hacer timeout (60 seg)
- Para consultas pesadas: agregar filtros de cola, agente o acortar el rango
- Los reportes avanzados muestran datos por LLAMADA INDIVIDUAL (drill-down)
- Para datos AGREGADOS usar reports.view_basic (mas rapido, max 31 dias)
- La exportacion de reportes avanzados requiere funcion adicional reports.export
- La exportacion via reports.export tiene limite de 10,000 registros

---

Sistema IACT - Analisis IVR
Version: 1.0.0 | Fecha documento: 2026-03-22 | Modelo RBAC: v7.0.0
