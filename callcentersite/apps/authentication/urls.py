"""
URLs para authentication.

CLEAN_CODE v3.0.1: URLs auto-documentadas.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.authentication.viewsets import AuthViewSet, SessionViewSet

# Router DRF
router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'sessions', SessionViewSet, basename='sessions')

urlpatterns = [
    path('', include(router.urls)),
]

"""
Endpoints generados (11 total):

Auth (7):
- POST   /api/v1/auth/login/                    (AllowAny)
- POST   /api/v1/auth/logout/                   (IsAuthenticated)
- POST   /api/v1/auth/change-password/          (IsAuthenticated + Permission)
- GET    /api/v1/auth/security-questions/       (AllowAny)
- POST   /api/v1/auth/set-security-answers/     (IsAuthenticated + Permission)
- POST   /api/v1/auth/verify-security-answers/  (AllowAny)
- POST   /api/v1/auth/reset-password/           (AllowAny)

Sessions (4):
- GET    /api/v1/sessions/                      (IsAuthenticated + Permission)
- GET    /api/v1/sessions/{id}/                 (IsAuthenticated + Permission)
- POST   /api/v1/sessions/{id}/invalidate/      (IsAuthenticated + Permission)
- POST   /api/v1/sessions/invalidate-all/       (IsAuthenticated + Permission)
"""
