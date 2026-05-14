# apps/alerts/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.alerts.views import (
    InternalMessageViewSet,
    AlertConfigurationViewSet,
    AlertSubscriptionViewSet,
)
from apps.alerts.alert_views import (
    AlertRuleListCreateView,
    AlertRuleDetailView,
    AlertRulePauseView,
    AlertRuleResumeView,
    AlertRuleDryRunView,
    ActiveAlertsView,
    AlertAcknowledgeView,
    AlertBulkAcknowledgeView,
)

app_name = 'alerts'

router = DefaultRouter()
router.register(r'messages',       InternalMessageViewSet,      basename='message')
router.register(r'configurations', AlertConfigurationViewSet,   basename='alertconfiguration')
router.register(r'subscriptions',  AlertSubscriptionViewSet,    basename='subscription')

urlpatterns = [
    # UC_ALR_01 — Gestionar Reglas de Alerta
    path('rules/',              AlertRuleListCreateView.as_view(), name='alert-rule-list-create'),
    path('rules/<uuid:rule_id>/', AlertRuleDetailView.as_view(),  name='alert-rule-detail'),
    path('rules/<uuid:rule_id>/pause/',  AlertRulePauseView.as_view(),  name='alert-rule-pause'),
    path('rules/<uuid:rule_id>/resume/', AlertRuleResumeView.as_view(), name='alert-rule-resume'),
    path('rules/dry-run/',      AlertRuleDryRunView.as_view(),    name='alert-rule-dry-run'),

    # UC_ALR_02 — Ver Alertas Activas
    path('active/',             ActiveAlertsView.as_view(),       name='active-alerts'),

    # UC_ALR_03 — Reconocer Alerta
    path('<uuid:alert_id>/acknowledge/', AlertAcknowledgeView.as_view(), name='alert-acknowledge'),
    path('bulk-acknowledge/',    AlertBulkAcknowledgeView.as_view(),     name='alert-bulk-acknowledge'),

    # Legacy router (mensajería, configuraciones)
    path('', include(router.urls)),
]
