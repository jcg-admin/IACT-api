"""
URLs para la gestion de usuarios y perfiles.
"""
from django.urls import path

from . import views

app_name = 'users'

urlpatterns = [
    path('profile/', views.get_user_profile_view, name='profile'),
    path('avatar/upload-avatar/', views.upload_avatar_view, name='upload-avatar'),
    path('avatar/', views.delete_avatar_view, name='delete-avatar'),
]
