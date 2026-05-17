"""
Tests de integración: Flujo de Recuperación de Contraseña.

Verifica preguntas de seguridad, configuración, verificación y reseteo.
CNST-010: Tests usan PostgreSQL (NO cache).
"""

import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model

from tests.test_data import (
    SecurityQuestionTestData,
    UserSecurityAnswerTestData,
)
from apps.authentication.models import UserSecurityAnswer

User = get_user_model()

# Pool mínimo de preguntas requerido por el sistema
POOL_MIN = 10
# Número exacto de respuestas que el sistema acepta/requiere
ANSWERS_REQUIRED = 5


@pytest.mark.integration
@pytest.mark.django_db
class TestPasswordRecoveryFlow:
    """Tests para el flujo de recuperación de contraseña via preguntas de seguridad."""

    def setup_method(self):
        self.client = APIClient()

    def test_get_security_questions(self):
        """Endpoint público retorna lista de preguntas activas (min POOL_MIN)."""
        SecurityQuestionTestData.create_batch(POOL_MIN)
        SecurityQuestionTestData.create_batch(2, is_active=False)

        url = reverse('authentication:auth-security-questions')
        resp = self.client.get(url, format='json')

        assert resp.status_code == status.HTTP_200_OK
        data = resp.data
        if isinstance(data, dict):
            data = data.get('data', data.get('results', []))
        assert len(data) >= POOL_MIN

    def test_set_security_answers_requires_authentication(self):
        """Configurar respuestas sin autenticación: 401."""
        questions = SecurityQuestionTestData.create_batch(ANSWERS_REQUIRED)
        url = reverse('authentication:auth-set-security-answers')

        resp = self.client.post(url, {
            'answers': [
                {'question_id': q.id, 'answer': f'Respuesta{i}'}
                for i, q in enumerate(questions)
            ]
        }, format='json')

        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_verify_with_incorrect_answers(self):
        """Verificar con respuestas incorrectas: 400."""
        import uuid
        u = uuid.uuid4().hex[:6]
        questions = SecurityQuestionTestData.create_batch(ANSWERS_REQUIRED)
        user = User.objects.create_user(username=f'vfy_{u}', password='OldPassword123!')

        for i, q in enumerate(questions):
            UserSecurityAnswerTestData(
                user=user, question=q,
                answer_text=f'Correcta{i}', created_by=user,
            )

        resp = self.client.post(reverse('authentication:auth-verify-security-answers'), {
            'username': f'vfy_{u}',
            'answers': [
                {'question_id': q.id, 'answer': 'Incorrecta'}
                for q in questions
            ],
        }, format='json')

        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_reset_password_with_incorrect_answers(self):
        """Reseteo con respuestas incorrectas: 400. Contraseña no cambia."""
        import uuid
        u = uuid.uuid4().hex[:6]
        questions = SecurityQuestionTestData.create_batch(ANSWERS_REQUIRED)
        user = User.objects.create_user(username=f'rst_{u}', password='OldPassword123!')

        for i, q in enumerate(questions):
            UserSecurityAnswerTestData(
                user=user, question=q,
                answer_text=f'Correcta{i}', created_by=user,
            )

        resp = self.client.post(reverse('authentication:auth-reset-password'), {
            'username': f'rst_{u}',
            'answers': [
                {'question_id': q.id, 'answer': 'Incorrecta'}
                for q in questions
            ],
            'new_password': 'NewPassword789!',
            'confirm_password': 'NewPassword789!',
        }, format='json')

        assert resp.status_code == status.HTTP_400_BAD_REQUEST

        user.refresh_from_db()
        assert user.check_password('OldPassword123!') is True
        assert user.check_password('NewPassword789!') is False

    def test_complete_recovery_flow(self):
        """
        Flujo completo: configurar 5 respuestas → verificar → resetear contraseña.
        Usa superusuario para bypass de RequiresFunctionPermission en set-security-answers.
        """
        import uuid
        u = uuid.uuid4().hex[:6]
        all_questions = SecurityQuestionTestData.create_batch(POOL_MIN)
        questions = all_questions[:ANSWERS_REQUIRED]

        user = User.objects.create_superuser(
            username=f'rec_{u}',
            email=f'rec_{u}@test.com',
            password='OldPassword123!',
        )

        self.client.force_authenticate(user=user)

        set_resp = self.client.post(reverse('authentication:auth-set-security-answers'), {
            'answers': [
                {'question_id': questions[i].id, 'answer': f'Respuesta{i}'}
                for i in range(ANSWERS_REQUIRED)
            ]
        }, format='json')
        assert set_resp.status_code == status.HTTP_200_OK
        assert UserSecurityAnswer.objects.filter(user=user).count() == ANSWERS_REQUIRED

        self.client.force_authenticate(user=None)

        reset_resp = self.client.post(reverse('authentication:auth-reset-password'), {
            'username': f'rec_{u}',
            'answers': [
                {'question_id': questions[i].id, 'answer': f'Respuesta{i}'}
                for i in range(ANSWERS_REQUIRED)
            ],
            'new_password': 'NewPassword789!',
            'confirm_password': 'NewPassword789!',
        }, format='json')
        assert reset_resp.status_code == status.HTTP_200_OK

        login_resp = self.client.post(reverse('authentication:login'), {
            'username': f'rec_{u}',
            'password': 'NewPassword789!',
        }, format='json')
        assert login_resp.status_code == status.HTTP_200_OK


@pytest.mark.integration
@pytest.mark.django_db
class TestSecurityAnswersNormalization:
    """
    Tests de normalización de respuestas: case-insensitive y strip de espacios.
    Usa force_authenticate para evitar dependencia de JWT Bearer.
    """

    def setup_method(self):
        self.client = APIClient()

    def _setup_user_with_answers(self, username, answers_map):
        """
        Crea usuario, pool de preguntas y respuestas hasheadas.
        Retorna (user, questions_list).
        """
        all_questions = SecurityQuestionTestData.create_batch(POOL_MIN)
        questions = all_questions[:ANSWERS_REQUIRED]
        user = User.objects.create_user(username=username, password='OldPassword123!')

        for i, q in enumerate(questions):
            UserSecurityAnswerTestData(
                user=user, question=q,
                answer_text=answers_map[i], created_by=user,
            )
        return user, questions

    def test_answers_are_case_insensitive(self):
        """'RESPUESTA0' == 'respuesta0' al verificar."""
        import uuid
        u = uuid.uuid4().hex[:6]
        _user, questions = self._setup_user_with_answers(
            f'ci_{u}',
            {i: f'RESPUESTA{i}' for i in range(ANSWERS_REQUIRED)}
        )

        resp = self.client.post(reverse('authentication:auth-verify-security-answers'), {
            'username': f'ci_{u}',
            'answers': [
                {'question_id': q.id, 'answer': f'respuesta{i}'}
                for i, q in enumerate(questions)
            ],
        }, format='json')

        assert resp.status_code == status.HTTP_200_OK

    def test_answers_strip_whitespace(self):
        """'  Respuesta0  ' == 'Respuesta0' al verificar."""
        import uuid
        u = uuid.uuid4().hex[:6]
        _user, questions = self._setup_user_with_answers(
            f'ws_{u}',
            {i: f'  Respuesta{i}  ' for i in range(ANSWERS_REQUIRED)}
        )

        resp = self.client.post(reverse('authentication:auth-verify-security-answers'), {
            'username': f'ws_{u}',
            'answers': [
                {'question_id': q.id, 'answer': f'Respuesta{i}'}
                for i, q in enumerate(questions)
            ],
        }, format='json')

        assert resp.status_code == status.HTTP_200_OK
