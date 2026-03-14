"""
Reports Serializers - Organización con SRP.

Este paquete organiza los serializers de reports aplicando el principio
de Responsabilidad Única (Single Responsibility Principle).

Estructura:
- report_serializers.py: Serialización de reportes
- export_serializers.py: Serialización de jobs de exportación

Importaciones centralizadas para mantener compatibilidad:
    from apps.reports.serializers import ReportSerializer
    from apps.reports.serializers import ExportJobSerializer
    # etc.

Constraints documentados:
- CNST-007: Límite de 100K registros por exportación

Principios aplicados:
- SRP: Cada archivo tiene una responsabilidad única
- DRY: Evitar duplicación de código
- Clean Code: Nombres descriptivos y organización clara
- Constraint Compliance: CNST-007 implementado
"""

# ====================================================================================
# REPORT SERIALIZERS
# ====================================================================================

from .report_serializers import (
    ReportSerializer,
    ReportCreateSerializer,
)

# ====================================================================================
# EXPORT SERIALIZERS
# ====================================================================================

from .export_serializers import (
    ExportJobSerializer,
)

# ====================================================================================
# __all__ - Exportaciones públicas
# ====================================================================================

__all__ = [
    # Report serializers
    'ReportSerializer',
    'ReportCreateSerializer',
    
    # Export serializers
    'ExportJobSerializer',
]

# ====================================================================================
# RESUMEN
# ====================================================================================
#
# Total Serializers: 3
#
# Reportes (2):
#   [SUCCESS] ReportSerializer - Reporte completo con creador
#   [SUCCESS] ReportCreateSerializer - Creación simplificada
#
# Exportación (1):
#   [SUCCESS] ExportJobSerializer - Job con progreso y CNST-007
#
# Características:
#   [SUCCESS] SRP aplicado (2 archivos con responsabilidades únicas)
#   [SUCCESS] Validaciones robustas (filters, report_type)
#   [SUCCESS] CNST-007 compliance (100K registros máx)
#   [SUCCESS] Campos enriched (created_by_username, report_name)
#   [SUCCESS] Progreso de exportación calculado
#   [SUCCESS] Validación de reporte completado
#   [SUCCESS] Compatibilidad mantenida
#
# ====================================================================================
