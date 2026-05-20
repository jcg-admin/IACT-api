"""
URLs principales del sistema IACT.

Registro completo de todas las apps activas.
B-03 fix: todas las apps conectadas al router raiz.
B-09 fix: authentication incluida.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Core navigation
    path('api/navigation/', include('apps.core.navigation.urls')),

    # Auth (UC_AUTH_01..05)
    path('api/', include('apps.authentication.urls')),

    # Users (UC_USR_01..04)
    path('api/users/', include('apps.users.urls')),

    # Access + Permissions (UC_ACC_01..09, UC_PERM_01..10, UC_ADM_01..03)
    path('api/access/', include('apps.access.urls')),

    # Audit (UC_AUD_01..04)
    path('api/audit/', include('apps.audit.urls')),

    # Alerts (UC_ALR_01..05)
    path('api/alerts/', include('apps.alerts.urls')),

    # Pipeline IVR ETL (UC_PIP_01..04)
    path('api/pipeline/', include('apps.pipeline.urls')),

    # Reports — infraestructura + IVR (UC_RPT_01..17)
    path('api/reports/', include('apps.reports.urls')),

    # Logs (UC_LOG_01..07)
    path('api/logs/', include('apps.logs.urls')),

    # Dashboard (UC_DSH_01..04) — registrado tras detectar 404 != 200 en
    # apps/dashboard/tests/test_viewsets.py: el router DRF de la app existia
    # pero config.urls no lo incluia. Iniciativa
    # resolver-tests-dashboard-iact-api.
    path('api/dashboard/', include('apps.dashboard.urls')),
]
