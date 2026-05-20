# apps/alerts/tests/test_services.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from apps.alerts.models import (
    InternalMessage,
    MessageRecipient,
    AlertConfiguration,
    AlertSubscription
)
from apps.alerts.services import MessageService, AlertService, SubscriptionService

User = get_user_model()


class MessageServiceTest(TestCase):
    """Tests para MessageService"""

    def setUp(self):
        """Setup para todos los tests"""
        self.sender = User.objects.create_user(
            username='sender',
            password='password123'
        )
        self.recipient1 = User.objects.create_user(
            username='recipient1',
            password='password123'
        )
        self.recipient2 = User.objects.create_user(
            username='recipient2',
            password='password123'
        )

    def test_send_message(self):
        """Test: Enviar mensaje"""
        message = MessageService.send_message(
            sender=self.sender,
            recipients=[self.recipient1, self.recipient2],
            subject='Test Subject',
            body='Test Body',
            priority='info'
        )

        self.assertIsInstance(message, InternalMessage)
        self.assertEqual(message.sender, self.sender)
        self.assertEqual(message.subject, 'Test Subject')
        self.assertEqual(message.recipients.count(), 2)

        # Verificar que se crearon MessageRecipient
        self.assertEqual(
            MessageRecipient.objects.filter(message=message).count(),
            2
        )

    def test_send_message_cnst024_validation(self):
        """Test: CNST-024 - Validación de 50 destinatarios"""
        # Crear 51 usuarios
        recipients = []
        for i in range(51):
            user = User.objects.create_user(
                username=f'user{i}',
                password='password123'
            )
            recipients.append(user)

        # Debe lanzar ValidationError
        with self.assertRaises(ValidationError) as context:
            MessageService.send_message(
                sender=self.sender,
                recipients=recipients,
                subject='Test',
                body='Test'
            )

        # Modelo retorna "Maximo 50 destinatarios permitidos.
        # Recibidos: N (CNST-024)" — capital M con acento.
        self.assertIn('Máximo 50 destinatarios', str(context.exception))

    def test_get_inbox(self):
        """Test: Obtener inbox de usuario"""
        # Crear mensajes
        MessageService.send_message(
            sender=self.sender,
            recipients=[self.recipient1],
            subject='Message 1',
            body='Body 1'
        )
        MessageService.send_message(
            sender=self.sender,
            recipients=[self.recipient1],
            subject='Message 2',
            body='Body 2'
        )

        # Obtener inbox
        inbox = MessageService.get_inbox(user=self.recipient1)

        self.assertEqual(inbox.count(), 2)

    def test_get_inbox_unread_only(self):
        """Test: Filtrar solo no leídos"""
        # Crear mensajes
        message1 = MessageService.send_message(
            sender=self.sender,
            recipients=[self.recipient1],
            subject='Message 1',
            body='Body 1'
        )
        MessageService.send_message(
            sender=self.sender,
            recipients=[self.recipient1],
            subject='Message 2',
            body='Body 2'
        )

        # Marcar uno como leído
        MessageService.mark_as_read(message1, self.recipient1)

        # Obtener solo no leídos
        unread = MessageService.get_inbox(user=self.recipient1, unread_only=True)

        self.assertEqual(unread.count(), 1)

    def test_mark_as_read(self):
        """Test: Marcar mensaje como leído"""
        message = MessageService.send_message(
            sender=self.sender,
            recipients=[self.recipient1],
            subject='Test',
            body='Test'
        )

        # Marcar como leído
        msg_recipient = MessageService.mark_as_read(message, self.recipient1)

        self.assertIsNotNone(msg_recipient.read_at)
        self.assertTrue(msg_recipient.is_read)

    def test_archive_message(self):
        """Test: Archivar mensaje"""
        message = MessageService.send_message(
            sender=self.sender,
            recipients=[self.recipient1],
            subject='Test',
            body='Test'
        )

        # Archivar
        msg_recipient = MessageService.archive_message(message, self.recipient1)

        self.assertIsNotNone(msg_recipient.archived_at)
        self.assertTrue(msg_recipient.is_archived)

    def test_unarchive_message(self):
        """Test: Desarchivar mensaje"""
        message = MessageService.send_message(
            sender=self.sender,
            recipients=[self.recipient1],
            subject='Test',
            body='Test'
        )

        # Archivar primero
        MessageService.archive_message(message, self.recipient1)

        # Desarchivar
        msg_recipient = MessageService.unarchive_message(message, self.recipient1)

        self.assertIsNone(msg_recipient.archived_at)
        self.assertFalse(msg_recipient.is_archived)


class AlertServiceTest(TestCase):
    """Tests para AlertService"""

    def test_evaluate_condition_structure(self):
        """Test: Validar estructura de condition"""
        # Condition válido
        valid_condition = {
            'metric': 'call_volume',
            'operator': '>',
            'value': 100,
            'period': '1h'
        }

        # Debe retornar boolean sin error
        result = AlertService._evaluate_condition(valid_condition)
        self.assertIsInstance(result, bool)

    def test_evaluate_operator(self):
        """Test: Evaluar operadores"""
        # Operator >
        self.assertTrue(AlertService._evaluate_operator(150, '>', 100))
        self.assertFalse(AlertService._evaluate_operator(50, '>', 100))

        # Operator <
        self.assertTrue(AlertService._evaluate_operator(50, '<', 100))
        self.assertFalse(AlertService._evaluate_operator(150, '<', 100))

        # Operator ==
        self.assertTrue(AlertService._evaluate_operator(100, '==', 100))
        self.assertFalse(AlertService._evaluate_operator(99, '==', 100))


class SubscriptionServiceTest(TestCase):
    """Tests para SubscriptionService"""

    def setUp(self):
        """Setup para todos los tests"""
        self.user = User.objects.create_user(
            username='testuser',
            password='password123'
        )
        self.config = AlertConfiguration.objects.create(
            name='Test Alert',
            condition={
                'metric': 'call_volume',
                'operator': '>',
                'value': 100,
                'period': '1h'
            }
        )

    def test_subscribe(self):
        """Test: Suscribir usuario a alerta"""
        subscription = SubscriptionService.subscribe(
            user=self.user,
            alert_configuration=self.config
        )

        self.assertIsInstance(subscription, AlertSubscription)
        self.assertEqual(subscription.user, self.user)
        self.assertEqual(subscription.alert_configuration, self.config)
        self.assertTrue(subscription.is_active)

    def test_unsubscribe(self):
        """Test: Desuscribir usuario"""
        # Suscribir primero
        SubscriptionService.subscribe(
            user=self.user,
            alert_configuration=self.config
        )

        # Desuscribir
        result = SubscriptionService.unsubscribe(
            user=self.user,
            alert_configuration=self.config
        )

        self.assertTrue(result)

        # Verificar que is_active = False
        subscription = AlertSubscription.objects.get(
            user=self.user,
            alert_configuration=self.config
        )
        self.assertFalse(subscription.is_active)

    def test_get_user_subscriptions(self):
        """Test: Obtener suscripciones de usuario"""
        # Crear 2 configuraciones y suscribirse
        config2 = AlertConfiguration.objects.create(
            name='Alert 2',
            condition={
                'metric': 'avg_wait_time',
                'operator': '>',
                'value': 60,
                'period': '30m'
            }
        )

        SubscriptionService.subscribe(self.user, self.config)
        SubscriptionService.subscribe(self.user, config2)

        # Obtener suscripciones
        subscriptions = SubscriptionService.get_user_subscriptions(self.user)

        self.assertEqual(subscriptions.count(), 2)
