"""
apps/access/function_assign_view.py

FunctionAssignView   — UC_ACC_01: Asignar funciones con SoD check.
FunctionRevokeView   — UC_ACC_02: Revocar funciones (baja lógica BR-009).
AGRAssignView        — UC_ACC_04 / UC_PERM_01: Asignar AccessGroup a usuario.
AGRRevokeView        — UC_PERM_02: Revocar AccessGroup de usuario.
FunctionGroupFnView  — UC_PERM_06: Asignar funciones a AGR custom.

Fuentes:
  uc-acc-01/criterios-aceptacion.rst (22 CAs)
  uc-acc-02/criterios-aceptacion.rst
  uc-acc-04/criterios-aceptacion.rst
  uc-perm-01/criterios-aceptacion.rst
  uc-perm-02/criterios-aceptacion.rst
  uc-perm-06/criterios-aceptacion.rst
"""
from django.db import transaction, DatabaseError
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access.permissions.function_permissions import HasFunction


# ---------------------------------------------------------------------------
# DutySeparationValidator — BR-007: validar separación de funciones antes de asignar.
# STD_008 FASE 1 (2026-05-13): SoDValidator → DutySeparationValidator
# ---------------------------------------------------------------------------
class DutySeparationValidator:
    """
    Valida reglas de separación de funciones (CNST-030) antes de asignar.

    UC_ACC_01 CA-05/06: all-or-nothing ante violación de separación.
    UC_ACC_04 CA-03: SoD check en asignación de grupo (AGR).
    Especificación BR-007.
    """
    @staticmethod
    def validate(user, new_function_codes: list[str]) -> list[dict]:
        """
        Evalúa las reglas de separación activas (state=ENABLED) contra
        el conjunto efectivo de funciones: actuales del usuario + nuevas a asignar.

        Retorna lista de violaciones: [{rule_id, rule_code, conflict_pair}].
        Lista vacía = sin violaciones — asignación puede proceder.
        """
        from apps.access.models import SeparationRule, UserFunctionAssignment
        violations = []
        current_codes = set(
            UserFunctionAssignment.objects.filter(user=user, state='ACTIVE')
            .values_list('function__code', flat=True)
        )
        all_codes = current_codes | set(new_function_codes)

        for rule in SeparationRule.objects.filter(state='ENABLED'):
            codes_set_a    = set(rule.functions_set_a.values_list('code', flat=True))
            codes_set_b    = set(rule.functions_set_b.values_list('code', flat=True))
            user_has_set_a = bool(all_codes & codes_set_a)
            user_has_set_b = bool(all_codes & codes_set_b)
            if user_has_set_a and user_has_set_b:
                violations.append({
                    'rule_id':       rule.pk,
                    'rule_code':     rule.code,
                    'conflict_pair': [list(codes_set_a), list(codes_set_b)],
                })
        return violations


# ---------------------------------------------------------------------------
# UC_ACC_01 — FunctionAssignView
# ---------------------------------------------------------------------------
class FunctionAssignSerializer(serializers.Serializer):
    function_ids = serializers.ListField(child=serializers.IntegerField(), min_length=1)
    expires_at   = serializers.DateTimeField(required=False, allow_null=True)
    reason       = serializers.CharField(required=False, allow_blank=True, default='')


@extend_schema(
    summary='UC_ACC_01 — Asignar funciones a usuario',
    description=(
        'Asigna funciones RBAC a un usuario con validación de separación (BR-007).\n\n'
        '**CA-01**: asignación exitosa → 201, Assignments, AuditEvent, cache invalidada.\n'
        '**CA-03**: ya activa → skipped (idempotente).\n'
        '**CA-05**: violación de separación → 409 SEPARATION_RULE_VIOLATION, rollback total.\n'
        '**CA-06**: all-or-nothing — si 1 viola, ninguna se asigna.\n'
        '**CA-07**: auto-asignación → 400 SELF_ASSIGN_FORBIDDEN.\n'
        '**CA-21**: re-asignación post-revocación → NUEVO Assignment preservando historial.'
    ),
    tags=['Control de Acceso'],
)
class FunctionAssignView(APIView):
    """POST /api/access/users/{user_id}/functions/  — ACC-001 assign_functions."""
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'ACC-001'

    def post(self, request, user_id):
        from apps.access.models import Function, UserFunctionAssignment
        from apps.audit.services import AuditLogService
        from apps.access.services.permission_service import PermissionCache
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # CA-07: auto-asignación prohibida (P-11)
        if user_id == request.user.pk:
            AuditLogService.emit(
                event_type='FUNCTIONS_ASSIGN_FAILED',
                actor_user_id=request.user.pk,
                payload={'reason': 'self_assign', 'target_user_id': user_id},
            )
            return Response({'error': 'SELF_ASSIGN_FORBIDDEN'}, status=400)

        # CA-09: user no existe
        try:
            target = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'error': 'USER_NOT_FOUND'}, status=404)

        # CA-10: User ELIMINATED rechaza
        if target.state == 'ELIMINATED':
            return Response({'error': 'INVALID_USER_STATE', 'state': target.state}, status=400)

        ser = FunctionAssignSerializer(data=request.data)
        if not ser.is_valid():
            return Response({'error': 'VALIDATION_ERROR', 'fields': ser.errors}, status=400)

        data       = ser.validated_data
        fn_ids     = data['function_ids']
        expires_at = data.get('expires_at')

        # CA-17/18: validar expires_at bounds
        if expires_at:
            now = timezone.now()
            if expires_at < now + timezone.timedelta(hours=1):
                return Response({'error': 'VALIDATION_ERROR', 'message': 'expires_at debe ser > now+1h.'}, status=400)
            if expires_at > now + timezone.timedelta(days=365):
                return Response({'error': 'VALIDATION_ERROR', 'message': 'expires_at máximo 1 año.'}, status=400)

        # CA-11: functions válidas
        fns = list(Function.objects.filter(pk__in=fn_ids))
        if len(fns) < len(fn_ids):
            missing = set(fn_ids) - {f.pk for f in fns}
            return Response({'error': 'FUNCTION_NOT_FOUND', 'missing_ids': list(missing)}, status=400)

        # CA-12: function activa
        inactive = [f.code for f in fns if not f.is_active]
        if inactive:
            return Response({'error': 'FUNCTION_INACTIVE', 'codes': inactive}, status=400)

        new_codes = [f.code for f in fns]

        # CA-05/06: validar SoD
        violations = DutySeparationValidator.validate(target, new_codes)
        if violations:
            AuditLogService.emit(
                event_type='FUNCTIONS_ASSIGN_FAILED',
                actor_user_id=request.user.pk,
                payload={'target_user_id': user_id, 'reason': 'separation_rule_violation', 'violations': violations},
            )
            return Response({
                'error': 'SEPARATION_RULE_VIOLATION',
                'violations': violations,
            }, status=409)

        assigned = []
        skipped  = []

        try:
            with transaction.atomic():
                for fn in fns:
                    # CA-03/CA-21: verificar asignación existente ACTIVE
                    existing_active = UserFunctionAssignment.objects.filter(
                        user=target, function=fn, state='ACTIVE'
                    ).first()

                    if existing_active:
                        # CA-03: ya activa → skip
                        skipped.append({'function_id': fn.pk, 'code': fn.code, 'reason': 'already_active'})
                        continue

                    # CA-21: puede existir REVOKED → crear NUEVO preservando historial
                    assignment = UserFunctionAssignment.objects.create(
                        user=target,
                        function=fn,
                        state='ACTIVE',
                        is_active=True,
                        assigned_by=request.user,
                        reason=data.get('reason', ''),
                        expires_at=expires_at,
                    )
                    assigned.append({'function_id': fn.pk, 'code': fn.code, 'assignment_id': assignment.pk})

                if assigned:
                    AuditLogService.emit(
                        event_type='FUNCTIONS_ASSIGNED',
                        actor_user_id=request.user.pk,
                        payload={
                            'target_user_id': user_id,
                            'function_ids_assigned': [a['function_id'] for a in assigned],
                        },
                    )
                    # CA-14: invalidar cache post-COMMIT
                    PermissionCache.invalidate(user_id=user_id)
                else:
                    AuditLogService.emit(
                        event_type='FUNCTIONS_ASSIGN_NOOP',
                        actor_user_id=request.user.pk,
                        payload={'target_user_id': user_id, 'all_skipped': True},
                    )

        except DatabaseError:
            return Response({'error': 'DB_TIMEOUT'}, status=500)

        http_status = 201 if assigned else 200
        return Response({'assigned': assigned, 'skipped': skipped}, status=http_status)


# ---------------------------------------------------------------------------
# UC_ACC_02 — FunctionRevokeView
# ---------------------------------------------------------------------------
class FunctionRevokeSerializer(serializers.Serializer):
    function_ids  = serializers.ListField(child=serializers.IntegerField(), min_length=1)
    revoke_reason = serializers.CharField(min_length=1)


@extend_schema(
    summary='UC_ACC_02 — Revocar funciones de usuario (BR-009)',
    description=(
        'Revoca funciones RBAC (baja lógica — no DELETE físico, BR-009).\n\n'
        '**CA-01**: revocación → Assignment.state=REVOKED, cache invalidada.\n'
        '**CA-02**: soft-delete — Assignment preservado con historial.\n'
        '**CA-03**: revoke_reason obligatorio.\n'
        '**CA-06**: auto-revocación → 400 SELF_REVOKE_FORBIDDEN.'
    ),
    tags=['Control de Acceso'],
)
class FunctionRevokeView(APIView):
    """DELETE /api/access/users/{user_id}/functions/  — ACC-002 revoke_functions."""
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'ACC-002'

    def delete(self, request, user_id):
        from apps.access.models import UserFunctionAssignment
        from apps.audit.services import AuditLogService
        from apps.access.services.permission_service import PermissionCache
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # CA-06: auto-revocación prohibida
        if user_id == request.user.pk:
            AuditLogService.emit(
                event_type='FUNCTIONS_REVOKE_FAILED',
                actor_user_id=request.user.pk,
                payload={'reason': 'self_revoke', 'target_user_id': user_id},
            )
            return Response({'error': 'SELF_REVOKE_FORBIDDEN'}, status=400)

        try:
            target = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'error': 'USER_NOT_FOUND'}, status=404)

        if target.state == 'ELIMINATED':
            return Response({'error': 'INVALID_USER_STATE'}, status=400)

        ser = FunctionRevokeSerializer(data=request.data)
        if not ser.is_valid():
            return Response({'error': 'VALIDATION_ERROR', 'fields': ser.errors}, status=400)

        fn_ids       = ser.validated_data['function_ids']
        revoke_reason = ser.validated_data['revoke_reason']

        revoked = []
        skipped = []

        try:
            with transaction.atomic():
                for fn_id in fn_ids:
                    assignment = UserFunctionAssignment.objects.filter(
                        user=target, function_id=fn_id, state='ACTIVE',
                    ).first()

                    if not assignment:
                        skipped.append({'function_id': fn_id, 'reason': 'not_active'})
                        continue

                    assignment.revoke(revoked_by=request.user, reason=revoke_reason)
                    revoked.append({'function_id': fn_id, 'assignment_id': assignment.pk})

                if revoked:
                    AuditLogService.emit(
                        event_type='FUNCTIONS_REVOKED',
                        actor_user_id=request.user.pk,
                        payload={
                            'target_user_id': user_id,
                            'function_ids_revoked': [r['function_id'] for r in revoked],
                            'revoke_reason': revoke_reason,
                        },
                    )
                    PermissionCache.invalidate(user_id=user_id)
                else:
                    AuditLogService.emit(
                        event_type='FUNCTIONS_REVOKE_NOOP',
                        actor_user_id=request.user.pk,
                        payload={'target_user_id': user_id},
                    )

        except DatabaseError:
            return Response({'error': 'DB_TIMEOUT'}, status=500)

        return Response({'revoked': revoked, 'skipped': skipped})


# ---------------------------------------------------------------------------
# UC_ACC_04 / UC_PERM_01 — AGRAssignView
# ---------------------------------------------------------------------------
class AGRAssignSerializer(serializers.Serializer):
    access_group_id = serializers.IntegerField()
    expires_at      = serializers.DateTimeField(required=False, allow_null=True)


@extend_schema(
    summary='UC_ACC_04 / UC_PERM_01 — Asignar AccessGroup a usuario',
    description=(
        'Asigna un AGR a un usuario con validación de separación de funciones.\n\n'
        '**CA-01**: asignación exitosa → 201.\n'
        '**CA-02**: ya asignado → 200 already_assigned.\n'
        '**CA-03**: violación de separación → 409 SEPARATION_RULE_VIOLATION.\n'
        '**CA-05**: auto-asignación → 400.\n'
        '**CA-06**: AGR no existe → 400.'
    ),
    tags=['Control de Acceso'],
)
class AGRAssignView(APIView):
    """POST /api/access/users/{user_id}/groups/  — ACC-004 assign_function_groups."""
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'ACC-004'

    def post(self, request, user_id):
        from apps.access.models import AccessGroup, UserAccessGroup, Function
        from apps.audit.services import AuditLogService
        from apps.access.services.permission_service import PermissionCache
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # CA-05: auto-asignación
        if user_id == request.user.pk:
            return Response({'error': 'SELF_ASSIGN_FORBIDDEN'}, status=400)

        try:
            target = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'error': 'USER_NOT_FOUND'}, status=404)

        ser = AGRAssignSerializer(data=request.data)
        if not ser.is_valid():
            return Response({'error': 'VALIDATION_ERROR', 'fields': ser.errors}, status=400)

        agr_id = ser.validated_data['access_group_id']

        # CA-06: AGR no existe
        try:
            agr = AccessGroup.objects.get(pk=agr_id, is_active=True)
        except AccessGroup.DoesNotExist:
            return Response({'error': 'ACCESS_GROUP_NOT_FOUND'}, status=400)

        # CA-02: ya asignado (idempotente)
        if UserAccessGroup.objects.filter(user=target, access_group=agr).exists():
            AuditLogService.emit(
                event_type='AGR_ASSIGN_NOOP',
                actor_user_id=request.user.pk,
                payload={'target_user_id': user_id, 'agr_id': agr_id},
            )
            return Response({'already_assigned': True, 'agr_code': agr.code}, status=200)

        # CA-03: validar separación — las funciones del AGR vs las del usuario
        agr_codes = list(agr.functions.values_list('code', flat=True))
        violations = DutySeparationValidator.validate(target, agr_codes)
        if violations:
            return Response({'error': 'SEPARATION_RULE_VIOLATION', 'violations': violations}, status=409)

        # Calcular cuántas funciones ya tiene el usuario directamente
        from apps.access.models import UserFunctionAssignment
        direct_codes = set(
            UserFunctionAssignment.objects.filter(user=target, state='ACTIVE')
            .values_list('function__code', flat=True)
        )
        already_present = len(set(agr_codes) & direct_codes)
        added = len(agr_codes) - already_present

        with transaction.atomic():
            UserAccessGroup.objects.create(
                user=target,
                access_group=agr,
                granted_by=request.user,
            )
            AuditLogService.emit(
                event_type='AGR_ASSIGNED',
                actor_user_id=request.user.pk,
                payload={
                    'target_user_id': user_id,
                    'agr_id': agr_id,
                    'agr_code': agr.code,
                    'functions_count_added': added,
                },
            )
            PermissionCache.invalidate(user_id=user_id)

        return Response({
            'agr_code': agr.code,
            'functions_count_added': added,
            'functions_already_present_count': already_present,
        }, status=201)


# ---------------------------------------------------------------------------
# UC_PERM_02 — AGRRevokeView
# ---------------------------------------------------------------------------
@extend_schema(
    summary='UC_PERM_02 — Revocar AccessGroup de usuario',
    description=(
        'Revoca la pertenencia de un usuario a un AGR.\n\n'
        '**CA-01**: revocación exitosa, cache invalidada.\n'
        '**CA-03**: auto-revocación → 400.\n'
        '**CA-02**: ya sin el AGR → 200 noop.'
    ),
    tags=['Control de Acceso'],
)
class AGRRevokeView(APIView):
    """DELETE /api/access/users/{user_id}/groups/{agr_id}/  — ACC-010 revoke_function_group."""
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'ACC-010'

    def delete(self, request, user_id, agr_id):
        from apps.access.models import UserAccessGroup
        from apps.audit.services import AuditLogService
        from apps.access.services.permission_service import PermissionCache
        from django.contrib.auth import get_user_model
        User = get_user_model()

        if user_id == request.user.pk:
            return Response({'error': 'SELF_REVOKE_FORBIDDEN'}, status=400)

        try:
            target = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'error': 'USER_NOT_FOUND'}, status=404)

        membership = UserAccessGroup.objects.filter(
            user=target, access_group_id=agr_id
        ).first()

        if not membership:
            # CA-PERM-01 (UC_PERM_02): 404 AGR_NOT_ASSIGNED cuando el AGR
            # nunca fue asignado al usuario. Anti-info-leak: no exponer si
            # el AGR existe o no, solo que no está asignado.
            # Hallazgo H-F6-GRP-GC-002 (2026-05-14): antes devolvía 200 noop.
            return Response(
                {'error': 'AGR_NOT_ASSIGNED',
                 'detail': 'El AGR no está asignado al usuario.'},
                status=404,
            )

        with transaction.atomic():
            membership.delete()   # UserAccessGroup no tiene estado — DELETE físico permitido
            AuditLogService.emit(
                event_type='AGR_REVOKED',
                actor_user_id=request.user.pk,
                payload={'target_user_id': user_id, 'agr_id': agr_id},
            )
            PermissionCache.invalidate(user_id=user_id)

        return Response({'message': 'AGR revocado exitosamente.', 'agr_id': agr_id})


# ---------------------------------------------------------------------------
# UC_PERM_06 — FunctionGroupFnView: asignar funciones a AGR custom
# ---------------------------------------------------------------------------
class GroupFnSerializer(serializers.Serializer):
    function_ids = serializers.ListField(
        child=serializers.IntegerField(), min_length=1
    )
    change_reason = serializers.CharField(
        min_length=5,
        help_text='CA-09 (UC_PERM_06): obligatorio para trazabilidad.',
    )


@extend_schema(
    summary='UC_PERM_06 — Asignar funciones a AGR custom',
    description=(
        'Agrega funciones a un AGR custom (is_predefined=False).\n\n'
        '**CA-07**: predefinido → 400.\n'
        '**CA-06**: function no existe → 400.'
    ),
    tags=['Control de Acceso'],
)
class FunctionGroupFnView(APIView):
    """POST /api/access/groups/{agr_id}/functions/  — ACC-007 assign_functions_to_group."""
    permission_classes = [IsAuthenticated, HasFunction]
    required_function  = 'ACC-007'

    def post(self, request, agr_id):
        from apps.access.models import AccessGroup, Function
        from apps.audit.services import AuditLogService

        try:
            agr = AccessGroup.objects.get(pk=agr_id)
        except AccessGroup.DoesNotExist:
            return Response({'error': 'ACCESS_GROUP_NOT_FOUND'}, status=404)

        if agr.is_predefined:
            return Response({'error': 'PREDEFINED_NOT_MUTABLE'}, status=400)

        # CA-07: AGR RETIRED bloqueado
        if not agr.is_active:
            return Response({'error': 'ACCESS_GROUP_RETIRED'}, status=400)

        ser = GroupFnSerializer(data=request.data)
        if not ser.is_valid():
            return Response({'error': 'VALIDATION_ERROR', 'fields': ser.errors}, status=400)

        fn_ids      = ser.validated_data['function_ids']
        change_reason = ser.validated_data['change_reason']
        fns         = list(Function.objects.filter(pk__in=fn_ids, is_active=True))

        if len(fns) < len(fn_ids):
            missing = set(fn_ids) - {f.pk for f in fns}
            return Response({'error': 'FUNCTION_NOT_FOUND', 'missing_ids': list(missing)}, status=400)

        already = set(agr.functions.values_list('pk', flat=True))
        new     = [f for f in fns if f.pk not in already]
        skipped = [f for f in fns if f.pk in already]
        agr.functions.add(*new)

        # CA-01: COMPOSITION_CHANGED audit (F6-GC-T8 fix)
        AuditLogService.emit(
            event_type='COMPOSITION_CHANGED',
            actor_user_id=request.user.pk,
            payload={
                'agr_id': agr_id,
                'added': [f.code for f in new],
                'skipped': [f.code for f in skipped],
                'change_reason': change_reason,
            },
        )

        return Response({
            'agr_code':          agr.code,
            'functions_added':   len(new),
            'functions_skipped': len(skipped),
        }, status=201 if new else 200)
