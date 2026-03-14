"""
URLs para apps/ivr - IACT Call Center System.

Define rutas de API REST para CallLog legacy.

CNST-003: API READ-ONLY (MariaDB ivr_legacy)
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import viewsets


# Router para API REST
router = DefaultRouter()
router.register(r'call-logs', viewsets.CallLogViewSet, basename='calllog')

app_name = 'ivr'

urlpatterns = [
    path('api/', include(router.urls)),
]
