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
from apps.authentication.viewsets import AuthViewSet, SessionViewSet

# Router para acciones secundarias (logout, change-password, security-questions…)
router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'sessions', SessionViewSet, basename='sessions')

app_name = 'authentication'

urlpatterns = [
    # UC_AUTH_01 — endpoint canónico con LoginView (drf-spectacular completo)
    path('auth/login/', LoginView.as_view(), name='login'),

    # Resto de endpoints de autenticación vía router
    path('', include(router.urls)),
]
