"""
apps/audit/access_audit_views.py

UC_ACC_09 — Auditar Cambios de Acceso.
GET /api/access/audit/
GET /api/access/audit/{event_id}/
GET /api/access/audit/aggregations/
"""
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access.permissions.function_permissions import HasFunction
from apps.audit.access_audit_service import AccessScopeFilter, AccessFilterValidator
from apps.audit.audit_query_service import AuditResponseSanitizer
from apps.audit.models import AuditLog
from apps.audit.services import AuditLogService

_TAG = 'Auditoría de Acceso'


@extend_schema_view(
    get=extend_schema(
        operation_id='access_audit_list',
        summary='UC_ACC_09 — Listar eventos de cambios de acceso',
        responses={
            200: OpenApiResponse(description='{results, count} — solo MOD_Access events'),
            400: OpenApiResponse(description='BAD_FILTER — ordering inválido'),
            403: OpenApiResponse(description='Sin ACC-012 view_access_audit'),
        },
        tags=[_TAG],
    )
)
class AccessAuditListView(APIView):
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'ACC-013'

    def get(self, request):
        ordering    = request.query_params.get('ordering', '-occurred_at')
        target_uid  = request.query_params.get('target_user_id')
        includes_fn = request.query_params.get('includes_function_id')

        # CA-07: anti-SQLi en ordering
        try:
            AccessFilterValidator.validate_ordering(ordering)
        except ValueError as e:
            return Response({'error': 'BAD_FILTER', 'detail': str(e)}, status=400)

        qs = AccessScopeFilter.queryset(AuditLog.objects.all()).order_by('-created_at')

        if target_uid:
            from django.db.models import Q
            qs = qs.filter(Q(resource__icontains=target_uid) | Q(user_id=target_uid))

        if includes_fn:
            qs = qs.filter(details__function_ids__contains=[int(includes_fn)])

        results = [
            AuditResponseSanitizer.sanitize_event({
                'id': a.pk, 'action': a.action,
                'user_id': a.user_id, 'resource': a.resource,
                'result': a.result, 'created_at': str(a.created_at),
                'details': a.details,
            })
            for a in qs[:200]
        ]

        # CA-03: audit selectivo — solo si se filtra por target_user_id
        if target_uid:
            AuditLogService.emit(
                event_type='ACCESS_AUDIT_VIEWED',
                actor_user_id=request.user.pk,
                payload={'target_user_id': int(target_uid), 'results_count': len(results)},
            )

        return Response({'count': len(results), 'results': results})


@extend_schema(
    operation_id='access_audit_detail',
    summary='UC_ACC_09 — Detalle de evento de acceso (solo scope ACCESS)',
    tags=[_TAG],
)
class AccessAuditDetailView(APIView):
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'ACC-013'

    def get(self, request, event_id):
        try:
            audit = AuditLog.objects.get(pk=event_id)
        except AuditLog.DoesNotExist:
            return Response({'error': 'NOT_FOUND'}, status=404)

        # CA-09: si el evento NO es de scope ACCESS → 404 (anti-info-leak)
        if not AccessScopeFilter.is_access_event(audit.action):
            return Response({'error': 'NOT_FOUND'}, status=404)

        AuditLogService.emit(
            event_type='ACCESS_AUDIT_VIEWED',
            actor_user_id=request.user.pk,
            payload={'viewed_event_id': str(event_id)},
        )

        return Response({
            'id': audit.pk, 'action': audit.action,
            'user_id': audit.user_id, 'resource': audit.resource,
            'result': audit.result, 'created_at': str(audit.created_at),
            'details': audit.details,
        })


@extend_schema(
    operation_id='access_audit_aggregations',
    summary='UC_ACC_09 — Agregaciones de eventos de acceso (sin audit)',
    tags=[_TAG],
)
class AccessAuditAggregationsView(APIView):
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'ACC-013'

    def get(self, request):
        group_by = request.query_params.get('group_by', 'event_type')

        from django.db.models import Count
        qs = AccessScopeFilter.queryset(AuditLog.objects.all()) \
            .values('action').annotate(count=Count('id')).order_by('-count')

        buckets = [{'event_type': row['action'], 'count': row['count']} for row in qs[:50]]

        # CA-10: NO se emite AuditEvent en aggregations
        return Response({'group_by': group_by, 'buckets': buckets})
