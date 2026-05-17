"""
URLs para logs app (UC_LOG_01..07).
"""
from django.urls import path
from .views import (
    DjangoLogTailView, ETLLogTailView, LogSearchView,
    InfraLogView, LogHealthView, LogMetricsView,
    PipelineEventLogView,
)
# UC_LOG_04 canónico (FASE 4) — vista con audit LOG_EXPORT_QUEUED
from apps.logs.log_export_views import LogExportView as _LogExportQueueView

app_name = 'logs'

urlpatterns = [
    path('django/tail/',       DjangoLogTailView.as_view(),    name='django-tail'),       # UC_LOG_01
    path('etl/tail/',          ETLLogTailView.as_view(),       name='etl-tail'),          # UC_LOG_02
    path('search/',            LogSearchView.as_view(),        name='search'),            # UC_LOG_03
    path('export/',            _LogExportQueueView.as_view(),  name='log-export-queue'),  # UC_LOG_04 canónico
    path('infra/',             InfraLogView.as_view(),         name='infra-tail'),        # UC_LOG_05
    path('health/',            LogHealthView.as_view(),        name='health'),            # UC_LOG_06
    path('metrics/',           LogMetricsView.as_view(),       name='metrics'),           # UC_LOG_07
    path('pipeline-events/',   PipelineEventLogView.as_view(), name='pipeline-events'),   # UC_LOG_08
]
