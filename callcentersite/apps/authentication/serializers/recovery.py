"""
Serializers para recuperación de contraseña.

CLEAN_CODE v3.0.1: Nombres auto-documentados.
SOLID SRP: Cada serializer una responsabilidad.

CNST-001: Password reset SIN email, solo preguntas.
"""

from rest_framework import serializers

from apps.authentication.models import SecurityQuestion
from apps.authentication.constants import (
    SECURITY_QUESTIONS_REQUIRED,
    PASSWORD_MIN_LENGTH,
    PASSWORD_MAX_LENGTH
)


class SecurityQuestionSerializer(serializers.ModelSerializer):
    """
    Serializer para SecurityQuestion.

    SOLID SRP: Solo representación de pregunta.

    Read-only para listar preguntas disponibles.
    """

    class Meta:
        model = SecurityQuestion
        fields = ['id', 'question', 'order']
        read_only_fields = ['id', 'question', 'order']


class SecurityAnswerInputSerializer(serializers.Serializer):
    """
    Serializer para input de respuesta de seguridad.

    SOLID SRP: Solo validación de answer input.

    Fields:
    - question_id: ID de la pregunta
    - answer: Respuesta del usuario
    """

    question_id = serializers.IntegerField(
        required=True,
        help_text='ID de la pregunta de seguridad'
    )

    answer = serializers.CharField(
        required=True,
        max_length=255,
        help_text='Respuesta a la pregunta'
    )

    def validate_answer(self, value):
        """
        Valida que la respuesta no esté vacía.

        SOLID SRP: Solo validación de answer.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("La respuesta no puede estar vacía")

        return value.strip()


class SetSecurityAnswersSerializer(serializers.Serializer):
    """
    Serializer para configurar respuestas de seguridad.

    SOLID SRP: Solo validación de configuración de respuestas.

    CNST-001: Usuario debe responder exactamente 5 preguntas.

    Fields:
    - answers: Lista de respuestas
    """

    answers = serializers.ListField(
        child=SecurityAnswerInputSerializer(),
        min_length=SECURITY_QUESTIONS_REQUIRED,
        max_length=SECURITY_QUESTIONS_REQUIRED,
        help_text=f'Lista de {SECURITY_QUESTIONS_REQUIRED} respuestas'
    )

    def validate_answers(self, value):
        """
        Valida que sean exactamente 5 preguntas únicas.

        SOLID SRP: Solo validación de answers.
        """
        # Validar cantidad
        if len(value) != SECURITY_QUESTIONS_REQUIRED:
            raise serializers.ValidationError(
                f"Debe proporcionar exactamente {SECURITY_QUESTIONS_REQUIRED} respuestas"
            )

        # Validar que no haya IDs duplicados
        question_ids = [answer['question_id'] for answer in value]

        if len(question_ids) != len(set(question_ids)):
            raise serializers.ValidationError(
                "No puede responder la misma pregunta múltiples veces"
            )

        # Validar que las preguntas existan y estén activas
        # [SUCCESS] Usar active() de ActiveRecordQuery
        existing_questions = SecurityQuestion.objects.active().filter(
            id__in=question_ids,
            is_active=True
        )

        if existing_questions.count() != len(question_ids):
            raise serializers.ValidationError(
                "Una o más preguntas no son válidas"
            )

        return value


class VerifySecurityAnswersSerializer(serializers.Serializer):
    """
    Serializer para verificar respuestas de seguridad.

    SOLID SRP: Solo validación de verificación.

    Fields:
    - username: Username del usuario
    - answers: Lista de respuestas
    """

    username = serializers.CharField(
        required=True,
        max_length=150,
        help_text='Username del usuario'
    )

    answers = serializers.ListField(
        child=SecurityAnswerInputSerializer(),
        min_length=SECURITY_QUESTIONS_REQUIRED,
        max_length=SECURITY_QUESTIONS_REQUIRED,
        help_text=f'Lista de {SECURITY_QUESTIONS_REQUIRED} respuestas'
    )


class ResetPasswordSerializer(serializers.Serializer):
    """
    Serializer para reset de contraseña mediante preguntas.

    SOLID SRP: Solo validación de password reset.

    CNST-001: Reset SIN email, solo preguntas.

    Fields:
    - username: Username
    - answers: Respuestas de seguridad
    - new_password: Nueva contraseña
    - confirm_password: Confirmación
    """

    username = serializers.CharField(
        required=True,
        max_length=150,
        help_text='Username del usuario'
    )

    answers = serializers.ListField(
        child=SecurityAnswerInputSerializer(),
        min_length=SECURITY_QUESTIONS_REQUIRED,
        max_length=SECURITY_QUESTIONS_REQUIRED,
        help_text=f'Lista de {SECURITY_QUESTIONS_REQUIRED} respuestas'
    )

    new_password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=PASSWORD_MIN_LENGTH,
        max_length=PASSWORD_MAX_LENGTH,
        style={'input_type': 'password'},
        help_text='Nueva contraseña'
    )

    confirm_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text='Confirmar nueva contraseña'
    )

    def validate(self, attrs):
        """
        Valida que las contraseñas coincidan.

        SOLID SRP: Solo validación de coincidencia.
        """
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')

        if new_password != confirm_password:
            raise serializers.ValidationError({
                'confirm_password': 'Las contraseñas no coinciden'
            })

        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Solicitud reset password vía preguntas de seguridad (sin email).

    CNST-001: Reset SIN email, solo preguntas.
    """

    username = serializers.CharField()
    question1_answer = serializers.CharField(write_only=True)
    question2_answer = serializers.CharField(write_only=True)
    question3_answer = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        username = attrs.get('username')
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise serializers.ValidationError("Usuario no existe")
        answers = user.security_answers.all()
        if answers.count() < 3:
            raise serializers.ValidationError(
                "Usuario sin preguntas de seguridad configuradas"
            )
        attrs['user'] = user
        return attrs

    def save(self):
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
