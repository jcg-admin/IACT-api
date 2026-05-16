"""
Servicio de recuperación de contraseña mediante preguntas de seguridad.

CLEAN_CODE v3.0.1: Nombre descriptivo.
SOLID SRP: Solo recuperación de contraseña.

CNST-001: SIN email externo, solo preguntas de seguridad.
"""

from typing import List, Dict
from django.contrib.auth import get_user_model

from apps.core.services.base_service import BaseService  # [SUCCESS] BaseService
from apps.authentication.models import SecurityQuestion, UserSecurityAnswer
from apps.authentication.constants import (
    SECURITY_QUESTIONS_REQUIRED,
    SECURITY_QUESTIONS_POOL_MIN
)
from apps.authentication.exceptions import (
    SecurityQuestionsNotConfiguredError,
    InvalidSecurityAnswersError,
    InsufficientSecurityQuestionsError
)

User = get_user_model()


class RecoveryService(BaseService):  # [SUCCESS] Hereda de BaseService
    """
    Servicio de recuperación de contraseña.
    
    SOLID SRP: Solo recuperación mediante preguntas de seguridad.
    
    Responsabilidades:
    - Obtener preguntas disponibles
    - Configurar respuestas de seguridad (primera vez)
    - Verificar respuestas de seguridad
    - Resetear contraseña
    
    CNST-001: SIN email, 5 preguntas de seguridad obligatorias.
    """
    
    def __init__(self):
        """Initialize service."""
        super().__init__()  # [SUCCESS] Llamar super
        self.required_questions = SECURITY_QUESTIONS_REQUIRED
        
        self.log_info(f"RecoveryService initialized: {self.required_questions} questions required")
    
    def get_available_questions(self) -> List[SecurityQuestion]:
        """
        Obtiene preguntas de seguridad disponibles.
        
        SOLID SRP: Solo obtiene preguntas.
        
        Returns:
            List[SecurityQuestion]: Preguntas activas y no eliminadas
        
        Raises:
            InsufficientSecurityQuestionsError: Si hay menos de 10 preguntas
        """
        # [SUCCESS] Usar ActiveRecordQuery.active()
        questions = SecurityQuestion.objects.active().filter(
            is_active=True
        ).order_by('order', 'question')
        
        count = questions.count()
        
        if count < SECURITY_QUESTIONS_POOL_MIN:
            self.log_error(f"Insufficient questions in pool: {count} (required: {SECURITY_QUESTIONS_POOL_MIN})")
            
            raise InsufficientSecurityQuestionsError(
                detail=f"Pool insuficiente de preguntas. Hay {count}, se requieren {SECURITY_QUESTIONS_POOL_MIN}.",
                details={'available': count, 'required': SECURITY_QUESTIONS_POOL_MIN}
            )
        
        self.log_info(f"Retrieved {count} available questions")
        
        return list(questions)
    
    def set_security_answers(
        self,
        user,
        answers_data: List[Dict]
    ) -> bool:
        """
        Configura respuestas de seguridad del usuario.
        
        CNST-001: Usuario debe responder exactamente 5 preguntas.
        
        Args:
            user: User object
            answers_data: Lista de dicts con:
                - question_id: int
                - answer: str
        
        Returns:
            bool: True si configuradas exitosamente
        
        Raises:
            InsufficientSecurityQuestionsError: Si no son 5 preguntas
        """
        # Validar cantidad
        if len(answers_data) != self.required_questions:
            self.log_warning(
                f"Invalid number of questions for user '{user.username}': "
                f"{len(answers_data)} (required: {self.required_questions})"
            )
            
            raise InsufficientSecurityQuestionsError(
                detail=f"Debe proporcionar exactamente {self.required_questions} preguntas.",
                details={
                    'provided': len(answers_data),
                    'required': self.required_questions
                }
            )
        
        # Eliminar respuestas anteriores (soft delete)
        # [SUCCESS] delete() hace soft delete automáticamente
        UserSecurityAnswer.objects.filter(user=user).delete()
        
        self.log_info(f"Deleted previous answers for user '{user.username}'")
        
        # Crear nuevas respuestas
        for answer_data in answers_data:
            question_id = answer_data['question_id']
            answer_text = answer_data['answer']
            
            # Obtener pregunta
            try:
                question = SecurityQuestion.objects.active().get(
                    id=question_id,
                    is_active=True
                )
            except SecurityQuestion.DoesNotExist:
                self.log_error(f"Question {question_id} not found or inactive")
                continue
            
            # Crear respuesta
            user_answer = UserSecurityAnswer(
                user=user,
                question=question,
                created_by=user  # [SUCCESS] Auditoría
            )
            
            # [SUCCESS] set_answer() hashea con PBKDF2
            user_answer.set_answer(answer_text)
            user_answer.save()
            
            self.log_info(f"Saved answer for question '{question.question[:30]}...' for user '{user.username}'")
        
        self.log_info(f"Security answers configured for user '{user.username}'")
        
        return True
    
    def verify_security_answers(
        self,
        username: str,
        answers_data: List[Dict]
    ) -> bool:
        """
        Verifica respuestas de seguridad del usuario.
        
        Args:
            username: Username
            answers_data: Lista de dicts con:
                - question_id: int
                - answer: str
        
        Returns:
            bool: True si todas las respuestas son correctas
        
        Raises:
            SecurityQuestionsNotConfiguredError: Si no tiene preguntas configuradas
            InvalidSecurityAnswersError: Si respuestas incorrectas
        """
        # Obtener usuario
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.log_warning(f"User '{username}' not found")
            raise InvalidSecurityAnswersError(
                detail="Usuario o respuestas incorrectas."
            )
        
        # Verificar que tenga preguntas configuradas
        # [SUCCESS] Usar active() para excluir soft deleted
        user_answers = UserSecurityAnswer.objects.active().filter(
            user=user
        )
        
        if user_answers.count() < self.required_questions:
            self.log_warning(f"User '{username}' has insufficient security questions configured")
            
            raise SecurityQuestionsNotConfiguredError(
                detail="Debe configurar sus preguntas de seguridad primero.",
                details={
                    'configured': user_answers.count(),
                    'required': self.required_questions
                }
            )
        
        # Verificar cada respuesta
        correct_count = 0
        
        for answer_data in answers_data:
            question_id = answer_data['question_id']
            answer_text = answer_data['answer']
            
            try:
                user_answer = user_answers.get(question_id=question_id)
                
                # [SUCCESS] check_answer() verifica hash PBKDF2
                if user_answer.check_answer(answer_text):
                    correct_count += 1
                else:
                    self.log_warning(f"Incorrect answer for question {question_id} from user '{username}'")
            
            except UserSecurityAnswer.DoesNotExist:
                self.log_warning(f"Question {question_id} not configured for user '{username}'")
        
        # Todas deben ser correctas
        if correct_count == len(answers_data):
            self.log_info(f"All security answers correct for user '{username}'")
            return True
        else:
            self.log_warning(
                f"Security answers verification failed for user '{username}': "
                f"{correct_count}/{len(answers_data)} correct"
            )
            
            raise InvalidSecurityAnswersError(
                detail="Las respuestas de seguridad son incorrectas.",
                details={
                    'correct': correct_count,
                    'total': len(answers_data)
                }
            )
    
    def reset_password_by_questions(
        self,
        username: str,
        answers_data: List[Dict],
        new_password: str
    ) -> bool:
        """
        Resetea contraseña después de verificar preguntas de seguridad.
        
        CNST-001: Password reset SIN email.
        
        Args:
            username: Username
            answers_data: Respuestas de seguridad
            new_password: Nueva contraseña
        
        Returns:
            bool: True si reset exitoso
        
        Raises:
            InvalidSecurityAnswersError: Si respuestas incorrectas
        """
        # Verificar respuestas
        self.verify_security_answers(username, answers_data)
        
        # Si llegó aquí, respuestas correctas
        user = User.objects.get(username=username)
        
        # Cambiar password
        # [SUCCESS] set_password() usa PBKDF2
        user.set_password(new_password)
        user.save()
        
        self.log_info(f"Password reset successful for user '{username}'")
        
        return True
