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
from .export_views    import ExportView, ExportDetailView
from .schedule_views    import ScheduledReportListCreateView, ScheduledReportDetailView
from .share_views       import ShareCreateView, ShareDetailView
from .saved_filter_views import (
    SavedFilterListView, SavedFilterDetailView,
    SavedViewListView, SavedViewDetailView, SavedViewCloneView,
)

from .analytics_views   import (
    AgentReportView, AgentDetailView, QueueReportView,
    CampaignReportView, TransferReportView, IVRMenuReportView,
    UniqueClientsReportView,
)
from .sla_views import SLADistribucionView
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
    path('realtime/',              RealtimeMetricsView.as_view(),  name='realtime-metrics'),
    path('historical/',            HistoricalReportView.as_view(), name='historical-report'),
    # UC_RPT_09 — Filtros guardados (FASE 5)
    path('me/filters/',              SavedFilterListView.as_view(),     name='saved-filter-list'),
    path('me/filters/<int:pk>/',     SavedFilterDetailView.as_view(),   name='saved-filter-detail'),
    # UC_RPT_10 — Vistas guardadas (FASE 5)
    path('me/views/',                SavedViewListView.as_view(),       name='saved-view-list'),
    path('me/views/<int:pk>/',       SavedViewDetailView.as_view(),     name='saved-view-detail'),
    path('me/views/<int:pk>/clone/', SavedViewCloneView.as_view(),      name='saved-view-clone'),
    # UC_RPT_07/08 — Reportes programados (FASE 4)
    path('schedules/',                ScheduledReportListCreateView.as_view(), name='schedule-list-create'),
    path('schedules/<int:sched_id>/', ScheduledReportDetailView.as_view(),     name='schedule-detail'),
    # UC_RPT_11 — Compartir reporte (FASE 4)
    path('shares/',                   ShareCreateView.as_view(),               name='share-create'),
    path('shares/<uuid:share_id>/',   ShareDetailView.as_view(),               name='share-detail'),
    # UC_RPT_12..17 — Reportes analíticos (FASE 4)
    path('agents/',                   AgentReportView.as_view(),               name='agent-report'),
    path('agents/<int:agent_id>/',    AgentDetailView.as_view(),               name='agent-detail'),
    path('queues/',                   QueueReportView.as_view(),               name='queue-report'),
    path('campaigns/',                CampaignReportView.as_view(),            name='campaign-report'),
    path('ivr/transfers/',            TransferReportView.as_view(),            name='transfer-report'),
    path('ivr/menus/',                IVRMenuReportView.as_view(),             name='ivr-menu-report'),
    path('ivr/unique-clients/',       UniqueClientsReportView.as_view(),       name='unique-clients-report'),
    path('export/',                ExportView.as_view(),           name='export-queue'),
    path('export/<uuid:job_id>/',  ExportDetailView.as_view(),     name='export-detail'),

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
    path('ivr/sla/',              SLADistribucionView.as_view(),    name='ivr-sla'),
]
