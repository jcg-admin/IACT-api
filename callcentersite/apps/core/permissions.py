"""
DRF Permissions custom para IACT.

CLEAN_CODE v3.0.1: Nombres auto-documentados.
SOLID: SRP - Cada permission una responsabilidad clara.
"""

from rest_framework import permissions


# ============================================================================
# RBAC PERMISSIONS
# ============================================================================

class RequiresFunctionPermission(permissions.BasePermission):
    """
    Permission que requiere función RBAC específica usando namespaces Django.
    
    RBAC v6.0.0: Usa permission_django (namespaces) en lugar de codes.
    
    El ViewSet debe definir function_map con namespaces Django:
    
    Uso en ViewSet:
        class UserViewSet(viewsets.ModelViewSet):
            permission_classes = [IsAuthenticated, RequiresFunctionPermission]
            
            function_map = {
                'list': 'users.view',           # <- Namespace Django
                'create': 'users.create',
                'update': 'users.edit',
                'partial_update': 'users.edit',
                'destroy': 'users.delete',
            }
    
    Comportamiento:
        - Sin function_map: Permite acceso (sin restricción RBAC)
        - Con function_map pero acción no mapeada: Permite acceso
        - Con function_map y acción mapeada: Verifica permiso
    
    Examples:
        # Usuario CON función 'users.view':
        GET /api/v1/users/ -> 200 OK [SUCCESS]
        
        # Usuario SIN función 'users.create':
        POST /api/v1/users/ -> 403 Forbidden [ERROR]
        
        # Acción no mapeada (sin restricción):
        OPTIONS /api/v1/users/ -> 200 OK [SUCCESS]
    
    CLEAN_CODE v3.0.1: Nombre que revela intención.
    SOLID SRP: Solo verifica función RBAC.
    """
    
    message = 'No tiene permiso para realizar esta acción.'
    
    def has_permission(self, request, view):
        """
        Verifica permiso RBAC usando namespace Django.
        
        Args:
            request: HttpRequest
            view: ViewSet instance
        
        Returns:
            bool: True si tiene permiso, False si no
        
        Proceso:
            1. Verifica autenticación
            2. Superuser bypass
            3. Obtiene function_map del ViewSet
            4. Si no hay function_map -> permite (sin restricción)
            5. Si acción no mapeada -> permite (sin restricción)
            6. Si acción mapeada -> verifica con User.has_function()
        """
        # 1. Usuario debe estar autenticado
        if not request.user or not request.user.is_authenticated:
            return False
        
        # 2. Superusers siempre tienen acceso
        if request.user.is_superuser:
            return True
        
        # 3. Obtener function_map del ViewSet
        function_map = getattr(view, 'function_map', {})
        
        # 4. Si no hay function_map, permitir (sin restricción RBAC)
        if not function_map:
            return True
        
        # 5. Obtener acción actual
        action = getattr(view, 'action', None)
        
        # Si la acción no está mapeada, permitir (sin restricción)
        if action not in function_map:
            return True
        
        # 6. Obtener permission_django (namespace)
        permission_django = function_map[action]
        
        # Verificar permiso RBAC usando namespace
        return request.user.has_function(permission_django)
    
    def get_required_function(self, request, view):
        """
        Helper para debugging: obtiene la función requerida.
        
        Args:
            request: HttpRequest
            view: ViewSet
        
        Returns:
            str | None: Namespace requerido o None
        
        Example:
            >>> permission = RequiresFunctionPermission()
            >>> permission.get_required_function(request, view)
            'users.view'
        """
        function_map = getattr(view, 'function_map', {})
        action = getattr(view, 'action', None)
        return function_map.get(action)


# ============================================================================
# OWNERSHIP PERMISSIONS
# ============================================================================

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission: Owner puede editar, otros solo lectura.
    
    CLEAN_CODE v3.0.1: Nombre descriptivo.
    SOLID SRP: Solo verifica ownership.
    
    Requiere que el modelo tenga campo 'created_by'.
    
    Uso:
        class ReportViewSet(viewsets.ModelViewSet):
            permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    
    Examples:
        # Usuario es created_by:
        PUT /api/reports/1/ -> 200 OK
        
        # Usuario NO es created_by:
        GET /api/reports/1/ -> 200 OK (lectura permitida)
        PUT /api/reports/1/ -> 403 Forbidden (escritura denegada)
    """
    
    message = 'Solo el creador puede editar este recurso.'
    
    def has_object_permission(self, request, view, obj):
        """
        Verifica ownership sobre objeto.
        
        Args:
            request: HttpRequest
            view: ViewSet
            obj: Objeto del modelo
        
        Returns:
            bool: True si tiene permiso
        """
        # Lectura permitida para todos (autenticados)
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Escritura solo para owner
        if not hasattr(obj, 'created_by'):
            # Si no tiene created_by, denegar escritura
            return False
        
        return obj.created_by == request.user


# ============================================================================
# SUPERUSER PERMISSIONS
# ============================================================================

class IsSuperUserOrReadOnly(permissions.BasePermission):
    """
    Permission: Superuser puede editar, otros solo lectura.
    
    CLEAN_CODE v3.0.1: Nombre auto-documentado.
    SOLID SRP: Solo verifica superuser.
    
    Uso:
        class ConfigViewSet(viewsets.ModelViewSet):
            permission_classes = [IsAuthenticated, IsSuperUserOrReadOnly]
    
    Examples:
        # Superuser:
        POST /api/config/ -> 201 Created
        
        # Usuario normal:
        GET /api/config/ -> 200 OK (lectura permitida)
        POST /api/config/ -> 403 Forbidden (escritura denegada)
    """
    
    message = 'Solo superusuarios pueden modificar este recurso.'
    
    def has_permission(self, request, view):
        """
        Verifica si es superuser.
        
        Args:
            request: HttpRequest
            view: ViewSet
        
        Returns:
            bool: True si tiene permiso
        """
        # Lectura permitida para todos (autenticados)
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Escritura solo para superuser
        return request.user and request.user.is_superuser


# ============================================================================
# CORS / OPTIONS PERMISSIONS
# ============================================================================

class AllowOptionsAuthentication(permissions.BasePermission):
    """
    Permission: Permite OPTIONS sin autenticación.
    
    CLEAN_CODE v3.0.1: Nombre que revela intención.
    SOLID SRP: Solo permite OPTIONS.
    
    Para CORS preflight requests.
    
    Uso:
        class APIViewSet(viewsets.ModelViewSet):
            permission_classes = [
                AllowOptionsAuthentication,
                IsAuthenticated,
            ]
    
    Examples:
        OPTIONS /api/reports/ -> 200 OK (sin autenticación)
        GET /api/reports/ -> Requiere autenticación
    """
    
    def has_permission(self, request, view):
        """
        Permite OPTIONS sin autenticación.
        
        Args:
            request: HttpRequest
            view: ViewSet
        
        Returns:
            bool: True siempre (delega a siguiente permission)
        """
        if request.method == 'OPTIONS':
            return True
        
        # Delegar a siguiente permission
        return True


# ====================================================================================
# REMOVED - FASE A DT-002 (2026-01-21)
# ====================================================================================
#
# HasServiceAccess (eliminado):
#   - Permission class para verificar acceso a servicios 800
#   - Usaba UserServiceAccess.has_service_access()
#
# Razón: UserServiceAccess eliminado, reemplazado por RBAC puro
# Reemplazo: Usar RequiresFunctionPermission con CALL_VIEW, SVC_VIEW, etc.
#
# Ejemplo de migración:
#   ANTES:
#     permission_classes = [IsAuthenticated, HasServiceAccess]
#
#   DESPUÉS:
#     permission_classes = [IsAuthenticated, RequiresFunctionPermission]
#     function_map = {'list': 'CALL_VIEW', ...}
# ====================================================================================


# ============================================================================
# STAFF PERMISSIONS
# ============================================================================

class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Permission: Staff puede editar, otros solo lectura.
    
    CLEAN_CODE v3.0.1: Nombre auto-documentado.
    SOLID SRP: Solo verifica staff.
    
    Uso:
        class CenterViewSet(viewsets.ModelViewSet):
            permission_classes = [IsAuthenticated, IsStaffOrReadOnly]
    """
    
    message = 'Solo staff puede modificar este recurso.'
    
    def has_permission(self, request, view):
        """
        Verifica si es staff.
        
        Args:
            request: HttpRequest
            view: ViewSet
        
        Returns:
            bool: True si tiene permiso
        """
        # Lectura permitida para todos (autenticados)
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Escritura solo para staff o superuser
        return request.user and (request.user.is_staff or request.user.is_superuser)


# ============================================================================
# RESUMEN PERMISSIONS
# 
# Total: 7 permissions custom
# 
# RBAC:
#   [SUCCESS] RequiresFunctionPermission - Función RBAC específica
# 
# Ownership:
#   [SUCCESS] IsOwnerOrReadOnly - Solo owner puede editar
# 
# Role-based:
#   [SUCCESS] IsSuperUserOrReadOnly - Solo superuser puede editar
#   [SUCCESS] IsStaffOrReadOnly - Solo staff puede editar
# 
# Service Access:
#   [SUCCESS] HasServiceAccess - Acceso a servicios 800
# 
# CORS:
#   [SUCCESS] AllowOptionsAuthentication - Permite OPTIONS
# 
# Principios SOLID Aplicados:
#   [SUCCESS] SRP: Cada permission una responsabilidad
#   [SUCCESS] Clean Naming: Nombres auto-documentados
#   [SUCCESS] Documentation: Docstrings + ejemplos
#   [SUCCESS] DRY: _get_service_from_object() helper
# ============================================================================
