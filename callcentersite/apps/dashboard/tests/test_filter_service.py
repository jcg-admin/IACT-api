"""
Tests para FilterService.

Pruebas de:
- apply_filter_to_queryset
- validate_filter_config
- parse_date_range

FASE 7: Tests de services.
"""

from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.pipeline.models import CallRecord
from apps.dashboard.services import FilterService

User = get_user_model()


class FilterServiceTestCase(TestCase):
    """Tests para FilterService."""
    
    @classmethod
    def setUpTestData(cls):
        """Configurar datos de prueba."""
        cls.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Crear registros de llamadas de prueba
        cls.call1 = CallRecord.objects.create(
            fecha=date.today(),
            telefono='1234567890',
            servicio_800='8001234567',
            total_llamadas=10,
            llamadas_contestadas=8,
            llamadas_abandonadas=2,
            duracion_total_segundos=600,
            call_type='inbound'
        )
        
        cls.call2 = CallRecord.objects.create(
            fecha=date.today() - timedelta(days=1),
            telefono='0987654321',
            servicio_800='8007654321',
            total_llamadas=5,
            llamadas_contestadas=3,
            llamadas_abandonadas=2,
            duracion_total_segundos=300,
            call_type='outbound'
        )
        
        cls.call3 = CallRecord.objects.create(
            fecha=date.today() - timedelta(days=7),
            telefono='5555555555',
            servicio_800='8005555555',
            total_llamadas=15,
            llamadas_contestadas=12,
            llamadas_abandonadas=3,
            duracion_total_segundos=900,
            call_type='transfer'
        )
    
    def test_apply_filter_date_from(self):
        """Test filtro por fecha desde."""
        filter_config = {
            'date_from': str(date.today() - timedelta(days=2))
        }
        
        queryset = CallRecord.objects.all()
        filtered = FilterService.apply_filter_to_queryset(queryset, filter_config)
        
        self.assertEqual(filtered.count(), 2)
        self.assertIn(self.call1, filtered)
        self.assertIn(self.call2, filtered)
        self.assertNotIn(self.call3, filtered)
    
    def test_apply_filter_date_to(self):
        """Test filtro por fecha hasta."""
        filter_config = {
            'date_to': str(date.today() - timedelta(days=2))
        }
        
        queryset = CallRecord.objects.all()
        filtered = FilterService.apply_filter_to_queryset(queryset, filter_config)
        
        self.assertEqual(filtered.count(), 1)
        self.assertIn(self.call3, filtered)
    
    def test_apply_filter_did(self):
        """Test filtro por DID (servicio_800)."""
        filter_config = {
            'did': '8001234567'
        }
        
        queryset = CallRecord.objects.all()
        filtered = FilterService.apply_filter_to_queryset(queryset, filter_config)
        
        self.assertEqual(filtered.count(), 1)
        self.assertIn(self.call1, filtered)
    
    def test_apply_filter_call_type(self):
        """Test filtro por tipo de llamada."""
        filter_config = {
            'call_type': 'transfer'
        }
        
        queryset = CallRecord.objects.all()
        filtered = FilterService.apply_filter_to_queryset(queryset, filter_config)
        
        self.assertEqual(filtered.count(), 1)
        self.assertIn(self.call3, filtered)
    
    def test_apply_filter_min_duration(self):
        """Test filtro por duración mínima."""
        filter_config = {
            'min_duration': 400
        }
        
        queryset = CallRecord.objects.all()
        filtered = FilterService.apply_filter_to_queryset(queryset, filter_config)
        
        self.assertEqual(filtered.count(), 2)
        self.assertIn(self.call1, filtered)
        self.assertIn(self.call3, filtered)
    
    def test_apply_filter_max_duration(self):
        """Test filtro por duración máxima."""
        filter_config = {
            'max_duration': 700
        }
        
        queryset = CallRecord.objects.all()
        filtered = FilterService.apply_filter_to_queryset(queryset, filter_config)
        
        self.assertEqual(filtered.count(), 2)
        self.assertIn(self.call1, filtered)
        self.assertIn(self.call2, filtered)
    
    def test_apply_filter_combined(self):
        """Test filtro con múltiples condiciones."""
        filter_config = {
            'date_from': str(date.today() - timedelta(days=2)),
            'call_type': 'inbound',
            'min_duration': 500
        }
        
        queryset = CallRecord.objects.all()
        filtered = FilterService.apply_filter_to_queryset(queryset, filter_config)
        
        self.assertEqual(filtered.count(), 1)
        self.assertIn(self.call1, filtered)
    
    def test_validate_filter_config_valid(self):
        """Test validación de configuración válida."""
        filter_config = {
            'date_from': '2025-01-01',
            'date_to': '2025-01-31',
            'did': '8001234567',
            'call_type': 'inbound',
            'min_duration': 0,
            'max_duration': 3600
        }
        
        # No debería lanzar excepción
        FilterService.validate_filter_config(filter_config)
    
    def test_validate_filter_config_invalid_date_format(self):
        """Test validación con formato de fecha inválido."""
        filter_config = {
            'date_from': '01/01/2025'  # Formato incorrecto
        }
        
        with self.assertRaises(ValueError) as context:
            FilterService.validate_filter_config(filter_config)
        
        self.assertIn('formato', str(context.exception).lower())
    
    def test_validate_filter_config_date_range_invalid(self):
        """Test validación con rango de fechas inválido."""
        filter_config = {
            'date_from': '2025-01-31',
            'date_to': '2025-01-01'
        }
        
        with self.assertRaises(ValueError) as context:
            FilterService.validate_filter_config(filter_config)
        
        self.assertIn('date_from', str(context.exception).lower())
    
    def test_validate_filter_config_negative_duration(self):
        """Test validación con duración negativa."""
        filter_config = {
            'min_duration': -100
        }
        
        with self.assertRaises(ValueError) as context:
            FilterService.validate_filter_config(filter_config)
        
        self.assertIn('negativo', str(context.exception).lower())
    
    def test_parse_date_range_today(self):
        """Test parseo de rango 'today'."""
        date_from, date_to = FilterService.parse_date_range('today')
        
        self.assertEqual(date_from, date.today())
        self.assertEqual(date_to, date.today())
    
    def test_parse_date_range_yesterday(self):
        """Test parseo de rango 'yesterday'."""
        date_from, date_to = FilterService.parse_date_range('yesterday')
        
        expected = date.today() - timedelta(days=1)
        self.assertEqual(date_from, expected)
        self.assertEqual(date_to, expected)
    
    def test_parse_date_range_last_7_days(self):
        """Test parseo de rango 'last_7_days'."""
        date_from, date_to = FilterService.parse_date_range('last_7_days')
        
        self.assertEqual(date_from, date.today() - timedelta(days=6))
        self.assertEqual(date_to, date.today())
    
    def test_parse_date_range_last_30_days(self):
        """Test parseo de rango 'last_30_days'."""
        date_from, date_to = FilterService.parse_date_range('last_30_days')
        
        self.assertEqual(date_from, date.today() - timedelta(days=29))
        self.assertEqual(date_to, date.today())
    
    def test_parse_date_range_this_week(self):
        """Test parseo de rango 'this_week'."""
        date_from, date_to = FilterService.parse_date_range('this_week')
        
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())
        
        self.assertEqual(date_from, start_of_week)
        self.assertEqual(date_to, today)
    
    def test_parse_date_range_this_month(self):
        """Test parseo de rango 'this_month'."""
        date_from, date_to = FilterService.parse_date_range('this_month')
        
        today = date.today()
        start_of_month = today.replace(day=1)
        
        self.assertEqual(date_from, start_of_month)
        self.assertEqual(date_to, today)
    
    def test_parse_date_range_invalid(self):
        """Test parseo de rango inválido."""
        with self.assertRaises(ValueError):
            FilterService.parse_date_range('invalid_range')
    
    def test_apply_filter_empty_config(self):
        """Test aplicar filtro con configuración vacía."""
        filter_config = {}
        
        queryset = CallRecord.objects.all()
        filtered = FilterService.apply_filter_to_queryset(queryset, filter_config)
        
        # Sin filtros, debería retornar todos
        self.assertEqual(filtered.count(), 3)
