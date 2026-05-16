from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse
"""
Views para consulta de AuditLog.

UC_AUD_01 — Consultar Auditoría.
Fuente: uc-aud-01/criterios-aceptacion.rst
Función RBAC: AUD-001 view_audit_log (CNST-010: permission_classes explícito).
"""
from rest_framework import viewsets, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from apps.access.permissions.function_permissions import HasFunction
from .models import AuditLog
from .serializers import AuditLogSerializer, AuditLogSummarySerializer


@extend_schema_view(
    list=extend_schema(
        summary='UC_AUD_01 — Consultar log de auditoría',
        description=(
            'Retorna el log de auditoría paginado con filtros por módulo, '
            'actor y rango de fechas.\n\n'
            '**AUD-001 `view_audit_log`** requerido (CA de UC_AUD_01).\n\n'
            'El propio acceso emite `GENERAL_AUDIT_QUERIED` via UC_PERM_09 '
            '(meta-audit — uc-aud-01/datos-involucrados.rst § 7.1).\n\n'
            '**CNST-025**: AuditLog append-only — no POST/PUT/DELETE.\n\n'
            '**Hallazgo F1-H-004**: permission_classes era [IsAuthenticated] sin '
            'HasFunction ni required_function — cualquier usuario autenticado '
            'podía ver logs de toda la organización.'
        ),
        parameters=[
            OpenApiParameter('user', int, location='query',
                             description='Filtrar por ID de usuario actor.'),
            OpenApiParameter('action', str, location='query',
                             description='Filtrar por tipo de evento (LOGIN, LOGOUT, ...).'),
            OpenApiParameter('result', str, location='query',
                             description='Filtrar por resultado (SUCCESS / FAILURE).'),
            OpenApiParameter('search', str, location='query',
                             description='Búsqueda libre en resource y details.'),
        ],
        responses={
            200: OpenApiResponse(description='Lista paginada de AuditLog.'),
            403: OpenApiResponse(description='Sin permiso AUD-001 view_audit_log.'),
        },
        tags=['Auditoria'],
    ),
    retrieve=extend_schema(
        summary='UC_AUD_02 — Detalle de registro de auditoría',
        description='Retorna el detalle completo de un AuditLog por ID.',
        tags=['Auditoria'],
    ),
)
class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    UC_AUD_01 — ViewSet de solo lectura para AuditLog.

    Endpoints:
    - GET /api/audit/logs/      — Listar logs (AUD-001)
    - GET /api/audit/logs/{id}/ — Detalle de log (AUD-001)

    CNST-025 / CNST-009: Append-only — solo GET, no POST/PUT/DELETE.
    CNST-010: permission_classes explícito.
    """

    queryset = AuditLog.objects.all()
    permission_classes = [IsAuthenticated, HasFunction]
    required_function = 'AUD-001'   # view_audit_log (F1-H-004: faltaba)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user', 'action', 'result']
    search_fields = ['resource', 'details']
    ordering_fields = ['timestamp', 'action']
    ordering = ['-timestamp']
    
    def get_serializer_class(self):
        """
        Usar serializer resumido para list, completo para retrieve.
        """
        if self.action == 'list':
            return AuditLogSummarySerializer
        return AuditLogSerializer
    
    def get_queryset(self):
        """
        Filtrar logs según permisos del usuario.
        
        - Superusuarios ven todos los logs
        - Usuarios normales solo ven sus propios logs
        """
        queryset = super().get_queryset()
        
        # Superusuarios ven todo
        if self.request.user.is_superuser:
            return queryset
        
        # Usuarios normales solo sus logs
        return queryset.filter(user=self.request.user)


# ---------------------------------------------------------------------------
# B-08: UC_AUD_04 — Firma y verificacion de integridad de AuditLog
# ---------------------------------------------------------------------------
import hashlib
import hmac
from django.conf import settings


@extend_schema(
    summary="UC_AUD_04 — Verificar integridad de AuditLog (HMAC-SHA256)",
    parameters=[OpenApiParameter('log_id', int, required=True,
        description="ID del registro de AuditLog a verificar")],
    responses={
        200: OpenApiResponse(description="estado: integro | comprometido | sin_firma"),
        404: OpenApiResponse(description="AuditLog no encontrado"),
    },
    tags=["Auditoria"]
)
class AuditIntegrityView(APIView):
    """
    UC_AUD_04 — Verificar integridad de registros de auditoria.

    La integridad se verifica calculando un HMAC-SHA256 del contenido
    del registro y comparandolo con la firma almacenada.

    GET  /api/audit/integrity/verify/?log_id=X  — verificar un registro
    POST /api/audit/integrity/sign/             — firmar un lote de registros
    """
    permission_classes = [IsAuthenticated]

    def _compute_signature(self, log) -> str:
        """Calcula HMAC-SHA256 del contenido del AuditLog."""
        secret = getattr(settings, 'AUDIT_HMAC_SECRET', 'iact-audit-secret-key')
        payload = f"{log.id}|{log.user_id}|{log.action}|{log.resource}|{log.result}|{log.timestamp}"
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

    def get(self, request):
        """Verificar integridad de un registro de auditoria."""
        from apps.audit.models import AuditLog
        log_id = request.query_params.get('log_id')
        if not log_id:
            return Response({'error': 'log_id es requerido.'}, status=400)

        try:
            log = AuditLog.objects.get(pk=log_id)
        except AuditLog.DoesNotExist:
            return Response({'error': 'AuditLog no encontrado.'}, status=404)

        firma_calculada = self._compute_signature(log)
        firma_almacenada = getattr(log, 'firma_integridad', None)

        if firma_almacenada is None:
            return Response({
                'log_id':  log_id,
                'estado':  'sin_firma',
                'detalle': 'Este registro no tiene firma de integridad almacenada.',
            })

        integro = hmac.compare_digest(firma_calculada, firma_almacenada)
        return Response({
            'log_id':  log_id,
            'estado':  'integro' if integro else 'comprometido',
            'integro': integro,
        })
