"""
Serializers para CallLog (Logs de llamadas IVR).
"""
# =============================================================================
# DEUDA TÉCNICA — PENDIENTE
# =============================================================================
# Fecha de eliminación: 2026-03-21
# Motivo: CallLogSerializer desactivado junto con el modelo CallLog.
#         La tabla call_logs no existe en ivr_legacy.
#         Reactivar cuando:
#           1. scripts/provisioners/mariadb/schema.sh esté implementado
#           2. La tabla call_logs exista en ivr_legacy (producción)
# Ver: documentos/planes/PLAN_IVR_SIMPLIFICACION_20260321.md
# =============================================================================
#
# from rest_framework import serializers
# from apps.ivr.models import CallLog
#
#
# class CallLogSerializer(serializers.ModelSerializer):
#     answer_rate  = serializers.SerializerMethodField()
#     abandon_rate = serializers.SerializerMethodField()
#
#     class Meta:
#         model  = CallLog
#         fields = (
#             'id', 'fecha', 'telefono', 'servicio_800',
#             'total_llamadas', 'llamadas_contestadas', 'llamadas_abandonadas',
#             'created_at', 'answer_rate', 'abandon_rate',
#         )
#         read_only_fields = fields
#
#     def get_answer_rate(self, obj):
#         if obj.total_llamadas > 0:
#             return round((obj.llamadas_contestadas / obj.total_llamadas) * 100, 2)
#         return 0.0
#
#     def get_abandon_rate(self, obj):
#         if obj.total_llamadas > 0:
#             return round((obj.llamadas_abandonadas / obj.total_llamadas) * 100, 2)
#         return 0.0
#
#
# class CallLogListSerializer(serializers.ModelSerializer):
#     class Meta:
#         model  = CallLog
#         fields = (
#             'id', 'fecha', 'telefono', 'servicio_800',
#             'total_llamadas', 'llamadas_contestadas', 'llamadas_abandonadas',
#         )
#         read_only_fields = fields
#
#
# class CallLogStatsSerializer(serializers.Serializer):
#     fecha_inicio               = serializers.DateField()
#     fecha_fin                  = serializers.DateField()
#     total_llamadas             = serializers.IntegerField()
#     total_contestadas          = serializers.IntegerField()
#     total_abandonadas          = serializers.IntegerField()
#     promedio_contestadas_dia   = serializers.FloatField()
#     tasa_respuesta_promedio    = serializers.FloatField()
