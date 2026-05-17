"""
Serializers para Acceso a Módulos.

Responsabilidad: Serialización de accesos de usuarios a módulos.

Serializers:
- UserModuleAccessSerializer: Acceso de usuario a módulo

Principios aplicados:
- SRP: Responsabilidad única (accesos a módulos)
- Clean Code: Campos enriched con información relacionada
"""

from rest_framework import serializers
from apps.access.models import UserModuleAccess


class UserModuleAccessSerializer(serializers.ModelSerializer):
    """
    Serializer para accesos de usuarios a módulos.

    Incluye información enriched:
    - user_username: Username del usuario
    - module_code: Código del módulo
    - module_name: Nombre del módulo
    - granted_by_username: Username de quien otorgó el acceso
    - revoked_by_username: Username de quien revocó el acceso
    """

    user_username = serializers.CharField(source='user.username', read_only=True)
    module_code = serializers.CharField(source='module.code', read_only=True)
    module_name = serializers.CharField(source='module.name', read_only=True)
    granted_by_username = serializers.CharField(
        source='granted_by.username',
        read_only=True,
        allow_null=True
    )
    revoked_by_username = serializers.CharField(
        source='revoked_by.username',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = UserModuleAccess
        fields = [
            'id',
            'user',
            'user_username',
            'module',
            'module_code',
            'module_name',
            'granted_at',
            'granted_by',
            'granted_by_username',
            'reason',
            'is_active',
            'revoked_at',
            'revoked_by',
            'revoked_by_username',
        ]
        read_only_fields = [
            'id',
            'granted_at',
            'granted_by',
            'revoked_at',
            'revoked_by',
        ]
