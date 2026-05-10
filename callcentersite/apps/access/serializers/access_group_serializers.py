from drf_spectacular.utils import extend_schema_field
"""
Serializers para AccessGroup y UserAccessGroup.
C-001: Serializacion correcta para IACT-ui.

accessService.getGroupers() espera:
  [{ id, name, code, description, function_count }]

accessService.assignGrouper(userId, grouperId) espera respuesta:
  { id, user, access_group, granted_at, granted_by }
"""
from rest_framework import serializers
from apps.access.models import AccessGroup, UserAccessGroup


class AccessGroupSerializer(serializers.ModelSerializer):
    function_count = serializers.SerializerMethodField()

    class Meta:
        model = AccessGroup
        fields = [
            'id', 'name', 'code', 'description',
            'functions', 'function_count', 'is_active',
        ]
        read_only_fields = ['is_active']

    @extend_schema_field({'type': 'integer'})
    @extend_schema_field({'type': 'integer'})
    def get_function_count(self, obj):
        return obj.functions.count()


class AccessGroupListSerializer(serializers.ModelSerializer):
    """Lightweight para GET /access/groupers/."""
    function_count = serializers.SerializerMethodField()

    class Meta:
        model = AccessGroup
        fields = ['id', 'name', 'code', 'description', 'function_count']

    @extend_schema_field({'type': 'integer'})
    def get_function_count(self, obj):
        return obj.functions.count()


class UserAccessGroupSerializer(serializers.ModelSerializer):
    """
    Para assign/revoke de groupers.
    POST /access/groupers/assign → { userId, grouperId }
    """
    class Meta:
        model = UserAccessGroup
        fields = ['id', 'user', 'access_group', 'granted_at', 'granted_by']
        read_only_fields = ['granted_at', 'granted_by']
