"""
Serializers para CallLog (Logs de llamadas IVR).

Responsabilidad: Serialización de logs de llamadas legacy (READ-ONLY).

Serializers:
- CallLogSerializer: Log completo con métricas calculadas
- CallLogListSerializer: Listado simplificado para performance
- CallLogStatsSerializer: Estadísticas agregadas

Constraints:
- CNST-003: CallLog es READ-ONLY (MariaDB ivr_legacy)

Principios aplicados:
- SRP: Responsabilidad única (logs de llamadas IVR)
- Clean Code: Cálculos de métricas explícitos
- READ-ONLY: No permite create/update/delete (datos legacy)
"""

from rest_framework import serializers
from apps.ivr.models import CallLog


class CallLogSerializer(serializers.ModelSerializer):
    """
    Serializer completo para CallLog legacy.
    
    Incluye métricas calculadas:
    - answer_rate: Porcentaje de llamadas contestadas
    - abandon_rate: Porcentaje de llamadas abandonadas
    
    CNST-003: READ-ONLY (no create/update/delete)
    """
    
    answer_rate = serializers.SerializerMethodField()
    abandon_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = CallLog
        # CLEAN CODE: Explicit is better than implicit (PEP 20)
        fields = (
            'id',
            'fecha',
            'telefono',
            'servicio_800',
            'total_llamadas',
            'llamadas_contestadas',
            'llamadas_abandonadas',
            'created_at',
            'answer_rate',
            'abandon_rate',
        )
        # Legacy data is read-only
        read_only_fields = fields
    
    def get_answer_rate(self, obj):
        """
        Calcula tasa de respuesta (%).
        
        Formula: (llamadas_contestadas / total_llamadas) * 100
        
        Returns:
            float: Porcentaje de llamadas contestadas (0-100)
        """
        if obj.total_llamadas > 0:
            return round((obj.llamadas_contestadas / obj.total_llamadas) * 100, 2)
        return 0.0
    
    def get_abandon_rate(self, obj):
        """
        Calcula tasa de abandono (%).
        
        Formula: (llamadas_abandonadas / total_llamadas) * 100
        
        Returns:
            float: Porcentaje de llamadas abandonadas (0-100)
        """
        if obj.total_llamadas > 0:
            return round((obj.llamadas_abandonadas / obj.total_llamadas) * 100, 2)
        return 0.0


class CallLogListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listado de CallLogs.
    
    Solo campos esenciales para performance en list views.
    
    CNST-003: READ-ONLY (no create/update/delete)
    """
    
    class Meta:
        model = CallLog
        # CLEAN CODE: Explicit is better than implicit (PEP 20)
        fields = (
            'id',
            'fecha',
            'telefono',
            'servicio_800',
            'total_llamadas',
            'llamadas_contestadas',
            'llamadas_abandonadas',
        )
        # Legacy data is read-only
        read_only_fields = fields


class CallLogStatsSerializer(serializers.Serializer):
    """
    Serializer para estadísticas agregadas de CallLogs.
    
    Usado para endpoints de estadísticas/reportes.
    No está vinculado a modelo (Serializer, no ModelSerializer).
    """
    
    fecha_inicio = serializers.DateField(
        help_text='Fecha inicio del periodo'
    )
    fecha_fin = serializers.DateField(
        help_text='Fecha fin del periodo'
    )
    total_llamadas = serializers.IntegerField(
        help_text='Total de llamadas en el periodo'
    )
    total_contestadas = serializers.IntegerField(
        help_text='Total de llamadas contestadas'
    )
    total_abandonadas = serializers.IntegerField(
        help_text='Total de llamadas abandonadas'
    )
    promedio_contestadas_dia = serializers.FloatField(
        help_text='Promedio de llamadas contestadas por día'
    )
    tasa_respuesta_promedio = serializers.FloatField(
        help_text='Tasa de respuesta promedio (%)'
    )
