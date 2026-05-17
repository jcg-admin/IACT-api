"""
apps/reports/share_service.py

ShareValidator — UC_RPT_11: valida target y permission.
"""
VALID_PERMISSIONS = {'read', 'clone'}
VALID_TARGET_TYPES = {'user', 'agr', 'segment_public'}


class ShareValidator:
    @staticmethod
    def validate(payload: dict) -> None:
        target_type = payload.get('target_type', '')
        target_id   = payload.get('target_id')
        owner_id    = payload.get('owner_id')
        permission  = payload.get('permission', 'read')

        if target_type not in VALID_TARGET_TYPES:
            raise ValueError(f"target_type '{target_type}' inválido.")
        if target_type == 'user' and target_id == owner_id:
            raise ValueError('No se puede compartir con uno mismo.')
        if permission not in VALID_PERMISSIONS:
            raise ValueError(f"permission '{permission}' inválido. Válidos: {sorted(VALID_PERMISSIONS)}")
