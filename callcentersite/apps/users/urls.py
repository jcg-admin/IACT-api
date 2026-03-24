"""URL patterns for the users app."""
from django.urls import path

from apps.users import views

app_name = 'users'

urlpatterns = [
    # Profile
    path('profile/', views.get_user_profile_view, name='profile'),

    # Avatar management
    path('avatar/upload/', views.upload_avatar_view, name='upload-avatar'),
    path('avatar/delete/', views.delete_avatar_view, name='delete-avatar'),
]
