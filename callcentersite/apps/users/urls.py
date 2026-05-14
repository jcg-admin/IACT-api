"""
apps/users/urls.py

URLs de gestión de usuarios — FASE 0 + FASE 2.

Hallazgo B-04 (FASE 2):
  EliminateUserView.delete() no estaba registrada. La ruta PATCH /api/users/{id}/
  solo aceptaba PATCH, devolviendo 405 para DELETE. Se resuelve con
  UserDetailView que despacha PATCH → ModifyUserView y DELETE → EliminateUserView.
"""
from django.urls import path, include
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

        class _Dispatcher(APIView):
            # No permission_classes aquí — cada view hija los tiene propios (CNST-010)
            permission_classes = [IsAuthenticated]

            def patch(self, request, user_id):
                return patch_view(request._request, user_id=user_id)

            def delete(self, request, user_id):
                return delete_view(request._request, user_id=user_id)

        return _Dispatcher.as_view()


urlpatterns = [
    # ────────────────────────────────────────────────────────────────────
    # FASE 2 — Rutas canónicas (declaradas antes del router)
    # ────────────────────────────────────────────────────────────────────

    # UC_USR_01 — Crear usuario (POST /api/users/)
    path('', CreateUserView.as_view(), name='user-create'),

    # UC_USR_03 + UC_USR_04 — Modificar / Eliminar (PATCH|DELETE /api/users/{id}/)
    path('<int:user_id>/', UserDetailDispatcher.as_view(), name='user-detail'),

    # UC_AUTH_03 — Resetear contraseña por admin (POST /api/users/{id}/reset-password/)
    path('<int:user_id>/reset-password/',
         ResetPasswordView.as_view(), name='user-reset-password'),

    # ────────────────────────────────────────────────────────────────────
    # Legacy router (compatibilidad UC_USR_02 list/retrieve existente)
    # ────────────────────────────────────────────────────────────────────
    path('', include(router.urls)),
]
