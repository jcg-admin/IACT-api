"""
URLs para app reports.

Endpoints REST API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReportViewSet, ExportJobViewSet

app_name = 'reports'

router = DefaultRouter()
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'export-jobs', ExportJobViewSet, basename='export-job')

urlpatterns = [
    path('', include(router.urls)),
]
