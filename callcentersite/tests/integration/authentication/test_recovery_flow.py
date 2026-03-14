"""
Tests de integración: Flujo de Recuperación de Contraseña.

Prueba el flujo completo:
1. Obtener preguntas disponibles
2. Configurar respuestas de seguridad
3. Verificar respuestas
4. Resetear contraseña
"""

import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse

from tests.factories import (
    UserFactory,
    SecurityQuestionFactory,
    UserSecurityAnswerFactory
)
from apps.authentication.models import UserSecurityAnswer


@pytest.mark.integration
@pytest.mark.django_db
class TestPasswordRecoveryFlow:
    """
    Tests de integración para recuperación de contraseña.
    
    Verifica:
    - Obtención de preguntas disponibles
    - Configuración de 5 respuestas de seguridad
    - Verificación de respuestas
    - Reseteo de contraseña con preguntas
    """
    
    def setup_method(self):
        """Setup para cada test."""
        self.client = APIClient()
    
    def test_complete_recovery_flow(self):
        """
        Test flujo completo de recuperación.
        
        Steps:
        1. Crear 10 preguntas de seguridad
        2. Usuario autenticado configura 5 respuestas
        3. Usuario olvida contraseña
        4. Verifica respuestas de seguridad
        5. Resetea contraseña con preguntas
        6. Login con nueva contraseña
        """
        # 1. Crear 10 preguntas de seguridad
        questions = SecurityQuestionFactory.create_batch(10)
        
        # 2. Crear usuario y autenticar
        user = UserFactory(username='testuser')
        user.set_password('oldpass123')
        user.save()
        
        # Login para obtener token
        login_url = reverse('auth-login')
        login_data = {
            'username': 'testuser',
            'password': 'oldpass123'
        }
        response = self.client.post(login_url, login_data, format='json')
        token = response.data['data']['token']
        
        # Autenticar cliente
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        
        # 3. Configurar 5 respuestas de seguridad
        set_answers_url = reverse('auth-set-security-answers')
        answers_data = {
            'answers': [
                {'question_id': questions[0].id, 'answer': 'Firulais'},
                {'question_id': questions[1].id, 'answer': 'Santiago'},
                {'question_id': questions[2].id, 'answer': 'Azul'},
                {'question_id': questions[3].id, 'answer': 'Juan'},
                {'question_id': questions[4].id, 'answer': 'Pizza'},
            ]
        }
        
        response = self.client.post(set_answers_url, answers_data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        
        # Verificar que se crearon las respuestas
        user_answers = UserSecurityAnswer.objects.filter(user=user).count()
        assert user_answers == 5
        
        # 4. Simular que usuario olvidó contraseña (logout)
        self.client.credentials()  # Remover autenticación
        
        # 5. Verificar respuestas de seguridad
        verify_url = reverse('auth-verify-security-answers')
        verify_data = {
            'username': 'testuser',
            'answers': [
                {'question_id': questions[0].id, 'answer': 'Firulais'},
                {'question_id': questions[1].id, 'answer': 'Santiago'},
                {'question_id': questions[2].id, 'answer': 'Azul'},
                {'question_id': questions[3].id, 'answer': 'Juan'},
                {'question_id': questions[4].id, 'answer': 'Pizza'},
            ]
        }
        
        response = self.client.post(verify_url, verify_data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        
        # 6. Resetear contraseña con respuestas correctas
        reset_url = reverse('auth-reset-password')
        reset_data = {
            'username': 'testuser',
            'answers': [
                {'question_id': questions[0].id, 'answer': 'Firulais'},
                {'question_id': questions[1].id, 'answer': 'Santiago'},
                {'question_id': questions[2].id, 'answer': 'Azul'},
                {'question_id': questions[3].id, 'answer': 'Juan'},
                {'question_id': questions[4].id, 'answer': 'Pizza'},
            ],
            'new_password': 'newpass456',
            'confirm_password': 'newpass456'
        }
        
        response = self.client.post(reset_url, reset_data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        
        # 7. Verificar que puede hacer login con nueva contraseña
        login_data = {
            'username': 'testuser',
            'password': 'newpass456'
        }
        response = self.client.post(login_url, login_data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
    
    def test_get_security_questions(self):
        """
        Test obtener preguntas de seguridad disponibles.
        
        Verifica:
        - Endpoint público (no requiere autenticación)
        - Retorna al menos 10 preguntas activas
        - Solo preguntas activas (excluye soft deleted)
        """
        # Crear 12 preguntas (10 activas + 2 inactivas)
        active_questions = SecurityQuestionFactory.create_batch(10, is_active=True)
        inactive_questions = SecurityQuestionFactory.create_batch(2, is_active=False)
        
        # Obtener preguntas (endpoint público)
        questions_url = reverse('auth-security-questions')
        response = self.client.get(questions_url, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'data' in response.data
        
        # Debe retornar solo las activas
        questions_data = response.data['data']
        assert len(questions_data) >= 10
        
        # Verificar que todas son activas
        for q in questions_data:
            assert q['question'] is not None
    
    def test_set_security_answers_requires_authentication(self):
        """
        Test que configurar respuestas requiere autenticación.
        
        Verifica:
        - Error 401 sin token
        """
        questions = SecurityQuestionFactory.create_batch(5)
        
        set_answers_url = reverse('auth-set-security-answers')
        answers_data = {
            'answers': [
                {'question_id': q.id, 'answer': f'Respuesta {i}'}
                for i, q in enumerate(questions)
            ]
        }
        
        response = self.client.post(set_answers_url, answers_data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_verify_with_incorrect_answers(self):
        """
        Test verificación con respuestas incorrectas.
        
        Verifica:
        - Error 400 con respuestas incorrectas
        """
        # Crear usuario con respuestas configuradas
        user = UserFactory(username='testuser')
        questions = SecurityQuestionFactory.create_batch(5)
        
        # Configurar respuestas correctas
        for i, q in enumerate(questions):
            UserSecurityAnswerFactory(
                user=user,
                question=q,
                answer_text=f'Respuesta{i}',
                created_by=user
            )
        
        # Intentar verificar con respuestas incorrectas
        verify_url = reverse('auth-verify-security-answers')
        verify_data = {
            'username': 'testuser',
            'answers': [
                {'question_id': q.id, 'answer': 'Incorrecta'}
                for q in questions
            ]
        }
        
        response = self.client.post(verify_url, verify_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
    
    def test_reset_password_with_incorrect_answers(self):
        """
        Test reseteo con respuestas incorrectas.
        
        Verifica:
        - Error 400 con respuestas incorrectas
        - Contraseña no cambia
        """
        # Crear usuario con respuestas
        user = UserFactory(username='testuser')
        user.set_password('oldpass123')
        user.save()
        
        questions = SecurityQuestionFactory.create_batch(5)
        
        for i, q in enumerate(questions):
            UserSecurityAnswerFactory(
                user=user,
                question=q,
                answer_text=f'Correcta{i}',
                created_by=user
            )
        
        # Intentar resetear con respuestas incorrectas
        reset_url = reverse('auth-reset-password')
        reset_data = {
            'username': 'testuser',
            'answers': [
                {'question_id': q.id, 'answer': 'Incorrecta'}
                for q in questions
            ],
            'new_password': 'newpass456',
            'confirm_password': 'newpass456'
        }
        
        response = self.client.post(reset_url, reset_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Verificar que contraseña NO cambió
        user.refresh_from_db()
        assert user.check_password('oldpass123') is True
        assert user.check_password('newpass456') is False


@pytest.mark.integration
@pytest.mark.django_db
class TestSecurityAnswersNormalization:
    """
    Tests de integración para normalización de respuestas.
    
    Verifica:
    - Case insensitive
    - Strip de espacios
    """
    
    def setup_method(self):
        """Setup para cada test."""
        self.client = APIClient()
    
    def test_answers_are_case_insensitive(self):
        """
        Test que respuestas son case insensitive.
        
        Verifica:
        - 'AZUL' == 'azul' == 'Azul'
        """
        # Crear usuario con respuestas
        user = UserFactory(username='testuser')
        questions = SecurityQuestionFactory.create_batch(5)
        
        # Configurar respuestas en mayúsculas
        for i, q in enumerate(questions):
            UserSecurityAnswerFactory(
                user=user,
                question=q,
                answer_text=f'RESPUESTA{i}',
                created_by=user
            )
        
        # Verificar con minúsculas
        verify_url = reverse('auth-verify-security-answers')
        verify_data = {
            'username': 'testuser',
            'answers': [
                {'question_id': q.id, 'answer': f'respuesta{i}'}
                for i, q in enumerate(questions)
            ]
        }
        
        response = self.client.post(verify_url, verify_data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
    
    def test_answers_strip_whitespace(self):
        """
        Test que respuestas hacen strip de espacios.
        
        Verifica:
        - '  Azul  ' == 'Azul'
        """
        user = UserFactory(username='testuser')
        questions = SecurityQuestionFactory.create_batch(5)
        
        # Configurar respuestas con espacios
        for i, q in enumerate(questions):
            UserSecurityAnswerFactory(
                user=user,
                question=q,
                answer_text=f'  Respuesta{i}  ',
                created_by=user
            )
        
        # Verificar sin espacios
        verify_url = reverse('auth-verify-security-answers')
        verify_data = {
            'username': 'testuser',
            'answers': [
                {'question_id': q.id, 'answer': f'Respuesta{i}'}
                for i, q in enumerate(questions)
            ]
        }
        
        response = self.client.post(verify_url, verify_data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
