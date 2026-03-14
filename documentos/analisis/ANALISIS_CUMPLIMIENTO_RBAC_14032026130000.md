# ANÁLISIS DE CUMPLIMIENTO - RBAC v7.0.0 vs IMPLEMENTACIÓN
**Sistema IACT - Análisis IVR**
**Fecha de análisis:** 2026-03-14 13:00:00 UTC
**Proyecto analizado:** /home/user/IACT-api/callcentersite
**Diccionario base:** ANALISIS_DICCIONARIO_PERMISOS_14032026130000.md

---

## RESUMEN EJECUTIVO

| Categoría | Estado | Detalle |
|-----------|--------|---------|
| Modelo Usuario & Funciones | ✅ Completo | Function, UserFunctionAssignment, SoftDeleteMixin |
| Validación SoD (3 reglas) | ⚠️ Parcial | Documentado en README, **NO validado en código** |
| MOD_Auth - Endpoints | ✅ Completo | 11 endpoints implementados |
| MOD_Users - Endpoints | ✅ Completo | CRUD + activate/deactivate + soft delete |
| MOD_Access - Endpoints | ⚠️ Parcial | Módulos sí, falta assign/revoke de funciones directas |
| MOD_Reports - Endpoints | ✅ Completo | CRUD + export |
| MOD_Audit - Endpoints | ✅ Completo | Read-only, inmutable, búsqueda y filtros |
| Soft Delete (CNST-014) | ✅ Completo | SoftDeleteMixin en todos los modelos relevantes |
| AuditLog (inmutable) | ✅ Completo | save/delete override, action, result, details JSON |
| DeletionLog (inmutable) | ❌ No existe | Tabla específica para borrados no implementada |
| CNST-010 (límite exportación) | ⚠️ Parcial | Constante = 100K (diccionario dice 10K) |
| CNST-011 (username) | ✅ Implementado | Django AbstractUser |
| CNST-012 (email) | ✅ Implementado | Django AbstractUser |
| CNST-013 (90 días inactivo) | ⚠️ Parcial | Constante definida, sin lógica automática |
| CNST-015 (retención 7 años) | ❌ No implementado | Sin política de retención |
| Permisos RBAC | ✅ Completo | RequiresFunctionPermission + function_map |

---

## ANÁLISIS DETALLADO POR MÓDULO

### 1. MODELO BASE DE PERMISOS

#### Function (Funciones Atómicas)
✅ **IMPLEMENTADO** — `apps/access/models.py`
- `permission_django` (CharField unique, db_index) — clave funcional del sistema RBAC
- `code` (CharField unique) — código referencial (ej: `users.view`)
- `module` (ForeignKey a Module)
- `name`, `description`, `status` (activo/planificado/deprecado), `is_active`
- Hereda `SoftDeleteMixin`

#### UserFunctionAssignment
✅ **IMPLEMENTADO** — `apps/access/models.py`
- FK a User y Function
- `assigned_at`, `assigned_by`, `reason` — auditoría completa
- `is_active`, `revoked_at`, `revoked_by` — soft revoke con timestamp
- `unique_together = [['user', 'function']]` — previene duplicados
- Índices optimizados: `(user, is_active)`, `(function, is_active)`

---

### 2. VALIDACIÓN SOD

⚠️ **PARCIALMENTE IMPLEMENTADO**

| Regla SoD | Diccionario | Estado en código |
|-----------|-------------|-----------------|
| SoD 1: `access.assign` ↔ `access.revoke` | ✅ Definida | ❌ No validada en código |
| SoD 2: `users.create/edit/delete` ↔ `audit.view/search` | ✅ Definida | ❌ No validada en código |
| SoD 3: `reports.modify_data` ↔ `reports.approve` | ✅ Definida | ❌ No validada en código |

**Hallazgo:** Las reglas SoD están documentadas en `apps/access/README.md` (líneas 531-576) pero no existe:
- Validador en `UserFunctionAssignment.save()`
- Service que verifique conflictos antes de asignar
- Modelo `SoDRule` o similar
- Endpoint que exponga las reglas SoD

**Archivo:** `apps/access/README.md` líneas 531-576 (solo documentación)

---

### 3. MOD_Auth — Autenticación

✅ **IMPLEMENTADO COMPLETO** — `apps/authentication/viewsets.py`

| Función del diccionario | Endpoint implementado | Estado |
|------------------------|----------------------|--------|
| auth.login | `POST /api/v1/auth/login/` | ✅ |
| auth.logout | `POST /api/v1/auth/logout/` | ✅ |
| auth.recover_password | `POST /api/v1/auth/reset-password/` + `verify-security-answers/` | ✅ |
| auth.manage_sessions | `GET/POST /api/v1/sessions/` + `invalidate/` + `invalidate-all/` | ✅ |

**Modelos adicionales:** `LoginAttempt`, `SessionLog`, `SecurityQuestion`, `UserSecurityAnswer`, `LoginLockout`

---

### 4. MOD_Users — Gestión de Usuarios

✅ **IMPLEMENTADO COMPLETO** — `apps/users/viewsets.py`

| Función del diccionario | Endpoint implementado | Estado |
|------------------------|----------------------|--------|
| users.view | `GET /api/v1/users/` | ✅ |
| users.create | `POST /api/v1/users/` | ✅ |
| users.edit | `PUT/PATCH /api/v1/users/{id}/` | ✅ |
| users.delete | `DELETE /api/v1/users/{id}/` (soft delete) | ✅ |
| users.reset_password | `POST /api/v1/users/{id}/reset-password/` | ✅ (vía auth app) |
| users.lock | `POST /api/v1/users/{id}/deactivate/` | ⚠️ (deactivate ≠ lock temporal) |
| users.unlock | `POST /api/v1/users/{id}/activate/` | ⚠️ (activate ≠ unlock temporal) |
| users.search | Filtros en `GET /api/v1/users/?search=...` | ⚠️ (no endpoint dedicado) |
| users.export | No encontrado | ❌ |

**Nota sobre lock/unlock:** El diccionario define `users.lock` como bloqueo **temporal** (is_locked + locked_until), pero la implementación usa `deactivate` (is_active=false), que es equivalente a `users.delete`. Son semánticamente distintos.

**Soft delete:** ✅ Correcto — User hereda `SoftDeleteMixin` con `is_deleted` + `deleted_at`

---

### 5. MOD_Access — Gestión de Permisos

⚠️ **PARCIALMENTE IMPLEMENTADO** — `apps/access/views.py`

| Función del diccionario | Endpoint implementado | Estado |
|------------------------|----------------------|--------|
| access.view | `GET /api/v1/access/my-modules/` + `module-accesses/` | ⚠️ (módulos, no funciones) |
| access.assign | `POST /api/v1/access/module-accesses/` | ⚠️ (asigna módulos, no funciones atómicas) |
| access.revoke | No encontrado como endpoint | ❌ |

**Hallazgo crítico:** El sistema implementa asignación de **módulos** (UserModuleAccess), pero el diccionario define asignación de **funciones atómicas** individuales (UserFunctionAssignment). Aunque el modelo UserFunctionAssignment existe, no hay endpoints para manipularlo directamente.

**Falta:**
- `POST /api/v1/users/{id}/functions/assign`
- `POST /api/v1/users/{id}/functions/revoke`
- `GET /api/v1/users/{id}/functions`
- `GET /api/v1/access/sod-rules/`

---

### 6. MOD_Reports — Reportes y Análisis

✅ **IMPLEMENTADO** — `apps/reports/views.py`

| Función del diccionario | Endpoint implementado | Estado |
|------------------------|----------------------|--------|
| reports.view_basic | `GET /api/v1/reports/` | ⚠️ (no separación básico/avanzado) |
| reports.view_advanced | `GET /api/v1/reports/` | ⚠️ (mismo endpoint) |
| reports.export | `POST /api/v1/reports/{id}/export/` | ✅ |
| reports.modify_data | No encontrado | ❌ |
| reports.approve | No encontrado | ❌ |
| reports.schedule | No encontrado | ❌ |

**Permisos reportes:** `CanViewReports`, `CanCreateReports`, `CanExportReports`, `IsReportOwner` — implementados en `apps/reports/permissions.py`

**Límite exportación:** Constante `MAX_EXPORT_ROWS = 100000` (100K) en `apps/utils/constants.py`. El diccionario indica 10,000. **Hay discrepancia.**

---

### 7. MOD_Audit — Auditoría y Compliance

✅ **IMPLEMENTADO COMPLETO** — `apps/audit/`

| Función del diccionario | Endpoint implementado | Estado |
|------------------------|----------------------|--------|
| audit.view | `GET /api/v1/audit/logs/` | ✅ |
| audit.search | Filtros en `GET /api/v1/audit/logs/?search=...&action=...` | ⚠️ (no endpoint dedicado) |
| audit.delete | No existe (ReadOnlyModelViewSet) | ❌ (intencionalmente no implementado) |

**AuditLog inmutable:** ✅
- `save()` override: lanza `PermissionError` si `pk` existe (previene UPDATE)
- `delete()` override: lanza `PermissionError` siempre
- `record()` classmethod para crear logs correctamente

**DeletionLog:** ❌ No existe — La tabla inmutable para auditar eliminaciones de logs no está implementada.

---

### 8. RESTRICCIONES TÉCNICAS (CNST)

| Constante | Descripción | Estado | Archivo |
|-----------|-------------|--------|---------|
| CNST-010 | Exportación máx. 10K registros | ⚠️ Implementado en 100K | `apps/utils/constants.py` (MAX_EXPORT_ROWS=100000) |
| CNST-011 | Username único, alfanumérico 3-30 | ✅ | Django AbstractUser |
| CNST-012 | Email único, formato válido | ✅ | Django AbstractUser |
| CNST-013 | Usuario inactivo tras 90 días sin login | ⚠️ Constante definida, sin lógica automática | `SESSION_CLEANUP_DAYS=90` |
| CNST-014 | Soft delete obligatorio | ✅ | `apps/core/models.py` SoftDeleteMixin |
| CNST-015 | Retención de auditoría 7 años | ❌ No implementado | Sin política de retención |

---

### 9. SISTEMA DE PERMISOS (RequiresFunctionPermission)

✅ **IMPLEMENTADO COMPLETO** — `apps/core/permissions.py`

- Verifica `permission_django` usando `has_function()` del usuario
- Soporta `function_map` en ViewSet: mapea acciones → permisos
  ```python
  function_map = {
      'list': 'users.view_user',
      'create': 'users.add_user',
      'destroy': 'users.delete_user',
  }
  ```
- Superusers bypasean validación (`is_superuser=True`)
- Sin `function_map` → permite acceso (sin restricción RBAC)

---

### 10. SIGNALS Y EVENTOS AUTOMÁTICOS

✅ **IMPLEMENTADO** — `apps/users/signals.py`

| Signal | Acción | Estado |
|--------|--------|--------|
| `post_save(User)` | Crea `UserProfile` automáticamente | ✅ |
| `post_save(User)` | Crea `UserSettings` automáticamente | ✅ |
| `user_logged_in` | Crea `SessionHistory` | ✅ |
| `user_logged_out` | Actualiza `SessionHistory.logout_at` | ✅ |

---

## BRECHAS CRÍTICAS IDENTIFICADAS

### 🔴 CRÍTICO — Requiere implementación inmediata

1. **Validación SoD no existe en código**
   - Las 3 reglas SoD solo están en README
   - Riesgo: Se pueden asignar funciones incompatibles sin bloqueo
   - Solución: Agregar validador en `UserFunctionAssignment.save()` o service

2. **Endpoints assign/revoke de funciones atómicas faltantes**
   - Existe el modelo `UserFunctionAssignment` pero no hay endpoints
   - Actualmente solo se puede asignar **módulos** (no funciones individuales)
   - Falta: `POST /api/v1/users/{id}/functions/assign` y `revoke`

3. **users.lock ≠ deactivate implementado**
   - El diccionario define `is_locked` + `locked_until` (bloqueo temporal)
   - La implementación usa `is_active=False` (equivale a delete, no a lock)
   - No existe campo `is_locked` ni `locked_until` en modelo User

### 🟡 IMPORTANTE — Requiere atención

4. **DeletionLog no implementado**
   - No hay tabla inmutable para auditar eliminaciones de registros de auditoría
   - CNST-015 no completamente cubierto

5. **CNST-010 discrepancia: 10K vs 100K**
   - Diccionario dice límite de 10,000 registros en exportación
   - Código implementa `MAX_EXPORT_ROWS = 100000` (100K)
   - Requiere alineación

6. **CNST-013 sin automatización**
   - La constante `SESSION_CLEANUP_DAYS=90` está definida
   - No hay tarea programada o señal que desactive usuarios tras 90 días de inactividad

7. **reports.modify_data / reports.approve / reports.schedule no implementados**
   - Tres funciones del MOD_Reports no tienen endpoints
   - El flujo de dual-control (modificar → aprobar) no existe en código

8. **audit.search sin endpoint dedicado**
   - El diccionario define búsqueda avanzada en histórico completo (sin límite)
   - La implementación usa filtros en el mismo endpoint `audit/logs/`

### 🟢 MENOR — Mejoras opcionales

9. **users.export no implementado**
   - `GET /api/v1/users/export` no existe
   - Solo existe exportación de reportes

10. **CNST-015 retención 7 años**
    - No hay política automática de retención ni archivado

---

## ARCHIVOS CLAVE DEL PROYECTO

```
callcentersite/apps/
├── access/
│   ├── models.py          → Function, UserFunctionAssignment, Module, UserModuleAccess
│   ├── views.py           → ModuleViewSet, UserModuleAccessViewSet, MyModulesView
│   ├── urls.py
│   └── README.md          → Documentación RBAC v6.0.0 (SoD solo aquí)
├── authentication/
│   ├── models.py          → LoginAttempt, SessionLog, SecurityQuestion, LoginLockout
│   ├── viewsets.py        → AuthViewSet (login/logout/reset), SessionViewSet
│   └── urls.py
├── users/
│   ├── models.py          → User + SoftDeleteMixin, UserProfile, SessionHistory
│   ├── viewsets.py        → UserViewSet, ProfileViewSet, SessionHistoryViewSet
│   ├── signals.py         → post_save → Profile/Settings, logged_in/out → SessionHistory
│   └── urls.py
├── audit/
│   ├── models.py          → AuditLog (inmutable: save/delete override)
│   ├── views.py           → AuditLogViewSet (ReadOnly)
│   └── urls.py
├── reports/
│   ├── models.py          → Report, ExportJob (SoftDeleteMixin)
│   ├── views.py           → ReportViewSet, ExportJobViewSet
│   ├── permissions.py     → CanViewReports, CanCreateReports, CanExportReports
│   └── urls.py
├── core/
│   ├── models.py          → TimeStampedModel, SoftDeleteMixin, AuditedModel
│   ├── permissions.py     → RequiresFunctionPermission, IsOwnerOrReadOnly
│   └── services.py
└── utils/
    └── constants.py       → MAX_EXPORT_ROWS=100000, SESSION_CLEANUP_DAYS=90
```

---

## PUNTUACIÓN DE CUMPLIMIENTO

| Módulo | Funciones documentadas | Implementadas | % Cumplimiento |
|--------|----------------------|---------------|----------------|
| MOD_Auth | 4 | 4 | **100%** |
| MOD_Users | 9 | 6 | **67%** |
| MOD_Access | 3 | 1 | **33%** |
| MOD_Reports | 6 | 2 | **33%** |
| MOD_Audit | 3 | 2 | **67%** |
| **TOTAL** | **25** | **15** | **60%** |

| Infraestructura | Estado |
|----------------|--------|
| Modelo RBAC base | ✅ 100% |
| Validación SoD | ❌ 0% |
| Soft delete | ✅ 100% |
| AuditLog inmutable | ✅ 100% |
| DeletionLog | ❌ 0% |
| Restricciones CNST | ⚠️ 60% |

---

*Análisis generado automáticamente: 2026-03-14 13:00:00 UTC*
*Herramienta: Claude Code — IACT-api análisis RBAC*
