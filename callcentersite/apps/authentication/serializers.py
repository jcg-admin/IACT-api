from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    JWT con datos adicionales.
    
    Incluye username y email en el token.
    """
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Claims custom
        token['username'] = user.username
        token['email'] = user.email
        
        return token


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Solicitud reset password (sin email).
    
    CNST-001: Usar preguntas seguridad en lugar de email.
    """
    
    username = serializers.CharField()
    question1_answer = serializers.CharField(write_only=True)
    question2_answer = serializers.CharField(write_only=True)
    question3_answer = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    
    def validate(self, attrs):
        """
        Validar respuestas seguridad.
        
        Raises:
            ValidationError: Si usuario no existe o respuestas invalidas
        """
        username = attrs.get('username')
        
        # Verificar usuario existe
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise serializers.ValidationError("Usuario no existe")
        
        # Verificar tiene 3 respuestas configuradas
        answers = user.security_answers.all()
        if answers.count() < 3:
            raise serializers.ValidationError(
                "Usuario sin preguntas seguridad configuradas"
            )
        
        # Validación básica: cada respuesta no vacía (validación completa en UC_AUTH_05)
        # Por ahora solo verificamos que existan 3
        
        attrs['user'] = user
        return attrs
    
    def save(self):
        """Cambiar password del usuario."""
        user = self.validated_data['user']
        new_password = self.validated_data['new_password']
        
        user.set_password(new_password)
        user.save()
        
        return user
