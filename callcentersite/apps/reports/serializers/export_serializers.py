"""
Serializers para ExportJob (Jobs de Exportación).

Responsabilidad: Serialización de jobs de exportación con validación CNST-007.

Serializers:
- ExportJobSerializer: Job de exportación con progreso y validaciones

Constraints:
- CNST-007: Límite de 100K registros por exportación

Principios aplicados:
- SRP: Responsabilidad única (exportación)
- Clean Code: Validaciones explícitas
- Constraint Compliance: CNST-007 validado
"""

from rest_framework import serializers
from apps.reports.models import ExportJob


class ExportJobSerializer(serializers.ModelSerializer):
    """
    Serializer para ExportJob.
    
    CNST-007: Valida límite de 100K registros.
    
    Incluye:
    - Datos del job de exportación
    - Progreso de exportación (%)
    - Validación CNST-007
    - Validación de reporte completado
    """
    
    # Constante CNST-007
    MAX_EXPORT_SIZE = 100000
    
    report_name = serializers.CharField(
        source='report.name',
        read_only=True
    )
    format_display = serializers.CharField(
        source='get_format_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    progress = serializers.SerializerMethodField()
    
    class Meta:
        model = ExportJob
        fields = [
            'id',
            'report',
            'report_name',
            'format',
            'format_display',
            'file_path',
            'total_records',
            'exported_records',
            'progress',
            'status',
            'status_display',
            'created_at',
            'started_at',
            'completed_at',
            'error_message',
        ]
        read_only_fields = [
            'id',
            'file_path',
            'exported_records',
            'status',
            'created_at',
            'started_at',
            'completed_at',
            'error_message',
        ]
    
    def get_progress(self, obj):
        """
        Obtener porcentaje de progreso.
        
        Calcula el progreso de exportación redondeado a 2 decimales.
        """
        return round(obj.progress_percentage, 2)
    
    def validate_total_records(self, value):
        """
        Validar CNST-007: máximo 100K registros.
        
        Args:
            value: Total de registros a exportar
            
        Returns:
            int: Total validado
            
        Raises:
            ValidationError: Si excede límite CNST-007 o es negativo
        """
        if value > self.MAX_EXPORT_SIZE:
            raise serializers.ValidationError(
                f"CNST-007: La exportación no puede exceder "
                f"{self.MAX_EXPORT_SIZE:,} registros. "
                f"Total solicitado: {value:,}"
            )
        
        if value < 0:
            raise serializers.ValidationError(
                "Total de registros debe ser positivo"
            )
        
        return value
    
    def validate(self, data):
        """
        Validación adicional del ExportJob.
        
        Verifica que el reporte asociado exista y esté completado.
        Solo se pueden exportar reportes en estado 'completed'.
        """
        report = data.get('report')
        
        if report and report.status != 'completed':
            raise serializers.ValidationError({
                'report': 'Solo se pueden exportar reportes completados'
            })
        
        return data
