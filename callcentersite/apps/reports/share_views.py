"""
apps/reports/share_views.py

UC_RPT_11 — Compartir Reporte.
POST /api/reports/shares/
DELETE /api/reports/shares/{id}/
"""
import uuid
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access.permissions.function_permissions import HasFunction
from apps.audit.services import AuditLogService
from apps.reports.share_service import ShareValidator

_TAG = 'Reportes'


class ShareCreateSerializer(serializers.Serializer):
    report_type  = serializers.CharField(max_length=50, required=False, default='')
    filters      = serializers.DictField(default=dict)
    target_type  = serializers.ChoiceField(choices=['user', 'agr', 'segment_public'])
    target_id    = serializers.IntegerField()
    permission   = serializers.ChoiceField(choices=['read', 'clone'], default='read')
    expires_at   = serializers.DateTimeField(required=False, allow_null=True)


@extend_schema_view(
    post=extend_schema(
        operation_id='reports_share_create',
        summary='UC_RPT_11 — Compartir reporte',
        responses={
            201: OpenApiResponse(description='ShareEntry creado'),
            403: OpenApiResponse(description='Sin RPT-011 share_report'),
        },
        tags=[_TAG],
    )
)
class ShareCreateView(APIView):
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'RPT-011'

    def post(self, request):
        ser = ShareCreateSerializer(data=request.data)
        if not ser.is_valid():
            return Response({'error': 'VALIDATION_ERROR', 'fields': ser.errors}, status=400)

        data = ser.validated_data
        try:
            ShareValidator.validate({
                'target_type': data['target_type'],
                'target_id':   data['target_id'],
                'owner_id':    request.user.pk,
                'permission':  data['permission'],
            })
        except ValueError as e:
            return Response({'error': 'VALIDATION_ERROR', 'detail': str(e)}, status=400)

        share_id = str(uuid.uuid4())

        AuditLogService.emit(
            event_type='REPORT_SHARE_CREATED',
            actor_user_id=request.user.pk,
            payload={
                'share_id':    share_id,
                'target_type': data['target_type'],
                'target_id':   data['target_id'],
                'permission':  data['permission'],
            },
        )

        # CA-14: CNST-001 — no email externo
        # Mailbox notify es opcional según preferencia del receptor
        return Response({
            'share_id':    share_id,
            'target_type': data['target_type'],
            'target_id':   data['target_id'],
            'permission':  data['permission'],
        }, status=201)


@extend_schema_view(
    delete=extend_schema(
        operation_id='reports_share_delete',
        summary='UC_RPT_11 — Revocar share',
        tags=[_TAG],
    )
)
class ShareDetailView(APIView):
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'RPT-011'

    def delete(self, request, share_id):
        AuditLogService.emit(
            event_type='REPORT_SHARE_REVOKED',
            actor_user_id=request.user.pk,
            payload={'share_id': str(share_id)},
        )
        return Response({'share_id': str(share_id), 'status': 'revoked'})
