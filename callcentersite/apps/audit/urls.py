"""
URLs para audit app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuditLogViewSet, AuditIntegrityView
from apps.audit.audit_event_views import (
    AuditLegacyExportView,
    GeneralAuditListView,
    AuditEventListView, AuditEventDetailView,
    AuditEventAggregateView, AuditEventExportView,
    AuditSearchView,
)
from apps.audit.compliance_views import ComplianceReportView, ComplianceVerifyView

router = DefaultRouter()
router.register(r'logs', AuditLogViewSet, basename='auditlog')

app_name = 'audit'

urlpatterns = [
    path('', include(router.urls)),
    # UC_PERM_10 — Consultar auditoría
    path('audit-events/',                   AuditEventListView.as_view(),      name='audit-event-list'),
    path('audit-events/<int:event_id>/',    AuditEventDetailView.as_view(),    name='audit-event-detail'),
    path('audit-events/aggregate/',         AuditEventAggregateView.as_view(), name='audit-event-aggregate'),
    path('audit-events/export/',            AuditEventExportView.as_view(),    name='audit-event-export'),
    # UC_AUD_02 — Buscar auditoría
    path('search/',                         AuditSearchView.as_view(),         name='audit-search'),
    # UC_AUD_03 — Exportar auditoría (same view, different required_function)
    path('export/',                         AuditLegacyExportView.as_view(),   name='audit-export'),
    path('general/',                        GeneralAuditListView.as_view(),    name='general-audit-list'),
    path('compliance-report/', ComplianceReportView.as_view(), name='compliance-report'),
    path('compliance-verify/', ComplianceVerifyView.as_view(), name='compliance-verify'),
    # B-08: UC_AUD_04 — integridad
    path('integrity/', AuditIntegrityView.as_view(), name='integrity'),
]
