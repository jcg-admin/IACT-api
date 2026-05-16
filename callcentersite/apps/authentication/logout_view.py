"""
apps/authentication/logout_view.py

LogoutView — POST /api/auth/logout/ — UC_AUTH_02.

Fuente: uc-auth-02/flujo-principal.rst (14 pasos)
        uc-auth-02/datos-involucrados.rst § 7.3, § 7.4
        uc-auth-02/criterios-aceptacion.rst § 9

Flujo backend (pasos 4-9):
  PASO 4  Validar JWT (middleware DRF)
  PASO 5  Localizar Session ACTIVE
  PASO 6  Transitar Session → CLOSED (close_reason='USER_LOGOUT') [atomic]
  PASO 7  Blacklistear access + refresh tokens                   [atomic]
  PASO 8  Emitir AuditEvent LOGOUT                               [atomic]
  PASO 9  Retornar 200 con {message, logout_at}

Atomicidad PASOS 6-8: transaction.atomic().
CA-06/07: si blacklist o audit fallan → Session permanece ACTIVE (rollback).
CA-09 (frontend): fuera del scope de este archivo.
CA-15 (HTTPS): Apache / nginx — fuera del scope de este archivo.
"""
import logging
from django.db import transaction, DatabaseError
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView


# ---------------------------------------------------------------------------
# Throttle — CA-08: rate limit
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)

class LogoutThrottle(UserRateThrottle):
    rate = '30/min'
    scope = 'logout'


# ---------------------------------------------------------------------------
# Serializers
# ---------------------------------------------------------------------------
class LogoutRequestSerializer(serializers.Serializer):
    """Body opcional — solo refresh_token."""
    refresh_token = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='Refresh JWT. Si se omite se aplica FA-01 (solo access blacklisteado).',
    )


# ---------------------------------------------------------------------------
# LogoutView
# ---------------------------------------------------------------------------
@extend_schema(
    summary='UC_AUTH_02 — Cerrar Sesión',
    description=(
        'Cierra la sesión activa del usuario autenticado.\n\n'
        '**Pasos 6-8 son atómicos** (transaction.atomic):\n'
        '- PASO 6: Session.state → CLOSED, close_reason="USER_LOGOUT".\n'
        '- PASO 7: BlacklistedToken INSERT para access + refresh (si se provee).\n'
        '- PASO 8: AuditEvent LOGOUT (CNST-025/026).\n\n'
        '**CA-06/07**: si blacklist o AuditEvent fallan → rollback total, '
        'Session permanece ACTIVE.\n\n'
        '**FA-01**: sin refresh_token en body → solo access blacklisteado.\n\n'
        '**CA-02**: si Session ya está CLOSED → 200 con LOGOUT_REPLAY.\n\n'
        '**CNST-010**: permission_classes=[IsAuthenticated] explícito.\n\n'
        '**CA-10**: el token blacklisteado es rechazado por cualquier endpoint '
        'protegido en requests subsiguientes.'
    ),
    request=LogoutRequestSerializer,
    responses={
        200: OpenApiResponse(description='Sesión cerrada exitosamente.'),
        401: OpenApiResponse(description='Token inválido o expirado.'),
        429: OpenApiResponse(description='Rate limit excedido.'),
        500: OpenApiResponse(description='Error al blacklistear o auditar (CA-06/07).'),
    },
    tags=['Autenticacion'],
)
class LogoutView(APIView):
    """
    POST /api/auth/logout/

    UC_AUTH_02 — cierre voluntario de sesión.
    CNST-010: permission_classes explícito.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes   = [LogoutThrottle]

    def post(self, request):
        ser = LogoutRequestSerializer(data=request.data)
        ser.is_valid()   # no raise_exception — refresh_token es opcional
        refresh_token = ser.validated_data.get('refresh_token', '')

        user = request.user
        access_token_str = self._extract_access_token(request)

        # PASO 5 — Localizar Session ACTIVE del usuario
        from apps.authentication.models import Session
        session = (
            Session.objects
            .filter(user=user, state=Session.STATE_ACTIVE)
            .order_by('-started_at')
            .first()
        )

        if session is None:
            # CA-02: ya estaba cerrada (idempotente)
            self._emit_audit('LOGOUT_REPLAY', user.pk, {
                'reason': 'no_active_session',
            })
            return Response({
                'message': 'Sesión ya estaba cerrada.',
                'logout_at': timezone.now().isoformat(),
            }, status=200)

        # PASOS 6-8: transacción atómica
        try:
            logout_at = self._atomic_logout(
                session=session,
                user=user,
                access_token_str=access_token_str,
                refresh_token_str=refresh_token,
                ip=self._get_ip(request),
            )
        except DatabaseError:
            return Response({
                'error': 'DB_TIMEOUT',
                'message': 'Servicio temporalmente no disponible.',
            }, status=500)
        except Exception as exc:
            return Response({
                'error': 'INTERNAL_ERROR',
                'message': str(exc),
            }, status=500)

        return Response({
            'message': 'Sesión cerrada',
            'logout_at': logout_at,
        }, status=200)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def _atomic_logout(session, user, access_token_str, refresh_token_str, ip) -> str:
        """
        PASOS 6-8 dentro de transaction.atomic.
        Fuente: uc-auth-02/flujo-principal.rst § 3.3 Atomicidad.
        """
        from apps.authentication.models import BlacklistedToken
        from apps.audit.services import AuditLogService

        now = timezone.now()

        # PASO 6: cerrar Session
        session.close(reason='USER_LOGOUT')

        # PASO 7: blacklistear tokens
        refresh_invalidated = False
        if access_token_str:
            try:
                BlacklistedToken.blacklist_jwt(
                    access_token_str, BlacklistedToken.TYPE_ACCESS, user=user
                )
            except ValueError:
                pass  # token ya expirado o malformado — no bloquea el logout

        if refresh_token_str:
            try:
                BlacklistedToken.blacklist_jwt(
                    refresh_token_str, BlacklistedToken.TYPE_REFRESH, user=user
                )
                refresh_invalidated = True
            except ValueError as exc:
                # Token con formato inválido — ignorar, el logout continúa.
                # El refresh token ya expiró o fue malformado por el cliente.
                logger.warning("blacklist_jwt: token inválido para user=%s: %s", user.pk, exc)

        # PASO 8: AuditEvent LOGOUT (CNST-025/026)
        AuditLogService.emit(
            event_type='LOGOUT',
            actor_user_id=user.pk,
            payload={
                'session_id': str(session.session_id),
                'close_reason': 'USER_LOGOUT',
                'ip': ip,
                'refresh_token_invalidated': refresh_invalidated,
            },
        )

        return now.isoformat()

    @staticmethod
    def _extract_access_token(request) -> str:
        auth = request.META.get('HTTP_AUTHORIZATION', '')
        if auth.startswith('Bearer '):
            return auth[7:].strip()
        return ''

    @staticmethod
    def _emit_audit(event_type: str, user_id: int, payload: dict) -> None:
        try:
            from apps.audit.services import AuditLogService
            AuditLogService.emit(event_type=event_type, actor_user_id=user_id, payload=payload)
        except Exception:
            pass  # LOGOUT_REPLAY no debe fallar por auditoría

    @staticmethod
    def _get_ip(request) -> str:
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        return xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR', '')
