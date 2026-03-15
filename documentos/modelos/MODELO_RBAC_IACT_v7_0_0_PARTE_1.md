# MODELO RBAC IACT v7.0.0 - PARTE 1

**Sistema de Análisis IVR de Atención al Cliente (IACT)**
**Versión:** 7.0.0
**Fecha:** 17 de Febrero de 2026
**Tipo:** Breaking Changes desde v6.0.0
**Estado:** Definitivo

---

## ÍNDICE

1. [Filosofía del Modelo](#1-filosofia)
2. [Arquitectura del Sistema](#2-arquitectura)
3. [Catálogo de Funciones](#3-catalogo)
4. [Separación de Funciones (SoD)](#4-sod)
5. [Permisos Temporales](#5-temporales)

Continúa en: `MODELO_RBAC_IACT_v7_0_0_PARTE_2.md`

---

## REGISTRO DE CAMBIOS v7.0.0

**BREAKING CHANGES:**
- Eliminado campo `code` del modelo `Function`
- Eliminados modelos `FunctionGroup` y `UserFunctionGroupAssignment`
- Grupos AGR-001 a AGR-010 completamente removidos
- Asignación directa de funciones sin capa intermedia

**AGREGADO:**
- Patrones comunes de asignación como guías opcionales
- Guía completa de migración desde v6.0.0
- Scripts de migración automática

**MODIFICADO:**
- Modelo `Function` simplificado
- Arquitectura de 3 capas reducida a 2 capas
- Documentación reorganizada
- Principio "Sin Pretensiones" aplicado consistentemente

**ELIMINADO:**
- Sección completa "Los 10 Grupos de Funciones"
- Campo `code` de tabla `Function`
- Referencias a grupos AGR-XXX

---

<a name="1-filosofia"></a>
## 1. FILOSOFÍA DEL MODELO

### 1.1 Principio Fundamental

> **Los nombres de funciones describen QUÉ HACE la función, NO QUIÉN es la persona**

Este principio es la base de todo el sistema RBAC del proyecto IACT. Cada decisión de diseño, nomenclatura y arquitectura se deriva de este concepto central.

### 1.2 Comparación de Enfoques

**Enfoque Tradicional (RECHAZADO):**

Basado en títulos organizacionales y jerarquías:

```
- CEO
- Director de Finanzas
- Desarrollador Senior
- Service Administrator
- Application Administrator
- Supervisor
- Analista Junior
- Gerente de Operaciones
```

Problemas identificados:
- Basado en jerarquía organizacional
- Cambio de título requiere cambio de sistema
- No describe qué permisos tiene
- Difícil de auditar
- Confunde organigrama con permisos técnicos
- Rígido y poco escalable

**Nuestro Enfoque (APROBADO):**

Basado en acciones específicas que se pueden realizar:

```
- crea_facturas
- aprueba_facturas
- identity:gestiona_aplicaciones
- epm:agrega_miembros
- modifica_codigo
- reports.view
- reports.export.csv
- users.create
- dashboard.view
- pipeline.execute
```

Ventajas demostradas:
- Claro qué puede hacer cada usuario
- Títulos organizacionales NO afectan RBAC
- Escalable y fácil de mantener
- Fácil de auditar
- Cumple regulaciones (NIST 800-53r5 AC-2, AC-5, AC-6)
- Desacoplamiento total entre organigrama y permisos

### 1.3 Estándar de Nomenclatura

**Regla general:**

```
CÓDIGO Python:           Inglés (clases, métodos, variables)
permission_django:       Inglés (reports.view, users.create)
COMENTARIOS/Docstrings:  Español
display_name (UI):       Español (Ver reportes, Crear usuarios)
description:             Español (con casos de uso)
```

**CAMBIO IMPORTANTE desde v6.0.0:**

```
v6.0.0 tenía:
  - permission_django: reports.view
  - code: RPT_VIEW              (campo redundante ELIMINADO)
  - display_name: Ver reportes

v7.0.0 tiene:
  - permission_django: reports.view  (único identificador)
  - display_name: Ver reportes

Razón de eliminación del campo code:
  - Redundante (solo abreviación de permission_django)
  - Duplicación innecesaria de datos
  - Riesgo de inconsistencias
  - Doble mantenimiento
```

**Convención de Nombres:**

Patrón general para `permission_django`:

```
[módulo].[acción]
[módulo].[acción].[especificador]

Ejemplos:
  reports.view                  (módulo.acción)
  reports.export.csv            (módulo.acción.formato)
  users.create                  (módulo.acción)
  auth.login                    (módulo.acción)
  pipeline.execute              (módulo.acción)
  dashboard.export.excel        (módulo.acción.formato)
```

**Acciones estándar:**

| Acción | Significado |
|---|---|
| `view` | Ver/Visualizar/Consultar |
| `create` | Crear nuevo elemento |
| `edit` | Editar elemento existente |
| `delete` | Eliminar elemento |
| `export` | Exportar datos a formato externo |
| `execute` | Ejecutar proceso/job |
| `send` | Enviar comunicación |
| `mark_read` | Marcar como leído |
| `search` | Buscar con criterios |
| `download` | Descargar archivo |
| `lock` | Bloquear |
| `unlock` | Desbloquear |
| `reset` | Resetear a estado inicial |

### 1.4 Modelo de Función

Definición del modelo `Function` simplificado en v7.0.0:

```python
class Function(models.Model):
    """Función atómica del sistema RBAC."""

    permission_django = models.CharField(
        max_length=100,
        primary_key=True,
        help_text="Permiso Django: reports.view, users.create"
    )

    display_name = models.CharField(
        max_length=200,
        help_text="Nombre para UI: Ver reportes, Crear usuarios"
    )

    module = models.CharField(
        max_length=50,
        help_text="Módulo: reports, users, dashboard, auth"
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ('activo', 'Activo'),
            ('planificado', 'Planificado'),
            ('deprecado', 'Deprecado'),
        ],
        default='activo'
    )

    description = models.TextField(
        help_text="Descripción detallada en español"
    )
```

---

<a name="2-arquitectura"></a>
## 2. ARQUITECTURA DEL SISTEMA

### 2.1 Visión General

El sistema IACT implementa **Flat RBAC** (Role-Based Access Control) sin jerarquías:

- 46 funciones atómicas específicas
- Asignación directa usuario-función (sin grupos intermedios)
- 3 reglas de validación SoD (Separation of Duties)
- Auditoría completa de todos los cambios

**CAMBIO ARQUITECTÓNICO FUNDAMENTAL desde v6.0.0:**

```
v6.0.0 (3 capas):   Usuario → Grupo AGR-XXX → Funciones
v7.0.0 (2 capas):   Usuario → Funciones
```

### 2.2 Diagrama de Arquitectura

```
┌────────────────────────────────────────────────────┐
│            SISTEMA IACT v7.0.0                     │
│        Control de Acceso Simplificado              │
└────────────────────────────────────────────────────┘

┌──────────────┐
│   USUARIO    │
│  Juan Pérez  │
└──────┬───────┘
       │
       │ tiene directamente (sin grupos intermedios)
       │
       ↓
┌──────────────────────────────────────────┐
│      FUNCIONES ASIGNADAS                 │
│   (UserFunctionAssignment)               │
├──────────────────────────────────────────┤
│  auth.login                              │
│  reports.view                            │
│  reports.export.csv                      │
│  dashboard.view                          │
│  alerts.view                             │
│  alerts.mark_read                        │
│                                          │
│  Cada asignación incluye:                │
│  - Justificación (obligatoria)           │
│  - Fecha de asignación                   │
│  - Quién asignó                          │
│  - Temporal (opcional con expiración)    │
└──────────────────────────────────────────┘
       ↑
       │ validadas contra
       │
┌──────────────────────────────────────────┐
│         REGLAS SoD                       │
├──────────────────────────────────────────┤
│  Regla 1: reports_export_separation      │
│  Regla 2: user_audit_separation          │
│  Regla 3: pipeline_audit_separation      │
└──────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────┐
│         AUDITORÍA                        │
│        (AuditLog)                        │
├──────────────────────────────────────────┤
│  Registro inmutable de:                  │
│  - Asignaciones                          │
│  - Revocaciones                          │
│  - Violaciones SoD                       │
│  - Excepciones SoD                       │
│  - Login/Logout                          │
│  - Cambios en usuarios                   │
│                                          │
│  Retención: 7 años                       │
└──────────────────────────────────────────┘
```

### 2.3 Componentes del Sistema

**Function (Función Atómica)**

Unidad mínima de permiso.

Características:
- Describe UNA acción específica
- Atómica (no divisible)
- Independiente de títulos organizacionales
- Combinable con otras funciones

Propiedades:
- `permission_django`: Identificador único
- `display_name`: Nombre para UI
- `module`: Módulo al que pertenece
- `status`: activo, planificado, deprecado
- `description`: Descripción detallada

---

**UserFunctionAssignment (Asignación)**

Relación directa entre usuario y función.

Características:
- Permanente o temporal
- Justificación obligatoria (mínimo 20 caracteres)
- 100% auditable
- Validación automática contra SoD
- Revocable en cualquier momento
- Soporta excepciones SoD

Propiedades:
- `user`: Usuario que recibe la función
- `function`: Función asignada
- `is_temporary`: Si expira automáticamente
- `valid_until`: Fecha de expiración
- `created_by`: Quién asignó
- `approved_by`: Quién aprobó
- `justification`: Por qué se asigna
- `sod_exception`: Si es excepción SoD
- `revoked_at`: Cuándo se revocó

---

**SoDRule (Regla de Separación)**

Define grupos de funciones mutuamente excluyentes.

Características:
- Usuario NO puede tener funciones de ambos grupos
- Previene conflictos de interés
- Validación automática
- Permite excepciones justificadas

Propiedades:
- `name`: Nombre de la regla
- `description`: Qué previene
- `group_a`: Array de funciones grupo A
- `group_b`: Array de funciones grupo B
- `is_active`: Si está activa

---

**AuditLog (Log de Auditoría)**

Registro inmutable de acciones.

Características:
- Inmutable (no modificable ni eliminable)
- Retención de 7 años
- Formato JSON estructurado
- Incluye timestamp, usuario, acción, detalles, IP

### 2.4 Flujo de Asignación

```
1. IDENTIFICACIÓN
   Pregunta: ¿QUÉ NECESITA HACER el usuario?

2. SELECCIÓN
   Consultar catálogo de 46 funciones
   Seleccionar las necesarias

3. VALIDACIÓN SoD
   Sistema valida contra 3 reglas SoD
   Si viola: rechazar o solicitar excepción

4. JUSTIFICACIÓN
   Ingresar justificación (mínimo 20 caracteres)

5. CREACIÓN
   Crear UserFunctionAssignment

6. AUDITORÍA
   Registrar en AuditLog

7. NOTIFICACIÓN
   Informar al usuario
```

### 2.5 Diferencias con v6.0.0

| Aspecto | v6.0.0 | v7.0.0 |
|---|---|---|
| Estructura | Usuario → Grupo → Funciones | Usuario → Funciones |
| Grupos AGR-XXX | 10 grupos | Eliminados |
| Campo `code` | Sí | NO |
| Asignación | Por grupo | Por función |
| Flexibilidad | Media | Alta |
| Capas | 3 | 2 |
| Consistencia | Grupos violan principio | Total |

---

<a name="3-catalogo"></a>
## 3. CATÁLOGO DE FUNCIONES

### 3.1 Resumen

**Total de funciones: 46**

- Activas: 42 (91.3%)
- Planificadas: 4 (8.7%)

**Distribución por módulo:**

| Módulo | Funciones |
|---|---|
| MOD_Auth | 4 |
| MOD_Users | 9 |
| MOD_Access | 5 |
| MOD_Pipeline | 4 |
| MOD_Reports | 6 |
| MOD_Dashboard | 6 |
| MOD_Alerts | 6 |
| MOD_Audit | 4 |
| MOD_Logs | 2 |

### 3.2 MOD_Auth: Autenticación (4 funciones)

**Propósito:** Gestión de sesiones y autenticación de usuarios.

**Restricciones:**
- CNST-001: Sesión expira tras 30 minutos de inactividad
- CNST-002: Máximo 3 sesiones concurrentes
- CNST-003: Contraseña con política de complejidad

| permission_django | display_name | status | descripción |
|---|---|---|---|
| `auth.login` | Iniciar Sesión | activo | Autenticarse con credenciales válidas |
| `auth.logout` | Cerrar Sesión | activo | Cerrar sesión activa |
| `auth.recover_password` | Recuperar Contraseña | activo | Solicitar recuperación por email |
| `auth.manage_sessions` | Gestionar Sesiones | activo | Ver y cerrar sesiones activas |

### 3.3 MOD_Users: Gestión de Usuarios (9 funciones)

**Propósito:** Administración del ciclo de vida de cuentas de usuario.

**Restricciones:**
- CNST-011: Username único, alfanumérico, 3-30 caracteres
- CNST-012: Email único, formato válido
- CNST-013: Usuario inactivo tras 90 días sin login
- CNST-014: Soft delete

| permission_django | display_name | status | descripción |
|---|---|---|---|
| `users.view` | Ver Usuarios | activo | Consultar lista de usuarios |
| `users.create` | Crear Usuarios | activo | Crear nuevas cuentas |
| `users.edit` | Editar Usuarios | activo | Modificar datos de usuarios |
| `users.delete` | Eliminar Usuarios | activo | Eliminar cuentas (soft delete) |
| `users.reset_password` | Resetear Contraseña | activo | Resetear contraseña de usuario |
| `users.lock` | Bloquear Usuario | activo | Bloquear cuenta temporalmente |
| `users.unlock` | Desbloquear Usuario | activo | Desbloquear cuenta bloqueada |
| `users.search` | Buscar Usuarios | activo | Buscar por criterios |
| `users.export` | Exportar Usuarios | activo | Exportar lista a CSV |

> **Nota:** Sujeto a Regla SoD 2 (ver sección 4.3)

### 3.4 MOD_Access: Gestión de Acceso RBAC (5 funciones)

**Propósito:** Administración del sistema de control de acceso.

**Restricciones:**
- CNST-020: Solo quien tiene `access.assign` puede asignar
- CNST-021: Temporales máximo 6 meses
- CNST-022: Justificación mínimo 20 caracteres
- CNST-023: Validación SoD automática

| permission_django | display_name | status | descripción |
|---|---|---|---|
| `access.view` | Ver Permisos | activo | Consultar funciones asignadas |
| `access.assign` | Asignar Funciones | activo | Asignar funciones a usuarios |
| `access.revoke` | Revocar Funciones | activo | Quitar funciones asignadas |
| `access.view_sod_rules` | Ver Reglas SoD | activo | Consultar reglas SoD activas |
| `access.audit` | Auditar Accesos | activo | Historial de cambios de permisos |

### 3.5 MOD_Pipeline: ETL y Procesamiento (4 funciones)

**Propósito:** Control del pipeline ETL de datos del IVR.

**Restricciones:**
- CNST-031: Jobs solo en horario 00:00-06:00
- CNST-032: Solo un job simultáneo
- CNST-033: Timeout máximo 4 horas
- CNST-034: Jobs con error generan alerta

| permission_django | display_name | status | descripción |
|---|---|---|---|
| `pipeline.view` | Ver Estado Pipeline | activo | Consultar estado de jobs ETL |
| `pipeline.execute` | Ejecutar Jobs ETL | activo | Iniciar job ETL manualmente |
| `pipeline.stop` | Detener Jobs ETL | activo | Detener job en ejecución |
| `pipeline.monitor` | Monitorear Pipeline | activo | Ver métricas y alertas |

> **Nota:** Sujeto a Regla SoD 3 (ver sección 4.4)

### 3.6 MOD_Reports: Generación de Reportes (6 funciones)

**Propósito:** Sistema de generación y exportación de reportes.

**Restricciones:**
- CNST-010: Exportación máximo 10,000 registros
- CNST-040: Reportes almacenados 30 días
- CNST-041: Formatos: CSV, Excel, PDF (planificado)

| permission_django | display_name | status | descripción |
|---|---|---|---|
| `reports.view` | Ver Reportes | activo | Consultar reportes generados |
| `reports.create` | Crear Reportes | activo | Generar nuevos reportes |
| `reports.edit` | Editar Reportes | activo | Modificar parámetros |
| `reports.delete` | Eliminar Reportes | activo | Eliminar reportes |
| `reports.export.csv` | Exportar CSV | activo | Exportar a CSV |
| `reports.export.excel` | Exportar Excel | activo | Exportar a Excel |
| `reports.export.pdf` | Exportar PDF | planificado | Exportar a PDF (v7.1.0) |

> **CRÍTICO — Regla SoD 1:**
>
> Grupos mutuamente excluyentes:
> - **Grupo A (Gestión):** `create`, `edit`, `delete`
> - **Grupo B (Exportación):** `export.csv`, `export.excel`, `export.pdf`
>
> Usuario NO puede tener funciones de ambos grupos.
> Razón: Prevenir manipulación sin revisión (ver sección 4.2)

### 3.7 MOD_Dashboard: Visualización (6 funciones)

**Propósito:** Dashboards con métricas en tiempo real.

**Restricciones:**
- CNST-010: Exportación máximo 10,000 registros
- CNST-050: Actualización cada 5 minutos
- CNST-051: Máximo 10 widgets por dashboard
- CNST-052: Datos de últimos 90 días

| permission_django | display_name | status | descripción |
|---|---|---|---|
| `dashboard.view` | Ver Dashboard | activo | Visualizar dashboards |
| `dashboard.export.csv` | Exportar CSV | activo | Exportar datos a CSV |
| `dashboard.export.excel` | Exportar Excel | activo | Exportar datos a Excel |
| `dashboard.export.pdf` | Exportar PDF | planificado | Exportar snapshot a PDF (v7.2.0) |
| `dashboard.share` | Compartir Dashboard | planificado | Compartir con link (v7.2.0) |
| `dashboard.edit` | Editar Dashboard | planificado | Personalizar widgets (v7.3.0) |

### 3.8 MOD_Alerts: Sistema de Alertas (6 funciones)

**Propósito:** Notificaciones internas y alertas del sistema.

**Restricciones:**
- CNST-060: Retención 90 días
- CNST-061: Máximo 5 alertas manuales por día
- CNST-062: Prioridades: LOW, MEDIUM, HIGH, CRITICAL
- CNST-063: CRITICAL genera email adicional

| permission_django | display_name | status | descripción |
|---|---|---|---|
| `alerts.view` | Ver Alertas | activo | Ver alertas recibidas |
| `alerts.create` | Crear Alertas | activo | Crear alertas manuales |
| `alerts.edit` | Editar Alertas | activo | Modificar alertas pendientes |
| `alerts.delete` | Eliminar Alertas | activo | Eliminar alertas |
| `alerts.mark_read` | Marcar Leída | activo | Marcar como leída |
| `alerts.send` | Enviar Alerta | activo | Enviar manualmente |

### 3.9 MOD_Audit: Auditoría (4 funciones)

**Propósito:** Auditoría y compliance regulatorio.

**Restricciones:**
- CNST-070: Retención 7 años
- CNST-071: Logs inmutables
- CNST-072: Formato JSON estructurado
- CNST-073: Acceso requiere justificación

| permission_django | display_name | status | descripción |
|---|---|---|---|
| `audit.view` | Ver Auditoría | activo | Consultar logs de auditoría |
| `audit.search` | Buscar Auditoría | activo | Búsqueda avanzada en logs |
| `audit.export` | Exportar Auditoría | activo | Exportar logs a CSV |
| `audit.compliance` | Generar Compliance | activo | Reportes regulatorios |

> **CRÍTICO — Reglas SoD 2 y 3:**
>
> `audit.view` y `audit.search` NO pueden coexistir con:
> - `users.create`, `users.edit`, `users.delete`, `users.reset_password` (Regla 2)
> - `pipeline.execute`, `pipeline.stop` (Regla 3)
>
> Ver secciones 4.3 y 4.4

### 3.10 MOD_Logs: Logs Técnicos (2 funciones)

**Propósito:** Logs técnicos del sistema.

**Restricciones:**
- CNST-030: Rotación 10MB x 10 archivos
- CNST-080: Formato JSON
- CNST-081: Sin PII en logs
- CNST-082: DEBUG no disponible en producción

| permission_django | display_name | status | descripción |
|---|---|---|---|
| `logs.view` | Ver Logs Técnicos | activo | Consultar logs (ERROR, WARNING, INFO) |
| `logs.download` | Descargar Logs | activo | Descargar archivos de logs |

**Diferencia con MOD_Audit:**
- **MOD_Logs:** Logs técnicos de aplicación
- **MOD_Audit:** Logs de auditoría de usuarios

---

<a name="4-sod"></a>
## 4. SEPARACIÓN DE FUNCIONES (SoD)

### 4.1 Concepto

Separation of Duties (SoD) es un principio de seguridad que previene conflictos de interés al prohibir que un mismo usuario tenga funciones que, combinadas, puedan usarse para actividades fraudulentas sin detección.

**Objetivos:**
- Prevenir fraude interno
- Reducir riesgo de actividad maliciosa
- Requerir colusión para actividades ilícitas
- Cumplir regulaciones (NIST 800-53r5 AC-5)
- Habilitar auditoría efectiva

> **Principio base:** "Ninguna persona debe tener suficiente poder para comprometer completamente un proceso crítico de forma unilateral"

**Implementación:**
- Sistema valida automáticamente 3 reglas SoD
- Si violación: rechaza asignación
- Registra intentos en AuditLog
- Permite excepciones con aprobación dual

### 4.2 Regla SoD 1: `reports_export_separation`

**Nombre:** Separación Gestión/Exportación de Reportes
**Objetivo:** Prevenir manipulación de datos sin revisión

**Grupos conflictivos:**

| Grupo A (Gestión) | Grupo B (Exportación) |
|---|---|
| `reports.create` | `reports.export.csv` |
| `reports.edit` | `reports.export.excel` |
| `reports.delete` | `reports.export.pdf` |

**Regla:** Usuario NO puede tener funciones de ambos grupos

**Razón:** Quien crea reportes NO debe exportarlos para prevenir que alguien manipule datos y exporte la versión alterada sin revisión de otra persona

**Casos permitidos:**
- Usuario 1: `reports.view`, `reports.export.csv` (solo exporta)
- Usuario 2: `reports.create`, `reports.edit` (solo gestiona)
- Usuario 3: `reports.view` (solo consulta)

**Casos NO permitidos:**
- Usuario 4: `reports.create`, `reports.export.csv` — **viola SoD**
- Usuario 5: `reports.edit`, `reports.export.excel` — **viola SoD**

### 4.3 Regla SoD 2: `user_audit_separation`

**Nombre:** Separación Gestión Usuarios/Auditoría
**Objetivo:** Prevenir ocultamiento de acciones propias

**Grupos conflictivos:**

| Grupo A (Gestión Usuarios) | Grupo B (Auditoría) |
|---|---|
| `users.create` | `audit.view` |
| `users.edit` | `audit.search` |
| `users.delete` | |
| `users.reset_password` | |

**Regla:** Usuario NO puede tener funciones de ambos grupos

**Razón:** Quien gestiona usuarios NO debe auditar sus propias acciones

**Casos permitidos:**
- Usuario 1: `users.view`, `users.search` (solo consulta)
- Usuario 2: `audit.view`, `audit.search` (solo audita)
- Usuario 3: `users.create`, `users.edit` (gestiona sin auditar)

**Casos NO permitidos:**
- Usuario 4: `users.create`, `audit.view` — **viola SoD**
- Usuario 5: `users.delete`, `audit.search` — **viola SoD**

### 4.4 Regla SoD 3: `pipeline_audit_separation`

**Nombre:** Separación Control Pipeline/Auditoría
**Objetivo:** Prevenir ocultamiento de errores en ETL

**Grupos conflictivos:**

| Grupo A (Control Pipeline) | Grupo B (Auditoría Compliance) |
|---|---|
| `pipeline.execute` | `audit.view` |
| `pipeline.stop` | `audit.compliance` |

**Regla:** Usuario NO puede tener funciones de ambos grupos

**Razón:** Quien controla pipeline ETL NO debe auditar sus propias ejecuciones

**Casos permitidos:**
- Usuario 1: `pipeline.view`, `pipeline.monitor` (solo monitorea)
- Usuario 2: `audit.view`, `audit.compliance` (solo audita)
- Usuario 3: `pipeline.execute`, `pipeline.stop` (controla sin auditar)

**Casos NO permitidos:**
- Usuario 4: `pipeline.execute`, `audit.view` — **viola SoD**
- Usuario 5: `pipeline.stop`, `audit.compliance` — **viola SoD**

### 4.5 Validación Automática

Sistema valida todas las reglas SoD en cada asignación:

```
1. Validar Regla SoD 1
2. Validar Regla SoD 2
3. Validar Regla SoD 3
4. Si alguna falla: rechazar y registrar en AuditLog
5. Si todas pasan: crear asignación
6. Auditar asignación exitosa
```

### 4.6 Excepciones

En casos excepcionales (ej: administrador técnico único), se permite excepción SoD:

**Requisitos:**
- Justificación detallada
- Aprobación dual (dos personas)
- Mitigaciones definidas
- Auditoría reforzada
- Revisión trimestral

**Límites:**
- Máximo 2-3 usuarios con excepciones
- Solo para necesidades absolutas
- Revocación si cambian circunstancias

---

<a name="5-temporales"></a>
## 5. PERMISOS TEMPORALES

### 5.1 Concepto

Permisos temporales permiten asignar funciones por período limitado. Al expirar, se revocan automáticamente.

**Casos de uso:**
- Reemplazo de empleado ausente
- Proyecto específico temporal
- Acceso de auditoría externa
- Capacitación temporal

### 5.2 Características

| Atributo | Valor |
|---|---|
| Duración máxima | 6 meses (180 días) |
| Justificación | Obligatoria, mínimo 20 caracteres |
| Revocación | Automática al expirar |
| Extensión | Requiere nueva solicitud |
| Auditoría | Registro de inicio, fin programado, fin real |
| Validación | Mismas reglas SoD que permanentes |

### 5.3 Implementación

Campos del modelo `UserFunctionAssignment`:

```python
is_temporary = models.BooleanField(default=False)
valid_from   = models.DateTimeField(auto_now_add=True)
valid_until  = models.DateTimeField(null=True, blank=True)
```

**Restricciones:**
- Si `is_temporary=True`, `valid_until` es obligatorio
- `valid_until` debe ser posterior a `valid_from`
- Duración máxima 180 días

### 5.4 Ejemplo de Uso

```
Caso:         María reemplaza a Juan durante licencia médica (90 días)
Función:      users.create
Duración:     90 días
Justificación: "Reemplazo temporal de Juan Pérez durante
                licencia médica. María asumirá gestión de
                usuarios del área comercial."
```

Sistema programa revocación automática para fecha de expiración.

### 5.5 Revocación Automática

Tarea programada diaria (01:00):
1. Busca asignaciones temporales expiradas
2. Revoca automáticamente
3. Registra en AuditLog
4. Notifica al usuario

### 5.6 Validaciones

Sistema valida:
- Duración no exceda 6 meses
- Fecha expiración sea futura
- Justificación mínimo 20 caracteres
- Reglas SoD (igual que permanentes)

### 5.7 Consulta de Funciones Activas

Sistema considera automáticamente expiración:
- **Permanentes:** siempre activas (si no revocadas)
- **Temporales:** activas solo si no expiradas

---

## FIN DE PARTE 1

Continúa en: `MODELO_RBAC_IACT_v7_0_0_PARTE_2.md`

**Contenido de Parte 2:**
- Modelo de Datos Completo
- Patrones Comunes de Asignación
- Casos de Uso Detallados
- Implementación Técnica
- Guía de Migración desde v6.0.0

---

Sistema IACT — Análisis IVR
**Versión:** 7.0.0 | **Fecha:** 17 de Febrero de 2026 | **Documento:** Parte 1 de 2 | **Estado:** Definitivo
