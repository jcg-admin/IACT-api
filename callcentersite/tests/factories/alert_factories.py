"""
Factories para apps/alerts/.

Factory boy para generación de datos test de alertas.
Basado en análisis ANALISIS_APP_ALERTS_v3_0_0.md (3 partes).

NOTA: Esta app aún no está implementada. Estas factories estarán
listas para cuando se implemente.

CLEAN_CODE v3.0.1: Nombres auto-documentados.
"""

import factory
from factory.django import DjangoModelFactory
from factory import fuzzy
from datetime import datetime, timedelta
from decimal import Decimal


# NOTA TEMPORAL: Imports comentados hasta que se implementen los modelos
# from apps.alerts.models import (
#     AlertRule,
#     Alert,
#     AlertNotification,
#     AlertHistory,
# )
from tests.factories.user_factory import UserFactory


# ============================================================================
# ALERTRULE FACTORIES
# ============================================================================

class AlertRuleFactory(DjangoModelFactory):
    """
    Factory para AlertRule (regla de alerta).
    
    Uso básico:
        rule = AlertRuleFactory(
            rule_name='High Abandonment Rate',
            metric='abandonment_rate',
            threshold_value=0.15
        )
    
    Con comparación:
        rule = AlertRuleFactory(
            metric='total_calls',
            threshold_value=1000,
            comparison_operator='<'
        )
    """
    
    class Meta:
        # model = AlertRule  # Descomentar cuando se implemente
        abstract = True  # Temporal
    
    rule_name = factory.Sequence(lambda n: f'Alert Rule {n}')
    description = factory.Faker('sentence', nb_words=15)
    rule_type = factory.Iterator(['THRESHOLD', 'TREND', 'ANOMALY'])
    metric = factory.Iterator([
        'abandonment_rate',
        'total_calls',
        'avg_duration',
        'transfer_rate',
        'queue_time'
    ])
    threshold_value = factory.Faker('pyfloat', min_value=0, max_value=100)
    comparison_operator = factory.Iterator(['>', '<', '>=', '<=', '=='])
    severity = factory.Iterator(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'])
    is_active = True
    evaluation_period_minutes = 60
    notification_cooldown_minutes = 30
    created_by = factory.SubFactory(UserFactory)
    created_at = factory.Faker('date_time_this_month')


class ThresholdAlertRuleFactory(AlertRuleFactory):
    """
    Factory para regla de tipo THRESHOLD (umbral).
    
    Uso:
        rule = ThresholdAlertRuleFactory(
            rule_name='High Abandonment',
            metric='abandonment_rate',
            threshold_value=0.15,
            comparison_operator='>'
        )
    """
    rule_type = 'THRESHOLD'


class HighAbandonmentRuleFactory(ThresholdAlertRuleFactory):
    """Factory para alerta de abandono alto (>15%)."""
    rule_name = 'High Abandonment Rate'
    metric = 'abandonment_rate'
    threshold_value = Decimal('0.15')
    comparison_operator = '>'
    severity = 'HIGH'


class LowCallVolumeRuleFactory(ThresholdAlertRuleFactory):
    """Factory para alerta de volumen bajo (<100 llamadas)."""
    rule_name = 'Low Call Volume'
    metric = 'total_calls'
    threshold_value = 100
    comparison_operator = '<'
    severity = 'MEDIUM'


class LongQueueTimeRuleFactory(ThresholdAlertRuleFactory):
    """Factory para alerta de tiempo de cola alto (>120s)."""
    rule_name = 'Long Queue Time'
    metric = 'queue_time'
    threshold_value = 120
    comparison_operator = '>'
    severity = 'HIGH'


class TrendAlertRuleFactory(AlertRuleFactory):
    """
    Factory para regla de tipo TREND (tendencia).
    
    Uso:
        rule = TrendAlertRuleFactory(
            rule_name='Declining Call Volume',
            metric='total_calls'
        )
    """
    rule_type = 'TREND'
    threshold_value = Decimal('0.20')  # 20% decline
    comparison_operator = '<'


class AnomalyAlertRuleFactory(AlertRuleFactory):
    """
    Factory para regla de tipo ANOMALY (anomalía).
    
    Usa detección de anomalías estadísticas.
    """
    rule_type = 'ANOMALY'
    threshold_value = Decimal('2.0')  # 2 standard deviations
    comparison_operator = '>'


# ============================================================================
# ALERT FACTORIES
# ============================================================================

class AlertFactory(DjangoModelFactory):
    """
    Factory para Alert (alerta disparada).
    
    Uso básico:
        alert = AlertFactory(
            rule=rule,
            severity='HIGH'
        )
    
    Con valores:
        alert = AlertFactory(
            current_value=0.18,
            threshold_value=0.15
        )
    """
    
    class Meta:
        # model = Alert  # Descomentar cuando se implemente
        abstract = True  # Temporal
    
    rule = factory.SubFactory(AlertRuleFactory)
    severity = factory.LazyAttribute(lambda obj: obj.rule.severity)
    message = factory.Faker('sentence', nb_words=12)
    current_value = factory.Faker('pyfloat', min_value=0, max_value=100)
    threshold_value = factory.LazyAttribute(lambda obj: obj.rule.threshold_value)
    metadata = factory.LazyFunction(lambda: {
        'did': '800123456',
        'time_period': 'last_hour',
        'data_points': 60
    })
    triggered_at = factory.Faker('date_time_this_hour')
    resolved_at = None
    is_resolved = False


class TriggeredAlertFactory(AlertFactory):
    """Factory para alerta disparada (no resuelta)."""
    is_resolved = False
    resolved_at = None


class ResolvedAlertFactory(AlertFactory):
    """Factory para alerta resuelta."""
    is_resolved = True
    resolved_at = factory.LazyAttribute(
        lambda obj: obj.triggered_at + timedelta(hours=1)
    )


class CriticalAlertFactory(AlertFactory):
    """Factory para alerta crítica."""
    severity = 'CRITICAL'
    message = 'CRITICAL: Sistema requiere atención inmediata'


class HighAlertFactory(AlertFactory):
    """Factory para alerta alta."""
    severity = 'HIGH'


class MediumAlertFactory(AlertFactory):
    """Factory para alerta media."""
    severity = 'MEDIUM'


class LowAlertFactory(AlertFactory):
    """Factory para alerta baja."""
    severity = 'LOW'


# ============================================================================
# ALERTNOTIFICATION FACTORIES
# ============================================================================

class AlertNotificationFactory(DjangoModelFactory):
    """
    Factory para AlertNotification (notificación de alerta).
    
    Uso básico:
        notification = AlertNotificationFactory(
            alert=alert,
            user=user,
            notification_type='EMAIL'
        )
    """
    
    class Meta:
        # model = AlertNotification  # Descomentar cuando se implemente
        abstract = True  # Temporal
    
    alert = factory.SubFactory(AlertFactory)
    user = factory.SubFactory(UserFactory)
    notification_type = factory.Iterator(['EMAIL', 'SMS', 'PUSH', 'WEBHOOK'])
    recipient = factory.LazyAttribute(
        lambda obj: obj.user.email if obj.notification_type == 'EMAIL' else obj.user.username
    )
    sent_at = factory.Faker('date_time_this_hour')
    delivery_status = factory.Iterator(['PENDING', 'SENT', 'DELIVERED', 'FAILED'])
    error_message = factory.LazyAttribute(
        lambda obj: None if obj.delivery_status in ['SENT', 'DELIVERED'] else 'Delivery failed'
    )
    is_read = False
    read_at = None


class EmailNotificationFactory(AlertNotificationFactory):
    """Factory para notificación por email."""
    notification_type = 'EMAIL'
    recipient = factory.LazyAttribute(lambda obj: obj.user.email)


class PendingNotificationFactory(AlertNotificationFactory):
    """Factory para notificación pendiente."""
    delivery_status = 'PENDING'
    sent_at = None
    error_message = None


class SentNotificationFactory(AlertNotificationFactory):
    """Factory para notificación enviada."""
    delivery_status = 'SENT'
    error_message = None


class DeliveredNotificationFactory(AlertNotificationFactory):
    """Factory para notificación entregada."""
    delivery_status = 'DELIVERED'
    error_message = None


class FailedNotificationFactory(AlertNotificationFactory):
    """Factory para notificación fallida."""
    delivery_status = 'FAILED'
    error_message = factory.Iterator([
        'Email address invalid',
        'SMTP server error',
        'Recipient not found',
        'Network timeout'
    ])


class ReadNotificationFactory(AlertNotificationFactory):
    """Factory para notificación leída."""
    is_read = True
    read_at = factory.LazyAttribute(
        lambda obj: obj.sent_at + timedelta(minutes=10) if obj.sent_at else None
    )


# ============================================================================
# ALERTHISTORY FACTORIES
# ============================================================================

class AlertHistoryFactory(DjangoModelFactory):
    """
    Factory para AlertHistory (historial de alertas).
    
    Uso básico:
        history = AlertHistoryFactory(
            alert=alert,
            action='TRIGGERED'
        )
    """
    
    class Meta:
        # model = AlertHistory  # Descomentar cuando se implemente
        abstract = True  # Temporal
    
    alert = factory.SubFactory(AlertFactory)
    action = factory.Iterator(['TRIGGERED', 'RESOLVED', 'ACKNOWLEDGED', 'ESCALATED'])
    performed_by = factory.SubFactory(UserFactory)
    comment = factory.Faker('sentence', nb_words=10)
    timestamp = factory.Faker('date_time_this_hour')
    metadata = factory.LazyFunction(lambda: {
        'previous_status': 'PENDING',
        'new_status': 'ACKNOWLEDGED'
    })


class TriggeredHistoryFactory(AlertHistoryFactory):
    """Factory para historial de disparo."""
    action = 'TRIGGERED'
    comment = 'Alert triggered automatically'


class ResolvedHistoryFactory(AlertHistoryFactory):
    """Factory para historial de resolución."""
    action = 'RESOLVED'
    comment = 'Issue resolved'


class AcknowledgedHistoryFactory(AlertHistoryFactory):
    """Factory para historial de reconocimiento."""
    action = 'ACKNOWLEDGED'
    comment = 'Alert acknowledged by operator'


class EscalatedHistoryFactory(AlertHistoryFactory):
    """Factory para historial de escalamiento."""
    action = 'ESCALATED'
    comment = 'Alert escalated to supervisor'
    metadata = factory.LazyFunction(lambda: {
        'escalated_to': 'supervisor@example.com',
        'reason': 'Unresolved after 1 hour'
    })


# ============================================================================
# HELPER FACTORIES (Complex scenarios)
# ============================================================================

class CompleteAlertFactory:
    """
    Factory que crea alerta completa con notificaciones.
    
    Uso:
        alert = CompleteAlertFactory.create_alert(
            rule=rule,
            users=[user1, user2]
        )
        # Retorna dict con alert y notifications
    """
    
    @staticmethod
    def create_alert(rule, users, severity='HIGH'):
        """
        Crea alerta completa con notificaciones.
        
        Args:
            rule: AlertRule
            users: Lista de usuarios a notificar
            severity: Severidad
        
        Returns:
            dict: {
                'alert': Alert,
                'notifications': [AlertNotification, ...]
            }
        """
        alert = AlertFactory(rule=rule, severity=severity)
        
        notifications = []
        for user in users:
            notification = EmailNotificationFactory(
                alert=alert,
                user=user
            )
            notifications.append(notification)
        
        return {
            'alert': alert,
            'notifications': notifications
        }


class AlertLifecycleFactory:
    """
    Factory que crea ciclo de vida completo de una alerta.
    
    Uso:
        lifecycle = AlertLifecycleFactory.create_lifecycle(
            rule=rule,
            user=user
        )
        # Retorna dict con alert, notifications, history
    """
    
    @staticmethod
    def create_lifecycle(rule, user):
        """
        Crea ciclo completo: triggered -> acknowledged -> resolved.
        
        Args:
            rule: AlertRule
            user: Usuario
        
        Returns:
            dict: {
                'alert': Alert,
                'notifications': [...],
                'history': [...]
            }
        """
        # Crear alerta
        alert = TriggeredAlertFactory(rule=rule)
        
        # Crear notificación
        notification = EmailNotificationFactory(alert=alert, user=user)
        
        # Crear historial
        history = [
            TriggeredHistoryFactory(alert=alert, performed_by=user),
            AcknowledgedHistoryFactory(alert=alert, performed_by=user),
            ResolvedHistoryFactory(alert=alert, performed_by=user)
        ]
        
        return {
            'alert': alert,
            'notifications': [notification],
            'history': history
        }


class UserWithAlertsFactory(UserFactory):
    """
    Factory que crea Usuario con alertas asignadas.
    
    Uso:
        user = UserWithAlertsFactory()
        # Usuario con 3 alertas automáticamente
    """
    
    @factory.post_generation
    def alerts(self, create, extracted, **kwargs):
        if not create:
            return
        
        # Crear 3 reglas
        rule1 = HighAbandonmentRuleFactory()
        rule2 = LowCallVolumeRuleFactory()
        rule3 = LongQueueTimeRuleFactory()
        
        # Crear alertas
        alert1 = TriggeredAlertFactory(rule=rule1)
        alert2 = ResolvedAlertFactory(rule=rule2)
        alert3 = CriticalAlertFactory(rule=rule3)
        
        # Crear notificaciones
        EmailNotificationFactory(alert=alert1, user=self)
        EmailNotificationFactory(alert=alert2, user=self)
        EmailNotificationFactory(alert=alert3, user=self)


# ============================================================================
# TOTAL FACTORIES: 29
# 
# AlertRule Factories (8):
#   - AlertRuleFactory
#   - ThresholdAlertRuleFactory
#   - HighAbandonmentRuleFactory
#   - LowCallVolumeRuleFactory
#   - LongQueueTimeRuleFactory
#   - TrendAlertRuleFactory
#   - AnomalyAlertRuleFactory
# 
# Alert Factories (7):
#   - AlertFactory
#   - TriggeredAlertFactory
#   - ResolvedAlertFactory
#   - CriticalAlertFactory
#   - HighAlertFactory
#   - MediumAlertFactory
#   - LowAlertFactory
# 
# AlertNotification Factories (7):
#   - AlertNotificationFactory
#   - EmailNotificationFactory
#   - PendingNotificationFactory
#   - SentNotificationFactory
#   - DeliveredNotificationFactory
#   - FailedNotificationFactory
#   - ReadNotificationFactory
# 
# AlertHistory Factories (5):
#   - AlertHistoryFactory
#   - TriggeredHistoryFactory
#   - ResolvedHistoryFactory
#   - AcknowledgedHistoryFactory
#   - EscalatedHistoryFactory
# 
# Helper Factories (3):
#   - CompleteAlertFactory (static)
#   - AlertLifecycleFactory (static)
#   - UserWithAlertsFactory
# 
# NOTA: Todas las factories están marcadas como abstract=True temporalmente.
# Cambiar a model=X cuando se implementen los modelos en apps/alerts/.
# 
# CLEAN_CODE v3.0.1: Nombres auto-documentados [SUCCESS]
# ============================================================================
