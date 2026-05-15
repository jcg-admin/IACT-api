"""
apps/access/services.py

Servicios de dominio para el módulo de control de acceso.
"""
from django.utils import timezone


class ModuleAccessService:
    """
    Servicio para gestionar acceso de usuarios a módulos del sistema.

    RBAC v5.4.0: el acceso a módulos se concede via UserModuleAccess.
    """

    @classmethod
    def has_module_access(cls, user, module_code: str) -> bool:
        """
        Retorna True si el usuario tiene acceso activo al módulo indicado.

        Args:
            user: instancia de User.
            module_code: código canónico del módulo (ej. 'MOD_RPT').

        Returns:
            bool: True si tiene acceso activo.
        """
        if user.is_superuser:
            return True
        from apps.access.models import UserModuleAccess
        return UserModuleAccess.objects.filter(
            user=user,
            module__code=module_code,
            is_active=True,
        ).exists()

    @classmethod
    def grant_module_access(
        cls,
        user,
        module_code: str,
        granted_by,
        reason: str = '',
    ):
        """
        Otorga acceso a un módulo al usuario indicado.

        Args:
            user: instancia de User que recibirá el acceso.
            module_code: código canónico del módulo.
            granted_by: instancia de User que concede el acceso.
            reason: justificación del acceso.

        Returns:
            UserModuleAccess: instancia creada o activada.
        """
        from apps.access.models import UserModuleAccess, Module
        module = Module.objects.get(code=module_code)
        access, _ = UserModuleAccess.objects.get_or_create(
            user=user,
            module=module,
            defaults={
                'granted_by': granted_by,
                'reason': reason,
                'granted_at': timezone.now(),
                'is_active': True,
            },
        )
        if not access.is_active:
            access.is_active = True
            access.granted_by = granted_by
            access.reason = reason
            access.granted_at = timezone.now()
            access.save(update_fields=['is_active', 'granted_by', 'reason', 'granted_at'])
        return access

    @classmethod
    def revoke_module_access(cls, user, module_code: str, revoked_by) -> bool:
        """
        Revoca el acceso a un módulo.

        Returns:
            bool: True si se revocó, False si no tenía acceso.
        """
        from apps.access.models import UserModuleAccess
        updated = UserModuleAccess.objects.filter(
            user=user,
            module__code=module_code,
            is_active=True,
        ).update(
            is_active=False,
            revoked_by=revoked_by,
            revoked_at=timezone.now(),
        )
        return updated > 0
