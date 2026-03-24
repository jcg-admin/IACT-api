## TARJETA: reports.view_basic

Nombre para UI: Ver Reportes Basicos
Modulo: MOD_Reports - Reportes y Analisis
ID Caso de Uso: UC-017
Prioridad: ALTA
Frecuencia: Diaria
Estado: Activo

### DESCRIPCION

Permite consultar reportes basicos del sistema IVR con informacion agregada por cola, hora o dia. Los reportes muestran metricas generales de llamadas: volumen, duracion promedio, niveles de servicio, uso de opciones IVR. El rango maximo de fechas es 31 dias. Acceso de solo lectura a la base IVR (CNST-003: READ-ONLY).

### PRECONDICIONES

- Usuario tiene sesion activa
- Usuario tiene funcion reports.view_basic asignada
- Base de datos IVR disponible (READ-ONLY)

### FLUJO PRINCIPAL (10 PASOS)

1. Usuario navega a seccion "Reportes" y selecciona "Reportes Basicos"
2. Sistema muestra catalogo de tipos de reportes disponibles
3. Usuario selecciona el tipo de reporte
4. Usuario selecciona rango de fechas (maximo 31 dias)
5. Usuario selecciona filtros adicionales (cola, agente, grupo)
6. Usuario hace clic en "Ver Reporte"
7. Sistema valida que el rango no exceda 31 dias
8. Sistema ejecuta consulta READ-ONLY en base IVR (timeout 30 seg)
9. Sistema muestra reporte con tablas y graficos
10. Usuario puede cambiar filtros o exportar (si tiene reports.export)

### FLUJOS ALTERNATIVOS

**A1. Rango de fechas mayor a 31 dias (paso 7)**

- Sistema detecta que el rango excede el limite
- Sistema muestra error: "El rango maximo para reportes basicos es 31 dias" (RPT-001)
- Usuario permanece en formulario
- Caso de uso puede reintentar desde paso 4
- Nota: Para rangos mayores usar reports.view_advanced

**A2. Timeout de consulta (paso 8)**

- Consulta excede 30 segundos sin respuesta
- Sistema cancela consulta
- Sistema muestra error: "La consulta tardo demasiado. Reduzca el rango de fechas o filtros" (RPT-002)
- Caso de uso puede reintentar desde paso 4 con filtros mas restrictivos

**A3. Sin datos para el periodo (paso 9)**

- Base IVR no tiene registros para el rango seleccionado
- Sistema muestra mensaje: "No hay datos para el periodo seleccionado" (INFO-021)
- Se muestra reporte vacio con estructura correcta
- Caso de uso termina exitosamente

**A4. Base IVR no disponible (paso 8)**

- Sistema no puede conectar a base IVR
- Sistema muestra error: "La base de datos IVR no esta disponible. Intente mas tarde" (RPT-003)
- Caso de uso termina

**A5. Exportar reporte (paso 10)**

- Usuario hace clic en "Exportar"
- Sistema verifica si usuario tiene reports.export
- Si NO tiene: muestra error "Requiere funcion reports.export" (RPT-004)
- Si SI tiene: genera archivo CSV/Excel con los datos del reporte

**A6. Usuario sin funcion reports.view_basic**

- Sistema detecta que usuario no tiene funcion
- Sistema muestra error 403: "No tiene permisos para ver reportes" (RPT-005)
- Usuario es redirigido a pagina anterior
- Caso de uso termina

### POSTCONDICIONES

Exito:

- Reporte mostrado con datos del periodo seleccionado
- Graficos y tablas renderizados correctamente

Fallo:

- Sin datos mostrados
- Usuario puede reintentar con parametros diferentes

### REGLAS DE NEGOCIO

- RN-067: Rango maximo de fechas: 31 dias
- RN-068: Base IVR es READ-ONLY (solo SELECT, nunca INSERT/UPDATE/DELETE)
- RN-069: Timeout de consulta: 30 segundos
- RN-070: Datos son de la base IVR (MariaDB), NO de Analytics (PostgreSQL)
- RN-071: Reportes basicos muestran datos agregados (no por llamada individual)

### RESTRICCIONES TECNICAS

- CNST-003: Base IVR es READ-ONLY (solo SELECT en MariaDB IVR)
- CNST-019: Timeout 30 segundos para consultas de reportes basicos
- CNST-021: Rango maximo 31 dias para reportes basicos

### REGLAS SoD

Ninguna

### MENSAJES DEL SISTEMA

Errores:

- RPT-001: "El rango maximo para reportes basicos es 31 dias"
- RPT-002: "La consulta tardo demasiado. Reduzca el rango de fechas o filtros"
- RPT-003: "La base de datos IVR no esta disponible. Intente mas tarde"
- RPT-004: "Requiere funcion reports.export para exportar"
- RPT-005: "No tiene permisos para ver reportes"

Informativos:

- INFO-021: "No hay datos para el periodo seleccionado"
- INFO-022: "Cargando reporte..."
- INFO-023: "Reporte generado en X segundos"

### IMPLEMENTACION TECNICA

**Ver reporte basico**

Endpoint: GET /api/v1/reports/basic/{report_type}

Tipos de reportes disponibles:
- calls_by_queue: Llamadas por cola de atencion
- daily_summary: Resumen diario de llamadas
- calls_by_hour: Distribucion de llamadas por hora del dia
- ivr_options_usage: Uso de opciones del menu IVR
- queue_performance: Desempeno de colas (nivel de servicio, abandono)

Query Parameters:
```
?date_from=2026-03-01
&date_to=2026-03-22
&queue=Cola_Ventas
&group=Comercial
```

Response Exitosa (200 OK) - calls_by_queue:

```json
{
  "success": true,
  "report": {
    "type": "calls_by_queue",
    "title": "Llamadas por Cola",
    "period": {
      "date_from": "2026-03-01",
      "date_to": "2026-03-22",
      "days": 22
    },
    "generated_at": "2026-03-22T10:30:00Z",
    "data": [
      {
        "queue": "Cola_Ventas",
        "total_calls": 1523,
        "answered": 1410,
        "abandoned": 113,
        "avg_duration_seconds": 187,
        "service_level_pct": 92.5
      },
      {
        "queue": "Cola_Soporte",
        "total_calls": 987,
        "answered": 945,
        "abandoned": 42,
        "avg_duration_seconds": 243,
        "service_level_pct": 95.7
      }
    ],
    "totals": {
      "total_calls": 2510,
      "total_answered": 2355,
      "total_abandoned": 155,
      "global_service_level_pct": 93.8
    }
  }
}
```

Response - Rango excedido (400 Bad Request):

```json
{
  "success": false,
  "error_code": "RPT-001",
  "message": "El rango maximo para reportes basicos es 31 dias",
  "requested_days": 45,
  "max_days": 31,
  "suggestion": "Use reports.view_advanced para rangos mayores a 31 dias"
}
```

Response - Sin permisos (403 Forbidden):

```json
{
  "success": false,
  "error_code": "RPT-005",
  "message": "No tiene permisos para ver reportes"
}
```

Codigos HTTP:

- 200 OK: Reporte generado exitosamente
- 400 Bad Request: Parametros invalidos (rango, tipo de reporte)
- 403 Forbidden: Sin funcion reports.view_basic
- 503 Service Unavailable: Base IVR no disponible
- 504 Gateway Timeout: Timeout de consulta (30 segundos)

### VALIDACIONES

Validacion de Parametros:

- report_type: Debe ser uno de los tipos disponibles
- date_from: Fecha valida, formato YYYY-MM-DD
- date_to: Fecha valida, formato YYYY-MM-DD
- date_from <= date_to
- (date_to - date_from) <= 31 dias
- date_to: No puede ser fecha futura (se permite dia actual)

### AUDITORIA

Se registra en AuditLog:

- Accion: view_basic_report
- Usuario: user_id (quien consulta)
- Timestamp: hora exacta
- Detalles: tipo de reporte, rango de fechas, tiempo de respuesta

Ejemplo de log:

```json
{
  "timestamp": "2026-03-22T10:30:00Z",
  "action": "view_basic_report",
  "user_id": 123,
  "ip_address": "192.168.1.100",
  "user_agent": "Chrome/120.0",
  "result": "success",
  "details": {
    "report_type": "calls_by_queue",
    "date_from": "2026-03-01",
    "date_to": "2026-03-22",
    "response_time_ms": 847,
    "rows_returned": 5
  }
}
```

### SEGURIDAD

Protecciones Implementadas:

- Base IVR es READ-ONLY: absolutamente prohibido modificar datos IVR
- Rango maximo 31 dias previene consultas excesivamente pesadas
- Timeout 30 segundos protege la base de datos
- Todas las consultas auditadas

Separacion de Bases de Datos:

- IVR (MariaDB): Solo lectura, datos originales de llamadas
- Analytics (PostgreSQL): Escritura, metricas procesadas
- Los reportes basicos leen de IVR directamente

### NOTAS IMPORTANTES

- NUNCA se modifica la base IVR: es READ-ONLY absoluto (CNST-003)
- Rango maximo 31 dias: para rangos mayores usar reports.view_advanced
- Timeout 30 segundos: si la consulta es lenta, reducir el rango o filtros
- Los reportes basicos muestran datos AGREGADOS, no individuales por llamada
- Para ver datos por llamada individual usar reports.view_advanced

---

Sistema IACT - Analisis IVR
Version: 1.0.0 | Fecha documento: 2026-03-22 | Modelo RBAC: v7.0.0
