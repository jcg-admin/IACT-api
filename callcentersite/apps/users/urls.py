"""
URLs para la gestion de usuarios y perfiles.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views
from .viewsets.user_viewset import UserViewSet

app_name = 'users'

router = DefaultRouter()
router.register(r'', UserViewSet, basename='user')

urlpatterns = [
    path('profile/', views.get_user_profile_view, name='profile'),
    path('avatar/upload-avatar/', views.upload_avatar_view, name='upload-avatar'),
    path('avatar/', views.delete_avatar_view, name='delete-avatar'),
    # UserViewSet CRUD: /api/users/, /api/users/{id}/
    path('', include(router.urls)),
]
