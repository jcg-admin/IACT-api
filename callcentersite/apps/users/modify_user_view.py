"""
apps/users/modify_user_view.py

ModifyUserView    — UC_USR_03: Modificar Usuario (PATCH parcial).
EliminateUserView — UC_USR_04: Eliminar Usuario (baja lógica BR-009).

Fuentes:
  uc-usr-03/criterios-aceptacion.rst, datos-involucrados.rst
  uc-usr-04/criterios-aceptacion.rst
"""
from django.db import transaction, DatabaseError
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access.permissions.function_permissions import HasFunction


# Transiciones de estado permitidas (UC_USR_03)
VALID_STATE_TRANSITIONS = {
    'ACTIVE':   {'INACTIVE', 'BLOCKED'},
    'INACTIVE': {'ACTIVE', 'BLOCKED'},
    'BLOCKED':  {'ACTIVE', 'INACTIVE'},
    # ELIMINATED: estado terminal (CA-08 UC_USR_03)
}


class ModifyUserSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=50, required=False)
    last_name  = serializers.CharField(max_length=50, required=False)
    email      = serializers.EmailField(required=False)
    state      = serializers.ChoiceField(
        choices=['ACTIVE', 'INACTIVE', 'BLOCKED', 'ELIMINATED'],
        required=False,
    )


@extend_schema(
    summary='UC_USR_03 — Modificar usuario (PATCH)',
    description=(
        'Modifica campos del usuario mediante PATCH parcial. **USR-002** modify_users.\n\n'
        '**CA-01**: cambio de first_name → USER_MODIFIED.\n'
        '**CA-02**: state→BLOCKED → Sessions cerradas + BlacklistedToken.\n'
        '**CA-03**: state→ACTIVE (desbloqueo).\n'
        '**CA-04**: auto-state-change → 400 SELF_STATE_CHANGE_FORBIDDEN.\n'
        '**CA-07**: email duplicado → 409.\n'
        '**CA-08**: transición inválida (ej: ELIMINATED→ACTIVE) → 400.'
    ),
    tags=['Usuarios'],
)
class ModifyUserView(APIView):
    """PATCH /api/users/{user_id}/  — USR-002 modify_users."""
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'USR-002'

    def patch(self, request, user_id):
        from django.contrib.auth import get_user_model
        from apps.audit.services import AuditLogService
        from apps.authentication.models import Session, BlacklistedToken
        User = get_user_model()

        try:
            target = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'error': 'USER_NOT_FOUND'}, status=404)

        ser = ModifyUserSerializer(data=request.data, partial=True)
        if not ser.is_valid():
            return Response({'error': 'VALIDATION_ERROR', 'fields': ser.errors}, status=400)

        data = ser.validated_data
        new_state = data.get('state')

        # CA-04: auto-state-change prohibido (P-11)
        if new_state and user_id == request.user.pk:
            AuditLogService.emit(
                event_type='USER_MODIFY_FAILED',
                actor_user_id=request.user.pk,
                payload={'reason': 'self_state_change', 'target_user_id': user_id},
            )
            return Response({'error': 'SELF_STATE_CHANGE_FORBIDDEN'}, status=400)

        # CA-08: transición inválida
        if new_state:
            allowed = VALID_STATE_TRANSITIONS.get(target.state, set())
            if new_state not in allowed:
                return Response({
                    'error': 'INVALID_STATE_TRANSITION',
                    'from':  target.state,
                    'to':    new_state,
                }, status=400)

        # CA-07: email duplicado
        if 'email' in data:
            if User.objects.filter(email=data['email']).exclude(pk=user_id).exists():
                return Response({'error': 'EMAIL_EXISTS'}, status=409)

        prior_state   = target.state
        fields_changed = list(data.keys())

        try:
            with transaction.atomic():
                # Aplicar campos modificados
                for field, val in data.items():
                    if field != 'state':
                        setattr(target, field, val)

                if new_state:
                    target.state = new_state
                    target.state_changed_at = timezone.now()

                target.last_modified_at = timezone.now()
                target.last_modified_by_admin = request.user
                target.save()

                sessions_closed = 0
                # CA-02: state→BLOCKED → cerrar Sessions y blacklistear
                if new_state == 'BLOCKED':
                    sessions_closed = self._close_user_sessions(target, 'ADMIN_BLOCKED')

                state_transition = (
                    {'from': prior_state, 'to': new_state}
                    if new_state else None
                )

                AuditLogService.emit(
                    event_type='USER_MODIFIED',
                    actor_user_id=request.user.pk,
                    payload={
                        'target_user_id': user_id,
                        'fields_changed': fields_changed,
                        'state_transition': state_transition,
                        'sessions_closed_count': sessions_closed,
                    },
                )

        except DatabaseError:
            return Response({'error': 'DB_TIMEOUT'}, status=500)

        return Response({
            'user_id':          user_id,
            'username':         target.username,
            'fields_changed':   fields_changed,
            'state_transition': state_transition if new_state else None,
            'sessions_closed':  sessions_closed if new_state == 'BLOCKED' else 0,
            'modified_at':      target.last_modified_at.isoformat(),
        })

    @staticmethod
    def _close_user_sessions(user, close_reason: str) -> int:
        from apps.authentication.models import Session
        sessions = list(Session.objects.filter(user=user, state='ACTIVE'))
        for s in sessions:
            s.close(reason=close_reason)
        return len(sessions)


@extend_schema(
    summary='UC_USR_04 — Eliminar usuario (baja lógica BR-009)',
    description=(
        'Baja definitiva del usuario. state→ELIMINATED. **USR-003** deactivate_users.\n\n'
        '**CA-01**: User.state=ELIMINATED, Sessions cerradas, Assignments revocados.\n'
        '**CA-02**: sin DELETE físico — registro preservado (BR-009).\n'
        '**CA-03**: auto-eliminación → 400.\n'
        '**CA-06**: ya ELIMINATED → 200 idempotente.'
    ),
    tags=['Usuarios'],
)
class EliminateUserView(APIView):
    """DELETE /api/users/{user_id}/  — USR-003 deactivate_users."""
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'USR-003'

    def delete(self, request, user_id):
        from django.contrib.auth import get_user_model
        from apps.audit.services import AuditLogService
        from apps.authentication.models import Session
        from apps.access.models import UserFunctionAssignment, UserAccessGroup
        User = get_user_model()

        # CA-03: auto-eliminación prohibida
        if user_id == request.user.pk:
            AuditLogService.emit(
                event_type='USER_ELIMINATE_FAILED',
                actor_user_id=request.user.pk,
                payload={'reason': 'self_elimination', 'target_user_id': user_id},
            )
            return Response({'error': 'SELF_ELIMINATION_FORBIDDEN'}, status=400)

        try:
            target = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'error': 'USER_NOT_FOUND'}, status=404)

        # CA-06: ya ELIMINATED (idempotente)
        if target.state == 'ELIMINATED':
            AuditLogService.emit(
                event_type='USER_ELIMINATE_NOOP',
                actor_user_id=request.user.pk,
                payload={'target_user_id': user_id},
            )
            return Response({
                'already_eliminated':    True,
                'original_eliminated_at': target.eliminated_at.isoformat() if target.eliminated_at else None,
            })

        try:
            with transaction.atomic():
                now = timezone.now()

                # Cerrar Sessions ACTIVE
                sessions = list(Session.objects.filter(user=target, state='ACTIVE'))
                for s in sessions:
                    s.close(reason='USER_ELIMINATED')

                # Revocar Assignments ACTIVE
                assignments = list(
                    UserFunctionAssignment.objects.filter(user=target, state='ACTIVE')
                )
                for a in assignments:
                    a.revoke(revoked_by=request.user, reason='USER_ELIMINATED')

                # Marcar User como ELIMINATED
                target.state                = 'ELIMINATED'
                target.eliminated_at        = now
                target.eliminated_by_admin  = request.user
                target.is_active            = False
                target.save(update_fields=[
                    'state', 'eliminated_at', 'eliminated_by_admin', 'is_active'
                ])

                AuditLogService.emit(
                    event_type='USER_ELIMINATED',
                    actor_user_id=request.user.pk,
                    payload={
                        'target_user_id':         user_id,
                        'sessions_closed_count':  len(sessions),
                        'assignments_revoked_count': len(assignments),
                    },
                )

        except DatabaseError:
            return Response({'error': 'DB_TIMEOUT'}, status=500)

        return Response({
            'state':                  'ELIMINATED',
            'eliminated_at':          target.eliminated_at.isoformat(),
            'sessions_closed':        len(sessions),
            'assignments_revoked':    len(assignments),
        })
