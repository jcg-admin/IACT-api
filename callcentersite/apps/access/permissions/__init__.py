"""
Custom permissions para access app.

RBAC v6.0.0:
- HasFunction: Permission usando namespaces Django
- Module permissions: Sistema de módulos jerárquicos (legacy)
"""

from .function_permissions import HasFunction

# Module permissions comentadas temporalmente hasta implementar ModuleAccessService
# from .module_permissions import (
#     HasModuleAccess,
#     HasAnyModuleAccess,
#     HasAllModuleAccess,
# )

__all__ = [
    'HasFunction',
    # 'HasModuleAccess',
    # 'HasAnyModuleAccess',
    # 'HasAllModuleAccess',
]
