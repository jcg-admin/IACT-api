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
from drf_spectacular.utils import extend_schema
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
    """
    FR-007.02: validacion selectiva de campos modificados.
    - first_name/last_name: min=2, max=50.
    - email: EmailField.
    - state: ChoiceField + motivo obligatorio cuando state=INACTIVE.
    """
    first_name      = serializers.CharField(min_length=2, max_length=50, required=False)
    last_name       = serializers.CharField(min_length=2, max_length=50, required=False)
    email           = serializers.EmailField(required=False)
    state           = serializers.ChoiceField(
        choices=['ACTIVE', 'INACTIVE', 'BLOCKED', 'ELIMINATED'],
        required=False,
    )
    deactivation_reason = serializers.CharField(
        max_length=255, required=False, allow_blank=False,
        help_text='Motivo (obligatorio si state=INACTIVE; FR-007.02/03).'
    )

    def validate(self, attrs):
        if attrs.get('state') == 'INACTIVE' and not attrs.get('deactivation_reason'):
            raise serializers.ValidationError({
                'deactivation_reason': (
                    'Motivo obligatorio al pasar state=INACTIVE (FR-007.02).'
                )
            })
        return attrs


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
        fields_changed = [k for k in data.keys() if k != 'deactivation_reason']

        # FR-007.04: capturar valores anteriores ANTES de mutar.
        prior_values = {f: getattr(target, f, None) for f in fields_changed}
        new_values   = {f: data[f] for f in fields_changed}

        # FR-006.05/007.04: ip del admin para audit
        ip_admin = (
            request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
            or request.META.get('REMOTE_ADDR', '')
        ) or None

        try:
            with transaction.atomic():
                # Aplicar campos modificados (excluye deactivation_reason — no es atributo del modelo)
                for field, val in data.items():
                    if field in ('state', 'deactivation_reason'):
                        continue
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

                # FR-007.04: audit con prior/new values + ip
                AuditLogService.emit(
                    event_type='USER_MODIFIED',
                    actor_user_id=request.user.pk,
                    target_entity_type='User',
                    target_entity_id=str(user_id),
                    ip_address=ip_admin,
                    payload={
                        'target_user_id': user_id,
                        'fields_changed': fields_changed,
                        'prior_values': prior_values,
                        'new_values': new_values,
                        'state_transition': state_transition,
                        'sessions_closed_count': sessions_closed,
                        'deactivation_reason': data.get('deactivation_reason'),
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

    @staticmethod
    def _is_last_system_admin(target_user) -> bool:
        """
        FR-008.01: protege contra eliminacion del ultimo usuario con
        AccessGroup code='AGR-010' (system_admin_group).

        Retorna True solo si target_user es el unico miembro ACTIVE
        del grupo. Si el target no pertenece al grupo, retorna False.
        """
        from apps.access.models import AccessGroup, UserAccessGroup
        try:
            agr = AccessGroup.objects.get(code='AGR-010')
        except AccessGroup.DoesNotExist:
            return False  # sin AGR, no aplica la proteccion
        members = UserAccessGroup.objects.filter(
            access_group=agr, user__state='ACTIVE',
        ).exclude(user__state='ELIMINATED')
        target_is_member = members.filter(user=target_user).exists()
        if not target_is_member:
            return False
        return members.count() <= 1


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
        from apps.access.models import UserFunctionAssignment
        User = get_user_model()

        # FR-008.02: motivo de baja (opcional en body/query; persistido en audit).
        deactivation_reason = (
            (request.data.get('reason') if hasattr(request, 'data') else None)
            or request.query_params.get('reason')
            or ''
        )
        ip_admin = (
            request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
            or request.META.get('REMOTE_ADDR', '')
        ) or None

        # CA-03 / FR-008.01: auto-eliminación prohibida
        if user_id == request.user.pk:
            AuditLogService.emit(
                event_type='USER_ELIMINATE_FAILED',
                actor_user_id=request.user.pk,
                ip_address=ip_admin,
                payload={'reason': 'self_elimination', 'target_user_id': user_id},
            )
            return Response({'error': 'SELF_ELIMINATION_FORBIDDEN'}, status=400)

        try:
            target = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'error': 'USER_NOT_FOUND'}, status=404)

        # FR-008.01: no eliminar al ultimo admin de system_admin_group (AGR-010).
        if ModifyUserView._is_last_system_admin(target):
            AuditLogService.emit(
                event_type='USER_ELIMINATE_FAILED',
                actor_user_id=request.user.pk,
                ip_address=ip_admin,
                payload={
                    'reason': 'last_system_admin',
                    'target_user_id': user_id,
                },
            )
            return Response({
                'error': 'LAST_SYSTEM_ADMIN',
                'message': (
                    'No se puede eliminar al ultimo usuario con grupo '
                    'system_admin_group (FR-008.01 / AGR-010).'
                ),
            }, status=400)

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
                    target_entity_type='User',
                    target_entity_id=str(user_id),
                    ip_address=ip_admin,
                    payload={
                        'target_user_id':         user_id,
                        'sessions_closed_count':  len(sessions),
                        'assignments_revoked_count': len(assignments),
                        'deactivation_reason':    deactivation_reason or None,
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
