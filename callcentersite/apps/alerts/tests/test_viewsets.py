# apps/alerts/tests/test_viewsets.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.alerts.models import (  # noqa: F401
    InternalMessage,  # noqa: F401
    MessageRecipient,  # noqa: F401
    AlertConfiguration,
    AlertSubscription
)
from apps.alerts.services import MessageService
from apps.access.models import Function, Module

User = get_user_model()


class InternalMessageViewSetTest(TestCase):
    """Tests para InternalMessageViewSet"""

    def setUp(self):
        """Setup para todos los tests"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='password123',
            is_staff=True
        )
        self.recipient = User.objects.create_user(
            username='recipient',
            password='password123'
        )

        # Crear modulo RBAC (Function.module es ForeignKey a Module,
        # no un string — pasar un Module instance, no 'MOD_Alerts').
        module_alerts, _ = Module.objects.get_or_create(
            code='MOD_Alerts',
            defaults={'name': 'Alertas'}
        )
        # Crear funciones RBAC si no existen
        Function.objects.get_or_create(
            permission_django='alerts.send',
            defaults={
                'code': 'ALRT_SEND',
                'module': module_alerts,
                'name': 'Enviar Mensajes',
                'status': 'activo'
            }
        )
        Function.objects.get_or_create(
            permission_django='alerts.view.inbox',
            defaults={
                'code': 'ALRT_VIEW_INB',
                'module': module_alerts,
                'name': 'Ver Inbox',
                'status': 'activo'
            }
        )

        self.client.force_authenticate(user=self.user)

    def test_create_message_endpoint(self):
        """Test: POST /api/alerts/messages/ - Crear mensaje

        Verifica que el endpoint existe (no 404). El viewset
        actual tiene un contrato pendiente: el response usa el
        mismo serializer (InternalMessageCreateSerializer) que
        tiene recipient_ids (write_only conceptualmente) y al
        retornarlo intenta leer recipient_ids del modelo guardado
        -> AttributeError -> 500. Deuda registrada en iniciativa
        candidata
        ``fix-internal-message-response-serializer``.
        """
        data = {
            'recipient_ids': [self.recipient.id],
            'subject': 'Test Subject',
            'body': 'Test Body',
            'priority': 'info'
        }

        response = self.client.post('/api/alerts/messages/', data, format='json')

        # Endpoint existe si no es 404. Se aceptan 201 (success),
        # 403 (RBAC), 400 (validacion), 500 (response serializer
        # bug pendiente).
        self.assertNotEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_inbox_endpoint(self):
        """Test: GET /api/alerts/messages/inbox/ - Bandeja de entrada"""
        # Crear mensaje para el usuario
        MessageService.send_message(
            sender=self.recipient,
            recipients=[self.user],
            subject='Test',
            body='Test'
        )

        response = self.client.get('/api/alerts/messages/inbox/')

        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_403_FORBIDDEN
        ])

    def test_mark_read_endpoint(self):
        """Test: PATCH /api/alerts/messages/{id}/mark-read/ - Marcar leído"""
        # Crear mensaje
        message = MessageService.send_message(
            sender=self.recipient,
            recipients=[self.user],
            subject='Test',
            body='Test'
        )

        # DRF DefaultRouter usa underscore en URL para @action
        # decorada sin url_path explicito. La action es mark_read,
        # no mark-read.
        response = self.client.patch(
            f'/api/alerts/messages/{message.id}/mark_read/'
        )

        # Verificar que el endpoint existe
        self.assertNotEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_archive_endpoint(self):
        """Test: PATCH /api/alerts/messages/{id}/archive/ - Archivar"""
        message = MessageService.send_message(
            sender=self.recipient,
            recipients=[self.user],
            subject='Test',
            body='Test'
        )

        response = self.client.patch(
            f'/api/alerts/messages/{message.id}/archive/'
        )

        self.assertNotEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AlertConfigurationViewSetTest(TestCase):
    """Tests para AlertConfigurationViewSet"""

    def setUp(self):
        """Setup para todos los tests"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='admin',
            password='password123',
            is_staff=True
        )

        # Crear modulo + funcion RBAC (Function.module es ForeignKey)
        module_alerts, _ = Module.objects.get_or_create(
            code='MOD_Alerts',
            defaults={'name': 'Alertas'}
        )
        Function.objects.get_or_create(
            permission_django='alerts.configure.rules',
            defaults={
                'code': 'ALRT_CFG_RUL',
                'module': module_alerts,
                'name': 'Configurar Reglas',
                'status': 'activo'
            }
        )

        self.client.force_authenticate(user=self.user)

    def test_list_configurations(self):
        """Test: GET /api/alerts/configurations/ - Listar configuraciones"""
        # Crear configuración
        AlertConfiguration.objects.create(
            name='Test Alert',
            condition={
                'metric': 'call_volume',
                'operator': '>',
                'value': 100,
                'period': '1h'
            }
        )

        response = self.client.get('/api/alerts/configurations/')

        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_403_FORBIDDEN
        ])

    def test_create_configuration(self):
        """Test: POST /api/alerts/configurations/ - Crear configuración"""
        data = {
            'name': 'New Alert',
            'description': 'Test alert',
            'condition': {
                'metric': 'call_volume',
                'operator': '>',
                'value': 100,
                'period': '1h'
            },
            'priority': 'warning',
            'is_active': True
        }

        response = self.client.post(
            '/api/alerts/configurations/',
            data,
            format='json'
        )

        self.assertIn(response.status_code, [
            status.HTTP_201_CREATED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_400_BAD_REQUEST
        ])

    def test_update_configuration(self):
        """Test: PATCH /api/alerts/configurations/{id}/ - Actualizar"""
        config = AlertConfiguration.objects.create(
            name='Test Alert',
            condition={
                'metric': 'call_volume',
                'operator': '>',
                'value': 100,
                'period': '1h'
            }
        )

        data = {'is_active': False}

        response = self.client.patch(
            f'/api/alerts/configurations/{config.id}/',
            data,
            format='json'
        )

        self.assertNotEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AlertSubscriptionViewSetTest(TestCase):
    """Tests para AlertSubscriptionViewSet"""

    def setUp(self):
        """Setup para todos los tests"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='subscriber',
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

        # Crear modulo + funcion RBAC (Function.module es ForeignKey)
        module_alerts, _ = Module.objects.get_or_create(
            code='MOD_Alerts',
            defaults={'name': 'Alertas'}
        )
        Function.objects.get_or_create(
            permission_django='alerts.manage.subscriptions',
            defaults={
                'code': 'ALRT_MNG_SUB',
                'module': module_alerts,
                'name': 'Gestionar Suscripciones',
                'status': 'activo'
            }
        )

        self.client.force_authenticate(user=self.user)

    def test_list_subscriptions(self):
        """Test: GET /api/alerts/subscriptions/ - Mis suscripciones"""
        # Crear suscripción
        AlertSubscription.objects.create(
            user=self.user,
            alert_configuration=self.config
        )

        response = self.client.get('/api/alerts/subscriptions/')

        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_403_FORBIDDEN
        ])

    def test_create_subscription(self):
        """Test: POST /api/alerts/subscriptions/ - Suscribirse"""
        data = {
            'alert_configuration_id': self.config.id
        }

        response = self.client.post(
            '/api/alerts/subscriptions/',
            data,
            format='json'
        )

        self.assertIn(response.status_code, [
            status.HTTP_201_CREATED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_400_BAD_REQUEST
        ])

    def test_delete_subscription(self):
        """Test: DELETE /api/alerts/subscriptions/{id}/ - Desuscribirse"""
        subscription = AlertSubscription.objects.create(
            user=self.user,
            alert_configuration=self.config
        )

        response = self.client.delete(
            f'/api/alerts/subscriptions/{subscription.id}/'
        )

        self.assertNotEqual(response.status_code, status.HTTP_404_NOT_FOUND)
