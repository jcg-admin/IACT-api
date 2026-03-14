import pytest
from django.contrib.auth.models import User
from apps.authentication.models import SecurityQuestion, UserSecurityAnswer
from apps.authentication.serializers import (
    CustomTokenObtainPairSerializer,
    PasswordResetRequestSerializer,
)


@pytest.mark.unit
@pytest.mark.django_db
class TestCustomTokenObtainPairSerializer:
    """Tests para JWT serializer custom."""
    
    def test_get_token_includes_custom_claims(self):
        """JWT debe incluir username y email."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='test123'
        )
        
        token = CustomTokenObtainPairSerializer.get_token(user)
        
        assert token['username'] == 'testuser'
        assert token['email'] == 'test@example.com'
    
    def test_token_contains_user_id(self):
        """Token debe incluir user_id por defecto."""
        user = User.objects.create_user(
            username='testuser',
            password='test123'
        )
        
        token = CustomTokenObtainPairSerializer.get_token(user)
        
        # SimpleJWT incluye user_id por defecto
        assert 'user_id' in token


@pytest.mark.unit
@pytest.mark.django_db
class TestPasswordResetRequestSerializer:
    """Tests para reset password sin email."""
    
    def test_validate_requires_3_answers(self):
        """Usuario debe tener 3 respuestas configuradas."""
        user = User.objects.create_user('testuser', password='test123')
        
        # Solo 2 respuestas
        q1 = SecurityQuestion.objects.create(question='Q1?')
        q2 = SecurityQuestion.objects.create(question='Q2?')
        
        ans1 = UserSecurityAnswer(user=user, question=q1)
        ans1.set_answer('answer1')
        ans1.save()
        
        ans2 = UserSecurityAnswer(user=user, question=q2)
        ans2.set_answer('answer2')
        ans2.save()
        
        serializer = PasswordResetRequestSerializer(data={
            'username': 'testuser',
            'question1_answer': 'answer1',
            'question2_answer': 'answer2',
            'question3_answer': 'answer3',
            'new_password': 'newpass123',
        })
        
        assert serializer.is_valid() is False
        errors_str = str(serializer.errors).lower()
        assert 'pregunta' in errors_str or 'seguridad' in errors_str
    
    def test_validate_user_not_exists(self):
        """Validar cuando usuario no existe."""
        serializer = PasswordResetRequestSerializer(data={
            'username': 'noexiste',
            'question1_answer': 'a1',
            'question2_answer': 'a2',
            'question3_answer': 'a3',
            'new_password': 'newpass123',
        })
        
        assert serializer.is_valid() is False
        errors_str = str(serializer.errors).lower()
        assert 'usuario' in errors_str or 'exist' in errors_str
    
    def test_validate_success_with_3_answers(self):
        """Validación exitosa con 3 respuestas."""
        user = User.objects.create_user('testuser', password='test123')
        
        # 3 respuestas
        q1 = SecurityQuestion.objects.create(question='Q1?')
        q2 = SecurityQuestion.objects.create(question='Q2?')
        q3 = SecurityQuestion.objects.create(question='Q3?')
        
        ans1 = UserSecurityAnswer(user=user, question=q1)
        ans1.set_answer('answer1')
        ans1.save()
        
        ans2 = UserSecurityAnswer(user=user, question=q2)
        ans2.set_answer('answer2')
        ans2.save()
        
        ans3 = UserSecurityAnswer(user=user, question=q3)
        ans3.set_answer('answer3')
        ans3.save()
        
        serializer = PasswordResetRequestSerializer(data={
            'username': 'testuser',
            'question1_answer': 'answer1',
            'question2_answer': 'answer2',
            'question3_answer': 'answer3',
            'new_password': 'newpass123',
        })
        
        assert serializer.is_valid() is True
        assert serializer.validated_data['user'] == user
    
    def test_save_changes_password(self):
        """save() debe cambiar el password del usuario."""
        user = User.objects.create_user('testuser', password='oldpass')
        
        # 3 respuestas
        q1 = SecurityQuestion.objects.create(question='Q1?')
        q2 = SecurityQuestion.objects.create(question='Q2?')
        q3 = SecurityQuestion.objects.create(question='Q3?')
        
        for q in [q1, q2, q3]:
            ans = UserSecurityAnswer(user=user, question=q)
            ans.set_answer('answer')
            ans.save()
        
        serializer = PasswordResetRequestSerializer(data={
            'username': 'testuser',
            'question1_answer': 'answer',
            'question2_answer': 'answer',
            'question3_answer': 'answer',
            'new_password': 'newpass123',
        })
        
        assert serializer.is_valid()
        serializer.save()
        
        # Verificar password cambió
        user.refresh_from_db()
        assert user.check_password('newpass123') is True
        assert user.check_password('oldpass') is False
