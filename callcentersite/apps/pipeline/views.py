"""
Views para app pipeline.

UC_PIP_01: Supervision del estado del ETL IVR.
  Lee directamente de job_execution_log y etl_runs en MariaDB (ivr_legacy)
  via connections['ivr'].cursor() segun especifica el UC.

  El modelo PipelineExecution del UC mapea a job_execution_log:
    id             → id
    source_table   → tabla_origen
    trimestre      → quarter_name
    started_at     → start_time
    finished_at    → end_time
    estado         → status  (SUCCESS/FAILED/RUNNING/SKIP)
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
from rest_framework.response import Response
from rest_framework import status


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
    ventana_14h = now - timedelta(hours=14)
    ventana_24h = now - timedelta(hours=24)

    ejecucion_en_curso   = None
    ultima_exitosa       = None
    ultima_fallida       = None
    total_exitosas_24h   = 0
    total_fallidas_24h   = 0

    for run in runs:
        end = run['end_time']
        # Normalizar a UTC si no tiene timezone
        if end and hasattr(end, 'tzinfo') and end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        start = run['start_time']
        if start and hasattr(start, 'tzinfo') and start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)

        s = run['status']

        if s == 'RUNNING' and ejecucion_en_curso is None:
            ejecucion_en_curso = run

        if s == 'SUCCESS':
            if ultima_exitosa is None:
                ultima_exitosa = run
            if end and end >= ventana_24h:
                total_exitosas_24h += 1

        if s == 'FAILED':
            if ultima_fallida is None:
                ultima_fallida = run
            if end and end >= ventana_24h:
                total_fallidas_24h += 1

    # Calcular estado general
    if ultima_exitosa:
        end_exitosa = ultima_exitosa['end_time']
        if end_exitosa and hasattr(end_exitosa, 'tzinfo') and end_exitosa.tzinfo is None:
            end_exitosa = end_exitosa.replace(tzinfo=timezone.utc)

        if end_exitosa and end_exitosa >= ventana_14h:
            estado_general = 'ok'
        elif end_exitosa and end_exitosa >= ventana_24h:
            estado_general = 'degradado'
        else:
            estado_general = 'critico'
    else:
        estado_general = 'critico'

    if ultima_fallida and ultima_exitosa is None:
        estado_general = 'critico'

    return {
        'estado_general':           estado_general,
        'ejecucion_en_curso':       ultima_exitosa if ejecucion_en_curso else None,
        'ultima_ejecucion_exitosa': ultima_exitosa,
        'ultima_ejecucion_fallida': ultima_fallida,
        'total_exitosas_24h':       total_exitosas_24h,
        'total_fallidas_24h':       total_fallidas_24h,
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
        'estado':            run['status'],
        'base_records':      run['records_procesados'],
        'duracion_seg':      run['duracion_seg'],
        'error_message':     run['error_message'],
        'executed_by':       run['ejecutado_por'],
    }


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def etl_status(request):
    """
    UC_PIP_01 — Supervision del estado del ETL IVR.

    GET /api/pipeline/status/

    Response:
    {
        "resumen": {
            "estado_general": "ok" | "degradado" | "critico",
            "ejecucion_en_curso": {...} | null,
            "ultima_ejecucion_exitosa": {...} | null,
            "ultima_ejecucion_fallida": {...} | null,
            "total_exitosas_24h": int,
            "total_fallidas_24h": int
        },
        "ultimas_ejecuciones": [...]
    }

    Fuente: job_execution_log en MariaDB ivr_legacy via connections['ivr'].
    """
    try:
        runs = _get_pipeline_runs(limit=20)
    except OperationalError as e:
        return Response(
            {'error': 'No se pudo conectar a la base de datos IVR.',
             'detail': str(e)},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    if not runs:
        return Response({
            'resumen': {
                'estado_general':           'critico',
                'ejecucion_en_curso':       None,
                'ultima_ejecucion_exitosa': None,
                'ultima_ejecucion_fallida': None,
                'total_exitosas_24h':       0,
                'total_fallidas_24h':       0,
            },
            'ultimas_ejecuciones': [],
            'message': 'No hay ejecuciones ETL registradas.'
        })

    resumen = _build_resumen_salud(runs)

    return Response({
        'resumen': {
            'estado_general':           resumen['estado_general'],
            'ejecucion_en_curso':       _format_run(resumen['ejecucion_en_curso']),
            'ultima_ejecucion_exitosa': _format_run(resumen['ultima_ejecucion_exitosa']),
            'ultima_ejecucion_fallida': _format_run(resumen['ultima_ejecucion_fallida']),
            'total_exitosas_24h':       resumen['total_exitosas_24h'],
            'total_fallidas_24h':       resumen['total_fallidas_24h'],
        },
        'ultimas_ejecuciones': [_format_run(r) for r in runs],
    })
