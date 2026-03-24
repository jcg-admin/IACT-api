## TARJETA: reports.approve

Nombre para UI: Aprobar Modificaciones de Reportes
Modulo: MOD_Reports - Reportes y Analisis
ID Caso de Uso: UC-021
Prioridad: CRITICA
Frecuencia: Ocasional
Estado: Activo

### DESCRIPCION

Permite aprobar o rechazar modificaciones pendientes de datos de reportes creadas por reports.modify_data. Implementa control dual (cuatro ojos): el usuario aprobador es siempre diferente al usuario modificador (SoD 3). El usuario NO puede aprobar modificaciones que el mismo solicito. Al aprobar, los cambios se aplican en la base Analytics. Al rechazar, los datos originales se mantienen sin cambios.

### PRECONDICIONES

- Usuario tiene sesion activa
- Usuario tiene funcion reports.approve asignada
- El usuario NO tiene reports.modify_data (SoD 3)
- Existen modificaciones en estado "pendiente_aprobacion"

### FLUJO PRINCIPAL (13 PASOS)

1. Usuario navega a seccion "Aprobar Modificaciones"
2. Sistema muestra lista de modificaciones pendientes de aprobacion
3. Usuario selecciona una modificacion para revisar
4. Sistema muestra detalle completo: datos originales vs nuevos, solicitante, justificacion
5. Usuario revisa los cambios propuestos
6. Usuario decide: Aprobar o Rechazar
7. Si aprueba: usuario ingresa comentario de aprobacion (opcional)
8. Si rechaza: usuario ingresa motivo de rechazo (obligatorio, minimo 20 caracteres)
9. Usuario hace clic en "Confirmar"
10. Sistema verifica que el aprobador no sea el mismo que el solicitante
11. Sistema aplica la decision:
    - Si aprobado: UPDATE en tabla Analytics con los nuevos valores
    - Si rechazado: registro queda con status "rechazado", datos originales sin cambios
12. Sistema registra en auditoria: decision, aprobador, timestamp, comentario
13. Sistema notifica internamente al solicitante sobre la decision

### FLUJOS ALTERNATIVOS

**A1. Aprobador es el mismo que el solicitante (paso 10)**

- Sistema detecta que el usuario que aprueba es el mismo que solicito la modificacion
- Sistema rechaza la operacion: "No puede aprobar sus propias modificaciones" (RPT-016)
- Operacion bloqueada por SoD 3
- Caso de uso termina

**A2. Modificacion ya procesada (paso 4)**

- Sistema detecta que la modificacion ya fue aprobada o rechazada previamente
- Sistema muestra informacion de la decision tomada anteriormente
- Sistema no permite tomar una nueva decision sobre modificacion ya procesada
- Caso de uso termina

**A3. Sin modificaciones pendientes (paso 2)**

- Sistema no encuentra modificaciones pendientes de aprobacion
- Sistema muestra mensaje: "No hay modificaciones pendientes de aprobacion" (INFO-031)
- Caso de uso termina

**A4. Rechazo sin motivo (paso 8)**

- Usuario intenta rechazar sin ingresar motivo
- Sistema muestra error: "El motivo de rechazo es obligatorio" (RPT-017)
- Usuario permanece en formulario
- Caso de uso puede reintentar desde paso 8

**A5. Rechazo con motivo muy corto (paso 8)**

- Sistema detecta motivo de rechazo con menos de 20 caracteres
- Sistema muestra error: "El motivo de rechazo debe tener al menos 20 caracteres" (RPT-018)
- Usuario permanece en formulario
- Caso de uso puede reintentar desde paso 8

**A6. Error al aplicar modificacion aprobada (paso 11)**

- Sistema falla al ejecutar UPDATE en Analytics
- Sistema mantiene la modificacion en estado "error_aplicacion"
- Sistema registra el error en auditoria
- Sistema notifica al equipo tecnico
- Caso de uso termina con estado especial

**A7. Usuario sin funcion reports.approve**

- Sistema detecta que usuario no tiene funcion
- Sistema muestra error 403: "No tiene permisos para aprobar modificaciones" (RPT-005)
- Usuario es redirigido a pagina anterior
- Caso de uso termina

### POSTCONDICIONES

Exito (aprobacion):

- Cambios aplicados en base Analytics (PostgreSQL)
- Modificacion marcada con status "aprobado", approved_at, approved_by, comentario
- Notificacion interna enviada al solicitante

Exito (rechazo):

- Datos originales sin cambios
- Modificacion marcada con status "rechazado", rejected_at, rejected_by, motivo
- Notificacion interna enviada al solicitante

Fallo:

- Modificacion permanece en estado "pendiente_aprobacion"
- Sin cambios en datos

### REGLAS DE NEGOCIO

- RN-091: Control dual obligatorio: aprobador != solicitante (SoD 3)
- RN-092: Aprobacion aplica inmediatamente los cambios en Analytics
- RN-093: Rechazo requiere motivo obligatorio minimo 20 caracteres
- RN-094: Una modificacion procesada (aprobada o rechazada) es DEFINITIVA
- RN-095: Comentario de aprobacion es opcional pero recomendado
- RN-096: Se notifica al solicitante sobre la decision tomada

### RESTRICCIONES TECNICAS

- CNST-003: Solo se modifican datos en Analytics (PostgreSQL), nunca en IVR
- Control dual garantizado por SoD 3 a nivel de sistema

### REGLAS SoD

- SoD 3 (report_data_separation)
- INCOMPATIBLE con: reports.modify_data
- Razon: Quien aprueba modificaciones NO puede haberlas creado (control dual)

### MENSAJES DEL SISTEMA

Errores:

- RPT-005: "No tiene permisos para aprobar modificaciones"
- RPT-016: "No puede aprobar sus propias modificaciones"
- RPT-017: "El motivo de rechazo es obligatorio"
- RPT-018: "El motivo de rechazo debe tener al menos 20 caracteres"

Confirmacion:

- OK-020: "Modificacion aprobada. Cambios aplicados en Analytics"
- OK-021: "Modificacion rechazada. Datos originales conservados"

Informativos:

- INFO-031: "No hay modificaciones pendientes de aprobacion"
- INFO-032: "Aplicando cambios en base Analytics..."

### IMPLEMENTACION TECNICA

**Aprobar o rechazar modificacion**

Endpoint: POST /api/v1/reports/approve-modification

Request - Aprobacion:

```json
{
  "modification_id": "MOD-2026-03-22-0045",
  "decision": "approve",
  "comment": "Verificado con grabacion de llamada. Categoria correcta segun criterios de ventas."
}
```

Request - Rechazo:

```json
{
  "modification_id": "MOD-2026-03-22-0045",
  "decision": "reject",
  "rejection_reason": "No hay evidencia suficiente para cambiar la categoria. Requiere revision adicional del supervisor."
}
```

Response Exitosa - Aprobacion (200 OK):

```json
{
  "success": true,
  "message": "Modificacion aprobada. Cambios aplicados en Analytics",
  "modification": {
    "id": "MOD-2026-03-22-0045",
    "status": "aprobado",
    "table": "call_metrics",
    "record_id": 78901,
    "changes_applied": {
      "categorization": {
        "old": "No Identificado",
        "new": "Venta Exitosa"
      },
      "quality_score": {
        "old": 60,
        "new": 85
      }
    },
    "approved_by": {
      "id": 200,
      "username": "supervisor_aprobador"
    },
    "approved_at": "2026-03-22T11:00:00Z",
    "comment": "Verificado con grabacion de llamada...",
    "original_request": {
      "requested_by": "jperez",
      "requested_at": "2026-03-22T10:30:00Z"
    }
  }
}
```

Response Exitosa - Rechazo (200 OK):

```json
{
  "success": true,
  "message": "Modificacion rechazada. Datos originales conservados",
  "modification": {
    "id": "MOD-2026-03-22-0045",
    "status": "rechazado",
    "rejected_by": {
      "id": 200,
      "username": "supervisor_aprobador"
    },
    "rejected_at": "2026-03-22T11:05:00Z",
    "rejection_reason": "No hay evidencia suficiente...",
    "data_unchanged": true
  }
}
```

Response - Auto-aprobacion bloqueada (403 Forbidden):

```json
{
  "success": false,
  "error_code": "RPT-016",
  "message": "No puede aprobar sus propias modificaciones",
  "sod_rule": "SoD 3 - report_data_separation",
  "modification_requested_by": "jperez",
  "current_user": "jperez"
}
```

Response - Sin permisos (403 Forbidden):

```json
{
  "success": false,
  "error_code": "RPT-005",
  "message": "No tiene permisos para aprobar modificaciones"
}
```

Estados de modificacion:

```
pendiente_aprobacion -> aprobado (cambios aplicados en Analytics)
pendiente_aprobacion -> rechazado (datos originales sin cambios)
pendiente_aprobacion -> error_aplicacion (fallo tecnico al aplicar)
```

Codigos HTTP:

- 200 OK: Decision aplicada exitosamente
- 400 Bad Request: Motivo de rechazo insuficiente, decision invalida
- 403 Forbidden: Sin permisos, auto-aprobacion bloqueada
- 404 Not Found: Modificacion no encontrada
- 409 Conflict: Modificacion ya procesada
- 500 Internal Server Error: Error al aplicar cambios en Analytics

### VALIDACIONES

Validacion de Modificacion:

- modification_id: Debe existir y estar en estado "pendiente_aprobacion"
- No puede estar en estado "aprobado" o "rechazado" previamente

Validacion de Decision:

- decision: Valores permitidos: "approve", "reject"
- Si "reject": rejection_reason obligatorio, minimo 20 caracteres
- Si "approve": comment es opcional

Validacion de Control Dual:

- approved_by (usuario actual) != requested_by (usuario que creo la modificacion)
- Verificacion por user_id, no por username

### AUDITORIA

Se registra en AuditLog:

- Accion: approve_modification o reject_modification
- Usuario: user_id (quien aprueba o rechaza)
- Timestamp: hora exacta
- Detalles: modification_id, decision, datos cambiados, justificacion del solicitante, comentario del aprobador

Ejemplo de log - Aprobacion:

```json
{
  "timestamp": "2026-03-22T11:00:00Z",
  "action": "approve_modification",
  "user_id": 200,
  "ip_address": "192.168.1.101",
  "user_agent": "Chrome/120.0",
  "result": "success",
  "details": {
    "modification_id": "MOD-2026-03-22-0045",
    "table": "call_metrics",
    "record_id": 78901,
    "decision": "approve",
    "changes_applied": ["categorization", "quality_score"],
    "original_requester_id": 123,
    "sod_validated": true,
    "database": "analytics_postgresql"
  }
}
```

### SEGURIDAD

Protecciones Implementadas:

- Control dual OBLIGATORIO (SoD 3): diferentes personas para modificar y aprobar
- Aprobacion de propias modificaciones BLOQUEADA a nivel de sistema
- Decision irreversible: modificacion aprobada o rechazada no puede cambiarse
- Auditoria completa: trazabilidad de toda la cadena de aprobacion

### NOTAS IMPORTANTES

- NUNCA puede aprobar sus propias modificaciones (SoD 3 - control dual)
- El aprobador no puede tener reports.modify_data (incompatible por SoD 3)
- La aprobacion aplica los cambios INMEDIATAMENTE en Analytics
- El rechazo NO modifica ningun dato: los originales se conservan
- Una vez procesada la decision (aprobar o rechazar) es DEFINITIVA
- El solicitante recibe notificacion interna sobre la decision

---

Sistema IACT - Analisis IVR
Version: 1.0.0 | Fecha documento: 2026-03-22 | Modelo RBAC: v7.0.0
