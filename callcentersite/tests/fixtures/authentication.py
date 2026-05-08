"""
Fixtures para authentication tests.

Proporciona fixtures reutilizables para tests de authentication.
"""

import pytest
from tests.testdata import (
    SecurityQuestionTestData,
    UserSecurityAnswerTestData,
    SessionLogTestData,
    UserTestData
)


@pytest.fixture
def security_questions(db):
    """
    Fixture: 10 preguntas de seguridad activas.
    
    Usage:
        def test_something(security_questions):
            assert len(security_questions) == 10
    """
    return SecurityQuestionTestData.create_batch(10)


@pytest.fixture
def user_with_security_answers(db):
    """
    Fixture: Usuario con 5 respuestas de seguridad configuradas.
    
    Usage:
        def test_verify_answers(user_with_security_answers):
            user, answers = user_with_security_answers
            assert user.security_answers.count() == 5
    """
    user = UserTestData()
    questions = SecurityQuestionTestData.create_batch(5)
    
    answers = []
    for i, question in enumerate(questions):
        answer = UserSecurityAnswerTestData(
            user=user,
            question=question,
            answer_text=f'Respuesta {i+1}',
            created_by=user
        )
        answers.append(answer)
    
    return user, answers


@pytest.fixture
def active_session(db):
    """
    Fixture: Sesión activa para un usuario.
    
    Usage:
        def test_session(active_session):
            assert active_session.is_active is True
    """
    user = UserTestData()
    return SessionLogTestData(
        user=user,
        is_active=True,
        created_by=user
    )


@pytest.fixture
def inactive_session(db):
    """
    Fixture: Sesión cerrada (logout).
    
    Usage:
        def test_inactive(inactive_session):
            assert inactive_session.is_active is False
            assert inactive_session.logout_at is not None
    """
    from django.utils import timezone
    from datetime import timedelta
    
    user = UserTestData()
    session = SessionLogTestData(
        user=user,
        is_active=False,
        created_by=user
    )
    
    # Simular logout 1 hora después del login
    session.logout_at = session.created_at + timedelta(hours=1)
    session.save()
    
    return session
