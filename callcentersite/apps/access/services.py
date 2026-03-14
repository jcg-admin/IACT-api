"""
Service para gestión de accesos a módulos.

Proporciona lógica de negocio para:
- Verificar accesos de usuarios
- Obtener módulos accesibles
- Gestionar jerarquía de módulos
"""
from typing import List, Optional
from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from .models import Module, UserModuleAccess

User = get_user_model()


class ModuleAccessService:
    """
    Service para gestión de accesos a módulos.
    
    Maneja la lógica de negocio de accesos considerando jerarquía.
    """
    
    @staticmethod
    def get_user_modules(user: User, include_inactive: bool = False) -> QuerySet:
        """
        Obtener módulos accesibles por usuario.
        
        Incluye módulos asignados directamente y todos sus descendientes.
        
        Args:
            user: Usuario
            include_inactive: Si True, incluye módulos inactivos
            
        Returns:
            QuerySet de Module accesibles
        """
        # Módulos directamente asignados y activos
        query = UserModuleAccess.objects.filter(
            user=user,
            is_active=True,
        )
        
        if not include_inactive:
            query = query.filter(module__is_active=True)
        
        direct_modules = Module.objects.filter(
            id__in=query.values_list('module_id', flat=True)
        )
        
        # Incluir todos los descendientes
        all_modules = set(direct_modules)
        for module in direct_modules:
            descendants = module.get_descendants()
            if include_inactive:
                all_modules.update(descendants)
            else:
                all_modules.update([d for d in descendants if d.is_active])
        
        # Retornar QuerySet
        module_ids = [m.id for m in all_modules]
        return Module.objects.filter(id__in=module_ids).order_by('order', 'code')
    
    @staticmethod
    def get_user_root_modules(user: User) -> QuerySet:
        """
        Obtener solo módulos raíz accesibles por usuario.
        
        Args:
            user: Usuario
            
        Returns:
            QuerySet de Module raíz (sin padre)
        """
        all_modules = ModuleAccessService.get_user_modules(user)
        return all_modules.filter(parent__isnull=True)
    
    @staticmethod
    def has_module_access(user: User, module_code: str) -> bool:
        """
        Verificar si usuario tiene acceso a un módulo.
        
        Considera jerarquía: acceso a padre implica acceso a hijos.
        
        Args:
            user: Usuario
            module_code: Código del módulo a verificar
            
        Returns:
            bool: True si tiene acceso
        """
        try:
            module = Module.objects.get(code=module_code, is_active=True)
        except Module.DoesNotExist:
            return False
        
        # Verificar acceso directo
        if UserModuleAccess.objects.filter(
            user=user,
            module=module,
            is_active=True,
        ).exists():
            return True
        
        # Verificar acceso a ancestros (padre tiene acceso a hijos)
        ancestors = module.get_ancestors()
        if not ancestors:
            return False
        
        return UserModuleAccess.objects.filter(
            user=user,
            module__in=ancestors,
            is_active=True,
        ).exists()
    
    @staticmethod
    def grant_module_access(
        user: User,
        module_code: str,
        granted_by: User,
        reason: str = ""
    ) -> UserModuleAccess:
        """
        Otorgar acceso a módulo.
        
        Args:
            user: Usuario a quien se otorga acceso
            module_code: Código del módulo
            granted_by: Usuario que otorga el acceso
            reason: Razón del otorgamiento
            
        Returns:
            UserModuleAccess creado o existente
            
        Raises:
            Module.DoesNotExist: Si módulo no existe
        """
        module = Module.objects.get(code=module_code)
        
        # Verificar si ya existe
        access, created = UserModuleAccess.objects.get_or_create(
            user=user,
            module=module,
            defaults={
                'granted_by': granted_by,
                'reason': reason,
                'is_active': True,
            }
        )
        
        # Si existía pero estaba inactivo, reactivarlo
        if not created and not access.is_active:
            access.is_active = True
            access.granted_by = granted_by
            access.reason = reason
            access.revoked_at = None
            access.revoked_by = None
            access.save()
        
        return access
    
    @staticmethod
    def revoke_module_access(
        user: User,
        module_code: str,
        revoked_by: User
    ) -> Optional[UserModuleAccess]:
        """
        Revocar acceso a módulo.
        
        Args:
            user: Usuario a quien se revoca acceso
            module_code: Código del módulo
            revoked_by: Usuario que revoca el acceso
            
        Returns:
            UserModuleAccess revocado o None si no existía
        """
        from django.utils import timezone
        
        try:
            access = UserModuleAccess.objects.get(
                user=user,
                module__code=module_code,
                is_active=True,
            )
            
            access.is_active = False
            access.revoked_at = timezone.now()
            access.revoked_by = revoked_by
            access.save()
            
            return access
        except UserModuleAccess.DoesNotExist:
            return None
    
    @staticmethod
    def get_module_hierarchy() -> List[dict]:
        """
        Obtener jerarquía completa de módulos.
        
        Returns:
            Lista de módulos raíz con sus hijos anidados
        """
        def build_tree(module):
            """Construir árbol recursivamente."""
            return {
                'id': module.id,
                'code': module.code,
                'name': module.name,
                'description': module.description,
                'icon': module.icon,
                'url_path': module.url_path,
                'order': module.order,
                'is_active': module.is_active,
                'level': module.get_level(),
                'children': [
                    build_tree(child)
                    for child in module.children.filter(is_active=True).order_by('order', 'code')
                ],
            }
        
        # Obtener módulos raíz
        root_modules = Module.objects.filter(
            parent__isnull=True,
            is_active=True,
        ).order_by('order', 'code')
        
        return [build_tree(module) for module in root_modules]
    
    @staticmethod
    def get_user_module_tree(user: User) -> List[dict]:
        """
        Obtener árbol de módulos accesibles por usuario.
        
        Args:
            user: Usuario
            
        Returns:
            Lista de módulos raíz accesibles con sus hijos
        """
        accessible_modules = ModuleAccessService.get_user_modules(user)
        accessible_ids = set(accessible_modules.values_list('id', flat=True))
        
        def build_tree(module):
            """Construir árbol solo con módulos accesibles."""
            children = [
                build_tree(child)
                for child in module.children.filter(
                    id__in=accessible_ids,
                    is_active=True,
                ).order_by('order', 'code')
            ]
            
            return {
                'id': module.id,
                'code': module.code,
                'name': module.name,
                'description': module.description,
                'icon': module.icon,
                'url_path': module.url_path,
                'order': module.order,
                'level': module.get_level(),
                'children': children,
            }
        
        # Solo módulos raíz accesibles
        root_modules = accessible_modules.filter(parent__isnull=True).order_by('order', 'code')
        
        return [build_tree(module) for module in root_modules]
