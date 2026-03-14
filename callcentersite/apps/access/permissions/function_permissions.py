"""
DRF Permissions para RBAC v6.0.0 - Funciones.

Usa namespaces Django (permission_django) en lugar de codes.
"""

from rest_framework.permissions import BasePermission


class HasFunction(BasePermission):
    """
    Permission que verifica función RBAC usando namespace Django.
    
    RBAC v6.0.0: Usa permission_django (namespaces) en lugar de codes.
    
    La view debe definir el atributo: required_function con namespace Django.
    
    Uso en APIView:
        class ReportListView(APIView):
            permission_classes = [IsAuthenticated, HasFunction]
            required_function = 'reports.view'  # <- Namespace Django
            
            def get(self, request):
                # Solo usuarios con función 'reports.view' pueden acceder
                return Response(...)
    
    Uso en ViewSet (alternativa a RequiresFunctionPermission):
        class ReportViewSet(viewsets.ReadOnlyModelViewSet):
            permission_classes = [IsAuthenticated, HasFunction]
            required_function = 'reports.view'
    
    Examples:
        # Usuario CON función 'reports.view':
        GET /api/v1/reports/ -> 200 OK [SUCCESS]
        
        # Usuario SIN función 'reports.view':
        GET /api/v1/reports/ -> 403 Forbidden [ERROR]
        
        # Superuser (bypass):
        GET /api/v1/reports/ -> 200 OK [SUCCESS]
    
    Nota:
        Para ViewSets con múltiples acciones, usar RequiresFunctionPermission
        con function_map en lugar de HasFunction.
    """
    
    message = 'No tiene permiso para realizar esta acción.'
    
    def has_permission(self, request, view):
        """
        Verificar si usuario tiene la función requerida.
        
        Args:
            request: HttpRequest
            view: View que requiere el permiso
        
        Returns:
            bool: True si tiene permiso, False si no
        
        Proceso:
            1. Verifica autenticación
            2. Superuser bypass
            3. Obtiene required_function de la view
            4. Si no hay required_function -> permite (sin restricción)
            5. Verifica con User.has_function(namespace)
        """
        # 1. Usuario debe estar autenticado
        if not request.user or not request.user.is_authenticated:
            return False
        
        # 2. Superuser siempre tiene permiso
        if request.user.is_superuser:
            return True
        
        # 3. Obtener función requerida de la view (namespace Django)
        required_function = getattr(view, 'required_function', None)
        
        # 4. Si no se especifica función, permitir (sin restricción)
        if not required_function:
            return True
        
        # 5. Verificar permiso usando namespace Django
        # Usa User.has_function() que filtra por:
        #   - permission_django (namespace)
        #   - status='activo'
        #   - is_active=True
        return request.user.has_function(required_function)
