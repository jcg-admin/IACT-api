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

    def get_functions(self):
        """
        Retorna las funciones/permisos asignados al usuario.

        Incluye funciones directas y las heredadas por roles.
        """
        functions = set()
        if hasattr(self, 'user_functions'):
            for uf in self.user_functions.filter(is_active=True).select_related('function'):
                functions.add(uf.function.code)
        return list(functions)
