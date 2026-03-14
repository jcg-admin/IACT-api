"""
Custom permissions para sistema de acceso.
"""
from rest_framework import permissions
from ..services import ModuleAccessService


class HasModuleAccess(permissions.BasePermission):
    """
    Permission para verificar acceso a módulos.
    
    Uso en views:
        permission_classes = [IsAuthenticated, HasModuleAccess]
        required_module = 'MOD_Reports'  # Código del módulo requerido
    
    Ejemplo:
        class ReportViewSet(viewsets.ModelViewSet):
            permission_classes = [IsAuthenticated, HasModuleAccess]
            required_module = 'MOD_Reports'
    """
    
    message = 'No tienes acceso a este módulo.'
    
    def has_permission(self, request, view):
        """
        Verificar si el usuario tiene acceso al módulo requerido.
        
        Args:
            request: HttpRequest
            view: View que requiere el permiso
            
        Returns:
            bool: True si tiene acceso, False si no
        """
        # Verificar autenticación
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusuarios siempre tienen acceso
        if request.user.is_superuser:
            return True
        
        # Obtener módulo requerido de la vista
        required_module = getattr(view, 'required_module', None)
        
        # Si no se especifica módulo, permitir acceso
        if not required_module:
            return True
        
        # Verificar acceso usando el service
        has_access = ModuleAccessService.has_module_access(
            user=request.user,
            module_code=required_module
        )
        
        if not has_access:
            self.message = f'No tienes acceso al módulo {required_module}.'
        
        return has_access
    
    def has_object_permission(self, request, view, obj):
        """
        Verificar permisos a nivel de objeto.
        
        Para módulos, usa la misma lógica que has_permission.
        """
        return self.has_permission(request, view)


class HasAnyModuleAccess(permissions.BasePermission):
    """
    Permission que verifica acceso a CUALQUIERA de múltiples módulos.
    
    Uso:
        permission_classes = [IsAuthenticated, HasAnyModuleAccess]
        required_modules = ['MOD_Reports', 'MOD_Dashboard']
    """
    
    message = 'No tienes acceso a ninguno de los módulos requeridos.'
    
    def has_permission(self, request, view):
        """
        Verificar acceso a cualquiera de los módulos.
        
        Args:
            request: HttpRequest
            view: View con required_modules
            
        Returns:
            bool: True si tiene acceso a al menos uno
        """
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        required_modules = getattr(view, 'required_modules', [])
        
        if not required_modules:
            return True
        
        # Verificar acceso a cualquiera
        for module_code in required_modules:
            if ModuleAccessService.has_module_access(request.user, module_code):
                return True
        
        self.message = f'No tienes acceso a ninguno de estos módulos: {", ".join(required_modules)}.'
        return False


class HasAllModuleAccess(permissions.BasePermission):
    """
    Permission que verifica acceso a TODOS los módulos especificados.
    
    Uso:
        permission_classes = [IsAuthenticated, HasAllModuleAccess]
        required_modules = ['MOD_Reports', 'MOD_Users']
    """
    
    message = 'No tienes acceso a todos los módulos requeridos.'
    
    def has_permission(self, request, view):
        """
        Verificar acceso a todos los módulos.
        
        Args:
            request: HttpRequest
            view: View con required_modules
            
        Returns:
            bool: True si tiene acceso a todos
        """
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        required_modules = getattr(view, 'required_modules', [])
        
        if not required_modules:
            return True
        
        # Verificar acceso a todos
        for module_code in required_modules:
            if not ModuleAccessService.has_module_access(request.user, module_code):
                self.message = f'No tienes acceso al módulo {module_code}.'
                return False
        
        return True
