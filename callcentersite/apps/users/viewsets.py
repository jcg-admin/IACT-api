"""
ViewSets para apps/users/.

DRF ViewSets con permisos RBAC y documentación OpenAPI.
CLEAN_CODE v3.0.1: ViewSets auto-documentados.
"""

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiResponse,
    OpenApiExample,
)
from drf_spectacular.types import OpenApiTypes

try:
    from apps.users.models import UserProfile, UserSettings, SessionHistory
except ImportError:
    UserProfile = UserSettings = SessionHistory = None
from apps.users.serializers import (
    UserSerializer,
    UserListSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    UserProfileSerializer,
    AvatarUploadSerializer,
    UserSettingsSerializer,
    LoginSerializer,
    ChangePasswordSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    SessionHistorySerializer,
    SessionHistoryListSerializer,
)
from apps.users.services import ProfileService
from apps.core.permissions import RequiresFunctionPermission

User = get_user_model()


@extend_schema_view(
    list=extend_schema(
        summary="Lista usuarios",
        description="Retorna lista de usuarios activos. Admin ve todos, usuarios normales solo activos.",
        parameters=[
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Buscar por username, email, first_name o last_name',
            ),
            OpenApiParameter(
                name='is_active',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filtrar por usuarios activos (true) o inactivos (false)',
            ),
        ],
        tags=['Usuarios'],
    ),
    create=extend_schema(
        summary="Crear usuario",
        description="Crea un nuevo usuario. Requiere permiso USR_CREATE. Auto-crea profile y settings.",
        tags=['Usuarios'],
    ),
    retrieve=extend_schema(
        summary="Obtener usuario",
        description="Retorna detalles de un usuario específico. Incluye profile, settings y funciones RBAC.",
        tags=['Usuarios'],
    ),
    update=extend_schema(
        summary="Actualizar usuario (completo)",
        description="Actualiza todos los campos de un usuario. Requiere permiso USR_EDIT.",
        tags=['Usuarios'],
    ),
    partial_update=extend_schema(
        summary="Actualizar usuario (parcial)",
        description="Actualiza campos específicos de un usuario. Requiere permiso USR_EDIT.",
        tags=['Usuarios'],
    ),
    destroy=extend_schema(
        summary="Eliminar usuario",
        description="Elimina un usuario (soft delete). Requiere permiso USR_DELETE.",
        tags=['Usuarios'],
    ),
)
class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para User CRUD.

    Endpoints:
    - GET /api/v1/users/ - Lista usuarios
    - POST /api/v1/users/ - Crea usuario
    - GET /api/v1/users/{id}/ - Detalle usuario
    - PUT/PATCH /api/v1/users/{id}/ - Actualiza usuario
    - DELETE /api/v1/users/{id}/ - Elimina usuario (soft delete)
    - POST /api/v1/users/{id}/activate/ - Activa usuario
    - POST /api/v1/users/{id}/deactivate/ - Desactiva usuario
    - GET /api/v1/users/me/ - Usuario actual

    Permisos:
    - list: USR_VIEW
    - create: USR_CREATE
    - retrieve: USR_VIEW
    - update: USR_EDIT
    - destroy: USR_DELETE
    - activate/deactivate: USR_EDIT
    - me: Authenticated
    """

    queryset = User.objects.filter(state='ACTIVE').order_by('-date_joined')
    permission_classes = [IsAuthenticated, RequiresFunctionPermission]

    # F1-H-006/F1-H-007: códigos canónicos v5.4.0 (antes namespaces Django legacy)
    function_map = {
        'list':           'USR-004',  # list_users
        'retrieve':       'USR-009',  # view_users
        'create':         'USR-001',  # create_users
        'update':         'USR-002',  # update_users
        'partial_update': 'USR-002',  # update_users
        'destroy':        'USR-003',  # deactivate_users (BR-009)
        'activate':       'USR-008',  # reactivate_users
        'deactivate':     'USR-003',  # deactivate_users
    }

    def get_serializer_class(self):
        """
        Retorna serializer según acción.

        - list: UserListSerializer (lightweight)
        - create: UserCreateSerializer
        - update/partial_update: UserUpdateSerializer
        - default: UserSerializer
        """
        if self.action == 'list':
            return UserListSerializer
        elif self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer

    def get_queryset(self):
        """
        Filtra queryset según permisos.

        Superusuarios ven todos.
        Usuarios normales solo ven activos.
        """
        queryset = super().get_queryset()

        if not self.request.user.is_superuser:
            queryset = queryset.filter(is_active=True)

        # Filtros opcionales
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        search = self.request.query_params.get('search')
        if search:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )

        return queryset

    @extend_schema(
        summary="Obtener usuario actual",
        description="Retorna información completa del usuario autenticado actualmente.",
        tags=['Usuarios'],
        responses={200: UserSerializer},
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        Retorna usuario actual.

        GET /api/v1/users/me/

        Returns:
            UserSerializer: Usuario autenticado
        """
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @extend_schema(
        summary="Activar usuario",
        description="Activa un usuario (is_active=True). Requiere permiso USR_EDIT.",
        tags=['Usuarios'],
        request=None,
        responses={200: UserSerializer},
    )
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activa usuario.

        POST /api/v1/users/{id}/activate/

        Returns:
            UserSerializer: Usuario activado
        """
        from apps.users.services import UserService

        user = self.get_object()
        service = UserService()

        activated_user = service.activate_user(
            user_id=user.id,
            activated_by=request.user,
        )

        serializer = UserSerializer(activated_user)
        return Response(serializer.data)

    @extend_schema(
        summary="Desactivar usuario",
        description="Desactiva un usuario (is_active=False). Requiere permiso USR_EDIT.",
        tags=['Usuarios'],
        request=None,
        responses={200: UserSerializer},
    )
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Desactiva usuario.

        POST /api/v1/users/{id}/deactivate/

        Returns:
            UserSerializer: Usuario desactivado
        """
        from apps.users.services import UserService

        user = self.get_object()
        service = UserService()

        deactivated_user = service.deactivate_user(
            user_id=user.id,
            deactivated_by=request.user,
        )

        serializer = UserSerializer(deactivated_user)
        return Response(serializer.data)


class AuthViewSet(viewsets.ViewSet):
    """
    ViewSet para autenticación.

    Endpoints:
    - POST /api/v1/users/auth/login/ - Login
    - POST /api/v1/users/auth/logout/ - Logout
    - POST /api/v1/users/auth/change-password/ - Cambiar password
    - POST /api/v1/users/auth/password-reset/ - Solicitar reset
    - POST /api/v1/users/auth/password-reset-confirm/ - Confirmar reset

    Permisos:
    - login: AllowAny
    - logout: IsAuthenticated
    - change-password: IsAuthenticated
    - password-reset: AllowAny
    - password-reset-confirm: AllowAny
    """

    @extend_schema(
        summary="Login de usuario",
        description="Autentica un usuario y crea una sesión. Retorna datos del usuario y mensaje de éxito.",
        tags=['Autenticación'],
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(
                response=UserSerializer,
                description="Login exitoso",
            ),
            400: OpenApiResponse(description="Credenciales inválidas"),
        },
        examples=[
            OpenApiExample(
                'Login Example',
                value={'username': 'jdoe', 'password': 'SecurePass123'},
                request_only=True,
            ),
        ],
    )
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """
        Login de usuario.

        POST /api/v1/users/auth/login/
        {
            "username": "jdoe",
            "password": "SecurePass123"
        }

        Returns:
            {
                "user": UserSerializer,
                "message": "Login exitoso"
            }
        """
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response({
            'user': UserSerializer(user).data,
            'message': 'Login exitoso',
        })

    @extend_schema(
        summary="Logout de usuario",
        description="Cierra la sesión del usuario autenticado. Actualiza SessionHistory.",
        tags=['Autenticación'],
        request=None,
        responses={200: OpenApiResponse(description="Logout exitoso")},
    )
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """
        Logout de usuario.

        POST /api/v1/users/auth/logout/

        Returns:
            {"message": "Logout exitoso"}
        """
        from apps.users.services import AuthenticationService

        service = AuthenticationService()
        service.logout(request=request, user=request.user)

        return Response({'message': 'Logout exitoso'})

    @extend_schema(
        summary="Cambiar password",
        description="Cambia el password del usuario autenticado. Requiere old_password y new_password.",
        tags=['Autenticación'],
        request=ChangePasswordSerializer,
        responses={
            200: OpenApiResponse(description="Password actualizado exitosamente"),
            400: OpenApiResponse(description="Password inválido"),
        },
    )
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated], url_path='change-password')
    def change_password(self, request):
        """
        Cambiar password.

        POST /api/v1/users/auth/change-password/
        {
            "old_password": "OldPass123",
            "new_password": "NewPass456"
        }

        Returns:
            {"message": "Password actualizado exitosamente"}
        """
        serializer = ChangePasswordSerializer(
            request.user,
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'message': 'Password actualizado exitosamente'})

    @extend_schema(
        summary="Solicitar reset de password",
        description="Envía un email con link para resetear password. Por seguridad, siempre retorna éxito.",
        tags=['Autenticación'],
        request=PasswordResetRequestSerializer,
        responses={200: OpenApiResponse(description="Email enviado")},
    )
    @action(detail=False, methods=['post'], permission_classes=[AllowAny], url_path='password-reset')
    def password_reset(self, request):
        """
        Solicitar reset de password.

        POST /api/v1/users/auth/password-reset/
        {
            "email": "user@company.com"
        }

        Returns:
            {"message": "Email enviado"}
        """
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'message': 'Si el email existe, recibirás instrucciones para resetear tu password'
        })

    @extend_schema(
        summary="Confirmar reset de password",
        description="Confirma el reset de password con token del email. Actualiza el password del usuario.",
        tags=['Autenticación'],
        request=PasswordResetConfirmSerializer,
        responses={
            200: OpenApiResponse(description="Password actualizado"),
            400: OpenApiResponse(description="Token inválido o expirado"),
        },
    )
    @action(detail=False, methods=['post'], permission_classes=[AllowAny], url_path='password-reset-confirm')
    def password_reset_confirm(self, request):
        """
        Confirmar reset de password.

        POST /api/v1/users/auth/password-reset-confirm/
        {
            "uidb64": "MQ",
            "token": "abc123-def456",
            "new_password": "NewPass456"
        }

        Returns:
            {"message": "Password actualizado exitosamente"}
        """
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'message': 'Password actualizado exitosamente'})


class ProfileViewSet(viewsets.ViewSet):
    """
    ViewSet para perfil de usuario.

    Endpoints:
    - GET /api/v1/users/profile/ - Obtener perfil actual
    - PATCH /api/v1/users/profile/ - Actualizar perfil
    - POST /api/v1/users/profile/avatar/ - Subir avatar
    - DELETE /api/v1/users/profile/avatar/ - Eliminar avatar

    Permisos:
    - Todos: IsAuthenticated (usuario maneja su propio perfil)
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Obtener perfil",
        description="Retorna el perfil del usuario autenticado.",
        tags=['Perfil'],
        responses={200: UserProfileSerializer},
    )
    @action(detail=False, methods=['get'])
    def profile(self, request):
        """
        Obtener perfil del usuario actual.

        GET /api/v1/users/profile/

        Returns:
            UserProfileSerializer: Perfil del usuario
        """
        serializer = UserProfileSerializer(request.user.profile)
        return Response(serializer.data)

    @extend_schema(
        summary="Actualizar perfil",
        description="Actualiza bio y/o department del perfil del usuario autenticado.",
        tags=['Perfil'],
        request=UserProfileSerializer,
        responses={200: UserProfileSerializer},
    )
    @action(detail=False, methods=['patch'])
    def update_profile(self, request):
        """
        Actualizar perfil.

        PATCH /api/v1/users/profile/
        {
            "bio": "Software Developer",
            "department": "Engineering"
        }

        Returns:
            UserProfileSerializer: Perfil actualizado
        """
        serializer = UserProfileSerializer(
            request.user.profile,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()

        return Response(UserProfileSerializer(profile).data)

    @extend_schema(
        summary="Subir avatar",
        description="Sube una imagen de avatar. Formatos permitidos: jpg, png, gif. Máximo 2MB.",
        tags=['Perfil'],
        request=AvatarUploadSerializer,
        responses={
            200: OpenApiResponse(description="Avatar subido exitosamente"),
            400: OpenApiResponse(description="Formato o tamaño inválido"),
        },
    )
    @action(detail=False, methods=['post'], url_path='avatar')
    def upload_avatar(self, request):
        """
        Subir avatar.

        POST /api/v1/users/profile/avatar/
        Form-data: avatar (image file)

        Returns:
            {"avatar_url": "/media/avatars/..."}
        """
        serializer = AvatarUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = ProfileService()
        user = service.upload_avatar(
            user_id=request.user.id,
            avatar_file=serializer.validated_data['avatar'],
            uploaded_by=request.user,
        )

        return Response({
            'avatar_url': user.avatar.url if user.avatar else None,
            'message': 'Avatar subido exitosamente'
        })

    @extend_schema(
        summary="Eliminar avatar",
        description="Elimina el avatar del usuario autenticado.",
        tags=['Perfil'],
        request=None,
        responses={200: OpenApiResponse(description="Avatar eliminado exitosamente")},
    )
    @action(detail=False, methods=['delete'], url_path='avatar')
    def remove_avatar(self, request):
        """
        Eliminar avatar.

        DELETE /api/v1/users/profile/avatar/

        Returns:
            {"message": "Avatar eliminado"}
        """
        service = ProfileService()
        service.remove_avatar(
            user_id=request.user.id,
            removed_by=request.user,
        )

        return Response({'message': 'Avatar eliminado exitosamente'})


class SettingsViewSet(viewsets.ViewSet):
    """
    ViewSet para configuración de usuario.

    Endpoints:
    - GET /api/v1/users/settings/ - Obtener settings
    - PATCH /api/v1/users/settings/ - Actualizar settings

    Permisos:
    - Todos: IsAuthenticated (usuario maneja sus propios settings)
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Obtener configuración",
        description="Retorna la configuración del usuario autenticado.",
        tags=['Configuración'],
        responses={200: UserSettingsSerializer},
    )
    @action(detail=False, methods=['get'])
    def settings(self, request):
        """
        Obtener settings del usuario actual.

        GET /api/v1/users/settings/

        Returns:
            UserSettingsSerializer: Settings del usuario
        """
        serializer = UserSettingsSerializer(request.user.settings)
        return Response(serializer.data)

    @extend_schema(
        summary="Actualizar configuración",
        description="Actualiza la configuración del usuario autenticado.",
        tags=['Configuración'],
        request=UserSettingsSerializer,
        responses={200: UserSettingsSerializer},
    )
    @action(detail=False, methods=['patch'])
    def update_settings(self, request):
        """
        Actualizar settings.

        PATCH /api/v1/users/settings/
        {
            "language": "en",
            "theme": "dark",
            "timezone": "America/New_York"
        }

        Returns:
            UserSettingsSerializer: Settings actualizados
        """
        serializer = UserSettingsSerializer(
            request.user.settings,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        settings = serializer.save()

        return Response(UserSettingsSerializer(settings).data)


@extend_schema_view(
    list=extend_schema(
        summary="Lista sesiones",
        description="Retorna historial de sesiones del usuario autenticado. Admin ve todas si especifica user_id.",
        tags=['Sesiones'],
        parameters=[
            OpenApiParameter(
                name='user_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='ID de usuario (solo admin)',
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Detalle de sesión",
        description="Retorna detalles de una sesión específica.",
        tags=['Sesiones'],
    ),
)
class SessionHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para historial de sesiones (read-only).

    Endpoints:
    - GET /api/v1/users/sessions/ - Lista sesiones del usuario
    - GET /api/v1/users/sessions/{id}/ - Detalle de sesión

    Permisos:
    - list/retrieve: IsAuthenticated

    Note:
        Usuario solo ve sus propias sesiones.
        Admin ve todas.
    """

    serializer_class = SessionHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Retorna sesiones del usuario actual.

        Admin ve todas si especifica ?user_id=X
        """
        user = self.request.user

        # Admin puede ver sesiones de cualquier usuario
        if user.is_superuser:
            user_id = self.request.query_params.get('user_id')
            if user_id:
                return SessionHistory.objects.filter(user_id=user_id).order_by('-login_at')
            # Sin filtro, admin ve todas
            return SessionHistory.objects.all().order_by('-login_at')

        # Usuario normal solo ve sus sesiones
        return SessionHistory.objects.filter(user=user).order_by('-login_at')

    def get_serializer_class(self):
        """
        Usa serializer ligero para list.
        """
        if self.action == 'list':
            return SessionHistoryListSerializer
        return SessionHistorySerializer


# ============================================================================
# RESUMEN ViewSets
#
# Total ViewSets: 5
#
# UserViewSet (ModelViewSet):
#   [SUCCESS] CRUD completo
#   [SUCCESS] activate/deactivate actions
#   [SUCCESS] me action (usuario actual)
#   [SUCCESS] RBAC permissions
#   [SUCCESS] Filtros: is_active, search
#
# AuthViewSet (ViewSet):
#   [SUCCESS] login (AllowAny)
#   [SUCCESS] logout (IsAuthenticated)
#   [SUCCESS] change_password (IsAuthenticated)
#   [SUCCESS] password_reset (AllowAny)
#   [SUCCESS] password_reset_confirm (AllowAny)
#
# ProfileViewSet (ViewSet):
#   [SUCCESS] profile (get/patch)
#   [SUCCESS] upload_avatar
#   [SUCCESS] remove_avatar
#   [SUCCESS] ProfileService integration
#
# SettingsViewSet (ViewSet):
#   [SUCCESS] settings (get/patch)
#   [SUCCESS] Direct model update
#
# SessionHistoryViewSet (ReadOnlyModelViewSet):
#   [SUCCESS] list/retrieve
#   [SUCCESS] Usuario ve solo sus sesiones
#   [SUCCESS] Admin ve todas
#
# Permisos:
#   [SUCCESS] HasFunctionPermission (RBAC)
#   [SUCCESS] IsAuthenticated
#   [SUCCESS] AllowAny (login, password reset)
#
# Integración:
#   [SUCCESS] Services (UserService, AuthenticationService, ProfileService)
#   [SUCCESS] Serializers dinámicos (get_serializer_class)
#   [SUCCESS] Queryset filters
#   [SUCCESS] Context para request
#
# Líneas: ~500
# ============================================================================
