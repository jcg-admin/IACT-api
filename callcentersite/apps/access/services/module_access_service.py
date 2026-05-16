"""
Access control services for the IACT API.
Provides RBAC helpers for function code resolution and navigation building.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.users.models import User


def get_user_function_codes(user: 'User') -> list[str]:
    """
    Returns the effective function codes for the given user.

    Delegates to User.get_functions() as the single source of truth.
    Superusers get all active function codes.
    """
    if user.is_superuser:
        from apps.access.models import Function
        return sorted(
            Function.objects.filter(is_active=True)
            .values_list('code', flat=True)
        )
    return user.get_functions()


def get_navigation_modules(user: 'User') -> list:
    """
    Return a list of NavigationItem objects for the modules the user can access.
    """
    from apps.access.models import Module
    from apps.core.navigation.builders import NavigationItem

    function_codes = get_user_function_codes(user)

    accessible_module_ids = set(
        Module.objects.filter(
            functions__code__in=function_codes,
            is_active=True,
        ).values_list('id', flat=True)
    )

    if user.is_superuser:
        top_modules = Module.objects.filter(
            parent__isnull=True,
            is_active=True,
        ).prefetch_related('children').order_by('order')
    else:
        top_modules = Module.objects.filter(
            parent__isnull=True,
            is_active=True,
        ).prefetch_related('children').order_by('order')

    items = []
    for module in top_modules:
        children = []
        for child in module.children.filter(is_active=True).order_by('order'):
            if user.is_superuser or child.id in accessible_module_ids:
                children.append(NavigationItem(
                    id=child.id,
                    name=child.name,
                    code=child.code,
                    icon=child.icon,
                    order=child.order,
                ))

        if user.is_superuser or module.id in accessible_module_ids or children:
            items.append(NavigationItem(
                id=module.id,
                name=module.name,
                code=module.code,
                icon=module.icon,
                order=module.order,
                children=children,
            ))

    return items


class ModuleAccessService:
    """
    Servicio de acceso a modulos para verificacion y navegacion.

    Metodos:
    - has_module_access: verifica si usuario tiene acceso a un modulo
    - get_user_modules: retorna modulos accesibles del usuario
    - get_user_module_tree: retorna arbol de modulos accesibles
    - get_module_hierarchy: retorna jerarquia completa de modulos
    """

    @staticmethod
    def has_module_access(user, module_code: str) -> bool:
        """
        Verifica si el usuario tiene acceso a un modulo especifico.
        Superuser tiene acceso a todo.
        """
        if user.is_superuser:
            return True
        from apps.access.models import Module, UserModuleAccess
        try:
            module = Module.objects.get(code=module_code, is_active=True)
        except Module.DoesNotExist:
            return False
        return UserModuleAccess.objects.filter(
            user=user, module=module, is_active=True
        ).exists()

    @staticmethod
    def get_user_modules(user):
        """Retorna los modulos activos accesibles por el usuario."""
        from apps.access.models import Module, UserModuleAccess
        if user.is_superuser:
            return Module.objects.filter(is_active=True).order_by('order')
        module_ids = UserModuleAccess.objects.filter(
            user=user, is_active=True
        ).values_list('module_id', flat=True)
        return Module.objects.filter(
            id__in=module_ids, is_active=True
        ).order_by('order')

    @staticmethod
    def get_user_module_tree(user):
        """
        Retorna los modulos de nivel raiz con sus hijos accesibles.
        Estructura: lista de modulos con atributo .children.
        """
        modules = ModuleAccessService.get_user_modules(user)
        module_ids = set(modules.values_list('id', flat=True))
        root_modules = modules.filter(parent__isnull=True).prefetch_related('children')
        result = []
        for mod in root_modules:
            accessible_children = [
                c for c in mod.children.filter(is_active=True).order_by('order')
                if user.is_superuser or c.id in module_ids
            ]
            mod._accessible_children = accessible_children
            result.append(mod)
        return result

    @staticmethod
    def get_module_hierarchy():
        """Retorna todos los modulos raiz con sus hijos (sin filtro de usuario)."""
        from apps.access.models import Module
        return Module.objects.filter(
            parent__isnull=True, is_active=True
        ).prefetch_related('children').order_by('order')

    @staticmethod
    def grant_module_access(user, module_code: str, granted_by, reason: str = ''):
        """
        Otorga acceso activo a un módulo.

        Args:
            user: User que recibirá acceso.
            module_code: código canónico del módulo.
            granted_by: User que concede el acceso.
            reason: justificación.

        Returns:
            UserModuleAccess: instancia creada o reactivada.
        """
        from django.utils import timezone
        from apps.access.models import Module, UserModuleAccess
        module = Module.objects.get(code=module_code)
        access, created = UserModuleAccess.objects.get_or_create(
            user=user,
            module=module,
            defaults={
                'granted_by': granted_by,
                'reason': reason,
                'granted_at': timezone.now(),
                'is_active': True,
            },
        )
        if not created and not access.is_active:
            access.is_active = True
            access.granted_by = granted_by
            access.reason = reason
            access.granted_at = timezone.now()
            access.save(update_fields=['is_active', 'granted_by', 'reason', 'granted_at'])
        return access

    @staticmethod
    def revoke_module_access(user, module_code: str, revoked_by) -> bool:
        """
        Revoca el acceso a un módulo.

        Returns:
            bool: True si se encontró y revocó, False si no tenía acceso activo.
        """
        from django.utils import timezone
        from apps.access.models import UserModuleAccess
        updated = UserModuleAccess.objects.filter(
            user=user,
            module__code=module_code,
            is_active=True,
        ).update(
            is_active=False,
            revoked_by=revoked_by,
            revoked_at=timezone.now(),
        )
        return updated > 0
