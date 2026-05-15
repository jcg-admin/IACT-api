"""
apps/authentication/reset_password_view.py

ResetPasswordView — UC_AUTH_03: Recuperar Contraseña (admin → contraseña temporal).

Fuente: uc-auth-03/criterios-aceptacion.rst § 9

Endpoint: POST /api/users/{user_id}/reset-password/
Requiere: AUTH-003 reset_password (AGR-010 system_admin_group)
"""
import secrets, string, unicodedata, re
from django.db import transaction, DatabaseError
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access.permissions.function_permissions import HasFunction
from apps.authentication.serializers.recovery import ResetPasswordSerializer



def _gen_temp_password() -> str:
    """Misma estrategia que PasswordGenerator (UC_USR_01)."""
    charset = string.ascii_uppercase + string.ascii_lowercase + string.digits + '!@#$%^&*()'
    for _ in range(100):
        pwd = ''.join(secrets.choice(charset) for _ in range(12))
        if (any(c.isupper() for c in pwd) and any(c.islower() for c in pwd)
                and any(c.isdigit() for c in pwd)):
            return pwd
    return secrets.token_urlsafe(12)


@extend_schema(
    summary='UC_AUTH_03 — Resetear contraseña de usuario (admin)',
    description=(
        'Admin resetea la contraseña de un usuario. **AUTH-003** reset_password.\n\n'
        '**CA-01**: nueva contraseña temporal, first_login=True, InternalMessage.\n'
        '**CA-02**: body NO contiene contraseña.\n'
        '**CA-04**: Sessions cerradas con close_reason=PASSWORD_RESET.\n'
        '**CA-05**: next login requiere UC_AUTH_04.\n'
        '**CA-06**: auto-reset → 400 SELF_RESET_FORBIDDEN.\n'
        '**CNST-001**: cero email externo — solo InternalMailbox.'
    ),
    responses={
        200: OpenApiResponse(description='Contraseña reseteada sin exponer el valor.'),
        400: OpenApiResponse(description='SELF_RESET_FORBIDDEN.'),
        404: OpenApiResponse(description='Usuario no encontrado.'),
    },
    tags=['Autenticacion'],
)
class ResetPasswordView(APIView):
    serializer_class = ResetPasswordSerializer
    """POST /api/users/{user_id}/reset-password/ — AUTH-003."""
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'AUTH-003'

    def post(self, request, user_id):
        from django.contrib.auth import get_user_model
        from apps.audit.services import AuditLogService
        from apps.authentication.models import Session
        User = get_user_model()

        # CA-06: auto-reset prohibido
        if user_id == request.user.pk:
            AuditLogService.emit(
                event_type='USER_MODIFY_FAILED',
                actor_user_id=request.user.pk,
                payload={'reason': 'self_reset_attempt', 'target_user_id': user_id},
            )
            return Response({'error': 'SELF_RESET_FORBIDDEN'}, status=400)

        try:
            target = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'error': 'USER_NOT_FOUND'}, status=404)

        # CA-07: User ELIMINATED rechaza
        if target.state == 'ELIMINATED':
            return Response({'error': 'INVALID_USER_STATE', 'state': target.state}, status=400)

        temp_password = _gen_temp_password()

        try:
            with transaction.atomic():
                # CA-04: cerrar Sessions
                sessions = list(Session.objects.filter(user=target, state='ACTIVE'))
                for s in sessions:
                    s.close(reason='PASSWORD_RESET')

                # Cambiar contraseña + first_login=True (CA-05)
                target.set_password(temp_password)
                target.first_login        = True
                target.password_changed_at = timezone.now()
                target.save(update_fields=['password', 'first_login', 'password_changed_at'])

                # InternalMessage con contraseña (CNST-001/002)
                self._notify(target, temp_password)

                AuditLogService.emit(
                    event_type='USER_PASSWORD_RESET',
                    actor_user_id=request.user.pk,
                    payload={
                        'target_user_id':     user_id,
                        'sessions_closed':    len(sessions),
                        'first_login_set':    True,
                    },
                )
        except DatabaseError:
            return Response({'error': 'DB_TIMEOUT'}, status=500)

        return Response({
            'message':         'Contraseña reseteada.',
            'user_id':         user_id,
            'first_login':     True,
            'sessions_closed': len(sessions),
            'notification_sent': True,
            # CA-02: temp_password NO aparece aquí
        })

    @staticmethod
    def _notify(user, temp_password: str) -> None:
        from apps.alerts.models import InternalMailbox, MailboxMessage
        mailbox, _ = InternalMailbox.objects.get_or_create(owner=user)
        MailboxMessage.objects.create(
            mailbox=mailbox,
            subject='Tu contraseña fue reseteada',
            body=(
                f'Un administrador ha reseteado tu contraseña.\n\n'
                f'Contraseña temporal: {temp_password}\n\n'
                f'Debes cambiarla en tu próximo inicio de sesión.'
            ),
        )
