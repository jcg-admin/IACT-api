## TARJETA: reports.modify_data

Nombre para UI: Modificar Datos de Reportes
Modulo: MOD_Reports - Reportes y Analisis
ID Caso de Uso: UC-020
Prioridad: CRITICA
Frecuencia: Ocasional
Estado: Activo

### DESCRIPCION

Permite modificar datos en la base de Analytics (PostgreSQL). NUNCA modifica la base IVR (MariaDB). Las modificaciones quedan en estado "pendiente_aprobacion" hasta que reports.approve las valide. El usuario que modifica NO puede aprobar sus propias modificaciones (control dual, SoD 3). Requiere justificacion obligatoria minimo 30 caracteres.

### PRECONDICIONES

- Usuario tiene sesion activa
- Usuario tiene funcion reports.modify_data asignada
- El usuario NO tiene reports.approve (SoD 3)
- El registro a modificar existe en Analytics (PostgreSQL)
- Justificacion disponible (minimo 30 caracteres)

### FLUJO PRINCIPAL (15 PASOS)

1. Usuario navega a seccion "Modificar Datos"
2. Sistema muestra tablas modificables de Analytics
3. Usuario selecciona tabla y busca el registro a modificar
4. Sistema muestra registro actual con todos sus campos
5. Usuario modifica los campos deseados
6. Sistema muestra diferencial: valores anteriores vs nuevos
7. Usuario ingresa justificacion (minimo 30 caracteres)
8. Usuario hace clic en "Solicitar Modificacion"
9. Sistema valida que la tabla sea modificable (lista blanca)
10. Sistema valida que los campos nuevos sean validos
11. Sistema valida la justificacion
12. Sistema guarda la modificacion en estado "pendiente_aprobacion"
13. Sistema registra: datos originales, datos nuevos, quien solicita, cuando
14. Sistema notifica internamente a usuarios con reports.approve
15. Sistema muestra confirmacion: "Modificacion enviada para aprobacion. ID: {mod_id}"

### FLUJOS ALTERNATIVOS

**A1. Tabla no modificable (paso 9)**

- Sistema detecta que el usuario intenta modificar una tabla no permitida
- Sistema muestra error: "La tabla seleccionada no permite modificaciones" (RPT-012)
- Caso de uso termina

**A2. Modificar base IVR (bloqueado)**

- Sistema detecta intento de modificar tablas de base IVR
- Sistema RECHAZA automaticamente: "Prohibido modificar la base IVR" (RPT-013)
- Operacion bloqueada a nivel de base de datos (permisos DB)
- Caso de uso termina

**A3. Justificacion insuficiente (paso 11)**

- Sistema detecta justificacion con menos de 30 caracteres
- Sistema muestra error: "La justificacion debe tener al menos 30 caracteres" (RPT-014)
- Usuario permanece en formulario
- Caso de uso puede reintentar desde paso 7

**A4. Campos invalidos (paso 10)**

- Sistema detecta valores que no cumplen validaciones del campo
- Sistema muestra errores especificos por campo
- Usuario permanece en formulario
- Caso de uso puede reintentar desde paso 5

**A5. Modificacion pendiente ya existente para el registro (paso 12)**

- Sistema detecta que el registro ya tiene una modificacion en estado "pendiente_aprobacion"
- Sistema muestra advertencia: "El registro ya tiene una modificacion pendiente de aprobacion" (RPT-015)
- Sistema puede rechazar nueva modificacion hasta que se resuelva la pendiente
- Caso de uso termina

**A6. Usuario sin funcion reports.modify_data**

- Sistema detecta que usuario no tiene funcion
- Sistema muestra error 403: "No tiene permisos para modificar datos de reportes" (RPT-005)
- Usuario es redirigido a pagina anterior
- Caso de uso termina

### POSTCONDICIONES

Exito:

- Modificacion guardada en estado "pendiente_aprobacion"
- Registro de auditoria creado con datos originales y nuevos
- Notificacion interna enviada a aprobadores

Fallo:

- Sin cambios en la base de datos
- Usuario puede corregir y reintentar

### REGLAS DE NEGOCIO

- RN-085: Las modificaciones NUNCA afectan la base IVR (MariaDB): solo Analytics (PostgreSQL)
- RN-086: Toda modificacion queda en estado "pendiente_aprobacion" hasta aprobacion explicita
- RN-087: Justificacion obligatoria minimo 30 caracteres
- RN-088: El usuario que modifica NO puede aprobar sus propias modificaciones (SoD 3)
- RN-089: Se registran: datos_originales, datos_nuevos, solicitante, timestamp
- RN-090: Un registro solo puede tener una modificacion pendiente a la vez

### RESTRICCIONES TECNICAS

- CNST-003: Base IVR es READ-ONLY absoluto (ni esta funcion puede modificarla)
- CNST-025: Tablas modificables en Analytics: call_metrics, categorizations, quality_scores, custom_tags
- CNST-026: Tablas PROHIBIDAS: cualquier tabla de base IVR, usuarios, funciones, auditoria

### REGLAS SoD

- SoD 3 (report_data_separation)
- INCOMPATIBLE con: reports.approve
- Razon: Quien modifica datos NO puede aprobar sus propias modificaciones (control dual)

### MENSAJES DEL SISTEMA

Errores:

- RPT-005: "No tiene permisos para modificar datos de reportes"
- RPT-012: "La tabla seleccionada no permite modificaciones"
- RPT-013: "Prohibido modificar la base IVR. Solo se permite modificar Analytics"
- RPT-014: "La justificacion debe tener al menos 30 caracteres"
- RPT-015: "El registro ya tiene una modificacion pendiente de aprobacion"

Confirmacion:

- OK-019: "Modificacion enviada para aprobacion. ID: {mod_id}"

Informativos:

- INFO-029: "La modificacion requiere aprobacion de otro usuario (control dual)"
- INFO-030: "Se notificara a los aprobadores disponibles"

### IMPLEMENTACION TECNICA

**Solicitar modificacion de datos**

Endpoint: POST /api/v1/reports/modify-data

Request:

```json
{
  "table": "call_metrics",
  "record_id": 78901,
  "changes": {
    "categorization": "Venta Exitosa",
    "quality_score": 85,
    "custom_tag": "prioridad_alta"
  },
  "justification": "Correccion de categoria de llamada. IVR clasifico incorrectamente como no exitosa. Evidencia en ticket CRM-2026-0789."
}
```

Response Exitosa (202 Accepted):

```json
{
  "success": true,
  "message": "Modificacion enviada para aprobacion",
  "modification": {
    "id": "MOD-2026-03-22-0045",
    "status": "pendiente_aprobacion",
    "table": "call_metrics",
    "record_id": 78901,
    "changes": {
      "categorization": {
        "old": "No Identificado",
        "new": "Venta Exitosa"
      },
      "quality_score": {
        "old": 60,
        "new": 85
      },
      "custom_tag": {
        "old": null,
        "new": "prioridad_alta"
      }
    },
    "requested_by": {
      "id": 123,
      "username": "jperez"
    },
    "requested_at": "2026-03-22T10:30:00Z",
    "justification": "Correccion de categoria de llamada...",
    "approvers_notified": 2
  }
}
```

Response - Tabla prohibida (403 Forbidden):

```json
{
  "success": false,
  "error_code": "RPT-013",
  "message": "Prohibido modificar la base IVR. Solo se permite modificar Analytics",
  "attempted_table": "ivr_calls",
  "allowed_tables": ["call_metrics", "categorizations", "quality_scores", "custom_tags"]
}
```

Response - Modificacion pendiente existente (409 Conflict):

```json
{
  "success": false,
  "error_code": "RPT-015",
  "message": "El registro ya tiene una modificacion pendiente de aprobacion",
  "pending_modification_id": "MOD-2026-03-20-0023",
  "pending_since": "2026-03-20T14:00:00Z"
}
```

Response - Sin permisos (403 Forbidden):

```json
{
  "success": false,
  "error_code": "RPT-005",
  "message": "No tiene permisos para modificar datos de reportes"
}
```

Codigos HTTP:

- 202 Accepted: Modificacion creada en estado pendiente
- 400 Bad Request: Justificacion invalida, campos invalidos
- 403 Forbidden: Sin permisos, tabla prohibida
- 404 Not Found: Registro no encontrado
- 409 Conflict: Ya existe modificacion pendiente para el registro
- 500 Internal Server Error: Error del servidor

### VALIDACIONES

Validacion de Tabla:

- table: Debe estar en lista blanca de tablas Analytics modificables
- NUNCA puede ser tabla de base IVR
- NUNCA puede ser tabla de usuarios, funciones o auditoria

Validacion de Registro:

- record_id: Debe existir en la tabla especificada
- Solo en Analytics (PostgreSQL), nunca en IVR (MariaDB)

Validacion de Campos:

- Solo campos no protegidos del sistema
- Tipos de datos correctos segun el campo
- Valores dentro de rangos permitidos

Validacion de Justificacion:

- Obligatoria
- Minimo 30 caracteres (mas estricta que otras funciones)
- Recomendado: referencia a ticket o evidencia

### AUDITORIA

Se registra en AuditLog:

- Accion: request_data_modification
- Usuario: user_id (quien solicita)
- Timestamp: hora exacta
- Detalles: tabla, record_id, cambios (old y new), justificacion, ID de modificacion

Ejemplo de log:

```json
{
  "timestamp": "2026-03-22T10:30:00Z",
  "action": "request_data_modification",
  "user_id": 123,
  "ip_address": "192.168.1.100",
  "user_agent": "Chrome/120.0",
  "result": "pending_approval",
  "details": {
    "modification_id": "MOD-2026-03-22-0045",
    "table": "call_metrics",
    "record_id": 78901,
    "fields_changed": ["categorization", "quality_score", "custom_tag"],
    "justification": "Correccion de categoria de llamada...",
    "database": "analytics_postgresql"
  }
}
```

### SEGURIDAD

Protecciones Implementadas:

- Base IVR ABSOLUTAMENTE PROHIBIDA para modificaciones
- Tablas Analytics modificables: lista blanca estricta (CNST-025)
- Control dual obligatorio: modificacion + aprobacion por personas diferentes (SoD 3)
- Datos originales siempre preservados para auditoria
- Justificacion mas estricta (30 chars) por la criticidad de la funcion
- Todas las modificaciones auditadas con datos completos

Control Dual (SoD 3):

- Usuario que MODIFICA: reports.modify_data
- Usuario que APRUEBA: reports.approve
- Son INCOMPATIBLES: no puede ser la misma persona
- Garantia de cuatro ojos en modificacion de datos de reportes

### NOTAS IMPORTANTES

- NUNCA modifica la base IVR: todos los cambios son en Analytics (PostgreSQL)
- La modificacion queda PENDIENTE hasta que un aprobador la valide (reports.approve)
- El usuario que modifica NO puede ser el mismo que aprueba (SoD 3)
- Los datos originales se preservan siempre para auditoria completa
- Si ya hay una modificacion pendiente para el mismo registro, se rechaza
- La justificacion debe incluir referencia clara (ticket, evidencia)

---

Sistema IACT - Analisis IVR
Version: 1.0.0 | Fecha documento: 2026-03-22 | Modelo RBAC: v7.0.0
