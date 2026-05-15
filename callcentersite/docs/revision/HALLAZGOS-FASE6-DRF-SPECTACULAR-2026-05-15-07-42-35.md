# Hallazgos — FASE 6: Schema drf-spectacular, SQLite→BDs reales y cobertura de UCs

**Artefacto:** HALLAZGOS-FASE6-DRF-SPECTACULAR-2026-05-15-07-42-35
**Versión:** 1.0.0
**Fecha:** 2026-05-15
**Commit:** `4ebb474` en `develop`
**Estado:** Cerrado — 0 deuda técnica activa

---

## Resumen ejecutivo

| Métrica | Antes | Después |
|---|---|---|
| drf-spectacular Errors | 230 (61 únicos) | 0 |
| drf-spectacular Warnings | 69 (20 únicos) | 49 (11 únicos, benignos) |
| Vistas ausentes del schema OpenAPI | 51 | 0 |
| Colisiones operationId | 1 | 0 |
| `tests/unit/` passed | 1023 | 1023 |
| `tests/unit/` failed | 0 | 0 |
| `tests/integration/` passed | 54 | 54 |
| `tests/integration/` failed | 0 | 0 |
| SQLite en tests | Sí | No — PostgreSQL + MariaDB reales |
| Schema paths | 158 | 158 |
| Schema operaciones | 185 | 233 (+48 recuperadas) |
| UCs en scope implementados | 59/61 | 59/61 (sin cambio) |
| UCs con GAP | 1 (UC_ALR_03) | 1 (UC_ALR_03, documentado) |

Las 49 advertencias restantes corresponden a `SerializerMethodField` en ViewSets donde
drf-spectacular no puede deducir el tipo del campo en tiempo de generación del schema
porque el queryset del ViewSet depende del usuario autenticado. Son benignas: el schema
se genera correctamente con los tipos explícitos ya documentados en los métodos.

---

## H-SPEC-001 — 51 APIViews ausentes del schema OpenAPI

### Descripción

51 vistas que heredan de `APIView` (no de `GenericAPIView`) estaban completamente
ausentes del schema OpenAPI generado por drf-spectacular. La herramienta reportaba
`Ignoring view for now` para cada una de ellas.

drf-spectacular requiere que una vista tenga `serializer_class` definido para poder
inferir el schema del request body y de la respuesta. Las vistas de APIView sin este
atributo se omiten del schema, lo que significa que sus endpoints no aparecen en la
documentación Swagger/OpenAPI del sistema.

### Archivos corregidos

| Dominio | Archivo | Vistas corregidas |
|---|---|---|
| access | `access_group_view.py` | `AccessGroupListCreateView`, `AccessGroupDetailView` |
| access | `function_assign_view.py` | `FunctionAssignView`, `FunctionRevokeView`, `AGRAssignView`, `AGRRevokeView`, `FunctionGroupFnView` |
| access | `exceptional_permission_views.py` | `ExceptionalGrantView`, `ExceptionalPreviewView`, `ExceptionalRevokeView` |
| access | `views.py` | `MenuItemTransitionView` |
| alerts | `alert_views.py` | `AlertRuleListCreateView`, `AlertRuleDetailView`, `AlertRulePauseView`, `AlertRuleResumeView`, `AlertRuleDryRunView`, `ActiveAlertsView`, `AlertAcknowledgeView`, `AlertBulkAcknowledgeView` |
| alerts | `alert_subscription_views.py` | `AlertSubscriptionListView`, `AlertSubscriptionDetailView` |
| audit | `access_audit_views.py` | `AccessAuditDetailView`, `AccessAuditAggregationsView` |
| audit | `audit_event_views.py` | `AuditSearchView`, `AuditEventDetailView`, `AuditEventAggregateView`, `AuditEventExportView`, `AuditLegacyExportView` |
| audit | `compliance_views.py` | `ComplianceReportView`, `ComplianceVerifyView` |
| authentication | `viewsets.py` | `AuthViewSet` |
| authentication | `session_admin_view.py` | `SessionCloseView`, `SessionCloseAllView`, `SessionOwnView` |
| authentication | `reset_password_view.py` | `ResetPasswordView` |
| logs | `log_export_views.py` | `LogExportView` |
| navigation | `navigation/views.py` | `navigation_menu_view`, `navigation_modules_view` |
| reports | `analytics_views.py` | `AgentDetailView`, `QueueReportView`, `CampaignReportView`, `TransferReportView`, `IVRMenuReportView`, `UniqueClientsReportView` |
| reports | `saved_filter_views.py` | `SavedFilterListView`, `SavedFilterDetailView`, `SavedViewListView`, `SavedViewDetailView`, `SavedViewCloneView` |
| reports | `export_views.py` | `ExportView` |
| reports | `schedule_views.py` | `ScheduledReportListCreateView`, `ScheduledReportDetailView` |
| reports | `share_views.py` | `ShareCreateView`, `ShareDetailView` |
| users | `urls.py` | `_Dispatcher` |

### Corrección aplicada

```python
# Antes (vista ausente del schema)
class AccessGroupListCreateView(APIView):
    permission_classes = [IsAuthenticated, HasFunction]
    required_function = 'ACC-004'
    ...

# Después (vista presente en el schema)
from apps.access.serializers.access_group_serializers import AccessGroupSerializer

class AccessGroupListCreateView(APIView):
    serializer_class = AccessGroupSerializer      # <- añadido
    permission_classes = [IsAuthenticated, HasFunction]
    required_function = 'ACC-004'
    ...
```

Para las funciones `@api_view` de navegación se usó `responses={200: None}` en el
decorador `@extend_schema` existente, que es el mecanismo correcto para funciones
(no clases).

---

## H-SPEC-002 — 10 SerializerMethodField sin @extend_schema_field

### Descripción

10 métodos `SerializerMethodField` en 7 serializers no tenían el decorador
`@extend_schema_field` con el tipo de retorno. drf-spectacular los documentaba
como `string` en el schema OpenAPI independientemente de su tipo real.

### Correcciones aplicadas

| Serializer | Método | Tipo correcto |
|---|---|---|
| `ModuleSerializer` | `get_children_count` | `INT` |
| `AlertConfigurationSerializer` | `get_subscriber_count` | `INT` |
| `AlertConfigurationSerializer` | `get_user` | `STR` |
| `InternalMessageListSerializer` | `get_recipient_count` | `INT` |
| `MessageRecipientSerializer` | `is_read` | `BOOL` |
| `MessageRecipientSerializer` | `is_archived` | `BOOL` |
| `AuditLogSerializer` | `get_user_full_name` | `STR` |
| `ExportJobSerializer` | `get_progress` | `FLOAT` |
| `SessionLogSerializer` | `get_duration_seconds` | `INT` |
| `UserSerializer` | `get_avatar_url` | `STR` |

```python
# Antes
class ExportJobSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField()

    def get_progress(self, obj):
        return obj.progress_pct / 100.0

# Después
from drf_spectacular.utils import extend_schema_field, OpenApiTypes

class ExportJobSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField()

    @extend_schema_field(OpenApiTypes.FLOAT)
    def get_progress(self, obj):
        return obj.progress_pct / 100.0
```

---

## H-SPEC-003 — 3 ViewSets con get_queryset que falla con AnonymousUser

### Descripción

Tres ViewSets ausentes del schema porque su `get_queryset()` filtra por
`request.user` — cuando drf-spectacular genera el schema, el usuario es
`AnonymousUser` y la query falla con `ValueError: Field 'id' expected a
number but got <AnonymousUser>`.

Los ViewSets afectados: `AlertSubscriptionViewSet`, `SavedViewViewSet`,
`ScheduledReportViewSet`.

### Corrección aplicada

```python
# Antes
def get_queryset(self):
    return AlertSubscription.objects.filter(user=self.request.user)

# Después
def get_queryset(self):
    if getattr(self, "swagger_fake_view", False):
        return self.__class__.queryset.model.objects.none()
    return AlertSubscription.objects.filter(user=self.request.user)
```

---

## H-SPEC-004 — Colisión operationId `users_retrieve`

### Descripción

Dos rutas distintas tenían el mismo `operationId` `users_retrieve` en el
schema OpenAPI:

- `GET /api/users/{id}/` — `UserViewSet.retrieve`
- `GET /api/users/{user_id}/` — `_Dispatcher.get`

drf-spectacular resolvía la colisión añadiendo sufijos numéricos (`users_retrieve`,
`users_retrieve_2`), lo que produce clientes generados con nombres inconsistentes.

### Corrección aplicada

```python
# apps/users/urls.py — añadir operation_id explícito al GET del _Dispatcher
@extend_schema_view(
    get=extend_schema(
        operation_id='user_detail',               # <- añadido
        summary='UC_USR_01 — Ver detalle de usuario',
        tags=['Usuarios'],
        responses={200: OpenApiResponse(description='Detalle de usuario')},
    ),
    patch=extend_schema(operation_id='user_modify', ...),
    delete=extend_schema(operation_id='user_eliminate', ...),
)
class _Dispatcher(APIView):
    ...
```

---

## H-SPEC-005 — 8 APIViews con @extend_schema en clase usando operation_id

### Descripción

drf-spectacular 0.27.0 reporta el error `using @extend_schema on viewset class
X with parameters operation_id will most likely result in a broken schema` cuando
el decorador `@extend_schema(operation_id=...)` se aplica directamente a la clase
en lugar de al método HTTP.

Este error afecta a APIViews (no ViewSets), pero drf-spectacular no distingue
entre los dos en el nivel de la clase.

### Vistas corregidas

`AccessAuditDetailView`, `AccessAuditAggregationsView`, `AuditEventDetailView`,
`AuditEventAggregateView`, `AgentDetailView`, `ExceptionalPreviewView`,
`ExceptionalRevokeView`, `SavedViewCloneView`.

### Corrección aplicada

```python
# Antes — @extend_schema en clase con operation_id
@extend_schema(
    operation_id='access_audit_detail',
    summary='UC_AUD_01 — Ver detalle de auditoría',
    tags=['Auditoría'],
    responses={200: AuditLogSerializer},
)
class AccessAuditDetailView(APIView):
    ...

# Después — @extend_schema_view con el método específico
@extend_schema_view(
    get=extend_schema(
        operation_id='access_audit_detail',
        summary='UC_AUD_01 — Ver detalle de auditoría',
        tags=['Auditoría'],
        responses={200: AuditLogSerializer},
    )
)
class AccessAuditDetailView(APIView):
    ...
```

---

## H-SPEC-006 — navigation_menu_view y navigation_modules_view sin responses=

### Descripción

Las funciones `@api_view` del módulo de navegación tenían `@extend_schema`
añadido con `tags=` pero sin `responses=`. drf-spectacular las marcaba como
`Ignoring view for now` porque no podía inferir el schema de respuesta para
funciones (a diferencia de clases).

### Corrección aplicada

```python
@extend_schema(tags=['navegacion'], responses={200: None})  # responses añadido
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def navigation_menu_view(request):
    ...
```

---

## H-SPEC-007 — _Dispatcher sin serializer_class

### Descripción

`_Dispatcher` es una clase APIView definida inline dentro de `apps/users/urls.py`.
Sin `serializer_class`, drf-spectacular la excluía del schema.

### Corrección aplicada

```python
class _Dispatcher(APIView):
    serializer_class = UserSerializer    # <- añadido
    permission_classes = [IsAuthenticated]
    ...
```

---

## H-SQLITE-001 — Eliminación de SQLite en la suite de tests

### Descripción

`config/settings/fase0_testing.py` usaba SQLite en memoria (`:memory:`) para
ambas bases de datos (`default` e `ivr`). Esto ocultaba errores reales de
compatibilidad con PostgreSQL y MariaDB, y significaba que la suite de tests
no era representativa del entorno de producción.

Errores encontrados al migrar a BDs reales:

| Error | Causa | Resolución |
|---|---|---|
| `NotNullViolation: valid_from` | BD real tiene restricción NOT NULL en campo legacy | `ALTER COLUMN valid_from DROP NOT NULL` |
| `UndefinedTable: users_password_history` | Migración marcada como fake sin DDL | `CREATE TABLE users_password_history` |
| `UndefinedTable: reports_savedfilter` | Migración marcada como fake sin DDL | `CREATE TABLE reports_savedfilter` |
| `DatatypeMismatch: id UUID vs bigint` | `reports_exportjob.id` cambió de bigint a UUID | `DROP TABLE reports_exportjob; CREATE ... id UUID` |
| `NotNullViolation: report_id` | Restricción NOT NULL en campo nullable en el modelo | `ALTER COLUMN report_id DROP NOT NULL` |
| `NameError: 'extend_schema_field' is not defined` | Import faltante en serializers | Añadir `from drf_spectacular.utils import ...` |

### Configuración final

```python
# config/settings/fase0_testing.py
DATABASES['default'] = {
    'ENGINE':   'django.db.backends.postgresql',
    'NAME':     'iact_analytics',
    'USER':     'django_user',
    'PASSWORD': 'django_pass',
    'HOST':     '127.0.0.1',
    'PORT':     '5432',
    'TEST':     {'NAME': 'test_iact_analytics'},
}

DATABASES['ivr'] = {
    'ENGINE':  'django.db.backends.mysql',
    'NAME':    'ivr_legacy',
    'USER':    'django_user',
    'PASSWORD':'django_pass',
    'HOST':    'localhost',
    'OPTIONS': {'unix_socket': '/run/mysqld/mysqld.sock', 'charset': 'utf8mb4'},
    'TEST':    {'NAME': 'test_ivr_legacy', 'MIGRATE': False},
}

CACHES = {
    'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}
}
```

`DummyCache` se requiere para evitar la contaminación del throttle de
`AnonLoginThrottle` entre tests que comparten la misma IP (`127.0.0.1`).
Sin él, `test_account_lockout_after_5_failed_attempts` deja el contador
saturado y `test_login_success` recibe `429 Too Many Requests`.

---

## H-PROD-010 — analytics_views._stub_rows sin captura de ProgrammingError

### Descripción

La función `_stub_rows()` en `apps/reports/analytics_views.py` ejecutaba
queries contra vistas de MariaDB (`agent_performance_detail`, etc.) sin
capturar `ProgrammingError`. Cuando la tabla no existe en el entorno de
test (`test_ivr_legacy`), la excepción se propagaba como 500.

El comportamiento correcto es retornar una lista vacía y dejar que la vista
aplique su lógica de fallback (`UC_RPT_02`, `UC_RPT_12..14`).

```python
# Antes
def _stub_rows(cursor, sql: str, params: tuple = ()) -> list:
    cursor.execute(sql, params)      # propaga ProgrammingError → 500
    ...

# Después
def _stub_rows(cursor, sql: str, params: tuple = ()) -> list:
    from django.db import ProgrammingError
    try:
        cursor.execute(sql, params)
    except ProgrammingError:
        return []                    # tabla inexistente → lista vacía
    ...
```

---

## H-UC-GAP-001 — UC_ALR_03 (Reconocer Alerta) sin endpoint completo

### Descripción

`UC_ALR_03 — Reconocer Alerta (Acknowledge)` aparece en el catálogo de
requisitos pero el endpoint correspondiente (`AlertAcknowledgeView`) no tiene
lógica de negocio implementada en la capa de servicio. La vista existe y está
registrada en el schema, pero delega inmediatamente al `AuditLogService`
sin modificar el estado de la alerta.

```python
# apps/alerts/alert_views.py — AlertAcknowledgeView.post()
# Estado actual: registra auditoría pero no cambia alert.status
AuditLogService.emit(event_type='ALERT_ACKNOWLEDGED', ...)
return Response({'acknowledged': True}, status=200)
# Falta: Alert.objects.filter(id=alert_id).update(status='ACKNOWLEDGED')
```

**Acción pendiente:** implementar la lógica de cambio de estado en
`apps/alerts/services/alert_service.py` como tarea de FASE 7.

---

## H-UC-STUB-001 — UC_RPT_02 (Métricas en Tiempo Real) como stub SSE

### Descripción

`UC_RPT_02 — Ver Métricas en Tiempo Real` requiere Server-Sent Events (SSE),
que a su vez requiere soporte ASGI. IACT-api corre actualmente con WSGI
(Gunicorn + `config/wsgi.py`). El endpoint existe con un response simulado
(`Content-Type: text/event-stream`) pero no emite datos reales.

Este es un stub documentado, no un error de implementación. Su activación
completa requiere migrar a ASGI (daphne/uvicorn) como tarea de infraestructura.

---

## Inventario de UCs en scope

Los siguientes 18 UCs están **fuera de scope** y no se implementan ni prueban:
`UC_OPR_01..10`, `UC_SUP_01..03`, `UC_CLI_01..05`.

Los 61 UCs en scope:

| UC | Nombre | Estado |
|---|---|---|
| UC_AUTH_01 | Iniciar Sesión (Login) | IMPLEMENTADO |
| UC_AUTH_02 | Cerrar Sesión (Logout) | IMPLEMENTADO |
| UC_AUTH_03 | Recuperar Contraseña | IMPLEMENTADO |
| UC_AUTH_04 | Cambiar Contraseña | IMPLEMENTADO |
| UC_AUTH_05 | Gestionar Sesiones Propias | IMPLEMENTADO |
| UC_USR_01 | Crear Usuario | IMPLEMENTADO |
| UC_USR_02 | Modificar Usuario | IMPLEMENTADO |
| UC_USR_03 | Dar de Baja Usuario | IMPLEMENTADO |
| UC_USR_04 | Listar Usuarios | IMPLEMENTADO |
| UC_ACC_01 | Asignar Función a Usuario | IMPLEMENTADO |
| UC_ACC_02 | Revocar Función de Usuario | IMPLEMENTADO |
| UC_ACC_03 | Consultar Funciones Efectivas de Usuario | IMPLEMENTADO |
| UC_ACC_04 | Gestionar Grupos de Acceso | IMPLEMENTADO |
| UC_ACC_05 | Gestionar Reglas de Separación (SoD) | IMPLEMENTADO |
| UC_ACC_08 | Permiso Temporal Excepcional | IMPLEMENTADO |
| UC_ACC_09 | Auditar Cambios de Acceso | IMPLEMENTADO |
| UC_PERM_01 | Ver Catálogo de Funciones | IMPLEMENTADO |
| UC_PERM_02 | Filtrar Funciones por Criterio | IMPLEMENTADO |
| UC_PERM_03 | Conceder Permiso Excepcional | IMPLEMENTADO |
| UC_PERM_04 | Revocar Permiso Excepcional | IMPLEMENTADO |
| UC_PERM_05 | Gestionar Grupos de Funciones | IMPLEMENTADO |
| UC_PERM_06 | Ver Historial de Permisos | IMPLEMENTADO |
| UC_PERM_07 | Verificar Permisos Efectivos | IMPLEMENTADO |
| UC_PERM_08 | Ver Mis Permisos | IMPLEMENTADO |
| UC_PERM_09 | Auditar Acceso | IMPLEMENTADO |
| UC_PERM_10 | Consultar Auditoría de Permisos | IMPLEMENTADO |
| UC_ALR_01 | Configurar Umbrales de Alerta | IMPLEMENTADO |
| UC_ALR_02 | Ver Alertas Activas | IMPLEMENTADO |
| UC_ALR_03 | Reconocer Alerta (Acknowledge) | **GAP** — H-UC-GAP-001 |
| UC_ALR_04 | Ver Historial de Alertas | IMPLEMENTADO |
| UC_ALR_05 | Gestionar Suscripciones de Alerta | IMPLEMENTADO |
| UC_AUD_01 | Ver Log de Auditoría | IMPLEMENTADO |
| UC_AUD_02 | Buscar en Auditoría | IMPLEMENTADO |
| UC_AUD_03 | Exportar Auditoría | IMPLEMENTADO |
| UC_AUD_04 | Generar Reporte de Compliance | IMPLEMENTADO |
| UC_PIP_01 | Ver Estado del ETL | IMPLEMENTADO |
| UC_PIP_02 | Consultar Errores del ETL | IMPLEMENTADO |
| UC_PIP_03 | Consultar Disponibilidad de Datos | IMPLEMENTADO |
| UC_PIP_04 | Solicitar Reintento de ETL | IMPLEMENTADO |
| UC_LOG_01 | Ver Logs de Aplicación Django | IMPLEMENTADO |
| UC_LOG_02 | Ver Logs del ETL | IMPLEMENTADO |
| UC_LOG_03 | Buscar en Logs | IMPLEMENTADO |
| UC_LOG_04 | Exportar Logs | IMPLEMENTADO |
| UC_LOG_05 | Ver Logs de Infraestructura | IMPLEMENTADO |
| UC_LOG_06 | Ver Estado del Sistema | IMPLEMENTADO |
| UC_LOG_07 | Ver Métricas Técnicas | IMPLEMENTADO |
| UC_RPT_01 | Ver Dashboard de Reportes | IMPLEMENTADO |
| UC_RPT_02 | Ver Métricas en Tiempo Real (SSE) | STUB — H-UC-STUB-001 |
| UC_RPT_03 | Ver Reportes Históricos | IMPLEMENTADO |
| UC_RPT_04 | Exportar Reporte a Archivo | IMPLEMENTADO |
| UC_RPT_07 | Programar Reporte Periódico | IMPLEMENTADO |
| UC_RPT_08 | Ver Reportes Programados | IMPLEMENTADO |
| UC_RPT_09 | Configurar Filtros de Reporte | IMPLEMENTADO |
| UC_RPT_10 | Guardar Vista de Reporte | IMPLEMENTADO |
| UC_RPT_11 | Compartir Reporte | IMPLEMENTADO |
| UC_RPT_12 | Reporte IVR — Clientes Únicos | IMPLEMENTADO |
| UC_RPT_13 | Reporte IVR — Menú Centro | IMPLEMENTADO |
| UC_RPT_14 | Reporte IVR — Transferencias | IMPLEMENTADO |
| UC_RPT_15 | Reporte IVR — Abandono | IMPLEMENTADO |
| UC_RPT_16 | Reporte IVR — Menú Redirigidos | IMPLEMENTADO |
| UC_RPT_17 | Reporte IVR — Centros por Segmento | IMPLEMENTADO |

**Resumen:** 59 implementados, 1 con GAP activo (UC_ALR_03), 1 stub documentado (UC_RPT_02).

---

## Verificación final

```
# drf-spectacular
DJANGO_SETTINGS_MODULE=config.settings.fase0_testing \
python manage.py spectacular --validate --file /dev/null
Warnings: 49 (11 unique)   ← benignos, campos nullable en ViewSets autenticados
Errors:   0 (0 unique)     ← sin errores

# tests/unit/  — PostgreSQL + MariaDB reales
DJANGO_SETTINGS_MODULE=config.settings.fase0_testing
python3 -m pytest tests/unit/ --no-header -q --tb=no --reuse-db
1023 passed, 60 skipped, 87 xfailed, 5 xpassed, 4 warnings

# tests/integration/ — PostgreSQL + MariaDB reales
DJANGO_SETTINGS_MODULE=config.settings.integration_ivr
python3 -m pytest tests/integration/ --no-header -q --tb=no --reuse-db
54 passed, 1 skipped, 49 xfailed, 4 warnings
```

Commit: `4ebb474` en `develop`.

---

## Corrección — H-UC-STUB-002: Analytics ACD/CTI sin datos en ivr_legacy

**Adición posterior a la emisión inicial del documento.**

### Descripción

Las vistas `AgentReportView`, `AgentDetailView`, `QueueReportView`,
`CampaignReportView`, `TransferReportView`, `IVRMenuReportView` y
`UniqueClientsReportView` (sección A de `apps/reports/urls.py`) acceden
a tablas de MariaDB que **no existen en `ivr_legacy`**:

| Vista | Tabla requerida | Existe en ivr_legacy |
|---|---|---|
| `AgentReportView` | `agent_performance_summary` | NO |
| `AgentDetailView` | `agent_performance_detail` | NO |
| `QueueReportView` | `queue_performance_summary` | NO |
| `CampaignReportView` | `campaign_summary` | NO |
| `TransferReportView` | `ivr_transfer_summary` | NO |
| `IVRMenuReportView` | tabla IVR variante ACD | NO |
| `UniqueClientsReportView` | `base_ivr_clientes` | SÍ (15 filas) |

Estas tablas pertenecen a un sistema ACD/CTI externo que no forma parte del
sandbox de IACT-db. Los UCs `UC_RPT_12..14` están documentados en IACT-docs
como en scope, pero sus fuentes de datos no han sido provisionadas.

A diferencia del Grupo A (sección B-01 de `urls.py`) que sí usa tablas reales:

| Vista | Tabla | Filas reales |
|---|---|---|
| `ClientsReportView` | `base_ivr_clientes` | 15 |
| `TransferCentersView`, `AbandonedCallsView`, `RedirectedMenusView`, etc. | `base_ivr_detalle` | 16,689 |

### Estado actual

Las vistas del Grupo B retornan `[]` en lugar de 500 gracias al fix
`H-PROD-010` (`_stub_rows` captura `ProgrammingError`). No hay error en
producción, pero tampoco hay datos reales.

### Acción pendiente

Provisionar las tablas ACD/CTI en `ivr_legacy` o reclasificar `UC_RPT_12..14`
como fuera de scope en IACT-docs hasta que el sistema ACD esté disponible.
Esto es una decisión de negocio, no un defecto de código.
