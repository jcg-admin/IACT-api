"""
URLs para reports app.
B-01: endpoints IVR via SPs de MariaDB.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ReportViewSet, ExportJobViewSet,
    ScheduledReportViewSet, SavedViewViewSet,
    RealtimeMetricsView,
)
from .ivr_views import (
    MenuRedirigidosView, MenuCentroView,
    ClientesReportView,
    CentrosTransferenciaView,
    LlamadasAbandonadasView,
    CMENUErrorView,
    CentrosXSegmentoView,
    MenusIVRView,
)

router = DefaultRouter()
router.register(r'reports',     ReportViewSet,    basename='report')
router.register(r'export-jobs',   ExportJobViewSet,       basename='export-job')
router.register(r'scheduled',     ScheduledReportViewSet, basename='scheduled-report')
router.register(r'saved-views',   SavedViewViewSet,       basename='saved-view')

app_name = 'reports'

urlpatterns = [
    path('', include(router.urls)),

    # K-005: UC_RPT_02 — real-time metrics stub (CNST-004)
    path('realtime/', RealtimeMetricsView.as_view(), name='realtime-metrics'),

    # B-01: Reportes IVR (UC_RPT_12..17) — leen de MariaDB via SPs
    path('ivr/clients/',            ClientesReportView.as_view(),        name='ivr-clients'),
    path('ivr/transfer-centers/',   CentrosTransferenciaView.as_view(),  name='ivr-transfer-centers'),
    path('ivr/abandoned/',          LlamadasAbandonadasView.as_view(),   name='ivr-abandoned'),
    path('ivr/menu-errors/',        CMENUErrorView.as_view(),            name='ivr-menu-errors'),
    path('ivr/centers-by-segment/', CentrosXSegmentoView.as_view(),      name='ivr-centers-by-segment'),
    path('ivr/menu-redirigidos/', MenuRedirigidosView.as_view(),  name='ivr-menu-redirigidos'),
    path('ivr/menu-centro/',      MenuCentroView.as_view(),       name='ivr-menu-centro'),
    path('ivr/menus/',              MenusIVRView.as_view(),              name='ivr-menus'),
]
