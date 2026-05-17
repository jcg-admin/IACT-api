"""
apps/users/create_user_view.py

CreateUserView — UC_USR_01: Crear Usuario.

Fuente: uc-usr-01/flujo-principal.rst (15 pasos)
        uc-usr-01/datos-involucrados.rst § 7
        uc-usr-01/criterios-aceptacion.rst (17 CAs)

Componentes:
  UsernameGenerator — CNST-029: {first}.{last}.{NNNN}
  PasswordGenerator — temp password entropía ≥ 72 bits, sin logging
  CreateUserService — orquesta pasos 5-14 (transaction.atomic PASOS 10-13)
  CreateUserView    — POST /api/users/
"""
import re
import secrets
import string
import unicodedata

from django.db import transaction, DatabaseError
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from apps.access.permissions.function_permissions import HasFunction


# ---------------------------------------------------------------------------
# UsernameGenerator — CNST-029
# ---------------------------------------------------------------------------
class UsernameGenerator:
    """
    Genera username en formato {first}.{last}.{NNNN}.
    CNST-029: autogenerado, no editable.
    """

    @staticmethod
    def _normalize(text: str) -> str:
        """Lowercase + quitar acentos."""
        nfkd = unicodedata.normalize('NFKD', text)
        ascii_only = nfkd.encode('ascii', 'ignore').decode('ascii')
        return re.sub(r'[^a-z]', '', ascii_only.lower())

    @classmethod
    def generate(cls, first_name: str, last_name: str) -> str:
        """
        Genera username único con sufijo incremental.
        first='Ana María' last='Gómez' → 'ana.gomez.0001' (o .0002 si existe)
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()

        first = cls._normalize(first_name) or 'user'
        last  = cls._normalize(last_name)  or 'x'
        base  = f'{first}.{last}'

        # Contar usuarios con ese prefijo
        count = User.objects.filter(username__startswith=base).count()
        suffix = count + 1

        # Evitar colisiones
        for _ in range(100):
            candidate = f'{base}.{suffix:04d}'
            if not User.objects.filter(username=candidate).exists():
                return candidate
            suffix += 1

        raise RuntimeError('No se pudo generar un username único tras 100 intentos.')


# ---------------------------------------------------------------------------
# PasswordGenerator — entropía ≥ 72 bits
# ---------------------------------------------------------------------------
class PasswordGenerator:
    """
    Genera contraseña temporal criptográficamente segura.
    CNST-026: NUNCA se loggea ni aparece en response.
    """
    CHARSET = (
        string.ascii_uppercase
        + string.ascii_lowercase
        + string.digits
        + '!@#$%^&*()-_=+[]{}|'
    )
    LENGTH = 12

    @classmethod
    def generate(cls) -> str:
        """Genera contraseña con al menos 1 mayús, 1 minús, 1 dígito, 1 símbolo."""
        for _ in range(100):
            pwd = ''.join(secrets.choice(cls.CHARSET) for _ in range(cls.LENGTH))
            if (any(c.isupper() for c in pwd)
                    and any(c.islower() for c in pwd)
                    and any(c.isdigit() for c in pwd)
                    and any(c in '!@#$%^&*()-_=+[]{}|' for c in pwd)):
                return pwd
        raise RuntimeError('No se pudo generar contraseña válida.')


# ---------------------------------------------------------------------------
# Serializers
# ---------------------------------------------------------------------------
class CreateUserRequestSerializer(serializers.Serializer):
    first_name      = serializers.CharField(max_length=50)
    last_name       = serializers.CharField(max_length=50)
    email           = serializers.EmailField()
    access_group_id = serializers.IntegerField(required=False, allow_null=True)


# ---------------------------------------------------------------------------
# CreateUserView
# ---------------------------------------------------------------------------
class CreateUserThrottle(UserRateThrottle):
    rate = '60/min'
    scope = 'create_user'


@extend_schema(
    summary='UC_USR_01 — Crear usuario',
    description=(
        'Crea un nuevo usuario con contraseña temporal. **USR-001** create_users.\n\n'
        'Pasos atómicos (PASOS 10-13):\n'
        '- PASO 7: UsernameGenerator — {first}.{last}.{NNNN} (CNST-029).\n'
        '- PASO 8: PasswordGenerator — entropía ≥ 72 bits.\n'
        '- PASO 10: INSERT User (state=ACTIVE, first_login=True).\n'
        '- PASO 11: INSERT Assignment (si access_group_id).\n'
        '- PASO 12: InternalMessage con credenciales (CNST-001/002).\n'
        '- PASO 13: AuditEvent USER_CREATED (CNST-025/026).\n\n'
        '**CA-02**: body NO contiene password (CNST-026).\n'
        '**CA-04**: first_login=True → next login necesita UC_AUTH_04.\n'
        '**CA-10**: si InternalMessage falla → rollback total (CNST-002).\n'
        '**CA-11**: CNST-001 — cero llamadas a email externo.\n'
        '**CA-16**: throttle 60/min.'
    ),
    request=CreateUserRequestSerializer,
    responses={
        201: OpenApiResponse(description='Usuario creado sin contraseña en body.'),
        400: OpenApiResponse(description='Datos inválidos.'),
        403: OpenApiResponse(description='Sin USR-001.'),
        409: OpenApiResponse(description='Email duplicado.'),
        500: OpenApiResponse(description='Error de BD o InternalMessage.'),
    },
    tags=['Usuarios'],
)
class CreateUserView(APIView):
    """POST /api/users/  — USR-001 create_users."""
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'USR-001'
    throttle_classes   = [CreateUserThrottle]

    def post(self, request):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        ser = CreateUserRequestSerializer(data=request.data)
        if not ser.is_valid():
            return Response({'error': 'VALIDATION_ERROR', 'fields': ser.errors}, status=400)

        data  = ser.validated_data
        email = data['email']

        # CA-08: email único
        if User.objects.filter(email=email).exists():
            return Response({'error': 'EMAIL_EXISTS', 'message': 'El email ya está registrado.'}, status=409)

        # PASO 7: generar username
        username = UsernameGenerator.generate(data['first_name'], data['last_name'])

        # PASO 8: generar password (NO se loggea)
        temp_password = PasswordGenerator.generate()

        # PASOS 10-13: atomic
        try:
            result = self._atomic_create(
                request=request,
                data=data,
                username=username,
                temp_password=temp_password,
                User=User,
            )
        except DatabaseError:
            return Response({'error': 'DB_TIMEOUT', 'message': 'Error de BD. Reintente.'}, status=500)
        except Exception as exc:
            return Response({'error': 'INTERNAL_ERROR', 'message': str(exc)}, status=500)

        return Response(result, status=201)

    @staticmethod
    @transaction.atomic
    def _atomic_create(request, data, username, temp_password, User):
        """PASOS 10-13 atómicos — si InternalMessage falla → rollback (CNST-002)."""
        from apps.access.models import AccessGroup, UserAccessGroup
        from apps.audit.services import AuditLogService

        # PASO 10: INSERT User
        user = User.objects.create_user(
            username=username,
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            password=temp_password,
            state='ACTIVE',
            first_login=True,
            password_changed_at=timezone.now(),
            created_by_admin=request.user,
        )

        # PASO 11: Assignment opcional
        agr_id      = data.get('access_group_id')
        has_initial = False
        if agr_id:
            try:
                agr = AccessGroup.objects.get(pk=agr_id, is_active=True)
                UserAccessGroup.objects.create(
                    user=user,
                    access_group=agr,
                    granted_by=request.user,
                )
                has_initial = True
            except AccessGroup.DoesNotExist:
                pass  # sin AGR, no es error fatal

        # PASO 12: InternalMessage (CNST-001/002 — OBLIGATORIO)
        # Si falla → rollback del User (CA-10)
        notification_sent = CreateUserView._send_credentials(
            new_user=user,
            username=username,
            temp_password=temp_password,
        )

        # PASO 13: AuditEvent (CNST-025/026 — sin contraseña en payload)
        AuditLogService.emit(
            event_type='USER_CREATED',
            actor_user_id=request.user.pk,
            payload={
                'target_user_id': user.pk,
                'access_group_id': agr_id,
                'has_initial_agr': has_initial,
                'username_generated': username,
            },
        )

        return {
            'user_id':           user.pk,
            'username':          username,
            'email':             data['email'],
            'state':             'ACTIVE',
            'first_login':       True,
            'created_at':        user.date_joined.isoformat(),
            'access_group_id':   agr_id if has_initial else None,
            'notification_sent': notification_sent,
        }

    @staticmethod
    def _send_credentials(new_user, username: str, temp_password: str) -> bool:
        """
        PASO 12: InternalMessage con credenciales al nuevo usuario.
        CNST-001: cero email externo — solo InternalMailbox.
        CNST-002: buzón obligatorio — si falla → excepción → rollback.
        """
        from apps.alerts.models import InternalMailbox, MailboxMessage
        mailbox = InternalMailbox.objects.filter(owner=new_user).first()
        if not mailbox:
            mailbox = InternalMailbox.objects.create(owner=new_user)

        MailboxMessage.objects.create(
            mailbox=mailbox,
            subject='Bienvenido a IACT — Credenciales de acceso',
            body=(
                f'Tu cuenta IACT ha sido creada.\n\n'
                f'Usuario:             {username}\n'
                f'Contraseña temporal: {temp_password}\n\n'
                f'Debes cambiar tu contraseña en el primer inicio de sesión.'
            ),
        )
        return True
