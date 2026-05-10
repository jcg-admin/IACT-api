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
from tests.test_data.user_test_data import UserTestData


# ============================================================================
# ALERTRULE FACTORIES
# ============================================================================

class AlertRuleTestData(DjangoModelFactory):
    """
    Factory para AlertRule (regla de alerta).
    
    Uso básico:
        rule = AlertRuleTestData(
            rule_name='High Abandonment Rate',
            metric='abandonment_rate',
            threshold_value=0.15
        )
    
    Con comparación:
        rule = AlertRuleTestData(
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
    created_by = factory.SubFactory(UserTestData)
    created_at = factory.Faker('date_time_this_month')


class ThresholdAlertRuleTestData(AlertRuleTestData):
    """
    Factory para regla de tipo THRESHOLD (umbral).
    
    Uso:
        rule = ThresholdAlertRuleTestData(
            rule_name='High Abandonment',
            metric='abandonment_rate',
            threshold_value=0.15,
            comparison_operator='>'
        )
    """
    rule_type = 'THRESHOLD'


class HighAbandonmentRuleTestData(ThresholdAlertRuleTestData):
    """Factory para alerta de abandono alto (>15%)."""
    rule_name = 'High Abandonment Rate'
    metric = 'abandonment_rate'
    threshold_value = Decimal('0.15')
    comparison_operator = '>'
    severity = 'HIGH'


class LowCallVolumeRuleTestData(ThresholdAlertRuleTestData):
    """Factory para alerta de volumen bajo (<100 llamadas)."""
    rule_name = 'Low Call Volume'
    metric = 'total_calls'
    threshold_value = 100
    comparison_operator = '<'
    severity = 'MEDIUM'


class LongQueueTimeRuleTestData(ThresholdAlertRuleTestData):
    """Factory para alerta de tiempo de cola alto (>120s)."""
    rule_name = 'Long Queue Time'
    metric = 'queue_time'
    threshold_value = 120
    comparison_operator = '>'
    severity = 'HIGH'


class TrendAlertRuleTestData(AlertRuleTestData):
    """
    Factory para regla de tipo TREND (tendencia).
    
    Uso:
        rule = TrendAlertRuleTestData(
            rule_name='Declining Call Volume',
            metric='total_calls'
        )
    """
    rule_type = 'TREND'
    threshold_value = Decimal('0.20')  # 20% decline
    comparison_operator = '<'


class AnomalyAlertRuleTestData(AlertRuleTestData):
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

class AlertTestData(DjangoModelFactory):
    """
    Factory para Alert (alerta disparada).
    
    Uso básico:
        alert = AlertTestData(
            rule=rule,
            severity='HIGH'
        )
    
    Con valores:
        alert = AlertTestData(
            current_value=0.18,
            threshold_value=0.15
        )
    """
    
    class Meta:
        # model = Alert  # Descomentar cuando se implemente
        abstract = True  # Temporal
    
    rule = factory.SubFactory(AlertRuleTestData)
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


class TriggeredAlertTestData(AlertTestData):
    """Factory para alerta disparada (no resuelta)."""
    is_resolved = False
    resolved_at = None


class ResolvedAlertTestData(AlertTestData):
    """Factory para alerta resuelta."""
    is_resolved = True
    resolved_at = factory.LazyAttribute(
        lambda obj: obj.triggered_at + timedelta(hours=1)
    )


class CriticalAlertTestData(AlertTestData):
    """Factory para alerta crítica."""
    severity = 'CRITICAL'
    message = 'CRITICAL: Sistema requiere atención inmediata'


class HighAlertTestData(AlertTestData):
    """Factory para alerta alta."""
    severity = 'HIGH'


class MediumAlertTestData(AlertTestData):
    """Factory para alerta media."""
    severity = 'MEDIUM'


class LowAlertTestData(AlertTestData):
    """Factory para alerta baja."""
    severity = 'LOW'


# ============================================================================
# ALERTNOTIFICATION FACTORIES
# ============================================================================

class AlertNotificationTestData(DjangoModelFactory):
    """
    Factory para AlertNotification (notificación de alerta).
    
    Uso básico:
        notification = AlertNotificationTestData(
            alert=alert,
            user=user,
            notification_type='EMAIL'
        )
    """
    
    class Meta:
        # model = AlertNotification  # Descomentar cuando se implemente
        abstract = True  # Temporal
    
    alert = factory.SubFactory(AlertTestData)
    user = factory.SubFactory(UserTestData)
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


class EmailNotificationTestData(AlertNotificationTestData):
    """Factory para notificación por email."""
    notification_type = 'EMAIL'
    recipient = factory.LazyAttribute(lambda obj: obj.user.email)


class PendingNotificationTestData(AlertNotificationTestData):
    """Factory para notificación pendiente."""
    delivery_status = 'PENDING'
    sent_at = None
    error_message = None


class SentNotificationTestData(AlertNotificationTestData):
    """Factory para notificación enviada."""
    delivery_status = 'SENT'
    error_message = None


class DeliveredNotificationTestData(AlertNotificationTestData):
    """Factory para notificación entregada."""
    delivery_status = 'DELIVERED'
    error_message = None


class FailedNotificationTestData(AlertNotificationTestData):
    """Factory para notificación fallida."""
    delivery_status = 'FAILED'
    error_message = factory.Iterator([
        'Email address invalid',
        'SMTP server error',
        'Recipient not found',
        'Network timeout'
    ])


class ReadNotificationTestData(AlertNotificationTestData):
    """Factory para notificación leída."""
    is_read = True
    read_at = factory.LazyAttribute(
        lambda obj: obj.sent_at + timedelta(minutes=10) if obj.sent_at else None
    )


# ============================================================================
# ALERTHISTORY FACTORIES
# ============================================================================

class AlertHistoryTestData(DjangoModelFactory):
    """
    Factory para AlertHistory (historial de alertas).
    
    Uso básico:
        history = AlertHistoryTestData(
            alert=alert,
            action='TRIGGERED'
        )
    """
    
    class Meta:
        # model = AlertHistory  # Descomentar cuando se implemente
        abstract = True  # Temporal
    
    alert = factory.SubFactory(AlertTestData)
    action = factory.Iterator(['TRIGGERED', 'RESOLVED', 'ACKNOWLEDGED', 'ESCALATED'])
    performed_by = factory.SubFactory(UserTestData)
    comment = factory.Faker('sentence', nb_words=10)
    timestamp = factory.Faker('date_time_this_hour')
    metadata = factory.LazyFunction(lambda: {
        'previous_status': 'PENDING',
        'new_status': 'ACKNOWLEDGED'
    })


class TriggeredHistoryTestData(AlertHistoryTestData):
    """Factory para historial de disparo."""
    action = 'TRIGGERED'
    comment = 'Alert triggered automatically'


class ResolvedHistoryTestData(AlertHistoryTestData):
    """Factory para historial de resolución."""
    action = 'RESOLVED'
    comment = 'Issue resolved'


class AcknowledgedHistoryTestData(AlertHistoryTestData):
    """Factory para historial de reconocimiento."""
    action = 'ACKNOWLEDGED'
    comment = 'Alert acknowledged by operator'


class EscalatedHistoryTestData(AlertHistoryTestData):
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

class CompleteAlertTestData:
    """
    Factory que crea alerta completa con notificaciones.
    
    Uso:
        alert = CompleteAlertTestData.create_alert(
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
        alert = AlertTestData(rule=rule, severity=severity)
        
        notifications = []
        for user in users:
            notification = EmailNotificationTestData(
                alert=alert,
                user=user
            )
            notifications.append(notification)
        
        return {
            'alert': alert,
            'notifications': notifications
        }


class AlertLifecycleTestData:
    """
    Factory que crea ciclo de vida completo de una alerta.
    
    Uso:
        lifecycle = AlertLifecycleTestData.create_lifecycle(
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
        alert = TriggeredAlertTestData(rule=rule)
        
        # Crear notificación
        notification = EmailNotificationTestData(alert=alert, user=user)
        
        # Crear historial
        history = [
            TriggeredHistoryTestData(alert=alert, performed_by=user),
            AcknowledgedHistoryTestData(alert=alert, performed_by=user),
            ResolvedHistoryTestData(alert=alert, performed_by=user)
        ]
        
        return {
            'alert': alert,
            'notifications': [notification],
            'history': history
        }


class UserWithAlertsTestData(UserTestData):
    """
    Factory que crea Usuario con alertas asignadas.
    
    Uso:
        user = UserWithAlertsTestData()
        # Usuario con 3 alertas automáticamente
    """
    
    @factory.post_generation
    def alerts(self, create, extracted, **kwargs):
        if not create:
            return
        
        # Crear 3 reglas
        rule1 = HighAbandonmentRuleTestData()
        rule2 = LowCallVolumeRuleTestData()
        rule3 = LongQueueTimeRuleTestData()
        
        # Crear alertas
        alert1 = TriggeredAlertTestData(rule=rule1)
        alert2 = ResolvedAlertTestData(rule=rule2)
        alert3 = CriticalAlertTestData(rule=rule3)
        
        # Crear notificaciones
        EmailNotificationTestData(alert=alert1, user=self)
        EmailNotificationTestData(alert=alert2, user=self)
        EmailNotificationTestData(alert=alert3, user=self)


# ============================================================================
# TOTAL FACTORIES: 29
# 
# AlertRule Factories (8):
#   - AlertRuleTestData
#   - ThresholdAlertRuleTestData
#   - HighAbandonmentRuleTestData
#   - LowCallVolumeRuleTestData
#   - LongQueueTimeRuleTestData
#   - TrendAlertRuleTestData
#   - AnomalyAlertRuleTestData
# 
# Alert Factories (7):
#   - AlertTestData
#   - TriggeredAlertTestData
#   - ResolvedAlertTestData
#   - CriticalAlertTestData
#   - HighAlertTestData
#   - MediumAlertTestData
#   - LowAlertTestData
# 
# AlertNotification Factories (7):
#   - AlertNotificationTestData
#   - EmailNotificationTestData
#   - PendingNotificationTestData
#   - SentNotificationTestData
#   - DeliveredNotificationTestData
#   - FailedNotificationTestData
#   - ReadNotificationTestData
# 
# AlertHistory Factories (5):
#   - AlertHistoryTestData
#   - TriggeredHistoryTestData
#   - ResolvedHistoryTestData
#   - AcknowledgedHistoryTestData
#   - EscalatedHistoryTestData
# 
# Helper Factories (3):
#   - CompleteAlertTestData (static)
#   - AlertLifecycleTestData (static)
#   - UserWithAlertsTestData
# 
# NOTA: Todas las factories están marcadas como abstract=True temporalmente.
# Cambiar a model=X cuando se implementen los modelos en apps/alerts/.
# 
# CLEAN_CODE v3.0.1: Nombres auto-documentados [SUCCESS]
# ============================================================================
