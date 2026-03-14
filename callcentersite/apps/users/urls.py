"""
URLs para apps/users/.

CLEAN_CODE v3.0.1: URLs organizadas con routers DRF.
FASE 2 PARTE 5: Routing de ViewSets.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.users.viewsets import (
    UserViewSet,
    ProfileViewSet,
    AuthViewSet,
    SessionHistoryViewSet,
)


# Router principal
router = DefaultRouter()

# Registrar ViewSets
router.register(r'users', UserViewSet, basename='user')
router.register(r'profile', ProfileViewSet, basename='profile')
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'sessions', SessionHistoryViewSet, basename='session')


app_name = 'users'

urlpatterns = [
    path('', include(router.urls)),
]


# ============================================================================
# ENDPOINTS GENERADOS
#
# UserViewSet (/api/users/):
#   GET    /api/users/                  - Listar usuarios (users.view)
#   POST   /api/users/                  - Crear usuario (users.create)
#   GET    /api/users/{id}/             - Detalle usuario (users.view)
#   PUT    /api/users/{id}/             - Actualizar completo (users.edit)
#   PATCH  /api/users/{id}/             - Actualizar parcial (users.edit)
#   DELETE /api/users/{id}/             - Soft delete (users.delete)
#   POST   /api/users/{id}/activate/    - Activar usuario (users.edit)
#   POST   /api/users/{id}/deactivate/  - Desactivar usuario (users.edit)
#
# ProfileViewSet (/api/profile/):
#   GET    /api/profile/me/             - Ver perfil propio
#   PUT    /api/profile/me/             - Actualizar perfil completo
#   PATCH  /api/profile/me/             - Actualizar perfil parcial
#   GET    /api/profile/me/settings/    - Ver settings
#   PUT    /api/profile/me/settings/    - Actualizar settings completo
#   PATCH  /api/profile/me/settings/    - Actualizar settings parcial
#   POST   /api/profile/me/avatar/      - Subir avatar
#   DELETE /api/profile/me/avatar/      - Eliminar avatar
#
# AuthViewSet (/api/auth/):
#   POST   /api/auth/change-password/   - Cambiar password
#
# SessionHistoryViewSet (/api/sessions/):
#   GET    /api/sessions/               - Listar sesiones (sessions.view)
#   GET    /api/sessions/{id}/          - Detalle sesión (sessions.view)
#
# Total endpoints: 18
#
# Namespaces Django requeridos:
#   - users.view      (listar, detalle usuarios)
#   - users.create    (crear usuario)
#   - users.edit      (actualizar, activar, desactivar)
#   - users.delete    (soft delete)
#   - sessions.view   (listar, detalle sesiones)
#
# Permissions:
#   - UserViewSet: RequiresFunctionPermission + function_map
#   - ProfileViewSet: IsAuthenticated (sin RBAC)
#   - AuthViewSet: IsAuthenticated (sin RBAC)
#   - SessionHistoryViewSet: RequiresFunctionPermission + function_map
#
# Notas:
#   - Todos los endpoints bajo /api/ (configurado en project urls.py)
#   - Login/Logout en apps/authentication (no aquí)
#   - RBAC management en apps/access (no aquí)
# ============================================================================
