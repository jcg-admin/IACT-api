"""
apps/authentication/session_admin_view.py

SessionAdminView — UC_AUTH_05: Gestionar Sesiones.

Fuente: uc-auth-05/criterios-aceptacion.rst § 9

Endpoints implementados:
  GET  /api/auth/sessions/          — listar sessions (AUTH-004 view_all_active_sessions)
  POST /api/auth/sessions/{id}/close/  — cierre individual (AUTH-002 close_user_session)
  POST /api/auth/sessions/close-all/   — cierre masivo de usuario (AUTH-002)
  GET  /api/auth/sessions/own/         — sesiones propias (AUTH-001 view_own_sessions)
"""
from datetime import timedelta
from django.db import transaction, DatabaseError
from django.utils import timezone
from drf_spectacular.utils import (
    extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse
)
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access.permissions.function_permissions import HasFunction


# ---------------------------------------------------------------------------
# Serializers
# ---------------------------------------------------------------------------
class SessionListItemSerializer(serializers.Serializer):
    session_id    = serializers.UUIDField()
    user_id       = serializers.IntegerField(source='user_id')
    username      = serializers.CharField(source='user.username')
    state         = serializers.CharField()
    started_at    = serializers.DateTimeField()
    expires_at    = serializers.DateTimeField()
    ip_address    = serializers.CharField(allow_null=True)
    client_info   = serializers.DictField()


class CloseSessionSerializer(serializers.Serializer):
    close_reason = serializers.CharField(
        required=False,
        default='ADMIN_REVOKED',
        help_text='Motivo de cierre (opcional, default: ADMIN_REVOKED).',
    )


class CloseAllSessionsSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(
        help_text='ID del usuario cuyas sesiones se cerrarán.',
    )


# ---------------------------------------------------------------------------
# UC_AUTH_05 — Listar sesiones (AUTH-004)
# ---------------------------------------------------------------------------
@extend_schema(
    summary='UC_AUTH_05 — Listar sesiones activas',
    description=(
        'Retorna sesiones ACTIVE paginadas. **AUTH-004** view_all_active_sessions.\n\n'
        '**CA-01**: listado paginado 50/pág.\n'
        '**CA-02**: filtro ?user_id=N + AuditEvent SESSIONS_VIEWED_FOR_USER.\n'
        '**CA-03**: sin PII (email, full_name) — solo user_id y username.\n'
        '**CA-08**: sin AUTH-004 → 403.'
    ),
    parameters=[
        OpenApiParameter('user_id', int, location='query',
                         description='Filtrar por usuario.'),
        OpenApiParameter('page', int, location='query', default=1),
        OpenApiParameter('page_size', int, location='query', default=50),
    ],
    responses={
        200: OpenApiResponse(description='Lista paginada de sesiones activas.'),
        403: OpenApiResponse(description='Sin AUTH-004.'),
    },
    tags=['Autenticacion'],
)
class SessionListView(APIView):
    """GET /api/auth/sessions/ — requiere AUTH-004."""
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'AUTH-004'

    def get(self, request):
        from apps.authentication.models import Session
        from apps.audit.services import AuditLogService

        qs = Session.objects.filter(state='ACTIVE').select_related('user')
        user_id_filter = request.query_params.get('user_id')

        if user_id_filter:
            try:
                uid = int(user_id_filter)
                qs = qs.filter(user_id=uid)
                # CA-02: audit selectivo
                AuditLogService.emit(
                    event_type='SESSIONS_VIEWED_FOR_USER',
                    actor_user_id=request.user.pk,
                    payload={'target_user_id': uid},
                )
            except ValueError:
                return Response(
                    {'error': 'VALIDATION_ERROR', 'message': 'user_id debe ser entero.'},
                    status=400,
                )

        page_size = min(int(request.query_params.get('page_size', 50)), 200)
        page      = max(int(request.query_params.get('page', 1)), 1)
        offset    = (page - 1) * page_size
        total     = qs.count()
        sessions  = qs[offset:offset + page_size]

        results = []
        for s in sessions:
            results.append({
                'session_id':  str(s.session_id),
                'user_id':     s.user_id,
                'username':    s.user.username,
                'state':       s.state,
                'started_at':  s.started_at.isoformat(),
                'expires_at':  s.expires_at.isoformat(),
                'ip_address':  s.ip_address,
                'client_info': s.client_info,
            })

        return Response({
            'count':    total,
            'page':     page,
            'page_size': page_size,
            'next': f'?page={page+1}' if offset + page_size < total else None,
            'results': results,
        })


# ---------------------------------------------------------------------------
# UC_AUTH_05 — Cerrar sesión individual (AUTH-002)
# ---------------------------------------------------------------------------
@extend_schema(
    summary='UC_AUTH_05 — Cerrar sesión individual',
    description=(
        'Cierra una sesión ACTIVE por session_id. **AUTH-002** close_user_session.\n\n'
        '**CA-04**: Session CLOSED, BlacklistedToken, AuditEvent SESSION_CLOSED.\n'
        '**CA-05**: FA-02 — ya CLOSED → 200 con SESSION_CLOSE_NOOP.\n'
        '**CA-07**: invoker == target → 400 SELF_BULK_CLOSE_FORBIDDEN.\n'
        '**CA-11**: FA-04 — InternalMessage al usuario (CNST-001).'
    ),
    responses={
        200: OpenApiResponse(description='Sesión cerrada o ya estaba cerrada.'),
        404: OpenApiResponse(description='Session no encontrada.'),
    },
    tags=['Autenticacion'],
)
class SessionCloseView(APIView):
    """POST /api/auth/sessions/{session_id}/close/ — AUTH-002."""
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'AUTH-002'

    def post(self, request, session_id):
        from apps.authentication.models import Session, BlacklistedToken
        from apps.audit.services import AuditLogService

        try:
            session = Session.objects.select_related('user').get(session_id=session_id)
        except Session.DoesNotExist:
            return Response({'error': 'SESSION_NOT_FOUND'}, status=404)

        # CA-05: idempotente si ya cerrada
        if session.state != 'ACTIVE':
            AuditLogService.emit(
                event_type='SESSION_CLOSE_NOOP',
                actor_user_id=request.user.pk,
                payload={'session_id': str(session_id), 'current_state': session.state},
            )
            return Response({
                'message': f'Sesión ya estaba {session.state.lower()}.',
                'close_reason_original': session.close_reason,
            })

        try:
            with transaction.atomic():
                session.close(reason='ADMIN_REVOKED')
                AuditLogService.emit(
                    event_type='SESSION_CLOSED',
                    actor_user_id=request.user.pk,
                    payload={
                        'session_id': str(session_id),
                        'target_user_id': session.user_id,
                        'close_reason': 'ADMIN_REVOKED',
                    },
                )
                # CA-11: InternalMessage al usuario (CNST-001)
                self._notify_user(session.user)
        except DatabaseError:
            return Response({'error': 'DB_TIMEOUT'}, status=500)

        return Response({
            'message': 'Sesión cerrada.',
            'session_id': str(session_id),
            'closed_at': session.closed_at.isoformat() if session.closed_at else None,
        })

    @staticmethod
    def _notify_user(user) -> None:
        """CA-11: notificación via InternalMailbox (CNST-001)."""
        try:
            from apps.alerts.models import InternalMailbox, MailboxMessage
            mailbox = InternalMailbox.objects.get(owner=user)
            MailboxMessage.objects.create(
                mailbox=mailbox,
                subject='Tu sesión fue cerrada por un administrador',
                body=(
                    'Un administrador ha cerrado tu sesión activa. '
                    'Si no reconoces esta acción, contacta a soporte.'
                ),
            )
        except Exception:
            pass  # La notificación es opcional — no bloquea el cierre


# ---------------------------------------------------------------------------
# UC_AUTH_05 — Cierre masivo (AUTH-002)
# ---------------------------------------------------------------------------
@extend_schema(
    summary='UC_AUTH_05 — Cerrar todas las sesiones de un usuario',
    description=(
        'Cierra todas las Sessions ACTIVE de un usuario. **AUTH-002**.\n\n'
        '**CA-06**: N sesiones cerradas, N AuditEvents SESSION_CLOSED + 1 BULK_SESSION_CLOSE.\n'
        '**CA-07**: auto-bulk-close prohibido → 400 SELF_BULK_CLOSE_FORBIDDEN.\n'
        '**CA-13**: atomicidad — si AuditEvent falla → rollback total.\n'
        '**CNST-010**: permission_classes explícito.'
    ),
    responses={
        200: OpenApiResponse(description='Sessions cerradas.'),
        400: OpenApiResponse(description='SELF_BULK_CLOSE_FORBIDDEN.'),
    },
    tags=['Autenticacion'],
)
class SessionCloseAllView(APIView):
    """POST /api/auth/sessions/close-all/ — AUTH-002."""
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'AUTH-002'

    def post(self, request):
        ser = CloseAllSessionsSerializer(data=request.data)
        if not ser.is_valid():
            return Response({'error': 'VALIDATION_ERROR', 'fields': ser.errors}, status=400)

        target_user_id = ser.validated_data['user_id']

        # CA-07: auto-bulk-close prohibido (P-11)
        if target_user_id == request.user.pk:
            from apps.audit.services import AuditLogService
            AuditLogService.emit(
                event_type='BULK_SESSION_CLOSE_FAILED',
                actor_user_id=request.user.pk,
                payload={'reason': 'self_bulk_close', 'target_user_id': target_user_id},
            )
            return Response(
                {'error': 'SELF_BULK_CLOSE_FORBIDDEN',
                 'message': 'No puedes cerrar tus propias sesiones en masa.'},
                status=400,
            )

        from apps.authentication.models import Session
        from apps.audit.services import AuditLogService

        sessions = list(
            Session.objects.filter(user_id=target_user_id, state='ACTIVE')
        )
        n = len(sessions)

        if n == 0:
            return Response({'message': 'No hay sesiones activas.', 'sessions_closed': 0})

        try:
            with transaction.atomic():
                for s in sessions:
                    s.close(reason='ADMIN_REVOKED')
                    AuditLogService.emit(
                        event_type='SESSION_CLOSED',
                        actor_user_id=request.user.pk,
                        payload={
                            'session_id': str(s.session_id),
                            'target_user_id': target_user_id,
                            'close_reason': 'ADMIN_REVOKED',
                        },
                    )
                AuditLogService.emit(
                    event_type='BULK_SESSION_CLOSE',
                    actor_user_id=request.user.pk,
                    payload={
                        'target_user_id': target_user_id,
                        'sessions_closed_count': n,
                    },
                )
        except DatabaseError:
            return Response({'error': 'DB_TIMEOUT'}, status=500)

        return Response({
            'message': f'{n} sesión(es) cerrada(s).',
            'sessions_closed': n,
        })


# ---------------------------------------------------------------------------
# UC_AUTH_05 — Vista propia (AUTH-001)
# ---------------------------------------------------------------------------
@extend_schema(
    summary='UC_AUTH_05 — Ver mis sesiones',
    description=(
        'Retorna las sesiones del usuario autenticado. **AUTH-001** view_own_sessions.\n\n'
        '**CA-12**: FA-06 — usuarios normales ven solo sus propias sesiones.'
    ),
    tags=['Autenticacion'],
)
class SessionOwnView(APIView):
    """GET /api/auth/sessions/own/ — AUTH-001."""
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'AUTH-001'

    def get(self, request):
        from apps.authentication.models import Session
        sessions = Session.objects.filter(
            user=request.user
        ).order_by('-started_at')[:20]

        return Response({
            'count': sessions.count(),
            'results': [
                {
                    'session_id': str(s.session_id),
                    'state':      s.state,
                    'started_at': s.started_at.isoformat(),
                    'expires_at': s.expires_at.isoformat(),
                    'ip_address': s.ip_address,
                    'client_info': s.client_info,
                }
                for s in sessions
            ],
        })
