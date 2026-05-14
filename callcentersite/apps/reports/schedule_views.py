"""
apps/reports/schedule_views.py

UC_RPT_07 — Programar Reporte. POST/PATCH/DELETE /api/reports/schedules/
UC_RPT_08 — Ver Reportes Programados. GET /api/reports/schedules/
"""
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access.permissions.function_permissions import HasFunction
from apps.audit.services import AuditLogService
from apps.reports.models import ScheduledReport
from apps.reports.schedule_service import ScheduleValidator, ScheduleService

_TAG = 'Reportes Programados'


class ScheduleCreateSerializer(serializers.Serializer):
    report_type    = serializers.CharField(max_length=50)
    format         = serializers.ChoiceField(choices=['csv','xlsx','json','pdf'], default='csv')
    frequency      = serializers.ChoiceField(choices=['daily','weekly','monthly','cron'])
    run_at_hour    = serializers.IntegerField(min_value=0, max_value=23, default=6)
    run_at_minute  = serializers.IntegerField(min_value=0, max_value=59, default=0)
    cron_expression= serializers.CharField(required=False, allow_blank=True, default='')
    day_of_week    = serializers.IntegerField(required=False, min_value=0, max_value=6, allow_null=True)
    day_of_month   = serializers.IntegerField(required=False, min_value=1, max_value=31, allow_null=True)
    filters        = serializers.DictField(default=dict)
    group_by       = serializers.ListField(child=serializers.CharField(), default=list)


class SchedulePatchSerializer(serializers.Serializer):
    status         = serializers.ChoiceField(required=False, choices=['active','paused','deleted'])
    run_at_hour    = serializers.IntegerField(required=False, min_value=0, max_value=23)
    cron_expression= serializers.CharField(required=False, allow_blank=True)


def _sched_to_dict(s: ScheduledReport) -> dict:
    return {
        'id': s.pk, 'report_type': s.report_type, 'format': s.format,
        'frequency': s.frequency, 'status': s.status,
        'next_run_at': s.next_run_at.isoformat() if s.next_run_at else None,
        'last_run_at': s.last_run_at.isoformat() if s.last_run_at else None,
        'failure_count': s.failure_count,
    }


@extend_schema_view(
    get=extend_schema(
        operation_id='reports_schedule_list',
        summary='UC_RPT_08 — Listar reportes programados',
        tags=[_TAG],
    ),
    post=extend_schema(
        operation_id='reports_schedule_create',
        summary='UC_RPT_07 — Programar reporte periódico',
        responses={
            201: OpenApiResponse(description='Schedule creado con next_run_at'),
            429: OpenApiResponse(description='SCHEDULE_LIMIT_EXCEEDED — > 10 activos'),
        },
        tags=[_TAG],
    ),
)
class ScheduledReportListCreateView(APIView):
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'RPT-009'

    def get(self, request):
        status_filter = request.query_params.get('status')
        qs = ScheduledReport.objects.filter(actor=request.user).order_by('-created_at')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return Response({'count': qs.count(), 'results': [_sched_to_dict(s) for s in qs]})

    def post(self, request):
        ser = ScheduleCreateSerializer(data=request.data)
        if not ser.is_valid():
            return Response({'error': 'VALIDATION_ERROR', 'fields': ser.errors}, status=400)

        data = ser.validated_data

        # CA-05: cron invalido
        if data.get('cron_expression'):
            try:
                ScheduleValidator.validate_cron(data['cron_expression'])
                ScheduleValidator.validate_min_frequency(data['cron_expression'])
            except ValueError as e:
                return Response({'error': 'INVALID_CRON', 'detail': str(e)}, status=400)

        # CA-07: límite 10 schedules activos
        active_count = ScheduledReport.objects.filter(
            actor=request.user,
            status__in=(ScheduledReport.STATUS_ACTIVE, ScheduledReport.STATUS_PAUSED),
        ).count()
        if active_count >= ScheduledReport.MAX_SCHEDULES_PER_USER:
            return Response({'error': 'SCHEDULE_LIMIT_EXCEEDED'}, status=429)

        next_run_at = ScheduleService.compute_next(data)

        sched = ScheduledReport.objects.create(
            actor=request.user,
            report_type=data['report_type'],
            format=data['format'],
            frequency=data['frequency'],
            run_at_hour=data.get('run_at_hour', 6),
            run_at_minute=data.get('run_at_minute', 0),
            cron_expression=data.get('cron_expression', ''),
            day_of_week=data.get('day_of_week'),
            day_of_month=data.get('day_of_month'),
            filters=data.get('filters', {}),
            group_by=data.get('group_by', []),
            status=ScheduledReport.STATUS_ACTIVE,
            next_run_at=next_run_at,
        )

        AuditLogService.emit(
            event_type='SCHEDULED_REPORT_CREATED',
            actor_user_id=request.user.pk,
            payload={'schedule_id': sched.pk, 'frequency': sched.frequency},
        )

        return Response(_sched_to_dict(sched), status=201)


@extend_schema_view(
    get=extend_schema(
        operation_id='reports_schedule_retrieve',
        summary='UC_RPT_08 — Detalle de reporte programado',
        tags=[_TAG],
    ),
    patch=extend_schema(
        operation_id='reports_schedule_update',
        summary='UC_RPT_07 — Modificar / pausar / reanudar schedule',
        tags=[_TAG],
    ),
    delete=extend_schema(
        operation_id='reports_schedule_delete',
        summary='UC_RPT_07 — Eliminar schedule (baja lógica BR-009)',
        tags=[_TAG],
    ),
)
class ScheduledReportDetailView(APIView):
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'RPT-009'

    def _get(self, sched_id, user):
        try:
            return ScheduledReport.objects.get(pk=sched_id, actor=user)
        except ScheduledReport.DoesNotExist:
            return None

    def get(self, request, sched_id):
        s = self._get(sched_id, request.user)
        if not s:
            return Response({'error': 'NOT_FOUND'}, status=404)
        return Response(_sched_to_dict(s))

    def patch(self, request, sched_id):
        s = self._get(sched_id, request.user)
        if not s:
            return Response({'error': 'NOT_FOUND'}, status=404)

        ser = SchedulePatchSerializer(data=request.data, partial=True)
        if not ser.is_valid():
            return Response({'error': 'VALIDATION_ERROR', 'fields': ser.errors}, status=400)

        for field, value in ser.validated_data.items():
            setattr(s, field, value)
        if 'run_at_hour' in ser.validated_data or 'cron_expression' in ser.validated_data:
            s.next_run_at = ScheduleService.compute_next({
                'frequency': s.frequency,
                'run_at_hour': s.run_at_hour,
                'run_at_minute': s.run_at_minute,
            })
        s.save()

        AuditLogService.emit(
            event_type='SCHEDULED_REPORT_PAUSED' if s.status == ScheduledReport.STATUS_PAUSED
                       else 'SCHEDULED_REPORT_RESUMED',
            actor_user_id=request.user.pk,
            payload={'schedule_id': s.pk},
        )
        return Response(_sched_to_dict(s))

    def delete(self, request, sched_id):
        s = self._get(sched_id, request.user)
        if not s:
            return Response({'error': 'NOT_FOUND'}, status=404)
        s.status = ScheduledReport.STATUS_DELETED
        s.save(update_fields=['status'])
        AuditLogService.emit(
            event_type='SCHEDULED_REPORT_DELETED',
            actor_user_id=request.user.pk,
            payload={'schedule_id': s.pk},
        )
        return Response({'id': s.pk, 'status': s.status})
