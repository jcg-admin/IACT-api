# Plan de implementacion v2.0.0 — IACT API

**Version:** 2.0.0
**Fecha:** 2026-05-07
**Fuente:** DEPENDENCY_GRAPH_v1_0_0.md + analisis exhaustivo del codebase
**Stack:** Django 4.x + DRF + drf_spectacular + PostgreSQL + MariaDB (ivr)
**Supersede:** IMPLEMENTATION_PLAN_v1_0_0.md

---

## Constraints vigentes (no negociables)

| ID | Restriccion |
|---|---|
| CNST-003 | Dual database: PostgreSQL (default) + MariaDB ivr_legacy (READ-ONLY) |
| CNST-004 | Sin WebSockets, sin Celery. Usar APScheduler para tareas programadas |
| CNST-010 | Sin cache de ningun tipo (Redis, Memcached, LocMemCache prohibidos) |

Impacto directo en el plan:
- E-002 del plan v1 (cache IVR) queda eliminado — viola CNST-010
- SSE (UC_RPT_02) queda como stub — viola CNST-004
- La expiracion de ExceptionalPermission usa APScheduler, no Celery

---

## Resumen de fases

| Fase | Nombre | Tareas | Prioridad | Estado |
|---|---|---|---|---|
| A | Nomenclatura y convenciones | 5 | CRITICA | COMPLETA |
| B | Migraciones Django | 3 | CRITICA | PENDIENTE |
| C | Serializers para modelos nuevos | 4 | CRITICA | PENDIENTE |
| D | Schema OpenAPI (drf_spectacular) | 6 | ALTA | PENDIENTE |
| E | Permisos en endpoints nuevos | 3 | ALTA | PENDIENTE |
| F | Completar get_functions() en User | 2 | ALTA | PENDIENTE |
| G | Permisos granulares RBAC | 4 | ALTA | PENDIENTE |
| H | APScheduler — tareas programadas | 3 | ALTA | PENDIENTE |
| I | Hardening pipeline IVR | 3 | ALTA | PENDIENTE |
| J | Admin Django — modelos nuevos | 2 | MEDIA | PENDIENTE |
| K | Reports pendientes (UC_RPT_07..11) | 5 | MEDIA | PENDIENTE |
| L | Deuda tecnica existente | 3 | MEDIA | PENDIENTE |
| M | Factories para modelos nuevos | 4 | ALTA | PENDIENTE |
| N | Tests unitarios — modelos nuevos | 8 | ALTA | PENDIENTE |
| O | Tests integracion — endpoints IVR | 5 | ALTA | PENDIENTE |

**Total:** 60 tareas atomicas

---

## FASE A — Nomenclatura y convenciones (COMPLETA)

| Tarea | Descripcion | Estado |
|---|---|---|
| A-001 | SodRule → SeparationRule en models.py | HECHO |
| A-002 | SodRuleViewSet → SeparationRuleViewSet en views.py | HECHO |
| A-003 | Endpoint sod-rules → separation-rules en urls.py | HECHO |
| A-004 | Crear RESTRICCIONES_ARQUITECTONICAS_IACT_v1_0_0.md | HECHO |
| A-005 | Eliminar concepto de role del codigo de produccion | HECHO |

---

## FASE B — Migraciones Django

**Prerequisito:** Fase A completa.
**Objetivo:** Crear y aplicar migraciones para los 4 modelos nuevos de access
(AccessGroup, UserAccessGroup, SeparationRule, ExceptionalPermission).

### B-001 — Generar migracion

```bash
python manage.py makemigrations access \
    --name "add_access_group_separation_rule_exceptional_permission"
```

**Criterio:** Archivo `0003_*.py` generado. Contiene las 4 tablas:
`access_group`, `access_user_group`, `access_separation_rule`,
`access_exceptional_permission`. Sin aparicion de `sod_rule`.

### B-002 — Verificar SQL en dry-run

```bash
python manage.py sqlmigrate access 0003
```

**Criterio:** SQL correcto sin errores. Los nombres de tabla usan
`separation_rule`, no `sod_rule`.

### B-003 — Aplicar migracion

```bash
python manage.py migrate access
python manage.py showmigrations access
```

**Criterio:** [X] en la migracion 0003. Las 4 tablas existen en PostgreSQL.

---

## FASE C — Serializers para modelos nuevos

**Prerequisito:** Fase B completa.
**Objetivo:** Los modelos nuevos tienen serializers propios en
`apps/access/serializers/` en lugar de clases inline en views.py.
Esto sigue el patron establecido del proyecto (ver `access/serializers/`).

### C-001 — Serializer para AccessGroup

**Archivo:** `apps/access/serializers/access_group_serializers.py`

```python
from rest_framework import serializers
from apps.access.models import AccessGroup, UserAccessGroup


class AccessGroupSerializer(serializers.ModelSerializer):
    function_count = serializers.SerializerMethodField()

    class Meta:
        model = AccessGroup
        fields = ['id', 'name', 'code', 'description',
                  'functions', 'function_count', 'deleted_at']
        read_only_fields = ['deleted_at']

    def get_function_count(self, obj):
        return obj.functions.count()


class AccessGroupListSerializer(serializers.ModelSerializer):
    """Lightweight para listados."""
    class Meta:
        model = AccessGroup
        fields = ['id', 'name', 'code', 'function_count']

    function_count = serializers.SerializerMethodField()

    def get_function_count(self, obj):
        return obj.functions.count()


class UserAccessGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAccessGroup
        fields = ['id', 'user', 'access_group', 'granted_at', 'granted_by']
        read_only_fields = ['granted_at']
```

**Criterio:** `from apps.access.serializers import AccessGroupSerializer`
funciona. Las views usan el serializer del modulo, no una clase inline.

### C-002 — Serializer para SeparationRule

**Archivo:** `apps/access/serializers/separation_rule_serializers.py`

```python
class SeparationRuleSerializer(serializers.ModelSerializer):
    function_a_code = serializers.CharField(
        source='function_a.code', read_only=True)
    function_b_code = serializers.CharField(
        source='function_b.code', read_only=True)

    class Meta:
        model = SeparationRule
        fields = ['id', 'name', 'function_a', 'function_a_code',
                  'function_b', 'function_b_code',
                  'justificacion', 'estado', 'creado_por']
        read_only_fields = ['creado_por']
```

**Criterio:** El endpoint `GET /api/access/separation-rules/` retorna
`function_a_code` y `function_b_code` como campos legibles ademas de los IDs.

### C-003 — Serializer para ExceptionalPermission

**Archivo:** `apps/access/serializers/exceptional_permission_serializers.py`

```python
class ExceptionalPermissionSerializer(serializers.ModelSerializer):
    function_code = serializers.CharField(
        source='function.code', read_only=True)
    es_activo = serializers.SerializerMethodField()

    class Meta:
        model = ExceptionalPermission
        fields = ['id', 'user', 'function', 'function_code',
                  'justificacion', 'estado', 'valido_desde',
                  'valido_hasta', 'otorgado_por', 'creado_en', 'es_activo']
        read_only_fields = ['estado', 'otorgado_por', 'creado_en']

    def get_es_activo(self, obj):
        from django.utils import timezone
        now = timezone.now()
        return (obj.estado == 'aprobado'
                and obj.valido_desde <= now <= obj.valido_hasta)

    def validate_justificacion(self, value):
        if len(value) < 50:
            raise serializers.ValidationError(
                'La justificacion debe tener al menos 50 caracteres.')
        return value

    def validate(self, data):
        if data.get('valido_hasta') and data.get('valido_desde'):
            if data['valido_hasta'] <= data['valido_desde']:
                raise serializers.ValidationError(
                    'valido_hasta debe ser posterior a valido_desde.')
        return data
```

**Criterio:** La creacion de ExceptionalPermission con justificacion < 50
chars retorna 400. Con fechas invertidas tambien retorna 400.

### C-004 — Actualizar views.py para usar serializers del modulo

**Archivo:** `apps/access/views.py`

Reemplazar las clases inline en `get_serializer_class()` por imports
de los serializers creados en C-001..C-003.

```python
from apps.access.serializers.access_group_serializers import (
    AccessGroupSerializer, UserAccessGroupSerializer)
from apps.access.serializers.separation_rule_serializers import (
    SeparationRuleSerializer)
from apps.access.serializers.exceptional_permission_serializers import (
    ExceptionalPermissionSerializer)
```

**Criterio:** Ningun ViewSet de access tiene clases serializer definidas
inline en `get_serializer_class()`.

---

## FASE D — Schema OpenAPI (drf_spectacular)

**Prerequisito:** Fase C completa.
**Objetivo:** Cada app sigue el patron establecido:
`schema.py` con `SPECTACULAR_TAGS` + `@extend_schema` en cada endpoint.

**Patron del proyecto:**
El hook `collect_app_tags` en `spectacular_hooks.py` lee automaticamente
`SPECTACULAR_TAGS` de cada `apps/{app}/schema.py`. Los endpoints se decoran
con `@extend_schema` en views.py, nunca en schema.py.

### D-001 — Crear schema.py para app logs

**Archivo:** `apps/logs/schema.py`

```python
SPECTACULAR_TAGS = [
    {
        'name': 'Logs',
        'description': 'Acceso a logs del sistema Django y del pipeline ETL IVR.',
    },
]
```

**Criterio:** `GET /api/schema/` incluye el tag "Logs".

### D-002 — Poblar SPECTACULAR_TAGS en apps existentes

Las siguientes apps tienen `schema.py` pero sin `SPECTACULAR_TAGS` definidos:
`access`, `alerts`, `audit`, `pipeline`, `reports`.

```python
# apps/access/schema.py
SPECTACULAR_TAGS = [
    {
        'name': 'RBAC',
        'description': 'Control de acceso basado en funciones: '
                       'AccessGroup, SeparationRule, ExceptionalPermission.',
    },
]

# apps/pipeline/schema.py
SPECTACULAR_TAGS = [
    {
        'name': 'Pipeline ETL',
        'description': 'Estado, errores, disponibilidad de datos y reintento '
                       'del pipeline ETL que lee de MariaDB ivr_legacy.',
    },
]

# apps/reports/schema.py
SPECTACULAR_TAGS = [
    {
        'name': 'Reportes IVR',
        'description': 'Reportes generados desde los SPs de MariaDB ivr_legacy.',
    },
    {
        'name': 'Reportes',
        'description': 'Gestion de reportes y exportaciones.',
    },
]
```

**Criterio:** `GET /api/schema/` muestra tags para cada app con descripcion.

### D-003 — Decorar endpoints de pipeline con @extend_schema

**Archivo:** `apps/pipeline/views.py`

```python
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

@extend_schema(
    summary="UC_PIP_01 — Estado del ETL IVR",
    description="Resumen de salud del pipeline. Lee job_execution_log en MariaDB.",
    responses={
        200: OpenApiResponse(description="ok | degradado | critico"),
        503: OpenApiResponse(description="MariaDB no disponible"),
    },
    tags=["Pipeline ETL"]
)
@api_view(['GET'])
def etl_status(request): ...

@extend_schema(
    summary="UC_PIP_02 — Errores del pipeline",
    parameters=[
        OpenApiParameter('trimestre', str, description="Ej: Q01_25"),
        OpenApiParameter('page', int, default=1),
        OpenApiParameter('page_size', int, default=20),
    ],
    tags=["Pipeline ETL"]
)
@api_view(['GET'])
def etl_errors(request): ...

@extend_schema(
    summary="UC_PIP_03 — Disponibilidad de datos",
    parameters=[OpenApiParameter('trimestre', str, required=True)],
    responses={200: OpenApiResponse(description="fresco | aceptable | vencido | sin_datos")},
    tags=["Pipeline ETL"]
)
@api_view(['GET'])
def etl_data_availability(request): ...

@extend_schema(
    summary="UC_PIP_04 — Solicitar reintento del pipeline",
    tags=["Pipeline ETL"],
    responses={202: OpenApiResponse(description="Reintento iniciado"),
               409: OpenApiResponse(description="Ejecucion activa en curso")}
)
@api_view(['POST'])
def etl_retry(request): ...
```

**Criterio:** Los 4 endpoints de pipeline aparecen en `GET /api/schema/`
bajo el tag "Pipeline ETL".

### D-004 — Decorar endpoints IVR de reports con @extend_schema

**Archivo:** `apps/reports/ivr_views.py`

```python
from drf_spectacular.utils import extend_schema, OpenApiParameter

IVR_QUARTER_PARAM = OpenApiParameter(
    'quarter', str,
    description="Quarter a consultar. Ej: Q01_25",
    required=True
)
IVR_SEGMENTO_PARAM = OpenApiParameter(
    'segmento', str,
    enum=['todas', 'nacional_A', 'nacional_B', 'puebla'],
    default='todas'
)
```

**Criterio:** Los 6 endpoints `/api/reports/ivr/*` aparecen en el schema
con sus parametros declarados.

### D-005 — Decorar endpoints de access con @extend_schema_view

**Archivo:** `apps/access/views.py`

```python
from drf_spectacular.utils import extend_schema_view, extend_schema

@extend_schema_view(
    list=extend_schema(
        summary="UC_PERM_05 — Listar grupos de acceso",
        tags=["RBAC"]),
    create=extend_schema(
        summary="UC_PERM_05 — Crear grupo de acceso",
        tags=["RBAC"]),
    ...
)
class AccessGroupViewSet(viewsets.ModelViewSet): ...
```

**Criterio:** AccessGroupViewSet, SeparationRuleViewSet,
ExceptionalPermissionViewSet y EffectivePermissionsView aparecen
en el schema con sus acciones documentadas.

### D-006 — Decorar endpoints de logs con @extend_schema

**Archivo:** `apps/logs/views.py`

**Criterio:** Los 7 endpoints `/api/logs/*` aparecen en el schema
con summary y tags.

---

## FASE E — Permisos en endpoints nuevos

**Prerequisito:** Fase D completa.
**Objetivo:** Los endpoints nuevos de pipeline, reports/ivr y logs usan
`RequiresFunctionPermission` ademas de `IsAuthenticated`, siguiendo el
patron RBAC del proyecto.

### E-001 — Agregar RequiresFunctionPermission a endpoints de pipeline

**Archivo:** `apps/pipeline/views.py`

```python
from apps.core.permissions import RequiresFunctionPermission

@extend_schema(...)
@api_view(['GET'])
@permission_classes([IsAuthenticated, RequiresFunctionPermission])
def etl_status(request):
    request.required_function = 'pipeline.view_status'
    ...

@api_view(['POST'])
@permission_classes([IsAuthenticated, RequiresFunctionPermission])
def etl_retry(request):
    request.required_function = 'pipeline.retry'
    ...
```

**Criterio:** Un usuario sin la funcion `pipeline.view_status` asignada
recibe 403 en `GET /api/pipeline/status/`.

### E-002 — Agregar RequiresFunctionPermission a endpoints IVR

**Archivo:** `apps/reports/ivr_views.py`

```python
class ClientesReportView(APIView):
    permission_classes = [IsAuthenticated, RequiresFunctionPermission]
    required_function = 'reports.view_ivr'
```

**Criterio:** Un usuario sin `reports.view_ivr` recibe 403 en todos
los endpoints `/api/reports/ivr/*`.

### E-003 — Agregar RequiresFunctionPermission a endpoints de logs

**Archivo:** `apps/logs/views.py`

```python
class DjangoLogTailView(APIView):
    permission_classes = [IsAuthenticated, RequiresFunctionPermission]
    required_function = 'logs.view'
```

**Criterio:** Un usuario sin `logs.view` recibe 403 en todos
los endpoints `/api/logs/*`.

---

## FASE F — Completar get_functions() en User

**Prerequisito:** Fase B completa (tablas existen).
**Objetivo:** `User.get_functions()` retorna la union real de funciones:
directas + via AccessGroup + ExceptionalPermission activos.
Actualmente solo retorna funciones directas.

### F-001 — Actualizar get_functions() para incluir AccessGroup

**Archivo:** `apps/users/models.py`

```python
def get_functions(self):
    """
    Retorna los codigos de funciones efectivos del usuario.

    Union de tres fuentes:
    1. UserPermission directos (funcion asignada individualmente)
    2. Funciones de los AccessGroup del usuario
    3. ExceptionalPermission aprobados y vigentes

    No aplica SeparationRule — las reglas se verifican al asignar,
    no al consultar. Un permiso ya asignado permanece valido.
    """
    from django.utils import timezone
    functions = set()

    # 1. Directos
    functions.update(
        UserPermission.objects.filter(user=self)
        .values_list('function__code', flat=True)
    )

    # 2. Via AccessGroup
    functions.update(
        Function.objects.filter(
            access_groups__memberships__user=self
        ).values_list('code', flat=True)
    )

    # 3. Excepcionales activos
    now = timezone.now()
    functions.update(
        ExceptionalPermission.objects.filter(
            user=self,
            estado='aprobado',
            valido_desde__lte=now,
            valido_hasta__gte=now,
        ).values_list('function__code', flat=True)
    )

    return sorted(functions)
```

**Criterio:**
- Un usuario con AccessGroup que contiene `reports.view` → `get_functions()`
  incluye `reports.view`.
- Un ExceptionalPermission expirado no aparece en el resultado.

### F-002 — Actualizar get_user_function_codes() en access/services.py

**Archivo:** `apps/access/services.py`

La funcion `get_user_function_codes(user)` debe delegar a
`user.get_functions()` en lugar de tener logica propia.

```python
def get_user_function_codes(user) -> list[str]:
    """
    Retorna los codigos de funciones efectivos del usuario.
    Delega a User.get_functions() como fuente de verdad.
    """
    return user.get_functions()
```

**Criterio:** `get_user_function_codes(user)` y `user.get_functions()`
retornan exactamente el mismo resultado.

---

## FASE G — Permisos granulares RBAC

**Prerequisito:** Fase F completa.
**Objetivo:** UC_ACC_01/02 — asignar y revocar funciones individuales
a un usuario, verificando SeparationRule antes de asignar.

### G-001 — Crear UserFunctionAssignView

**Archivo:** `apps/access/views.py`

```python
@extend_schema(
    summary="UC_ACC_01 — Asignar funcion a usuario",
    tags=["RBAC"]
)
class UserFunctionAssignView(APIView):
    """
    POST /api/access/users/{user_id}/functions/
    Body: { "function_id": 42 }

    Verifica SeparationRule antes de asignar.
    Emite evento de auditoria.
    """
    permission_classes = [IsAuthenticated, RequiresFunctionPermission]
    required_function = 'access.assign_functions'

    def post(self, request, user_id):
        # 1. Obtener usuario y funcion
        # 2. Verificar que no existe UserPermission duplicado
        # 3. Verificar conflictos SeparationRule contra funciones actuales
        # 4. Crear UserPermission
        # 5. Emitir AuditLog
```

**Criterio:**
- 201 al asignar correctamente.
- 409 si la funcion ya esta asignada.
- 409 si existe SeparationRule activa con alguna funcion existente del usuario.
- AuditLog registra el evento con `action='ACCESS_FUNCTION_ASSIGNED'`.

### G-002 — Crear UserFunctionRevokeView

**Archivo:** `apps/access/views.py`

```python
@extend_schema(
    summary="UC_ACC_02 — Revocar funcion de usuario",
    tags=["RBAC"]
)
class UserFunctionRevokeView(APIView):
    """
    DELETE /api/access/users/{user_id}/functions/{function_id}/
    """
    permission_classes = [IsAuthenticated, RequiresFunctionPermission]
    required_function = 'access.assign_functions'
```

**Criterio:**
- 204 al revocar correctamente.
- 404 si el UserPermission no existe.
- AuditLog registra `action='ACCESS_FUNCTION_REVOKED'`.

### G-003 — Registrar URLs en access/urls.py

```python
path('users/<int:user_id>/functions/',
     UserFunctionAssignView.as_view(), name='assign-function'),
path('users/<int:user_id>/functions/<int:function_id>/',
     UserFunctionRevokeView.as_view(), name='revoke-function'),
```

**Criterio:** Las URLs se resuelven sin ImportError.

### G-004 — Verificar SeparationRule al asignar AccessGroup

**Archivo:** `apps/access/views.py :: UserAccessGroupViewSet.perform_create`

Al asignar un AccessGroup, cada funcion del grupo se verifica contra
las funciones actuales del usuario.

**Criterio:** Asignar AccessGroup cuyas funciones generan conflicto
retorna 400 con detalle del conflicto detectado.

---

## FASE H — APScheduler — tareas programadas

**Prerequisito:** Fases B y F completas.
**Objetivo:** Las tareas periodicas usan APScheduler (CNST-004: sin Celery).

### H-001 — Tarea de expiracion de ExceptionalPermission

**Archivo:** `apps/access/scheduler.py` (nuevo)

```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django.utils import timezone
from apps.access.models import ExceptionalPermission


def expire_exceptional_permissions():
    """
    Marca como 'expirado' los ExceptionalPermission cuya fecha
    valido_hasta ya paso y siguen en estado 'aprobado'.
    Se ejecuta cada hora via APScheduler.
    """
    now = timezone.now()
    actualizados = ExceptionalPermission.objects.filter(
        estado='aprobado',
        valido_hasta__lt=now
    ).update(estado='expirado')
    return actualizados


class AccessScheduler:
    scheduler = None

    @classmethod
    def start(cls):
        if cls.scheduler:
            return
        cls.scheduler = BackgroundScheduler()
        cls.scheduler.add_job(
            expire_exceptional_permissions,
            trigger=IntervalTrigger(hours=1),
            id='expire_exceptional_permissions',
            replace_existing=True,
        )
        cls.scheduler.start()

    @classmethod
    def stop(cls):
        if cls.scheduler:
            cls.scheduler.shutdown()
            cls.scheduler = None
```

**Criterio:** Un ExceptionalPermission con `valido_hasta` en el pasado
cambia a `estado='expirado'` al ejecutar `expire_exceptional_permissions()`.

### H-002 — Arrancar scheduler en apps/access/apps.py

```python
class AccessConfig(AppConfig):
    name = 'apps.access'

    def ready(self):
        from apps.access.scheduler import AccessScheduler
        AccessScheduler.start()
```

**Criterio:** El scheduler arranca junto con Django.
`AccessScheduler.scheduler` no es None tras el arrange.

### H-003 — Verificar que pipeline/scheduler.py usa el mismo patron

**Archivo:** `apps/pipeline/scheduler.py`

El scheduler de pipeline ya existe. Verificar que `BackgroundScheduler`
se inicia en `apps/pipeline/apps.py :: PipelineConfig.ready()`.

**Criterio:** `python manage.py check` no reporta advertencias de
scheduler duplicado o no iniciado.

---

## FASE I — Hardening pipeline IVR

**Prerequisito:** Fases D y E completas.
**CNST-010:** Cache eliminado del plan v1 (E-002 eliminado).

### I-001 — Timeout configurable en conexion MariaDB

**Archivo:** `apps/pipeline/views.py` y `apps/reports/ivr_services.py`

```python
IVR_QUERY_TIMEOUT_MS = getattr(settings, 'IVR_QUERY_TIMEOUT_SEC', 30) * 1000

with connections['ivr'].cursor() as cursor:
    cursor.execute(f"SET SESSION MAX_EXECUTION_TIME={IVR_QUERY_TIMEOUT_MS}")
    cursor.execute(sql, params)
```

**Criterio:** `IVR_QUERY_TIMEOUT_SEC = 5` en settings provoca timeout
en queries que excedan 5 segundos.

### I-002 — Quarters disponibles desde MariaDB, no constante hardcodeada

**Archivo:** `apps/reports/ivr_services.py`

```python
def get_available_quarters() -> set[str]:
    """
    Consulta los quarters disponibles en base_ivr_detalle.
    Sin cache (CNST-010). Llamada ligera: SELECT DISTINCT sobre columna indexada.
    """
    with connections['ivr'].cursor() as cursor:
        cursor.execute(
            "SELECT DISTINCT trimestre FROM base_ivr_detalle ORDER BY trimestre"
        )
        return {row[0] for row in cursor.fetchall()}
```

**Criterio:** Un quarter inexistente en base_ivr_detalle retorna 404.
La constante `QUARTERS_VALIDOS` queda eliminada de ivr_services.py.

### I-003 — Endpoint health de la conexion IVR

**Archivo:** `apps/pipeline/views.py`

```python
@extend_schema(
    summary="Estado de la conexion MariaDB IVR",
    tags=["Pipeline ETL"]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ivr_health(request):
    """GET /api/pipeline/ivr-health/"""
    try:
        with connections['ivr'].cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
        return Response({'status': 'ok', 'version': version})
    except OperationalError as e:
        return Response({'status': 'error', 'detail': str(e)}, status=503)
```

**Criterio:** 200 con MariaDB activo. 503 cuando no disponible.

---

## FASE J — Admin Django — modelos nuevos

**Prerequisito:** Fase B completa.

### J-001 — Registrar AccessGroup, SeparationRule en admin.py

**Archivo:** `apps/access/admin.py`

```python
from django.contrib import admin
from apps.access.models import (
    AccessGroup, UserAccessGroup,
    SeparationRule, ExceptionalPermission
)


@admin.register(AccessGroup)
class AccessGroupAdmin(admin.ModelAdmin):
    list_display  = ['code', 'name', 'function_count']
    search_fields = ['code', 'name']
    filter_horizontal = ['functions']

    def function_count(self, obj):
        return obj.functions.count()


@admin.register(SeparationRule)
class SeparationRuleAdmin(admin.ModelAdmin):
    list_display  = ['name', 'function_a', 'function_b', 'estado']
    list_filter   = ['estado']
    search_fields = ['name']


@admin.register(ExceptionalPermission)
class ExceptionalPermissionAdmin(admin.ModelAdmin):
    list_display  = ['user', 'function', 'estado', 'valido_desde', 'valido_hasta']
    list_filter   = ['estado']
    search_fields = ['user__email', 'function__code']
```

**Criterio:** Los 3 modelos aparecen en `/admin/` sin errores.

### J-002 — Registrar UserAccessGroup en admin.py

**Criterio:** `UserAccessGroup` aparece en `/admin/` con filtro por
`access_group` y busqueda por `user__email`.

---

## FASE K — Reports pendientes (UC_RPT_07..11)

**Prerequisito:** Fases D y B completas.

### K-001 — Modelo ScheduledReport (UC_RPT_07)

**Archivo:** `apps/reports/models.py`

```python
class ScheduledReport(SoftDeleteMixin, models.Model):
    """Reporte programado para ejecutarse periodicamente."""
    report      = models.ForeignKey(Report, on_delete=models.CASCADE)
    cron_expr   = models.CharField(max_length=50, help_text="Expresion cron")
    es_activo   = models.BooleanField(default=True)
    ultima_ejec = models.DateTimeField(null=True, blank=True)
    proxima_ejec= models.DateTimeField(null=True, blank=True)
    creado_por  = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
```

**Criterio:** `makemigrations reports` genera la migracion para ScheduledReport.

### K-002 — Endpoint programar reporte (UC_RPT_07)

**Criterio:** `POST /api/reports/scheduled/` crea un ScheduledReport.

### K-003 — Endpoint listar reportes programados (UC_RPT_08)

**Criterio:** `GET /api/reports/scheduled/` lista los ScheduledReport
del usuario autenticado.

### K-004 — Modelo SavedView (UC_RPT_10)

```python
class SavedView(models.Model):
    """Vista guardada de un reporte (filtros + columnas)."""
    name       = models.CharField(max_length=100)
    report     = models.ForeignKey(Report, on_delete=models.CASCADE)
    filtros    = models.JSONField(default=dict)
    columnas   = models.JSONField(default=list)
    creado_por = models.ForeignKey('users.User', on_delete=models.CASCADE)
```

**Criterio:** CRUD `/api/reports/saved-views/` funciona.

### K-005 — UC_RPT_02 stub documentado (SSE)

**CNST-004:** Sin WebSockets. El endpoint retorna snapshot con nota.

```python
@extend_schema(
    summary="UC_RPT_02 — Metricas en tiempo real (CNST-004: stub)",
    description="CNST-004 prohibe WebSockets. Retorna snapshot estatico. "
                "SSE disponible al migrar a ASGI.",
    tags=["Reportes"]
)
class MetricasRealtimeView(APIView): ...
```

**Criterio:** El endpoint existe, retorna 200 con snapshot y nota.
El schema documenta la limitacion de CNST-004.

---

## FASE L — Deuda tecnica existente

**Objetivo:** Cerrar los items pendientes de `documents/deuda-tecnica.md`.

### L-001 — DT-001: wsgi.py apunta a settings.development

**Archivo:** `config/wsgi.py`

```python
os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'config.settings.production'   # cambiado de development
)
```

**Criterio:** El archivo wsgi.py usa `production` como default.
El deployment puede overridear via variable de entorno.

### L-002 — DT-002: Fixture IVR para tests de integracion

**Archivo:** `tests/conftest.py`

```python
@pytest.fixture(scope='session')
def django_db_setup(django_test_environment, django_db_blocker):
    """Crea schema de prueba en ivr_legacy."""
    with django_db_blocker.unblock():
        with connections['ivr'].cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_temp_prueba_ivr (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    trimestre VARCHAR(10),
                    total_llamadas INT DEFAULT 0
                )
            """)
```

**Criterio:** Los tests marcados con
`@pytest.mark.django_db(databases=['default', 'ivr'])` pueden leer
y escribir en la DB de test IVR sin mocks.

### L-003 — Actualizar deuda-tecnica.md

Marcar DT-001 y DT-002 como resueltos en `documents/deuda-tecnica.md`
con fecha y descripcion de la correccion.

---

## FASE M — Factories para modelos nuevos

**Prerequisito:** Fase B completa.
**Objetivo:** Cada modelo nuevo tiene su factory en
`tests/factories/access_factories.py`.

### M-001 — AccessGroupFactory

```python
class AccessGroupFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: f'Grupo {n}')
    code = factory.Sequence(lambda n: f'GRP_{n:04d}')
    description = factory.Faker('sentence')

    class Meta:
        model = AccessGroup
```

### M-002 — SeparationRuleFactory

```python
class SeparationRuleFactory(DjangoModelFactory):
    name         = factory.Faker('sentence', nb_words=4)
    function_a   = factory.SubFactory(FunctionFactory)
    function_b   = factory.SubFactory(FunctionFactory)
    justificacion = factory.Faker('paragraph')
    estado       = 'activa'

    class Meta:
        model = SeparationRule
```

### M-003 — ExceptionalPermissionFactory

```python
class ExceptionalPermissionFactory(DjangoModelFactory):
    user         = factory.SubFactory(UserFactory)
    function     = factory.SubFactory(FunctionFactory)
    justificacion = factory.Faker('paragraph', nb_sentences=5)
    estado       = 'pendiente'
    valido_desde = factory.LazyFunction(timezone.now)
    valido_hasta = factory.LazyFunction(
        lambda: timezone.now() + timedelta(days=7))

    class Meta:
        model = ExceptionalPermission
```

### M-004 — UserAccessGroupFactory

```python
class UserAccessGroupFactory(DjangoModelFactory):
    user         = factory.SubFactory(UserFactory)
    access_group = factory.SubFactory(AccessGroupFactory)

    class Meta:
        model = UserAccessGroup
```

**Criterio (M-001..M-004):** `from tests.factories.access_factories import
AccessGroupFactory` funciona. Las factories crean instancias validas
en tests con `@pytest.mark.django_db`.

---

## FASE N — Tests unitarios — modelos nuevos

**Prerequisito:** Fases B, C y M completas.

### N-001 — Tests de modelo SeparationRule

**Archivo:** `tests/unit/access/test_separation_rule.py`

```python
def test_separation_rule_unique_pair(db, separation_rule_factory):
    fn_a, fn_b = FunctionFactory(), FunctionFactory()
    SeparationRuleFactory(function_a=fn_a, function_b=fn_b)
    with pytest.raises(IntegrityError):
        SeparationRuleFactory(function_a=fn_a, function_b=fn_b)

def test_separation_rule_pair_order_independiente(db):
    """La regla (A, B) y (B, A) son la misma restriccion."""
    fn_a, fn_b = FunctionFactory(), FunctionFactory()
    regla = SeparationRuleFactory(function_a=fn_a, function_b=fn_b)
    conflicto = SeparationRule.objects.filter(
        Q(function_a=fn_b, function_b=fn_a) |
        Q(function_a=fn_a, function_b=fn_b)
    ).first()
    assert conflicto == regla
```

### N-002 — Tests de serializer ExceptionalPermission

**Criterio:** Justificacion < 50 chars → error. Fechas invertidas → error.
Fechas validas → objeto creado.

### N-003 — Tests de AccessGroupViewSet

**Criterio:** CRUD completo. `add-function` agrega funcion al grupo.
`remove-function` la quita.

### N-004 — Tests de SeparationRuleViewSet

**Criterio:** `GET /check/?function_a=X&function_b=Y` retorna
`tiene_conflicto: true` cuando existe regla activa.

### N-005 — Tests de ExceptionalPermissionViewSet flujo completo

**Criterio:**
- POST crea con estado `pendiente`.
- PATCH `/approve/` cambia a `aprobado`.
- PATCH `/revoke/` cambia a `revocado`.
- No se puede aprobar algo ya revocado.

### N-006 — Tests de EffectivePermissionsView

**Criterio:** El endpoint retorna la union de las tres fuentes.
Un ExceptionalPermission expirado no aparece en el resultado.

### N-007 — Tests de expire_exceptional_permissions()

**Criterio:** Permisos con `valido_hasta` en el pasado quedan en
`estado='expirado'`. Permisos vigentes no se tocan.

### N-008 — Tests de get_functions() con las tres fuentes

**Criterio:** `user.get_functions()` incluye funciones de UserPermission,
de AccessGroup y de ExceptionalPermission activos, y excluye los expirados.

---

## FASE O — Tests de integracion — endpoints IVR

**Prerequisito:** Fase L-002 (fixture IVR real).

### O-001 — Tests de etl_status con MariaDB real

```python
@pytest.mark.django_db(databases=['default', 'ivr'])
def test_etl_status_retorna_resumen(authenticated_client):
    response = authenticated_client.get('/api/pipeline/status/')
    assert response.status_code == 200
    assert response.data['resumen']['estado_general'] in ('ok','degradado','critico')
    assert 'ultimas_ejecuciones' in response.data
```

### O-002 — Tests de etl_retry validaciones

```python
def test_etl_retry_motivo_muy_corto(authenticated_client):
    r = authenticated_client.post('/api/pipeline/retry/',
        {'trimestre': 'Q01_25', 'motivo': 'corto'})
    assert r.status_code == 400

def test_etl_retry_trimestre_invalido(authenticated_client):
    r = authenticated_client.post('/api/pipeline/retry/',
        {'trimestre': 'XXXX', 'motivo': 'x' * 20})
    assert r.status_code == 400
```

### O-003 — Tests de IVR reports quarter invalido

```python
def test_ivr_clients_quarter_invalido(authenticated_client):
    r = authenticated_client.get('/api/reports/ivr/clients/?quarter=XXXX')
    assert r.status_code == 404

@pytest.mark.django_db(databases=['default', 'ivr'])
def test_ivr_clients_quarter_valido(authenticated_client):
    r = authenticated_client.get('/api/reports/ivr/clients/?quarter=Q01_25')
    assert r.status_code == 200
    assert r.data['total_filas'] == 3
```

### O-004 — Tests de ivr_health

```python
@pytest.mark.django_db(databases=['default', 'ivr'])
def test_ivr_health_ok(authenticated_client):
    r = authenticated_client.get('/api/pipeline/ivr-health/')
    assert r.status_code == 200
    assert r.data['status'] == 'ok'
```

### O-005 — Tests de logs/etl/tail con MariaDB real

```python
@pytest.mark.django_db(databases=['default', 'ivr'])
def test_etl_log_tail_retorna_entries(authenticated_client):
    r = authenticated_client.get('/api/logs/etl/tail/?lines=10')
    assert r.status_code == 200
    assert 'entries' in r.data
```

---

## Convenciones de implementacion (vigentes para todas las fases)

1. **Naming:** Ver `docs/conventions/CLEAN_CODE_NAMING_PRINCIPLES_v3_0_1.md`.
   Sin acronimos, sin patrones de diseno como nombre de clase.

2. **Restricciones:** Ver `docs/conventions/RESTRICCIONES_ARQUITECTONICAS_IACT_v1_0_0.md`.
   En particular: CNST-010 (sin cache), CNST-004 (sin Celery/WebSockets),
   CNST-003 (ivr READ-ONLY).

3. **drf_spectacular:** Todo endpoint nuevo tiene `@extend_schema` con
   `summary`, `tags` y `responses`. Los tags se declaran en `schema.py`
   de cada app, nunca en `settings/base.py`.

4. **Auditoria:** Asignar/revocar funcion, aprobar/revocar permiso
   excepcional → emite evento en AuditLog.

5. **Tests:** Cada tarea de implementacion tiene al menos un test positivo
   y uno negativo. Los tests de MariaDB se marcan con
   `@pytest.mark.django_db(databases=['default', 'ivr'])`.

6. **Serializers:** Ningun ViewSet define serializers inline.
   Los serializers viven en `apps/{app}/serializers/`.
