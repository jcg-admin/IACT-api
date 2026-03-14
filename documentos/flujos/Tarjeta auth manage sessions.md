## TARJETA: auth.manage_sessions

Nombre para UI: Gestionar Sesiones
Modulo: MOD_Auth - Autenticacion
ID Caso de Uso: No documentado en E1
Prioridad: MEDIA
Frecuencia: Ocasional
Estado: Activo

### DESCRIPCION

Permite al usuario ver todas sus sesiones activas en diferentes dispositivos y cerrar sesiones especificas de forma remota. Esto es util para controlar el acceso a la cuenta desde multiples dispositivos y cerrar sesiones olvidadas o no reconocidas.

### PRECONDICIONES

- Usuario tiene sesion activa
- Usuario esta autenticado

### FLUJO PRINCIPAL (10 PASOS)

1. Usuario navega a seccion "Gestionar Sesiones" o "Dispositivos Activos"
2. Sistema carga todas las sesiones activas del usuario
3. Sistema muestra lista de sesiones con detalles
4. Usuario revisa sesiones activas
5. Usuario identifica sesion a cerrar
6. Usuario hace clic en boton "Cerrar Sesion" junto a la sesion especifica
7. Sistema muestra confirmacion: "Desea cerrar esta sesion?"
8. Usuario confirma
9. Sistema invalida la sesion seleccionada
10. Sistema actualiza lista de sesiones activas

### FLUJOS ALTERNATIVOS

**A1. Usuario cancela cierre (paso 8)**

- Usuario hace clic en "Cancelar"
- Sistema cierra dialogo
- Lista de sesiones permanece sin cambios
- Caso de uso termina

**A2. Cerrar todas las demas sesiones (desde paso 4)**

- Usuario hace clic en "Cerrar Todas las Demas Sesiones"
- Sistema muestra confirmacion: "Desea cerrar todas las sesiones excepto la actual?"
- Usuario confirma
- Sistema invalida todas las sesiones excepto la actual
- Sistema actualiza lista mostrando solo sesion actual
- Caso de uso termina

**A3. No hay otras sesiones activas (paso 3)**

- Sistema detecta que solo hay sesion actual
- Sistema muestra mensaje: "Solo tiene una sesion activa (esta sesion)"
- No muestra opciones de cerrar otras sesiones
- Caso de uso termina

**A4. Sesion ya expirada (paso 9)**

- Sistema detecta que sesion seleccionada ya expiro
- Sistema la marca como inactiva
- Sistema actualiza lista automaticamente
- Sistema muestra mensaje: "Sesion ya expirada"
- Caso de uso continua

**A5. Intentar cerrar sesion actual (paso 6)**

- Usuario intenta cerrar su sesion actual
- Sistema detecta que es la sesion actual
- Sistema muestra advertencia: "Esta es su sesion actual. Use 'Cerrar Sesion' del menu principal"
- Sistema NO permite cerrar sesion actual desde gestion
- Caso de uso continua

### POSTCONDICIONES

Exito:

- Sesion(es) seleccionada(s) invalidada(s)
- Lista de sesiones actualizada
- Usuario permanece autenticado en sesion actual

Fallo:

- Si hay error tecnico, sesion actual permanece activa
- Usuario puede reintentar operacion

### REGLAS DE NEGOCIO

- RN-020: Usuario puede tener maximo 5 sesiones simultaneas
- RN-021: Al crear sesion numero 6, se invalida automaticamente la mas antigua
- RN-022: Usuario NO puede cerrar su sesion actual desde gestion de sesiones
- RN-023: Usuario puede ver todas sus sesiones activas
- RN-024: Usuario solo puede cerrar sus propias sesiones
- RN-025: Cerrar sesion es irreversible (requiere nuevo login)

### RESTRICCIONES TECNICAS

- CNST-002: Sesiones almacenadas en base de datos PostgreSQL
  - Tabla: UserSession
  - Timeout: 8 horas absoluto
  - Maximo 5 sesiones concurrentes

### REGLAS SoD

Ninguna

### MENSAJES DEL SISTEMA

Confirmacion:

- SES-005: "Sesion cerrada exitosamente" (sesion remota cerrada)
- SES-006: "Todas las demas sesiones han sido cerradas" (cierre masivo)

Errores:

- SES-004: "Ha alcanzado el limite de sesiones simultaneas" (al intentar crear sesion numero 6)
- SES-007: "No puede cerrar su sesion actual desde aqui" (intenta cerrar sesion actual)

Informativos:

- INFO-005: "Solo tiene una sesion activa (esta sesion)" (sin otras sesiones)
- INFO-006: "Sesion ya expirada" (sesion seleccionada expiro)

### IMPLEMENTACION TECNICA

**Listar sesiones activas**

Endpoint: GET /api/v1/auth/sessions

Response (200 OK):

```json
{
  "success": true,
  "sessions": [
    {
      "session_id": "abc123xyz",
      "is_current": true,
      "device": "Chrome en Windows",
      "ip_address": "192.168.1.100",
      "location": "Guadalajara, Mexico",
      "created_at": "2026-02-24T10:30:00Z",
      "last_activity": "2026-02-24T15:45:00Z",
      "expires_at": "2026-02-24T18:30:00Z"
    },
    {
      "session_id": "def456uvw",
      "is_current": false,
      "device": "Safari en iPhone",
      "ip_address": "192.168.1.105",
      "location": "Guadalajara, Mexico",
      "created_at": "2026-02-23T08:15:00Z",
      "last_activity": "2026-02-24T12:20:00Z",
      "expires_at": "2026-02-24T16:15:00Z"
    },
    {
      "session_id": "ghi789rst",
      "is_current": false,
      "device": "Firefox en Linux",
      "ip_address": "201.123.45.67",
      "location": "Ciudad de Mexico, Mexico",
      "created_at": "2026-02-22T14:00:00Z",
      "last_activity": "2026-02-24T09:30:00Z",
      "expires_at": "2026-02-24T22:00:00Z"
    }
  ],
  "total_sessions": 3,
  "max_sessions": 5
}
```

**Cerrar sesion especifica**

Endpoint: DELETE /api/v1/auth/sessions/{session_id}

Request:

```
DELETE /api/v1/auth/sessions/def456uvw
```

Response Exitosa (200 OK):

```json
{
  "success": true,
  "message": "Sesion cerrada exitosamente",
  "session_id": "def456uvw",
  "sessions_remaining": 2
}
```

Response - Intentar cerrar sesion actual (400 Bad Request):

```json
{
  "success": false,
  "error_code": "SES-007",
  "message": "No puede cerrar su sesion actual desde aqui"
}
```

Response - Sesion no existe (404 Not Found):

```json
{
  "success": false,
  "error_code": "SES-008",
  "message": "Sesion no encontrada o ya expirada"
}
```

**Cerrar todas las demas sesiones**

Endpoint: DELETE /api/v1/auth/sessions/others

Response Exitosa (200 OK):

```json
{
  "success": true,
  "message": "Todas las demas sesiones han sido cerradas",
  "sessions_closed": 4,
  "sessions_remaining": 1
}
```

Response - Sin otras sesiones (200 OK):

```json
{
  "success": true,
  "message": "No hay otras sesiones activas para cerrar",
  "sessions_closed": 0,
  "sessions_remaining": 1
}
```

Codigos HTTP:

- 200 OK: Operacion exitosa
- 400 Bad Request: Intento de cerrar sesion actual
- 404 Not Found: Sesion no existe
- 500 Internal Server Error: Error del servidor

### VALIDACIONES

Validacion de Sesion:

- Sesion existe en base de datos
- Sesion pertenece al usuario autenticado
- Sesion NO es la sesion actual (para cierre individual)

Validacion de Propiedad:

- Usuario solo puede ver y cerrar sus propias sesiones
- No puede acceder a sesiones de otros usuarios

Limite de Sesiones:

- Sistema mantiene maximo 5 sesiones activas
- Al crear sesion numero 6, invalida automaticamente la mas antigua

### AUDITORIA

Se registra en AuditLog:

- Accion: close_remote_session
- Usuario: user_id
- Timestamp: hora exacta
- IP Address: IP desde donde se solicita cierre
- User Agent: navegador y dispositivo
- Detalles: session_id cerrado, IP de la sesion cerrada, dispositivo de la sesion cerrada, si fue cierre individual o masivo

Ejemplo de log - Cerrar sesion individual:

```json
{
  "timestamp": "2026-02-24T15:45:00Z",
  "action": "close_remote_session",
  "user_id": 123,
  "ip_address": "192.168.1.100",
  "user_agent": "Chrome/120.0",
  "result": "success",
  "details": {
    "closed_session_id": "def456uvw",
    "closed_session_ip": "192.168.1.105",
    "closed_session_device": "Safari en iPhone",
    "closure_type": "individual"
  }
}
```

Ejemplo de log - Cerrar todas las demas:

```json
{
  "timestamp": "2026-02-24T15:50:00Z",
  "action": "close_all_other_sessions",
  "user_id": 123,
  "ip_address": "192.168.1.100",
  "user_agent": "Chrome/120.0",
  "result": "success",
  "details": {
    "sessions_closed": 4,
    "session_ids": ["def456uvw", "ghi789rst", "jkl012mno", "pqr345stu"],
    "closure_type": "bulk"
  }
}
```

### SEGURIDAD

Protecciones Implementadas:

- Usuario solo ve sus propias sesiones
- Usuario solo puede cerrar sus propias sesiones
- Sesion actual no puede cerrarse desde gestion (previene cierre accidental)
- Todas las acciones son auditadas
- Informacion de ubicacion basada en IP (aproximada)

Informacion Mostrada por Sesion:

- Dispositivo y navegador (del User-Agent)
- IP Address
- Ubicacion aproximada (basada en IP)
- Fecha y hora de creacion
- Ultima actividad
- Fecha y hora de expiracion
- Si es la sesion actual

### NOTAS IMPORTANTES

- Usuario puede tener maximo 5 sesiones simultaneas
- Cuando se crea sesion numero 6, automaticamente se cierra la mas antigua
- Sesion actual NO puede cerrarse desde gestion de sesiones
- Para cerrar sesion actual, usar opcion "Cerrar Sesion" del menu principal
- Cerrar sesion remota es irreversible, requiere nuevo login en ese dispositivo
- Lista de sesiones se actualiza automaticamente cada 30 segundos
- Sesiones expiradas se muestran durante 24 horas y luego se eliminan automaticamente
- Ubicacion es aproximada basada en IP (no siempre precisa)
- Usuario puede cerrar todas las demas sesiones con un solo clic

Casos de Uso Tipicos:

- Olvido cerrar sesion en computadora publica
- Cambio de dispositivo y quiere cerrar sesion anterior
- Sospecha de acceso no autorizado
- Limpieza periodica de sesiones antiguas

Timeouts:

- Timeout absoluto: 8 horas desde login
- Timeout por inactividad: 2 horas sin actividad
- Sesion numero 6 invalida automaticamente la mas antigua

---

Sistema IACT - Analisis IVR
Version: 1.0.0 | Fecha documento: 2026-03-14 | Modelo RBAC: v7.0.0
