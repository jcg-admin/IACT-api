"""
URLs para reports app.
B-01: endpoints IVR via SPs de MariaDB.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ReportViewSet, ExportJobViewSet,
    ScheduledReportViewSet, SavedViewViewSet,
)
from .realtime_view   import RealtimeMetricsView
from .dashboard_view  import DashboardView
from .historical_view import HistoricalReportView
from .ivr_views import (
    RedirectedMenusView, CenterMenuView,
    ClientsReportView,
    TransferCentersView,
    AbandonedCallsView,
    CMENUErrorView,
    CentersBySegmentView,
    IvrMenusView,
    AbandonmentSummaryView,
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
    path('realtime/',   RealtimeMetricsView.as_view(),  name='realtime-metrics'),
    path('historical/', HistoricalReportView.as_view(), name='historical-report'),

    # B-01: Reportes IVR (UC_RPT_12..17) — leen de MariaDB via SPs
    # UC_RPT_01 — Dashboard principal de KPIs IVR
    path('dashboard/', DashboardView.as_view(), name='dashboard'),

    # B-01: Reportes IVR (UC_RPT_12..17)
    path('ivr/clients/',            ClientsReportView.as_view(),        name='ivr-clients'),
    path('ivr/transfer-centers/',   TransferCentersView.as_view(),  name='ivr-transfer-centers'),
    path('ivr/abandoned/',          AbandonedCallsView.as_view(),   name='ivr-abandoned'),
    path('ivr/menu-errors/',        CMENUErrorView.as_view(),            name='ivr-menu-errors'),
    path('ivr/centers-by-segment/', CentersBySegmentView.as_view(),      name='ivr-centers-by-segment'),
    path('ivr/menu-redirected/',  RedirectedMenusView.as_view(), name='ivr-menu-redirected'),
    path('ivr/menu-center/',      CenterMenuView.as_view(),      name='ivr-menu-center'),
    path('ivr/menus/',              IvrMenusView.as_view(),              name='ivr-menus'),
    path('ivr/abandonment-summary/', AbandonmentSummaryView.as_view(),  name='ivr-abandonment-summary'),
]
