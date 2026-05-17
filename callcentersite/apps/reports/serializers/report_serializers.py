"""
Serializers para Report (Reportes).

Responsabilidad: Serialización de reportes y su creación.

Serializers:
- ReportSerializer: Reporte completo con información del creador
- ReportCreateSerializer: Creación simplificada de reportes

Principios aplicados:
- SRP: Responsabilidad única (reportes)
- Clean Code: Validaciones claras
- Type Safety: Validación de report_type
"""

from rest_framework import serializers
from apps.reports.models import Report


class ReportSerializer(serializers.ModelSerializer):
    """
    Serializer para Report.

    Incluye:
    - Datos básicos del reporte
    - Usuario creador (read-only)
    - Validación de filtros JSON
    - Campos display para choices
    """

    created_by_username = serializers.CharField(
        source='created_by.username',
        read_only=True
    )
    report_type_display = serializers.CharField(
        source='get_report_type_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )

    class Meta:
        model = Report
        fields = [
            'id',
            'name',
            'report_type',
            'report_type_display',
            'created_by',
            'created_by_username',
            'created_at',
            'updated_at',
            'filters',
            'total_records',
            'status',
            'status_display',
        ]
        read_only_fields = [
            'id',
            'created_by',
            'created_at',
            'updated_at',
            'total_records',
            'status',
        ]

    def validate_filters(self, value):
        """
        Validar que filters sea un dict válido.

        Args:
            value: Filtros en formato JSON

        Returns:
            dict: Filtros validados

        Raises:
            ValidationError: Si filters no es dict
        """
        if not isinstance(value, dict):
            raise serializers.ValidationError(
                "Filters debe ser un objeto JSON válido"
            )
        return value


class ReportCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear reportes.

    Simplificado para creación, sin campos calculados.
    El usuario creador se asigna automáticamente desde request.user.
    """

    class Meta:
        model = Report
        fields = [
            'name',
            'report_type',
            'filters',
        ]

    def validate_report_type(self, value):
        """
        Validar que report_type sea válido.

        Verifica contra Report.REPORT_TYPES.
        """
        valid_types = [choice[0] for choice in Report.REPORT_TYPES]
        if value not in valid_types:
            raise serializers.ValidationError(
                f"Tipo de reporte inválido. Opciones: {', '.join(valid_types)}"
            )
        return value
