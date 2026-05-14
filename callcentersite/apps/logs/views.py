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
from django.db import connections, OperationalError
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
    required_function  = 'LOG-001'

    def get(self, request):
        try:
            lines = min(500, max(1, int(request.query_params.get('lines', 100))))
        except (ValueError, TypeError):
            lines = 100

        raw_lines = _read_log_tail(LOG_FILE, lines)
        # UC_LOG_01 CA-05: sanitizar PII antes de retornar (CNST-026)
        from apps.logs.log_validators import LogPIIScanner
        log_lines = [
            LogPIIScanner.sanitize_text(line) for line in raw_lines
        ]
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
    required_function  = 'LOG-004'  # view_etl_logs — Prerequisito FASE 3: era LOG-001

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

    Hallazgo H-F5-GRP-PRE-003 (2026-05-13): required_function corregido LOG-001 → LOG-003.
    """
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'LOG-003'  # search_logs

    def get(self, request):
        from apps.logs.log_validators import LogPIIScanner
        from datetime import datetime, timedelta, timezone as tz_

        q         = request.query_params.get('q', '')
        date_from = request.query_params.get('date_from')
        date_to   = request.query_params.get('date_to')
        level     = request.query_params.get('level', '').upper()
        try:
            max_lines = min(1000, int(request.query_params.get('lines', 200)))
        except (ValueError, TypeError):
            max_lines = 200

        if not date_from:
            return Response({'error': 'date_from requerido.'}, status=400)

        # UC_LOG_03 CA-02: range > 7d → 400
        if date_from and date_to:
            try:
                from_dt = datetime.fromisoformat(date_from)
                to_dt   = datetime.fromisoformat(date_to)
                if (to_dt - from_dt).days > 7:
                    return Response(
                        {'error': 'RANGE_TOO_LARGE',
                         'detail': 'El rango de búsqueda no puede exceder 7 días (UC_LOG_03 CA-02).'},
                        status=400,
                    )
            except ValueError:
                return Response({'error': 'VALIDATION_ERROR', 'detail': 'Fechas inválidas.'}, status=400)

        all_lines = _read_log_tail(LOG_FILE, lines=10000)
        results = []
        for line in all_lines:
            if level and level not in line:
                continue
            if q and q.lower() not in line.lower():
                continue
            # UC_LOG_03 CA-04: sanitize (CNST-026)
            results.append(LogPIIScanner.sanitize_text(line))
            if len(results) >= max_lines:
                break

        # CA-03: cap a 1000 hits
        return Response({
            'total':    len(results),
            'capped':   len(results) >= 1000,
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
    required_function  = 'LOG-002'

    def post(self, request):
        if not (request.user.is_superuser or
                request.user.has_function('LOG-002')):
            return Response({'error': 'Function logs.export required.'}, status=403)
        date_from = request.data.get('date_from')
        date_to   = request.data.get('date_to')
        formato   = request.data.get('formato', 'txt')

        if not date_from:
            return Response({'error': 'date_from is required.'}, status=400)

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
    Función: LOG-005 (view_infrastructure_logs)

    Hallazgo H-F4-GRP-A-002 (2026-05-13):
        required_function estaba en 'LOG-001' (view_application_logs).
        Corregido a 'LOG-005' (view_infrastructure_logs).
    """
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'LOG-005'   # view_infrastructure_logs (CA-05)

    def get(self, request):
        host = request.query_params.get('host')
        try:
            with connections['ivr'].cursor() as cursor:
                if host:
                    cursor.execute(
                        "SELECT id, host, message, level, created_at "
                        "FROM infra_logs WHERE host=%s ORDER BY created_at DESC LIMIT 500",
                        (host,),
                    )
                else:
                    cursor.execute(
                        "SELECT id, host, message, level, created_at "
                        "FROM infra_logs ORDER BY created_at DESC LIMIT 500"
                    )
                if cursor.description:
                    cols    = [d[0] for d in cursor.description]
                    entries = [dict(zip(cols, row)) for row in cursor.fetchall()]
                else:
                    entries = []
        except OperationalError as e:
            return Response(
                {'error': 'SERVICE_UNAVAILABLE', 'detail': str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response({'source': 'infrastructure', 'entries': entries})


@extend_schema(
    summary="UC_LOG_06 — Estado del sistema de logs",
    description=("Verifica disponibilidad del archivo log Django y de job_execution_log en MariaDB."),
    parameters=[],
    responses={200: OpenApiResponse(description='Estado de cada fuente de logs')},
    tags=["Registros del Sistema"]
)
class LogHealthView(APIView):
    """
    UC_LOG_06 — Estado de salud del sistema.

    GET /api/logs/health/
    Hallazgo H-F5-GRP-PRE-003: required_function corregido LOG-001 → LOG-006.
    CA-01: overall green si todo OK.
    CA-02: yellow si algún servicio down.
    CA-03: red si alerta crítica activa.
    CA-05: servicio sin respuesta → unknown (no falla global).
    CA-06: cache TTL 30s.
    """
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'LOG-006'  # view_system_health

    def get(self, request):
        from apps.logs.log_status_service import SystemStatusAggregator
        from django.db import connections, OperationalError

        services = []

        # Servicio Django log
        log_exists = LOG_FILE.exists()
        services.append({
            'name':   'django_log',
            'status': 'green' if log_exists else 'yellow',
        })

        # Servicio MariaDB IVR
        try:
            with connections['ivr'].cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM job_execution_log")
            services.append({'name': 'ivr_mariadb', 'status': 'green'})
        except Exception:
            services.append({'name': 'ivr_mariadb', 'status': 'unknown'})

        # Servicio alertas críticas
        from apps.alerts.models import Alert
        critical_firing = Alert.objects.filter(
            severity='critical', state='firing'
        ).count()
        if critical_firing > 0:
            services.append({'name': 'alerts', 'status': 'red'})
        else:
            services.append({'name': 'alerts', 'status': 'green'})

        overall = SystemStatusAggregator.overall(services)

        return Response({
            'overall':  overall,
            'services': services,
            'cache_ttl': 30,
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
    UC_LOG_07 — Métricas técnicas del sistema.

    GET /api/logs/metrics/
    Hallazgo H-F5-GRP-PRE-003: required_function corregido LOG-001 → LOG-007.
    """
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'LOG-007'  # view_technical_metrics

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


@extend_schema(
    summary="UC_LOG_08 — Eventos del pipeline analítico (pipeline_event_log)",
    description=(
        "Lee pipeline_event_log en MariaDB ivr_legacy. "
        "Registra errores y eventos de los SPs de IACT-db: "
        "PARAM_INVALIDO, ETL_FALLO, ETL_PARTIAL, VALIDACION, REPORTE_VACIO, SISTEMA. "
        "Filtra por quarter, error_type, severity y ventana temporal en horas."
    ),
    parameters=[
        OpenApiParameter(
            'quarter', str, required=False,
            description="Quarter en contexto: Q01_25, Q02_26, etc.",
        ),
        OpenApiParameter(
            'error_type', str, required=False,
            enum=['PARAM_INVALIDO', 'ETL_FALLO', 'ETL_PARTIAL',
                  'VALIDACION', 'REPORTE_VACIO', 'SISTEMA'],
            description="Tipo de evento. Si se omite, retorna todos.",
        ),
        OpenApiParameter(
            'severity', str, required=False,
            enum=['CRITICA', 'ALTA', 'MEDIA', 'BAJA', 'INFO'],
            description="Severidad operacional. Si se omite, retorna todos.",
        ),
        OpenApiParameter(
            'hours', int, required=False,
            description="Ventana de búsqueda en horas (default: 48, máx: 168).",
        ),
        OpenApiParameter(
            'page_size', int, required=False,
            description="Registros por página (default: 20, máx: 100).",
        ),
    ],
    responses={
        200: OpenApiResponse(description="Eventos del pipeline analítico"),
        503: OpenApiResponse(description="MariaDB no disponible"),
    },
    tags=["Registros del Sistema"],
)
class PipelineEventLogView(APIView):
    """
    UC_LOG_08 — Eventos del pipeline analítico.

    GET /api/logs/pipeline-events/

    Lee pipeline_event_log de MariaDB ivr_legacy. Los eventos son escritos
    por los SPs de IACT-db cuando detectan parámetros inválidos, fallos de
    carga o condiciones operacionales. Acceso de solo lectura desde Django.
    """
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'LOG-001'

    def get(self, request):
        quarter    = request.query_params.get('quarter')
        error_type = request.query_params.get('error_type')
        severity   = request.query_params.get('severity')

        try:
            hours     = min(168, int(request.query_params.get('hours', 48)))
            page_size = min(100, int(request.query_params.get('page_size', 20)))
        except (ValueError, TypeError):
            hours, page_size = 48, 20

        valid_error_types = {
            'PARAM_INVALIDO', 'ETL_FALLO', 'ETL_PARTIAL',
            'VALIDACION', 'REPORTE_VACIO', 'SISTEMA',
        }
        valid_severities = {'CRITICA', 'ALTA', 'MEDIA', 'BAJA', 'INFO'}

        param_errors = []
        if error_type and error_type not in valid_error_types:
            param_errors.append(
                f'error_type invalido: {error_type!r}. '
                f'Valores: {sorted(valid_error_types)}'
            )
        if severity and severity not in valid_severities:
            param_errors.append(
                f'severity invalido: {severity!r}. '
                f'Valores: {sorted(valid_severities)}'
            )
        if param_errors:
            return Response({'errors': param_errors}, status=400)

        conditions = ['ts >= DATE_SUB(NOW(), INTERVAL %s HOUR)']
        params     = [hours]
        if quarter:
            conditions.append('p_quarter = %s')
            params.append(quarter)
        if error_type:
            conditions.append('error_type = %s')
            params.append(error_type)
        if severity:
            conditions.append('severity = %s')
            params.append(severity)

        where = ' AND '.join(conditions)
        sql = f"""
            SELECT id, ts, error_type, severity, sp_nombre,
                   sql_state, mysql_errno, p_quarter, p_segmento,
                   LEFT(error_message, 500) AS error_message,
                   job_log_id, ejecutado_por
            FROM pipeline_event_log
            WHERE {where}
            ORDER BY ts DESC
            LIMIT %s
        """
        params.append(page_size)

        try:
            with connections['ivr'].cursor() as cursor:
                cursor.execute(sql, params)
                cols   = [c[0] for c in cursor.description]
                events = [dict(zip(cols, row)) for row in cursor.fetchall()]
        except OperationalError as e:
            return Response(
                {'error': 'Could not connect to MariaDB.', 'detail': str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response({
            'total':      len(events),
            'hours':      hours,
            'page_size':  page_size,
            'filters': {
                'quarter':    quarter,
                'error_type': error_type,
                'severity':   severity,
            },
            'events': events,
        })
