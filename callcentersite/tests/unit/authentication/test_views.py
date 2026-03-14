import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from apps.authentication.models import SecurityQuestion, UserSecurityAnswer


@pytest.mark.unit
@pytest.mark.django_db
class TestCustomTokenObtainPairView:
    """Tests para login JWT."""
    
    def test_login_success(self):
        """Login exitoso devuelve access y refresh token."""
        # Crear usuario
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        client = APIClient()
        url = reverse('authentication:token_obtain_pair')
        
        response = client.post(url, {
            'username': 'testuser',
            'password': 'testpass123'
        }, format='json')
        
        assert response.status_code == 200
        assert 'access' in response.data
        assert 'refresh' in response.data
    
    def test_login_invalid_credentials(self):
        """Login con credenciales invalidas retorna 401."""
        User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        client = APIClient()
        url = reverse('authentication:token_obtain_pair')
        
        response = client.post(url, {
            'username': 'testuser',
            'password': 'wrongpassword'
        }, format='json')
        
        assert response.status_code == 401


@pytest.mark.unit
@pytest.mark.django_db
class TestPasswordResetView:
    """Tests para password reset sin email."""
    
    def test_password_reset_success(self):
        """Reset password exitoso."""
        # Crear usuario con 3 preguntas
        user = User.objects.create_user(
            username='testuser',
            password='oldpass123'
        )
        
        q1 = SecurityQuestion.objects.create(question='Q1?')
        q2 = SecurityQuestion.objects.create(question='Q2?')
        q3 = SecurityQuestion.objects.create(question='Q3?')
        
        for q in [q1, q2, q3]:
            ans = UserSecurityAnswer(user=user, question=q)
            ans.set_answer('answer')
            ans.save()
        
        client = APIClient()
        url = reverse('authentication:password_reset')
        
        response = client.post(url, {
            'username': 'testuser',
            'question1_answer': 'answer',
            'question2_answer': 'answer',
            'question3_answer': 'answer',
            'new_password': 'newpass123'
        }, format='json')
        
        assert response.status_code == 200
        assert 'message' in response.data
        
        # Verificar password cambió
        user.refresh_from_db()
        assert user.check_password('newpass123')
    
    def test_password_reset_user_not_found(self):
        """Password reset con usuario inexistente retorna 400."""
        client = APIClient()
        url = reverse('authentication:password_reset')
        
        response = client.post(url, {
            'username': 'noexiste',
            'question1_answer': 'a1',
            'question2_answer': 'a2',
            'question3_answer': 'a3',
            'new_password': 'newpass123'
        }, format='json')
        
        assert response.status_code == 400
    
    def test_password_reset_insufficient_questions(self):
        """Password reset sin 3 preguntas retorna 400."""
        user = User.objects.create_user(
            username='testuser',
            password='oldpass'
        )
        
        # Solo 2 preguntas
        q1 = SecurityQuestion.objects.create(question='Q1?')
        q2 = SecurityQuestion.objects.create(question='Q2?')
        
        for q in [q1, q2]:
            ans = UserSecurityAnswer(user=user, question=q)
            ans.set_answer('answer')
            ans.save()
        
        client = APIClient()
        url = reverse('authentication:password_reset')
        
        response = client.post(url, {
            'username': 'testuser',
            'question1_answer': 'answer',
            'question2_answer': 'answer',
            'question3_answer': 'answer',
            'new_password': 'newpass123'
        }, format='json')
        
        assert response.status_code == 400
