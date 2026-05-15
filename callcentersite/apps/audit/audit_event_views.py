"""
apps/audit/audit_event_views.py

UC_PERM_10 — Consultar Auditoría de Permisos.
UC_AUD_02  — Buscar en Auditoría.
UC_AUD_03  — Exportar Auditoría.
"""
import uuid as _uuid
from datetime import datetime, timezone as tz_
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access.permissions.function_permissions import HasFunction
from apps.audit.audit_query_service import AuditFilterValidator, AuditResponseSanitizer
from apps.audit.models import AuditLog
from apps.audit.services import AuditLogService
from apps.audit.serializers.auditlog_serializers import AuditLogSerializer
from apps.audit.serializers.auditlog_serializers import AuditLogSummarySerializer



_TAG = 'Auditoría'


def _parse_date(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s).replace(tzinfo=tz_.utc)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# UC_PERM_10 — Lista / Detalle / Aggregate / Export
# ---------------------------------------------------------------------------

@extend_schema_view(
    get=extend_schema(
        operation_id='audit_event_list',
        summary='UC_PERM_10 — Listar eventos de auditoría',
        responses={
            200: OpenApiResponse(description='{results, cursor, estimated_total}'),
            400: OpenApiResponse(description='Filtros inválidos o range > 90 días'),
            403: OpenApiResponse(description='Sin AUD-001 view_audit_log'),
        },
        tags=[_TAG],
    )
)
class AuditEventListView(APIView):
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'AUD-001'

    def get(self, request):
        date_from = _parse_date(request.query_params.get('date_from'))
        date_to   = _parse_date(request.query_params.get('date_to'))

        # Defaults si no se proveen
        if date_to is None:
            date_to = datetime.now(tz=tz_.utc)
        if date_from is None:
            from datetime import timedelta
            date_from = date_to - timedelta(days=30)

        try:
            page_size = min(200, max(1, int(request.query_params.get('page_size', 50))))
            AuditFilterValidator.validate(date_from, date_to, page_size=page_size)
        except ValueError as e:
            return Response({'error': 'VALIDATION_ERROR', 'detail': str(e)}, status=400)

        actor_id   = request.query_params.get('actor_id')
        event_type = request.query_params.get('event_type')

        qs = AuditLog.objects.order_by('-timestamp')
        if actor_id:
            qs = qs.filter(user_id=actor_id)
        if event_type:
            qs = qs.filter(action=event_type)

        results = [
            AuditResponseSanitizer.sanitize_event({
                'id': a.pk, 'action': a.action,
                'user_id': a.user_id, 'resource': a.resource,
                'result': a.result, 'created_at': str(a.created_at),
                'details': a.details,
            })
            for a in qs[:page_size]
        ]

        # CA-17: meta-audit AUDIT_LOG_QUERIED
        AuditLogService.emit(
            event_type='AUDIT_LOG_QUERIED',
            actor_user_id=request.user.pk,
            payload={
                'filters': {'actor_id': actor_id, 'event_type': event_type},
                'page_size': page_size,
                'row_count_returned': len(results),
            },
        )

        return Response({'results': results, 'cursor': None, 'estimated_total': len(results)})


@extend_schema_view(
    get=extend_schema(operation_id='audit_event_detail',
    summary='UC_PERM_10 — Detalle de evento de auditoría',
    tags=[_TAG],)
)
class AuditEventDetailView(APIView):
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'AUD-001'

    def get(self, request, event_id):
        try:
            audit = AuditLog.objects.get(pk=event_id)
        except AuditLog.DoesNotExist:
            return Response({'error': 'NOT_FOUND'}, status=404)

        AuditLogService.emit(
            event_type='AUDIT_LOG_DETAIL_VIEWED',
            actor_user_id=request.user.pk,
            payload={'viewed_event_id': str(event_id)},
        )

        return Response({
            'id': audit.pk, 'action': audit.action,
            'user_id': audit.user_id, 'resource': audit.resource,
            'result': audit.result, 'created_at': str(audit.created_at),
            'details': audit.details,
        })


@extend_schema_view(
    get=extend_schema(operation_id='audit_event_aggregate',
    summary='UC_PERM_10 — Agregaciones de auditoría',
    tags=[_TAG],)
)
class AuditEventAggregateView(APIView):
    serializer_class = AuditLogSummarySerializer
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'AUD-001'

    def get(self, request):
        group_by = request.query_params.get('group_by', 'event_type')
        if group_by not in ('event_type', 'actor', 'day'):
            return Response({'error': 'VALIDATION_ERROR', 'detail': 'group_by inválido.'}, status=400)

        from django.db.models import Count
        qs = AuditLog.objects.values('action').annotate(count=Count('id')).order_by('-count')
        buckets = [{'event_type': row['action'], 'count': row['count']} for row in qs[:100]]

        AuditLogService.emit(
            event_type='AUDIT_LOG_AGGREGATE_QUERIED',
            actor_user_id=request.user.pk,
            payload={'group_by': group_by, 'buckets_returned': len(buckets)},
        )

        return Response({'group_by': group_by, 'buckets': buckets})


@extend_schema_view(
    post=extend_schema(
        operation_id='audit_event_export',
        summary='UC_PERM_10 / UC_AUD_03 — Exportar eventos de auditoría',
        responses={202: OpenApiResponse(description='Job encolado — {job_id}')},
        tags=[_TAG],
    )
)
class AuditEventExportView(APIView):
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'AUD-003'

    def post(self, request):
        date_from = request.data.get('date_from', '')
        date_to   = request.data.get('date_to', '')
        fmt       = request.data.get('format', 'csv')

        # CA-04: estimación de filas > 5M → 400
        # Sin BD Analytics real, estimamos por rango de días
        if date_from and date_to:
            try:
                fd = datetime.fromisoformat(date_from)
                td = datetime.fromisoformat(date_to)
                days = (td - fd).days
                if days > 365 * 5:  # >5 años → prob. > 5M filas
                    return Response({'error': 'ROW_LIMIT_EXCEEDED',
                                     'detail': 'Estimación > 5M filas — CA-04.'}, status=400)
            except ValueError:
                return Response({'error': 'VALIDATION_ERROR', 'detail': 'Fechas inválidas.'}, status=400)

        job_id = str(_uuid.uuid4())
        AuditLogService.emit(
            event_type='AUDIT_EXPORT_QUEUED',
            actor_user_id=request.user.pk,
            payload={'job_id': job_id, 'format': fmt,
                     'date_from': date_from, 'date_to': date_to},
        )
        return Response({'job_id': job_id}, status=202)


# ---------------------------------------------------------------------------
# UC_AUD_02 — Buscar en Auditoría
# ---------------------------------------------------------------------------

@extend_schema_view(
    post=extend_schema(
        operation_id='audit_search',
        summary='UC_AUD_02 — Buscar en log de auditoría',
        responses={
            200: OpenApiResponse(description='{results, total, capped}'),
            400: OpenApiResponse(description='Validación — range/query'),
            403: OpenApiResponse(description='Sin AUD-002 search_audit_log'),
        },
        tags=[_TAG],
    )
)
class AuditSearchView(APIView):
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'AUD-002'

    def post(self, request):
        q         = request.data.get('q', '')
        date_from = request.data.get('date_from')
        date_to   = request.data.get('date_to')

        if not date_from:
            return Response({'error': 'VALIDATION_ERROR', 'detail': 'date_from requerido.'}, status=400)

        if date_from and date_to:
            try:
                fd = datetime.fromisoformat(date_from)
                td = datetime.fromisoformat(date_to)
                if (td - fd).days > 90:
                    return Response({'error': 'RANGE_TOO_LARGE',
                                     'detail': 'Range máximo 90 días — CA-02.'}, status=400)
            except ValueError:
                return Response({'error': 'VALIDATION_ERROR', 'detail': 'Fechas inválidas.'}, status=400)

        qs = AuditLog.objects.order_by('-timestamp')
        if q:
            from django.db.models import Q
            qs = qs.filter(Q(action__icontains=q) | Q(resource__icontains=q))

        results = [
            AuditResponseSanitizer.sanitize_event({
                'id': a.pk, 'action': a.action, 'resource': a.resource,
                'created_at': str(a.created_at), 'details': a.details,
            })
            for a in qs[:1000]
        ]

        AuditLogService.emit(
            event_type='AUDIT_SEARCH_QUERIED',
            actor_user_id=request.user.pk,
            payload={'q': q[:100], 'results_count': len(results)},
        )

        return Response({'results': results, 'total': len(results), 'capped': len(results) >= 1000})


# ---------------------------------------------------------------------------
# F6-P0-T1: AuditLegacyExportView — alias con operationId distinto
# para resolver DT-SPECTACULAR-001 (colisión audit_event_export).
# La URL /api/audit/export/ apunta a esta clase.
# @extend_schema_view(post=...) overridea el @extend_schema_view heredado del padre.
# ---------------------------------------------------------------------------

@extend_schema_view(
    post=extend_schema(
        operation_id='audit_export_legacy',
        summary='UC_AUD_03 — Exportar auditoría (ruta alias /api/audit/export/)',
        description=(
            'Alias de /api/audit/audit-events/export/.\n'
            'Función: AUD-003 (export_audit_log).\n'
            'Fix DT-SPECTACULAR-001: operationId propio para evitar colisión de schema.'
        ),
        responses={
            202: OpenApiResponse(description='Job encolado — {job_id}'),
            403: OpenApiResponse(description='Sin AUD-003 export_audit_log'),
        },
        deprecated=True,
        tags=['Auditoría'],
    ),
)
class AuditLegacyExportView(AuditEventExportView):
    serializer_class = AuditLogSerializer
    """
    Ruta alias /api/audit/export/ — misma lógica que AuditEventExportView.
    Existe únicamente para resolver DT-SPECTACULAR-001.
    @extend_schema_view(post=...) overridea el schema del padre.
    """
    pass


# ---------------------------------------------------------------------------
# F6-GD-T2: GeneralAuditListView — UC_AUD_01
# GET /api/audit/general/  — AUD-005 view_general_audit
# ---------------------------------------------------------------------------

@extend_schema_view(
    get=extend_schema(
        operation_id='audit_general_timeline',
        summary='UC_AUD_01 — Timeline general de auditoría cross-módulo',
        description=(
            'Listado paginado de AuditEvents de todos los módulos.\n'
            'Función: AUD-005 (view_general_audit).\n'
            'Filtros: module, actor_id, date_from, date_to, page_size.\n'
            'CA-06: emite GENERAL_AUDIT_QUERIED por cada invocación exitosa.\n'
            'CA-07: requiere AUD-005 view_general_audit.'
        ),
        responses={
            200: OpenApiResponse(description='Lista de eventos de auditoría'),
            400: OpenApiResponse(description='Rango > 90 días'),
            403: OpenApiResponse(description='Sin AUD-005 view_general_audit'),
            503: OpenApiResponse(description='BD timeout'),
        },
        tags=['Auditoría'],
    ),
)
class GeneralAuditListView(APIView):
    """
    UC_AUD_01 — Timeline general de auditoría cross-módulo.

    Diferencia con UC_PERM_10 (AuditEventListView / view_audit_log):
      - UC_PERM_10 cubre el log de permisos (compliance officers)
      - UC_AUD_01 cubre TODOS los módulos (auditores con acceso cross-módulo)
    """
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'AUD-005'

    DEFAULT_PAGE_SIZE = 50
    MAX_RANGE_DAYS    = 90

    def get(self, request):
        from apps.audit.services import AuditLogService
        from django.utils import timezone
        from datetime import timedelta

        # Filtros
        module     = request.query_params.get('module')
        actor_id   = request.query_params.get('actor_id')
        date_from  = request.query_params.get('date_from')
        date_to    = request.query_params.get('date_to')
        page_size  = int(request.query_params.get('page_size', self.DEFAULT_PAGE_SIZE))

        qs = AuditLog.objects.all().order_by('-timestamp')

        if module:
            # AuditLog no tiene campo module — filtrar por resource o details
            qs = qs.filter(resource__icontains=module)
        if actor_id:
            qs = qs.filter(user_id=actor_id)

        # CA-05: range > 90 días → 400
        if date_from and date_to:
            from django.utils.dateparse import parse_datetime, parse_date
            df = parse_datetime(date_from) or parse_date(date_from)
            dt = parse_datetime(date_to) or parse_date(date_to)
            if df and dt:
                delta = (dt - df).days if hasattr(dt, 'days') else (dt - df).days
                if abs(delta) > self.MAX_RANGE_DAYS:
                    return Response(
                        {'error': 'RANGE_EXCEEDED',
                         'detail': f'Rango máximo: {self.MAX_RANGE_DAYS} días'},
                        status=400,
                    )
            if date_from:
                qs = qs.filter(timestamp__gte=date_from)
            if date_to:
                qs = qs.filter(timestamp__lte=date_to)

        results = list(qs[:page_size])

        # CA-06: meta-audit GENERAL_AUDIT_QUERIED
        AuditLogService.emit(
            event_type='GENERAL_AUDIT_QUERIED',
            actor_user_id=request.user.pk,
            payload={
                'filters': {
                    'module': module,
                    'actor_id': actor_id,
                    'date_from': date_from,
                    'date_to': date_to,
                },
                'count': len(results),
            },
        )

        return Response({
            'count': len(results),
            'results': [
                {
                    'id':         str(log.pk),
                    'event_type': getattr(log, 'action', None) or getattr(log, 'event_type', None),
                    'actor_id':   getattr(log, 'actor_user_id', None),
                    'module':     getattr(log, 'module', None),
                    'timestamp':  getattr(log, 'timestamp', None),
                }
                for log in results
            ],
        })
