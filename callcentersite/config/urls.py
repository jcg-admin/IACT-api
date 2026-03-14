"""
URL Configuration - IACT Call Center System.

The `urlpatterns` list routes URLs to views.

Examples:
    Function views
        1. Add an import:  from my_app import views
        2. Add a URL to urlpatterns:  path('', views.home, name='home')
    Class-based views
        1. Add an import:  from other_app.views import Home
        2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
    Including another URLconf
        1. Import the include() function: from django.urls import include, path
        2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)


urlpatterns = [
    # Admin
    path(settings.ADMIN_URL if hasattr(settings, 'ADMIN_URL') else 'admin/', admin.site.urls),
    
    # API Schema (OpenAPI)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API endpoints (se agregan en Sprints)
    # path('api/v1/', include('apps.core.urls')),  # ELIMINADO: Movido a apps.pipeline.urls
    path('api/v1/navigation/', include('apps.core.navigation.urls')),  # Sistema de navegacion
    path('api/v1/auth/', include('apps.authentication.urls')),  # Sprint 2 - FASE 1 PARTE 5 [SUCCESS]
    # path('api/v1/access/', include('apps.access.urls')),  # Sprint 2 - TODO: implementar FASE 2
    path('api/v1/audit/', include('apps.audit.urls')),  # Sprint 2
    path('api/v1/users/', include('apps.users.urls')),  # Sprint 3
    path('api/v1/pipeline/', include('apps.pipeline.urls')),  # Sprint 3 - FASE 0.2 [SUCCESS]
    path('api/v1/reports/', include('apps.reports.urls')),  # Sprint 4
    path('api/v1/ivr/', include('apps.ivr.urls')),  # FASE 0.1 - IVR legacy READ-ONLY [SUCCESS]
    path('api/v1/alerts/', include('apps.alerts.urls')),  # Sistema de alertas internas [SUCCESS]
    path('api/v1/dashboard/', include('apps.dashboard.urls')),  # Sistema de dashboards [SUCCESS]
]

# Static/Media files (development)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Debug Toolbar (development)
if settings.DEBUG and 'debug_toolbar' in settings.INSTALLED_APPS:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
