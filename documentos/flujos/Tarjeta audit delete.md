## TARJETA: audit.delete

Nombre para UI: Eliminar Registros de Auditoria
Modulo: MOD_Audit - Auditoria y Compliance
ID Caso de Uso: UC-025
Prioridad: CRITICA
Frecuencia: Muy Ocasional
Estado: Activo

### DESCRIPCION

Permite eliminar registros especificos de auditoria bajo circunstancias excepcionales (ej: cumplimiento de regulaciones de privacidad, eliminacion de datos personales por solicitud legal). Esta es una funcion MUY RESTRINGIDA que solo debe usarse en casos justificados legalmente. Todas las eliminaciones quedan permanentemente registradas en log inmutable separado.

### PRECONDICIONES

- Usuario tiene sesion activa
- Usuario tiene funcion audit.delete asignada
- Existe justificacion legal o regulatoria documentada
- Registros a eliminar existen en base de datos
- Eliminacion NO viola periodo de retencion obligatorio (7 anos)

### FLUJO PRINCIPAL (17 PASOS)

1. Usuario navega a seccion "Eliminar Registros de Auditoria"
2. Sistema muestra advertencia critica sobre naturaleza de esta funcion
3. Usuario confirma que entiende las implicaciones
4. Usuario busca registros a eliminar usando filtros
5. Sistema muestra registros encontrados
6. Usuario selecciona registros especificos a eliminar
7. Sistema muestra resumen de registros seleccionados
8. Usuario ingresa justificacion legal (minimo 100 caracteres)
9. Usuario adjunta documento de respaldo (opcional pero recomendado)
10. Usuario ingresa su contrasena actual para confirmar
11. Usuario hace clic en "Confirmar Eliminacion"
12. Sistema valida contrasena
13. Sistema valida justificacion
14. Sistema valida que eliminacion NO viola retencion de 7 anos
15. Sistema elimina registros de tabla AuditLog
16. Sistema registra eliminacion en tabla DeletionLog (INMUTABLE)
17. Sistema muestra confirmacion: "Registros eliminados. Accion registrada permanentemente"

### FLUJOS ALTERNATIVOS

**A1. Viola periodo de retencion (paso 14)**

- Sistema detecta que registros tienen menos de 7 anos
- Sistema muestra error: "No se puede eliminar. Periodo de retencion obligatorio 7 anos" (AUD-004)
- Sistema rechaza operacion
- Caso de uso termina

**A2. Justificacion insuficiente (paso 13)**

- Sistema detecta justificacion menor a 100 caracteres
- Sistema muestra error: "Justificacion debe tener al menos 100 caracteres y fundamento legal" (AUD-005)
- Usuario permanece en formulario
- Caso de uso puede reintentar desde paso 8

**A3. Contrasena incorrecta (paso 12)**

- Sistema detecta que contrasena no coincide
- Sistema muestra error: "Contrasena incorrecta" (AUD-006)
- Usuario permanece en formulario
- Caso de uso puede reintentar desde paso 10

**A4. Usuario sin funcion audit.delete**

- Sistema detecta que usuario no tiene funcion
- Sistema muestra error 403: "No tiene permisos para eliminar auditoria" (AUD-007)
- Usuario es redirigido a pagina anterior
- Caso de uso termina

**A5. Usuario cancela eliminacion (paso 11)**

- Usuario hace clic en "Cancelar"
- Sistema cierra formulario
- Sin cambios
- Caso de uso termina

**A6. Sin registros seleccionados (paso 11)**

- Sistema detecta que no hay registros seleccionados
- Sistema muestra mensaje: "Seleccione al menos un registro" (INFO-049)
- Usuario permanece en formulario
- Caso de uso puede reintentar desde paso 6

### POSTCONDICIONES

Exito:

- Registros eliminados de AuditLog
- Eliminacion registrada PERMANENTEMENTE en DeletionLog
- Usuario, fecha, hora, registros eliminados, justificacion preservados
- Accion irreversible completada

Fallo:

- Registros sin cambios
- Usuario puede reintentar con justificacion adecuada

### REGLAS DE NEGOCIO

- RN-145: Justificacion legal obligatoria minimo 100 caracteres
- RN-146: NO se puede eliminar registros con menos de 7 anos (retencion obligatoria)
- RN-147: Usuario debe confirmar con su contrasena actual
- RN-148: Eliminacion se registra PERMANENTEMENTE en tabla DeletionLog inmutable
- RN-149: Maximo 100 registros por operacion de eliminacion
- RN-150: Eliminacion es IRREVERSIBLE

### RESTRICCIONES TECNICAS

- CNST-015: Retencion de auditoria minimo 7 anos
  - No se puede eliminar logs con menos de 7 anos
  - Excepto por orden legal explicita documentada

### REGLAS SoD

Ninguna (funcion tan restringida que no requiere SoD adicional)

### MENSAJES DEL SISTEMA

Errores:

- AUD-004: "No se puede eliminar. Periodo de retencion obligatorio 7 anos" (viola retencion)
- AUD-005: "Justificacion debe tener al menos 100 caracteres y fundamento legal" (justificacion insuficiente)
- AUD-006: "Contrasena incorrecta" (password no coincide)
- AUD-007: "No tiene permisos para eliminar auditoria" (sin funcion audit.delete)

Confirmacion:

- OK-023: "Registros eliminados. Accion registrada permanentemente" (eliminacion exitosa)

Advertencias:

- WARN-016: "ADVERTENCIA CRITICA: Esta accion elimina registros de auditoria permanentemente" (confirmacion inicial)
- WARN-017: "La eliminacion quedara registrada permanentemente y es irreversible" (recordatorio)

Informativos:

- INFO-049: "Seleccione al menos un registro" (sin seleccion)
- INFO-050: "Se eliminaran X registros. Confirme con su contrasena" (confirmacion)

### IMPLEMENTACION TECNICA

**Eliminar registros de auditoria**

Endpoint: POST /api/v1/audit/delete

Request:

```json
{
  "log_ids": [12345, 12346, 12347],
  "justification": "Eliminacion conforme a Ley de Proteccion de Datos Personales. Solicitud de usuario ejerciendo derecho al olvido segun expediente legal LPD-2026-0123. Documentacion adjunta en sistema legal. Aprobado por departamento juridico.",
  "password": "contrasena_actual_usuario",
  "legal_document_reference": "LPD-2026-0123"
}
```

Response Exitosa (200 OK):

```json
{
  "success": true,
  "message": "Registros eliminados. Accion registrada permanentemente",
  "deletion_record": {
    "deletion_id": "DEL-2026-02-26-0001",
    "deleted_at": "2026-02-26T11:00:00Z",
    "deleted_by": 125,
    "deleted_by_username": "legal_admin",
    "records_deleted": 3,
    "log_ids": [12345, 12346, 12347],
    "justification": "Eliminacion conforme a Ley de Proteccion de Datos Personales...",
    "legal_document_reference": "LPD-2026-0123",
    "oldest_deleted_record": "2018-03-15T10:00:00Z",
    "newest_deleted_record": "2018-03-15T11:30:00Z",
    "deletion_log_id": 456
  },
  "warnings": [
    "Esta accion es IRREVERSIBLE",
    "Eliminacion registrada permanentemente en DeletionLog"
  ]
}
```

Response - Viola retencion (403 Forbidden):

```json
{
  "success": false,
  "error_code": "AUD-004",
  "message": "No se puede eliminar. Periodo de retencion obligatorio 7 anos",
  "oldest_record_date": "2020-06-15T10:00:00Z",
  "years_old": 5.7,
  "min_years_required": 7.0,
  "rejected_log_ids": [12345, 12346]
}
```

Response - Justificacion insuficiente (400 Bad Request):

```json
{
  "success": false,
  "error_code": "AUD-005",
  "message": "Justificacion debe tener al menos 100 caracteres y fundamento legal",
  "current_length": 75,
  "required_length": 100
}
```

Response - Contrasena incorrecta (401 Unauthorized):

```json
{
  "success": false,
  "error_code": "AUD-006",
  "message": "Contrasena incorrecta"
}
```

Response - Sin permisos (403 Forbidden):

```json
{
  "success": false,
  "error_code": "AUD-007",
  "message": "No tiene permisos para eliminar auditoria"
}
```

Codigos HTTP:

- 200 OK: Registros eliminados exitosamente
- 400 Bad Request: Justificacion insuficiente o sin registros
- 401 Unauthorized: Contrasena incorrecta
- 403 Forbidden: Sin permisos o viola retencion
- 500 Internal Server Error: Error del servidor

### VALIDACIONES

Validacion de Registros:

- log_ids: Lista de IDs validos
- Maximo 100 registros por operacion
- Todos deben existir en AuditLog

Validacion de Retencion:

- Para cada registro: timestamp >= NOW() - 7 anos
- Si alguno viola retencion: rechazar TODA la operacion
- Excepcion: Justificacion incluye "orden legal" o "tribunal"

Validacion de Justificacion:

- Obligatoria
- Minimo 100 caracteres
- Debe incluir fundamento legal claro
- Recomendado: numero de expediente o referencia legal

Validacion de Contrasena:

- Debe coincidir con contrasena actual del usuario
- Verificacion con PBKDF2
- Medida de seguridad adicional

Proceso de Eliminacion:

1. Validar contrasena del usuario
2. Validar justificacion (>= 100 caracteres)
3. Validar retencion para cada registro: si alguno tiene menos de 7 anos, rechazar todo
4. Crear registro PERMANENTE en DeletionLog: deletion_id, deleted_at, deleted_by, log_ids, justification, legal_document_reference
5. DELETE FROM AuditLog WHERE id IN (log_ids)
6. Registrar en AuditLog la accion de eliminacion

### AUDITORIA

Se registra en AuditLog:

- Accion: delete_audit_logs
- Usuario: user_id (quien elimina)
- Timestamp: hora exacta
- IP Address: IP desde donde elimina
- User Agent: navegador y dispositivo
- Detalles: deletion_id del DeletionLog, cantidad de registros eliminados, IDs eliminados, justificacion legal, referencia legal

Ejemplo de log:

```json
{
  "timestamp": "2026-02-26T11:00:00Z",
  "action": "delete_audit_logs",
  "user_id": 125,
  "ip_address": "192.168.1.102",
  "user_agent": "Chrome/120.0",
  "result": "success",
  "details": {
    "deletion_id": "DEL-2026-02-26-0001",
    "records_deleted": 3,
    "log_ids": [12345, 12346, 12347],
    "justification": "Eliminacion conforme a Ley de Proteccion de Datos Personales...",
    "legal_document_reference": "LPD-2026-0123",
    "oldest_deleted_record": "2018-03-15T10:00:00Z",
    "retention_compliance": true
  }
}
```

Tabla DeletionLog (INMUTABLE):

```sql
CREATE TABLE DeletionLog (
  id SERIAL PRIMARY KEY,
  deletion_id VARCHAR(50) UNIQUE NOT NULL,
  deleted_at TIMESTAMP NOT NULL,
  deleted_by INTEGER NOT NULL,
  log_ids INTEGER[] NOT NULL,
  justification TEXT NOT NULL,
  legal_document_reference VARCHAR(200),
  oldest_deleted_record TIMESTAMP,
  newest_deleted_record TIMESTAMP,
  records_count INTEGER NOT NULL
);

-- Esta tabla NO permite UPDATE ni DELETE
-- Solo INSERT permitido
```

### SEGURIDAD

Protecciones Implementadas:

- Justificacion legal muy estricta (100+ caracteres)
- Retencion obligatoria de 7 anos
- Confirmacion con contrasena actual
- Eliminacion registrada PERMANENTEMENTE en DeletionLog inmutable
- Tabla DeletionLog NO permite UPDATE ni DELETE
- Todas las eliminaciones auditadas
- Maximo 100 registros por operacion

Tabla DeletionLog Inmutable:

- Solo permite INSERT
- NO permite UPDATE
- NO permite DELETE
- Preserva evidencia permanente de toda eliminacion
- Accesible solo para auditoria legal

Casos Validos de Eliminacion:

- Cumplimiento de derecho al olvido (GDPR)
- Orden judicial o legal explicita
- Regulaciones de proteccion de datos personales
- Eliminacion de datos personales sensibles por ley
- Resolucion de autoridad regulatoria

Casos NO Validos:

- "Limpiar logs antiguos" - NO VALIDO
- "Liberar espacio" - NO VALIDO
- "Ocultar errores" - NO VALIDO
- "Borrar evidencia" - NO VALIDO

### NOTAS IMPORTANTES

ADVERTENCIA CRITICA: Esta funcion es EXTREMADAMENTE SENSIBLE. Solo debe usarse bajo circunstancias legales excepcionales:

- Orden judicial
- Derecho al olvido (GDPR/LPDA)
- Regulacion de proteccion de datos
- Resolucion de autoridad regulatoria

Retencion de 7 Anos:

- Obligatoria por compliance
- Solo se puede eliminar registros con 7 o mas anos de antiguedad
- Excepcion: Orden legal explicita documentada

Confirmacion con Contrasena:

- Medida de seguridad adicional
- Verifica identidad del usuario
- Previene eliminaciones accidentales
- Previene uso no autorizado si sesion comprometida

Tabla DeletionLog Inmutable:

- Proposito: Preservar evidencia permanente de eliminaciones
- Contenido: que se elimino (log_ids), quien lo elimino (deleted_by), cuando (deleted_at), por que (justification), referencia legal (legal_document_reference)
- Proteccion: solo INSERT permitido, NO UPDATE, NO DELETE
- Acceso solo para auditorias legales

Ejemplo de Justificacion Valida (mas de 100 caracteres con fundamento legal):

- "Eliminacion conforme a Ley de Proteccion de Datos Personales articulo 18. Solicitud formal de usuario ejerciendo derecho al olvido segun expediente legal LPD-2026-0123. Documentacion completa adjunta en sistema legal. Aprobado por departamento juridico."

Ejemplo de Justificacion Invalida:

- "Eliminar logs antiguos para liberar espacio"
- "Orden del jefe"
- "Ya no se necesitan"

Proceso Recomendado:

1. Recibir solicitud legal documentada
2. Revisar con departamento juridico
3. Obtener aprobacion formal
4. Documentar expediente legal
5. Ejecutar eliminacion con referencia legal
6. Archivar documentacion soporte
7. Notificar a compliance/auditoria

Limitaciones:

- Maximo 100 registros por operacion
- NO permite eliminar registros con menos de 7 anos (excepto orden legal)
- Eliminacion es irreversible
- No hay funcion de restaurar

Responsabilidad Legal:

- Usuario que elimina asume responsabilidad
- Justificacion debe ser legalmente defendible
- Eliminacion incorrecta puede tener consecuencias legales
- Coordinacion con juridico es OBLIGATORIA

---

Sistema IACT - Analisis IVR
Version: 1.0.0 | Fecha documento: 2026-03-14 | Modelo RBAC: v7.0.0
