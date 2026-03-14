"""
URLs core - IACT Call Center System.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CallRecordViewSet, CenterViewSet, ServiceViewSet

router = DefaultRouter()
router.register(r'calls', CallRecordViewSet, basename='callrecord')
router.register(r'centers', CenterViewSet, basename='center')
router.register(r'services', ServiceViewSet, basename='service')

urlpatterns = [
    path('', include(router.urls)),
]
