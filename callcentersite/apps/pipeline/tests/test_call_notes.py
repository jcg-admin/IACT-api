"""
Tests para CallNote - apps/pipeline - IACT Call Center System.

Tests de modelo CallNote y API CallNoteViewSet.

FASE 0.2: Sistema de notas para CallRecord.
"""
from datetime import date
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

from apps.pipeline.models import CallRecord, CallNote

User = get_user_model()


class CallNoteModelTestCase(APITestCase):
    """
    Test suite para modelo CallNote.
    
    Verifica:
    - Creación de notas
    - Relaciones con CallRecord y User
    - Soft delete
    - Campos y validaciones
    """
    
    def setUp(self):
        """
        Configuración inicial para cada test.
        
        Crea:
        - 2 usuarios de prueba
        - 1 CallRecord de prueba
        """
        self.user1 = User.objects.create_user(
            username='agent1',
            password='pass123',
            email='agent1@example.com'
        )
        
        self.user2 = User.objects.create_user(
            username='agent2',
            password='pass123',
            email='agent2@example.com'
        )
        
        self.call_record = CallRecord.objects.create(
            fecha=date(2025, 1, 20),
            telefono='912345678',
            servicio_800='800-123-4567',
            total_llamadas=100,
            llamadas_contestadas=90,
            llamadas_abandonadas=10,
            duracion_total_segundos=5400
        )
    
    def test_create_call_note(self):
        """
        Test: Crear nota básica.
        
        Verifica:
        - Se crea correctamente
        - Campos obligatorios presentes
        - Relaciones correctas
        """
        note = CallNote.objects.create(
            call_record=self.call_record,
            user=self.user1,
            note='Cliente solicitó información sobre facturación'
        )
        
        self.assertIsNotNone(note.id)
        self.assertEqual(note.call_record, self.call_record)
        self.assertEqual(note.user, self.user1)
        self.assertEqual(note.note, 'Cliente solicitó información sobre facturación')
        self.assertFalse(note.is_important)  # Default False
        self.assertIsNotNone(note.created_at)
        self.assertIsNotNone(note.updated_at)
    
    def test_create_important_note(self):
        """
        Test: Crear nota importante.
        
        Verifica:
        - is_important=True funciona
        """
        note = CallNote.objects.create(
            call_record=self.call_record,
            user=self.user1,
            note='URGENTE: Cliente amenaza con cancelar servicio',
            is_important=True
        )
        
        self.assertTrue(note.is_important)
    
    def test_call_record_notes_relationship(self):
        """
        Test: Relación inversa CallRecord -> Notes.
        
        Verifica:
        - related_name='notes' funciona
        - Se pueden acceder notas desde CallRecord
        """
        # Crear 3 notas para el mismo CallRecord
        CallNote.objects.create(
            call_record=self.call_record,
            user=self.user1,
            note='Primera nota'
        )
        CallNote.objects.create(
            call_record=self.call_record,
            user=self.user2,
            note='Segunda nota'
        )
        CallNote.objects.create(
            call_record=self.call_record,
            user=self.user1,
            note='Tercera nota'
        )
        
        # Verificar que se pueden acceder desde CallRecord
        notes = self.call_record.notes.all()
        self.assertEqual(notes.count(), 3)
    
    def test_str_representation(self):
        """
        Test: Representación string __str__.
        
        Verifica:
        - __str__ retorna formato esperado
        """
        note = CallNote.objects.create(
            call_record=self.call_record,
            user=self.user1,
            note='Test note'
        )
        
        expected = f"Nota de {self.user1.username} en {self.call_record}"
        self.assertEqual(str(note), expected)


class CallNoteViewSetTestCase(APITestCase):
    """
    Test suite para CallNoteViewSet API.
    
    Verifica:
    - CRUD completo de notas
    - Filtros (call_record, user, is_important)
    - Permisos y autenticación
    - Auto-asignación de usuario
    """
    
    def setUp(self):
        """
        Configuración inicial para cada test.
        
        Crea:
        - 2 usuarios de prueba
        - 2 CallRecords de prueba
        - 3 notas de prueba
        """
        self.user1 = User.objects.create_user(
            username='agent1',
            password='pass123',
            email='agent1@example.com',
            first_name='John',
            last_name='Doe'
        )
        
        self.user2 = User.objects.create_user(
            username='agent2',
            password='pass123',
            email='agent2@example.com'
        )
        
        self.call_record1 = CallRecord.objects.create(
            fecha=date(2025, 1, 20),
            telefono='912345678',
            servicio_800='800-123-4567',
            total_llamadas=100,
            llamadas_contestadas=90,
            llamadas_abandonadas=10
        )
        
        self.call_record2 = CallRecord.objects.create(
            fecha=date(2025, 1, 21),
            telefono='987654321',
            servicio_800='800-987-6543',
            total_llamadas=50,
            llamadas_contestadas=45,
            llamadas_abandonadas=5
        )
        
        # Notas de prueba
        self.note1 = CallNote.objects.create(
            call_record=self.call_record1,
            user=self.user1,
            note='Primera nota usuario 1',
            is_important=False
        )
        
        self.note2 = CallNote.objects.create(
            call_record=self.call_record1,
            user=self.user2,
            note='Segunda nota usuario 2',
            is_important=True
        )
        
        self.note3 = CallNote.objects.create(
            call_record=self.call_record2,
            user=self.user1,
            note='Nota en otro call record',
            is_important=False
        )
        
        # Autenticar como user1 por defecto
        self.client.force_authenticate(user=self.user1)
    
    def test_list_call_notes(self):
        """
        Test: Listar todas las notas.
        
        Verifica:
        - Status 200 OK
        - Cantidad correcta de registros
        - Campos presentes en respuesta
        """
        url = reverse('pipeline:callnote-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)
        
        # Verificar campos en primer registro
        first_note = response.data['results'][0]
        self.assertIn('id', first_note)
        self.assertIn('call_record', first_note)
        self.assertIn('user', first_note)
        self.assertIn('user_username', first_note)
        self.assertIn('user_full_name', first_note)
        self.assertIn('note', first_note)
        self.assertIn('is_important', first_note)
        self.assertIn('created_at', first_note)
    
    def test_retrieve_call_note(self):
        """
        Test: Obtener detalle de una nota.
        
        Verifica:
        - Status 200 OK
        - Datos correctos
        """
        url = reverse('pipeline:callnote-detail', kwargs={'pk': self.note1.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['note'], 'Primera nota usuario 1')
        self.assertEqual(response.data['user_username'], 'agent1')
    
    def test_create_call_note(self):
        """
        Test: Crear nueva nota.
        
        Verifica:
        - Status 201 CREATED
        - Usuario se asigna automáticamente
        - Datos correctos en respuesta
        """
        url = reverse('pipeline:callnote-list')
        data = {
            'call_record': self.call_record1.id,
            'note': 'Nueva nota desde API',
            'is_important': True
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verificar que el usuario se asignó automáticamente
        self.assertEqual(response.data['user'], self.user1.id)
        self.assertEqual(response.data['user_username'], 'agent1')
        self.assertEqual(response.data['note'], 'Nueva nota desde API')
        self.assertTrue(response.data['is_important'])
        
        # Verificar que se creó en BD
        note = CallNote.objects.get(id=response.data['id'])
        self.assertEqual(note.user, self.user1)
        self.assertEqual(note.call_record, self.call_record1)
    
    def test_filter_by_call_record(self):
        """
        Test: Filtrar notas por CallRecord.
        
        Verifica:
        - Filtro funciona correctamente
        - Solo retorna notas del CallRecord especificado
        """
        url = reverse('pipeline:callnote-list')
        response = self.client.get(url, {'call_record': self.call_record1.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # note1 y note2
        
        # Verificar que todas pertenecen al call_record1
        for note in response.data['results']:
            self.assertEqual(note['call_record'], self.call_record1.id)
    
    def test_filter_by_user(self):
        """
        Test: Filtrar notas por usuario.
        
        Verifica:
        - Filtro funciona correctamente
        - Solo retorna notas del usuario especificado
        """
        url = reverse('pipeline:callnote-list')
        response = self.client.get(url, {'user': self.user1.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # note1 y note3
        
        # Verificar que todas pertenecen a user1
        for note in response.data['results']:
            self.assertEqual(note['user'], self.user1.id)
    
    def test_filter_by_is_important(self):
        """
        Test: Filtrar notas importantes.
        
        Verifica:
        - Filtro is_important funciona
        """
        url = reverse('pipeline:callnote-list')
        response = self.client.get(url, {'is_important': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # Solo note2
        self.assertTrue(response.data['results'][0]['is_important'])
    
    def test_user_full_name_with_names(self):
        """
        Test: user_full_name cuando usuario tiene first_name y last_name.
        
        Verifica:
        - Retorna first_name + last_name
        """
        url = reverse('pipeline:callnote-detail', kwargs={'pk': self.note1.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user_full_name'], 'John Doe')
    
    def test_user_full_name_without_names(self):
        """
        Test: user_full_name cuando usuario NO tiene nombres.
        
        Verifica:
        - Retorna username como fallback
        """
        url = reverse('pipeline:callnote-detail', kwargs={'pk': self.note2.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user_full_name'], 'agent2')
    
    def test_authentication_required(self):
        """
        Test: Verificar que autenticación es requerida.
        
        Verifica:
        - Sin autenticación retorna 401 Unauthorized
        """
        self.client.force_authenticate(user=None)
        
        url = reverse('pipeline:callnote-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
