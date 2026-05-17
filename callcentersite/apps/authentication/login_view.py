"""
apps/authentication/login_view.py

LoginView — POST /api/auth/login/ — UC_AUTH_01.

Fuente: uc-auth-01/implementacion-tecnica.rst § 11
        uc-auth-01/datos-involucrados.rst § 7.2 y § 7.3

Responsabilidades de esta view:
  1. Validar el payload de entrada (LoginRequestSerializer).
  2. Delegar al LoginService.login().
  3. Serializar la salida (LoginResponseSerializer).
  4. Mapear excepciones de dominio → respuestas HTTP con
     estructura unificada (CNST-013).

La lógica de negocio vive exclusivamente en LoginService.
"""
import uuid

from django.utils import timezone
from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
)
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from apps.authentication.services.login_service import (
    LoginOutput,
    LoginService,
    InvalidCredentialsError,
    AccountBlockedError,
    AccountInactiveError,
    DBTransientError,
)


# ---------------------------------------------------------------------------
# Serializers de entrada / salida (documentados con drf-spectacular)
# ---------------------------------------------------------------------------

class LoginRequestSerializer(serializers.Serializer):
    """Payload de la petición POST /api/auth/login/."""

    username = serializers.CharField(
        min_length=3,
        max_length=150,
        help_text='Nombre de usuario (3-150 caracteres).',
    )
    password = serializers.CharField(
        min_length=8,
        max_length=128,
        write_only=True,
        style={'input_type': 'password'},
        help_text='Contraseña (8-128 caracteres). Nunca se almacena en claro.',
    )
    client_info = serializers.DictField(
        required=False,
        default=dict,
        help_text='Información opcional del dispositivo cliente (device, platform).',
    )


class TokenPairSerializer(serializers.Serializer):
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    access_expires_at = serializers.CharField(read_only=True)
    refresh_expires_at = serializers.CharField(read_only=True)


class UserInfoSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    primary_access_group_id = serializers.CharField(
        allow_null=True, read_only=True,
    )
    access_groups = serializers.ListField(
        child=serializers.CharField(), read_only=True,
    )
    first_login = serializers.BooleanField(read_only=True)


class SessionInfoSerializer(serializers.Serializer):
    session_id = serializers.CharField(read_only=True)
    started_at = serializers.CharField(read_only=True)
    expires_at = serializers.CharField(read_only=True)


class LoginWarningSerializer(serializers.Serializer):
    type = serializers.CharField(read_only=True)
    message = serializers.CharField(read_only=True)
    days_remaining = serializers.IntegerField(
        allow_null=True, read_only=True,
    )


class LoginResponseSerializer(serializers.Serializer):
    """Respuesta exitosa 200 de POST /api/auth/login/."""

    tokens = TokenPairSerializer(read_only=True)
    user = UserInfoSerializer(read_only=True)
    session = SessionInfoSerializer(read_only=True)
    next_step = serializers.CharField(allow_null=True, read_only=True)
    warning = LoginWarningSerializer(allow_null=True, read_only=True)
    request_id = serializers.CharField(read_only=True)
    timestamp = serializers.CharField(read_only=True)


class LoginErrorSerializer(serializers.Serializer):
    """Respuesta de error unificada (CNST-013)."""

    class _ErrorDetailSerializer(serializers.Serializer):
        code = serializers.CharField()
        message = serializers.CharField()
        fields = serializers.DictField(required=False)
        retry_after = serializers.IntegerField(required=False)

    error = _ErrorDetailSerializer()
    request_id = serializers.CharField()
    timestamp = serializers.CharField()


# ---------------------------------------------------------------------------
# Throttle personalizado — CNST-011: 10 req/min por IP
# ---------------------------------------------------------------------------

class AnonLoginThrottle(AnonRateThrottle):
    rate = '10/min'
    scope = 'login'


# ---------------------------------------------------------------------------
# LoginView
# ---------------------------------------------------------------------------

_LOGIN_200 = OpenApiResponse(
    description='Login exitoso.',
    response=LoginResponseSerializer,
)
_LOGIN_400 = OpenApiResponse(
    description='Datos inválidos (EX-06: VALIDATION_ERROR).',
    response=LoginErrorSerializer,
)
_LOGIN_401 = OpenApiResponse(
    description='Credenciales incorrectas (EX-01/EX-02: INVALID_CREDENTIALS).',
    response=LoginErrorSerializer,
)
_LOGIN_403 = OpenApiResponse(
    description=(
        'Cuenta bloqueada (EX-03: ACCOUNT_BLOCKED) '
        'o inactiva (EX-04: ACCOUNT_INACTIVE).'
    ),
    response=LoginErrorSerializer,
)
_LOGIN_429 = OpenApiResponse(
    description='Rate limit excedido (EX-05: RATE_LIMITED).',
    response=LoginErrorSerializer,
)
_LOGIN_503 = OpenApiResponse(
    description='Error transitorio de BD (EX-07: DB_TRANSIENT_ERROR).',
    response=LoginErrorSerializer,
)


@extend_schema(
    summary='UC_AUTH_01 — Iniciar Sesión',
    description=(
        'Autentica al usuario con username y contraseña. '
        'Genera tokens JWT (SimpleJWT), crea una Session ACTIVE y emite '
        'un AuditEvent LOGIN inmutable (CNST-025).\n\n'
        '**BR-005 / CNST-004**: Si el usuario ya tiene una sesión activa, '
        'es cerrada con close_reason=SUPERSEDED antes de crear la nueva.\n\n'
        '**BR-015**: Después de 5 intentos fallidos la cuenta pasa a '
        'state=BLOCKED.\n\n'
        '**FA-01**: Si first_login=True, next_step="change_password" y la '
        'sesión tiene scope="restricted".\n\n'
        '**FA-02**: Si password_expires_at < now + 7 días, se incluye '
        'warning.type="password_expiring".\n\n'
        '**FA-04**: Si el usuario no tiene Assignments activos, se incluye '
        'warning.type="no_permissions".\n\n'
        '**CNST-011**: Límite de 10 peticiones/minuto por IP.'
    ),
    request=LoginRequestSerializer,
    responses={
        200: _LOGIN_200,
        400: _LOGIN_400,
        401: _LOGIN_401,
        403: _LOGIN_403,
        429: _LOGIN_429,
        503: _LOGIN_503,
    },
    tags=['Autenticacion'],
)
class LoginView(APIView):
    """
    POST /api/auth/login/

    Endpoint público de inicio de sesión.
    No requiere autenticación previa (permission_classes=[]).
    CNST-010: permission_classes explícito — no AllowAny implícito.
    """

    permission_classes = []
    throttle_classes = [AnonLoginThrottle]
    serializer_class = LoginRequestSerializer  # para drf-spectacular

    def post(self, request):
        # 1. Validar payload
        serializer = LoginRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return self._error_response(
                code='VALIDATION_ERROR',
                message='Los datos enviados no son válidos.',
                http_status=400,
                fields=serializer.errors,
            )

        data = serializer.validated_data
        ip = self._get_client_ip(request)

        # 2. Delegar al LoginService
        try:
            output: LoginOutput = LoginService.login(
                username=data['username'],
                password=data['password'],
                client_info=data.get('client_info', {}),
                ip_address=ip,
            )
        except InvalidCredentialsError as exc:
            return self._error_response(
                code=exc.code,
                message=str(exc),
                http_status=exc.http_status,
            )
        except AccountBlockedError as exc:
            return self._error_response(
                code=exc.code,
                message=str(exc),
                http_status=exc.http_status,
            )
        except AccountInactiveError as exc:
            return self._error_response(
                code=exc.code,
                message=str(exc),
                http_status=exc.http_status,
            )
        except DBTransientError as exc:
            return self._error_response(
                code=exc.code,
                message=str(exc),
                http_status=exc.http_status,
                retry_after=30,
            )

        # 3. Serializar respuesta exitosa
        now_iso = timezone.now().isoformat()
        response_data = {
            'tokens': {
                'access': output.tokens.access,
                'refresh': output.tokens.refresh,
                'access_expires_at': output.tokens.access_expires_at,
                'refresh_expires_at': output.tokens.refresh_expires_at,
            },
            'user': {
                'user_id': output.user.user_id,
                'username': output.user.username,
                'full_name': output.user.full_name,
                'primary_access_group_id': output.user.primary_access_group_id,
                'access_groups': output.user.access_groups,
                'first_login': output.user.first_login,
            },
            'session': {
                'session_id': output.session.session_id,
                'started_at': output.session.started_at,
                'expires_at': output.session.expires_at,
            },
            'next_step': output.next_step,
            'warning': (
                {
                    'type': output.warning.type,
                    'message': output.warning.message,
                    'days_remaining': output.warning.days_remaining,
                }
                if output.warning else None
            ),
            'request_id': output.request_id,
            'timestamp': now_iso,
        }
        return Response(response_data, status=status.HTTP_200_OK)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _error_response(
        code: str,
        message: str,
        http_status: int,
        fields: dict | None = None,
        retry_after: int | None = None,
    ) -> Response:
        """
        Construye la respuesta de error unificada (CNST-013 § 7.3).
        """
        error_body: dict = {'code': code, 'message': message}
        if fields:
            error_body['fields'] = fields
        if retry_after is not None:
            error_body['retry_after'] = retry_after

        return Response(
            {
                'error': error_body,
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat(),
            },
            status=http_status,
        )

    @staticmethod
    def _get_client_ip(request) -> str | None:
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
