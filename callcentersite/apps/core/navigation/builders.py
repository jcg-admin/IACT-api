"""
Navigation builders for the IACT API v3.0.0.
Builds user-specific navigation menus based on RBAC permissions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.users.models import User


@dataclass
class NavigationItem:
    """Represents a single navigation item (module or sub-module)."""
    id: int
    name: str
    code: str
    icon: str = ''
    url: str = ''
    order: int = 0
    children: list['NavigationItem'] = field(default_factory=list)

    def to_dict(self) -> dict:
        data = {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'icon': self.icon,
            'url': self.url,
            'order': self.order,
        }
        if self.children:
            data['children'] = [child.to_dict() for child in self.children]
        return data


class NavigationBuilder:
    """
    Builds the navigation menu for a given user based on their RBAC permissions.
    """

    def __init__(self, user: 'User'):
        self.user = user
        self._function_codes: list[str] | None = None

    @property
    def function_codes(self) -> list[str]:
        if self._function_codes is None:
            self._function_codes = self.user.get_functions()
        return self._function_codes

    def build(self) -> list[dict]:
        """Build and return the navigation menu as a list of dicts."""
        from apps.access.services import get_navigation_modules
        modules = get_navigation_modules(self.user)
        return [item.to_dict() for item in modules]

    @classmethod
    def for_user(cls, user: 'User') -> list[dict]:
        """Convenience class method."""
        return cls(user).build()
