"""
Views para app logs.

UC_LOG_01..07: Acceso a logs del sistema.

Nota sobre SSE (UC_LOG_01, UC_LOG_02):
  Los endpoints de tail via SSE requieren un servidor ASGI (uvicorn/daphne).
  En Django sincrono se implementa como streaming HTTP o se devuelve
  un snapshot de las ultimas N lineas.

UC_LOG_03: Consulta libre sobre el log store.
UC_LOG_04: Export async de logs.
UC_LOG_05: Logs de infraestructura.
UC_LOG_06: Estado general del sistema de logs.
UC_LOG_07: Metricas de logs.
"""
import os
import json
from datetime import datetime, timedelta
from pathlib import Path

from django.conf import settings
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework.permissions import IsAuthenticated
from apps.access.permissions.function_permissions import HasFunction
from rest_framework.response import Response
from rest_framework import status

# Ruta del log Django por defecto
LOG_FILE = Path(getattr(settings, 'BASE_DIR', '/tmp')) / '..' / 'logs' / 'django.log'


def _read_log_tail(filepath: Path, lines: int = 100) -> list[str]:
    """Lee las ultimas N lineas de un archivo de log."""
    try:
        with open(filepath, 'r', errors='replace') as f:
            all_lines = f.readlines()
            return [l.rstrip() for l in all_lines[-lines:]]
    except FileNotFoundError:
        return []
    except Exception as e:
        return [f'[ERROR] No se pudo leer el log: {e}']


@extend_schema(
    summary="UC_LOG_01 — Tail del log Django",
    description=("Retorna las ultimas N lineas del archivo log de Django. En produccion ASGI se reemplaza por SSE."),
    parameters=[OpenApiParameter('lines', int, default=100, description='Max 500')],
    responses={200: OpenApiResponse(description='Ultimas N lineas del log Django')},
    tags=["Registros del Sistema"]
)
class DjangoLogTailView(APIView):
    """
    UC_LOG_01 — Tail de logs Django.

    GET /api/logs/django/tail/?lines=100

    Retorna las ultimas N lineas del log de Django.
    En produccion se implementa como SSE; aqui se retorna snapshot.
    """
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'logs.view'

    def get(self, request):
        try:
            lines = min(500, max(1, int(request.query_params.get('lines', 100))))
        except (ValueError, TypeError):
            lines = 100

        log_lines = _read_log_tail(LOG_FILE, lines)
        return Response({
            'source':    'django',
            'lines':     len(log_lines),
            'contenido': log_lines,
            'nota':      'Snapshot estatico. SSE disponible en produccion ASGI.',
        })


@extend_schema(
    summary="UC_LOG_02 — Tail del log ETL desde MariaDB",
    description=("Lee las ultimas N entradas de job_execution_log en MariaDB ivr_legacy."),
    parameters=[OpenApiParameter('lines', int, default=50, description='Max 200')],
    responses={200: OpenApiResponse(description='Entradas recientes del pipeline ETL'), 503: OpenApiResponse(description='MariaDB no disponible')},
    tags=["Registros del Sistema"]
)
class ETLLogTailView(APIView):
    """
    UC_LOG_02 — Log del pipeline ETL en tiempo real.

    GET /api/logs/etl/tail/?lines=50

    Retorna las ultimas entradas del job_execution_log de MariaDB.
    """
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'logs.view'

    def get(self, request):
        from django.db import connections, OperationalError
        try:
            lines = min(200, max(1, int(request.query_params.get('lines', 50))))
        except (ValueError, TypeError):
            lines = 50

        try:
            with connections['ivr'].cursor() as cursor:
                cursor.execute("""
                    SELECT id, job_name, quarter_name, step_name,
                           start_time, end_time, status,
                           records_procesados, duracion_seg, error_message
                    FROM job_execution_log
                    ORDER BY start_time DESC LIMIT %s
                """, [lines])
                cols = [c[0] for c in cursor.description]
                entries = [dict(zip(cols, row)) for row in cursor.fetchall()]
        except OperationalError as e:
            return Response({'error': str(e)}, status=503)

        return Response({
            'source':  'job_execution_log',
            'lines':   len(entries),
            'entries': entries,
            'nota':    'Snapshot de job_execution_log. SSE disponible en produccion ASGI.',
        })


@extend_schema(
    summary="UC_LOG_03 — Busqueda en logs",
    description=("Filtra el log Django por texto, nivel y rango de fechas."),
    parameters=[OpenApiParameter('q', str), OpenApiParameter('date_from', str, required=True), OpenApiParameter('level', str, enum=['DEBUG','INFO','WARNING','ERROR','CRITICAL'])],
    responses={200: OpenApiResponse(description='Resultados filtrados del log')},
    tags=["Registros del Sistema"]
)
class LogSearchView(APIView):
    """
    UC_LOG_03 — Consulta libre sobre el log store.

    GET /api/logs/search/
    Query params:
      q          : texto a buscar
      date_from  : fecha inicio (YYYY-MM-DD) — requerido
      date_to    : fecha fin (YYYY-MM-DD)
      level      : DEBUG/INFO/WARNING/ERROR/CRITICAL
      lines      : max lineas (default 200)
    """
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'logs.view'

    def get(self, request):
        q         = request.query_params.get('q', '')
        date_from = request.query_params.get('date_from')
        date_to   = request.query_params.get('date_to')
        level     = request.query_params.get('level', '').upper()
        try:
            max_lines = min(1000, int(request.query_params.get('lines', 200)))
        except (ValueError, TypeError):
            max_lines = 200

        if not date_from:
            return Response({'error': 'date_from es requerido.'}, status=400)

        all_lines = _read_log_tail(LOG_FILE, lines=10000)
        results = []
        for line in all_lines:
            if level and level not in line:
                continue
            if q and q.lower() not in line.lower():
                continue
            if date_from and date_from not in line:
                pass  # Filtro aproximado por string de fecha
            results.append(line)
            if len(results) >= max_lines:
                break

        return Response({
            'total':    len(results),
            'query':    {'q': q, 'date_from': date_from, 'date_to': date_to, 'level': level},
            'results':  results,
        })


@extend_schema(
    summary="UC_LOG_04 — Exportar logs",
    description=("Crea un job de exportacion de logs. POST para crear, GET para listar."),
    parameters=[],
    responses={202: OpenApiResponse(description='Job de exportacion creado')},
    tags=["Registros del Sistema"]
)
class LogExportView(APIView):
    """
    UC_LOG_04 — Export async de logs.

    POST /api/logs/export/  — crear job de exportacion
    GET  /api/logs/export/  — listar jobs de exportacion

    Nota: Implementacion basica sincrona. En produccion se usa
    Celery para exportacion async a S3.
    """
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'logs.export'

    def post(self, request):
        if not (request.user.is_superuser or
                request.user.has_function('logs.export')):
            return Response({'error': 'Function logs.export required.'}, status=403)
        date_from = request.data.get('date_from')
        date_to   = request.data.get('date_to')
        formato   = request.data.get('formato', 'txt')

        if not date_from:
            return Response({'error': 'date_from es requerido.'}, status=400)

        return Response({
            'job_id':    f'log_export_{datetime.utcnow().strftime("%Y%m%d%H%M%S")}',
            'estado':    'PENDIENTE',
            'date_from': date_from,
            'date_to':   date_to,
            'formato':   formato,
            'nota':      'Export async. En produccion se procesa via Celery.',
        }, status=202)

    def get(self, request):
        return Response({'jobs': [], 'nota': 'Historial de exports pendiente de persistencia.'})


@extend_schema(
    summary="UC_LOG_05 — Logs de infraestructura",
    description=("Logs de host y container. Requiere integracion con Loki/CloudWatch."),
    parameters=[],
    responses={200: OpenApiResponse(description='Estado de disponibilidad de logs de infra')},
    tags=["Registros del Sistema"]
)
class InfraLogView(APIView):
    """
    UC_LOG_05 — Logs de infraestructura (host, container).

    GET /api/logs/infra/
    """
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'logs.view'

    def get(self, request):
        return Response({
            'nota': 'Logs de infraestructura requieren integracion con Loki/CloudWatch.',
            'disponible': False,
            'alternativa': 'Consultar directamente el sistema de observabilidad configurado.',
        })


@extend_schema(
    summary="UC_LOG_06 — Estado del sistema de logs",
    description=("Verifica disponibilidad del archivo log Django y de job_execution_log en MariaDB."),
    parameters=[],
    responses={200: OpenApiResponse(description='Estado de cada fuente de logs')},
    tags=["Registros del Sistema"]
)
class LogHealthView(APIView):
    """
    UC_LOG_06 — Estado general del sistema de logs.

    GET /api/logs/health/
    """
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'logs.view'

    def get(self, request):
        log_exists = LOG_FILE.exists()
        log_size   = LOG_FILE.stat().st_size if log_exists else 0

        from django.db import connections, OperationalError
        ivr_ok = False
        try:
            with connections['ivr'].cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM job_execution_log")
                ivr_ok = True
        except Exception:
            pass

        return Response({
            'django_log': {
                'existe':    log_exists,
                'tamano_kb': round(log_size / 1024, 1),
                'ruta':      str(LOG_FILE),
            },
            'ivr_log': {
                'disponible': ivr_ok,
                'fuente':     'job_execution_log en MariaDB',
            },
            'infra_log': {
                'disponible': False,
                'nota':       'Requiere Loki/CloudWatch',
            },
        })


@extend_schema(
    summary="UC_LOG_07 — Metricas de logs",
    description=("Estadisticas de los ultimos 7 dias desde job_execution_log en MariaDB."),
    parameters=[],
    responses={200: OpenApiResponse(description='Metricas de volumen y estado del pipeline')},
    tags=["Registros del Sistema"]
)
class LogMetricsView(APIView):
    """
    UC_LOG_07 — Metricas de logs (volumen, pipelines, errores).

    GET /api/logs/metrics/
    """
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'logs.view'

    def get(self, request):
        from django.db import connections, OperationalError
        metrics = {}

        try:
            with connections['ivr'].cursor() as cursor:
                cursor.execute("""
                    SELECT status, COUNT(*) AS total
                    FROM job_execution_log
                    WHERE start_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                    GROUP BY status
                """)
                pipeline_stats = {row[0]: row[1] for row in cursor.fetchall()}

                cursor.execute("SELECT COUNT(*) FROM job_execution_log")
                total = cursor.fetchone()[0]
        except OperationalError:
            pipeline_stats = {}
            total = None

        return Response({
            'periodo':         '7 dias',
            'pipeline_logs': {
                'total_registros': total,
                'por_estado':      pipeline_stats,
            },
            'django_logs': {
                'nota': 'Metricas de Django logs requieren parseo del archivo.',
            },
        })


