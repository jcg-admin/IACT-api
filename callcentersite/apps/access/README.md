# apps/access - Sistema RBAC (Role-Based Access Control)

**Versión:** 6.0.0 (Corregido v4.0.0)
**Fecha:** 2026-01-21  
**Última actualización:** FASE D - Corrección Crítica  
**Basado en:** MODELO_RBAC_IACT_v6_0_0_PARTE_1.md

> ⚠️ **NOTA IMPORTANTE:** Este documento fue corregido en FASE D para alinearse con el modelo RBAC v6.0.0 oficial. Ver: [PLAN_CORRECCION_v4_0_0.md](../../../docs/ejecucion/PLAN_CORRECCION_v4_0_0.md)

---

## 📋 ÍNDICE

1. [Descripción General](#descripción-general)
2. [Arquitectura RBAC](#arquitectura-rbac)
3. [Modelos](#modelos)
4. [Catálogo de 46 Funciones](#catálogo-de-funciones)
5. [Grupos de Funciones](#grupos-de-funciones)
6. [Flujos de Trabajo](#flujos-de-trabajo)
7. [API Endpoints](#api-endpoints)
8. [Ejemplos de Uso](#ejemplos-de-uso)

---

## 📖 DESCRIPCIÓN GENERAL

### ¿Qué es apps/access/?

`apps/access/` es el sistema de **Control de Acceso Basado en Roles (RBAC)** del sistema IACT. Implementa **Flat RBAC** sin jerarquías basado en:

- ✅ **46 funciones atómicas** (42 activas + 4 planificadas)
- ✅ **9 módulos funcionales**
- ✅ **10 grupos de funciones**
- ✅ **3 reglas de separación de funciones (SoD)**
- ✅ **Permisos temporales** con justificación y auditoría

### Filosofía del Modelo

> **Los nombres de funciones describen QUÉ HACE la función, NO QUIÉN es la persona**

**❌ INCORRECTO:**
```
Roles basados en títulos:
- USERS_FULL_MANAGER
- SYSTEM_ADMIN
```

**✅ CORRECTO:**
```
Funciones basadas en acciones:
- users.view_user
- reports.export.csv
- dashboard.view
```

### Estándar de Nomenclatura

```yaml
permission_django:  Clave primaria (PK)
  Formato: reports.view, dashboard.export.csv
  Idioma: Inglés
  Uso: Base de datos, código Python

code:  Referencial (NO es PK)
  Formato: RPT_VIEW, DSH_EXP_CSV
  Idioma: Inglés
  Uso: Documentación, migraciones

display_name:  UI
  Formato: Ver Reportes, Exportar CSV
  Idioma: Español
  Uso: Interfaz de usuario

description:  Explicación
  Idioma: Español
  Uso: Documentación, ayuda
```

**Ejemplo completo:**

```python
{
    "permission_django": "reports.export.csv",  # ← PK
    "code": "RPT_EXP_CSV",                      # ← Referencial
    "display_name": "Exportar Reportes CSV",    # ← UI español
    "description": "Exporta reportes a CSV. Límite: 100K registros",
    "module": "reports",
    "status": "activo"
}
```

---

## 🏗️ ARQUITECTURA RBAC

### Diagrama de Flujo

```
User (Usuario)
   ↓
UserGroup (Asignación)
   ↓
Group (Grupo de permisos)
   ↓
GroupFunction (Asignación)
   ↓
Function (Permiso granular)
   ↓
Module (Agrupación UI)
```

### Componentes del Sistema

```yaml
Modelos RBAC (6):
  1. Function: Funciones del sistema (46 total)
  2. Module: Módulos UI (9 total)
  3. Group: Grupos de permisos (10 predefinidos)
  4. UserGroup: Usuario ↔ Group
  5. GroupFunction: Group ↔ Function
  6. UserModuleAccess: Usuario ↔ Module (visibilidad UI)

Permissions (DRF):
  - RequiresFunctionPermission: Verifica RBAC
  - DynamicFunctionPermission: Para objetos

Services:
  - ModuleAccessService: Lógica módulos
  - FunctionService: Lógica funciones
```

### Distribución de Funciones por Módulo

| Módulo | Código | Funciones | % | Activas | Planif | Propósito |
|--------|--------|-----------|---|---------|--------|-----------|
| MOD_Auth | AUTH | 4 | 8.7% | 4 | 0 | Sesiones y autenticación |
| MOD_Users | USR | 9 | 19.6% | 9 | 0 | Gestión de identidades |
| MOD_Access | ACC | 5 | 10.9% | 5 | 0 | RBAC core + Reglas SoD |
| MOD_Pipeline | PIP | 4 | 8.7% | 4 | 0 | Supervisión ETL |
| MOD_Reports | RPT | 6 | 13.0% | 5 | 1 | Generación reportes |
| MOD_Dashboard | DSH | 6 | 13.0% | 3 | 3 | Visualización widgets |
| MOD_Alerts | ALR | 6 | 13.0% | 6 | 0 | Alertas internas |
| MOD_Audit | AUD | 4 | 8.7% | 4 | 0 | Auditoría funcional |
| MOD_Logs | LOG | 2 | 4.3% | 2 | 0 | Logs técnicos |
| **TOTAL** | - | **46** | **100%** | **42** | **4** | - |

---

## 📦 MODELOS

### Function

```python
class Function(models.Model):
    """
    Función atómica del sistema RBAC.
    
    Una función representa una acción específica que un usuario puede realizar.
    Granularidad: Nivel action de ViewSet (list, create, delete, etc).
    """
    
    permission_django = models.CharField(
        max_length=100,
        primary_key=True,  # ← CLAVE PRIMARIA
        help_text="Formato: reports.view, dashboard.export.csv"
    )
    # Ejemplos: 'reports.view', 'dashboard.export.csv'
    
    code = models.CharField(
        max_length=30,
        unique=True,
        help_text="Código referencial: RPT_VIEW, DSH_EXP_CSV"
    )
    # Ejemplos: 'RPT_VIEW', 'DSH_EXP_CSV' (solo referencia)
    
    display_name = models.CharField(
        max_length=200,
        help_text="Nombre UI en español"
    )
    # Ejemplos: 'Ver Reportes', 'Exportar CSV'
    
    description = models.TextField(
        help_text="Descripción detallada en español"
    )
    # Ejemplo: 'Exporta reportes a CSV. Límite: 100K registros'
    
    module = models.ForeignKey(
        Module,
        related_name='functions'
    )
    # Módulo al que pertenece
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('activo', 'Activo'),
            ('planificado', 'Planificado'),
            ('deprecado', 'Deprecado'),
        ],
        default='activo'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
```

**Uso correcto:**

```python
# ✅ CORRECTO: Buscar por permission_django (PK)
function = Function.objects.get(permission_django='reports.view')

# ✅ También correcto: Buscar por code (referencial)
function = Function.objects.get(code='RPT_VIEW')

# ❌ INCORRECTO: No usar code como si fuera PK en relaciones
# Siempre usar permission_django en ForeignKeys
```

### Module

```python
class Module(models.Model):
    """
    Módulo del sistema (sección UI).
    
    Representa una sección en la interfaz de usuario.
    Organización jerárquica: módulos pueden tener padres e hijos.
    """
    
    code = models.CharField(
        max_length=50,
        unique=True
    )
    # Ejemplo: 'MOD_Reports', 'MOD_Dashboard'
    
    name = models.CharField(max_length=200)
    # Ejemplo: 'Reportes', 'Dashboard'
    
    parent = models.ForeignKey(
        'self',
        null=True,
        related_name='children'
    )
    # Jerarquía de módulos
```

### Group

```python
class Group(models.Model):
    """
    Grupo de permisos.
    
    Agrupa múltiples funciones relacionadas para asignación en bloque.
    No son roles jerárquicos (Flat RBAC).
    """
    
    code = models.CharField(max_length=50, unique=True)
    # Ejemplo: 'AGR-001', 'AGR-002'
    
    name = models.CharField(max_length=200)
    # Ejemplo: 'Operador Básico', 'Admin Usuarios'
    
    functions = models.ManyToManyField(
        Function,
        through='GroupFunction'
    )
    # Funciones asignadas a este grupo
```

### UserModuleAccess

```python
class UserModuleAccess(models.Model):
    """
    Acceso de usuario a módulo (visibilidad UI).
    
    Controla qué módulos VE el usuario en el menú.
    NO controla permisos (eso lo hace RBAC con Functions).
    
    COMPLEMENTARIO a Groups/Functions, NO redundante.
    Ver: FASE_B_ANALISIS_USER_MODULE_ACCESS.md
    """
    
    user = models.ForeignKey(User, related_name='module_accesses')
    module = models.ForeignKey(Module, related_name='user_accesses')
    
    granted_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
```

---

## 🗂️ CATÁLOGO DE FUNCIONES

### MOD_Auth (4 funciones)

**Propósito:** Gestión de sesiones y autenticación

| permission_django | code | display_name | status | description |
|-------------------|------|--------------|--------|-------------|
| `auth.login` | AUTH_LOGIN | Iniciar Sesión | activo | Inicia sesión con usuario y contraseña. Valida con PBKDF2 y genera token |
| `auth.logout` | AUTH_LOGOUT | Cerrar Sesión | activo | Cierra sesión activa. Invalida token y registra en auditoría |
| `auth.recover_password` | AUTH_RECOVER | Recuperar Contraseña | activo | Recupera contraseña mediante 3 preguntas de seguridad. NO usa email |
| `auth.manage_sessions` | AUTH_SESSIONS | Gestionar Sesiones | activo | Gestiona sesiones activas. Puede cerrar sesiones de otros usuarios (admin) |

---

### MOD_Users (9 funciones)

**Propósito:** Gestión completa del ciclo de vida de usuarios

| permission_django | code | display_name | status | description |
|-------------------|------|--------------|--------|-------------|
| `users.view_user` | USR_VIEW | Ver Usuarios | activo | Ve lista de usuarios con filtros por estado, rol, fecha |
| `users.add_user` | USR_CREATE | Crear Usuarios | activo | Crea nuevos usuarios. Valida contraseña mínimo 12 caracteres |
| `users.change_user` | USR_EDIT | Editar Usuarios | activo | Edita información de usuarios (nombre, email, estado) |
| `users.delete_user` | USR_DELETE | Eliminar Usuarios | activo | Elimina usuarios (soft delete). Audita operación |
| `users.change_password` | USR_PASS | Cambiar Contraseña | activo | Cambia la contraseña propia del usuario |
| `users.reset_password` | USR_RESET | Resetear Contraseña | activo | Resetea contraseña de otro usuario. Genera temporal |
| `users.lock_user` | USR_LOCK | Bloquear Usuario | activo | Bloquea usuario (manual o por intentos fallidos: 3 → 15 min) |
| `users.unlock_user` | USR_UNLOCK | Desbloquear Usuario | activo | Desbloquea usuario. Resetea contador de intentos |
| `users.view_profile` | USR_PROFILE | Ver Perfil | activo | Ve perfil completo de usuario (propio o de otros) |

---

### MOD_Access (5 funciones)

**Propósito:** Core del sistema RBAC. Gestión de funciones, grupos y reglas SoD

| permission_django | code | display_name | status | description |
|-------------------|------|--------------|--------|-------------|
| `access.assign_functions` | ACC_ASSIGN | Asignar Funciones | activo | Asigna funciones RBAC a usuarios. Valida reglas SoD. Audita cambio |
| `access.revoke_functions` | ACC_REVOKE | Revocar Funciones | activo | Revoca funciones previamente asignadas. Audita cambio |
| `access.view_permissions` | ACC_VIEW_PERM | Ver Permisos | activo | Ve permisos asignados a usuarios. Muestra funciones activas y grupos |
| `access.manage_groups` | ACC_GROUPS | Gestionar Grupos | activo | Gestiona grupos de funciones (AGR-001 a AGR-010) |
| `access.view_separation` | ACC_SOD | Ver Reglas SoD | activo | Ve reglas de separación de funciones. Muestra conflictos detectados |

---

### MOD_Pipeline (4 funciones)

**Propósito:** Supervisión y control del proceso ETL

| permission_django | code | display_name | status | description |
|-------------------|------|--------------|--------|-------------|
| `pipeline.view_job` | PIP_VIEW | Ver Jobs ETL | activo | Ve estado de jobs ETL (pendiente, ejecutando, completado, fallido) |
| `pipeline.execute_job` | PIP_EXEC | Ejecutar Jobs | activo | Ejecuta jobs ETL manualmente. Valida que no haya otro corriendo |
| `pipeline.stop_job` | PIP_STOP | Detener Jobs | activo | Detiene jobs ETL en ejecución. Marca como "cancelado" y audita |
| `pipeline.view_logs` | PIP_LOGS | Ver Logs Jobs | activo | Ve logs detallados de ejecución ETL (errores, warnings, stats) |

---

### MOD_Reports (6 funciones)

**Propósito:** Generación y exportación de reportes

**Endpoints:** `/api/v1/reports/{tipo}/`

| permission_django | code | display_name | status | description |
|-------------------|------|--------------|--------|-------------|
| `reports.view` | RPT_VIEW | Ver Reportes | activo | Ve reportes tabulares: Llamadas Abandonadas, Clientes Únicos, Promedio Clientes, Clientes Menú, Llamadas por Menú, Detalle Transferencias, Menú con Errores |
| `reports.create` | RPT_CREATE | Crear Reporte | activo | Crea configuración de reporte. Define filtros (trimestre, DID, menú, rango). POST /api/v1/reports/{tipo}/ |
| `reports.delete` | RPT_DELETE | Eliminar Reporte | activo | Elimina reportes antiguos. Solo propios o con permisos admin |
| `reports.export.csv` | RPT_EXP_CSV | Exportar CSV | activo | Exporta reportes a CSV. Límite: 100K registros. POST /api/v1/reports/{tipo}/{id}/export/ con format=csv |
| `reports.export.excel` | RPT_EXP_EXCEL | Exportar Excel | activo | Exporta reportes a Excel. Límite: 50K registros. POST /api/v1/reports/{tipo}/{id}/export/ con format=excel |
| `reports.export.pdf` | RPT_EXP_PDF | Exportar PDF | planificado | Exporta reportes a PDF. Límite: 10K registros. Funcionalidad planificada |

**Tipos de reportes:**
- RPT-TR-021: Llamadas Abandonadas (trimestral)
- RPT-TR-011: Clientes Únicos por DID (trimestral)
- RPT-TR-031: Promedio Clientes Únicos (trimestral)
- RPT-TR-041: Promedio Clientes Menú (trimestral)
- RPT-TR-121: Llamadas por Menú (trimestral)
- RPT-DET-001: Detalle Transferencias (mensual)
- RPT-ERR-001: Menú con Errores (anual)

---

### MOD_Dashboard (6 funciones) ⭐ NUEVO v6.0.0

**Propósito:** Visualización de métricas y widgets interactivos

**Endpoints:** `/api/v1/dashboard/{tipo}/`

| permission_django | code | display_name | status | description |
|-------------------|------|--------------|--------|-------------|
| `dashboard.view` | DSH_VIEW | Ver Dashboard | activo | Ve dashboards con widgets predefinidos. Incluye KPIs, gráficos (barras, líneas, torta) y tablas. Dashboards: Métricas Trimestrales, Análisis Clientes, Performance IVR. Datos desfasados 6-12h |
| `dashboard.export.csv` | DSH_EXP_CSV | Exportar Dashboard CSV | activo | Exporta snapshot del dashboard a CSV. Incluye todos los widgets. POST /api/v1/dashboard/{tipo}/export/ con format=csv |
| `dashboard.export.excel` | DSH_EXP_EXCEL | Exportar Dashboard Excel | activo | Exporta snapshot del dashboard a Excel con formato y gráficos. POST /api/v1/dashboard/{tipo}/export/ con format=excel |
| `dashboard.export.pdf` | DSH_EXP_PDF | Exportar Dashboard PDF | planificado | Exporta snapshot del dashboard a PDF. Funcionalidad planificada |
| `dashboard.share` | DSH_SHARE | Compartir Dashboard | planificado | Comparte dashboard con otros usuarios mediante enlace interno. Planificado |
| `dashboard.edit` | DSH_EDIT | Editar Dashboard | planificado | Edita configuración de widgets (posición, tamaño, filtros). Planificado |

**Dashboards disponibles:**
1. **DASH-TRIM:** Métricas Trimestrales
   - KPIs: Total llamadas, tasa abandono, clientes únicos
   - Charts: Top 10 menús, tendencia trimestral

2. **DASH-CLI:** Análisis de Clientes
   - KPIs: Clientes únicos, promedio por menú, recurrentes
   - Charts: Distribución por menú (pie), tendencia (line)

3. **DASH-IVR:** Performance IVR
   - KPIs: Total llamadas, tasa éxito transferencia
   - Charts: Llamadas por menú (bar), transferencias (pie)

**Separación de MOD_Reports:**
- ✅ Apps Django separadas (apps/reports/ vs apps/dashboard/)
- ✅ Endpoints diferentes (/api/v1/reports/ vs /api/v1/dashboard/)
- ✅ Permisos independientes (reports.* vs dashboard.*)
- ✅ Responsabilidad única (generación vs visualización)

---

### MOD_Alerts (6 funciones)

**Propósito:** Sistema de alertas internas (buzón interno, NO email)

| permission_django | code | display_name | status | description |
|-------------------|------|--------------|--------|-------------|
| `alerts.view_alert` | ALR_VIEW | Ver Alertas | activo | Ve alertas del buzón interno. Muestra no leídas con prioridad |
| `alerts.configure_alert` | ALR_CONF | Configurar Alerta | activo | Configura alertas automáticas (umbrales, condiciones). Solo admin |
| `alerts.send_alert` | ALR_SEND | Enviar Alerta | activo | Envía alertas manuales a destinatarios (máx 50). Solo buzón interno |
| `alerts.manage_subscriptions` | ALR_SUBS | Gestionar Suscripciones | activo | Gestiona suscripciones a tipos de alertas (informativa, advertencia, crítica) |
| `alerts.mark_read` | ALR_MARK | Marcar Leída | activo | Marca alerta como leída. Actualiza timestamp |
| `alerts.delete_alert` | ALR_DELETE | Eliminar Alerta | activo | Elimina alertas antiguas (>90 días automático, manual con permisos) |

---

### MOD_Audit (4 funciones)

**Propósito:** Auditoría funcional con log immutable

| permission_django | code | display_name | status | description |
|-------------------|------|--------------|--------|-------------|
| `audit.view_log` | AUD_VIEW | Ver Auditoría | activo | Ve logs de auditoría. Muestra eventos críticos (login, cambios permisos, exportaciones) |
| `audit.search_log` | AUD_SEARCH | Buscar Auditoría | activo | Busca eventos específicos por usuario, fecha, acción, resultado |
| `audit.export_log` | AUD_EXP | Exportar Auditoría | activo | Exporta logs a CSV/Excel para análisis. Mantiene checksums SHA-256 |
| `audit.generate_compliance` | AUD_COMPLIANCE | Generar Compliance | activo | Genera reporte de cumplimiento normativo. Valida integridad con checksums |

---

### MOD_Logs (2 funciones)

**Propósito:** Logs técnicos del sistema

| permission_django | code | display_name | status | description |
|-------------------|------|--------------|--------|-------------|
| `logs.view_technical` | LOG_VIEW | Ver Logs Técnicos | activo | Ve logs técnicos (ERROR, WARNING, INFO). No DEBUG en producción |
| `logs.export_logs` | LOG_EXP | Exportar Logs | activo | Exporta logs técnicos para análisis. Sanitiza PII antes |

---

### Resumen del Catálogo

```
┌────────────────────────────────────────────────────────────────┐
│           CATÁLOGO COMPLETO DE FUNCIONES v6.0.0                │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Total Funciones:         46                                   │
│  ├─ Activas:              42 (91.3%)                          │
│  └─ Planificadas:         4  (8.7%)                           │
│                                                                │
│  Funciones Planificadas:                                       │
│  ├─ reports.export.pdf                                         │
│  ├─ dashboard.export.pdf                                       │
│  ├─ dashboard.share                                            │
│  └─ dashboard.edit                                             │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 👥 GRUPOS DE FUNCIONES

### AGR-001: Operador Básico

**Perfil:** Usuario con acceso mínimo al sistema

**Funciones (7):**
```yaml
- auth.login
- auth.logout
- reports.view
- dashboard.view
- alerts.view_alert
- alerts.mark_read
- users.view_profile
```

### AGR-002: Analista de Reportes

**Perfil:** Genera y exporta reportes

**Funciones (10):**
```yaml
Hereda de AGR-001 (7) +
- reports.create
- reports.export.csv
- reports.export.excel
```

### AGR-003: Administrador de Dashboards

**Perfil:** Gestiona visualizaciones

**Funciones (9):**
```yaml
Hereda de AGR-001 (7) +
- dashboard.export.csv
- dashboard.export.excel
```

### AGR-004: Admin Usuarios

**Perfil:** Gestiona usuarios del sistema

**Funciones (12):**
```yaml
Hereda de AGR-001 (7) +
- users.view_user
- users.add_user
- users.change_user
- users.delete_user
- users.reset_password
```

**⚠️ Conflicto SoD:** NO puede tener funciones de auditoría (AGR-006)

### AGR-005: Admin RBAC

**Perfil:** Gestiona permisos y accesos

**Funciones (12):**
```yaml
Hereda de AGR-001 (7) +
- access.assign_functions
- access.revoke_functions
- access.view_permissions
- access.manage_groups
- access.view_separation
```

### AGR-006: Auditor

**Perfil:** Revisa logs y auditoría

**Funciones (10):**
```yaml
Hereda de AGR-001 (7) +
- audit.view_log
- audit.search_log
- audit.generate_compliance
```

**⚠️ Conflictos SoD:**
- NO puede tener funciones de AGR-004 (Admin Usuarios)
- NO puede tener funciones de AGR-007 (Supervisor Pipeline)

### AGR-007: Supervisor Pipeline

**Perfil:** Controla ETL

**Funciones (11):**
```yaml
Hereda de AGR-001 (7) +
- pipeline.view_job
- pipeline.execute_job
- pipeline.stop_job
- pipeline.view_logs
```

**⚠️ Conflicto SoD:** NO puede tener funciones de auditoría (AGR-006)

### AGR-008: Admin Alertas

**Perfil:** Gestiona sistema de alertas

**Funciones (10):**
```yaml
Hereda de AGR-001 (7) +
- alerts.configure_alert
- alerts.send_alert
- alerts.manage_subscriptions
```

### AGR-009: Admin Logs

**Perfil:** Acceso a logs técnicos

**Funciones (9):**
```yaml
Hereda de AGR-001 (7) +
- logs.view_technical
- logs.export_logs
```

### AGR-010: Superadministrador

**Perfil:** Acceso completo (excepto conflictos SoD)

**Funciones (42 activas):**
```yaml
TODAS las funciones activas
EXCEPTO:
- Debe respetar reglas SoD
- No puede auditar sus propias acciones si gestiona usuarios/pipeline
```

---

## 🔄 FLUJOS DE TRABAJO

### Workflow 1: Crear Función

```python
# Crear nueva función en el sistema
function = Function.objects.create(
    permission_django='reports.view',  # ← PK
    code='RPT_VIEW',                    # ← Referencial
    display_name='Ver Reportes',
    description='Ve reportes tabulares del sistema',
    module=Module.objects.get(code='MOD_Reports'),
    status='activo'
)

print(f"Función creada: {function.permission_django}")
# Output: Función creada: reports.view
```

### Workflow 2: Asignar Usuario a Grupo

```python
# Obtener usuario y grupo
user = User.objects.get(username='maria')
group = Group.objects.get(code='AGR-002')  # Analista de Reportes

# Asignar usuario al grupo
UserGroup.objects.create(
    user=user,
    group=group,
    assigned_by=admin_user,
    reason='María es analista de reportes',
)

# Dar visibilidad módulo
UserModuleAccess.objects.create(
    user=user,
    module=Module.objects.get(code='MOD_Reports'),
    granted_by=admin_user,
)

# Resultado:
# María ahora:
#   ✅ Ve "Reportes" en el menú (UserModuleAccess)
#   ✅ Puede ver reportes (reports.view via Group)
#   ✅ Puede exportar reportes (reports.export.csv via Group)
```

### Workflow 3: Verificar Permisos en ViewSet

```python
# apps/reports/views.py

from apps.core.permissions import RequiresFunctionPermission

class ReportViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de reportes."""
    
    permission_classes = [
        IsAuthenticated,
        RequiresFunctionPermission,
    ]
    
    # Mapeo actions → permission_django
    function_map = {
        'list': 'reports.view',
        'retrieve': 'reports.view',
        'create': 'reports.create',
        'update': 'reports.create',
        'destroy': 'reports.delete',
        'export_csv': 'reports.export.csv',
        'export_excel': 'reports.export.excel',
    }
    
    @action(detail=True, methods=['post'])
    def export_csv(self, request, pk=None):
        """
        Exportar reporte a CSV.
        Requiere: reports.export.csv
        """
        # RequiresFunctionPermission verifica automáticamente
        # user.has_function('reports.export.csv')
        report = self.get_object()
        return export_to_csv(report)

# Flujo verificación:
# 1. User hace: POST /api/v1/reports/123/export_csv/
# 2. RequiresFunctionPermission intercepta
# 3. Busca en function_map: 'export_csv' → 'reports.export.csv'
# 4. Llama user.has_function('reports.export.csv')
# 5. Busca: UserGroup → Group → GroupFunction → Function
# 6. Si encuentra 'reports.export.csv' → 200 OK
# 7. Si no encuentra → 403 Forbidden
```

### Workflow 4: Verificar Permisos Manualmente

```python
# Obtener usuario
user = User.objects.get(username='maria')

# Verificar si tiene función específica
if user.has_function('reports.view'):
    print("✅ María puede ver reportes")
else:
    print("❌ María NO puede ver reportes")

# Obtener todas las funciones del usuario
functions = user.get_user_functions()
print(f"Funciones: {[f.permission_django for f in functions]}")
# Output: ['auth.login', 'reports.view', 'reports.export.csv']

# Verificar con permission_django (PK)
function = Function.objects.get(permission_django='reports.export.csv')
if function in functions:
    print("✅ María puede exportar CSV")
```

---

## 🌐 API ENDPOINTS

### Funciones

```http
GET    /api/v1/access/functions/
  Lista todas las funciones
  Filtros: module, status, permission_django

POST   /api/v1/access/functions/
  Crea nueva función
  Requiere: access.manage_groups

GET    /api/v1/access/functions/{permission_django}/
  Detalle de función
  Ejemplo: GET /api/v1/access/functions/reports.view/

PUT    /api/v1/access/functions/{permission_django}/
  Actualiza función
  Requiere: access.manage_groups
```

### Grupos

```http
GET    /api/v1/access/groups/
  Lista todos los grupos
  Filtros: code

GET    /api/v1/access/groups/{code}/
  Detalle de grupo con funciones
  Ejemplo: GET /api/v1/access/groups/AGR-002/

POST   /api/v1/access/user-groups/
  Asigna usuario a grupo
  Requiere: access.assign_functions
  Body: {user_id, group_code, reason}
```

### UserModuleAccess

```http
GET    /api/v1/access/module-accesses/
  Lista accesos a módulos
  Filtros: user, module, is_active

POST   /api/v1/access/module-accesses/
  Otorga acceso a módulo
  Requiere: access.assign_functions

GET    /api/v1/access/my-modules/
  Módulos accesibles del usuario autenticado
  Retorna: árbol jerárquico de módulos
  Usado por: Frontend para renderizar menú
```

---

## 💡 EJEMPLOS DE USO

### Ejemplo 1: Sistema RBAC Básico

```python
# 1. Obtener función por permission_django (PK)
view_reports = Function.objects.get(
    permission_django='reports.view'
)

export_csv = Function.objects.get(
    permission_django='reports.export.csv'
)

# 2. Crear grupo personalizado
analyst_group = Group.objects.create(
    code='AGR-CUSTOM-01',
    name='Analista Personalizado',
    description='Grupo custom para proyecto X'
)

# 3. Asignar funciones al grupo
GroupFunction.objects.bulk_create([
    GroupFunction(group=analyst_group, function=view_reports),
    GroupFunction(group=analyst_group, function=export_csv),
])

# 4. Asignar usuario al grupo
user = User.objects.get(username='juan')
UserGroup.objects.create(
    user=user,
    group=analyst_group,
    assigned_by=admin,
    reason='Proyecto X - análisis trimestral'
)

# 5. Verificar
assert user.has_function('reports.view') == True
assert user.has_function('reports.export.csv') == True
assert user.has_function('reports.delete') == False

print("✅ Sistema RBAC configurado correctamente")
```

### Ejemplo 2: Migración de Permisos Django

```python
# Script para migrar permisos Django legacy a RBAC

from django.contrib.auth.models import Permission

# Mapeo permisos Django → permission_django RBAC
PERMISSION_MAPPING = {
    'reports.view_report': 'reports.view',
    'reports.add_report': 'reports.create',
    'reports.delete_report': 'reports.delete',
    'dashboard.view_dashboard': 'dashboard.view',
}

def migrate_permissions():
    migration_group = Group.objects.create(
        code='AGR-MIGRATED',
        name='Permisos Migrados',
    )
    
    users_with_perms = User.objects.exclude(
        user_permissions__isnull=True
    ).distinct()
    
    for user in users_with_perms:
        django_perms = user.user_permissions.all()
        
        for perm in django_perms:
            perm_key = f"{perm.content_type.app_label}.{perm.codename}"
            
            if perm_key in PERMISSION_MAPPING:
                rbac_perm = PERMISSION_MAPPING[perm_key]
                
                try:
                    function = Function.objects.get(
                        permission_django=rbac_perm  # ← Usar PK
                    )
                    
                    GroupFunction.objects.get_or_create(
                        group=migration_group,
                        function=function,
                    )
                except Function.DoesNotExist:
                    print(f"⚠️  Función {rbac_perm} no existe")
        
        UserGroup.objects.get_or_create(
            user=user,
            group=migration_group,
        )
    
    print(f"✅ Migrados {users_with_perms.count()} usuarios")

# Ejecutar
migrate_permissions()
```

### Ejemplo 3: Dashboard de Usuario

```python
from apps.access.services import ModuleAccessService

def user_dashboard(request):
    """Vista dashboard del usuario."""
    user = request.user
    
    # Obtener módulos con jerarquía
    modules = ModuleAccessService.get_user_modules(user)
    
    # Obtener funciones activas del usuario
    functions = user.get_user_functions().filter(status='activo')
    
    # Agrupar funciones por módulo
    functions_by_module = {}
    for func in functions:
        module = func.module.code
        if module not in functions_by_module:
            functions_by_module[module] = []
        functions_by_module[module].append({
            'permission': func.permission_django,
            'name': func.display_name,
            'code': func.code,  # Referencial
        })
    
    context = {
        'modules': modules,
        'functions_count': functions.count(),
        'functions_by_module': functions_by_module,
    }
    
    return render(request, 'dashboard.html', context)
```

---

## 📚 DOCUMENTACIÓN ADICIONAL

### Documentos Relacionados

```yaml
Modelo RBAC Oficial:
  - docs/rbac/MODELO_RBAC_IACT_v6_0_0_PARTE_1.md ⭐
  - docs/rbac/MODELO_RBAC_IACT_v6_0_0_PARTE_2.md ⭐

Análisis y Decisiones:
  - docs/ejecucion/FASE_A_COMPLETADO.md (UserServiceAccess eliminado)
  - docs/ejecucion/FASE_B_ANALISIS_USER_MODULE_ACCESS.md (Análisis)
  - docs/ejecucion/FASE_C_COMPLETADO.md (Documentación v1)
  - docs/ejecucion/PLAN_CORRECCION_v4_0_0.md (Esta corrección)

Arquitectura:
  - URLS_REPORTES_Y_DASHBOARDS.md (Separación apps/)
  - CLEAN_CODE_NAMING_PRINCIPLES_v3_0_1.md
  - RESTRICCIONES_ARQUITECTONICAS_IACT_v1_0_0.md

Deuda Técnica:
  - docs/DEUDA_TECNICA.md (DT-002 resuelto)
```

### Glosario

```yaml
permission_django:
  Clave primaria de Function
  Formato: app.action o app.action.format
  Ejemplo: reports.view, dashboard.export.csv

code:
  Código referencial de Function (NO es PK)
  Formato: MÓDULO_ACCIÓN o MÓDULO_PREFIJO_ACCIÓN
  Ejemplo: RPT_VIEW, DSH_EXP_CSV

display_name:
  Nombre en español para UI
  Ejemplo: Ver Reportes, Exportar CSV

RBAC:
  Role-Based Access Control
  Sistema de permisos basado en funciones

Flat RBAC:
  RBAC sin jerarquías de roles
  Funciones son composables via Groups

SoD:
  Separation of Duties
  Reglas de separación de funciones
  Evitan conflictos de interés
```

---

## ⚠️ NOTAS IMPORTANTES

### UserServiceAccess ELIMINADO

```yaml
IMPORTANTE: UserServiceAccess fue eliminado en FASE A (DT-002)

Razón:
  - Mezclaba RBAC con servicios 800
  - Redundante con RBAC puro
  - Reemplazado por Functions

Migración:
  - apps/access/migrations/0003_remove_user_service_access.py
  - Usar RequiresFunctionPermission en ViewSets

Ver: docs/ejecucion/FASE_A_COMPLETADO.md
```

### UserModuleAccess MANTENIDO

```yaml
IMPORTANTE: UserModuleAccess se mantiene (FASE B)

Razón:
  - Controla VISIBILIDAD UI (qué módulos ve)
  - Complementario a RBAC (no redundante)
  - API MyModulesView usado por frontend

Propósito:
  - UserModuleAccess: "¿Qué módulos veo en menú?"
  - Groups/RBAC: "¿Qué puedo hacer?"

Ver: docs/ejecucion/FASE_B_ANALISIS_USER_MODULE_ACCESS.md
```

### Corrección v4.0.0

```yaml
CRÍTICO: README corregido en FASE D

Error original:
  ❌ Usaba códigos (RPT_VIEW) como clave primaria
  ❌ Funciones inventadas, no basadas en modelo oficial

Corrección:
  ✅ permission_django como clave primaria
  ✅ code solo referencial
  ✅ Basado 100% en MODELO_RBAC_IACT_v6_0_0

Ver: docs/ejecucion/PLAN_CORRECCION_v4_0_0.md
```

### Mejores Prácticas

```yaml
1. Usar permission_django en código:
   ✅ Function.objects.get(permission_django='reports.view')
   ❌ Function.objects.get(code='RPT_VIEW') # Solo para ref

2. Usar Groups, no asignar Functions directamente:
   ✅ Crear AGR-CUSTOM, asignar grupo a usuario
   ❌ Asignar reports.view directamente

3. Respetar reglas SoD:
   ✅ Validar conflictos antes de asignar
   ❌ Admin Usuarios NO puede ser Auditor

4. UserModuleAccess + Group siempre juntos:
   ✅ Dar visibilidad módulo + permisos functions
   ❌ Solo uno de los dos

5. Documentar razón en asignaciones:
   ✅ UserGroup(reason='Proyecto X - análisis')
   ❌ UserGroup(reason='')
```

---

## 📊 RESUMEN

```yaml
Componentes:
  - 46 funciones (42 activas + 4 planificadas)
  - 9 módulos funcionales
  - 10 grupos predefinidos
  - 3 reglas SoD

Características:
  ✅ Permisos granulares (nivel action)
  ✅ Flat RBAC (no jerarquías)
  ✅ Agrupación via Groups
  ✅ Auditoría completa
  ✅ Permisos temporales
  ✅ API REST completa

Estado:
  ✅ Producción ready
  ✅ Basado en MODELO_RBAC_IACT_v6_0_0
  ✅ Corregido v4.0.0
  ✅ 100% alineado con arquitectura oficial
```

---

**Versión:** 6.0.0 (Corregido v4.0.0)  
**Última actualización:** 2026-01-21 (FASE D)  
**Basado en:** MODELO_RBAC_IACT_v6_0_0_PARTE_1.md  
**Mantenido por:** IACT Development Team
