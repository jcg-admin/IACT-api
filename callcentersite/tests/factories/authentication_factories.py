"""
Factories para models de authentication.

Usa factory_boy para crear objetos de prueba.
"""

import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model

from apps.authentication.models import (
    LoginAttempt,
    SecurityQuestion,
    UserSecurityAnswer,
    SessionLog
)

User = get_user_model()


class LoginAttemptFactory(DjangoModelFactory):
    """
    Factory para LoginAttempt.
    
    Usage:
        LoginAttemptFactory()  # Intento fallido
        LoginAttemptFactory(success=True)  # Intento exitoso
        LoginAttemptFactory(user=user)  # Con usuario específico
    """
    
    class Meta:
        model = LoginAttempt
    
    user = None  # Puede ser None si username no existe
    username = factory.Sequence(lambda n: f'user{n}')
    success = False  # Por defecto fallido
    ip_address = '192.168.1.1'
    user_agent = 'Mozilla/5.0 (Test Browser)'


class SecurityQuestionFactory(DjangoModelFactory):
    """
    Factory para SecurityQuestion.
    
    Usage:
        SecurityQuestionFactory()  # Pregunta activa
        SecurityQuestionFactory(is_active=False)  # Pregunta inactiva
        SecurityQuestionFactory.create_batch(10)  # 10 preguntas
    """
    
    class Meta:
        model = SecurityQuestion
    
    question = factory.Sequence(lambda n: f'¿Pregunta de seguridad {n}?')
    is_active = True
    order = factory.Sequence(lambda n: n)


class UserSecurityAnswerFactory(DjangoModelFactory):
    """
    Factory para UserSecurityAnswer.
    
    Usage:
        UserSecurityAnswerFactory(user=user, question=question)
        UserSecurityAnswerFactory(answer_text='Azul')  # Hashea automáticamente
    """
    
    class Meta:
        model = UserSecurityAnswer
    
    user = factory.SubFactory('tests.factories.user_factory.UserFactory')
    question = factory.SubFactory(SecurityQuestionFactory)
    answer_hash = 'dummy_hash'  # Se sobreescribe si se usa _create con answer_text
    created_by = factory.SelfAttribute('user')
    
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """
        Override para hashear answer si se proporciona answer_text.
        
        Usage:
            UserSecurityAnswerFactory(answer_text='Mi Respuesta')
        """
        answer_text = kwargs.pop('answer_text', None)
        
        obj = model_class(*args, **kwargs)
        
        if answer_text:
            # [SUCCESS] Usa set_answer() del modelo que hashea con PBKDF2
            obj.set_answer(answer_text)
        
        obj.save()
        return obj


class SessionLogFactory(DjangoModelFactory):
    """
    Factory para SessionLog.
    
    Usage:
        SessionLogFactory(user=user)  # Sesión activa
        SessionLogFactory(is_active=False)  # Sesión cerrada
    """
    
    class Meta:
        model = SessionLog
    
    user = factory.SubFactory('tests.factories.user_factory.UserFactory')
    session_key = factory.Sequence(lambda n: f'session_key_{n}')
    ip_address = '192.168.1.1'
    user_agent = 'Mozilla/5.0 (Test Browser)'
    is_active = True
    logout_at = None
    created_by = factory.SelfAttribute('user')
