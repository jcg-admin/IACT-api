## TARJETA: auth.recover_password

Nombre para UI: Recuperar Contrasena
Modulo: MOD_Auth - Autenticacion
ID Caso de Uso: UC-003
Prioridad: ALTA
Frecuencia: Ocasional
Estado: Activo

### DESCRIPCION

Permite al usuario recuperar su contrasena cuando la olvida, mediante validacion de su username y respuesta a 5 preguntas de seguridad previamente configuradas. Si las respuestas son correctas, el usuario puede establecer una nueva contrasena. Todas las sesiones anteriores se invalidan automaticamente.

### PRECONDICIONES

- Usuario existe en el sistema
- Usuario configuro sus 5 preguntas de seguridad

### FLUJO PRINCIPAL (23 PASOS)

1. Usuario accede a pantalla de login
2. Usuario hace clic en enlace "Olvido su contrasena?"
3. Sistema muestra pantalla de recuperacion
4. Sistema muestra formulario con campo "Usuario"
5. Usuario ingresa su username
6. Usuario hace clic en boton "Continuar"
7. Sistema valida formato de username
8. Sistema busca username en base de datos
9. Sistema carga las 5 preguntas de seguridad del usuario
10. Sistema muestra las 5 preguntas de seguridad
11. Usuario responde las 5 preguntas
12. Usuario hace clic en "Validar Respuestas"
13. Sistema valida que las 5 respuestas sean correctas
14. Sistema muestra formulario de nueva contrasena
15. Usuario ingresa nueva contrasena
16. Usuario confirma nueva contrasena
17. Usuario hace clic en "Actualizar Contrasena"
18. Sistema valida que contrasenas coinciden
19. Sistema valida politica de contrasenas
20. Sistema actualiza hash de contrasena
21. Sistema invalida todas las sesiones anteriores del usuario
22. Sistema muestra confirmacion: "Contrasena actualizada exitosamente"
23. Sistema redirige a pantalla de login

### FLUJOS ALTERNATIVOS

**A1. Username no existe (paso 8)**

- Sistema NO encuentra username en base de datos
- Sistema muestra MISMO mensaje generico (seguridad)
- Sistema NO revela que username no existe
- Sistema muestra mensaje: "Si el usuario existe, vera sus preguntas de seguridad"
- Caso de uso termina

**A2. Usuario no tiene preguntas configuradas (paso 9)**

- Sistema detecta que usuario no configuro preguntas
- Sistema muestra error: "Contacte al administrador para recuperar su contrasena" (REC-004)
- Usuario retorna a login
- Caso de uso termina

**A3. Respuestas incorrectas (paso 13)**

- Sistema detecta que una o mas respuestas son incorrectas
- Sistema muestra error: "Las respuestas no son correctas" (REC-005)
- Sistema NO indica cuales respuestas fallan (seguridad)
- Usuario puede reintentar desde paso 11
- Despues de 3 intentos fallidos, sistema bloquea recuperacion por 15 minutos
- Caso de uso termina

**A4. Contrasenas no coinciden (paso 18)**

- Sistema detecta que contrasenas difieren
- Sistema muestra error: "Las contrasenas no coinciden" (PWD-004)
- Usuario permanece en formulario
- Caso de uso puede reintentar desde paso 15

**A5. Contrasena no cumple politica (paso 19)**

- Sistema valida contrasena contra politica
- Sistema detecta incumplimiento
- Sistema muestra errores especificos:
  - PWD-001: "La contrasena debe tener al menos 8 caracteres"
  - PWD-002: "La contrasena debe incluir mayusculas, minusculas, numeros y simbolos"
  - PWD-003: "La contrasena no puede ser igual a tus ultimas 3 contrasenas"
  - PWD-007: "La contrasena es muy comun. Elija una mas segura"
- Usuario permanece en formulario
- Caso de uso puede reintentar desde paso 15

**A6. Bloqueo por 3 intentos fallidos (despues de A3)**

- Usuario fallo 3 veces validando preguntas
- Sistema bloquea recuperacion de este username por 15 minutos
- Sistema muestra error: "Recuperacion bloqueada por 15 minutos debido a intentos fallidos"
- Sistema registra evento de bloqueo en AuditLog
- Caso de uso termina

### POSTCONDICIONES

Exito:

- Contrasena actualizada
- Todas las sesiones anteriores invalidadas
- Usuario puede iniciar sesion con nueva contrasena
- Contador de intentos de recuperacion reseteado a 0

Fallo:

- Contrasena sin cambios
- Usuario puede reintentar proceso (maximo 3 intentos)
- Posible bloqueo temporal si falla 3 veces

### REGLAS DE NEGOCIO

- RN-012: Usuario debe tener 5 preguntas de seguridad configuradas
- RN-013: Las 5 respuestas deben ser correctas para continuar
- RN-014: Maximo 3 intentos de validacion de respuestas
- RN-015: Bloqueo temporal de 15 minutos tras 3 intentos fallidos
- RN-016: Invalidar todas las sesiones al cambiar contrasena
- RN-017: NO revelar si username existe (seguridad)
- RN-018: NO indicar cuales respuestas son incorrectas (seguridad)

### RESTRICCIONES TECNICAS

- CNST-001: NO usar email externo (recuperacion sin mensajeria externa)
- CNST-003: Politica de contrasena:
  - Minimo 8 caracteres
  - Incluir mayusculas, minusculas, numeros y simbolos
  - No estar en lista de contrasenas comunes
  - No coincidir con ultimas 3 contrasenas

### REGLAS SoD

Ninguna

### MENSAJES DEL SISTEMA

Errores:

- REC-004: "Contacte al administrador para recuperar su contrasena" (no tiene preguntas configuradas)
- REC-005: "Las respuestas no son correctas" (respuestas incorrectas)
- REC-006: "Recuperacion bloqueada por 15 minutos debido a intentos fallidos" (3 intentos)
- PWD-001: "La contrasena debe tener al menos 8 caracteres" (longitud insuficiente)
- PWD-002: "La contrasena debe incluir mayusculas, minusculas, numeros y simbolos" (no cumple complejidad)
- PWD-003: "La contrasena no puede ser igual a tus ultimas 3 contrasenas" (en historial)
- PWD-004: "Las contrasenas no coinciden" (nueva diferente a confirmacion)
- PWD-007: "La contrasena es muy comun. Elija una mas segura" (en lista de contrasenas debiles)

Confirmacion:

- OK-005: "Contrasena actualizada exitosamente. Puede iniciar sesion" (recuperacion completada)

Informativos:

- INFO-004: "Si el usuario existe, vera sus preguntas de seguridad" (username no revelado)

### IMPLEMENTACION TECNICA

**Paso 1: Validar username**

Endpoint: POST /api/v1/auth/recover-password/verify-username

Request:

```json
{
  "username": "juanperez"
}
```

Response Exitosa (200 OK):

```json
{
  "success": true,
  "message": "Responda las siguientes preguntas de seguridad",
  "questions": [
    {
      "id": 1,
      "question": "Cual es el nombre de tu primera mascota?"
    },
    {
      "id": 2,
      "question": "En que ciudad naciste?"
    },
    {
      "id": 3,
      "question": "Cual es tu comida favorita?"
    },
    {
      "id": 4,
      "question": "Nombre de tu mejor amigo de la infancia?"
    },
    {
      "id": 5,
      "question": "Marca de tu primer auto?"
    }
  ]
}
```

Response - Username no existe (200 OK - por seguridad):

```json
{
  "success": true,
  "message": "Si el usuario existe, vera sus preguntas de seguridad"
}
```

**Paso 2: Validar respuestas**

Endpoint: POST /api/v1/auth/recover-password/validate-answers

Request:

```json
{
  "username": "juanperez",
  "answers": [
    {
      "question_id": 1,
      "answer": "Firulais"
    },
    {
      "question_id": 2,
      "answer": "Guadalajara"
    },
    {
      "question_id": 3,
      "answer": "Pizza"
    },
    {
      "question_id": 4,
      "answer": "Pedro"
    },
    {
      "question_id": 5,
      "answer": "Toyota"
    }
  ]
}
```

Response Exitosa (200 OK):

```json
{
  "success": true,
  "message": "Respuestas correctas. Puede establecer nueva contrasena",
  "reset_token": "temp_token_abc123xyz"
}
```

Response - Respuestas incorrectas (401 Unauthorized):

```json
{
  "success": false,
  "error_code": "REC-005",
  "message": "Las respuestas no son correctas",
  "attempts_remaining": 2
}
```

Response - 3 intentos fallidos (403 Forbidden):

```json
{
  "success": false,
  "error_code": "REC-006",
  "message": "Recuperacion bloqueada por 15 minutos debido a intentos fallidos",
  "blocked_until": "2026-02-24T11:15:00Z"
}
```

**Paso 3: Establecer nueva contrasena**

Endpoint: POST /api/v1/auth/recover-password/reset

Request:

```json
{
  "reset_token": "temp_token_abc123xyz",
  "new_password": "NuevaContrasena123!",
  "confirm_password": "NuevaContrasena123!"
}
```

Response Exitosa (200 OK):

```json
{
  "success": true,
  "message": "Contrasena actualizada exitosamente. Puede iniciar sesion",
  "sessions_invalidated": 2
}
```

Response - Contrasenas no coinciden (400 Bad Request):

```json
{
  "success": false,
  "error_code": "PWD-004",
  "message": "Las contrasenas no coinciden"
}
```

Response - No cumple politica (400 Bad Request):

```json
{
  "success": false,
  "error_code": "PWD-002",
  "message": "La contrasena debe incluir mayusculas, minusculas, numeros y simbolos"
}
```

Codigos HTTP:

- 200 OK: Operacion exitosa
- 400 Bad Request: Datos invalidos (contrasenas no coinciden, no cumple politica)
- 401 Unauthorized: Respuestas incorrectas
- 403 Forbidden: Recuperacion bloqueada
- 500 Internal Server Error: Error del servidor

### VALIDACIONES

Validacion de Username:

- Formato valido (alfanumerico, 3-30 caracteres)
- Case-sensitive

Validacion de Respuestas:

- Las 5 respuestas deben estar presentes
- Comparacion case-insensitive (normalizar a minusculas)
- Eliminar espacios al inicio y final
- Todas las 5 respuestas deben ser correctas

Validacion de Contrasena Nueva:

- Minimo 8 caracteres
- Al menos una mayuscula
- Al menos una minuscula
- Al menos un numero
- Al menos un caracter especial
- No estar en lista de contrasenas comunes
- No coincidir con ultimas 3 contrasenas del usuario

Validacion de Coincidencia:

- new_password debe ser exactamente igual a confirm_password

### AUDITORIA

Se registra en AuditLog:

- Accion: recover_password_attempt
- Usuario: username ingresado
- Timestamp: hora exacta
- IP Address: IP desde donde se solicita
- User Agent: navegador y dispositivo
- Resultado: success, failed_answers, blocked, password_updated
- Detalles: numero de intentos, si se bloqueo, si se actualizo contrasena, sesiones invalidadas

Ejemplo de log - Respuestas correctas:

```json
{
  "timestamp": "2026-02-24T10:30:00Z",
  "action": "recover_password_attempt",
  "username": "juanperez",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "result": "answers_correct",
  "details": {
    "attempt_number": 1,
    "questions_answered": 5
  }
}
```

Ejemplo de log - Contrasena actualizada:

```json
{
  "timestamp": "2026-02-24T10:32:00Z",
  "action": "password_reset",
  "username": "juanperez",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "result": "success",
  "details": {
    "sessions_invalidated": 2,
    "recovery_method": "security_questions"
  }
}
```

Ejemplo de log - Bloqueo:

```json
{
  "timestamp": "2026-02-24T10:35:00Z",
  "action": "recover_password_blocked",
  "username": "juanperez",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "result": "blocked",
  "details": {
    "attempts": 3,
    "blocked_duration_minutes": 15,
    "blocked_until": "2026-02-24T10:50:00Z"
  }
}
```

### SEGURIDAD

Protecciones Implementadas:

- Username no se revela si no existe (mensaje generico)
- Respuestas incorrectas no se indican especificamente
- Bloqueo automatico tras 3 intentos
- Todas las sesiones invalidadas al cambiar contrasena
- Reset token temporal de un solo uso
- Contrasena hasheada con PBKDF2
- Validacion de politica de contrasena
- Prevencion de contrasenas comunes
- Historial de contrasenas (ultimas 3)

Informacion NO Revelada:

- Si el username existe en el sistema
- Cuales respuestas de seguridad son incorrectas
- Numero exacto de preguntas configuradas

### NOTAS IMPORTANTES

- Usuario DEBE tener 5 preguntas de seguridad configuradas
- Si usuario no tiene preguntas configuradas, debe contactar al administrador
- Las 5 respuestas se validan simultaneamente (todas o ninguna)
- Respuestas son case-insensitive (no importan mayusculas/minusculas)
- Despues de 3 intentos fallidos, se bloquea recuperacion por 15 minutos
- Bloqueo es por username, no por IP
- Al cambiar contrasena, TODAS las sesiones activas se invalidan
- Usuario debe iniciar sesion nuevamente con la nueva contrasena
- Reset token es de un solo uso y expira al usarse
- Contador de intentos se resetea despues de recuperacion exitosa
- Contador de intentos tambien se resetea despues de 24 horas sin intentos

Sistema NO usa email externo:

- CNST-001: NO se envian emails externos
- Recuperacion es completamente interna al sistema
- Usuario debe recordar su username para iniciar recuperacion

---

Sistema IACT - Analisis IVR
Version: 1.0.0 | Fecha documento: 2026-03-14 | Modelo RBAC: v7.0.0
