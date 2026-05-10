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
    Return a list of function codes that the given user has access to.
    Combines direct permissions. Superusers get all functions.
    """
    if user.is_superuser:
        from apps.access.models import Function
        return list(Function.objects.filter(is_active=True).values_list('code', flat=True))

    from apps.access.models import UserPermission
    codes = UserPermission.objects.filter(
        user=user,
        function__is_active=True,
        function__module__is_active=True,
    ).values_list('function__code', flat=True)

    return list(codes)


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
