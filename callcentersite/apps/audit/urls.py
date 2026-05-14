from apps.audit.compliance_views import ComplianceReportView, ComplianceVerifyView
"""
URLs para audit app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuditLogViewSet

router = DefaultRouter()
router.register(r'logs', AuditLogViewSet, basename='auditlog')

app_name = 'audit'

urlpatterns = [
    path('', include(router.urls)),
]

# B-08: UC_AUD_04 — integridad
from .views import AuditIntegrityView
urlpatterns += [
    path('compliance-report/', ComplianceReportView.as_view(), name='compliance-report'),
    path('compliance-verify/', ComplianceVerifyView.as_view(), name='compliance-verify'),
    path('integrity/', AuditIntegrityView.as_view(), name='integrity'),
]
