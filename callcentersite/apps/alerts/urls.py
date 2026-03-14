# apps/alerts/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.alerts.views import (
    InternalMessageViewSet,
    AlertConfigurationViewSet,
    AlertSubscriptionViewSet
)

app_name = 'alerts'

router = DefaultRouter()
router.register(r'messages', InternalMessageViewSet, basename='message')
router.register(r'configurations', AlertConfigurationViewSet, basename='alertconfiguration')
router.register(r'subscriptions', AlertSubscriptionViewSet, basename='subscription')

urlpatterns = [
    path('', include(router.urls)),
]
