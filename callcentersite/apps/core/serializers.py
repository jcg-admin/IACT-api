"""
Serializers core - IACT Call Center System.

Django REST Framework serializers.
"""
from rest_framework import serializers
from apps.pipeline.models import CallRecord, Center, Service  # modelos en apps.pipeline


class CallRecordSerializer(serializers.ModelSerializer):
    """
    Serializer para CallRecord.
    
    Incluye campo calculado answer_rate.
    """
    
    answer_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = CallRecord
        fields = [
            'id',
            'fecha',
            'telefono',
            'servicio_800',
            'total_llamadas',
            'llamadas_contestadas',
            'llamadas_abandonadas',
            'answer_rate',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'answer_rate', 'created_at', 'updated_at']
    
    def get_answer_rate(self, obj):
        """Calcular answer_rate."""
        return str(obj.answer_rate())


class CenterSerializer(serializers.ModelSerializer):
    """Serializer para Center."""
    
    class Meta:
        model = Center
        fields = [
            'id',
            'nombre',
            'codigo',
            'activo',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ServiceSerializer(serializers.ModelSerializer):
    """Serializer para Service."""
    
    center_nombre = serializers.CharField(
        source='center.nombre',
        read_only=True
    )
    
    class Meta:
        model = Service
        fields = [
            'id',
            'numero_800',
            'nombre',
            'center',
            'center_nombre',
            'activo',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'center_nombre', 'created_at', 'updated_at']
