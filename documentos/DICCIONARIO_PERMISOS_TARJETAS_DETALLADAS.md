# DICCIONARIO DE PERMISOS - TARJETAS DETALLADAS

Sistema IACT - Analisis IVR
Version: 1.0.0
Fecha: 2026-03-10
Modelo RBAC: v7.0.0
Formato: Tarjetas Individuales por Funcion

---

## INFORMACIÓN GENERAL

Este diccionario documenta las 46 funciones atómicas del sistema IACT mediante tarjetas detalladas que especifican QUÉ HACE cada función, sin roles predefinidos.

Estado actual: 25 de 46 funciones documentadas (54.3%)

---

## MÓDULOS COMPLETADOS

- MOD_Auth - Autenticación (4/4 funciones - 100%)
- MOD_Users - Gestión de Usuarios (9/9 funciones - 100%)
- MOD_Access - Gestión de Permisos (3/3 funciones - 100%)
- MOD_Reports - Reportes y Análisis (6/6 funciones - 100%)
- MOD_Audit - Auditoría y Compliance (3/3 funciones - 100%)

---

## ÍNDICE DE FUNCIONES DOCUMENTADAS

### MOD_Auth - Autenticación (4)
1. auth.login - Iniciar Sesión
2. auth.logout - Cerrar Sesión
3. auth.recover_password - Recuperar Contraseña
4. auth.manage_sessions - Gestionar Sesiones

### MOD_Users - Gestión de Usuarios (9)
1. users.view - Ver Usuarios
2. users.create - Crear Usuarios
3. users.edit - Editar Usuarios
4. users.delete - Eliminar Usuarios
5. users.reset_password - Resetear Contraseña
6. users.lock - Bloquear Usuario
7. users.unlock - Desbloquear Usuario
8. users.search - Buscar Usuarios
9. users.export - Exportar Usuarios

### MOD_Access - Gestión de Permisos (3)
1. access.view - Ver Funciones Asignadas
2. access.assign - Asignar Funciones (SoD 1)
3. access.revoke - Revocar Funciones (SoD 1)

### MOD_Reports - Reportes y Análisis (6)
1. reports.view_basic - Ver Reportes Básicos
2. reports.view_advanced - Ver Reportes Avanzados
3. reports.export - Exportar Reportes
4. reports.modify_data - Modificar Datos de Reportes (SoD 3)
5. reports.approve - Aprobar Modificaciones de Reportes (SoD 3)
6. reports.schedule - Programar Reportes

### MOD_Audit - Auditoría y Compliance (3)
1. audit.view - Ver Auditoría (SoD 2)
2. audit.search - Buscar en Auditoría (SoD 2)
3. audit.delete - Eliminar Registros de Auditoría

---

## REGLAS DE SEGREGACIÓN DE FUNCIONES (SoD)

### SoD 1 - function_assignment_control:
- `access.assign` INCOMPATIBLE con `access.revoke`
- Razon: Separación de poderes en gestión de permisos

### SoD 2 - user_audit_separation:
- `users.create`, `users.edit`, `users.delete` INCOMPATIBLES con `audit.view`, `audit.search`
- Razon: Quien gestiona usuarios NO debe auditar sus propias acciones

### SoD 3 - report_data_separation:
- `reports.modify_data` INCOMPATIBLE con `reports.approve`
- Razon: Quien modifica datos NO debe aprobar sus propias modificaciones

---

## PRINCIPIOS DEL MODELO RBAC v7.0.0

1. Asignación Directa: Usuario -> Funciones (sin grupos intermedios)
2. Funciones Atómicas: 46 funciones granulares
3. QUÉ HACE, NO QUIÉN ES: Funciones describen acciones, no roles
4. Flat RBAC: Sin jerarquías
5. 3 Reglas SoD: Separación obligatoria de funciones incompatibles

---

## TARJETA: users.view

Nombre para UI: Ver Usuarios
Modulo: MOD_Users - Gestión de Usuarios
ID Caso de Uso: UC-006 | Prioridad: ALTA | Frecuencia: Diaria | Estado: Activo

### DESCRIPCIÓN
Permite consultar la lista de usuarios del sistema con sus datos básicos. Los usuarios se muestran con información general como username, email, nombre completo, estado de la cuenta y última actividad. La vista puede filtrarse por diferentes criterios.

### PRECONDICIONES
- Usuario tiene sesión activa
- Usuario tiene función `users.view` asignada

### FLUJO PRINCIPAL (8 PASOS)
1. Usuario navega a sección "Usuarios" o "Gestión de Usuarios"
2. Sistema carga lista de usuarios
3. Sistema aplica filtros por objeto según área del usuario (si aplica)
4. Sistema muestra lista paginada de usuarios
5. Usuario puede ordenar por columna (username, email, fecha creación)
6. Usuario puede filtrar por estado (activo, inactivo, bloqueado)
7. Usuario puede buscar por texto (username, email, nombre)
8. Sistema actualiza lista según filtros aplicados

### FLUJOS ALTERNATIVOS

A1. Sin usuarios encontrados (paso 4)
- Sistema no encuentra usuarios con los filtros aplicados
- Sistema muestra mensaje: "No se encontraron usuarios"
- Usuario puede limpiar filtros o cambiar criterios

A2. Usuario sin función users.view (paso 2)
- Sistema detecta que usuario no tiene función
- Sistema muestra error 403: "No tiene permisos para ver usuarios"
- Usuario es redirigido a página anterior

A3. Exportar lista (desde paso 4)
- Usuario hace clic en "Exportar"
- Sistema verifica si usuario tiene `users.export`
- Si NO tiene: muestra error "Requiere función users.export"
- Si SÍ tiene: genera archivo CSV con usuarios

### POSTCONDICIONES
Exito:
- Lista de usuarios mostrada
- Filtros aplicados correctamente

Fallo:
- Si no tiene permisos, no accede a la lista

### REGLAS DE NEGOCIO
- RN-026: Usuario solo ve usuarios de su área (si aplica filtro por objeto)
- RN-027: Administradores ven todos los usuarios
- RN-028: Lista paginada de 25 usuarios por página
- RN-029: Datos sensibles (teléfono, dirección) no se muestran sin función adicional

### RESTRICCIONES TÉCNICAS
- CNST-011: Username único, alfanumérico, 3-30 caracteres
- CNST-012: Email único, formato válido
- CNST-013: Usuario inactivo tras 90 días sin login

### REGLAS SoD
Ninguna

### MENSAJES DEL SISTEMA
Errores:
- `USR-001`: "No tiene permisos para ver usuarios"
- `USR-002`: "Requiere función users.export para exportar"

Informativos:
- `INFO-007`: "No se encontraron usuarios"
- `INFO-008`: "Mostrando X de Y usuarios"

### IMPLEMENTACIÓN TÉCNICA
Endpoint: `GET /api/v1/users`

Query Parameters:
```
?page=1
&page_size=25
&search=juan
&status=active
&order_by=username
&order=asc
&area=Comercial
```

Response Exitosa (200 OK):
```json
{
  "success": true,
  "users": [
    {
      "id": 1,
      "username": "juanperez",
      "email": "juan.perez@empresa.com",
      "first_name": "Juan",
      "last_name": "Pérez",
      "is_active": true,
      "is_locked": false,
      "locked_until": null,
      "last_login": "2026-02-24T10:30:00Z",
      "date_joined": "2025-01-15T08:00:00Z",
      "area": "Comercial",
      "functions_count": 12
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 25,
    "total_users": 47,
    "total_pages": 2
  },
  "filters_applied": {
    "search": "juan",
    "status": "active",
    "area": null
  }
}
```

Codigos HTTP:
- `200 OK`: Consulta exitosa
- `403 Forbidden`: Sin función users.view
- `500 Internal Server Error`: Error del servidor

### VALIDACIONES
- `page`: Entero positivo, mínimo 1
- `page_size`: Entero positivo, máximo 100
- `status`: valores permitidos: `active`, `inactive`, `locked`, `all`
- `order_by`: valores permitidos: `username`, `email`, `last_login`, `date_joined`

### AUDITORÍA
```json
{
  "timestamp": "2026-02-24T15:00:00Z",
  "action": "view_users",
  "user_id": 123,
  "ip_address": "192.168.1.100",
  "user_agent": "Chrome/120.0",
  "result": "success",
  "details": {
    "filters": {"search": "juan", "status": "active", "area": "Comercial"},
    "results_count": 3,
    "page": 1
  }
}
```

---

## TARJETA: users.create

Nombre para UI: Crear Usuarios
Modulo: MOD_Users - Gestión de Usuarios
ID Caso de Uso: UC-006 | Prioridad: ALTA | Frecuencia: Semanal | Estado: Activo

### DESCRIPCIÓN
Permite crear nuevas cuentas de usuario en el sistema especificando datos básicos requeridos: username, email, nombre completo. El usuario creado se genera con estado activo por defecto y sin funciones asignadas.

### PRECONDICIONES
- Usuario tiene sesión activa
- Usuario tiene función `users.create` asignada
- Datos del nuevo usuario disponibles (username, email, nombre)

### FLUJO PRINCIPAL (15 PASOS)
1. Usuario navega a sección "Crear Usuario"
2. Sistema muestra formulario de creación
3. Usuario ingresa username (3-30 caracteres alfanuméricos)
4. Usuario ingresa email (formato válido)
5. Usuario ingresa nombre (first_name)
6. Usuario ingresa apellido (last_name)
7. Usuario selecciona área asignada
8. Usuario hace clic en "Crear Usuario"
9. Sistema valida formato de username (CNST-011)
10. Sistema valida que username sea único
11. Sistema valida formato de email (CNST-012)
12. Sistema valida que email sea único
13. Sistema genera contraseña temporal aleatoria
14. Sistema crea cuenta con estado activo
15. Sistema muestra confirmación con username y contraseña temporal

### REGLAS SoD
- SoD 2 - Grupo A (user_audit_separation)
- INCOMPATIBLE con: `audit.view`, `audit.search`
- Razon: Quien crea usuarios NO debe auditar sus propias acciones

### IMPLEMENTACIÓN TÉCNICA
Endpoint: `POST /api/v1/users`

Request:
```json
{
  "username": "plopez",
  "email": "pedro.lopez@empresa.com",
  "first_name": "Pedro",
  "last_name": "López",
  "area": "Soporte"
}
```

Response Exitosa (201 Created):
```json
{
  "success": true,
  "message": "Usuario creado exitosamente",
  "user": {
    "id": 150,
    "username": "plopez",
    "email": "pedro.lopez@empresa.com",
    "first_name": "Pedro",
    "last_name": "López",
    "is_active": true,
    "is_locked": false,
    "area": "Soporte",
    "date_joined": "2026-02-24T16:00:00Z",
    "last_login": null,
    "functions_count": 0
  },
  "temporary_password": "Abc123XyZ"
}
```

Codigos HTTP:
- `201 Created`: Usuario creado exitosamente
- `400 Bad Request`: Datos inválidos o duplicados
- `403 Forbidden`: Sin función users.create
- `500 Internal Server Error`: Error del servidor

---

## TARJETA: users.edit

Nombre para UI: Editar Usuarios
Modulo: MOD_Users - Gestión de Usuarios
ID Caso de Uso: UC-007 | Prioridad: ALTA | Frecuencia: Semanal | Estado: Activo

### DESCRIPCIÓN
Permite modificar datos de usuarios existentes: email, nombre completo, área asignada. El username NO puede modificarse una vez creado.

### REGLAS SoD
- SoD 2 - Grupo A (user_audit_separation)
- INCOMPATIBLE con: `audit.view`, `audit.search`

### IMPLEMENTACIÓN TÉCNICA
Endpoint: `PATCH /api/v1/users/{user_id}`

Request:
```json
{
  "email": "pedro.lopez.nuevo@empresa.com",
  "first_name": "Pedro Antonio",
  "last_name": "López García",
  "area": "Finanzas"
}
```

Response Exitosa (200 OK):
```json
{
  "success": true,
  "message": "Usuario actualizado exitosamente",
  "user": { "id": 150, "username": "plopez" },
  "changes_made": [
    {"field": "email", "old_value": "pedro.lopez@empresa.com", "new_value": "pedro.lopez.nuevo@empresa.com"},
    {"field": "area", "old_value": "Soporte", "new_value": "Finanzas"}
  ]
}
```

Campos NO Modificables: username, id, date_joined, is_active, is_locked, funciones

---

## TARJETA: users.delete

Nombre para UI: Eliminar Usuarios
Modulo: MOD_Users - Gestión de Usuarios
ID Caso de Uso: UC-008 | Prioridad: ALTA | Frecuencia: Ocasional | Estado: Activo

### DESCRIPCIÓN
Permite eliminar usuarios del sistema mediante soft delete (is_active=false). El usuario no se elimina físicamente. Requiere justificación obligatoria (mín. 20 caracteres).

### REGLAS DE NEGOCIO
- RN-043: Soft delete obligatorio (NO eliminación física)
- RN-044: Usuario NO puede eliminar su propia cuenta
- RN-045: Justificación obligatoria mínimo 20 caracteres
- RN-046: Todas las sesiones del usuario se invalidan
- RN-047: Todas las funciones del usuario se revocan
- RN-048: Datos se preservan para auditoría (CNST-014)

### REGLAS SoD
- SoD 2 - Grupo A (user_audit_separation)
- INCOMPATIBLE con: `audit.view`, `audit.search`

### IMPLEMENTACIÓN TÉCNICA
Endpoint: `DELETE /api/v1/users/{user_id}`

Request:
```json
{
  "justification": "Usuario solicitó baja voluntaria del sistema. Ticket RRHH-2024-0156."
}
```

---

## TARJETA: users.reset_password

Nombre para UI: Resetear Contraseña
Modulo: MOD_Users - Gestión de Usuarios
ID Caso de Uso: UC-009 | Prioridad: ALTA | Frecuencia: Ocasional | Estado: Activo

### DESCRIPCIÓN
Permite a un administrador resetear la contraseña de un usuario generando una nueva contraseña temporal. Todas las sesiones activas se invalidan automáticamente. Requiere justificación (mín. 20 caracteres).

### REGLAS SoD
- SoD 2 - Grupo A (user_audit_separation)
- INCOMPATIBLE con: `audit.view`, `audit.search`

### IMPLEMENTACIÓN TÉCNICA
Endpoint: `POST /api/v1/users/{user_id}/reset-password`

---

## TARJETA: users.lock

Nombre para UI: Bloquear Usuario
Modulo: MOD_Users - Gestión de Usuarios
ID Caso de Uso: UC-010 | Prioridad: ALTA | Frecuencia: Ocasional | Estado: Activo

### DESCRIPCIÓN
Permite bloquear temporalmente una cuenta de usuario. El bloqueo es temporal (por defecto 15 minutos). Las sesiones activas NO se invalidan automáticamente.

### REGLAS SoD
Ninguna

### IMPLEMENTACIÓN TÉCNICA
Endpoint: `POST /api/v1/users/{user_id}/lock`

Request:
```json
{
  "duration_minutes": 15,
  "reason": "Actividad sospechosa detectada. Revisión de seguridad pendiente. Ticket SEC-2024-0123."
}
```

Opciones de duration_minutes: 15, 60, 1440, 0 (indefinido)

---

## TARJETA: users.unlock

Nombre para UI: Desbloquear Usuario
Modulo: MOD_Users - Gestión de Usuarios
ID Caso de Uso: UC-011 | Prioridad: ALTA | Frecuencia: Ocasional | Estado: Activo

### DESCRIPCIÓN
Permite desbloquear manualmente una cuenta de usuario bloqueada (ya sea por bloqueo manual o automático por intentos fallidos).

### REGLAS SoD
Ninguna

### IMPLEMENTACIÓN TÉCNICA
Endpoint: `POST /api/v1/users/{user_id}/unlock`

---

## TARJETA: users.search

Nombre para UI: Buscar Usuarios
Modulo: MOD_Users - Gestión de Usuarios
ID Caso de Uso: UC-012 | Prioridad: MEDIA | Frecuencia: Diaria | Estado: Activo

### DESCRIPCIÓN
Permite buscar usuarios con criterios avanzados: username, email, nombre, área, estado, rango de fechas. Complementa a `users.view`.

### REGLAS SoD
Ninguna

### IMPLEMENTACIÓN TÉCNICA
Endpoint: `GET /api/v1/users/search`

---

## TARJETA: users.export

Nombre para UI: Exportar Usuarios
Modulo: MOD_Users - Gestión de Usuarios
ID Caso de Uso: UC-013 | Prioridad: MEDIA | Frecuencia: Semanal | Estado: Activo

### DESCRIPCIÓN
Permite exportar la lista de usuarios a CSV. Limitada a máximo 10,000 registros (CNST-010).

### RESTRICCIONES TÉCNICAS
- CNST-010: Exportación máximo 10,000 registros por operación

### IMPLEMENTACIÓN TÉCNICA
Endpoint: `GET /api/v1/users/export`

---

## TARJETA: access.view

Nombre para UI: Ver Funciones Asignadas
Modulo: MOD_Access - Gestión de Permisos
ID Caso de Uso: UC-014 | Prioridad: ALTA | Frecuencia: Diaria | Estado: Activo

### DESCRIPCIÓN
Permite consultar las funciones asignadas a un usuario: cuándo fueron asignadas, quién las asignó, si están activas o revocadas.

### REGLAS SoD
Ninguna

### IMPLEMENTACIÓN TÉCNICA
Endpoint: `GET /api/v1/users/{user_id}/functions`

---

## TARJETA: access.assign

Nombre para UI: Asignar Funciones
Modulo: MOD_Access - Gestión de Permisos
ID Caso de Uso: UC-015 | Prioridad: CRÍTICA | Frecuencia: Semanal | Estado: Activo

### DESCRIPCIÓN
Permite asignar una o varias funciones a un usuario. Valida reglas SoD antes de asignar. Operación atómica: todas o ninguna si hay violación SoD.

### REGLAS SoD
- SoD 1 (function_assignment_control)
- INCOMPATIBLE con: `access.revoke`
- Razon: Quien asigna funciones NO puede revocarlas

### IMPLEMENTACIÓN TÉCNICA
Endpoint: `POST /api/v1/users/{user_id}/functions/assign`

Request:
```json
{
  "function_codes": ["users.view", "users.search", "reports.view_basic"],
  "justification": "Nuevo analista de datos. Requiere acceso a usuarios y reportes básicos. Aprobado por gerente RRHH ticket HR-2024-0456."
}
```

Response - Violación SoD (400):
```json
{
  "success": false,
  "error_code": "ACC-004",
  "message": "Violación de regla SoD 2: user_audit_separation",
  "details": {
    "rule_violated": "SoD 2 - user_audit_separation",
    "incompatible_functions": [
      {
        "attempting_to_assign": "users.create",
        "conflicts_with": "audit.view",
        "reason": "Quien crea usuarios NO debe auditar sus propias acciones"
      }
    ]
  }
}
```

---

## TARJETA: access.revoke

Nombre para UI: Revocar Funciones
Modulo: MOD_Access - Gestión de Permisos
ID Caso de Uso: UC-016 | Prioridad: CRÍTICA | Frecuencia: Ocasional | Estado: Activo

### DESCRIPCIÓN
Permite revocar funciones asignadas a un usuario. Soft delete del registro (preserva con `revoked_at`). Requiere justificación (mín. 20 caracteres).

### REGLAS SoD
- SoD 1 (function_assignment_control)
- INCOMPATIBLE con: `access.assign`

### IMPLEMENTACIÓN TÉCNICA
Endpoint: `POST /api/v1/users/{user_id}/functions/revoke`

---

## TARJETA: reports.view_basic

Nombre para UI: Ver Reportes Básicos
Modulo: MOD_Reports - Reportes y Análisis
ID Caso de Uso: UC-017 | Prioridad: ALTA | Frecuencia: Diaria | Estado: Activo

### DESCRIPCIÓN
Permite consultar reportes básicos del sistema IVR con información agregada. Rango máximo 31 dias. Solo lectura (SELECT en BD IVR).

### RESTRICCIONES TÉCNICAS
- CNST-003: Base IVR es READ-ONLY (solo SELECT)
- CNST-009: Timeout 30 segundos

### REGLAS SoD
Ninguna

### IMPLEMENTACIÓN TÉCNICA
Endpoint: `GET /api/v1/reports/basic/{report_type}`

Reportes disponibles: calls_by_queue, daily_summary, calls_by_hour, ivr_options_usage, queue_performance

---

## TARJETA: reports.view_advanced

Nombre para UI: Ver Reportes Avanzados
Modulo: MOD_Reports - Reportes y Análisis
ID Caso de Uso: UC-018 | Prioridad: ALTA | Frecuencia: Semanal | Estado: Activo

### DESCRIPCIÓN
Permite reportes avanzados con datos detallados por llamada individual. Sin límite de rango de fechas. Drill-down disponible. Timeout extendido 60 segundos.

### REGLAS SoD
Ninguna

### IMPLEMENTACIÓN TÉCNICA
Endpoint: `GET /api/v1/reports/advanced/{report_type}`

---

## TARJETA: reports.export

Nombre para UI: Exportar Reportes
Modulo: MOD_Reports - Reportes y Análisis
ID Caso de Uso: UC-019 | Prioridad: MEDIA | Frecuencia: Semanal | Estado: Activo

### DESCRIPCIÓN
Permite exportar reportes IVR a CSV o Excel. Limitada a 10,000 registros (CNST-010).

### IMPLEMENTACIÓN TÉCNICA
Endpoint: `GET /api/v1/reports/export`

---

## TARJETA: reports.modify_data

Nombre para UI: Modificar Datos de Reportes
Modulo: MOD_Reports - Reportes y Análisis
ID Caso de Uso: UC-020 | Prioridad: CRÍTICA | Frecuencia: Ocasional | Estado: Activo

### DESCRIPCIÓN
Permite modificar datos en la base Analytics (PostgreSQL). NUNCA modifica la base IVR. Las modificaciones quedan en estado "pendiente_aprobacion" hasta que `reports.approve` las valide. Requiere justificación mínimo 30 caracteres.

### REGLAS SoD
- SoD 3 (report_data_separation)
- INCOMPATIBLE con: `reports.approve`
- Razon: Quien modifica datos NO puede aprobar sus propias modificaciones

### IMPLEMENTACIÓN TÉCNICA
Endpoint: `POST /api/v1/reports/modify-data`

Tablas Modificables (Analytics PostgreSQL): call_metrics, categorizations, quality_scores, custom_tags

Base IVR (MariaDB): INMUTABLE - absolutamente prohibido modificar

---

## TARJETA: reports.approve

Nombre para UI: Aprobar Modificaciones de Reportes
Modulo: MOD_Reports - Reportes y Análisis
ID Caso de Uso: UC-021 | Prioridad: CRÍTICA | Frecuencia: Ocasional | Estado: Activo

### DESCRIPCIÓN
Permite aprobar o rechazar modificaciones pendientes creadas por `reports.modify_data`. Implementa dual control. Usuario NO puede aprobar sus propias modificaciones.

### REGLAS SoD
- SoD 3 (report_data_separation)
- INCOMPATIBLE con: `reports.modify_data`

### IMPLEMENTACIÓN TÉCNICA
Endpoint: `POST /api/v1/reports/approve-modification`

Estados de modificacion: pendiente_aprobacion -> aprobado / rechazado

---

## TARJETA: reports.schedule

Nombre para UI: Programar Reportes
Modulo: MOD_Reports - Reportes y Análisis
ID Caso de Uso: UC-022 | Prioridad: MEDIA | Frecuencia: Ocasional | Estado: Activo

### DESCRIPCIÓN
Permite programar generación automática de reportes (diaria, semanal, mensual). Los reportes se entregan por mensaje interno a destinatarios especificados. Máximo 10 reportes activos por usuario.

### REGLAS SoD
Ninguna

### IMPLEMENTACIÓN TÉCNICA
Endpoint: `POST /api/v1/reports/schedule`

Frecuencias: daily, weekly, monthly

Rangos relativos: last_7_days, last_30_days, last_week, last_month

---

## TARJETA: audit.view

Nombre para UI: Ver Auditoría
Modulo: MOD_Audit - Auditoría y Compliance
ID Caso de Uso: UC-023 | Prioridad: ALTA | Frecuencia: Semanal | Estado: Activo

### DESCRIPCIÓN
Permite consultar registros de auditoría. Rango máximo 90 dias. Solo lectura. Logs se preservan mínimo 7 anos.

### REGLAS SoD
- SoD 2 - Grupo AUDIT (user_audit_separation)
- INCOMPATIBLE con: `users.create`, `users.edit`, `users.delete`

### IMPLEMENTACIÓN TÉCNICA
Endpoint: `GET /api/v1/audit/logs`

---

## TARJETA: audit.search

Nombre para UI: Buscar en Auditoría
Modulo: MOD_Audit - Auditoría y Compliance
ID Caso de Uso: UC-024 | Prioridad: MEDIA | Frecuencia: Ocasional | Estado: Activo

### DESCRIPCIÓN
Búsqueda avanzada en auditoría sin límite temporal (acceso histórico completo). Soporta búsqueda en campos JSON de detalles. Máximo 10,000 resultados.

### REGLAS SoD
- SoD 2 - Grupo AUDIT (user_audit_separation)
- INCOMPATIBLE con: `users.create`, `users.edit`, `users.delete`

### IMPLEMENTACIÓN TÉCNICA
Endpoint: `GET /api/v1/audit/search`

---

## TARJETA: audit.delete

Nombre para UI: Eliminar Registros de Auditoría
Modulo: MOD_Audit - Auditoría y Compliance
ID Caso de Uso: UC-025 | Prioridad: CRÍTICA | Frecuencia: Muy Ocasional | Estado: Activo

### DESCRIPCIÓN
FUNCION MUY RESTRINGIDA. Permite eliminar registros de auditoría bajo circunstancias legales excepcionales. Requiere:
- Justificación legal mínimo 100 caracteres
- Confirmación con contraseña actual
- Registros deben tener minimo 7 anos (CNST-015)
- Eliminación queda registrada en tabla DeletionLog INMUTABLE

### RESTRICCIONES TÉCNICAS
- CNST-015: Retención mínima 7 años
- Máximo 100 registros por operación
- Eliminación IRREVERSIBLE

### REGLAS SoD
Ninguna (función tan restringida que no requiere SoD adicional)

### IMPLEMENTACIÓN TÉCNICA
Endpoint: `POST /api/v1/audit/delete`

Request:
```json
{
  "log_ids": [12345, 12346, 12347],
  "justification": "Eliminación conforme a Ley de Protección de Datos Personales. Solicitud de usuario ejerciendo derecho al olvido según expediente legal LPD-2026-0123. Documentación adjunta en sistema legal. Aprobado por departamento jurídico.",
  "password": "contraseña_actual_usuario",
  "legal_document_reference": "LPD-2026-0123"
}
```

Tabla DeletionLog:
```sql
CREATE TABLE DeletionLog (
  id SERIAL PRIMARY KEY,
  deletion_id VARCHAR(50) UNIQUE NOT NULL,
  deleted_at TIMESTAMP NOT NULL,
  deleted_by INTEGER NOT NULL,
  log_ids INTEGER[] NOT NULL,
  justification TEXT NOT NULL,
  legal_document_reference VARCHAR(200),
  records_count INTEGER NOT NULL
);
-- Solo INSERT permitido. NO UPDATE. NO DELETE.
```

---

Documento: DICCIONARIO DE PERMISOS - TARJETAS DETALLADAS
Sistema IACT - Analisis IVR
Version: 1.0.0 | Fecha documento: 2026-03-10 | Modelo RBAC: v7.0.0
