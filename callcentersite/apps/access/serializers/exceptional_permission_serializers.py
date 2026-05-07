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
    es_activo = serializers.SerializerMethodField()

    class Meta:
        model = ExceptionalPermission
        fields = [
            'id', 'user', 'function', 'function_code', 'function_name',
            'justificacion', 'estado', 'valido_desde', 'valido_hasta',
            'otorgado_por', 'creado_en', 'es_activo',
        ]
        read_only_fields = ['estado', 'otorgado_por', 'creado_en']

    def get_es_activo(self, obj):
        from django.utils import timezone
        now = timezone.now()
        return (
            obj.estado == 'aprobado'
            and obj.valido_desde <= now <= obj.valido_hasta
        )

    def validate_justificacion(self, value):
        if len(value) < 50:
            raise serializers.ValidationError(
                'La justificacion debe tener al menos 50 caracteres.')
        return value

    def validate(self, data):
        desde = data.get('valido_desde')
        hasta = data.get('valido_hasta')
        if desde and hasta and hasta <= desde:
            raise serializers.ValidationError(
                'valido_hasta debe ser posterior a valido_desde.')
        return data
