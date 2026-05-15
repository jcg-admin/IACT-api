"""
apps/users/urls.py

URLs de gestión de usuarios — FASE 0 + FASE 2.

Hallazgo B-04 (FASE 2):
  EliminateUserView.delete() no estaba registrada. La ruta PATCH /api/users/{id}/
  solo aceptaba PATCH, devolviendo 405 para DELETE. Se resuelve con
  UserDetailView que despacha PATCH → ModifyUserView y DELETE → EliminateUserView.
"""
from django.urls import path, include
from drf_spectacular.utils import extend_schema_view
from rest_framework.routers import DefaultRouter

from apps.users.viewsets import UserViewSet
from apps.users.viewsets.user_viewset import UserViewSet as CanonicalUserViewSet
from apps.users.create_user_view import CreateUserView
from apps.users.modify_user_view import ModifyUserView, EliminateUserView
from apps.authentication.reset_password_view import ResetPasswordView

router = DefaultRouter()
router.register(r'', UserViewSet, basename='user')

app_name = 'users'


class UserDetailDispatcher:
    """
    B-04: Despacha PATCH → ModifyUserView y DELETE → EliminateUserView
    en el mismo path /api/users/{user_id}/.

    Esto evita registrar dos vistas en el mismo path (Django no lo soporta
    directamente) sin necesidad de un router personalizado.
    """
    @staticmethod
    def as_view():
        from rest_framework.views import APIView
        from rest_framework.response import Response
        from rest_framework.permissions import IsAuthenticated

        patch_view  = ModifyUserView.as_view()
        delete_view = EliminateUserView.as_view()

        from drf_spectacular.utils import extend_schema, OpenApiResponse

        @extend_schema_view(
            patch=extend_schema(
                operation_id='user_modify',
                summary='UC_USR_03 — Modificar usuario (PATCH parcial)',
                tags=['Usuarios'],
                responses={
                    200: OpenApiResponse(description='Usuario modificado'),
                    400: OpenApiResponse(description='SELF_STATE_CHANGE_FORBIDDEN | INVALID_STATE_TRANSITION'),
                    403: OpenApiResponse(description='Sin USR-002 modify_users'),
                    404: OpenApiResponse(description='USER_NOT_FOUND'),
                },
            ),
            delete=extend_schema(
                operation_id='user_eliminate',
                summary='UC_USR_04 — Eliminar usuario (baja lógica BR-009)',
                tags=['Usuarios'],
                responses={
                    200: OpenApiResponse(description='USER_ELIMINATED o USER_ELIMINATE_NOOP'),
                    400: OpenApiResponse(description='SELF_ELIMINATION_FORBIDDEN'),
                    403: OpenApiResponse(description='Sin USR-003 deactivate_users'),
                    404: OpenApiResponse(description='USER_NOT_FOUND'),
                },
            ),
        )
        class _Dispatcher(APIView):
            # GET → UserViewSet.retrieve (USR-009 view_users)
            # PATCH → ModifyUserView (USR-002 modify_users)
            # DELETE → EliminateUserView (USR-003 deactivate_users)
            # H-F6-GRP-GB-001: dispatcher centralizado para /api/users/{user_id}/
            permission_classes = [IsAuthenticated]

            def get(self, request, user_id):
                rv = CanonicalUserViewSet.as_view({'get': 'retrieve'})
                return rv(request._request, pk=user_id)

            def patch(self, request, user_id):
                return patch_view(request._request, user_id=user_id)

            def delete(self, request, user_id):
                return delete_view(request._request, user_id=user_id)

        return _Dispatcher.as_view()


urlpatterns = [
    # ────────────────────────────────────────────────────────────────────
    # UC_USR_03 + UC_USR_04 — PATCH|DELETE deben ir ANTES del router
    # (H-F6-GRP-GB-001: fix routing, _Dispatcher limitado a PATCH/DELETE)
    # ────────────────────────────────────────────────────────────────────
    path('<int:user_id>/', UserDetailDispatcher.as_view(), name='user-detail'),
    path('<int:user_id>/reset-password/',
         ResetPasswordView.as_view(), name='user-reset-password'),

    # Router — UserViewSet: GET /api/users/ (list) y GET /api/users/{pk}/ (retrieve)
    # el router también registra POST create — pero CreateUserView lo cubre explícitamente
    path('', include(router.urls)),

    # UC_USR_01 alias — CreateUserView canónica en /api/users/create/
    path('create/', CreateUserView.as_view(), name='user-create'),
]
