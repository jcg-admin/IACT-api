"""
apps/authentication/urls.py

URLs de autenticación — UC_AUTH_01..05.

La LoginView canónica (UC_AUTH_01) se registra directamente como APIView
en /api/auth/login/ para tener control total sobre el endpoint y el schema
de drf-spectacular.

El router de AuthViewSet gestiona el resto de acciones.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.authentication.login_view import LoginView
from apps.authentication.change_password_view import ChangePasswordView
from apps.authentication.logout_view import LogoutView
from apps.authentication.session_admin_view import (
    SessionListView, SessionCloseView, SessionCloseAllView, SessionOwnView,
)
from apps.authentication.viewsets import AuthViewSet, SessionViewSet

# Router para acciones secundarias (logout, change-password, security-questions…)
router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'sessions', SessionViewSet, basename='sessions')

app_name = 'authentication'

urlpatterns = [
    # UC_AUTH_01 — endpoint canónico con LoginView (drf-spectacular completo)
    path('auth/login/', LoginView.as_view(), name='login'),
    # UC_AUTH_04 — cambio de contraseña (canónico, reemplaza AuthViewSet.change_password)
    path('auth/change-password/', ChangePasswordView.as_view(), name='change-password'),
    # UC_AUTH_02 — cerrar sesión con blacklist de tokens
    path('auth/logout/', LogoutView.as_view(), name='logout'),

    # UC_AUTH_05 — Gestionar Sesiones
    path('auth/sessions/', SessionListView.as_view(), name='session-list'),
    path('auth/sessions/own/', SessionOwnView.as_view(), name='session-own'),
    path('auth/sessions/close-all/', SessionCloseAllView.as_view(), name='session-close-all'),
    path('auth/sessions/<uuid:session_id>/close/', SessionCloseView.as_view(), name='session-close'),

    # Resto de endpoints de autenticación vía router
    path('', include(router.urls)),
]
