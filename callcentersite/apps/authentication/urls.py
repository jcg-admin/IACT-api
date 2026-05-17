"""
apps/authentication/urls.py

URLs de autenticación — UC_AUTH_01..05 + UC_PERM_08.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.authentication.login_view import LoginView
from apps.authentication.change_password_view import ChangePasswordView
from apps.authentication.logout_view import LogoutView
from apps.authentication.session_admin_view import (
    SessionListView, SessionCloseView, SessionCloseAllView, SessionOwnView,
)
from apps.authentication.menu_view import MenuView
from apps.authentication.viewsets import AuthViewSet, SessionViewSet

router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'sessions', SessionViewSet, basename='sessions')

app_name = 'authentication'

urlpatterns = [
    path('auth/login/',           LoginView.as_view(),          name='login'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('auth/logout/',          LogoutView.as_view(),          name='logout'),

    path('auth/sessions/',                              SessionListView.as_view(),     name='session-list'),
    path('auth/sessions/own/',                          SessionOwnView.as_view(),      name='session-own'),
    path('auth/sessions/close-all/',                    SessionCloseAllView.as_view(), name='session-close-all'),
    path('auth/sessions/<uuid:session_id>/close/',      SessionCloseView.as_view(),    name='session-close'),

    path('me/menu/', MenuView.as_view(), name='me-menu'),

    path('', include(router.urls)),
]
