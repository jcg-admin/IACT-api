"""
ViewSets para authentication.

CLEAN_CODE v3.0.1: Nombres descriptivos.
SOLID SRP: Cada viewset una responsabilidad.
"""

from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from apps.core.permissions import RequiresFunctionPermission  # [SUCCESS] De apps.core
from apps.core.mixins import AuditMixin  # [SUCCESS] De apps.core
from apps.authentication.models import SessionLog
from apps.authentication.serializers.auth import LoginSerializer
from apps.authentication.serializers import (
    LoginSerializer,
    LogoutSerializer,
    ChangePasswordSerializer,
    SecurityQuestionSerializer,
    SetSecurityAnswersSerializer,
    VerifySecurityAnswersSerializer,
    ResetPasswordSerializer,
    SessionLogSerializer,
    SessionLogDetailSerializer,
)
from apps.authentication.services import (
    AuthenticationService,
    LockoutService,
    RecoveryService,
    SessionService,
)
from apps.authentication.exceptions import (
    InvalidCredentialsError,
    AccountLockedError,
    UserInactiveError,
)


class AuthViewSet(viewsets.ViewSet):
    serializer_class = LoginSerializer
    """
    ViewSet para autenticación.
    
    SOLID SRP: Solo endpoints de autenticación.
    
    Endpoints:
    - POST /auth/login/ (AllowAny)
    - POST /auth/logout/ (IsAuthenticated)
    - POST /auth/change-password/ (IsAuthenticated + Permission)
    - GET /auth/security-questions/ (AllowAny)
    - POST /auth/set-security-answers/ (IsAuthenticated + Permission)
    - POST /auth/verify-security-answers/ (AllowAny)
    - POST /auth/reset-password/ (AllowAny)
    """
    
    # [SUCCESS] function_map con permission_django (NOT code)
    function_map = {
        'change_password': 'authentication.change_password',  # [SUCCESS] permission_django
        'set_security_answers': 'authentication.set_security_answers',  # [SUCCESS]
    }
    
    def __init__(self, *args, **kwargs):
        """Initialize viewset with services."""
        super().__init__(*args, **kwargs)
        # [SUCCESS] Services inyectados
        self.auth_service = AuthenticationService()
        self.lockout_service = LockoutService()
        self.recovery_service = RecoveryService()
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """
        Login de usuario.
        
        POST /auth/login/
        
        Body:
        - username: str
        - password: str
        
        Returns:
        - user: User data
        - token: DRF token
        - session_key: Django session
        - first_login: bool
        """
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            result = self.auth_service.login_user(
                request=request,
                username=serializer.validated_data['username'],
                password=serializer.validated_data['password']
            )
            
            return Response({
                'success': True,
                'message': 'Login exitoso',
                'data': {
                    'user': {
                        'id': result['user'].id,
                        'username': result['user'].username,
                        'email': result['user'].email,
                        'first_name': result['user'].first_name,
                        'last_name': result['user'].last_name,
                    },
                    'token': result['token'],
                    'session_key': result['session_key'],
                    'first_login': result['first_login']
                }
            }, status=status.HTTP_200_OK)
        
        except (InvalidCredentialsError, AccountLockedError, UserInactiveError) as e:
            return Response({
                'success': False,
                'error': e.to_dict()
            }, status=e.status_code)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """
        Logout de usuario.
        
        POST /auth/logout/
        
        Requiere autenticación.
        """
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        success = self.auth_service.logout_user(request)
        
        if success:
            return Response({
                'success': True,
                'message': 'Logout exitoso'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': 'No hay sesión activa'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        operation_id='auth_viewset_change_password_legacy',
        deprecated=True,
        summary='[LEGACY] Cambio contraseña via ViewSet — usar POST /api/auth/change-password/',
        description='Delegado a ChangePasswordView canónica. Fix DT-SPECTACULAR-003.',
        tags=['Autenticación'],
    )
    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated, RequiresFunctionPermission]  # [SUCCESS]
    )
    def change_password(self, request):
        """
        Cambio de contraseña.
        
        POST /auth/change-password/
        
        Requiere autenticación + permiso.
        
        Body:
        - current_password: str
        - new_password: str
        - confirm_password: str
        """
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        
        # Verificar contraseña actual
        if not user.check_password(serializer.validated_data['current_password']):
            return Response({
                'success': False,
                'error': {
                    'current_password': 'Contraseña actual incorrecta'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Cambiar contraseña
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({
            'success': True,
            'message': 'Contraseña cambiada exitosamente'
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def security_questions(self, request):
        """
        Lista preguntas de seguridad disponibles.
        
        GET /auth/security-questions/
        
        Público.
        """
        questions = self.recovery_service.get_available_questions()
        serializer = SecurityQuestionSerializer(questions, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated, RequiresFunctionPermission]  # [SUCCESS]
    )
    def set_security_answers(self, request):
        """
        Configura respuestas de seguridad.
        
        POST /auth/set-security-answers/
        
        Requiere autenticación + permiso.
        
        Body:
        - answers: [
            {question_id: int, answer: str},
            ...
          ]
        """
        serializer = SetSecurityAnswersSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        success = self.recovery_service.set_security_answers(
            user=request.user,
            answers_data=serializer.validated_data['answers']
        )
        
        if success:
            return Response({
                'success': True,
                'message': 'Respuestas de seguridad configuradas exitosamente'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': 'Error al configurar respuestas'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def verify_security_answers(self, request):
        """
        Verifica respuestas de seguridad.
        
        POST /auth/verify-security-answers/
        
        Público.
        
        Body:
        - username: str
        - answers: [
            {question_id: int, answer: str},
            ...
          ]
        """
        serializer = VerifySecurityAnswersSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            success = self.recovery_service.verify_security_answers(
                username=serializer.validated_data['username'],
                answers_data=serializer.validated_data['answers']
            )
            
            return Response({
                'success': True,
                'message': 'Respuestas correctas',
                'verified': success
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def reset_password(self, request):
        """
        Reset de contraseña mediante preguntas.
        
        POST /auth/reset-password/
        
        Público. CNST-001: SIN email.
        
        Body:
        - username: str
        - answers: [...]
        - new_password: str
        - confirm_password: str
        """
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            success = self.recovery_service.reset_password_by_questions(
                username=serializer.validated_data['username'],
                answers_data=serializer.validated_data['answers'],
                new_password=serializer.validated_data['new_password']
            )
            
            return Response({
                'success': True,
                'message': 'Contraseña reseteada exitosamente'
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class SessionViewSet(AuditMixin, viewsets.ReadOnlyModelViewSet):  # [SUCCESS] AuditMixin
    """
    ViewSet para gestión de sesiones.
    
    SOLID SRP: Solo endpoints de sesiones.
    
    Endpoints:
    - GET /sessions/ (list)
    - GET /sessions/{id}/ (retrieve)
    - POST /sessions/{id}/invalidate/
    - POST /sessions/invalidate-all/
    """
    
    queryset = SessionLog.objects.all()
    serializer_class = SessionLogSerializer
    permission_classes = [IsAuthenticated, RequiresFunctionPermission]  # [SUCCESS]
    
    # [SUCCESS] function_map con permission_django
    function_map = {
        'list': 'authentication.view_sessions',  # [SUCCESS] permission_django
        'retrieve': 'authentication.view_sessions',  # [SUCCESS]
        'invalidate': 'authentication.invalidate_session',  # [SUCCESS]
        'invalidate_all': 'authentication.invalidate_all_sessions',  # [SUCCESS]
    }
    
    def __init__(self, *args, **kwargs):
        """Initialize viewset with service."""
        super().__init__(*args, **kwargs)
        # [SUCCESS] Service inyectado
        self.session_service = SessionService()
    
    def get_queryset(self):
        """
        Filtra sesiones del usuario actual.
        
        SOLID SRP: Solo filtra por usuario.
        """
        # [SUCCESS] Usar active() para excluir soft deleted
        return SessionLog.objects.active().filter(
            user=self.request.user
        ).order_by('-created_at')  # [SUCCESS] login_at = created_at
    
    def get_serializer_class(self):
        """
        Serializer según acción.
        
        SOLID SRP: Solo selecciona serializer.
        """
        if self.action == 'retrieve':
            return SessionLogDetailSerializer
        return SessionLogSerializer
    
    @action(detail=True, methods=['post'])
    def invalidate(self, request, pk=None):
        """
        Invalida sesión específica.
        
        POST /sessions/{id}/invalidate/
        """
        session_log = self.get_object()
        
        success = self.session_service.invalidate_session(
            session_key=session_log.session_key,
            user=request.user
        )
        
        if success:
            return Response({
                'success': True,
                'message': 'Sesión invalidada exitosamente'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': 'Error al invalidar sesión'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def invalidate_all(self, request):
        """
        Invalida todas las sesiones del usuario.
        
        POST /sessions/invalidate-all/
        
        Logout de todos los dispositivos.
        """
        # Obtener sesión actual
        current_session_key = request.session.session_key
        
        count = self.session_service.invalidate_all_user_sessions(
            user=request.user,
            except_current=current_session_key
        )
        
        return Response({
            'success': True,
            'message': f'{count} sesiones invalidadas exitosamente',
            'invalidated_count': count
        }, status=status.HTTP_200_OK)
