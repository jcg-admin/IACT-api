"""
URLs principales del sistema IACT.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Navigation
    path('api/navigation/', include('apps.core.navigation.urls')),

    # Users
    path('api/users/', include('apps.users.urls')),
]
