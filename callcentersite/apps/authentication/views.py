from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.authentication.serializers import (
    CustomTokenObtainPairSerializer,
    PasswordResetRequestSerializer,
)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Login JWT custom.
    
    POST /api/v1/auth/login/
    {
        "username": "user",
        "password": "pass"
    }
    
    Returns:
        {
            "access": "...",
            "refresh": "...",
            "username": "user",
            "email": "user@example.com"
        }
    """
    serializer_class = CustomTokenObtainPairSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    """
    Reset password sin email.
    
    POST /api/v1/auth/password-reset/
    {
        "username": "user",
        "question1_answer": "azul",
        "question2_answer": "cdmx",
        "question3_answer": "perro",
        "new_password": "newpass123"
    }
    
    CNST-001: NO usar email.
    """
    serializer = PasswordResetRequestSerializer(data=request.data)
    
    if serializer.is_valid():
        serializer.save()
        return Response(
            {'message': 'Password actualizado exitosamente'},
            status=status.HTTP_200_OK
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
