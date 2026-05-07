# Plan de implementacion — IACT API

**Version:** 1.0.0
**Fecha:** 2026-05-07
**Fuente:** DEPENDENCY_GRAPH_v1_0_0.md
**Stack:** Django 4.x + DRF + drf_spectacular + MariaDB (ivr) + PostgreSQL

---

## Resumen de fases

| Fase | Nombre | Tareas | Prioridad |
|---|---|---|---|
| A | Nomenclatura y convenciones | 4 | CRITICA |
| B | Migraciones Django | 3 | CRITICA |
| C | Schema OpenAPI (drf_spectacular) | 5 | ALTA |
| D | Permisos granulares RBAC | 4 | ALTA |
| E | Hardening pipeline IVR | 4 | ALTA |
| F | Reports pendientes | 5 | MEDIA |
| G | Tests de los endpoints nuevos | 8 | ALTA |

---

## FASE A — Nomenclatura y convenciones

**Objetivo:** Eliminar nombres prohibidos por CLEAN_CODE_NAMING_PRINCIPLES
antes de agregar mas codigo.

### A-001 — Renombrar SodRule → SeparationRule en models.py

**Archivo:** `apps/access/models.py`
**Criterio:** `grep -n SodRule apps/access/models.py` retorna 0 resultados.
**Nota:** La tabla en DB mantiene `access_sod_rule`. La migracion en Fase B
crea la nueva tabla con el nombre correcto.

```python
# Antes
class SodRule(SoftDeleteModel):
    ...
    class Meta:
        db_table = 'access_sod_rule'

# Despues
class SeparationRule(SoftDeleteModel):
    ...
    class Meta:
        db_table = 'access_separation_rule'
```

**Estado:** HECHO (corregido al crear este plan)

### A-002 — Renombrar SodRuleViewSet → SeparationRuleViewSet en views.py

**Archivo:** `apps/access/views.py`
**Criterio:** `grep -n SodRule apps/access/views.py` retorna 0 resultados.
**Estado:** HECHO

### A-003 — Renombrar endpoint sod-rules → separation-rules en urls.py

**Archivo:** `apps/access/urls.py`
**Antes:** `router.register(r'sod-rules', SodRuleViewSet, basename='sodrule')`
**Despues:** `router.register(r'separation-rules', SeparationRuleViewSet, basename='separationrule')`
**Criterio:** `GET /api/access/separation-rules/` retorna 200.
**Estado:** HECHO

### A-004 — Crear RESTRICCIONES_ARQUITECTONICAS_IACT_v1_0_0.md

**Archivo:** `docs/conventions/RESTRICCIONES_ARQUITECTONICAS_IACT_v1_0_0.md`
**Contenido:** Complemento de CLEAN_CODE_NAMING_PRINCIPLES con restricciones
a nivel de arquitectura (sin logica de negocio en views, sin queries en
serializers, etc.)
**Criterio:** El archivo existe y cubre al menos 10 restricciones.

---

## FASE B — Migraciones Django

**Objetivo:** Crear las migraciones para los 4 modelos nuevos de access.

### B-001 — makemigrations access

```bash
python manage.py makemigrations access \
    --name "add_access_group_separation_rule_exceptional_permission"
```

**Criterio:** Archivo `apps/access/migrations/0003_*.py` generado con las
4 tablas nuevas: `access_group`, `access_user_group`,
`access_separation_rule`, `access_exceptional_permission`.

### B-002 — Verificar migracion en modo dry-run

```bash
python manage.py sqlmigrate access 0003
```

**Criterio:** El SQL generado muestra los 4 CREATE TABLE sin errores.
No debe aparecer `sod_rule` en ningun nombre de tabla.

### B-003 — Aplicar migracion

```bash
python manage.py migrate access
```

**Criterio:** `python manage.py showmigrations access` muestra [X] en 0003.

---

## FASE C — Schema OpenAPI con drf_spectacular

**Objetivo:** Decorar todos los endpoints nuevos con @extend_schema para que
`drf_spectacular` genere documentacion precisa.

**Instalacion** (si no esta):
```python
# settings/base.py — ya debe existir
INSTALLED_APPS += ['drf_spectacular']
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}
```

### C-001 — Decorar endpoints de pipeline (UC_PIP_01..04)

**Archivo:** `apps/pipeline/views.py`
**Patron:**

```python
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

@extend_schema(
    summary="UC_PIP_01 — Estado del ETL IVR",
    description="Retorna el resumen de salud del pipeline ETL leyendo "
                "job_execution_log en MariaDB.",
    responses={
        200: OpenApiResponse(description="ResumenSalud con estado: ok | degradado | critico"),
        503: OpenApiResponse(description="MariaDB inaccesible"),
    },
    tags=["Pipeline ETL"]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def etl_status(request):
    ...

@extend_schema(
    summary="UC_PIP_02 — Errores del pipeline ETL",
    parameters=[
        OpenApiParameter('trimestre', str, description="Ej: Q01_25"),
        OpenApiParameter('page', int, default=1),
        OpenApiParameter('page_size', int, default=20),
    ],
    tags=["Pipeline ETL"]
)
@api_view(['GET'])
def etl_errors(request):
    ...

@extend_schema(
    summary="UC_PIP_03 — Disponibilidad de datos por quarter",
    parameters=[
        OpenApiParameter('trimestre', str, required=True),
    ],
    responses={200: OpenApiResponse(description="Estado frescura: fresco | aceptable | vencido")},
    tags=["Pipeline ETL"]
)
@api_view(['GET'])
def etl_data_availability(request):
    ...

@extend_schema(
    summary="UC_PIP_04 — Solicitar reintento del pipeline",
    request={"application/json": {"type": "object", "properties": {
        "trimestre": {"type": "string", "example": "Q01_25"},
        "motivo": {"type": "string", "minLength": 20},
    }, "required": ["trimestre", "motivo"]}},
    responses={
        202: OpenApiResponse(description="Reintento iniciado"),
        409: OpenApiResponse(description="Ejecucion activa en curso"),
    },
    tags=["Pipeline ETL"]
)
@api_view(['POST'])
def etl_retry(request):
    ...
```

**Criterio:** `GET /api/schema/` incluye los 4 endpoints de pipeline con
sus parametros y respuestas documentadas.

### C-002 — Decorar endpoints IVR de reports (UC_RPT_12..17)

**Archivo:** `apps/reports/ivr_views.py`
**Patron:**

```python
from drf_spectacular.utils import extend_schema, OpenApiParameter

IVR_PARAMS = [
    OpenApiParameter('quarter', str, description="Ej: Q01_25", required=True),
    OpenApiParameter('segmento', str,
                     enum=['todas','nacional_A','nacional_B','puebla'],
                     default='todas'),
]

@extend_schema(
    summary="UC_RPT_17 — Clientes unicos por segmento",
    parameters=[OpenApiParameter('quarter', str, required=True)],
    tags=["Reportes IVR"]
)
class ClientesReportView(APIView):
    ...
```

**Criterio:** Los 6 endpoints `/api/reports/ivr/*` aparecen en el schema
con sus parametros de quarter y segmento.

### C-003 — Decorar endpoints de access (AccessGroup, SeparationRule, ExceptionalPermission)

**Archivo:** `apps/access/views.py`

```python
from drf_spectacular.utils import extend_schema_view, extend_schema

@extend_schema_view(
    list=extend_schema(summary="UC_PERM_05 — Listar grupos de acceso", tags=["RBAC"]),
    create=extend_schema(summary="UC_PERM_05 — Crear grupo de acceso", tags=["RBAC"]),
    retrieve=extend_schema(summary="UC_PERM_05 — Detalle de grupo", tags=["RBAC"]),
    partial_update=extend_schema(summary="UC_PERM_05 — Modificar grupo", tags=["RBAC"]),
    destroy=extend_schema(summary="UC_PERM_05 — Eliminar grupo", tags=["RBAC"]),
)
class AccessGroupViewSet(viewsets.ModelViewSet):
    ...
```

**Criterio:** AccessGroupViewSet, SeparationRuleViewSet y
ExceptionalPermissionViewSet aparecen en el schema con sus acciones.

### C-004 — Decorar endpoints de logs (UC_LOG_01..07)

**Archivo:** `apps/logs/views.py`
**Criterio:** Los 7 endpoints `/api/logs/*` aparecen en el schema.

### C-005 — Verificar schema generado

```bash
python manage.py spectacular --color --validate --fail-on-warn --file schema.yaml
```

**Criterio:** El comando termina sin warnings ni errores.
El archivo `schema.yaml` contiene al menos 40 paths.

---

## FASE D — Permisos granulares RBAC

**Objetivo:** UC_ACC_01/02 deben usar UserPermission (funcion individual)
en lugar de UserModuleAccess (modulo completo).

### D-001 — Crear endpoint asignar-funcion a usuario

**Archivo:** `apps/access/views.py`

```python
@extend_schema(summary="UC_ACC_01 — Asignar funcion a usuario", tags=["RBAC"])
class UserFunctionAssignView(APIView):
    """
    POST /api/access/users/{user_id}/functions/
    Body: { "function_code": "reports.view" }
    Verifica SeparationRule antes de asignar.
    """
    def post(self, request, user_id):
        fn_code = request.data.get('function_code')
        # 1. Obtener funcion
        # 2. Verificar conflicto SeparationRule
        # 3. Crear UserPermission
        # 4. Emitir evento de auditoria
```

**Criterio:**
- `POST /api/access/users/{id}/functions/` retorna 201 al asignar.
- Si existe SeparationRule activa → retorna 409.
- El evento queda en AuditLog.

### D-002 — Crear endpoint revocar-funcion de usuario

**Archivo:** `apps/access/views.py`

```python
@extend_schema(summary="UC_ACC_02 — Revocar funcion de usuario", tags=["RBAC"])
class UserFunctionRevokeView(APIView):
    """
    DELETE /api/access/users/{user_id}/functions/{function_id}/
    """
```

**Criterio:** `DELETE` elimina el UserPermission y queda en AuditLog.

### D-003 — Registrar URLs en access/urls.py

```python
path('users/<int:user_id>/functions/',
     UserFunctionAssignView.as_view(), name='assign-function'),
path('users/<int:user_id>/functions/<int:function_id>/',
     UserFunctionRevokeView.as_view(), name='revoke-function'),
```

### D-004 — Integrar verificacion SeparationRule en asignacion de grupos

**Archivo:** `apps/access/views.py :: UserAccessGroupViewSet.perform_create`

Al asignar un AccessGroup a un usuario, verificar que ninguna funcion
del grupo genera conflicto con las funciones que el usuario ya tiene.

```python
def perform_create(self, serializer):
    user = serializer.validated_data['user']
    group = serializer.validated_data['access_group']
    for fn in group.functions.all():
        existing_codes = get_user_function_codes(user)
        for existing_code in existing_codes:
            conflict = SeparationRule.objects.filter(
                estado='activa'
            ).filter(
                Q(function_a__code=fn.code, function_b__code=existing_code) |
                Q(function_a__code=existing_code, function_b__code=fn.code)
            ).first()
            if conflict:
                raise ValidationError(f'Conflicto SeparationRule: {conflict}')
    serializer.save(granted_by=self.request.user)
```

**Criterio:** Asignar grupo que genera conflicto retorna 400 con detalle.

---

## FASE E — Hardening pipeline IVR

**Objetivo:** Robustecer los endpoints de pipeline para produccion.

### E-001 — Timeout configurable en conexiones MariaDB

**Archivo:** `apps/pipeline/views.py`

Los timeouts de MariaDB deben ser configurables via settings, no hardcoded.

```python
IVR_QUERY_TIMEOUT = getattr(settings, 'IVR_QUERY_TIMEOUT_SEC', 30)

with connections['ivr'].cursor() as cursor:
    cursor.execute(f"SET SESSION MAX_EXECUTION_TIME={IVR_QUERY_TIMEOUT * 1000}")
    cursor.execute(sql, params)
```

**Criterio:** `IVR_QUERY_TIMEOUT_SEC` en settings controla el timeout.

### E-002 — Cache de resultados IVR (UC_RPT_17..12)

Los SPs de reporte son costosos. Agregar cache por quarter + segmento.

```python
from django.core.cache import cache

def get_clientes(quarter: str) -> list[dict]:
    key = f'ivr:clientes:{quarter}'
    cached = cache.get(key)
    if cached:
        return cached
    result = _call_sp('sp_rpt_clientes', [quarter])
    cache.set(key, result, timeout=300)  # 5 minutos
    return result
```

**Criterio:** Segunda llamada al mismo quarter es servida desde cache.
TTL configurable via `IVR_CACHE_TTL_SEC` en settings.

### E-003 — Validacion de quarter contra quarters disponibles en MariaDB

Actualmente `QUARTERS_VALIDOS` es una constante hardcodeada. Debe
consultarse desde `base_ivr_detalle`.

```python
def get_available_quarters() -> set[str]:
    key = 'ivr:available_quarters'
    cached = cache.get(key)
    if cached:
        return set(cached)
    with connections['ivr'].cursor() as cursor:
        cursor.execute("SELECT DISTINCT trimestre FROM base_ivr_detalle")
        quarters = {row[0] for row in cursor.fetchall()}
    cache.set(key, list(quarters), timeout=3600)
    return quarters
```

**Criterio:** Un quarter inexistente en la BD retorna 404, no 200 con
lista vacia.

### E-004 — Endpoint de health de la conexion IVR

```python
@extend_schema(summary="Estado de la conexion MariaDB IVR", tags=["Health"])
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ivr_health(request):
    """GET /api/pipeline/ivr-health/"""
    try:
        with connections['ivr'].cursor() as cursor:
            cursor.execute("SELECT 1")
        return Response({'status': 'ok', 'database': 'ivr_legacy'})
    except Exception as e:
        return Response({'status': 'error', 'detail': str(e)}, status=503)
```

**Criterio:** Retorna 200 cuando MariaDB esta activo, 503 cuando no.

---

## FASE F — Reports pendientes

### F-001 — UC_RPT_07 — Programar reporte

```python
class ScheduledReportView(APIView):
    """POST /api/reports/scheduled/ — Crear reporte programado."""
```

### F-002 — UC_RPT_08 — Listar reportes programados

```python
class ScheduledReportListView(APIView):
    """GET /api/reports/scheduled/"""
```

### F-003 — UC_RPT_09 — Aplicar filtro guardado

Depende de UC_RPT_10.

### F-004 — UC_RPT_10 — Guardar vista

```python
class SavedViewViewSet(viewsets.ModelViewSet):
    """CRUD /api/reports/saved-views/"""
```

### F-005 — UC_RPT_02 — SSE metricas tiempo real

**Requisito previo:** Servidor ASGI (uvicorn). No implementable en
Django sync. Crear stub que documente el contrato:

```python
@extend_schema(
    summary="UC_RPT_02 — Metricas en tiempo real (SSE)",
    description="Requiere servidor ASGI. En modo sync retorna snapshot.",
    tags=["Reportes"]
)
class MetricasRealtimeView(APIView):
    ...
```

---

## FASE G — Tests de endpoints nuevos

### G-001 — Tests pipeline UC_PIP_01 (MariaDB)

```python
@pytest.mark.django_db(databases=['default', 'ivr'])
def test_etl_status_retorna_resumen_salud(authenticated_client, ivr_data):
    response = authenticated_client.get('/api/pipeline/status/')
    assert response.status_code == 200
    assert 'resumen' in response.data
    assert response.data['resumen']['estado_general'] in ('ok','degradado','critico')
```

### G-002 — Tests pipeline UC_PIP_04 reintento

```python
def test_retry_requiere_motivo_minimo(authenticated_client):
    response = authenticated_client.post('/api/pipeline/retry/',
        {'trimestre': 'Q01_25', 'motivo': 'corto'})
    assert response.status_code == 400

def test_retry_rechaza_si_hay_running(authenticated_client, ivr_running):
    response = authenticated_client.post('/api/pipeline/retry/',
        {'trimestre': 'Q01_25', 'motivo': 'x' * 20})
    assert response.status_code == 409
```

### G-003 — Tests IVR reports UC_RPT_17

```python
def test_clientes_quarter_invalido(authenticated_client):
    response = authenticated_client.get('/api/reports/ivr/clients/?quarter=XXXX')
    assert response.status_code == 400

@pytest.mark.django_db(databases=['default', 'ivr'])
def test_clientes_retorna_3_segmentos(authenticated_client):
    response = authenticated_client.get('/api/reports/ivr/clients/?quarter=Q01_25')
    assert response.status_code == 200
    assert response.data['total_filas'] == 3
```

### G-004 — Tests AccessGroup CRUD

### G-005 — Tests SeparationRule conflicto

```python
def test_separation_rule_detecta_conflicto(authenticated_client, fn_a, fn_b):
    # Crear la regla
    authenticated_client.post('/api/access/separation-rules/',
        {'function_a': fn_a.id, 'function_b': fn_b.id, 'justificacion': '...'})
    # Verificar conflicto
    response = authenticated_client.get(
        f'/api/access/separation-rules/check/?function_a={fn_a.id}&function_b={fn_b.id}')
    assert response.data['tiene_conflicto'] is True
```

### G-006 — Tests ExceptionalPermission flujo completo

### G-007 — Tests EffectivePermissions union de fuentes

### G-008 — Tests logs health y metrics

---

## Convenciones de implementacion

Todos los endpoints nuevos deben seguir:

1. **Naming** (ver CLEAN_CODE_NAMING_PRINCIPLES_v3_0_1.md): sin acronimos,
   sin patrones como nombre de clase.

2. **drf_spectacular** (ver Fase C): todo endpoint tiene `@extend_schema`
   con `summary`, `tags`, `responses`. El schema no debe tener warnings.

3. **Conexion IVR**: siempre dentro de `try/except OperationalError` que
   retorna 503. Nunca asumir que MariaDB esta disponible.

4. **Auditoria**: acciones que modifican acceso (asignar/revocar funcion,
   aprobar permiso excepcional) emiten evento en AuditLog.

5. **Tests**: cada tarea de implementacion tiene al menos un test positivo
   y un test negativo (parametro invalido o condicion de error).
