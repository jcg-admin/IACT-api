"""
apps/audit/access_audit_service.py

AccessScopeFilter    — UC_ACC_09: filtra eventos al scope MOD_Access.
AccessFilterValidator — UC_ACC_09: anti-SQLi en ordering.
"""

# Eventos de acceso (MOD_Access) — UC_ACC_09 CA-02
ACCESS_EVENT_TYPES = frozenset({
    'FUNCTIONS_ASSIGNED', 'FUNCTIONS_REVOKED', 'FUNCTIONS_REVOKE_NOOP',
    'FUNCTIONS_ASSIGN_NOOP', 'FUNCTIONS_ASSIGN_FAILED', 'FUNCTIONS_REVOKE_FAILED',
    'AGR_ASSIGNED', 'AGR_REVOKED', 'AGR_ASSIGN_NOOP',
    'SEPARATION_RULE_CREATED', 'SEPARATION_RULE_UPDATED', 'SEPARATION_RULE_DISABLED',
    'EXCEPTIONAL_GRANTED', 'EXCEPTIONAL_REVOKED',
    'EXCEPTIONAL_PERMISSION_GRANTED', 'EXCEPTIONAL_PERMISSION_REVOKED',
    'EXCEPTIONAL_PERMISSION_EXPIRED', 'EXCEPTIONAL_PERMISSION_REVOKE_NOOP',
    'ACCESS_GROUP_CREATED', 'ACCESS_GROUP_MODIFIED', 'ACCESS_GROUP_RETIRED',
    'ACCESS_AUDIT_VIEWED',
})

_ALLOWED_ORDERINGS = frozenset({
    'occurred_at', '-occurred_at', 'event_type', '-event_type',
    'actor_user_id', '-actor_user_id',
})


class AccessScopeFilter:
    @staticmethod
    def is_access_event(event_type: str) -> bool:
        return event_type in ACCESS_EVENT_TYPES

    @staticmethod
    def queryset(qs):
        return qs.filter(action__in=ACCESS_EVENT_TYPES)


class AccessFilterValidator:
    @staticmethod
    def validate_ordering(ordering: str) -> None:
        if ordering not in _ALLOWED_ORDERINGS:
            raise ValueError(
                f"ordering '{ordering}' no permitido — whitelist anti-SQLi (CA-07). "
                f"Válidos: {sorted(_ALLOWED_ORDERINGS)}"
            )
