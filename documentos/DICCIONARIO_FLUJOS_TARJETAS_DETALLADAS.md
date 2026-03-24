# DICCIONARIO DE FLUJOS - TARJETAS DETALLADAS

Sistema IACT - Analisis IVR
Version: 2.0.0
Fecha: 2026-03-22
Modelo RBAC: v7.0.0
Formato: Tarjetas Individuales por Funcion

---

## INFORMACION GENERAL

Este diccionario documenta los flujos de cada funcion atomica del sistema IACT mediante tarjetas detalladas. Cada tarjeta describe el comportamiento completo de una funcion: flujo principal, flujos alternativos, validaciones, mensajes, implementacion tecnica y auditoria.

Cada tarjeta es un archivo independiente ubicado en: documentos/flujos/

Estado actual: 25 de 46 funciones documentadas (54.3%)

---

## MODULOS

- MOD_Auth - Autenticacion (4/4 funciones documentadas - 100%)
- MOD_Users - Gestion de Usuarios (9/9 funciones documentadas - 100%)
- MOD_Access - Gestion de Permisos (3/3 funciones documentadas - 100%)
- MOD_Reports - Reportes y Analisis (6/6 funciones documentadas - 100%)
- MOD_Audit - Auditoria y Compliance (3/3 funciones documentadas - 100%)
- Modulos adicionales: 21 funciones pendientes de identificar y documentar

---

## INDICE DE FUNCIONES DOCUMENTADAS

### MOD_Auth - Autenticacion

1. auth.login - Iniciar Sesion | Tarjeta auth login.md
2. auth.logout - Cerrar Sesion | Tarjeta auth logout.md
3. auth.recover_password - Recuperar Contrasena | Tarjeta auth recover password.md
4. auth.manage_sessions - Gestionar Sesiones | Tarjeta auth manage sessions.md

### MOD_Users - Gestion de Usuarios

5. users.view - Ver Usuarios | Tarjeta users view.md
6. users.create - Crear Usuarios | Tarjeta users create.md
7. users.edit - Editar Usuarios | Tarjeta users edit.md
8. users.delete - Eliminar Usuarios | Tarjeta users delete.md
9. users.reset_password - Resetear Contrasena | Tarjeta users reset password.md
10. users.lock - Bloquear Usuario | Tarjeta users lock.md
11. users.unlock - Desbloquear Usuario | Tarjeta users unlock.md
12. users.search - Buscar Usuarios | Tarjeta users search.md
13. users.export - Exportar Usuarios | Tarjeta users export.md

### MOD_Access - Gestion de Permisos

14. access.view - Ver Funciones Asignadas | Tarjeta access view.md
15. access.assign - Asignar Funciones | Tarjeta access assign.md
16. access.revoke - Revocar Funciones | Tarjeta access revoke.md

### MOD_Reports - Reportes y Analisis

17. reports.view_basic - Ver Reportes Basicos | Tarjeta reports view basic.md
18. reports.view_advanced - Ver Reportes Avanzados | Tarjeta reports view advanced.md
19. reports.export - Exportar Reportes | Tarjeta reports export.md
20. reports.modify_data - Modificar Datos de Reportes | Tarjeta reports modify data.md
21. reports.approve - Aprobar Modificaciones | Tarjeta reports approve.md
22. reports.schedule - Programar Reportes | Tarjeta reports schedule.md

### MOD_Audit - Auditoria y Compliance

23. audit.view - Ver Auditoria | Tarjeta audit view.md
24. audit.search - Buscar en Auditoria | Tarjeta audit search.md
25. audit.delete - Eliminar Registros de Auditoria | Tarjeta audit delete.md

---

## FUNCIONES PENDIENTES DE IDENTIFICAR Y DOCUMENTAR

Las siguientes 21 funciones existen en el sistema IACT pero aun no han sido catalogadas. Requieren analisis del codigo fuente para identificar sus nombres, modulos y comportamiento.

Para identificarlas: ver documentos/TARJETAS_FALTANTES.md

| # | Modulo | Funcion | Estado |
|---|---|---|---|
| 26-46 | Por identificar | Por identificar | Pendiente |

---

## ESTRUCTURA DE CADA TARJETA

Cada tarjeta incluye:

- Nombre para UI, Modulo, ID Caso de Uso, Prioridad, Frecuencia, Estado
- Descripcion
- Precondiciones
- Flujo Principal (pasos numerados)
- Flujos Alternativos
- Postcondiciones
- Reglas de Negocio
- Restricciones Tecnicas
- Reglas SoD (si aplica)
- Mensajes del Sistema
- Implementacion Tecnica (endpoint, request/response JSON, codigos HTTP)
- Validaciones
- Auditoria (con ejemplo JSON)
- Seguridad
- Notas Importantes

---

## REGLAS SoD DOCUMENTADAS

### SoD 1 - function_assignment_control
- access.assign INCOMPATIBLE con access.revoke
- Razon: Separacion de poderes en gestion de permisos

### SoD 2 - user_audit_separation
- users.create, users.edit, users.delete INCOMPATIBLES con audit.view, audit.search
- Razon: Quien gestiona usuarios NO debe auditar sus propias acciones

### SoD 3 - report_data_separation
- reports.modify_data INCOMPATIBLE con reports.approve
- Razon: Quien modifica datos NO debe aprobar sus propias modificaciones

---

## HISTORIAL DE VERSIONES

| Version | Fecha | Cambios |
|---|---|---|
| 1.0.0 | 2026-03-14 | Version inicial: 12/46 funciones documentadas (26.1%) |
| 2.0.0 | 2026-03-22 | 25/46 funciones documentadas (54.3%). MOD_Users completo, MOD_Access, MOD_Reports y MOD_Audit agregados |

---

Documento: DICCIONARIO DE FLUJOS - TARJETAS DETALLADAS
Sistema IACT - Analisis IVR
Version: 2.0.0 | Fecha documento: 2026-03-22 | Modelo RBAC: v7.0.0
