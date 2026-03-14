"""
Serializers para CallRecord (Registros de llamadas).

Responsabilidad: Serialización de registros de llamadas y estadísticas.

Serializers:
- CallRecordSerializer: Registro completo con métricas calculadas
- CallRecordListSerializer: Listado simplificado de registros
- CallRecordStatsSerializer: Estadísticas agregadas (no vinculado a modelo)

Principios aplicados:
- SRP: Responsabilidad única (registros de llamadas)
- Clean Code: Validaciones de consistencia de datos
- Performance: Serializers list/detail separados
- FASE 0.2: Soporte para agent, call_type, recording_path, service
"""

from rest_framework import serializers
from apps.pipeline.models import CallRecord


class CallRecordSerializer(serializers.ModelSerializer):
    """
    Serializer para CallRecord.
    
    Campos adicionales calculados:
        - answer_rate (read-only): Tasa de respuesta %
        - abandonment_rate (read-only): Tasa de abandono %
        - avg_duration_seconds (read-only): Duración promedio
    
    FASE 0.2: Agregados campos agent, call_type, recording_path, service
    """
    
    answer_rate = serializers.SerializerMethodField()
    abandonment_rate = serializers.SerializerMethodField()
    avg_duration_seconds = serializers.SerializerMethodField()
    
    # FASE 0.2: Campos para ForeignKeys (mostrar nombres)
    agent_username = serializers.CharField(
        source='agent.username', 
        read_only=True,
        allow_null=True
    )
    service_name = serializers.CharField(
        source='service.nombre',
        read_only=True,
        allow_null=True
    )
    
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
            'duracion_total_segundos',
            # FASE 0.2: Campos nuevos
            'agent',
            'agent_username',
            'call_type',
            'recording_path',
            'service',
            'service_name',
            # Métricas calculadas
            'answer_rate',
            'abandonment_rate',
            'avg_duration_seconds',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_answer_rate(self, obj):
        """Tasa de respuesta en porcentaje."""
        return float(obj.answer_rate())
    
    def get_abandonment_rate(self, obj):
        """Tasa de abandono en porcentaje."""
        return float(obj.abandonment_rate())
    
    def get_avg_duration_seconds(self, obj):
        """Duración promedio por llamada contestada."""
        return float(obj.avg_duration_seconds())
    
    def validate(self, data):
        """
        Validar consistencia de datos.
        
        Valida que suma de contestadas + abandonadas <= total.
        """
        total = data.get('total_llamadas', 0)
        contestadas = data.get('llamadas_contestadas', 0)
        abandonadas = data.get('llamadas_abandonadas', 0)
        
        if contestadas + abandonadas > total:
            raise serializers.ValidationError(
                'La suma de llamadas contestadas y abandonadas no puede '
                'ser mayor al total de llamadas'
            )
        
        return data


class CallRecordListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listado de registros.
    
    Solo campos esenciales para optimizar queries.
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
        ]
    
    def get_answer_rate(self, obj):
        """Tasa de respuesta en porcentaje."""
        return float(obj.answer_rate())


class CallRecordStatsSerializer(serializers.Serializer):
    """
    Serializer para estadísticas agregadas de CallRecord.
    
    No vinculado a modelo, usado para stats endpoints.
    Recibe datos agregados desde la vista/service.
    """
    
    total_calls = serializers.IntegerField()
    total_answered = serializers.IntegerField()
    total_abandoned = serializers.IntegerField()
    answer_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    abandonment_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    unique_callers = serializers.IntegerField()
    avg_duration_seconds = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_duration_hours = serializers.DecimalField(max_digits=10, decimal_places=2)
    days_with_data = serializers.IntegerField()
