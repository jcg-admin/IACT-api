"""
Tests para viewsets de apps/ivr - IACT Call Center System.

Verifica API REST READ-ONLY para CallLog legacy.

CNST-003: CallLog es READ-ONLY (MariaDB ivr_legacy)
"""
from datetime import date
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

from apps.ivr.models import CallLog

User = get_user_model()


class CallLogViewSetTestCase(APITestCase):
    """
    Test suite para CallLogViewSet.
    
    Verifica:
    - Listado de call logs
    - Detalle de call log
    - Filtros (fecha, servicio_800)
    - Ordenamiento
    - READ-ONLY (no create/update/delete)
    - Cálculo de métricas (answer_rate, abandon_rate)
    """
    
    def setUp(self):
        """
        Configuración inicial para cada test.
        
        Crea:
        - Usuario de prueba
        - 3 call logs de ejemplo
        """
        # Usuario de prueba
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.client.force_authenticate(user=self.user)
        
        # Call logs de prueba
        # NOTA: CallLog es unmanaged, estos datos solo existen en tests
        self.calllog1 = CallLog.objects.create(
            fecha=date(2025, 1, 15),
            telefono='912345678',
            servicio_800='800-123-4567',
            total_llamadas=100,
            llamadas_contestadas=85,
            llamadas_abandonadas=15
        )
        
        self.calllog2 = CallLog.objects.create(
            fecha=date(2025, 1, 16),
            telefono='987654321',
            servicio_800='800-987-6543',
            total_llamadas=50,
            llamadas_contestadas=40,
            llamadas_abandonadas=10
        )
        
        self.calllog3 = CallLog.objects.create(
            fecha=date(2025, 1, 17),
            telefono='912345678',
            servicio_800='800-123-4567',
            total_llamadas=200,
            llamadas_contestadas=180,
            llamadas_abandonadas=20
        )
    
    def test_list_call_logs(self):
        """
        Test: Listar todos los call logs.
        
        Verifica:
        - Status 200 OK
        - Cantidad correcta de registros
        - Campos esperados en respuesta
        """
        url = reverse('ivr:calllog-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)
        
        # Verificar campos en primer registro
        first_log = response.data['results'][0]
        self.assertIn('id', first_log)
        self.assertIn('fecha', first_log)
        self.assertIn('telefono', first_log)
        self.assertIn('servicio_800', first_log)
        self.assertIn('total_llamadas', first_log)
        self.assertIn('llamadas_contestadas', first_log)
        self.assertIn('llamadas_abandonadas', first_log)
    
    def test_retrieve_call_log(self):
        """
        Test: Obtener detalle de un call log específico.
        
        Verifica:
        - Status 200 OK
        - Datos correctos del registro
        - Métricas calculadas (answer_rate, abandon_rate)
        """
        url = reverse('ivr:calllog-detail', kwargs={'pk': self.calllog1.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['telefono'], '912345678')
        self.assertEqual(response.data['total_llamadas'], 100)
        
        # Verificar métricas calculadas
        self.assertIn('answer_rate', response.data)
        self.assertIn('abandon_rate', response.data)
        self.assertEqual(response.data['answer_rate'], 85.0)  # 85/100 * 100
        self.assertEqual(response.data['abandon_rate'], 15.0)  # 15/100 * 100
    
    def test_filter_by_fecha(self):
        """
        Test: Filtrar call logs por fecha.
        
        Verifica:
        - Filtro funciona correctamente
        - Solo retorna registros de la fecha especificada
        """
        url = reverse('ivr:calllog-list')
        response = self.client.get(url, {'fecha': '2025-01-15'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['fecha'], '2025-01-15')
    
    def test_filter_by_servicio_800(self):
        """
        Test: Filtrar call logs por servicio 800.
        
        Verifica:
        - Filtro funciona correctamente
        - Solo retorna registros del servicio especificado
        """
        url = reverse('ivr:calllog-list')
        response = self.client.get(url, {'servicio_800': '800-123-4567'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # calllog1 y calllog3
        
        # Verificar que todos tienen el servicio correcto
        for log in response.data['results']:
            self.assertEqual(log['servicio_800'], '800-123-4567')
    
    def test_ordering_by_fecha_desc(self):
        """
        Test: Ordenar call logs por fecha descendente.
        
        Verifica:
        - Ordenamiento por defecto es -fecha (más recientes primero)
        - Registros están en orden correcto
        """
        url = reverse('ivr:calllog-list')
        response = self.client.get(url, {'ordering': '-fecha'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar orden descendente
        results = response.data['results']
        self.assertEqual(results[0]['fecha'], '2025-01-17')  # Más reciente
        self.assertEqual(results[1]['fecha'], '2025-01-16')
        self.assertEqual(results[2]['fecha'], '2025-01-15')  # Más antigua
    
    def test_readonly_no_create(self):
        """
        Test: Verificar que NO se permite CREATE.
        
        CNST-003: CallLog es READ-ONLY (MariaDB legacy).
        
        Verifica:
        - POST retorna 405 Method Not Allowed
        """
        url = reverse('ivr:calllog-list')
        data = {
            'fecha': '2025-01-18',
            'telefono': '999999999',
            'servicio_800': '800-999-9999',
            'total_llamadas': 10,
            'llamadas_contestadas': 5,
            'llamadas_abandonadas': 5
        }
        response = self.client.post(url, data)
        
        # ReadOnlyModelViewSet no permite POST
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_readonly_no_update(self):
        """
        Test: Verificar que NO se permite UPDATE.
        
        CNST-003: CallLog es READ-ONLY (MariaDB legacy).
        
        Verifica:
        - PUT retorna 405 Method Not Allowed
        """
        url = reverse('ivr:calllog-detail', kwargs={'pk': self.calllog1.pk})
        data = {
            'total_llamadas': 999
        }
        response = self.client.put(url, data)
        
        # ReadOnlyModelViewSet no permite PUT
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_readonly_no_delete(self):
        """
        Test: Verificar que NO se permite DELETE.
        
        CNST-003: CallLog es READ-ONLY (MariaDB legacy).
        
        Verifica:
        - DELETE retorna 405 Method Not Allowed
        """
        url = reverse('ivr:calllog-detail', kwargs={'pk': self.calllog1.pk})
        response = self.client.delete(url)
        
        # ReadOnlyModelViewSet no permite DELETE
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_metrics_calculation_zero_division(self):
        """
        Test: Verificar manejo de división por cero en métricas.
        
        Cuando total_llamadas = 0, las métricas deben retornar 0.0.
        
        Verifica:
        - answer_rate = 0.0
        - abandon_rate = 0.0
        """
        calllog_zero = CallLog.objects.create(
            fecha=date(2025, 1, 18),
            telefono='000000000',
            servicio_800='800-000-0000',
            total_llamadas=0,
            llamadas_contestadas=0,
            llamadas_abandonadas=0
        )
        
        url = reverse('ivr:calllog-detail', kwargs={'pk': calllog_zero.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['answer_rate'], 0.0)
        self.assertEqual(response.data['abandon_rate'], 0.0)
