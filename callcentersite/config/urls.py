"""
Main URL configuration for the IACT API.
"""
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import ReDocView, SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # OpenAPI schema & docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', ReDocView.as_view(url_name='schema'), name='redoc'),

    # Navigation (Sistema de Navegacion v3.0.0)
    path('api/navigation/', include('apps.core.navigation.urls')),

    # Users
    path('api/users/', include('apps.users.urls', namespace='users')),
]
