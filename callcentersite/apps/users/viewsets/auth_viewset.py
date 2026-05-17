"""
ViewSet para autenticación y gestión de password.

CLEAN_CODE v3.0.1: ViewSet con responsabilidad única.
SOLID SRP: Solo gestión de password.

NOTA: Login/Logout están en apps/authentication (no aquí).

FASE 2 PARTE 5: ViewSets de apps/users/
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.users.serializers import PasswordChangeSerializer


class AuthViewSet(viewsets.GenericViewSet):
    """
    ViewSet para gestión de password.

    Solo endpoints de cambio de password.
    Login/Logout están en apps/authentication.

    Endpoints:
    - POST /api/auth/change-password/ - Cambiar password

    Permissions:
    - IsAuthenticated: Solo usuarios autenticados
    - NO RequiresFunctionPermission (password propio)

    NOTA:
    Login/Logout/Reset están en apps/authentication:
    - POST /api/auth/login/
    - POST /api/auth/logout/
    - POST /api/auth/password-reset/

    Example:
        # Cambiar password
        POST /api/auth/change-password/
        {
            "old_password": "OldPass123!",
            "new_password": "NewPass456!",
            "new_password_confirm": "NewPass456!"
        }
    """

    permission_classes = [IsAuthenticated]
    # NO function_map: password propio no requiere RBAC

    @action(detail=False, methods=['post'], url_path='change-password')
    def change_password(self, request):
        """
        Cambiar password del usuario autenticado.

        Endpoint: POST /api/auth/change-password/
        Permission: IsAuthenticated (sin RBAC)

        Request body:
        {
            "old_password": "OldPass123!",
            "new_password": "NewPass456!",
            "new_password_confirm": "NewPass456!"
        }

        Validations:
        - old_password correcto
        - new_password != old_password
        - new_password fuerte (8 chars, mayús/minús/número/especial)
        - new_password == new_password_confirm

        Args:
            request: HttpRequest

        Returns:
            Response: Confirmación de cambio
        """
        user = request.user

        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Cambiar password (delega a PasswordService)
        serializer.save(user=user)

        return Response(
            {'detail': 'Password cambiado correctamente'},
            status=status.HTTP_200_OK
        )


# ============================================================================
# RESUMEN AUTH VIEWSET
#
# ViewSet: AuthViewSet
#
# Endpoints:
#   [SUCCESS] POST /api/auth/change-password/ - Cambiar password
#
# NO incluidos (apps/authentication):
#   [ERROR] POST /api/auth/login/ -> apps/authentication
#   [ERROR] POST /api/auth/logout/ -> apps/authentication
#   [ERROR] POST /api/auth/password-reset/ -> apps/authentication
#
# Permissions:
#   [SUCCESS] IsAuthenticated (sin RBAC)
#   [ERROR] NO function_map (password propio)
#
# Features:
#   [SUCCESS] Cambiar password propio
#   [SUCCESS] Validaciones completas
#
# Delegación:
#   [SUCCESS] PasswordChangeSerializer -> PasswordService.change_password()
#
# Principios:
#   [SUCCESS] SRP: Solo gestión de password
#   [SUCCESS] DRY: Delegar a serializers/services
#   [SUCCESS] Clean Code: Nombres auto-documentados
#   [SUCCESS] Separation: Login/Logout en apps/authentication
# ============================================================================
