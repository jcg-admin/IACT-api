from drf_spectacular.utils import extend_schema_field
"""
Serializers para ExceptionalPermission.
C-003.
"""
from rest_framework import serializers
from apps.access.models import ExceptionalPermission


class ExceptionalPermissionSerializer(serializers.ModelSerializer):
    function_code = serializers.CharField(
        source='function.code', read_only=True)
    function_name = serializers.CharField(
        source='function.name', read_only=True)
    is_currently_active = serializers.SerializerMethodField()

    class Meta:
        model = ExceptionalPermission
        fields = [
            'id', 'user', 'function', 'function_code', 'function_name',
            'justification', 'status', 'valid_from', 'valid_until',
            'granted_by', 'created_at', 'is_currently_active',
        ]
        read_only_fields = ['status', 'granted_by', 'created_at']

    @extend_schema_field({'type': 'boolean'})
    def get_is_currently_active(self, obj):
        from django.utils import timezone
        now = timezone.now()
        return (
            obj.status == 'approved'
            and obj.valid_from <= now <= obj.valid_until
        )

    def validate_justification(self, value):
        if len(value) < 50:
            raise serializers.ValidationError(
                'La justification debe tener al menos 50 caracteres.')
        return value

    def validate(self, data):
        desde = data.get('valid_from')
        hasta = data.get('valid_until')
        if desde and hasta and hasta <= desde:
            raise serializers.ValidationError(
                'valid_until debe ser posterior a valid_from.')
        return data
