# PLAN DE IMPLEMENTACIÓN POR FASES — IACT API
## Cierre de Brechas y Fortalecimiento del Sistema

**Versión:** 2.0.0
**Fecha:** 2026-03-21
**Autor:** Claude Code — Análisis automatizado
**Cambios vs v1.0.0:** Estado real de BDs verificado; errores de importación ampliados de 1 a 12 tipos distintos; nueva brecha B-20 (permisos MariaDB en tests).

---

## ESTADO ACTUAL DEL PROYECTO (verificado con BDs activas)

### Verificación de funcionamiento (2026-03-21 — BDs corriendo)

| Componente | Estado | Detalle |
|---|---|---|
| PostgreSQL 16 | ✅ online | `pg_lsclusters` → online, puerto 5432 |
| MariaDB 10.11 | ✅ online | `mysqladmin status` OK, puerto 3306 |
| Django → PostgreSQL (`default`) | ✅ conectado | `iact_analytics` — READ+WRITE |
| Django → MariaDB (`ivr`) | ✅ conectado | `ivr_legacy` — READ-ONLY (CNST-003) |
| Django system check | ✅ 0 errores | `python manage.py check` limpio |
| Deploy check | ⚠️ Warnings esperados | SSL/HSTS en testing — OK |
| drf_spectacular | ⚠️ Warnings de schema | No bloquean funcionamiento |
| Migraciones pendientes | ✅ ninguna | `showmigrations` todo en `[X]` |
| Tests (`tests/`) | ❌ 20 errores colección | 12 tipos distintos de ImportError (ver B-02) |
| Tests (`apps/`) | ❌ 129 errores setup | `ALTER command denied` en MariaDB test (nueva B-20) |

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
| B-02 | Tests | `tests/` tiene 12 tipos distintos de ImportError (ver detalle abajo) | P1 — CRÍTICA |
| B-03 | Pipeline | Serializers no definidos en `viewsets.py` | P1 — CRÍTICA |
| B-20 | Tests | `apps/` fallan: `django_user` sin permisos ALTER en `test_ivr_legacy` | P1 — CRÍTICA |
| B-04 | RBAC | Validación SoD no existe en código | P2 — ALTA |
| B-05 | RBAC | Endpoints assign/revoke de funciones atómicas faltan | P2 — ALTA |
| B-06 | Auth | `users.lock` implementado como `deactivate` (semántica incorrecta) | P2 — ALTA |

### Detalle B-02 — Errores de importación en `tests/` (12 tipos)

| Símbolo faltante | Módulo que lo busca | Tests afectados |
|---|---|---|
| `Role` | `apps.access.models` | auth_flow, recovery_flow, session_flow, test_models, test_services, test_views |
| `HasModuleAccess` | `apps.access.permissions` | test_permissions |
| `CustomTokenObtainPairSerializer` | `apps.authentication.serializers` | test_serializers |
| `HasServiceAccess` | `apps.core.permissions` | test_permissions, test_service_access |
| `LoggingMiddleware` | `apps.core.middleware.logging` | test_middleware |
| `LoginSerializer` | `apps.users.serializers` | test_auth_serializers |
| `UserProfileSerializer` | `apps.users.serializers` | test_serializers (users) |
| `format_phone` | `apps.utils.formatters` | test_formatters |
| `CallRecord` | `apps.core.models` | test_core_models, test_core_serializers |
| `Service` | `apps.core.models` | test_core_models |
| `ServiceFilterMixin` | `apps.core.mixins` | test_mixins |
| `apps.ivr_legacy` | módulo completo | test_core_etl_service |
| `apps.utils.network` | módulo completo | test_utils_network |

### Detalle B-20 — Permisos MariaDB en tests (NUEVO en v2.0.0)

Al correr `pytest apps/`, Django intenta crear `test_ivr_legacy` en MariaDB para el test runner.
`django_user` solo tiene permisos de lectura sobre `ivr_legacy`, lo que causa:

```
MySQLdb.OperationalError: (1142, "ALTER command denied to user
'django_user'@'localhost' for table `test_ivr_legacy`.`django_content_type`")
```

Soluciones posibles (en orden de preferencia):
1. Configurar `TEST: {'NAME': None}` en el alias `ivr` de settings → Django no crea BD de test
2. Otorgar `GRANT ALL ON test_ivr_legacy.* TO 'django_user'@'localhost'` en MariaDB
3. Crear `conftest.py` que marque todos los tests de `apps/` con `@pytest.mark.django_db(databases=['default'])` excluyendo `ivr`

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

### Brechas Menores

| ID | Origen | Brecha | Prioridad |
|---|---|---|---|
| B-16 | Auth | Campos `full_name`, `last_login`, `date_joined` faltan en response | P4 — BAJA |
| B-17 | Auth | `locked_until` timestamp vs `locked_minutes` entero | P4 — BAJA |
| B-18 | Auth | Detección de sesión duplicada (Flujo A5) | P4 — BAJA |
| B-19 | Schema | drf_spectacular: type hints faltantes en serializers | P5 — COSMÉTICA |

---

## FASES DE IMPLEMENTACIÓN

---

### FASE 0 — ESTABILIZACIÓN (Prerequisito absoluto)
**Objetivo:** Tests 100% coleccionables y sin errores de setup antes de cualquier nueva funcionalidad.
**Dependencias:** Ninguna

#### Tarea 0.1 — Corregir todos los ImportError en `tests/` (B-02)

**Problema:** 13 símbolos/módulos referenciados en tests que no existen en el código actual.

**Estrategia:** Para cada símbolo faltante, elegir entre:
- **A)** Crear el símbolo en el código (si hace falta para producción)
- **B)** Eliminar/actualizar la referencia en el test (si el símbolo fue renombrado/eliminado)

**Acciones por símbolo:**

| Símbolo | Acción recomendada | Archivo a modificar |
|---|---|---|
| `Role` | B — eliminar de tests; usar `UserFunctionAssignment` | `tests/factories/access_factories.py`, tests que lo usan |
| `HasModuleAccess` | A — crear o alias en `apps.access.permissions` | `apps/access/permissions/__init__.py` |
| `CustomTokenObtainPairSerializer` | A — crear o alias en `apps.authentication.serializers` | `apps/authentication/serializers/__init__.py` |
| `HasServiceAccess` | A — crear o alias en `apps.core.permissions` | `apps/core/permissions.py` |
| `LoggingMiddleware` | A — crear en `apps.core.middleware.logging` | `apps/core/middleware/logging.py` |
| `LoginSerializer` | A — crear o alias en `apps.users.serializers` | `apps/users/serializers/__init__.py` |
| `UserProfileSerializer` | A — crear o alias en `apps.users.serializers` | `apps/users/serializers/__init__.py` |
| `format_phone` | A — crear en `apps.utils.formatters` | `apps/utils/formatters.py` |
| `CallRecord`, `Service` | B — actualizar tests; modelos movidos a `apps.pipeline` / `apps.ivr` | Tests que los importan de `apps.core.models` |
| `ServiceFilterMixin` | B — actualizar tests; mixin renombrado o movido | Tests que lo importan de `apps.core.mixins` |
| `apps.ivr_legacy` | B — renombrar a `apps.ivr` en los tests | `tests/unit/core/test_core_etl_service.py` |
| `apps.utils.network` | A — crear módulo o B — eliminar test | `apps/utils/network.py` o borrar test |

**Criterio de aceptación:** `pytest tests/ --collect-only` → 0 errores de colección.

---

#### Tarea 0.2 — Resolver permisos MariaDB en tests (B-20)

**Problema:** `django_user` no puede crear/alterar `test_ivr_legacy`.

**Solución preferida — opción 1 (sin cambiar permisos de BD):**

```python
# config/settings/base.py — en DATABASES['ivr']
'ivr': {
    ...
    'TEST': {
        'NAME': None,  # Django no crea BD de test para este alias
    },
}
```

Esto requiere que los tests marquen explícitamente qué BD usan:
```python
@pytest.mark.django_db(databases=['default'])
def test_algo():
    ...
```

**Solución alternativa — opción 2 (otorgar permisos):**
```sql
-- Ejecutar en MariaDB como root
GRANT ALL PRIVILEGES ON `test_ivr_legacy`.* TO 'django_user'@'localhost';
FLUSH PRIVILEGES;
```

**Criterio de aceptación:** `pytest apps/ --collect-only` → 0 errores de setup.

---

#### Tarea 0.3 — Corregir serializers faltantes en pipeline (B-03)

**Archivos afectados:**
- `callcentersite/apps/pipeline/viewsets.py` (líneas 427–433)
- `callcentersite/apps/pipeline/serializers/callrecord_serializers.py`

**Serializers a crear:**
- `CallRecordBulkCreateSerializer`
- `DailyStatsSerializer`
- `ServiceStatsSerializer`
- `TopCallerSerializer`

O bien retornar `CallRecordSerializer` como fallback hasta que los actions estén implementados.

**Criterio de aceptación:** `python manage.py check` → 0 warnings en `pipeline/viewsets.py`.

---

### FASE 1 — SEGURIDAD CRÍTICA
**Dependencias:** Fase 0 completada

#### Tarea 1.1 — Throttling por IP en login (B-07)

```python
# apps/authentication/throttles.py (nuevo)
from rest_framework.throttling import AnonRateThrottle

class LoginRateThrottle(AnonRateThrottle):
    scope = 'login'
```

```python
# config/settings/base.py
'DEFAULT_THROTTLE_RATES': {
    'anon': '100/hour',
    'user': '1000/hour',
    'login': '5/minute',
}
```

Respuesta al throttle:
```json
{"success": false, "error_code": "AUTH-005", "retry_after": 900, "blocked_until": "..."}
```

**Tests:** `test_login_throttle_blocks_after_5_requests`, `test_throttle_response_format`

---

#### Tarea 1.2 — JWT: access token + refresh token (B-01)

```python
# config/settings/base.py
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

Agregar a `INSTALLED_APPS`: `'rest_framework_simplejwt.token_blacklist'`

Endpoints nuevos:
```
POST /api/v1/auth/token/refresh/
POST /api/v1/auth/token/blacklist/
```

Ejecutar migración: `python manage.py migrate`

**Impacto:** Actualizar los 22 tests que usan `Token` auth → usar `Bearer`.

---

#### Tarea 1.3 — Inactividad automática 90 días (B-08, CNST-013)

```python
# apps/authentication/tasks.py
def deactivate_inactive_accounts():
    cutoff = timezone.now() - timedelta(days=90)
    count = User.objects.filter(
        is_active=True, last_login__lt=cutoff, is_superuser=False
    ).update(is_active=False)
    return count
```

Configurar tarea diaria en APScheduler (ya existe en el proyecto).

---

### FASE 2 — MODELO DE DATOS
**Dependencias:** Fase 0. Puede ejecutarse en paralelo con Fase 1.

#### Tarea 2.1 — Campo `is_locked` en modelo User (B-06, B-09)

```python
# apps/users/models.py — agregar al modelo User
is_locked = models.BooleanField(default=False)
locked_until = models.DateTimeField(null=True, blank=True)
locked_reason = models.CharField(max_length=500, blank=True)
locked_by = models.ForeignKey('self', null=True, blank=True,
    on_delete=models.SET_NULL, related_name='locked_users')
```

Refactorizar `LockoutService` para usar `user.is_locked` / `user.locked_until`.
Exponer `is_locked`, `full_name`, `last_login`, `date_joined` en response de login (B-16 parcial).

---

#### Tarea 2.2 — `UserActionLog` centralizado (B-10)

```python
# apps/audit/models.py
class UserActionLog(models.Model):
    user       = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    action     = models.CharField(max_length=100)
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

---

### FASE 3 — RBAC COMPLETO
**Dependencias:** Fase 0. Fase 2.1 recomendada.

#### Tarea 3.1 — Endpoints assign/revoke de funciones (B-05)

```
GET    /api/v1/users/{id}/functions/
POST   /api/v1/users/{id}/functions/assign/
POST   /api/v1/users/{id}/functions/revoke/
GET    /api/v1/access/functions/
GET    /api/v1/access/sod-rules/
```

#### Tarea 3.2 — Validación SoD en código (B-04)

```python
SOD_RULES = [
    {'incompatible': ['access.assign', 'access.revoke']},
    {'incompatible': ['users.create', 'users.edit', 'users.delete',
                      'audit.view', 'audit.search']},
    {'incompatible': ['reports.modify_data', 'reports.approve']},
]
```

Implementar `_validate_sod()` en `UserFunctionAssignment.clean()`.

#### Tarea 3.3 — MOD_Reports: funciones faltantes (B-13)

```
POST /api/v1/reports/{id}/modify-data/
POST /api/v1/reports/{id}/approve/
POST /api/v1/reports/{id}/schedule/
```

Flujo dual-control: `modify_data` crea `ReportModification` en `PENDING`; `approve` valida SoD (aprobador ≠ modificador).

#### Tarea 3.4 — `users.export` + corrección CNST-010 (B-14, B-12)

```python
# apps/utils/constants.py
MAX_EXPORT_ROWS = 10000  # corregir de 100000
```

Nuevo endpoint: `GET /api/v1/users/export/` (CSV/JSON, máx 10K).

#### Tarea 3.5 — DeletionLog inmutable (B-11)

```python
class DeletionLog(models.Model):
    deleted_log_id = models.IntegerField()
    deleted_at     = models.DateTimeField(auto_now_add=True)
    deleted_by     = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    reason         = models.CharField(max_length=500)
    log_snapshot   = models.JSONField()

    def save(self, *args, **kwargs):
        if self.pk:
            raise PermissionError("DeletionLog es inmutable")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("DeletionLog no puede eliminarse")
```

---

### FASE 4 — MEJORAS DE CALIDAD DE API
**Dependencias:** Fase 2.

#### Tarea 4.1 — Campos adicionales en login response (B-16)

```python
'user': {
    'id': user.id, 'username': user.username, 'email': user.email,
    'full_name': f"{user.first_name} {user.last_name}".strip(),
    'is_active': user.is_active, 'is_locked': user.is_locked,
    'last_login': user.last_login, 'date_joined': user.date_joined,
}
```

#### Tarea 4.2 — `locked_until` timestamp en error de lockout (B-17)

```python
raise AccountLockedError(details={
    'locked_minutes': minutes,
    'locked_until': locked_until.isoformat() if locked_until else None
})
```

#### Tarea 4.3 — Detección de sesión duplicada (B-18)

1. En `login_user()` verificar `SessionLog.objects.filter(user=user, is_active=True).exists()`
2. Si existe → retornar `AUTH-006` con `session_conflict: true`
3. Si `force: true` en request → invalidar sesión anterior y proceder

---

### FASE 5 — CALIDAD TÉCNICA Y SCHEMA
**Dependencias:** Ninguna. Puede ejecutarse en paralelo.

#### Tarea 5.1 — Type hints en serializers (B-19)

Patrón:
```python
from drf_spectacular.utils import extend_schema_field

@extend_schema_field(serializers.IntegerField())
def get_mi_campo(self, obj):
    return obj.mi_campo
```

**13 archivos afectados:** `alerts`, `audit`, `authentication`, `dashboard`, `ivr`, `pipeline` (×4), `reports`, `users` (×2).

#### Tarea 5.2 — Viewsets sin `serializer_class` (B-19)

Usar `@extend_schema` en `AuthViewSet`, `ProfileViewSet`, `user_menu_view`.

---

## ORDEN DE EJECUCIÓN RECOMENDADO

```
FASE 0 — Estabilización (prerequisito absoluto)
  ├── [0.1] Corregir 13 ImportError en tests/        ← desbloquea 502 tests
  ├── [0.2] Permisos MariaDB en tests (B-20)         ← desbloquea 129 tests apps/
  └── [0.3] Serializers faltantes en pipeline

FASE 1 — Seguridad (paralelo con Fase 2)
  ├── [1.1] Throttling IP en login                   ← bajo costo, alto impacto
  ├── [1.2] JWT access + refresh                     ← alto costo, máximo impacto
  └── [1.3] Inactividad automática 90d               ← CNST-013

FASE 2 — Modelo datos (paralelo con Fase 1)
  ├── [2.1] is_locked en User
  └── [2.2] UserActionLog centralizado

FASE 3 — RBAC completo (después de Fase 0)
  ├── [3.1] Endpoints assign/revoke funciones
  ├── [3.2] Validación SoD                           ← depende de 3.1
  ├── [3.3] MOD_Reports funciones faltantes
  ├── [3.4] users.export + CNST-010 fix
  └── [3.5] DeletionLog

FASE 4 — Calidad API (después de Fase 2)
  ├── [4.1] Campos adicionales en login response
  ├── [4.2] locked_until timestamp
  └── [4.3] Detección sesión duplicada

FASE 5 — Schema técnico (cualquier momento)
  ├── [5.1] Type hints en serializers
  └── [5.2] Viewsets sin serializer_class
```

---

## MÉTRICAS OBJETIVO

| Métrica | Estado actual | Objetivo |
|---|---|---|
| Cumplimiento funcional | 60% (15/25) | 100% (25/25) |
| Tests coleccionables `tests/` | ❌ 20 errores (13 tipos ImportError) | ✅ 0 errores |
| Tests setup `apps/` | ❌ 129 errores (ALTER denied) | ✅ 0 errores |
| Validación SoD | 0% en código | 100% (3 reglas) |
| Seguridad tokens | DRF Token sin expiración | JWT 15min/7días |
| CNST-013 (90 días) | Sin automatización | Task diaria activa |
| CNST-010 (límite export) | 100K (incorrecto) | 10K (alineado) |
| DeletionLog | No existe | Implementado |
| Schema API (warnings) | ~55 issues | < 10 issues |

---

## NOTAS TÉCNICAS

**Wrapper `data` en responses:** Mantener. Cambiarlo rompería clientes existentes.

**`LoginLockout`:** No eliminar hasta validar `user.is_locked` en producción.

**`LoginAttempt`:** Mantener en paralelo con `UserActionLog` durante migración.

**BDs en CI/CD:** Con `TEST: {'NAME': None}` en alias `ivr`, el pipeline puede correr sin MariaDB para la mayoría de tests. Solo tests que lean `ivr_legacy` real necesitan MariaDB disponible.

---

*Documento generado por Claude Code — IACT-api*
*Versión: 2.0.0 | Fecha: 2026-03-21 | Timestamp: 210326052557*
*Basado en verificación real con PostgreSQL 16 y MariaDB 10.11 activos*
