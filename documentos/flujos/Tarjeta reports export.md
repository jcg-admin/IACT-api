## TARJETA: reports.export

Nombre para UI: Exportar Reportes
Modulo: MOD_Reports - Reportes y Analisis
ID Caso de Uso: UC-019
Prioridad: MEDIA
Frecuencia: Semanal
Estado: Activo

### DESCRIPCION

Permite exportar reportes IVR a formato CSV o Excel. Limitada a un maximo de 10,000 registros por operacion (CNST-010). El usuario debe tener adicionalmente reports.view_basic o reports.view_advanced para ver el reporte; reports.export solo habilita la exportacion. Acceso READ-ONLY a la base IVR (CNST-003).

### PRECONDICIONES

- Usuario tiene sesion activa
- Usuario tiene funcion reports.export asignada
- Usuario tiene reports.view_basic o reports.view_advanced para haber generado el reporte
- Existe un reporte generado para exportar
- Base de datos IVR disponible

### FLUJO PRINCIPAL (10 PASOS)

1. Usuario ha visualizado un reporte (via reports.view_basic o view_advanced)
2. Usuario hace clic en "Exportar" en el reporte visualizado
3. Sistema muestra opciones de formato: CSV o Excel (XLSX)
4. Sistema muestra rango de registros a exportar (maximo 10,000)
5. Usuario selecciona formato y confirma
6. Sistema valida que el total de registros no supere 10,000 (CNST-010)
7. Sistema genera el archivo con los datos del reporte actual
8. Sistema descarga el archivo al cliente
9. Sistema registra la exportacion en auditoria
10. Sistema muestra confirmacion: "Archivo exportado: {nombre}.{ext}"

### FLUJOS ALTERNATIVOS

**A1. Demasiados registros (paso 6)**

- Sistema detecta que el reporte tiene mas de 10,000 registros
- Sistema muestra error: "La exportacion supera el limite de 10,000 registros. Aplique filtros para reducir los resultados" (RPT-009)
- Sistema puede ofrecer exportar solo los primeros 10,000
- Caso de uso puede reintentar con filtros mas restrictivos

**A2. Error al generar archivo (paso 7)**

- Sistema falla al generar el archivo (error de servidor)
- Sistema muestra error: "Error al generar el archivo. Intente nuevamente" (RPT-010)
- Caso de uso termina con fallo

**A3. Usuario sin funcion reports.export**

- Sistema detecta que usuario no tiene funcion
- Sistema muestra error 403: "No tiene permisos para exportar reportes" (RPT-005)
- Boton de exportar no visible o deshabilitado en la UI
- Caso de uso termina

**A4. Sin reporte generado previamente**

- Usuario intenta exportar sin haber generado un reporte
- Sistema muestra error: "Primero genere un reporte para exportar" (RPT-011)
- Caso de uso termina

### POSTCONDICIONES

Exito:

- Archivo descargado al cliente (CSV o XLSX)
- Registro de auditoria creado con la operacion de exportacion

Fallo:

- Sin archivo generado
- Usuario puede reintentar con filtros diferentes

### REGLAS DE NEGOCIO

- RN-078: Exportacion limitada a 10,000 registros (CNST-010)
- RN-079: Formatos disponibles: CSV (UTF-8 con BOM) o Excel (XLSX)
- RN-080: Nombre del archivo: reporte_{tipo}_{fecha_desde}_{fecha_hasta}.{ext}
- RN-081: El CSV usa coma como separador, texto entre comillas dobles
- RN-082: El XLSX incluye formato basico: encabezados en negrita, autoajuste de columnas
- RN-083: reports.export complementa a reports.view_basic y reports.view_advanced
- RN-084: La exportacion hereda los filtros aplicados en el reporte visualizado

### RESTRICCIONES TECNICAS

- CNST-010: Exportacion maxima 10,000 registros por operacion
- CNST-003: Base IVR es READ-ONLY
- CNST-024: Timeout de generacion de archivo: 60 segundos

### REGLAS SoD

Ninguna

### MENSAJES DEL SISTEMA

Errores:

- RPT-004: "Requiere funcion reports.export para exportar" (desde otros reportes)
- RPT-005: "No tiene permisos para exportar reportes"
- RPT-009: "La exportacion supera el limite de 10,000 registros. Aplique filtros para reducir los resultados"
- RPT-010: "Error al generar el archivo. Intente nuevamente"
- RPT-011: "Primero genere un reporte para exportar"

Informativos:

- INFO-027: "Generando archivo {formato}..."
- INFO-028: "Archivo exportado: {nombre}.{ext} ({registros} registros)"

### IMPLEMENTACION TECNICA

**Exportar reporte**

Endpoint: GET /api/v1/reports/export

Query Parameters:
```
?report_type=calls_by_queue
&date_from=2026-03-01
&date_to=2026-03-22
&queue=Cola_Ventas
&format=csv
```

Parametros adicionales segun tipo de reporte (hereda filtros de view_basic o view_advanced)

Response Exitosa (200 OK) - CSV:

- Content-Type: text/csv; charset=utf-8
- Content-Disposition: attachment; filename="reporte_calls_by_queue_2026-03-01_2026-03-22.csv"
- Body: archivo CSV

Contenido del CSV (ejemplo calls_by_queue):
```
cola,total_llamadas,respondidas,abandonadas,duracion_promedio_seg,nivel_servicio_pct
Cola_Ventas,1523,1410,113,187,92.5
Cola_Soporte,987,945,42,243,95.7
```

Response Exitosa (200 OK) - Excel:

- Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
- Content-Disposition: attachment; filename="reporte_calls_by_queue_2026-03-01_2026-03-22.xlsx"
- Body: archivo XLSX

Response - Limite excedido (400 Bad Request):

```json
{
  "success": false,
  "error_code": "RPT-009",
  "message": "La exportacion supera el limite de 10,000 registros. Aplique filtros para reducir los resultados",
  "total_records": 18500,
  "max_allowed": 10000,
  "suggestion": "Reduzca el rango de fechas a menos de 31 dias o agregue filtros de cola"
}
```

Response - Sin permisos (403 Forbidden):

```json
{
  "success": false,
  "error_code": "RPT-005",
  "message": "No tiene permisos para exportar reportes"
}
```

Codigos HTTP:

- 200 OK: Archivo generado y descargado
- 400 Bad Request: Limite excedido, parametros invalidos
- 403 Forbidden: Sin funcion reports.export
- 504 Gateway Timeout: Timeout al generar archivo
- 500 Internal Server Error: Error al generar archivo

### VALIDACIONES

Validacion de Formato:

- format: Valores permitidos: csv, xlsx
- Si no se especifica: csv por defecto

Validacion de Parametros:

- Mismas validaciones que reports.view_basic o view_advanced segun el tipo de reporte
- Validacion de limite: COUNT(*) antes de generar el archivo

### AUDITORIA

Se registra en AuditLog:

- Accion: export_report
- Usuario: user_id (quien exporta)
- Timestamp: hora exacta
- Detalles: tipo de reporte, filtros, formato, registros exportados, nombre del archivo

Ejemplo de log:

```json
{
  "timestamp": "2026-03-22T10:30:00Z",
  "action": "export_report",
  "user_id": 123,
  "ip_address": "192.168.1.100",
  "user_agent": "Chrome/120.0",
  "result": "success",
  "details": {
    "report_type": "calls_by_queue",
    "date_from": "2026-03-01",
    "date_to": "2026-03-22",
    "filters": {"queue": "Cola_Ventas"},
    "format": "csv",
    "records_exported": 5,
    "filename": "reporte_calls_by_queue_2026-03-01_2026-03-22.csv"
  }
}
```

### SEGURIDAD

Protecciones Implementadas:

- Limite de 10,000 registros previene extraccion masiva de datos IVR
- Base IVR READ-ONLY: nunca se modifican datos durante exportacion
- Todas las exportaciones auditadas con detalle
- reports.export es funcion adicional: usuario debe tener tambien view_basic o view_advanced

### NOTAS IMPORTANTES

- reports.export es una funcion COMPLEMENTARIA: por si sola no permite ver reportes
- Se requiere reports.view_basic o reports.view_advanced para ver el reporte antes de exportar
- Limite de 10,000 registros por exportacion (CNST-010)
- Si se necesitan mas de 10,000 registros, exportar por partes usando filtros de fechas
- Formato CSV: UTF-8 con BOM para compatibilidad con Microsoft Excel
- Formato XLSX: incluye formato basico de hoja de calculo

---

Sistema IACT - Analisis IVR
Version: 1.0.0 | Fecha documento: 2026-03-22 | Modelo RBAC: v7.0.0
