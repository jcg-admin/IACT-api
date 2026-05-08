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

from django.db import connections, OperationalError
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
    with connections['ivr'].cursor() as cursor:
        cursor.execute(sql, [limit])
        cols = [c[0] for c in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]


def _build_resumen_salud(runs: list[dict]) -> dict:
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
    if not (request.user.is_superuser or
            request.user.has_function('pipeline.view_status')):
        return Response(
            {'error': 'Function pipeline.view_status required.'},
            status=status.HTTP_403_FORBIDDEN)

    try:
        runs = _get_pipeline_runs(limit=20)
    except OperationalError as e:
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

    resumen = _build_resumen_salud(runs)

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
    """
    if not (request.user.is_superuser or
            request.user.has_function('pipeline.view_errors')):
        return Response(
            {'error': 'Function pipeline.view_errors required.'},
            status=status.HTTP_403_FORBIDDEN)

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
    except OperationalError as e:
        return Response({'error': 'Could not connect to MariaDB.', 'detail': str(e)},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE)

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
    """
    if not (request.user.is_superuser or
            request.user.has_function('pipeline.view_data_availability')):
        return Response(
            {'error': 'Function pipeline.view_data_availability required.'},
            status=status.HTTP_403_FORBIDDEN)

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
    except OperationalError as e:
        return Response({'error': 'Could not connect to MariaDB.', 'detail': str(e)},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE)

    if not row:
        return Response({
            'trimestre':             trimestre,
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
    summary="UC_PIP_04 — Solicitar reintento del pipeline",
    description=(
        "Llama sp_etl_historico(year, quarter_num) en MariaDB. "
        "Requiere que no haya ejecucion RUNNING activa. "
        "El motivo debe tener al menos 20 caracteres."
    ),
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "quarter": {"type": "string", "example": "Q01_25"},
                "motivo":    {"type": "string", "minLength": 20},
            },
            "required": ["quarter", "motivo"],
        }
    },
    responses={
        202: OpenApiResponse(description="Reintento iniciado"),
        400: OpenApiResponse(description="Parametros invalidos o motivo muy corto"),
        409: OpenApiResponse(description="Hay una ejecucion activa en curso"),
        503: OpenApiResponse(description="MariaDB no disponible"),
    },
    tags=["Estado del Pipeline"]
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, HasFunction])
def etl_retry(request):
    """
    UC_PIP_04 — Solicitar reintento del pipeline para un quarter.

    POST /api/pipeline/retry/
    Body: { "quarter": "Q01_25", "motivo": "Failure reason at least 20 chars..." }

    Verifica que no haya ejecucion activa, luego llama sp_etl_historico
    directamente en MariaDB.
    Requerimiento: motivo >= 20 caracteres.
    """
    quarter = request.data.get('quarter')
    motivo    = request.data.get('motivo', '')

    if not quarter:
        return Response({'error': 'quarter is required.'}, status=400)
    if len(motivo) < 20:
        return Response({'error': 'motivo debe tener al menos 20 caracteres.'}, status=400)

    # Parsear trimestre: Q01_25 -> year=2025, quarter_num=1
    try:
        parts       = quarter.upper().split('_')   # ['Q01', '25']
        quarter_num = int(parts[0][1:])              # 1
        year        = 2000 + int(parts[1])           # 2025
        assert 1 <= quarter_num <= 4
        assert 2020 <= year <= 2030
    except Exception:
        return Response(
            {'error': f'Invalid quarter: {quarter}. Formato esperado: Q01_25'},
            status=400
        )

    try:
        with connections['ivr'].cursor() as cursor:
            # Verificar que no haya ejecucion activa
            cursor.execute(
                "SELECT COUNT(*) FROM job_execution_log WHERE status='RUNNING'"
            )
            activos = cursor.fetchone()[0]
            if activos > 0:
                return Response(
                    {'error': 'An execution is already running. Wait for it to finish before retrying.'},
                    status=409
                )

            # Ejecutar sp_etl_historico
            cursor.callproc('sp_etl_historico', [year, quarter_num])
            result = cursor.fetchone()

    except OperationalError as e:
        return Response({'error': 'Could not connect to MariaDB.', 'detail': str(e)},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE)

    return Response({
        'detail':    f'Retry initiated for {quarter}.',
        'quarter': quarter,
        'motivo':    motivo,
        'resultado': list(result) if result else None,
        'ejecutado_por': str(request.user),
    }, status=status.HTTP_202_ACCEPTED)
