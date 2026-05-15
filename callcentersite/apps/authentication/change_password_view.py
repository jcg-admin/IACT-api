"""
apps/authentication/change_password_view.py

ChangePasswordView — POST /api/auth/change-password/ — UC_AUTH_04.

Fuente: uc-auth-04/implementacion-tecnica.rst § 11
        uc-auth-04/datos-involucrados.rst § 7.2, § 7.3
        uc-auth-04/flujo-principal.rst § 3.1 (14 pasos)

Flujo (transacción atómica en pasos 10-13):
  PASO 7  Validar password actual
  PASO 8  Validar política de complejidad (min 12, mayús, minús, dígito, símbolo)
  PASO 9  Validar no-reuso (últimos 5 hashes en PasswordHistory)
  PASO 10 Hashear + UPDATE User (password, first_login=False, password_changed_at)
  PASO 11 INSERT PasswordHistory + purge >5
  PASO 12 Cerrar otras Sessions (close_reason='PASSWORD_CHANGED')
  PASO 13 AuditEvent PASSWORD_CHANGED
  PASO 14 Response 200

FA-01: si venía de first_login, Session actual pasa a scope='full' (scope_upgraded=True).
"""
import re
import uuid

from django.db import transaction, DatabaseError
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView


# ---------------------------------------------------------------------------
# Throttle — CA protección de brute-force (EX-08)
# ---------------------------------------------------------------------------
class ChangePasswordThrottle(UserRateThrottle):
    rate = '10/hour'
    scope = 'change_password'


# ---------------------------------------------------------------------------
# Serializer de entrada
# ---------------------------------------------------------------------------
class ChangePasswordRequestSerializer(serializers.Serializer):
    """Payload de POST /api/auth/change-password/."""

    current_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='Contraseña actual del usuario.',
    )
    new_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='Nueva contraseña (política: mínimo 12 chars, mayúscula, minúscula, dígito, símbolo).',
    )
    new_password_confirmation = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='Confirmación de la nueva contraseña.',
    )

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirmation']:
            raise serializers.ValidationError({
                'new_password_confirmation': 'La confirmación no coincide.',
            })
        return attrs


# ---------------------------------------------------------------------------
# PasswordPolicyValidator — PASO 8
# ---------------------------------------------------------------------------
class PasswordPolicyValidator:
    """
    Valida la política de complejidad de contraseñas.
    Fuente: uc-auth-04/implementacion-tecnica.rst § 11.5
    """
    MIN_LENGTH = 12

    def validate(self, password: str, user) -> list[str]:
        violations = []
        if len(password) < self.MIN_LENGTH:
            violations.append('min_length')
        if not re.search(r'[A-Z]', password):
            violations.append('missing_uppercase')
        if not re.search(r'[a-z]', password):
            violations.append('missing_lowercase')
        if not re.search(r'[0-9]', password):
            violations.append('missing_digit')
        if not re.search(r'[!@#$%^&*()\-_=+\[\]{}|;:,.<>?]', password):
            violations.append('missing_symbol')
        if user.username and user.username.lower() in password.lower():
            violations.append('contains_username')
        return violations


# ---------------------------------------------------------------------------
# ChangePasswordView
# ---------------------------------------------------------------------------
_200 = OpenApiResponse(description='Contraseña actualizada exitosamente.')
_400 = OpenApiResponse(description=(
    'WRONG_CURRENT_PASSWORD | WEAK_PASSWORD (con violations) | '
    'SAME_AS_CURRENT | PASSWORD_REUSED | MISMATCH'
))
_401 = OpenApiResponse(description='JWT inválido o expirado.')
_429 = OpenApiResponse(description='Demasiados intentos (EX-08).')
_503 = OpenApiResponse(description='Error transitorio de BD (EX-09).')


@extend_schema(
    summary='UC_AUTH_04 — Cambiar Contraseña',
    description=(
        'Cambia la contraseña del usuario autenticado.\n\n'
        'Ejecuta los 14 pasos del flujo de forma atómica (PASOS 10-13):\n\n'
        '- **PASO 7**: verifica contraseña actual.\n'
        '- **PASO 8**: valida política (≥12 chars, mayús, minús, dígito, símbolo).\n'
        '- **PASO 9**: verifica que la nueva no esté en los últimos 5 hashes.\n'
        '- **PASO 10**: hashea + UPDATE User (first_login=False).\n'
        '- **PASO 11**: INSERT PasswordHistory + purge >5.\n'
        '- **PASO 12**: cierra otras Sessions (close_reason=PASSWORD_CHANGED).\n'
        '- **PASO 13**: AuditEvent PASSWORD_CHANGED (CNST-025, CNST-026).\n\n'
        '**FA-01**: si la sesión tenía scope=restricted (first_login), '
        'pasa a scope=full tras el cambio exitoso (scope_upgraded=true).\n\n'
        'CNST-026: el body de respuesta nunca contiene la nueva contraseña.'
    ),
    request=ChangePasswordRequestSerializer,
    responses={200: _200, 400: _400, 401: _401, 429: _429, 503: _503},
    tags=['Autenticacion'],
)
class ChangePasswordView(APIView):
    """
    POST /api/auth/change-password/

    Requiere autenticación JWT (IsAuthenticated).
    CNST-010: permission_classes explícito — sin restricción RBAC adicional.
    El usuario siempre puede cambiar su propia contraseña.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [ChangePasswordThrottle]

    def post(self, request):
        ser = ChangePasswordRequestSerializer(data=request.data)
        if not ser.is_valid():
            return self._error(
                'VALIDATION_ERROR',
                'Datos inválidos.',
                400,
                fields=ser.errors,
            )

        user = request.user
        data = ser.validated_data
        ip = self._get_ip(request)

        # PASO 7: validar contraseña actual
        if not user.check_password(data['current_password']):
            return self._error('WRONG_CURRENT_PASSWORD',
                               'Contraseña actual incorrecta.', 400)

        # PASO 8: política de complejidad
        violations = PasswordPolicyValidator().validate(
            data['new_password'], user
        )
        if violations:
            return Response(
                {'error': 'WEAK_PASSWORD',
                 'message': 'La nueva contraseña no cumple la política.',
                 'violations': violations},
                status=400,
            )

        # PASO 9a: igual a la actual
        if user.check_password(data['new_password']):
            return self._error('SAME_AS_CURRENT',
                               'La nueva contraseña debe ser distinta de la actual.', 400)

        # PASO 9b: historial
        from apps.users.models import PasswordHistory
        recent = (PasswordHistory.objects.filter(user=user)
                  .order_by('-changed_at')[:PasswordHistory.HISTORY_DEPTH])
        for entry in recent:
            import django.contrib.auth.hashers as hashers
            if hashers.check_password(data['new_password'], entry.password_hash):
                return self._error('PASSWORD_REUSED',
                                   'No puedes reutilizar una de tus últimas 5 contraseñas.', 400)

        # PASOS 10-13: transacción atómica
        prior_first_login = user.first_login
        try:
            result = self._commit_change(
                user=user,
                new_password=data['new_password'],
                prior_first_login=prior_first_login,
                ip=ip,
                request=request,
            )
        except DatabaseError:
            return self._error('DB_TRANSIENT_ERROR',
                               'Error transitorio. Reintente en breve.', 503,
                               retry_after=30)

        return Response(result, status=200)

    @staticmethod
    @transaction.atomic
    def _commit_change(user, new_password, prior_first_login, ip, request):
        """
        PASOS 10-13 dentro de transaction.atomic.
        Fuente: uc-auth-04/flujo-principal.rst § 3.3 Atomicidad.
        """
        from apps.authentication.models import Session
        from apps.users.models import PasswordHistory
        from apps.audit.services import AuditLogService
        now = timezone.now()

        # PASO 10: UPDATE User
        user.set_password(new_password)
        user.first_login = False
        user.password_changed_at = now
        user.save(update_fields=['password', 'first_login', 'password_changed_at'])

        # PASO 11: PasswordHistory
        PasswordHistory.record_and_purge(user)

        # PASO 12: cerrar otras Sessions
        current_session_id = None
        if hasattr(request, 'auth') and request.auth:
            current_session_id = getattr(request.auth, 'payload', {}).get('session_id')

        other_sessions_qs = Session.objects.filter(user=user, state='ACTIVE')
        if current_session_id:
            other_sessions_qs = other_sessions_qs.exclude(
                session_id=current_session_id
            )
        closed_count = other_sessions_qs.count()
        for sess in other_sessions_qs:
            sess.close(reason='PASSWORD_CHANGED')

        # FA-01: si la sesión actual era restricted, promoverla a full
        # CA-08: scope_upgraded=True si el usuario venía de first_login=True
        # (independientemente de si hay sesión activa con scope restrictido)
        scope_upgraded = bool(prior_first_login)
        if prior_first_login and current_session_id:
            Session.objects.filter(
                session_id=current_session_id,
                state='ACTIVE',
                scope='restricted',
            ).update(scope='full')

        # PASO 13: AuditEvent PASSWORD_CHANGED (CNST-026: sin contraseña en payload)
        AuditLogService.emit(
            event_type='PASSWORD_CHANGED',
            actor_user_id=user.pk,
            payload={
                'ip': ip,
                'prior_first_login': prior_first_login,
                'other_sessions_closed_count': closed_count,
                'scope_upgrade': scope_upgraded,
            },
        )

        return {
            'message': 'Contraseña actualizada',
            'changed_at': now.isoformat(),
            'next_step': 'landing',
            'scope_upgraded': scope_upgraded,
            'other_sessions_closed': closed_count,
        }

    @staticmethod
    def _error(code: str, message: str, http_status: int,
               fields: dict | None = None,
               retry_after: int | None = None) -> Response:
        body: dict = {'error': code, 'message': message}
        if fields:
            body['fields'] = fields
        if retry_after:
            body['retry_after'] = retry_after
        return Response(body, status=http_status)

    @staticmethod
    def _get_ip(request) -> str:
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        return xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR', '')
