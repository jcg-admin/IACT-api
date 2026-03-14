"""
ViewSet para Profile (perfil del usuario autenticado).

CLEAN_CODE v3.0.1: ViewSet con responsabilidad única.
SOLID SRP: Solo gestión de perfil propio.

FASE 2 PARTE 5: ViewSets de apps/users/
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.users.serializers import (
    ProfileSerializer,
    UserSettingsSerializer,
    AvatarUploadSerializer,
)


class ProfileViewSet(viewsets.GenericViewSet):
    """
    ViewSet para gestión de perfil propio.
    
    Solo endpoints /me/ (usuario autenticado).
    NO requiere function_map (perfil propio, sin RBAC).
    
    Endpoints:
    - GET /api/profile/me/ - Ver perfil
    - PUT /api/profile/me/ - Actualizar perfil completo
    - PATCH /api/profile/me/ - Actualizar perfil parcial
    - GET /api/profile/me/settings/ - Ver settings
    - PUT /api/profile/me/settings/ - Actualizar settings
    - POST /api/profile/me/avatar/ - Subir avatar
    - DELETE /api/profile/me/avatar/ - Eliminar avatar
    
    Permissions:
    - IsAuthenticated: Solo usuarios autenticados
    - NO RequiresFunctionPermission (perfil propio)
    
    Example:
        # Ver perfil propio
        GET /api/profile/me/
        
        # Actualizar perfil
        PATCH /api/profile/me/
        {"bio": "Desarrollador Python", "department": "IT"}
        
        # Subir avatar
        POST /api/profile/me/avatar/
        FormData: {avatar: file}
    """
    
    permission_classes = [IsAuthenticated]
    # NO function_map: perfil propio no requiere RBAC
    
    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        """
        Ver/actualizar perfil propio.
        
        Endpoint: GET|PUT|PATCH /api/profile/me/
        Permission: IsAuthenticated (sin RBAC)
        
        GET - Ver perfil
        PUT/PATCH - Actualizar perfil
        
        Request body (PUT/PATCH):
        {
            "bio": "Desarrollador Python Senior",
            "department": "IT"
        }
        
        Args:
            request: HttpRequest
            
        Returns:
            Response: Profile data
        """
        user = request.user
        
        # Asegurar que existe profile (auto-creado vía signal)
        if not hasattr(user, 'profile'):
            from apps.users.models import UserProfile
            UserProfile.objects.create(user=user)
        
        profile = user.profile
        
        if request.method == 'GET':
            # Ver perfil
            serializer = ProfileSerializer(profile)
            return Response(serializer.data)
        
        else:
            # Actualizar perfil (PUT/PATCH)
            partial = request.method == 'PATCH'
            serializer = ProfileSerializer(
                profile,
                data=request.data,
                partial=partial
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
    
    @action(detail=False, methods=['get', 'put', 'patch'], url_path='me/settings')
    def settings(self, request):
        """
        Ver/actualizar settings propios.
        
        Endpoint: GET|PUT|PATCH /api/profile/me/settings/
        Permission: IsAuthenticated (sin RBAC)
        
        GET - Ver settings
        PUT/PATCH - Actualizar settings
        
        Request body (PUT/PATCH):
        {
            "language": "en",
            "notifications_enabled": false
        }
        
        Args:
            request: HttpRequest
            
        Returns:
            Response: Settings data
        """
        user = request.user
        
        # Asegurar que existe settings (auto-creado vía signal)
        if not hasattr(user, 'settings'):
            from apps.users.models import UserSettings
            UserSettings.objects.create(user=user)
        
        settings = user.settings
        
        if request.method == 'GET':
            # Ver settings
            serializer = UserSettingsSerializer(settings)
            return Response(serializer.data)
        
        else:
            # Actualizar settings (PUT/PATCH)
            partial = request.method == 'PATCH'
            serializer = UserSettingsSerializer(
                settings,
                data=request.data,
                partial=partial
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='me/avatar')
    def upload_avatar(self, request):
        """
        Subir avatar.
        
        Endpoint: POST /api/profile/me/avatar/
        Permission: IsAuthenticated (sin RBAC)
        
        Request: multipart/form-data
        {
            "avatar": <image file>
        }
        
        Validations:
        - Formatos: jpg, jpeg, png, gif
        - Tamaño máximo: 2MB
        
        Args:
            request: HttpRequest con file
            
        Returns:
            Response: User data con avatar actualizado
        """
        user = request.user
        
        serializer = AvatarUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Subir avatar (delega a ProfileService)
        serializer.save(instance=user)
        
        # Refrescar user
        user.refresh_from_db()
        
        # Retornar profile con avatar_url
        profile_serializer = ProfileSerializer(user.profile)
        return Response(profile_serializer.data)
    
    @action(detail=False, methods=['delete'], url_path='me/avatar')
    def remove_avatar(self, request):
        """
        Eliminar avatar.
        
        Endpoint: DELETE /api/profile/me/avatar/
        Permission: IsAuthenticated (sin RBAC)
        
        Args:
            request: HttpRequest
            
        Returns:
            Response: Confirmación
        """
        user = request.user
        
        # Eliminar avatar (delega a ProfileService)
        from apps.users.services.profile_service import ProfileService
        
        ProfileService().remove_avatar(user)
        
        return Response(
            {'detail': 'Avatar eliminado correctamente'},
            status=status.HTTP_204_NO_CONTENT
        )


# ============================================================================
# RESUMEN PROFILE VIEWSET
#
# ViewSet: ProfileViewSet
#
# Endpoints:
#   [SUCCESS] GET /api/profile/me/ - Ver perfil
#   [SUCCESS] PUT/PATCH /api/profile/me/ - Actualizar perfil
#   [SUCCESS] GET /api/profile/me/settings/ - Ver settings
#   [SUCCESS] PUT/PATCH /api/profile/me/settings/ - Actualizar settings
#   [SUCCESS] POST /api/profile/me/avatar/ - Subir avatar
#   [SUCCESS] DELETE /api/profile/me/avatar/ - Eliminar avatar
#
# Permissions:
#   [SUCCESS] IsAuthenticated (sin RBAC)
#   [ERROR] NO function_map (perfil propio)
#
# Features:
#   [SUCCESS] Solo /me/ endpoints (usuario autenticado)
#   [SUCCESS] Auto-crear profile/settings si no existen
#   [SUCCESS] Upload avatar con validación
#   [SUCCESS] Remove avatar
#
# Delegación:
#   [SUCCESS] ProfileSerializer -> ProfileService.update_profile()
#   [SUCCESS] AvatarUploadSerializer -> ProfileService.upload_avatar()
#   [SUCCESS] ProfileService.remove_avatar()
#
# Principios:
#   [SUCCESS] SRP: Solo gestión de perfil propio
#   [SUCCESS] DRY: Delegar a serializers/services
#   [SUCCESS] Clean Code: Nombres auto-documentados
#   [SUCCESS] No RBAC: Perfil propio no requiere permissions
# ============================================================================
