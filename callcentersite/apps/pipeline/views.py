"""
Views para app pipeline.

UC_PIP_01: Supervision del status del ETL IVR.
  Lee directamente de job_execution_log y etl_runs en MariaDB (ivr_legacy)
  via connections['ivr'].cursor() segun especifica el UC.

  El modelo PipelineExecution del UC mapea a job_execution_log:
    id             → id
    source_table   → tabla_origen
    trimestre      → quarter_name
    started_at     → start_time
    finished_at    → end_time
    status         → status  (SUCCESS/FAILED/RUNNING/SKIP)
    base_records   → records_procesados
    error_message  → error_message
    executed_by    → ejecutado_por

  ResumenSalud calculado segun UC:
    ok         — ultima ejecucion exitosa dentro de las ultimas 14h
    degradado  — ultima exitosa entre 14h y 24h
    critico    — ninguna exitosa en 24h o ultima es fallida

Nota: La implementacion anterior usaba ETLExecution (modelo Django ORM
en PostgreSQL) lo cual era incorrecto. ETLExecution corresponde al
registro del management command Django (etl_runs), no al log granular
del pipeline (job_execution_log).
"""
from datetime import datetime, timedelta, timezone

from django.conf import settings
from django.db import connections, OperationalError, ProgrammingError
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from apps.access.permissions.function_permissions import HasFunction
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_pipeline_runs(limit: int = 20) -> list[dict]:
    """
    Lee las ultimas ejecuciones del ETL desde job_execution_log en MariaDB.
    Solo incluye registros de nivel 'maestro' para el resumen de salud.
    Los pasos internos (etl_base_detalle, etl_base_clientes) se agrupan
    bajo su ejecucion maestra correspondiente.
    """
    sql = """
        SELECT
            id,
            job_name,
            quarter_name,
            step_name,
            tabla_origen,
            start_time,
            end_time,
            status,
            records_procesados,
            duracion_seg,
            error_message,
            ejecutado_por
        FROM job_execution_log
        ORDER BY start_time DESC
        LIMIT %s
    """
    timeout_sec = getattr(settings, 'IVR_QUERY_TIMEOUT_SEC', 30)
    with connections['ivr'].cursor() as cursor:
        cursor.execute(f"SET SESSION MAX_STATEMENT_TIME={timeout_sec}")
        cursor.execute(sql, [limit])
        cols = [c[0] for c in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]


def _build_pipeline_health_summary(runs: list[dict]) -> dict:
    """
    Construye ResumenSalud segun la logica del UC_PIP_01:
      ok        — ultima exitosa dentro de 14h
      degradado — ultima exitosa entre 14h y 24h
      critico   — ninguna exitosa en 24h o ultima es fallida
    """
    now = datetime.now(timezone.utc)
    window_14h = now - timedelta(hours=14)
    window_24h = now - timedelta(hours=24)

    running_execution   = None
    last_successful       = None
    last_failed       = None
    total_successful_24h   = 0
    total_failed_24h   = 0

    for run in runs:
        end = run['end_time']
        # Normalizar a UTC si no tiene timezone
        if end and hasattr(end, 'tzinfo') and end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        start = run['start_time']
        if start and hasattr(start, 'tzinfo') and start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)

        s = run['status']

        if s == 'RUNNING' and running_execution is None:
            running_execution = run

        if s == 'SUCCESS':
            if last_successful is None:
                last_successful = run
            if end and end >= window_24h:
                total_successful_24h += 1

        if s == 'FAILED':
            if last_failed is None:
                last_failed = run
            if end and end >= window_24h:
                total_failed_24h += 1

    # Calcular status general
    if last_successful:
        last_successful_end = last_successful['end_time']
        if last_successful_end and hasattr(last_successful_end, 'tzinfo') and last_successful_end.tzinfo is None:
            last_successful_end = last_successful_end.replace(tzinfo=timezone.utc)

        if last_successful_end and last_successful_end >= window_14h:
            status_general = 'ok'
        elif last_successful_end and last_successful_end >= window_24h:
            status_general = 'degradado'
        else:
            status_general = 'critico'
    else:
        status_general = 'critico'

    if last_failed and last_successful is None:
        status_general = 'critico'

    return {
        'status_general':           status_general,
        'running_execution':       last_successful if running_execution else None,
        'last_successful_execution': last_successful,
        'last_failed_execution': last_failed,
        'total_successful_24h':       total_successful_24h,
        'total_failed_24h':       total_failed_24h,
    }


def _format_run(run: dict | None) -> dict | None:
    """Serializa un registro de job_execution_log al formato del UC."""
    if run is None:
        return None
    return {
        'id':                run['id'],
        'source_table':      run['tabla_origen'],
        'trimestre':         run['quarter_name'],
        'step_name':         run['step_name'],
        'started_at':        run['start_time'],
        'finished_at':       run['end_time'],
        'status':            run['status'],
        'base_records':      run['records_procesados'],
        'duracion_seg':      run['duracion_seg'],
        'error_message':     run['error_message'],
        'executed_by':       run['ejecutado_por'],
    }


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

@extend_schema(
    summary="UC_PIP_01 — Estado del pipeline ETL IVR",
    description=(
        "Resumen de salud del pipeline. Lee job_execution_log en MariaDB ivr_legacy. "
        "Retorna status: ok (ultima exitosa < 14h), degradado (14-24h) o critico (> 24h)."
    ),
    responses={
        200: OpenApiResponse(description="ResumenSalud con status ok | degradado | critico"),
        503: OpenApiResponse(description="MariaDB ivr_legacy no disponible"),
    },
    tags=["Estado del Pipeline"]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, HasFunction])
def etl_status(request):
    """
    UC_PIP_01 — Supervision del status del ETL IVR.

    GET /api/pipeline/status/

    Función RBAC: PIP-001 view_pipeline_status
    CNST-010: HasFunction verifica required_function='PIP-001' automáticamente.

    Response:
    {
        "resumen": {
            "status_general": "ok" | "degradado" | "critico",
            "running_execution": {...} | null,
            "ultima_ejecucion_exitosa": {...} | null,
            "ultima_ejecucion_fallida": {...} | null,
            "total_successful_24h": int,
            "total_failed_24h": int
        },
        "ultimas_ejecuciones": [...]
    }

    Fuente: job_execution_log en MariaDB ivr_legacy via connections['ivr'].
    """
    try:
        runs = _get_pipeline_runs(limit=20)
    except (OperationalError, ProgrammingError) as e:
        return Response(
            {'error': 'Could not connect to the IVR database.',
             'detail': str(e)},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    if not runs:
        return Response({
            'resumen': {
                'status_general':           'critico',
                'running_execution':       None,
                'last_successful_execution': None,
                'last_failed_execution': None,
                'total_successful_24h':       0,
                'total_failed_24h':       0,
            },
            'latest_executions': [],
            'message': 'No hay ejecuciones ETL registradas.'
        })

    resumen = _build_pipeline_health_summary(runs)

    return Response({
        'resumen': {
            'status_general':           resumen['status_general'],
            'running_execution':       _format_run(resumen['running_execution']),
            'last_successful_execution': _format_run(resumen['last_successful_execution']),
            'last_failed_execution': _format_run(resumen['last_failed_execution']),
            'total_successful_24h':       resumen['total_successful_24h'],
            'total_failed_24h':       resumen['total_failed_24h'],
        },
        'latest_executions': [_format_run(r) for r in runs],
    })


# required_function='PIP-001' — HasFunction lo lee vía getattr(view, 'required_function')
# En @api_view, la view es el wrapper function, por eso se setea como atributo.
# F1-H-005: etl_status tenía una verificación manual has_function('pipeline.view_status')
# que usaba un namespace legado en lugar del código canónico v5.4.0.
etl_status.required_function = 'PIP-001'
# ---------------------------------------------------------------------------
# B-04: UC_PIP_02 — Errores ETL
# ---------------------------------------------------------------------------

@extend_schema(
    summary="UC_PIP_02 — Errores del pipeline ETL",
    parameters=[
        OpenApiParameter('quarter', str,
            description="Filter by quarter. E.g.: Q01_25"),
        OpenApiParameter('page', int, default=1),
        OpenApiParameter('page_size', int, default=20,
            description="Max 100 registros por pagina"),
    ],
    responses={
        200: OpenApiResponse(description="Lista paginada de errores ETL"),
        503: OpenApiResponse(description="MariaDB no disponible"),
    },
    tags=["Estado del Pipeline"]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, HasFunction])
def etl_errors(request):
    """
    UC_PIP_02 — Ver errores del pipeline ETL.

    GET /api/pipeline/errors/
    Query params:
      quarter (optional): filter by quarter (e.g.: Q01_25)
      page      (opcional): pagina (default 1)
      page_size (opcional): tamano de pagina (default 20, max 100)

    Fuente: job_execution_log WHERE status='FAILED' en MariaDB.
    RBAC: PIP-002 (view_pipeline_errors) — verificado por HasFunction.

    Prerequisito FASE 3 (2026-05-13):
      Eliminada verificación inline has_function('pipeline.view_errors')
      (formato legacy). HasFunction lee required_function='PIP-002' vía
      getattr(view, 'required_function') — asignado al final del módulo.
    """

    quarter = request.query_params.get('quarter')
    try:
        page      = max(1, int(request.query_params.get('page', 1)))
        page_size = min(100, max(1, int(request.query_params.get('page_size', 20))))
    except (ValueError, TypeError):
        page, page_size = 1, 20

    offset = (page - 1) * page_size

    conditions = ["status = 'FAILED'"]
    params = []

    if quarter:
        conditions.append("quarter_name = %s")
        params.append(quarter)

    where = ' AND '.join(conditions)
    sql = f"""
        SELECT id, job_name, quarter_name, step_name, tabla_origen,
               start_time, end_time, error_message, ejecutado_por
        FROM job_execution_log
        WHERE {where}
        ORDER BY start_time DESC
        LIMIT %s OFFSET %s
    """
    params += [page_size, offset]

    sql_count = f"SELECT COUNT(*) FROM job_execution_log WHERE {where}"

    try:
        with connections['ivr'].cursor() as cursor:
            cursor.execute(sql_count, params[:-2] if quarter else [])
            total = cursor.fetchone()[0]
            cursor.execute(sql, params)
            cols = [c[0] for c in cursor.description]
            errors = [dict(zip(cols, row)) for row in cursor.fetchall()]
    except (OperationalError, ProgrammingError) as e:
        return Response({'error': 'Could not connect to MariaDB.', 'detail': str(e)},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE)

    # UC_PIP_02 CA-03: sanitizar PII antes de retornar (CNST-026)
    from apps.pipeline.pii_scanner import PIIScanner
    errors = [PIIScanner.sanitize_error_row(row) for row in errors]

    return Response({
        'total':    total,
        'page':     page,
        'page_size':page_size,
        'errors': errors,
    })


# ---------------------------------------------------------------------------
# B-04: UC_PIP_03 — Disponibilidad de datos por quarter
# ---------------------------------------------------------------------------

@extend_schema(
    summary="UC_PIP_03 — Disponibilidad de datos por quarter",
    parameters=[
        OpenApiParameter('quarter', str, required=True,
            description="Quarter to query. E.g.: Q01_25"),
    ],
    responses={
        200: OpenApiResponse(
            description="Estado frescura: fresco | aceptable | vencido | sin_datos"),
        400: OpenApiResponse(description="Parameter quarter is required."),
        503: OpenApiResponse(description="MariaDB no disponible"),
    },
    tags=["Estado del Pipeline"]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, HasFunction])
def etl_data_availability(request):
    """
    UC_PIP_03 — Ver disponibilidad de datos por quarter.

    GET /api/pipeline/data-availability/
    Query params:
      quarter (required): e.g. Q01_25

    Retorna el ultimo ETL exitoso para ese quarter y el status de frescura.
    Fuente: job_execution_log WHERE status='SUCCESS' en MariaDB.
    RBAC: PIP-003 (view_data_availability) — verificado por HasFunction.

    Prerequisito FASE 3 (2026-05-13):
      Eliminada verificación inline has_function('pipeline.view_data_availability')
      (formato legacy namespace.action). HasFunction lee required_function='PIP-003'.
    """

    quarter = request.query_params.get('quarter')
    if not quarter:
        return Response({'error': 'Parameter quarter is required.'}, status=400)

    sql = """
        SELECT quarter_name, MAX(end_time) AS ultima_carga,
               SUM(records_procesados) AS registros_disponibles
        FROM job_execution_log
        WHERE status = 'SUCCESS'
          AND quarter_name = %s
          AND step_name = 'etl_base_detalle'
        GROUP BY quarter_name
    """
    try:
        with connections['ivr'].cursor() as cursor:
            cursor.execute(sql, [quarter])
            row = cursor.fetchone()
    except (OperationalError, ProgrammingError) as e:
        return Response({'error': 'Could not connect to MariaDB.', 'detail': str(e)},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE)

    if not row:
        return Response({
            'trimestre':             quarter,       # H-F1-001: era 'trimestre' (NameError)
            'status_frescura':       'sin_datos',
            'ultima_carga':          None,
            'registros_disponibles': 0,
            'minutos_desde_etl':     None,
        })

    quarter_name, ultima_carga, registros = row
    now = datetime.now(timezone.utc)
    if ultima_carga:
        if ultima_carga.tzinfo is None:
            ultima_carga = ultima_carga.replace(tzinfo=timezone.utc)
        minutos = int((now - ultima_carga).total_seconds() / 60)
        if minutos < 60 * 14:
            frescura = 'fresco'
        elif minutos < 60 * 24:
            frescura = 'aceptable'
        else:
            frescura = 'vencido'
    else:
        minutos = None
        frescura = 'sin_datos'

    return Response({
        'trimestre':             quarter_name,
        'status_frescura':       frescura,
        'ultima_carga':          ultima_carga,
        'registros_disponibles': registros,
        'minutos_desde_etl':     minutos,
    })


# ---------------------------------------------------------------------------
# B-04: UC_PIP_04 — Solicitar reintento de pipeline
# ---------------------------------------------------------------------------

@extend_schema(
    summary='UC_PIP_04 — Solicitar reintento del pipeline',
    description=(
        'POST /api/pipeline/retry/\n\n'
        'Solicita un reintento del ETL para el quarter indicado.\n\n'
        '**Requisitos:**\n'
        '- `reason` ≥ 20 caracteres (CA-03).\n'
        '- No puede haber una ejecución `RUNNING` activa (CA-02).\n'
        '- Idempotente por `run_id`: doble retry del mismo `run_id` → 409 (CA-05).\n\n'
        '**Auditoría:** emite `PIPELINE_RETRY_REQUESTED` con actor, reason y run_id (CA-04).'
    ),
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'quarter':  {'type': 'string', 'example': 'Q01_25'},
                'reason':   {'type': 'string', 'minLength': 20,
                             'description': 'Motivo del reintento (≥ 20 caracteres).'},
                'run_id':   {'type': 'string', 'nullable': True,
                             'description': 'ID del run a reintentar (para idempotencia CA-05).'},
                'priority': {'type': 'string', 'enum': ['normal', 'high'],
                             'default': 'normal',
                             'description': 'high → encola al frente (CA-06).'},
            },
            'required': ['quarter', 'reason'],
        }
    },
    responses={
        202: OpenApiResponse(description='Reintento iniciado — {new_run_id, quarter, priority}'),
        400: OpenApiResponse(description='Parámetros inválidos o reason < 20 chars'),
        403: OpenApiResponse(description='Sin PIP-004 request_pipeline_retry'),
        404: OpenApiResponse(description='Pipeline / quarter no encontrado'),
        409: OpenApiResponse(description='ALREADY_RUNNING o ALREADY_RETRIED (idempotencia)'),
        503: OpenApiResponse(description='MariaDB no disponible'),
    },
    tags=['Estado del Pipeline'],
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, HasFunction])
def etl_retry(request):
    """
    UC_PIP_04 — Solicitar reintento del pipeline ETL.

    POST /api/pipeline/retry/
    Body: { "quarter": "Q01_25", "reason": "...", "run_id"?: "...", "priority"?: "high" }

    CNST-010: HasFunction verifica required_function='PIP-004'.
    CA-03: reason ≥ 20 caracteres.
    CA-04: AuditEvent PIPELINE_RETRY_REQUESTED.
    CA-05: idempotencia — doble retry del mismo run_id → 409.
    CA-06: priority=high encola al frente.
    """
    from apps.pipeline.pipeline_retry_service import (
        PipelineRetryValidator, PipelineRetryIdempotency,
    )
    from apps.audit.services import AuditLogService

    quarter  = request.data.get('quarter')
    reason   = request.data.get('reason', '')
    run_id   = request.data.get('run_id')          # opcional — para idempotencia CA-05
    priority = request.data.get('priority', 'normal')

    # CA-03: reason obligatorio y ≥ 20 chars
    if not quarter:
        return Response({'error': 'quarter requerido.'}, status=400)
    try:
        PipelineRetryValidator.validate_reason(reason)
    except ValueError as e:
        return Response({'error': 'VALIDATION_ERROR', 'detail': str(e)}, status=400)

    # CA-05: idempotencia por run_id
    if run_id and PipelineRetryIdempotency.is_already_retried(run_id):
        return Response(
            {'error': 'ALREADY_RETRIED',
             'detail': f'El run_id {run_id} ya fue reintentado.'},
            status=409,
        )

    # Parsear quarter: Q01_25 → year=2025, quarter_num=1
    try:
        parts       = quarter.upper().split('_')
        quarter_num = int(parts[0][1:])
        year        = 2000 + int(parts[1])
        assert 1 <= quarter_num <= 4
        assert 2020 <= year <= 2030
    except Exception:
        return Response(
            {'error': 'VALIDATION_ERROR',
             'detail': f'quarter inválido: {quarter}. Formato esperado: Q01_25'},
            status=400,
        )

    try:
        with connections['ivr'].cursor() as cursor:
            # CA-02: verificar que no haya ejecución activa
            cursor.execute(
                "SELECT COUNT(*) FROM job_execution_log WHERE status='RUNNING'"
            )
            activos = cursor.fetchone()[0]
            if activos > 0:
                return Response(
                    {'error': 'ALREADY_RUNNING',
                     'detail': 'Hay una ejecución activa. Espere a que termine.'},
                    status=409,
                )

            # CA-06: priority=high → SP con parámetro de prioridad (si soportado)
            # El SP actual no recibe priority — se documenta en la respuesta
            cursor.callproc('sp_etl_historico', [year, quarter_num])
            cursor.fetchone()  # descarta resultado del SP

    except (OperationalError, ProgrammingError) as e:
        return Response(
            {'error': 'SERVICE_UNAVAILABLE', 'detail': str(e)},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    # Generar new_run_id (CA-01)
    import uuid as _uuid_mod
    new_run_id = str(_uuid_mod.uuid4())

    # CA-05: registrar idempotencia
    if run_id:
        PipelineRetryIdempotency.mark_retried(run_id, new_run_id)

    # CA-04: AuditEvent PIPELINE_RETRY_REQUESTED
    AuditLogService.emit(
        event_type='PIPELINE_RETRY_REQUESTED',
        actor_user_id=request.user.pk,
        payload={
            'quarter':    quarter,
            'run_id':     run_id,
            'new_run_id': new_run_id,
            'priority':   priority,
            'reason':     reason[:100],  # CNST-026: no PII, truncar
        },
    )

    return Response(
        {
            'new_run_id':     new_run_id,
            'quarter':        quarter,
            'priority':       priority,
            'run_id_origen':  run_id,
            'ejecutado_por':  str(request.user),
        },
        status=status.HTTP_202_ACCEPTED,
    )


# Prerequisito FASE 3 (2026-05-13): asignar required_function canónico a las
# vistas @api_view de UC_PIP_02/03/04. HasFunction los lee vía getattr(view, ...)
# Las verificaciones inline has_function('pipeline.*') fueron eliminadas
# (formato legacy namespace.action).
etl_errors.required_function           = 'PIP-002'  # view_pipeline_errors
etl_data_availability.required_function = 'PIP-003'  # view_data_availability
etl_retry.required_function            = 'PIP-004'  # request_pipeline_retry


@extend_schema(
    summary="IVR MariaDB connection health check",
    description=(
        "Verifies connectivity to MariaDB ivr_legacy. "
        "Returns MariaDB version on success, error detail on failure."
    ),
    responses={
        200: OpenApiResponse(description="MariaDB available — returns version"),
        503: OpenApiResponse(description="MariaDB unavailable"),
    },
    tags=["Estado del Pipeline"]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ivr_health(request):
    """
    GET /api/pipeline/ivr-health/

    Lightweight connectivity check: SELECT VERSION() on connections['ivr'].
    """
    try:
        with connections['ivr'].cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
        return Response({'status': 'ok', 'mariadb_version': version})
    except (OperationalError, ProgrammingError) as e:
        return Response(
            {'status': 'error', 'detail': str(e)},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )


@extend_schema(
    summary="ETL step performance — regresiones vía LAG()",
    description=(
        "Lee v_etl_rendimiento en MariaDB ivr_legacy. "
        "Muestra duracion_seg, duracion_anterior_seg y delta_seg por step. "
        "delta_seg > 0: regresión (tardó más); delta_seg < 0: mejora; "
        "delta_seg = NULL: primera ejecución registrada del step. "
        "Solo incluye ejecuciones con status=SUCCESS."
    ),
    parameters=[
        OpenApiParameter(
            'step_name', str, required=False,
            description=(
                "Filtrar por paso del pipeline: "
                "etl_base_detalle | etl_base_clientes | validacion | maestro"
            ),
        ),
        OpenApiParameter(
            'limit', int, required=False,
            description="Máximo de registros a retornar (default: 50, máx: 200).",
        ),
    ],
    responses={
        200: OpenApiResponse(description="Regresiones de rendimiento por step"),
        503: OpenApiResponse(description="MariaDB no disponible"),
    },
    tags=["Estado del Pipeline"],
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, HasFunction])
def etl_performance(request):
    """
    GET /api/pipeline/performance/

    Lee v_etl_rendimiento — duracion_seg, duracion_anterior_seg y delta_seg
    por step del pipeline ETL. Usa LAG() sobre job_execution_log (status=SUCCESS).
    Permite detectar regresiones de rendimiento entre ejecuciones consecutivas.
    """
    if not (request.user.is_superuser or
            request.user.has_function('pipeline.view_status')):
        return Response(
            {'error': 'Function pipeline.view_status required.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    step_name = request.query_params.get('step_name')
    try:
        limit = min(200, max(1, int(request.query_params.get('limit', 50))))
    except (ValueError, TypeError):
        limit = 50

    conditions = []
    params     = []
    if step_name:
        conditions.append('step_name = %s')
        params.append(step_name)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ''

    sql = f"""
        SELECT job_name, quarter_name, step_name, status,
               start_time, duracion_seg, duracion_anterior_seg, delta_seg
        FROM v_etl_rendimiento
        {where}
        ORDER BY step_name, start_time DESC
        LIMIT %s
    """
    params.append(limit)

    try:
        with connections['ivr'].cursor() as cursor:
            cursor.execute(sql, params)
            cols  = [c[0] for c in cursor.description]
            steps = [dict(zip(cols, row)) for row in cursor.fetchall()]
    except (OperationalError, ProgrammingError) as e:
        return Response(
            {'error': 'Could not connect to MariaDB.', 'detail': str(e)},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    return Response({
        'total':     len(steps),
        'limit':     limit,
        'step_name': step_name,
        'steps':     steps,
    })
