# PLAN DE IMPLEMENTACIÓN POR FASES — IACT API
## Cierre de Brechas y Fortalecimiento del Sistema

**Versión:** 1.0.0
**Fecha:** 2026-03-21
**Autor:** Claude Code — Análisis automatizado
**Documentos base:**
- `documentos/analisis/ANALISIS_BRECHAS_AUTH_LOGIN_15032026.md`
- `documentos/analisis/ANALISIS_CUMPLIMIENTO_RBAC_14032026130000.md`
- `documentos/analisis/ANALISIS_DICCIONARIO_PERMISOS_14032026130000.md`

---

## ESTADO ACTUAL DEL PROYECTO

### Verificación de funcionamiento (2026-03-21)

| Componente | Estado | Detalle |
|---|---|---|
| Django system check (`testing`) | ✅ 0 errores | `python manage.py check` limpio |
| Deploy check | ⚠️ Warnings esperados | SSL/HSTS en testing — OK |
| drf_spectacular | ⚠️ Warnings de schema | No bloquean funcionamiento |
| Tests (`tests/`) | ❌ No coleccionan | `factories/access_factories.py` importa `Role`, `UserRoleAssignment`, `RoleFunctionAssignment` — no existen en RBAC v7.0.0 |
| Tests (`apps/`) | ❌ Sin DB | PostgreSQL no disponible en este entorno (esperado) |
| `pipeline/viewsets.py` | ⚠️ Schema roto | Referencias a serializers no definidos: `CallRecordBulkCreateSerializer`, `DailyStatsSerializer`, `ServiceStatsSerializer`, `TopCallerSerializer` |

### Cumplimiento general por módulo

| Módulo | Funciones documentadas | Implementadas | % |
|---|---|---|---|
| MOD_Auth | 4 | 4 | **100%** |
| MOD_Users | 9 | 6 | **67%** |
| MOD_Access | 3 | 1 | **33%** |
| MOD_Reports | 6 | 2 | **33%** |
| MOD_Audit | 3 | 2 | **67%** |
| **TOTAL** | **25** | **15** | **60%** |

---

## RESUMEN DE BRECHAS IDENTIFICADAS

### Brechas Críticas (bloquean seguridad o funcionamiento)

| ID | Origen | Brecha | Prioridad |
|---|---|---|---|
| B-01 | Auth | JWT vs DRF Token (tokens sin expiración) | P1 — CRÍTICA |
| B-02 | Tests | `access_factories.py` importa modelos inexistentes (`Role`, etc.) | P1 — CRÍTICA |
| B-03 | Pipeline | Serializers no definidos en `viewsets.py` | P1 — CRÍTICA |
| B-04 | RBAC | Validación SoD no existe en código | P2 — ALTA |
| B-05 | RBAC | Endpoints assign/revoke de funciones atómicas faltan | P2 — ALTA |
| B-06 | Auth | `users.lock` implementado como `deactivate` (semántica incorrecta) | P2 — ALTA |

### Brechas Importantes

| ID | Origen | Brecha | Prioridad |
|---|---|---|---|
| B-07 | Auth | Throttling por IP en login (solo bloqueo por username hoy) | P2 — ALTA |
| B-08 | Auth | Inactividad automática 90 días (CNST-013 sin automatización) | P2 — ALTA |
| B-09 | Auth | `is_locked` en User vs tabla `LoginLockout` separada | P3 — MEDIA |
| B-10 | Auth | `UserActionLog` centralizado vs `LoginAttempt` específico | P3 — MEDIA |
| B-11 | RBAC | `DeletionLog` no implementado | P3 — MEDIA |
| B-12 | RBAC | CNST-010: límite exportación 100K vs 10K en diccionario | P3 — MEDIA |
| B-13 | RBAC | `reports.modify_data`, `reports.approve`, `reports.schedule` sin endpoint | P3 — MEDIA |
| B-14 | RBAC | `users.export` sin endpoint | P3 — MEDIA |
| B-15 | RBAC | CNST-015: retención 7 años sin política automática | P3 — MEDIA |

### Brechas Menores (mejoras de calidad)

| ID | Origen | Brecha | Prioridad |
|---|---|---|---|
| B-16 | Auth | Campos `full_name`, `last_login`, `date_joined` faltan en response | P4 — BAJA |
| B-17 | Auth | `locked_until` timestamp vs `locked_minutes` entero | P4 — BAJA |
| B-18 | Auth | Detección de sesión duplicada (Flujo A5) | P4 — BAJA |
| B-19 | Schema | drf_spectacular: type hints faltantes en serializers | P5 — COSMÉTICA |

---

## FASES DE IMPLEMENTACIÓN

---

### FASE 0 — ESTABILIZACIÓN (Prerequisito)
**Objetivo:** Dejar el proyecto 100% coleccionable y sin errores estructurales antes de implementar nuevas funcionalidades.
**Duración estimada:** 1–2 días
**Dependencias:** Ninguna

#### Tarea 0.1 — Corregir factories de tests (B-02)

**Archivos afectados:**
- `callcentersite/tests/factories/access_factories.py`
- `callcentersite/tests/factories/__init__.py`

**Problema:** `access_factories.py` importa `Role`, `UserRoleAssignment`, `RoleFunctionAssignment` que no existen en RBAC v7.0.0 (flat — sin roles).

**Solución:**
1. Eliminar `RoleFactory`, `AdminRoleFactory`, `ManagerRoleFactory`, `AnalystRoleFactory`, `ViewerRoleFactory`, `UserRoleAssignmentFactory`, `RoleFunctionAssignmentFactory` de `access_factories.py`
2. Actualizar importaciones en `__init__.py` para no exportar las factories eliminadas
3. Reemplazar usos de `RoleFactory` en tests con `UserFunctionAssignmentFactory`
4. Verificar que `python -m pytest --collect-only` no lanza `ImportError`

**Criterio de aceptación:** `pytest --collect-only` en `tests/` sin errores de importación.

---

#### Tarea 0.2 — Corregir serializers faltantes en pipeline (B-03)

**Archivos afectados:**
- `callcentersite/apps/pipeline/viewsets.py` (líneas 427–433)
- `callcentersite/apps/pipeline/serializers/callrecord_serializers.py`

**Problema:** `CallRecordViewSet.get_serializer_class()` referencia serializers no definidos.

**Solución (opción A — preferida):**
1. Crear los serializers faltantes en `callrecord_serializers.py`:
   - `CallRecordBulkCreateSerializer` — campos básicos de CallRecord para creación masiva
   - `DailyStatsSerializer` — campos de estadísticas diarias (fecha, total, resueltos, etc.)
   - `ServiceStatsSerializer` — estadísticas por servicio
   - `TopCallerSerializer` — datos de top callers (número, cantidad de llamadas, etc.)
2. Exportarlos desde `serializers/__init__.py`

**Solución (opción B — si los actions no están implementados):**
1. Retornar `CallRecordSerializer` como fallback en `get_serializer_class()` hasta que los actions estén completos.

**Criterio de aceptación:** `python manage.py check` sin `W002` en `pipeline/viewsets.py`.

---

### FASE 1 — SEGURIDAD CRÍTICA
**Objetivo:** Cerrar las brechas de seguridad de mayor impacto.
**Duración estimada:** 3–5 días
**Dependencias:** Fase 0 completada

#### Tarea 1.1 — Throttling por IP en login (B-07)

**Archivos a crear/modificar:**
- `callcentersite/apps/authentication/throttles.py` ← nuevo archivo
- `callcentersite/config/settings/base.py`
- `callcentersite/apps/authentication/viewsets.py`
- `callcentersite/tests/` — tests nuevos

**Implementación:**

```python
# apps/authentication/throttles.py
from rest_framework.throttling import AnonRateThrottle

class LoginRateThrottle(AnonRateThrottle):
    scope = 'login'
```

```python
# config/settings/base.py — en REST_FRAMEWORK
'DEFAULT_THROTTLE_RATES': {
    'anon': '100/hour',
    'user': '1000/hour',
    'login': '5/minute',
}
```

```python
# apps/authentication/viewsets.py — en action login
@action(methods=['post'], detail=False, throttle_classes=[LoginRateThrottle])
def login(self, request):
    ...
```

**Manejo de Throttled exception:**
- Capturar `Throttled` en el viewset o en el exception handler global
- Retornar formato: `{"success": false, "error_code": "AUTH-005", "retry_after": 900, "blocked_until": "..."}`

**Tests a escribir:**
- `test_login_throttle_blocks_after_5_requests_per_minute`
- `test_login_throttle_resets_after_minute`
- `test_throttle_response_format_includes_retry_after`

---

#### Tarea 1.2 — JWT: access token + refresh token (B-01)

**Archivos a modificar:**
- `callcentersite/config/settings/base.py`
- `callcentersite/apps/authentication/services/authentication.py`
- `callcentersite/apps/authentication/viewsets.py`
- `callcentersite/apps/authentication/urls.py`
- `callcentersite/tests/conftest.py`
- `callcentersite/tests/` — 22 tests a actualizar

**Pasos de implementación:**

1. Activar `JWTAuthentication` en settings:
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}
```

2. Actualizar `AuthenticationService.login_user()`:
```python
# En lugar de: token, created = Token.objects.get_or_create(user=user)
from rest_framework_simplejwt.tokens import RefreshToken
refresh = RefreshToken.for_user(user)
return {
    'access': str(refresh.access_token),
    'refresh': str(refresh),
    ...
}
```

3. Agregar a `INSTALLED_APPS`:
```python
'rest_framework_simplejwt.token_blacklist',
```

4. Agregar endpoints:
```python
# urls.py
path('auth/token/refresh/', TokenRefreshView.as_view()),
path('auth/token/blacklist/', TokenBlacklistView.as_view()),
```

5. Actualizar logout para invalidar refresh token en blacklist.

6. Actualizar `conftest.py` para usar `Bearer` en lugar de `Token`.

7. Actualizar los 22 tests en `test_views.py` que usan `Token` auth.

**Migración:**
- Ejecutar `python manage.py migrate` para crear tabla de blacklist de simplejwt.

**Tests a actualizar/crear:**
- `test_login_retorna_access_y_refresh_token`
- `test_access_token_expira_en_15_minutos`
- `test_refresh_token_rota_en_cada_uso`
- `test_logout_invalida_refresh_token_en_blacklist`
- `test_token_robado_expira_solo_en_15_minutos`

---

#### Tarea 1.3 — Inactividad automática 90 días (B-08)

**Archivos a crear/modificar:**
- `callcentersite/apps/authentication/tasks.py` ← nuevo o ampliar
- `callcentersite/apps/authentication/scheduler.py`
- `callcentersite/apps/utils/constants.py`

**Implementación:**

```python
# apps/authentication/tasks.py
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

User = get_user_model()
INACTIVITY_DAYS = 90

def deactivate_inactive_accounts():
    cutoff = timezone.now() - timedelta(days=INACTIVITY_DAYS)
    inactive_users = User.objects.filter(
        is_active=True,
        last_login__lt=cutoff,
        is_superuser=False
    )
    count = inactive_users.update(is_active=False)
    # Registrar en auditoría
    return count
```

- Configurar ejecución diaria vía APScheduler (ya en uso en el proyecto).
- Registrar cada desactivación en `AuditLog`.
- Retornar `AUTH-004: "Cuenta inactiva. Contacte al administrador"` al intentar login.

**Tests:**
- `test_cuenta_se_desactiva_tras_90_dias_sin_login`
- `test_superuser_no_se_desactiva_automaticamente`
- `test_login_cuenta_inactiva_retorna_AUTH004`

---

### FASE 2 — MODELO DE DATOS
**Objetivo:** Unificar modelo de usuarios (is_locked) y centralizar auditoría.
**Duración estimada:** 3–4 días
**Dependencias:** Fase 0 completada. Puede ejecutarse en paralelo con Fase 1.

#### Tarea 2.1 — Campo `is_locked` en modelo User (B-06, B-09)

**Archivos a modificar:**
- `callcentersite/apps/users/models.py`
- `callcentersite/apps/users/serializers/user_serializer.py`
- `callcentersite/apps/authentication/services/lockout.py`
- `callcentersite/apps/users/viewsets/` — actions `lock` y `unlock`
- Nueva migración

**Migración:**
```python
# Agregar al modelo User
is_locked = models.BooleanField(default=False)
locked_until = models.DateTimeField(null=True, blank=True)
locked_reason = models.CharField(max_length=500, blank=True)
locked_by = models.ForeignKey(
    'self', null=True, blank=True,
    on_delete=models.SET_NULL,
    related_name='locked_users'
)
```

**Refactor de `LockoutService`:**
- Usar `user.is_locked` y `user.locked_until` en lugar de `LoginLockout`
- Mantener `LoginLockout` como historial (no eliminar todavía)
- `users.lock` → `user.is_locked=True` + `user.locked_until` (bloqueo temporal)
- `users.unlock` → `user.is_locked=False` + `user.locked_until=None`

**Serializer — exponer `is_locked` en response de login (B-16 parcial):**
```python
'user': {
    ...,
    'is_locked': user.is_locked,
    'full_name': f"{user.first_name} {user.last_name}".strip(),
    'last_login': user.last_login,
    'date_joined': user.date_joined,
}
```

**Tests:**
- `test_users_lock_sets_is_locked_true_con_locked_until`
- `test_users_unlock_sets_is_locked_false`
- `test_login_retorna_is_locked_en_user_response`
- `test_lockout_service_usa_user_is_locked`

---

#### Tarea 2.2 — `UserActionLog` centralizado (B-10)

**Archivos a crear/modificar:**
- `callcentersite/apps/audit/models.py` — agregar `UserActionLog`
- Nueva migración en `apps/audit`
- `callcentersite/apps/authentication/services/authentication.py` — actualizar `_record_attempt()`

**Modelo:**
```python
class UserActionLog(models.Model):
    user       = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    action     = models.CharField(max_length=100)  # 'login', 'logout', 'lock', etc.
    resource   = models.CharField(max_length=200, blank=True)
    result     = models.CharField(max_length=50)   # 'success', 'failed', 'blocked'
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(blank=True)
    timestamp  = models.DateTimeField(auto_now_add=True)
    details    = models.JSONField(default=dict)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'action']),
            models.Index(fields=['timestamp']),
        ]
```

- Migrar registros de `LoginAttempt` a `UserActionLog` mediante management command
- Mantener `LoginAttempt` como legacy hasta validar migración

---

### FASE 3 — RBAC COMPLETO
**Objetivo:** Implementar endpoints faltantes de RBAC y validación SoD.
**Duración estimada:** 5–7 días
**Dependencias:** Fase 0 completada. Fase 2.1 recomendada (para `is_locked`).

#### Tarea 3.1 — Endpoints assign/revoke de funciones atómicas (B-05)

**Archivos a crear/modificar:**
- `callcentersite/apps/access/views.py` — nuevas vistas
- `callcentersite/apps/access/urls.py`
- `callcentersite/apps/access/services.py` — lógica de asignación/revocación

**Endpoints nuevos:**
```
GET    /api/v1/users/{id}/functions/              — Listar funciones del usuario
POST   /api/v1/users/{id}/functions/assign/       — Asignar función
POST   /api/v1/users/{id}/functions/revoke/       — Revocar función
GET    /api/v1/access/functions/                  — Listar todas las funciones disponibles
GET    /api/v1/access/sod-rules/                  — Listar reglas SoD
```

**Lógica del service:**
```python
class FunctionAssignmentService:
    def assign_function(self, user, function, assigned_by, reason=''):
        # 1. Verificar reglas SoD antes de asignar
        # 2. Crear UserFunctionAssignment
        # 3. Registrar en AuditLog/UserActionLog

    def revoke_function(self, user, function, revoked_by, reason=''):
        # 1. Marcar is_active=False en UserFunctionAssignment
        # 2. Registrar revoked_at, revoked_by
        # 3. Registrar en AuditLog/UserActionLog
```

---

#### Tarea 3.2 — Validación SoD en código (B-04)

**Archivos a modificar:**
- `callcentersite/apps/access/models.py` — override en `UserFunctionAssignment`
- `callcentersite/apps/access/services.py`

**Implementación:**

```python
# apps/access/models.py
SOD_RULES = [
    # SoD 1: access.assign ↔ access.revoke
    {'incompatible': ['access.assign', 'access.revoke']},
    # SoD 2: users.create/edit/delete ↔ audit.view/search
    {'incompatible': ['users.create', 'users.edit', 'users.delete',
                      'audit.view', 'audit.search']},
    # SoD 3: reports.modify_data ↔ reports.approve
    {'incompatible': ['reports.modify_data', 'reports.approve']},
]

class UserFunctionAssignment(SoftDeleteMixin, models.Model):
    ...
    def clean(self):
        self._validate_sod()

    def _validate_sod(self):
        existing_codes = set(
            self.user.function_assignments
                .filter(is_active=True)
                .values_list('function__code', flat=True)
        )
        new_code = self.function.code
        for rule in SOD_RULES:
            incompatible = rule['incompatible']
            if new_code in incompatible:
                conflicting = existing_codes & (set(incompatible) - {new_code})
                if conflicting:
                    raise ValidationError(
                        f"La función '{new_code}' es incompatible con: {conflicting} (SoD)"
                    )
```

**Endpoint para consultar reglas SoD:**
```
GET /api/v1/access/sod-rules/
→ Retorna lista de reglas con funciones incompatibles
```

**Tests:**
- `test_sod1_no_puede_asignar_access_assign_y_revoke_al_mismo_usuario`
- `test_sod2_no_puede_asignar_users_create_y_audit_view_al_mismo_usuario`
- `test_sod3_no_puede_asignar_reports_modify_y_reports_approve_al_mismo_usuario`

---

#### Tarea 3.3 — MOD_Reports: funciones faltantes (B-13)

**Archivos a crear/modificar:**
- `callcentersite/apps/reports/views.py`
- `callcentersite/apps/reports/urls.py`
- `callcentersite/apps/reports/serializers/`

**Endpoints nuevos:**
```
POST   /api/v1/reports/{id}/modify-data/    — reports.modify_data (propone modificación)
POST   /api/v1/reports/{id}/approve/        — reports.approve (aprueba modificación)
POST   /api/v1/reports/{id}/schedule/       — reports.schedule (programa ejecución)
```

**Flujo dual-control (SoD 3):**
1. `reports.modify_data` → crea `ReportModification` en estado `PENDING`
2. `reports.approve` → valida que quien aprueba ≠ quien modificó (SoD) → aprueba y aplica

---

#### Tarea 3.4 — users.export y corrección CNST-010 (B-14, B-12)

**Archivos a modificar:**
- `callcentersite/apps/users/viewsets/` — agregar action `export`
- `callcentersite/apps/utils/constants.py` — corregir `MAX_EXPORT_ROWS`

**Corrección:**
```python
# apps/utils/constants.py
MAX_EXPORT_ROWS = 10000  # Era 100000 — alinear con CNST-010 del diccionario
```

**Nuevo endpoint:**
```
GET /api/v1/users/export/   — Exporta lista de usuarios (CSV/JSON, máx 10K)
```

---

#### Tarea 3.5 — DeletionLog (B-11)

**Archivos a crear:**
- `callcentersite/apps/audit/models.py` — agregar `DeletionLog`
- Nueva migración

**Modelo:**
```python
class DeletionLog(models.Model):
    """Registro inmutable de eliminaciones de registros de auditoría."""
    deleted_log_id = models.IntegerField()
    deleted_at = models.DateTimeField(auto_now_add=True)
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    reason = models.CharField(max_length=500)
    log_snapshot = models.JSONField()  # copia del AuditLog antes de eliminar

    def save(self, *args, **kwargs):
        if self.pk:
            raise PermissionError("DeletionLog es inmutable")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("DeletionLog no puede eliminarse")
```

---

### FASE 4 — MEJORAS DE CALIDAD DE API
**Objetivo:** Mejorar respuestas de API y experiencia de integración.
**Duración estimada:** 2–3 días
**Dependencias:** Fase 2 completada para `is_locked`.

#### Tarea 4.1 — Campos adicionales en response de login (B-16)

**Archivos a modificar:**
- `callcentersite/apps/authentication/viewsets.py` (línea ~101)

```python
'user': {
    'id': user.id,
    'username': user.username,
    'email': user.email,
    'first_name': user.first_name,
    'last_name': user.last_name,
    'full_name': f"{user.first_name} {user.last_name}".strip(),
    'is_active': user.is_active,
    'is_locked': user.is_locked,     # requiere Fase 2.1
    'last_login': user.last_login,
    'date_joined': user.date_joined,
}
```

---

#### Tarea 4.2 — `locked_until` timestamp en error de lockout (B-17)

**Archivos a modificar:**
- `callcentersite/apps/authentication/services/authentication.py`

```python
# Agregar locked_until al raise AccountLockedError
raise AccountLockedError(
    detail=f"Cuenta bloqueada. Intenta en {minutes} minutos.",
    details={
        'locked_minutes': minutes,
        'locked_until': locked_until.isoformat() if locked_until else None
    }
)
```

---

#### Tarea 4.3 — Detección de sesión duplicada (B-18)

**Archivos a modificar:**
- `callcentersite/apps/authentication/services/authentication.py`
- `callcentersite/apps/authentication/viewsets.py`

**Flujo:**
1. En `login_user()`: verificar `SessionLog.objects.filter(user=user, is_active=True).exists()`
2. Si existe → retornar `AUTH-006` con flag `session_conflict: true`
3. Si request incluye `force: true` → invalidar sesión anterior y proceder
4. Si no → retornar conflicto al frontend para confirmación del usuario

---

### FASE 5 — CALIDAD TÉCNICA Y SCHEMA
**Objetivo:** Corregir warnings de drf_spectacular y mejorar documentación de API.
**Duración estimada:** 1–2 días
**Dependencias:** Ninguna (puede ejecutarse en paralelo)

#### Tarea 5.1 — Type hints en serializers (B-19)

**Archivos a modificar:** Todos los serializers con `SerializerMethodField` sin type hint.

**Patrón de corrección:**
```python
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

class MySerializer(serializers.ModelSerializer):
    subscriber_count = serializers.SerializerMethodField()

    @extend_schema_field(serializers.IntegerField())
    def get_subscriber_count(self, obj):
        return obj.subscribers.count()
```

**Archivos afectados:**
- `apps/alerts/serializers/alert_serializers.py`
- `apps/alerts/serializers/message_serializers.py`
- `apps/audit/serializers/auditlog_serializers.py`
- `apps/authentication/serializers/session.py`
- `apps/dashboard/serializers/dashboard_serializers.py`
- `apps/ivr/serializers/calllog_serializers.py`
- `apps/pipeline/serializers/callnote_serializers.py`
- `apps/pipeline/serializers/callrecord_serializers.py`
- `apps/pipeline/serializers/center_serializers.py`
- `apps/pipeline/serializers/service_serializers.py`
- `apps/reports/serializers/export_serializers.py`
- `apps/users/serializers/session_serializer.py`
- `apps/users/serializers/user_serializer.py`

#### Tarea 5.2 — Corregir viewsets sin serializer_class (B-19)

**Archivos a modificar:**
- `apps/authentication/viewsets.py` — `AuthViewSet` sin `serializer_class`
- `apps/users/viewsets/auth_viewset.py` — `AuthViewSet` sin `serializer_class`
- `apps/users/viewsets/profile_viewset.py` — `ProfileViewSet` sin `serializer_class`
- `apps/core/navigation/views.py` — `user_menu_view` sin serializer

**Solución:** Usar `@extend_schema` en los endpoints que no necesitan serializer de respuesta estándar.

---

## ORDEN DE EJECUCIÓN RECOMENDADO

```
FASE 0 — Estabilización (1–2 días)
  ├── [0.1] Corregir factories (bloquea todos los tests)
  └── [0.2] Corregir serializers pipeline

FASE 1 — Seguridad (3–5 días) — PARALELO CON FASE 2
  ├── [1.1] Throttling IP en login        ← bajo costo, alto impacto
  ├── [1.2] JWT access + refresh          ← alto costo, máximo impacto
  └── [1.3] Inactividad automática 90d    ← CNST-013

FASE 2 — Modelo datos (3–4 días) — PARALELO CON FASE 1
  ├── [2.1] is_locked en User             ← habilita B-06, B-09, B-16 parcial
  └── [2.2] UserActionLog centralizado

FASE 3 — RBAC completo (5–7 días) — después de Fase 0
  ├── [3.1] Endpoints assign/revoke funciones
  ├── [3.2] Validación SoD en código      ← depende de 3.1
  ├── [3.3] MOD_Reports funciones faltantes
  ├── [3.4] users.export + CNST-010 fix
  └── [3.5] DeletionLog

FASE 4 — Calidad API (2–3 días) — después de Fase 2
  ├── [4.1] Campos adicionales en login response
  ├── [4.2] locked_until timestamp
  └── [4.3] Detección sesión duplicada

FASE 5 — Schema técnico (1–2 días) — puede ejecutarse en cualquier momento
  ├── [5.1] Type hints en serializers
  └── [5.2] Viewsets sin serializer_class
```

---

## MÉTRICAS OBJETIVO AL COMPLETAR TODAS LAS FASES

| Métrica | Hoy | Objetivo |
|---|---|---|
| Cumplimiento funcional | 60% (15/25) | 100% (25/25) |
| Tests coleccionables | ❌ ImportError | ✅ Todos coleccionan |
| Validación SoD | 0% en código | 100% (3 reglas) |
| Seguridad tokens | DRF Token sin expiración | JWT 15min/7días |
| CNST-013 (90 días) | Constante sin automatización | Task diaria activa |
| CNST-010 (límite export) | 100K (incorrecto) | 10K (alineado) |
| DeletionLog | ❌ No existe | ✅ Implementado |
| Schema API (warnings) | 55 issues | < 10 issues |

---

## NOTAS TÉCNICAS

### Sobre el wrapper `data` en responses
Se recomienda **mantener el wrapper `data`** de la implementación actual (brecha B-05 del análisis Auth). Tiene ventajas arquitectónicas (consistencia, metadatos futuros, parsing uniforme) y cambiar el contrato rompería clientes existentes. La tarjeta `auth.login` debe actualizarse para reflejar esta decisión.

### Sobre `LoginLockout`
No eliminar la tabla `LoginLockout` hasta que `UserFunctionAssignment` con `is_locked` haya sido probado en producción. Mantenerla como historial o como tabla legacy.

### Sobre `LoginAttempt`
Mantener en paralelo con `UserActionLog` durante la migración. Crear management command de migración antes de deprecar.

### Stack de testing
Los tests del directorio `apps/` requieren PostgreSQL disponible. Para CI/CD usar `pytest --ignore=apps/` hasta que la DB esté disponible, o configurar un contenedor Docker PostgreSQL en el pipeline.

---

*Documento generado por Claude Code — IACT-api*
*Versión: 1.0.0 | Fecha: 2026-03-21 | Timestamp: 210326040159*
