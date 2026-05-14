"""
apps/audit/compliance_views.py

UC_AUD_04 — Generar Reporte de Compliance.
POST /api/audit/compliance-report/
POST /api/audit/compliance-verify/
"""
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access.permissions.function_permissions import HasFunction
from apps.audit.compliance_service import ComplianceTemplateValidator, HMACSigner
from apps.audit.services import AuditLogService

_TAG = 'Auditoría'


class ComplianceRequestSerializer(serializers.Serializer):
    template  = serializers.CharField()
    date_from = serializers.DateField()
    date_to   = serializers.DateField()


class ComplianceVerifySerializer(serializers.Serializer):
    payload   = serializers.CharField()
    signature = serializers.CharField(max_length=128)


@extend_schema_view(
    post=extend_schema(
        operation_id='audit_compliance_report',
        summary='UC_AUD_04 — Generar reporte de compliance',
        responses={
            200: OpenApiResponse(description='Reporte + firma HMAC'),
            400: OpenApiResponse(description='Template inválido'),
            403: OpenApiResponse(description='Sin AUD-004'),
        },
        tags=[_TAG],
    )
)
class ComplianceReportView(APIView):
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'AUD-004'

    def post(self, request):
        ser = ComplianceRequestSerializer(data=request.data)
        if not ser.is_valid():
            return Response({'error': 'VALIDATION_ERROR', 'fields': ser.errors}, status=400)

        data = ser.validated_data
        try:
            ComplianceTemplateValidator.validate(data['template'])
        except ValueError as e:
            return Response({'error': 'INVALID_TEMPLATE', 'detail': str(e)}, status=400)

        # Stub: genera payload mínimo y lo firma
        import json
        report_payload = json.dumps({
            'template':  data['template'],
            'date_from': str(data['date_from']),
            'date_to':   str(data['date_to']),
            'generated_by': request.user.pk,
            'findings': [],
        }).encode()

        signature = HMACSigner.sign(report_payload)

        AuditLogService.emit(
            event_type='COMPLIANCE_REPORT_REQUESTED',
            actor_user_id=request.user.pk,
            payload={'template': data['template']},
        )

        return Response({
            'template':  data['template'],
            'signature': signature,
            'report':    report_payload.decode(),
        })


@extend_schema_view(
    post=extend_schema(
        operation_id='audit_compliance_verify',
        summary='UC_AUD_04 CA-06 — Verificar firma de reporte de compliance',
        tags=[_TAG],
    )
)
class ComplianceVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = ComplianceVerifySerializer(data=request.data)
        if not ser.is_valid():
            return Response({'error': 'VALIDATION_ERROR'}, status=400)

        payload   = ser.validated_data['payload'].encode()
        signature = ser.validated_data['signature']
        valid     = HMACSigner.verify(payload, signature)
        return Response({'valid': valid})
