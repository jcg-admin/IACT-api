# Análisis Minucioso — Integración IACT-db con IACT-api

**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Repositorios:** `/tmp/references/IACT-db` (MariaDB) y `/tmp/references/IACT-api` (Django)
**Método:** Lectura completa del código fuente de ambos repositorios.
Sin inferencias — solo lo que el código contiene.

---

## Resumen ejecutivo

La integración funciona para los 7 SPs de reporte existentes. Hay
**1 bug que provoca un NameError en producción**, **2 nuevos objetos de IACT-db
sin endpoint en IACT-api**, y **1 gap de observabilidad** donde
`pipeline_event_log` no está expuesto a Django. Ninguno de los cambios de
FASE 1-4 rompió funcionalidad existente.

---

## Mapa de integración — qué llama a qué

### Desde Django → MariaDB (vía `connections['ivr']`)

| Capa Django | Método | SP / tabla MariaDB | Estado |
|---|---|---|---|
| `ivr_services.get_clients()` | `callproc` | `sp_rpt_clientes` | OK |
| `ivr_services.get_transfer_centers()` | `callproc` | `sp_rpt_centros_transferencia` | OK |
| `ivr_services.get_abandoned_calls()` | `callproc` | `sp_rpt_llamadas_abandonadas` | OK |
| `ivr_services.get_cmenu_errors()` | `callproc` | `sp_rpt_cMENU_ERROR` | OK |
| `ivr_services.get_centers_by_segment()` | `callproc` | `sp_rpt_centros_xsegmento` | OK |
| `ivr_services.get_redirected_menus()` | `callproc` | `sp_rpt_menu_redirigidos` | OK |
| `ivr_services.get_center_menus()` | `callproc` | `sp_rpt_menu_centro` | OK |
| `ivr_services.get_available_quarters()` | `execute` | `base_ivr_detalle` (DISTINCT) | OK |
| `pipeline/views.etl_status` | `execute` | `job_execution_log` | OK |
| `pipeline/views.etl_errors` | `execute` | `job_execution_log WHERE FAILED` | OK |
| `pipeline/views.etl_data_availability` | `execute` | `job_execution_log WHERE SUCCESS` | **BUG** |
| `pipeline/views.etl_retry` | `callproc` | `sp_etl_historico` | OK |
| `pipeline/views.ivr_health` | `execute` | `SELECT VERSION()` | OK |
| `run_etl.py Command` | `callproc` | `sp_etl_maestro` | OK |
| `run_etl.py Command` | `execute` | `etl_runs` (INSERT/UPDATE) | OK |
| `logs/views.ETLLogTailView` | `execute` | `job_execution_log` | OK |
| `logs/views.LogMetricsView` | `execute` | `job_execution_log` | OK |

### Objetos de IACT-db SIN endpoint en IACT-api

| Objeto IACT-db | Tipo | Implementado | Endpoint en IACT-api |
|---|---|---|---|
| `sp_rpt_resumen_abandono_rollup` | SP nuevo (T3.2) | Sí | **NO — falta** |
| `v_etl_rendimiento` | Vista nueva (T3.1) | Sí | **NO — falta** |
| `pipeline_event_log` | Tabla (T1.1) | Sí | **NO — falta** |

---

## BUG-01 — `NameError: trimestre` en `etl_data_availability`

**Severidad:** CRÍTICA — el endpoint falla con `NameError` cuando no hay
datos para el quarter solicitado.  
**Archivo:** `apps/pipeline/views.py`, función `etl_data_availability`, línea ~398.

### Descripción

Cuando `job_execution_log` no tiene registros SUCCESS para el quarter
pedido (`row` es `None`), la rama de respuesta usa la variable `trimestre`
que nunca fue definida en el scope de la función:

```python
# CÓDIGO ACTUAL (bug):
if not row:
    return Response({
        'trimestre':             trimestre,    # ← NameError: 'trimestre' no existe
        'status_frescura':       'sin_datos',
        ...
    })

quarter_name, ultima_carga, registros = row  # ← esto solo corre si row no es None
```

`trimestre` no existe — debería ser el parámetro `quarter` de la función.

### Corrección

```python
if not row:
    return Response({
        'trimestre':             quarter,      # ← variable correcta
        'status_frescura':       'sin_datos',
        'ultima_carga':          None,
        'registros_disponibles': 0,
        'minutos_desde_etl':     None,
    })
```

### Impacto

Este endpoint se activa con cualquier quarter que aún no tenga datos de
producción. En el entorno de desarrollo actual (donde `Q01_25` sí tiene
datos) el bug no se dispara, lo que explica por qué no ha sido detectado.
En un nuevo entorno o con un quarter sin ETL completado → `NameError 500`.

---

## GAP-01 — `sp_rpt_resumen_abandono_rollup` sin endpoint

**Severidad:** MEDIA — funcionalidad nueva sin exposición  
**Contexto:** El SP fue creado en T3.2. Retorna la jerarquía completa de
abandono (detalle + subtotales + TOTAL) en una sola llamada — 13 filas.

### Situación actual

`ivr_services.py` tiene 7 funciones, una por SP de reporte existente.
El nuevo SP `sp_rpt_resumen_abandono_rollup` **no tiene función** en
`ivr_services.py` ni view en `ivr_views.py` ni URL en `reports/urls.py`.

### Lo que falta en IACT-api

**En `ivr_services.py`:**
```python
def get_abandonment_summary(quarter: str) -> list[dict]:
    """
    Resumen ejecutivo de abandono con jerarquía completa.
    Llama: sp_rpt_resumen_abandono_rollup(p_quarter)
    Retorna: 13 filas (3 segs × 3 menus + 3 subtotales + 1 TOTAL).
    """
    return _call_sp('sp_rpt_resumen_abandono_rollup', [quarter])
```

**En `ivr_views.py`:**
```python
class AbandonmentSummaryView(APIView):
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'reports.view_ivr'

    def get(self, request):
        quarter = request.query_params.get('quarter', 'Q01_25')
        errors = _validate(quarter=quarter)
        if errors:
            return Response({'errors': errors}, status=400)
        return _ivr_response(svc.get_abandonment_summary, quarter,
                             extra={'quarter': quarter})
```

**En `reports/urls.py`:**
```python
path('ivr/abandonment-summary/', AbandonmentSummaryView.as_view(),
     name='ivr-abandonment-summary'),
```

### Columnas nuevas en SPs existentes que Django ya consume

Los SPs modificados en FASE 2 y FASE 4 retornan columnas nuevas que Django
recibirá automáticamente. El patrón `dict(zip(cols, row))` en `_call_sp`
construye el diccionario a partir de `cursor.description` — cualquier columna
nueva que el SP retorne aparece en el JSON de respuesta sin cambios en Django.

| SP | Columnas nuevas | Impacto en IACT-api |
|---|---|---|
| `sp_rpt_centros_xsegmento` | `percentil_actividad`, `pct_del_lider` | Aparecen en `/ivr/centers-by-segment/` automáticamente ✓ |
| `sp_rpt_centros_transferencia` | `cuartil_centro` | Aparece en `/ivr/transfer-centers/` automáticamente ✓ |
| `sp_rpt_menu_redirigidos` | Sin columnas nuevas (solo refactoring interno) | Sin impacto ✓ |
| `sp_rpt_cMENU_ERROR` | Sin columnas nuevas | Sin impacto ✓ |
| `sp_rpt_menu_centro` | Sin columnas nuevas | Sin impacto ✓ |
| `sp_rpt_clientes` | Sin columnas nuevas | Sin impacto ✓ |

---

## GAP-02 — `v_etl_rendimiento` sin endpoint

**Severidad:** BAJA — la vista es de observabilidad interna  
**Contexto:** La vista fue creada en T3.1. Expone `duracion_seg`,
`duracion_anterior_seg` y `delta_seg` para detectar regresiones del ETL.

### Situación actual

Ningún archivo en IACT-api referencia `v_etl_rendimiento`.

### Lo que falta en IACT-api (opcional)

Podría agregarse como nuevo endpoint en `pipeline/views.py`:

```python
@api_view(['GET'])
@permission_classes([IsAuthenticated, HasFunction])
def etl_performance(request):
    """
    GET /api/pipeline/performance/
    Lee v_etl_rendimiento: duracion, anterior y delta por step.
    """
    sql = """
        SELECT job_name, step_name, start_time,
               duracion_seg, duracion_anterior_seg, delta_seg
        FROM v_etl_rendimiento
        ORDER BY step_name, start_time DESC
        LIMIT 50
    """
    with connections['ivr'].cursor() as cursor:
        cursor.execute(sql)
        cols = [c[0] for c in cursor.description]
        return Response([dict(zip(cols, row)) for row in cursor.fetchall()])
```

Este endpoint es opcional — `v_etl_rendimiento` es principalmente una
herramienta de diagnóstico para el equipo, no un dato de negocio para
el frontend. La prioridad de implementación es baja.

---

## GAP-03 — `pipeline_event_log` sin endpoint

**Severidad:** MEDIA — tabla de auditoría central sin acceso desde la API  
**Contexto:** La tabla `pipeline_event_log` recibe eventos de todos los SPs
de IACT-db desde FASE 1. Es la tabla de auditoría centralizada. Django no
tiene ningún endpoint que la lea.

### Situación actual

`logs/views.py` expone `job_execution_log` (UC_LOG_02, UC_LOG_07) pero
no expone `pipeline_event_log`. El operador que quiera saber "¿qué parámetros
inválidos ha enviado el frontend?" o "¿qué fases del ETL han fallado?" no
tiene acceso via API.

### Lo que falta en IACT-api

En `logs/views.py`, un nuevo endpoint:

```python
class PipelineEventLogView(APIView):
    """
    UC_LOG_08 — Eventos del pipeline analítico.
    GET /api/logs/pipeline-events/
    Fuente: pipeline_event_log en MariaDB ivr_legacy.
    """
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'logs.view'

    def get(self, request):
        quarter    = request.query_params.get('quarter')
        error_type = request.query_params.get('error_type')
        hours      = min(168, int(request.query_params.get('hours', 48)))
        page_size  = min(100, int(request.query_params.get('page_size', 20)))

        conditions = ["ts >= DATE_SUB(NOW(), INTERVAL %s HOUR)"]
        params = [hours]
        if quarter:
            conditions.append("p_quarter = %s"); params.append(quarter)
        if error_type:
            conditions.append("error_type = %s"); params.append(error_type)

        where = ' AND '.join(conditions)
        sql = f"""
            SELECT id, ts, error_type, severity, sp_nombre,
                   sql_state, p_quarter, p_segmento,
                   LEFT(error_message, 200) AS error_message,
                   job_log_id, ejecutado_por
            FROM pipeline_event_log
            WHERE {where}
            ORDER BY ts DESC LIMIT %s
        """
        with connections['ivr'].cursor() as cursor:
            cursor.execute(sql, params + [page_size])
            cols = [c[0] for c in cursor.description]
            events = [dict(zip(cols, row)) for row in cursor.fetchall()]
        return Response({'total': len(events), 'events': events})
```

---

## Verificación: cambios de IACT-db que SÍ son compatibles con IACT-api

### Renombre ivr_error_log → pipeline_event_log

IACT-api **nunca referenció** `ivr_error_log`. La búsqueda en todos los
archivos `.py` de IACT-api devuelve 0 resultados. El renombre no rompe nada.

### SIGNAL ahora inserta en pipeline_event_log antes de propagar

Cuando Django llama a un SP con parámetros inválidos (ej: quarter='INVALIDO'):
1. El SP inserta en `pipeline_event_log` (nuevo comportamiento FASE 1)
2. El SP lanza `SIGNAL SQLSTATE '22023'` (igual que antes)
3. Django captura `OperationalError` o `ProgrammingError` vía `_ivr_response`

El comportamiento observable desde Django no cambia. El 400/503 sigue
propagando igual. El INSERT a `pipeline_event_log` es transparente.

### Nuevas columnas en SPs de reporte existentes

El patrón `dict(zip(cols, row))` en `_call_sp` construye dicts dinámicamente
desde `cursor.description`. Nuevas columnas aparecen en el JSON sin cambios
en Django — aditividad estricta, sin breaking changes.

### sp_etl_maestro v2.5.0 — INSERTs a pipeline_event_log en handlers

`run_etl.py` llama `callproc("sp_etl_maestro", [])`. Cuando el SP falla,
Django recibe el error via `OperationalError` y lo maneja correctamente.
El nuevo INSERT a `pipeline_event_log` dentro del handler es interno al SP
y transparente para Django.

---

## Resumen de hallazgos

| ID | Tipo | Descripción | Archivo IACT-api | Prioridad |
|---|---|---|---|---|
| BUG-01 | Bug — NameError | `trimestre` sin definir en rama `if not row` | `apps/pipeline/views.py:398` | CRÍTICA |
| GAP-01 | Feature faltante | Sin endpoint para `sp_rpt_resumen_abandono_rollup` | `apps/reports/ivr_services.py` | MEDIA |
| GAP-02 | Feature faltante | Sin endpoint para `v_etl_rendimiento` | `apps/pipeline/views.py` | BAJA |
| GAP-03 | Feature faltante | Sin endpoint para `pipeline_event_log` | `apps/logs/views.py` | MEDIA |
