"""
Tests unitarios para services de authentication.

CLEAN_CODE v3.0.1: Tests con factories.
CNST-010: Tests usan PostgreSQL (NO cache).
"""

import pytest
from django.test import RequestFactory

from apps.authentication.services import (
    LockoutService,
    AuthenticationService,
    RecoveryService,
    SessionService
)
from apps.authentication.models import LoginLockout
from apps.authentication.exceptions import (
    InvalidCredentialsError,
    AccountLockedError,
    InsufficientSecurityQuestionsError,
    InvalidSecurityAnswersError
)
from tests.factories import (
    UserFactory,
    SecurityQuestionFactory,
    UserSecurityAnswerFactory,
    SessionLogFactory
)


# ============================================================================
# TESTS LOCKOUT SERVICE
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestLockoutService:
    """
    Tests unitarios para LockoutService.
    
    Verifica:
    - BaseService inheritance
    - Lockout después de 5 intentos
    """
    
    def setup_method(self):
        """
        Setup antes de cada test.
        
        CNST-010: Limpia LoginLockout de BD (NO cache).
        """
        self.service = LockoutService()
        # Limpiar registros de lockout en BD
        LoginLockout.objects.all().delete()
    
    def test_inherits_from_base_service(self):
        """Test que hereda de BaseService."""
        assert hasattr(self.service, 'log_info')
        assert hasattr(self.service, 'log_warning')
        assert hasattr(self.service, 'log_error')
    
    def test_record_failed_attempt_increments(self):
        """Test record_failed_attempt incrementa contador."""
        count1 = self.service.record_failed_attempt('testuser')
        assert count1 == 1
        
        count2 = self.service.record_failed_attempt('testuser')
        assert count2 == 2
    
    def test_lockout_after_max_attempts(self):
        """Test bloqueo después de 5 intentos."""
        for i in range(4):
            self.service.record_failed_attempt('testuser')
            assert self.service.is_locked('testuser') is False
        
        # 5to intento bloquea
        self.service.record_failed_attempt('testuser')
        assert self.service.is_locked('testuser') is True
    
    def test_unlock_account(self):
        """Test unlock_account limpia lockout."""
        for i in range(5):
            self.service.record_failed_attempt('testuser')
        
        assert self.service.is_locked('testuser') is True
        
        self.service.unlock_account('testuser')
        
        assert self.service.is_locked('testuser') is False
        assert self.service.get_failed_attempts_count('testuser') == 0


# ============================================================================
# TESTS AUTHENTICATION SERVICE
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestAuthenticationService:
    """
    Tests unitarios para AuthenticationService.
    
    Verifica:
    - BaseService inheritance
    - Uso de helpers from apps.utils
    """
    
    def setup_method(self):
        """
        Setup antes de cada test.
        
        CNST-010: Limpia LoginLockout de BD (NO cache).
        """
        self.service = AuthenticationService()
        self.factory = RequestFactory()
        # Limpiar registros de lockout en BD
        LoginLockout.objects.all().delete()
    
    def test_inherits_from_base_service(self):
        """Test que hereda de BaseService."""
        assert hasattr(self.service, 'log_info')
        assert hasattr(self.service, 'log_warning')
    
    def test_uses_helpers_from_apps_utils(self):
        """Test importa helpers de apps.utils."""
        from apps.authentication.services.authentication import (
            get_client_ip,
            get_user_agent
        )
        
        request = self.factory.post('/login/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        request.META['HTTP_USER_AGENT'] = 'Test'
        
        ip = get_client_ip(request)
        agent = get_user_agent(request)
        
        assert ip is not None
        assert agent is not None
    
    def test_login_user_success(self):
        """Test login exitoso."""
        user = UserFactory(password='testpass123')
        user.set_password('testpass123')
        user.save()
        
        request = self.factory.post('/login/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        request.META['HTTP_USER_AGENT'] = 'Test'
        request.session = {}
        
        result = self.service.login_user(
            request=request,
            username=user.username,
            password='testpass123'
        )
        
        assert result['user'] == user
        assert 'token' in result
        assert 'session_key' in result
        assert 'first_login' in result
    
    def test_login_user_invalid_credentials(self):
        """Test login con credenciales inválidas lanza InvalidCredentialsError."""
        user = UserFactory(password='testpass123')

        request = self.factory.post('/login/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        request.META['HTTP_USER_AGENT'] = 'Test'
        request.session = {}

        with pytest.raises(InvalidCredentialsError):
            self.service.login_user(
                request=request,
                username=user.username,
                password='wrongpassword'
            )

    def test_login_user_account_locked_lanza_account_locked_error(self):
        """Test login con cuenta bloqueada lanza AccountLockedError."""
        user = UserFactory()
        user.set_password('pass1234')
        user.save()

        # Bloquear la cuenta
        from apps.authentication.services import LockoutService
        lockout_service = LockoutService()
        for _ in range(5):
            lockout_service.record_failed_attempt(user.username)

        request = self.factory.post('/login/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        request.META['HTTP_USER_AGENT'] = 'Test'
        request.session = {}

        with pytest.raises(AccountLockedError):
            self.service.login_user(
                request=request,
                username=user.username,
                password='pass1234'
            )

    def test_login_user_inactive_lanza_user_inactive_error(self):
        """Test login con usuario inactivo lanza UserInactiveError."""
        from apps.authentication.exceptions import UserInactiveError

        user = UserFactory(is_active=False)
        user.set_password('pass1234')
        user.save()

        request = self.factory.post('/login/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        request.META['HTTP_USER_AGENT'] = 'Test'
        request.session = {}

        with pytest.raises(UserInactiveError):
            self.service.login_user(
                request=request,
                username=user.username,
                password='pass1234'
            )

    def test_login_user_first_login_true_en_primer_acceso(self):
        """Test que first_login es True cuando no hay LoginAttempts exitosos previos."""
        user = UserFactory()
        user.set_password('pass1234')
        user.save()

        request = self.factory.post('/login/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        request.META['HTTP_USER_AGENT'] = 'Test'
        request.session = {}

        result = self.service.login_user(
            request=request,
            username=user.username,
            password='pass1234'
        )

        assert result['first_login'] is True

    def test_login_user_first_login_false_en_segundo_acceso(self):
        """Test que first_login es False cuando ya existe un LoginAttempt exitoso previo."""
        from tests.factories import LoginAttemptFactory

        user = UserFactory()
        user.set_password('pass1234')
        user.save()

        # Simular que ya hubo un login exitoso anterior
        LoginAttemptFactory(user=user, username=user.username, success=True)

        request = self.factory.post('/login/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        request.META['HTTP_USER_AGENT'] = 'Test'
        request.session = {}

        result = self.service.login_user(
            request=request,
            username=user.username,
            password='pass1234'
        )

        assert result['first_login'] is False


# ============================================================================
# TESTS RECOVERY SERVICE
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestRecoveryService:
    """
    Tests unitarios para RecoveryService.
    
    Verifica:
    - get_available_questions() usa active()
    """
    
    def setup_method(self):
        """Setup antes de cada test."""
        self.service = RecoveryService()
    
    def test_inherits_from_base_service(self):
        """Test que hereda de BaseService."""
        assert hasattr(self.service, 'log_info')
    
    def test_get_available_questions_uses_active(self):
        """Test get_available_questions() usa active()."""
        # Crear 10 preguntas
        questions = SecurityQuestionFactory.create_batch(10)
        
        # Soft delete una
        questions[0].delete()
        
        # [SUCCESS] active() debe excluir soft deleted
        available = self.service.get_available_questions()
        
        assert len(available) == 9
        assert questions[0] not in available
    
    def test_get_available_questions_insufficient(self):
        """Test con menos de 10 preguntas lanza error."""
        SecurityQuestionFactory.create_batch(5)
        
        with pytest.raises(InsufficientSecurityQuestionsError):
            self.service.get_available_questions()
    
    def test_verify_security_answers_correct(self):
        """Test verificar respuestas correctas."""
        user = UserFactory()
        questions = SecurityQuestionFactory.create_batch(5)
        
        # Configurar respuestas
        answers_data = []
        for i, q in enumerate(questions):
            UserSecurityAnswerFactory(
                user=user,
                question=q,
                answer_text=f'Respuesta {i}',
                created_by=user
            )
            answers_data.append({
                'question_id': q.id,
                'answer': f'Respuesta {i}'
            })
        
        # Verificar
        verified = self.service.verify_security_answers(
            username=user.username,
            answers_data=answers_data
        )
        
        assert verified is True


# ============================================================================
# TESTS SESSION SERVICE
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestSessionService:
    """
    Tests unitarios para SessionService.
    
    Verifica:
    - get_active_sessions() usa active()
    """
    
    def setup_method(self):
        """Setup antes de cada test."""
        self.service = SessionService()
    
    def test_inherits_from_base_service(self):
        """Test que hereda de BaseService."""
        assert hasattr(self.service, 'log_info')
    
    def test_get_active_sessions_uses_active(self):
        """Test get_active_sessions() usa active()."""
        user = UserFactory()
        
        # Crear 2 sesiones
        s1 = SessionLogFactory(user=user, created_by=user)
        s2 = SessionLogFactory(user=user, created_by=user)
        
        # Soft delete s1
        s1.delete()
        
        # [SUCCESS] active() debe excluir soft deleted
        active = self.service.get_active_sessions(user)
        
        assert len(active) == 1
        assert s2 in active
        assert s1 not in active
    
    def test_invalidate_session(self):
        """Test invalidar sesión."""
        user = UserFactory()
        session = SessionLogFactory(user=user, is_active=True, created_by=user)
        
        self.service.invalidate_session(session.session_key, user)
        
        session.refresh_from_db()
        assert session.is_active is False
        assert session.logout_at is not None
