## TARJETA: auth.logout

Nombre para UI: Cerrar Sesion
Modulo: MOD_Auth - Autenticacion
ID Caso de Uso: No documentado en E1
Prioridad: ALTA
Frecuencia: Alta
Estado: Activo

### DESCRIPCION

Permite al usuario cerrar su sesion activa en el sistema. Invalida la sesion de Django, actualiza el registro de sesion marcandolo como inactivo y registra la hora de cierre. El token DRF no se elimina en el proceso de logout; solo se destruye la sesion activa.

### PRECONDICIONES

- Usuario tiene sesion activa
- Usuario esta autenticado (token DRF valido en el header)

### FLUJO PRINCIPAL (6 PASOS)

1. Usuario hace clic en "Cerrar Sesion" en el menu principal
2. Sistema recibe peticion POST con el token de autenticacion
3. Sistema verifica que el usuario esta autenticado
4. Sistema actualiza SessionLog: logout_at = ahora, is_active = false
5. Sistema destruye la sesion de Django (logout)
6. Sistema retorna confirmacion de cierre exitoso

### FLUJOS ALTERNATIVOS

**A1. Usuario no autenticado (paso 3)**

- Sistema detecta que no hay credenciales de autenticacion en el header
- Sistema retorna 401 Unauthorized antes de ejecutar cualquier logica
- No se realiza ninguna operacion sobre la sesion
- Caso de uso termina

**A2. Sesion ya expirada (paso 4)**

- Sistema intenta actualizar SessionLog pero no encuentra sesion activa con ese session_key
- La operacion de update afecta 0 registros (no es un error)
- Sistema ejecuta Django logout normalmente
- Sistema retorna confirmacion exitosa
- Caso de uso termina

**A3. No hay sesion activa en servidor (paso 5)**

- Django logout se ejecuta aunque no haya sesion activa en servidor
- Funcion logout() de Django es idempotente (no lanza error)
- Sistema retorna HTTP 400 con mensaje "No hay sesion activa"
- Caso de uso termina

### POSTCONDICIONES

Exito:

- Sesion de Django destruida
- SessionLog actualizado: logout_at establecido, is_active = false
- Token DRF permanece en base de datos (no se elimina)
- Usuario no puede acceder a endpoints protegidos con la sesion cerrada

Fallo:

- Si usuario no estaba autenticado: no se realiza ninguna operacion
- Si sesion ya estaba expirada: SessionLog no se actualiza pero logout procede

### REGLAS DE NEGOCIO

- RN-009: El logout solo cierra la sesion activa actual, no otras sesiones del usuario
- RN-010: El token DRF NO se elimina al hacer logout; persiste en base de datos
- RN-011: El cierre de sesion es inmediato e irreversible (requiere nuevo login)
- RN-012: La sesion de Django queda destruida; el session_key deja de ser valido
- RN-013: SessionLog registra la hora exacta de logout para auditoria

### RESTRICCIONES TECNICAS

- CNST-002: SessionLog almacenado en PostgreSQL (tabla: tbl_log_sesiones)
- Endpoint protegido: IsAuthenticated (requiere token DRF en Authorization header)
- Django logout() destruye la sesion del lado del servidor
- No se implementa blacklist de tokens; el token DRF sigue siendo tecnicamente valido tras logout

### REGLAS SoD

Ninguna

### MENSAJES DEL SISTEMA

Exito:

- AUTH-010: "Logout exitoso"

Errores:

- AUTH-011: "No hay sesion activa" (intento de logout sin sesion activa)
- 401 Unauthorized: "Authentication credentials were not provided." (sin token en header)

### IMPLEMENTACION TECNICA

**Cerrar sesion**

Endpoint: POST /api/v1/auth/logout/

Request:

```
POST /api/v1/auth/logout/
Authorization: Token abc123def456xyz789...
```

Sin cuerpo (body vacio).

Response Exitosa (200 OK):

```json
{
  "success": true,
  "message": "Logout exitoso"
}
```

Response - Sin sesion activa (400 Bad Request):

```json
{
  "success": false,
  "message": "No hay sesion activa"
}
```

Response - Sin autenticacion (401 Unauthorized):

```json
{
  "detail": "Authentication credentials were not provided."
}
```

Codigos HTTP:

- 200 OK: Logout exitoso
- 400 Bad Request: No hay sesion activa
- 401 Unauthorized: Sin credenciales de autenticacion
- 500 Internal Server Error: Error del servidor

### VALIDACIONES

Validacion de Autenticacion:

- Header Authorization con token DRF valido (IsAuthenticated)
- Si no hay token o es invalido: 401 antes de ejecutar logica de logout

Validacion de Sesion:

- No se valida explicitamente que haya sesion activa antes del logout
- Django logout() es seguro de llamar aunque no haya sesion activa

### AUDITORIA

Se actualiza en SessionLog (tabla: tbl_log_sesiones):

- logout_at: timestamp exacto del cierre de sesion
- is_active: se establece en false

La infraestructura de AuditLog tiene el metodo log_logout() disponible pero no esta integrado en el flujo de logout actualmente. El registro de auditoria se realiza a nivel de SessionLog.

Ejemplo de actualizacion en SessionLog:

```json
{
  "table": "tbl_log_sesiones",
  "session_key": "abcdef1234567890abcdef1234567890",
  "user_id": 123,
  "logout_at": "2026-02-24T16:30:00Z",
  "is_active": false
}
```

### SEGURIDAD

Protecciones Implementadas:

- Solo el usuario autenticado puede cerrar su propia sesion
- Endpoint protegido con IsAuthenticated (requiere token valido)
- SessionLog registra hora exacta de logout para auditoria
- Sesion de Django destruida completamente al hacer logout

Consideracion Importante:

- El token DRF no se elimina al hacer logout
- Si se requiere invalidacion completa del token, se debe implementar un endpoint de revocacion de token separado
- Para cerrar sesiones en otros dispositivos, usar auth.manage_sessions

### NOTAS IMPORTANTES

- El logout solo afecta la sesion actual; otras sesiones del usuario permanecen activas
- Para cerrar sesiones en otros dispositivos, usar la funcion Gestionar Sesiones
- El token DRF persiste tras el logout; esto es una limitacion conocida de la implementacion actual
- SessionLog.logout_at se establece al momento exacto del logout para calcular duracion de sesion
- El campo SessionLog.duration (propiedad calculada) usa logout_at para determinar duracion total
- Django logout() es una funcion estandar de django.contrib.auth; siempre es segura de llamar

---

Sistema IACT - Analisis IVR
Version: 1.0.0 | Fecha documento: 2026-03-14 | Modelo RBAC: v7.0.0
