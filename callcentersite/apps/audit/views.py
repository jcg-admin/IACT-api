"""
Views para consulta de AuditLog.
"""
from rest_framework import viewsets, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import AuditLog
from .serializers import AuditLogSerializer, AuditLogSummarySerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para AuditLog.
    
    Endpoints:
    - GET /api/v1/audit/logs/ - Listar logs
    - GET /api/v1/audit/logs/{id}/ - Detalle de log
    
    INMUTABLE (CNST-009): Solo permite GET, no POST/PUT/DELETE.
    
    Filtros disponibles:
    - user: ID de usuario
    - action: Tipo de acción (LOGIN, CREATE, etc.)
    - result: SUCCESS o FAILURE
    - timestamp: Rango de fechas
    
    Búsqueda:
    - resource: Buscar en nombre de recurso
    
    Ordenamiento:
    - timestamp (default: -timestamp)
    """
    
    queryset = AuditLog.objects.all()
    permission_classes = [IsAuthenticated]
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
from rest_framework.decorators import action


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
        from apps.audit.models import AuditLog
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
