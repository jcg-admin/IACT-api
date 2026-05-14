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
# FASE 4
from apps.alerts.alert_history_view import AlertHistoryView
from apps.alerts.alert_subscription_views import (
    AlertSubscriptionListView, AlertSubscriptionDetailView,
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


    # UC_ALR_04 — Historial de alertas (FASE 4)
    path('history/', AlertHistoryView.as_view(), name='alert-history'),
    # UC_ALR_05 — Suscripciones (FASE 4)
    path('me/subscriptions/', AlertSubscriptionListView.as_view(), name='alert-subscription-list'),
    path('me/subscriptions/<int:sub_id>/', AlertSubscriptionDetailView.as_view(), name='alert-subscription-detail'),

    # Legacy router (mensajería, configuraciones)
    path('', include(router.urls)),
]
