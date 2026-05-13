"""
Modelos de usuario para el sistema IACT.
"""
import os

from django.contrib.auth.models import AbstractUser
from django.db import models


def avatar_upload_path(instance, filename):
    ext = filename.rsplit('.', 1)[-1].lower()
    return os.path.join('profiles', f'user_{instance.pk}_avatar.{ext}')


class User(AbstractUser):
    """
    Usuario extendido del sistema IACT.

    Agrega soporte para:
    - Avatar / foto de perfil
    - Funciones y permisos RBAC
    """

    avatar = models.ImageField(
        upload_to=avatar_upload_path,
        null=True,
        blank=True,
        verbose_name='Avatar',
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        default='',
        verbose_name='Telefono',
    )
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    state = models.CharField(
        max_length=10,
        choices=[
            ('ACTIVE',   'Activo'),
            ('INACTIVE', 'Inactivo'),   # BR-009: baja lógica
            ('BLOCKED',  'Bloqueado'),  # BR-015: 5 intentos fallidos
        ],
        default='ACTIVE',
        verbose_name='Estado',
        db_index=True,
        help_text='Estado canónico del usuario. Fuente: modelo-dominio-iact.rst § 4.1.',
    )
    first_login = models.BooleanField(
        default=True,
        verbose_name='Primer login',
        help_text='True al crear la cuenta. UC_AUTH_01 FA-01: fuerza cambio de contraseña.',
    )
    password_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Contraseña expira',
        help_text='UC_AUTH_01 FA-02: aviso cuando password_expires_at - now() < ventana.',
    )
    last_login_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Último login',
        help_text='UC_AUTH_01 paso 14: actualizado en cada login exitoso.',
        db_index=True,
    )


    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        db_table = 'users_user'

    def __str__(self):
        return self.get_full_name() or self.username

    def get_avatar_url(self):
        """Retorna la URL del avatar o None si no tiene."""
        if self.avatar and hasattr(self.avatar, 'url'):
            try:
                return self.avatar.url
            except Exception:
                return None
        return None

    def get_functions(self) -> list[str]:
        """
        Returns the effective function codes for this user.

        Union of three sources:
        1. UserPermission — functions assigned directly to the user.
        2. AccessGroup — functions via group membership.
        3. ExceptionalPermission — approved and currently valid.

        SeparationRule is not applied here. Rules are enforced at
        assignment time, not at query time. An already-assigned
        permission remains valid.
        """
        from django.utils import timezone
        from apps.access.models import (
            UserPermission, Function,
            ExceptionalPermission,
        )

        function_codes: set[str] = set()

        # 1. Direct UserPermission
        function_codes.update(
            UserPermission.objects.filter(user=self)
            .values_list('function__code', flat=True)
        )

        # 2. Via AccessGroup membership
        function_codes.update(
            Function.objects.filter(
                access_groups__memberships__user=self
            ).values_list('code', flat=True)
        )

        # 3. Active ExceptionalPermission
        now = timezone.now()
        function_codes.update(
            ExceptionalPermission.objects.filter(
                user=self,
                status='approved',
                valid_from__lte=now,
                valid_until__gte=now,
            ).values_list('function__code', flat=True)
        )

        return sorted(function_codes)

    def has_function(self, permission_django: str) -> bool:
        """
        Returns True if the user has the given function (by permission_django).

        Used by HasFunction permission class.
        Superusers always return True.
        """
        if self.is_superuser:
            return True
        from apps.access.models import Function
        # Resolve permission_django to function code, then check
        try:
            fn = Function.objects.get(
                permission_django=permission_django,
                is_active=True,
            )
        except Function.DoesNotExist:
            # If the function doesn't exist in DB, deny
            return False
        return fn.code in self.get_functions()
    def has_function_by_code(self, function_code: str) -> bool:
        """
        Verifica si el usuario tiene la función por código canónico v5.4.0.

        ADR-BACK-006: verificación por Function.code (ej: 'RPT-001').
        CNST-033: código en formato MOD-NNN.

        A diferencia de has_function() que usa permission_django (legacy),
        este método usa el campo code canónico.

        Args:
            function_code: Código canónico v5.4.0 (ej: 'RPT-001').

        Returns:
            bool: True si el usuario tiene la función, False si no.
        """
        if self.is_superuser:
            return True
        return function_code in self.get_functions()

