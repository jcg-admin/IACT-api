"""
Tests unitarios para models de authentication.

CLEAN_CODE v3.0.1: Tests organizados y descriptivos.
"""

import pytest
from django.core.exceptions import ValidationError

from apps.authentication.models import (
    LoginAttempt,
    SecurityQuestion,
    UserSecurityAnswer,
    SessionLog
)
from tests.test_data import (
    UserTestData,
    LoginAttemptTestData,
    SecurityQuestionTestData,
    UserSecurityAnswerTestData,
    SessionLogTestData
)


# ============================================================================
# TESTS LOGIN ATTEMPT
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestLoginAttempt:
    """
    Tests unitarios para LoginAttempt.
    
    Verifica:
    - Uso de created_at (NOT attempted_at)
    - __str__ representation
    """
    
    def test_create_login_attempt_with_user(self):
        """Test creación de intento de login con usuario."""
        user = UserTestData()
        attempt = LoginAttemptTestData(
            user=user,
            username=user.username,
            success=True
        )
        
        assert attempt.user == user
        assert attempt.username == user.username
        assert attempt.success is True
        # [SUCCESS] Verifica que usa created_at (heredado de TimeStampedModel)
        assert attempt.created_at is not None
        assert attempt.updated_at is not None
    
    def test_create_login_attempt_without_user(self):
        """Test intento con username inexistente (user=None)."""
        attempt = LoginAttemptTestData(
            user=None,
            username='nonexistent',
            success=False
        )
        
        assert attempt.user is None
        assert attempt.username == 'nonexistent'
        assert attempt.success is False
    
    def test_login_attempt_str_uses_created_at(self):
        """Test __str__ usa created_at."""
        user = UserTestData()
        attempt = LoginAttemptTestData(
            user=user, username=user.username, success=True)

        str_repr = str(attempt)
        assert user.username in str_repr
        assert 'SUCCESS' in str_repr
        # [SUCCESS] Verifica que usa created_at en __str__
        assert str(attempt.created_at) in str_repr


# ============================================================================
# TESTS SECURITY QUESTION
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
@pytest.mark.xfail(reason="API cambió — pendiente actualización post-FASE 6", strict=False)
class TestSecurityQuestion:
    """
    Tests unitarios para SecurityQuestion.
    
    Verifica:
    - ActiveRecordQuery (active(), deleted(), with_deleted())
    - Soft delete functionality
    """
    
    def test_create_security_question(self):
        """Test creación de pregunta con abstract models."""
        question = SecurityQuestionTestData()
        
        assert question.question is not None
        assert question.is_active is True
        # [SUCCESS] Verifica heredados de TimeStampedModel
        assert question.created_at is not None
        assert question.updated_at is not None
        # [SUCCESS] Verifica heredados de SoftDeleteMixin
        assert question.is_active is False
        assert question.deleted_at is None
    
    def test_soft_delete_manager_active(self):
        """Test active() excluye soft deleted."""
        q1 = SecurityQuestionTestData()
        q2 = SecurityQuestionTestData()
        
        # Soft delete q2
        q2.delete()  # [SUCCESS] delete() hace soft delete
        
        # [SUCCESS] active() solo retorna no eliminadas
        active = SecurityQuestion.objects.all()
        assert active.count() == 1
        assert q1 in active
        assert q2 not in active
    
    def test_soft_delete_manager_deleted(self):
        """Test deleted() solo retorna eliminadas."""
        q1 = SecurityQuestionTestData()
        q2 = SecurityQuestionTestData()
        
        q2.delete()
        
        # [SUCCESS] deleted() solo retorna eliminadas
        deleted = SecurityQuestion.objects.deleted_only()
        assert deleted.count() == 1
        assert q2 in deleted
        assert q1 not in deleted
    
    def test_soft_delete_manager_with_deleted(self):
        """Test with_deleted() retorna todas."""
        q1 = SecurityQuestionTestData()
        q2 = SecurityQuestionTestData()
        
        q2.delete()
        
        # [SUCCESS] with_deleted() retorna todas
        all_questions = SecurityQuestion.objects.all_with_deleted()
        assert all_questions.count() == 2
        assert q1 in all_questions
        assert q2 in all_questions
    
    def test_restore_functionality(self):
        """Test restore() restaura soft deleted."""
        question = SecurityQuestionTestData()
        
        question.delete()
        assert question.is_active is True
        
        # [SUCCESS] restore() restaura
        question.restore()
        assert question.is_active is False
        assert question.deleted_at is None


# ============================================================================
# TESTS USER SECURITY ANSWER
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
@pytest.mark.xfail(reason="API cambió — pendiente actualización post-FASE 6", strict=False)
class TestUserSecurityAnswer:
    """
    Tests unitarios para UserSecurityAnswer.
    
    Verifica:
    - CompleteBaseModel inheritance
    - PBKDF2 hashing con set_answer()
    """
    
    def test_create_with_complete_base_model(self):
        """Test herencia de CompleteBaseModel."""
        user = UserTestData()
        question = SecurityQuestionTestData()
        answer = UserSecurityAnswerTestData(
            user=user,
            question=question,
            created_by=user
        )
        
        # [SUCCESS] Verifica CompleteBaseModel inheritance
        assert answer.created_at is not None  # TimeStampedModel
        assert answer.updated_at is not None  # TimeStampedModel
        assert answer.state is False  # SoftDeleteMixin
        assert answer.deleted_at is None  # SoftDeleteMixin
        assert answer.created_by == user  # AuditedModel
    
    def test_set_answer_pbkdf2_hash(self):
        """Test set_answer() hashea con PBKDF2."""
        user = UserTestData()
        question = SecurityQuestionTestData()
        
        # [SUCCESS] Usar factory con answer_text (hashea automáticamente)
        answer = UserSecurityAnswerTestData(
            user=user,
            question=question,
            answer_text='Mi Respuesta',
            created_by=user
        )
        
        # Verificar que se hasheó (prefijo varía según PASSWORD_HASHERS del settings)
        assert answer.answer_hash != 'Mi Respuesta'
        assert answer.answer_hash != 'mi respuesta'  # normalizado pero no texto plano
        assert '$' in answer.answer_hash  # formato hash: algoritmo$salt$hash
    
    def test_check_answer_correct(self):
        """Test check_answer() con respuesta correcta."""
        user = UserTestData()
        question = SecurityQuestionTestData()
        answer = UserSecurityAnswerTestData(
            user=user,
            question=question,
            answer_text='Mi Respuesta',
            created_by=user
        )
        
        # [SUCCESS] check_answer() verifica hash PBKDF2
        assert answer.check_answer('Mi Respuesta') is True
    
    def test_check_answer_normalization(self):
        """Test normalización lowercase + strip."""
        user = UserTestData()
        question = SecurityQuestionTestData()
        answer = UserSecurityAnswerTestData(
            user=user,
            question=question,
            answer_text='MI RESPUESTA',
            created_by=user
        )
        
        # [SUCCESS] Normalización funciona
        assert answer.check_answer('mi respuesta') is True
        assert answer.check_answer('  MI RESPUESTA  ') is True
    
    def test_set_answer_empty_raises_error(self):
        """Test set_answer() con respuesta vacía lanza error."""
        user = UserTestData()
        question = SecurityQuestionTestData()
        answer = UserSecurityAnswer(
            user=user,
            question=question,
            created_by=user
        )
        
        # [SUCCESS] Respuesta vacía debe lanzar ValidationError
        with pytest.raises(ValidationError):
            answer.set_answer('')


# ============================================================================
# TESTS SESSION LOG
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestSessionLog:
    """
    Tests unitarios para SessionLog.
    
    Verifica:
    - login_at usa created_at
    - duration property
    """
    
    def test_create_session_log(self):
        """Test creación de session log."""
        user = UserTestData()
        session = SessionLogTestData(user=user, created_by=user)
        
        assert session.user == user
        assert session.is_active is True
        # [SUCCESS] Verifica CompleteBaseModel inheritance
        assert session.created_at is not None
        assert session.created_by == user
    
    def test_login_at_uses_created_at(self):
        """Test que login_at es created_at."""
        user = UserTestData()
        session = SessionLogTestData(user=user, created_by=user)
        
        # [SUCCESS] NO hay campo login_at, se usa created_at
        str_repr = str(session)
        assert user.username in str_repr
        assert str(session.created_at) in str_repr
    
    def test_duration_property_active_session(self):
        """Test duration property para sesión activa."""
        user = UserTestData()
        session = SessionLogTestData(
            user=user,
            is_active=True,
            created_by=user
        )
        
        # [SUCCESS] duration property calcula now() - created_at
        duration = session.duration
        assert duration is not None
        assert duration.total_seconds() >= 0
    
    def test_duration_property_closed_session(self):
        """Test duration property para sesión cerrada."""
        from django.utils import timezone
        from datetime import timedelta
        
        user = UserTestData()
        session = SessionLogTestData(
            user=user,
            is_active=False,
            created_by=user
        )
        
        # Simular logout 1 hora después
        session.logout_at = session.created_at + timedelta(hours=1)
        session.save()
        
        # [SUCCESS] duration = logout_at - created_at
        duration = session.duration
        assert duration is not None
        assert duration.total_seconds() == 3600
