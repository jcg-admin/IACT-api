"""
apps/access/exceptional_permission_service.py

Servicios de dominio para UC_ACC_08, UC_PERM_03, UC_PERM_04.

JustificationValidator  — reason ≥ 20 chars + ticket_reference si política.
ExpirationPolicy        — NOW()+1h ≤ expires_at ≤ NOW()+30d.
AntiSelfActionPolicy    — P-11 anti-self-grant / anti-self-revoke.
ExceptionalPermissionService — grant() y revoke().
GrantPreviewService     — preview sin persistir (UC_PERM_03 CA-PERM-01).
"""
from datetime import timedelta
from django.db import transaction
from django.utils import timezone

MIN_JUSTIFICATION_LEN = 20
MIN_REASON_LEN        = 20
MIN_EXPIRES_HOURS     = 1
MAX_EXPIRES_DAYS      = 30


class JustificationValidator:
    @staticmethod
    def validate(justification: str, require_ticket: bool = False) -> None:
        if not justification or len(justification) < MIN_JUSTIFICATION_LEN:
            raise ValueError(
                f'justification debe tener al menos {MIN_JUSTIFICATION_LEN} caracteres '
                f'(CA-02, uc-acc-08).'
            )
        if require_ticket and 'TKT-' not in justification.upper():
            raise ValueError('TICKET_REFERENCE_REQUIRED: justification debe contener TKT-NNNNN (CA-11).')


class ExpirationPolicy:
    @staticmethod
    def validate(expires_at) -> None:
        if expires_at is None:
            raise ValueError('expires_at es obligatorio (CA-04).')
        now = timezone.now()
        if expires_at <= now + timedelta(hours=MIN_EXPIRES_HOURS):
            raise ValueError(
                f'expires_at debe ser al menos NOW()+{MIN_EXPIRES_HOURS}h (CA-03).'
            )
        if expires_at > now + timedelta(days=MAX_EXPIRES_DAYS):
            raise ValueError(
                f'expires_at no puede exceder NOW()+{MAX_EXPIRES_DAYS}d (CA-03).'
            )


class AntiSelfActionPolicy:
    @staticmethod
    def check_grant(invoker_id: int, target_id: int) -> None:
        if invoker_id == target_id:
            raise ValueError('SELF_GRANT_FORBIDDEN: auto-grant prohibido (CA-05, P-09).')

    @staticmethod
    def check_revoke(invoker_id: int, target_id: int) -> None:
        if invoker_id == target_id:
            raise ValueError('SELF_REVOKE_FORBIDDEN: auto-revoke prohibido (CA-07, P-11).')


class ExceptionalPermissionService:
    """
    Servicio principal de grant y revoke.

    Mailbox HARD (CA-07, CA-08): si _notify/_notify_revoke lanza, el error
    se propaga y el transaction.atomic() hace rollback total.
    """

    @classmethod
    def grant(cls, target_user, function_ids: list, expires_at,
              justification: str, ticket_reference: str,
              invoker, require_ticket: bool = False) -> dict:
        from apps.access.models import ExceptionalPermission, Function
        from apps.audit.services import AuditLogService

        # CA-02: justification ≥ 20 chars
        JustificationValidator.validate(justification, require_ticket=require_ticket)
        # CA-03/04: expires_at bounds
        ExpirationPolicy.validate(expires_at)
        # CA-05: anti-self
        AntiSelfActionPolicy.check_grant(invoker.pk, target_user.pk)

        functions = list(Function.objects.filter(id__in=function_ids))
        if not functions:
            raise ValueError('Ninguna función válida encontrada para los function_ids dados.')

        granted = []
        skipped = []

        with transaction.atomic():
            for fn in functions:
                # CA-09: idempotencia parcial — skip si ya existe ACTIVE
                existing = ExceptionalPermission.objects.filter(
                    user=target_user,
                    function=fn,
                    status=ExceptionalPermission.STATE_ACTIVE,
                ).first()
                if existing:
                    skipped.append({'function_id': fn.pk, 'function_code': fn.code})
                    continue

                perm = ExceptionalPermission.objects.create(
                    user=target_user,
                    function=fn,
                    justification=justification,
                    ticket_reference=ticket_reference,
                    status=ExceptionalPermission.STATE_ACTIVE,
                    granted_at=timezone.now(),
                    expires_at=expires_at,
                    granted_by=invoker,
                )
                granted.append({
                    'permission_id': perm.pk,
                    'function_id': fn.pk,
                    'function_code': fn.code,
                    'expires_at': expires_at.isoformat(),
                })

            # CA-07: mailbox HARD — dentro del atomic para que rollback incluya perm INSERT
            cls._notify(target_user, functions, expires_at, justification)

            # CA-12: audit con payload reforzado (sin email/full_name — CNST-026)
            AuditLogService.emit(
                event_type='EXCEPTIONAL_PERMISSION_GRANTED',
                actor_user_id=invoker.pk,
                payload={
                    'target_user_id':   target_user.pk,
                    'function_ids':     function_ids,
                    'expires_at':       expires_at.isoformat(),
                    'justification':    justification[:100],
                    'ticket_reference': ticket_reference,
                    'granted_count':    len(granted),
                    'skipped_count':    len(skipped),
                },
            )

        return {
            'target_user_id': target_user.pk,
            'granted':        granted,
            'skipped':        skipped,
            'justification':  justification,
            'ticket_reference': ticket_reference,
            'user_notified':  True,
            'granted_at':     timezone.now().isoformat(),
        }

    @classmethod
    def revoke(cls, permission, invoker, revoke_reason: str) -> dict:
        from apps.access.models import ExceptionalPermission
        from apps.audit.services import AuditLogService

        # CA-07: anti-self
        AntiSelfActionPolicy.check_revoke(invoker.pk, permission.user_id)

        # CA-06: revoke_reason ≥ 20 chars
        if not revoke_reason or len(revoke_reason) < MIN_REASON_LEN:
            raise ValueError(
                f'revoke_reason debe tener al menos {MIN_REASON_LEN} caracteres (CA-06).'
            )

        # CA-03: idempotencia — ya REVOKED
        if permission.status == ExceptionalPermission.STATE_REVOKED:
            AuditLogService.emit(
                event_type='EXCEPTIONAL_PERMISSION_REVOKE_NOOP',
                actor_user_id=invoker.pk,
                payload={'permission_id': permission.pk},
            )
            return {'noop': True, 'permission_id': permission.pk,
                    'state': permission.status}

        # CA-04: EXPIRED no revocable
        if permission.status == ExceptionalPermission.STATE_EXPIRED:
            raise ValueError('INVALID_STATE: no se puede revocar un permiso EXPIRED (CA-04).')

        previous_expires_at = permission.expires_at

        with transaction.atomic():
            permission.status    = ExceptionalPermission.STATE_REVOKED
            permission.revoked_at = timezone.now()
            permission.revoked_by = invoker
            permission.revoke_reason = revoke_reason
            permission.save(update_fields=[
                'status', 'revoked_at', 'revoked_by', 'revoke_reason',
            ])

            # CA-08: mailbox HARD
            cls._notify_revoke(permission.user, permission.function, revoke_reason)

            # CA-14: audit high-priority
            AuditLogService.emit(
                event_type='EXCEPTIONAL_PERMISSION_REVOKED',
                actor_user_id=invoker.pk,
                payload={
                    'target_user_id':     permission.user_id,
                    'permission_id':      permission.pk,
                    'function_id':        permission.function_id,
                    'function_code':      permission.function.code,
                    'revoke_reason':      revoke_reason[:100],
                    'previous_expires_at': (
                        previous_expires_at.isoformat() if previous_expires_at else None
                    ),
                },
            )

        return {
            'permission_id':    permission.pk,
            'target_user_id':   permission.user_id,
            'function_id':      permission.function_id,
            'function_code':    permission.function.code,
            'state':            ExceptionalPermission.STATE_REVOKED,
            'revoked_at':       permission.revoked_at.isoformat(),
            'revoked_by_admin_id': invoker.pk,
            'revoke_reason':    revoke_reason,
            'previous_expires_at': (
                previous_expires_at.isoformat() if previous_expires_at else None
            ),
            'user_notified':    True,
        }

    @staticmethod
    def _notify(user, functions, expires_at, justification: str) -> None:
        """CA-07: HARD — lanza si el mailbox falla. El atomic rollback recupera."""
        from apps.alerts.models import InternalMailbox
        fn_names = ', '.join(f.code for f in functions)
        mailbox, _ = InternalMailbox.objects.get_or_create(owner=user)
        mailbox.deliver_message(
            subject='Permiso temporal otorgado',
            body=(
                f'Se te otorgaron los siguientes permisos temporales: {fn_names}.\n'
                f'Expiran: {expires_at.isoformat()}\n'
                f'Motivo: {justification[:100]}'
            ),
            priority='info',
        )

    @staticmethod
    def _notify_revoke(user, function, revoke_reason: str) -> None:
        """CA-08: HARD — lanza si el mailbox falla."""
        from apps.alerts.models import InternalMailbox
        mailbox, _ = InternalMailbox.objects.get_or_create(owner=user)
        mailbox.deliver_message(
            subject='Permiso temporal revocado',
            body=(
                f'Tu permiso temporal {function.code} fue revocado anticipadamente.\n'
                f'Motivo: {revoke_reason[:100]}'
            ),
            priority='warning',
        )


class GrantPreviewService:
    """
    UC_PERM_03 CA-PERM-01: calcula impacto SIN persistir ni emitir audit.
    """

    @staticmethod
    def preview(target_user, function_ids: list, expires_at) -> dict:
        from apps.access.models import Function, SeparationRule

        ExpirationPolicy.validate(expires_at)
        functions = list(Function.objects.filter(id__in=function_ids))
        now = expires_at - expires_at  # timedelta zero
        duration_days = (expires_at - timezone.now()).days

        # Evaluar SoD conflicts (stub — count reglas que apliquen)
        sod_count = SeparationRule.objects.filter(
            functions_set_a__in=functions,
            state='ACTIVE',
        ).count() + SeparationRule.objects.filter(
            functions_set_b__in=functions,
            state='ACTIVE',
        ).count()

        warnings = []
        if sod_count > 0:
            warnings.append(f'{sod_count} reglas SoD potencialmente afectadas.')

        return {
            'target_user_id':          target_user.pk,
            'function_ids':            function_ids,
            'expires_at':              expires_at.isoformat(),
            'duration_days':           duration_days,
            'estimated_sod_violations': sod_count,
            'warnings':                warnings,
        }
