# apps/alerts/tests/test_models.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from apps.alerts.models import (
    InternalMessage,
    MessageRecipient,
    AlertConfiguration,
    AlertSubscription
)

User = get_user_model()


class InternalMessageModelTest(TestCase):
    """Tests para modelo InternalMessage"""
    
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
    
    def test_create_message(self):
        """Test: Crear mensaje básico"""
        message = InternalMessage.objects.create(
            sender=self.sender,
            subject='Test Subject',
            body='Test Body',
            priority='info'
        )
        message.recipients.add(self.recipient1)
        
        self.assertEqual(message.sender, self.sender)
        self.assertEqual(message.subject, 'Test Subject')
        self.assertEqual(message.body, 'Test Body')
        self.assertEqual(message.priority, 'info')
        self.assertEqual(message.recipients.count(), 1)
    
    def test_cnst024_max_50_recipients(self):
        """Test: CNST-024 - Máximo 50 destinatarios"""
        message = InternalMessage(
            sender=self.sender,
            subject='Test',
            body='Test'
        )
        message.save()
        
        # Crear 51 usuarios
        recipients = []
        for i in range(51):
            user = User.objects.create_user(
                username=f'user{i}',
                password='password123'
            )
            recipients.append(user)
        
        # Agregar 51 destinatarios
        message.recipients.add(*recipients)
        
        # Debe lanzar ValidationError
        with self.assertRaises(ValidationError) as context:
            message.clean()
        
        self.assertIn('máximo 50 destinatarios', str(context.exception))
    
    def test_cnst024_50_recipients_ok(self):
        """Test: CNST-024 - 50 destinatarios es válido"""
        message = InternalMessage(
            sender=self.sender,
            subject='Test',
            body='Test'
        )
        message.save()
        
        # Crear 50 usuarios
        recipients = []
        for i in range(50):
            user = User.objects.create_user(
                username=f'user{i}',
                password='password123'
            )
            recipients.append(user)
        
        message.recipients.add(*recipients)
        
        # No debe lanzar error
        try:
            message.clean()
        except ValidationError:
            self.fail("50 destinatarios debería ser válido")
    
    def test_message_str(self):
        """Test: __str__ method"""
        message = InternalMessage.objects.create(
            sender=self.sender,
            subject='Test Subject',
            body='Test Body'
        )
        
        self.assertEqual(
            str(message),
            f"Message from {self.sender.username}: Test Subject"
        )


class MessageRecipientModelTest(TestCase):
    """Tests para modelo MessageRecipient"""
    
    def setUp(self):
        """Setup para todos los tests"""
        self.sender = User.objects.create_user(
            username='sender',
            password='password123'
        )
        self.recipient = User.objects.create_user(
            username='recipient',
            password='password123'
        )
        self.message = InternalMessage.objects.create(
            sender=self.sender,
            subject='Test',
            body='Test'
        )
        self.message.recipients.add(self.recipient)
    
    def test_is_read_property(self):
        """Test: Propiedad is_read"""
        msg_recipient = MessageRecipient.objects.get(
            message=self.message,
            user=self.recipient
        )
        
        # Inicialmente no leído
        self.assertFalse(msg_recipient.is_read)
        
        # Marcar como leído
        from django.utils import timezone
        msg_recipient.read_at = timezone.now()
        msg_recipient.save()
        
        # Ahora debe ser True
        self.assertTrue(msg_recipient.is_read)
    
    def test_is_archived_property(self):
        """Test: Propiedad is_archived"""
        msg_recipient = MessageRecipient.objects.get(
            message=self.message,
            user=self.recipient
        )
        
        # Inicialmente no archivado
        self.assertFalse(msg_recipient.is_archived)
        
        # Archivar
        from django.utils import timezone
        msg_recipient.archived_at = timezone.now()
        msg_recipient.save()
        
        # Ahora debe ser True
        self.assertTrue(msg_recipient.is_archived)


class AlertConfigurationModelTest(TestCase):
    """Tests para modelo AlertConfiguration"""
    
    def test_create_configuration(self):
        """Test: Crear configuración de alerta"""
        config = AlertConfiguration.objects.create(
            name='High Call Volume',
            description='Alert when call volume > 100',
            condition={
                'metric': 'call_volume',
                'operator': '>',
                'value': 100,
                'period': '1h'
            },
            priority='warning',
            is_active=True
        )
        
        self.assertEqual(config.name, 'High Call Volume')
        self.assertTrue(config.is_active)
        self.assertEqual(config.condition['metric'], 'call_volume')
    
    def test_configuration_str(self):
        """Test: __str__ method"""
        config = AlertConfiguration.objects.create(
            name='Test Alert',
            condition={
                'metric': 'call_volume',
                'operator': '>',
                'value': 100,
                'period': '1h'
            }
        )
        
        self.assertEqual(str(config), 'Test Alert')


class AlertSubscriptionModelTest(TestCase):
    """Tests para modelo AlertSubscription"""
    
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
    
    def test_create_subscription(self):
        """Test: Crear suscripción"""
        subscription = AlertSubscription.objects.create(
            user=self.user,
            alert_configuration=self.config,
            is_active=True
        )
        
        self.assertEqual(subscription.user, self.user)
        self.assertEqual(subscription.alert_configuration, self.config)
        self.assertTrue(subscription.is_active)
        self.assertIsNotNone(subscription.subscribed_at)
    
    def test_unique_together_constraint(self):
        """Test: Constraint unique_together (user, alert_configuration)"""
        # Crear primera suscripción
        AlertSubscription.objects.create(
            user=self.user,
            alert_configuration=self.config
        )
        
        # Intentar crear duplicado debe fallar
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            AlertSubscription.objects.create(
                user=self.user,
                alert_configuration=self.config
            )
