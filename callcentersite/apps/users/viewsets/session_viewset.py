"""
ViewSet para SessionHistory (auditoría de sesiones).

CLEAN_CODE v3.0.1: ViewSet con responsabilidad única.
SOLID SRP: Solo auditoría de sesiones.

FASE 2 PARTE 5: ViewSets de apps/users/
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.core.permissions import RequiresFunctionPermission
from apps.users.models import SessionHistory
from apps.users.serializers import SessionHistorySerializer
from apps.users.constants import PERM_SESSIONS_VIEW


class SessionHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para auditoría de sesiones.
    
    Read-only: Solo ver, no crear/modificar/eliminar.
    La creación es automática vía signals (log_user_login).
    
    Endpoints:
    - GET /api/sessions/ - Listar sesiones (requires: sessions.view)
    - GET /api/sessions/{id}/ - Detalle sesión (requires: sessions.view)
    
    Permissions:
    - RequiresFunctionPermission: Verifica function_map
    - function_map: Requiere 'sessions.view'
    
    Queryset:
    - Usuarios normales: Solo sus propias sesiones
    - Staff/Superuser: Todas las sesiones
    
    Example:
        # Listar mis sesiones (usuario normal)
        GET /api/sessions/
        
        # Listar todas las sesiones (staff)
        GET /api/sessions/
        
        # Filtros disponibles:
        GET /api/sessions/?is_active=true
        GET /api/sessions/?user=1
    """
    
    serializer_class = SessionHistorySerializer
    permission_classes = [IsAuthenticated, RequiresFunctionPermission]
    
    # function_map: Mapea actions a namespaces Django
    function_map = {
        'list': PERM_SESSIONS_VIEW,     # 'sessions.view'
        'retrieve': PERM_SESSIONS_VIEW, # 'sessions.view'
    }
    
    def get_queryset(self):
        """
        Obtiene queryset de sesiones.
        
        Lógica:
        - Staff/Superuser: Todas las sesiones
        - Usuario normal: Solo sus sesiones
        
        Filtros opcionales vía query params:
        - is_active: true/false
        - user: user_id (solo staff)
        
        Returns:
            QuerySet: Sesiones filtradas
        """
        user = self.request.user
        
        # Staff ve todas las sesiones
        if user.is_staff or user.is_superuser:
            queryset = SessionHistory.objects.all()
        else:
            # Usuarios normales solo ven sus sesiones
            queryset = SessionHistory.objects.filter(user=user)
        
        # Optimización: select_related user
        queryset = queryset.select_related('user')
        
        # Filtros opcionales
        is_active = self.request.query_params.get('is_active')
        user_id = self.request.query_params.get('user')
        
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filtro por user_id (solo staff)
        if user_id and (user.is_staff or user.is_superuser):
            queryset = queryset.filter(user_id=user_id)
        
        return queryset.order_by('-login_at')


# ============================================================================
# RESUMEN SESSION VIEWSET
#
# ViewSet: SessionHistoryViewSet
#
# Endpoints:
#   [SUCCESS] GET /api/sessions/ - Listar sesiones (sessions.view)
#   [SUCCESS] GET /api/sessions/{id}/ - Detalle sesión (sessions.view)
#
# Permissions:
#   [SUCCESS] RequiresFunctionPermission (apps/core)
#   [SUCCESS] function_map con namespace 'sessions.view'
#
# Features:
#   [SUCCESS] Read-only (no crear/modificar/eliminar)
#   [SUCCESS] Creación automática vía signals
#   [SUCCESS] Queryset por rol:
#      - Staff: Todas las sesiones
#      - Usuario: Solo sus sesiones
#   [SUCCESS] Filtros: is_active, user
#   [SUCCESS] Optimizado: select_related('user')
#
# Principios:
#   [SUCCESS] SRP: Solo auditoría de sesiones
#   [SUCCESS] Clean Code: Nombres auto-documentados
#   [SUCCESS] RBAC: Permission vía function_map
#   [SUCCESS] Read-only: Protege integridad de auditoría
# ============================================================================
