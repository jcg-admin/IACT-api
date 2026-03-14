# DICCIONARIO DE FLUJOS - TARJETAS DETALLADAS

Sistema IACT - Analisis IVR
Version: 1.0.0
Fecha: 2026-03-14
Modelo RBAC: v7.0.0
Formato: Tarjetas Individuales por Funcion

---

## INFORMACION GENERAL

Este diccionario documenta los flujos de cada funcion atomica del sistema IACT mediante tarjetas detalladas. Cada tarjeta describe el comportamiento completo de una funcion: flujo principal, flujos alternativos, validaciones, mensajes, implementacion tecnica y auditoria.

Cada tarjeta es un archivo independiente ubicado en: documentos/flujos/

Estado actual: 3 de 46 funciones documentadas (6.5%)

---

## MODULOS

- MOD_Auth - Autenticacion (3/4 funciones documentadas)
- MOD_Users - Gestion de Usuarios (0/9 funciones documentadas)
- MOD_Access - Gestion de Permisos (0/3 funciones documentadas)
- MOD_Reports - Reportes y Analisis (0/6 funciones documentadas)
- MOD_Audit - Auditoria y Compliance (0/3 funciones documentadas)

---

## INDICE DE FUNCIONES DOCUMENTADAS

### MOD_Auth - Autenticacion

1. auth.login - Iniciar Sesion | Tarjeta auth login.md
2. auth.logout - Cerrar Sesion | Tarjeta auth logout.md
3. auth.recover_password - Recuperar Contrasena | pendiente
4. auth.manage_sessions - Gestionar Sesiones | Tarjeta auth manage sessions.md

### MOD_Users - Gestion de Usuarios

5. users.view - Ver Usuarios | pendiente
6. users.create - Crear Usuarios | pendiente
7. users.edit - Editar Usuarios | pendiente
8. users.delete - Eliminar Usuarios | pendiente
9. users.reset_password - Resetear Contrasena | pendiente
10. users.lock - Bloquear Usuario | pendiente
11. users.unlock - Desbloquear Usuario | pendiente
12. users.search - Buscar Usuarios | pendiente
13. users.export - Exportar Usuarios | pendiente

### MOD_Access - Gestion de Permisos

14. access.view - Ver Funciones Asignadas | pendiente
15. access.assign - Asignar Funciones | pendiente
16. access.revoke - Revocar Funciones | pendiente

### MOD_Reports - Reportes y Analisis

17. reports.view_basic - Ver Reportes Basicos | pendiente
18. reports.view_advanced - Ver Reportes Avanzados | pendiente
19. reports.export - Exportar Reportes | pendiente
20. reports.modify_data - Modificar Datos de Reportes | pendiente
21. reports.approve - Aprobar Modificaciones | pendiente
22. reports.schedule - Programar Reportes | pendiente

### MOD_Audit - Auditoria y Compliance

23. audit.view - Ver Auditoria | pendiente
24. audit.search - Buscar en Auditoria | pendiente
25. audit.delete - Eliminar Registros de Auditoria | pendiente

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

Documento: DICCIONARIO DE FLUJOS - TARJETAS DETALLADAS
Sistema IACT - Analisis IVR
Version: 1.0.0 | Fecha documento: 2026-03-14 | Modelo RBAC: v7.0.0
