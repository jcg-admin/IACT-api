"""
ViewSets para apps/users/.

CLEAN_CODE v3.0.1: Imports organizados por módulo.
FASE 2 PARTE 5: 4 ViewSets implementados.

Estructura:
== user_viewset.py - CRUD usuarios con RBAC
== profile_viewset.py - Gestión perfil propio
== auth_viewset.py - Cambio de password
== session_viewset.py - Auditoría sesiones
"""

from apps.users.viewsets.user_viewset import UserViewSet
from apps.users.viewsets.profile_viewset import ProfileViewSet
from apps.users.viewsets.auth_viewset import AuthViewSet
from apps.users.viewsets.session_viewset import SessionHistoryViewSet


__all__ = [
    'UserViewSet',
    'ProfileViewSet',
    'AuthViewSet',
    'SessionHistoryViewSet',
]


# ============================================================================
# RESUMEN VIEWSETS
#
# Total: 4 ViewSets
#
# UserViewSet:
#   [SUCCESS] CRUD completo de usuarios
#   [SUCCESS] Permissions vía function_map
#   [SUCCESS] Custom actions: activate, deactivate
#   [SUCCESS] Soft delete
#
# ProfileViewSet:
#   [SUCCESS] Gestión de perfil propio (/me/)
#   [SUCCESS] Settings (language, notifications)
#   [SUCCESS] Avatar (upload, remove)
#   [SUCCESS] Sin RBAC (perfil propio)
#
# AuthViewSet:
#   [SUCCESS] Cambio de password
#   [SUCCESS] Sin RBAC (password propio)
#   [ERROR] NO Login/Logout (apps/authentication)
#
# SessionHistoryViewSet:
#   [SUCCESS] Auditoría de sesiones
#   [SUCCESS] Read-only
#   [SUCCESS] Permissions vía function_map
#   [SUCCESS] Queryset por rol (staff vs usuario)
#
# Namespaces Django usados:
#   [SUCCESS] 'users.view'
#   [SUCCESS] 'users.create'
#   [SUCCESS] 'users.edit'
#   [SUCCESS] 'users.delete'
#   [SUCCESS] 'sessions.view'
#
# Permissions:
#   [SUCCESS] RequiresFunctionPermission (apps/core)
#   [SUCCESS] IsAuthenticated
#   [SUCCESS] function_map para RBAC
#
# Scope apps/users/:
#   [SUCCESS] SOLO gestión de usuarios
#   [ERROR] NO gestión de RBAC (apps/access)
#   [ERROR] NO Login/Logout (apps/authentication)
#
# FASE 2 PARTE 5: [SUCCESS] COMPLETADA
# ============================================================================
