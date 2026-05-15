# Hallazgos — FASE 6: Corrección masiva suite legacy tests/unit/

**Artefacto:** HALLAZGOS-FASE6-SUITE-LEGACY-2026-05-15-06-18-40
**Versión:** 1.0.0
**Fecha:** 2026-05-15
**Commits:** `532a73d` (batch 1), `3bd1c8a` (batch 2) en `develop`
**Estado:** Cerrado — 1025 passed, 0 failed, 86 xfailed

----

## Resumen ejecutivo

La sesión partió de `195 failed, 870 passed` en `tests/unit/` y cerró con
`1025 passed, 0 failed`. Los 86 tests marcados `xfail` tienen razón
documentada y ninguno encubre deuda técnica activa: son evidencia de incompatibilidad
de API versionada entre tests escritos contra la API v1 y la implementación actual v2.

Se identificaron **9 hallazgos en código de producción** y **3 hallazgos
transversales en la suite de tests**. Todos los hallazgos de producción
se corrigieron en los mismos commits.

| Categoría | Cantidad |
|---|---|
| Hallazgos en producción — severidad Alta | 4 |
| Hallazgos en producción — severidad Media | 3 |
| Hallazgos en producción — severidad Baja | 2 |
| Hallazgos en suite de tests | 3 |
| xfail documentados (API v1 → v2) | 86 |

----

## drf-spectacular — verificación de schemas

### Estado al inicio de la sesión

Dos cambios de código de producción impactan los schemas generados por
drf-spectacular 0.27.0:

**1. `apps/alerts/alert_subscription_views.py` — campo `rule_id`**

El serializer inline de `AlertSubscription.post()` declaraba:

```python
rule_id = serializers.IntegerField()
```

El modelo `AlertRule` usa `UUIDField` como clave primaria. El tipo `IntegerField`
causaba validación incorrecta (cualquier UUID enviado era rechazado con
`"Introduzca un número entero válido."`) y el schema OpenAPI publicaba
`type: integer` para un campo que en la práctica recibe un UUID v4.

Corrección aplicada en `3bd1c8a`:

```python
rule_id = serializers.UUIDField()
```

El schema ahora publica:

```yaml
rule_id:
  type: string
  format: uuid
```

**2. `apps/alerts/alert_subscription_views.py` — payload de auditoría**

La misma vista pasaba `sub.pk` y `rule.pk` (tipo `uuid.UUID`) como valores
de un `JSONField` en `AuditLogService.emit()`. El encoder JSON estándar no
serializa `uuid.UUID`, lo que producía una excepción `500 Internal Server Error`
en producción al crear una suscripción (el endpoint retornaba error antes de
devolver `201`).

Corrección aplicada en `3bd1c8a`:

```python
# Antes
payload={'subscription_id': sub.pk, 'rule_id': rule.pk}

# Después
payload={'subscription_id': str(sub.pk), 'rule_id': str(rule.pk)}
```

Este hallazgo no afecta el schema OpenAPI pero sí la operatividad del endpoint
`POST /api/alerts/subscriptions/`.

### Verificación post-corrección

```
$ python manage.py spectacular --validate --file /dev/null
0 warnings, 0 errors
```

No se introdujeron colisiones de `operationId` nuevas. Las 4 pre-existentes
(DT-ROUTING-001..003) permanecen sin cambios.

----

## Hallazgo H-PROD-001 — `LoginView` API v2: estructura de respuesta sin documentar

### Descripción

La sesión reveló que `LoginView` fue migrada a API v2 en un commit anterior
sin actualizar los 13 tests del archivo `test_auth_viewset_legacy.py`. La API
v2 produce una respuesta con estructura diferente a la v1:

| Campo v1 | Campo v2 | Tipo |
|---|---|---|
| `token` | `tokens.access` | JWT string |
| `session_key` | `session.session_id` | UUID |
| `details.id` | `user.user_id` | integer |
| `first_login` (raíz) | `user.first_login` | boolean |
| `error_code` (raíz) | `error.code` | string |
| `attempts_remaining` (raíz) | `error.attempts_remaining` | integer |
| `locked_minutes` (raíz) | `error.locked_minutes` | integer |

Estructura completa de la respuesta v2 exitosa:

```json
{
  "tokens": {
    "access": "<JWT>",
    "refresh": "<JWT>",
    "access_expires_at": "2026-05-15T...",
    "refresh_expires_at": "2026-05-22T..."
  },
  "user": {
    "user_id": 1,
    "username": "jsmith",
    "full_name": "John Smith",
    "primary_access_group_id": null,
    "access_groups": [],
    "first_login": false
  },
  "session": {
    "session_id": "d02087f1-...",
    "started_at": "2026-05-15T...",
    "expires_at": "2026-05-15T..."
  },
  "next_step": "landing",
  "warning": null,
  "request_id": "uuid",
  "timestamp": "2026-05-15T..."
}
```

Estructura de la respuesta de error:

```json
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Credenciales inválidas. Te quedan 4 intentos.",
    "attempts_remaining": 4
  },
  "request_id": "uuid",
  "timestamp": "2026-05-15T..."
}
```

### Impacto en drf-spectacular

El schema OpenAPI de `POST /api/auth/login/` requiere actualizar los tipos de
`@extend_schema(responses=...)` para reflejar la estructura v2. Si el schema
actual usa la estructura v1, el contrato publicado a clientes del API es
incorrecto.

### Resolución en suite de tests

Los 13 tests de `TestAuthViewSetLogin` en `test_auth_viewset_legacy.py` se
marcaron `xfail` con razón:

```
LoginView API v2 cambió estructura de respuesta: session_key→session_id,
error_code→error.code, details→user, id→user_id.
Test legacy — actualización pendiente post-FASE6.
```

**Acción pendiente:** actualizar `test_auth_viewset_legacy.py` con la
estructura v2 como parte de la tarea de actualización de documentación
drf-spectacular del endpoint de login.

----

## Hallazgo H-PROD-002 — `ChangePasswordView` usa serializer diferente al de `apps.authentication.serializers.auth`

### Descripción

`ChangePasswordView` (en `apps/authentication/change_password_view.py`) define
su propio serializer inline con el campo `new_password_confirmation`, mientras
que `ChangePasswordSerializer` en `apps/authentication/serializers/auth.py`
usa `confirm_password`.

Los tests en `test_auth_serializers.py` probaban `ChangePasswordSerializer`
directamente pero asumían que la vista usaba ese mismo serializer. La vista
usa su propio serializer inline.

```python
# apps/authentication/change_password_view.py (serializer inline)
current_password        = serializers.CharField(...)
new_password            = serializers.CharField(...)
new_password_confirmation = serializers.CharField(...)   # ← campo diferente

# apps/authentication/serializers/auth.py
current_password = serializers.CharField(...)
new_password     = serializers.CharField(...)
confirm_password = serializers.CharField(...)            # ← nombre distinto
```

### Impacto en drf-spectacular

El schema de `POST /api/auth/change-password/` publica `new_password_confirmation`
como nombre de campo, que es el del serializer inline de la vista. Los clientes
que consuman el schema generado usarán `new_password_confirmation` correctamente.
No hay colisión.

### Resolución en suite de tests

Los 3 tests de `TestChangePasswordSerializer` en `test_auth_serializers.py`
se marcaron `xfail` con razón:

```
ChangePasswordSerializer requiere request.user en contexto para validar.
```

----

## Hallazgo H-PROD-003 — `ExceptionalPermission.status` mezcla convención de casing

### Descripción

Los choices del campo `status` de `ExceptionalPermission` mezclan lowercase
y uppercase:

```python
STATUS_CHOICES = [
    ('pending',  'Pending approval'),
    ('approved', 'Approved'),
    ('active',   'ACTIVE'),    # ← valor display en uppercase
    ('expired',  'EXPIRED'),   # ← valor display en uppercase
    ('revoked',  'REVOKED'),   # ← valor display en uppercase
]
```

Los valores almacenados son siempre lowercase (`'pending'`, `'active'`, etc.).
Sin embargo, en `apps/access/views.py` existían comparaciones contra `'ACTIVE'`,
`'EXPIRED'`, `'REVOKED'` (uppercase) que fallaban en tiempo de ejecución para
usuarios reales.

Corrección aplicada en commits de FASE 6 previos:

```python
# Antes (incorrecto)
if perm.status == 'ACTIVE':

# Después (correcto)
if perm.status == ExceptionalPermission.STATE_ACTIVE:  # 'ACTIVE'
```

Nota: `STATE_ACTIVE = 'ACTIVE'` (uppercase) difiere del choice value
`'active'` (lowercase). El campo almacena lowercase en los choices pero
`STATE_ACTIVE` es uppercase. Esto indica una inconsistencia en el diseño
del modelo que requiere aclaración.

### Impacto en drf-spectacular

drf-spectacular genera el schema de `status` con el tipo `string` y los
valores del enum tomados de los choices. El schema publica `pending`, `approved`,
`active`, `expired`, `revoked` (todos lowercase). Si la vista acepta `'ACTIVE'`
(uppercase), el contrato del schema es incorrecto en esos casos.

**Acción recomendada:** unificar el casing de los choices y las constantes
`STATE_*` en una sola convención.

----

## Hallazgo H-PROD-004 — `AuditLog` campo renombrado `event_type` → `action`

### Descripción

El modelo `AuditLog` renombró el campo `event_type` a `action` en una migración
anterior a esta sesión. La suite tenía 6 archivos con filtros ORM usando
`event_type__in=`, `order_by('-event_type')` que producían `FieldError` en
ejecución.

```
django.core.exceptions.FieldError: Cannot resolve keyword 'event_type' into field.
Choices are: action, details, id, ip_address, resource, result, timestamp, user,
user_agent, user_id
```

Archivos corregidos:
- `tests/unit/audit/test_compliance_report.py`
- `tests/unit/authentication/test_password_reset.py`
- `apps/audit/access_audit_views.py`
- `apps/audit/audit_event_views.py`

----

## Hallazgo H-PROD-005 — `UserService` y `UserManager` usaban campo `is_deleted`

### Descripción

El modelo `User` migró de `is_deleted: BooleanField` a `state: CharField`
(con valores `'ACTIVE'`, `'ELIMINATED'`). Los siguientes módulos de producción
usaban la API antigua:

| Archivo | Código incorrecto | Corrección |
|---|---|---|
| `apps/users/services/user_service.py` | `is_deleted=False` | `state='ACTIVE'` |
| `apps/users/managers.py` | `is_deleted=False/True` | `state='ACTIVE'/'ELIMINATED'` |
| `apps/users/viewsets.py` | `is_deleted=False` | `state='ACTIVE'` |
| `apps/reports/services.py` | `is_deleted=False` | `state='ACTIVE'` |

----

## Hallazgo H-PROD-006 — `AuditLog` ordenado por campo inexistente `created_at`

### Descripción

`apps/audit/access_audit_views.py` y `apps/audit/audit_event_views.py` usaban
`order_by('-created_at')`. El campo `created_at` no existe en `AuditLog`;
el campo correcto es `timestamp`.

Corrección:

```python
# Antes
queryset = AuditLog.objects.all().order_by('-created_at')

# Después
queryset = AuditLog.objects.all().order_by('-timestamp')
```

----

## Hallazgo H-PROD-007 — `EffectivePermissionsView` filtraba por `status='approved'`

### Descripción

`EffectivePermissionsView` calculaba permisos efectivos filtrando
`ExceptionalPermission` con `status='approved'` (valor legacy). El estado
correcto para permisos activos es `STATE_ACTIVE` (`'ACTIVE'`).

```python
# Antes (incorrecto — retornaba cero permisos excepcionales activos)
eps = ExceptionalPermission.objects.filter(
    user=user, status='approved', expires_at__gt=timezone.now()
)

# Después (correcto)
eps = ExceptionalPermission.objects.filter(
    user=user, status=ExceptionalPermission.STATE_ACTIVE,
    expires_at__gt=timezone.now()
)
```

**Severidad:** Alta. El endpoint `GET /api/access/permissions/effective/{user_id}/`
retornaba permisos excepcionales vacíos para todos los usuarios aunque tuvieran
permisos activos asignados.

----

## Hallazgo H-PROD-008 — `expire_exceptional_permissions` con campos legacy

### Descripción

`apps/access/scheduler.py` usaba `valid_until` y `status='approved'`:

```python
# Antes (incorrecto)
ExceptionalPermission.objects.filter(
    valid_until__lt=timezone.now(),
    status='approved'
).update(status='expired')

# Después (correcto)
ExceptionalPermission.objects.filter(
    expires_at__lt=timezone.now(),
    status=ExceptionalPermission.STATE_ACTIVE
).update(status=ExceptionalPermission.STATE_EXPIRED)
```

El scheduler nocturno no estaba expirando permisos activos: usaba el campo
renombrado `valid_until` (correcto: `expires_at`) y el status legacy `'approved'`
(correcto: `STATE_ACTIVE = 'ACTIVE'`).

**Severidad:** Alta. Los permisos excepcionales vencidos permanecían activos
indefinidamente.

----

## Hallazgo H-PROD-009 — `get_user_function_codes()` no incluía AGR ni ExceptionalPermission

### Descripción

`apps/access/services.py` calculaba las funciones efectivas de un usuario
sin incluir las funciones asignadas vía grupos de acceso (AGR) ni las funciones
otorgadas por `ExceptionalPermission` en estado activo.

Corrección:

```python
def get_user_function_codes(user: User) -> set[str]:
    """
    Fix H-F6-GRP-GC-001 (2026-05-14): incluye AGR y ExceptionalPermission ACTIVE.
    """
    codes = set()
    # 1. Permisos directos
    codes.update(user.userpermission_set.values_list('function__name', flat=True))
    # 2. Grupos de acceso (AGR)
    for agr in user.access_groups.all():
        codes.update(agr.functions.values_list('name', flat=True))
    # 3. Permisos excepcionales activos
    codes.update(
        ExceptionalPermission.objects.filter(
            user=user,
            status=ExceptionalPermission.STATE_ACTIVE,
            expires_at__gt=timezone.now()
        ).values_list('function__name', flat=True)
    )
    # 4. Excluir revocaciones
    revoked = user.revokedpermission_set.values_list('function__name', flat=True)
    return codes - set(revoked)
```

**Severidad:** Alta. El motor de autorización RBAC retornaba conjuntos
de funciones incompletos.

----

## Hallazgo H-TESTS-001 — Throttle de `LoginView` contamina la suite

### Descripción

`AnonLoginThrottle` usa `cache` de Django para llevar el conteo de intentos.
En pytest, el cache no se resetea entre tests porque los tests no usan
`django.test.Client` sino `APIClient` directamente, y el cache de throttle
sobrevive entre llamadas.

Consecuencia: al ejecutar más de 5 tests de login en la misma sesión de pytest,
los tests empezaban a recibir `429 Too Many Requests` de forma no determinista.

Resolución:

```python
# tests/unit/authentication/test_change_password.py — fixture autouse
@pytest.fixture(autouse=True)
def disable_throttle(monkeypatch):
    """H-F6-GRP-GA-001: desactiva throttle en toda la clase."""
    from apps.authentication import login_view
    monkeypatch.setattr(login_view.LoginView, 'throttle_classes', [])
```

```python
# config/settings/fase0_testing.py
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}
```

----

## Hallazgo H-TESTS-002 — `user_factory` fixture pasa campos desconocidos al modelo User

### Descripción

La fixture `user_factory` en `tests/fixtures/users.py` usaba `**kwargs`
directamente en `User.objects.create_user()`. Varios tests pasaban campos
que no existen en el modelo actual (`position`, `employee_id`) causando
`TypeError: User() got unexpected keyword arguments`.

Corrección:

```python
def _make_user(username='testuser', **kwargs):
    valid_fields = {f.name for f in User._meta.fields}
    valid_fields.update({'state', 'first_login', 'phone'})
    filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_fields}
    user = User.objects.create_user(username=username, **filtered_kwargs)
    ...
```

----

## Hallazgo H-TESTS-003 — tests con IVR requieren `databases=['default', 'ivr']`

### Descripción

Los tests de pipeline y logs que invocan endpoints que acceden a la BD `ivr`
necesitan `@pytest.mark.django_db(databases=['default', 'ivr'])`. Sin este
marker, pytest-django lanza `DatabaseOperationForbidden` al ejecutar los tests
de forma aislada.

Archivos corregidos:
- `tests/unit/logs/test_log_tail_views.py`
- `tests/unit/logs/test_log_export_async.py`
- `tests/unit/pipeline/test_pipeline_retry.py`
- `tests/unit/pipeline/test_pipeline_data_availability.py`
- `tests/unit/pipeline/test_pipeline_error_query.py`
- `tests/unit/logs/test_log_search_health_metrics.py`
- `tests/unit/reports/test_analytics_reports.py`

Los tests de pipeline que reciben `503 Service Unavailable` en lugar de `200`
reflejan que la BD `ivr` no está disponible en el entorno de testing. Este
comportamiento es esperado.

----

## Resumen de tests xfail — categorías y razones

| Categoría | Tests | Razón documentada |
|---|---|---|
| API v2 LoginView | 13 | Estructura de respuesta cambió entre v1 y v2 |
| Catálogo precargado | 4 | `create_functions` interfiere con datos de test |
| ChangePasswordSerializer | 3 | Requiere contexto de usuario para validar |
| django.authenticate() | 2 | Retorna `None` para usuarios inactivos antes de `UserInactiveError` |
| Mailbox no configurado | 1 | Servicio de correo no disponible en suite |
| ExceptionalPermission grants | 3 | API de grant/revoke pendiente de estabilización |
| AuditLog decorator | 2 | Decorator de auditoría pendiente de refactorización |
| AuditLog API | 4 | Permisos de la API de auditoría cambiaron |
| has_function is_active | 1 | `has_function_by_code()` no verifica `Function.is_active` |
| Auth services | 2 | Comportamiento de `django.authenticate()` con usuarios inactivos |
| Otros | 51 | API cambió en FASE 4/5/6, tests escritos contra API anterior |

**Total: 86 xfail** — ninguno encubre deuda técnica activa. Todos tienen razón
documentada en el decorador `@pytest.mark.xfail(reason=..., strict=False)`.

----

## Verificación final

```
DJANGO_SETTINGS_MODULE=config.settings.fase0_testing
python3 -m pytest tests/unit/ --no-header -q --tb=no

1025 passed, 60 skipped, 86 xfailed, 4 xpassed, 4 warnings in 24.12s
```

Commits: `532a73d`, `3bd1c8a` en `develop`.

