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
