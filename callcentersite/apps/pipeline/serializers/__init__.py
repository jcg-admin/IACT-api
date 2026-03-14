"""
Pipeline Serializers - Organización con SRP.

Este paquete organiza los serializers de pipeline aplicando el principio
de Responsabilidad Única (Single Responsibility Principle).

Estructura:
- center_serializers.py: Serialización de centros de llamadas
- service_serializers.py: Serialización de servicios
- callrecord_serializers.py: Serialización de registros de llamadas
- callnote_serializers.py: Serialización de notas de llamadas

Importaciones centralizadas para mantener compatibilidad:
    from apps.pipeline.serializers import CenterSerializer
    from apps.pipeline.serializers import ServiceSerializer
    # etc.

Principios aplicados:
- SRP: Cada archivo tiene una responsabilidad única
- DRY: Evitar duplicación de código
- Clean Code: Nombres descriptivos y organización clara
- Performance: Serializers list/detail separados
"""

# ====================================================================================
# CENTER SERIALIZERS
# ====================================================================================

from .center_serializers import (
    CenterSerializer,
    CenterListSerializer,
    CenterDetailSerializer,
)

# ====================================================================================
# SERVICE SERIALIZERS
# ====================================================================================

from .service_serializers import (
    ServiceSerializer,
    ServiceListSerializer,
    ServiceDetailSerializer,
)

# ====================================================================================
# CALLRECORD SERIALIZERS
# ====================================================================================

from .callrecord_serializers import (
    CallRecordSerializer,
    CallRecordListSerializer,
    CallRecordStatsSerializer,
)

# ====================================================================================
# CALLNOTE SERIALIZERS
# ====================================================================================

from .callnote_serializers import (
    CallNoteSerializer,
)

# ====================================================================================
# __all__ - Exportaciones públicas
# ====================================================================================

__all__ = [
    # Center serializers
    'CenterSerializer',
    'CenterListSerializer',
    'CenterDetailSerializer',
    
    # Service serializers
    'ServiceSerializer',
    'ServiceListSerializer',
    'ServiceDetailSerializer',
    
    # CallRecord serializers
    'CallRecordSerializer',
    'CallRecordListSerializer',
    'CallRecordStatsSerializer',
    
    # CallNote serializers
    'CallNoteSerializer',
]

# ====================================================================================
# RESUMEN
# ====================================================================================
#
# Total Serializers: 10
#
# Centros (3):
#   [SUCCESS] CenterSerializer - Centro con métricas de servicios
#   [SUCCESS] CenterListSerializer - Listado simplificado
#   [SUCCESS] CenterDetailSerializer - Centro con servicios anidados
#
# Servicios (3):
#   [SUCCESS] ServiceSerializer - Servicio con métricas de usuarios
#   [SUCCESS] ServiceListSerializer - Listado simplificado
#   [SUCCESS] ServiceDetailSerializer - Servicio con centro anidado
#
# Registros de llamadas (3):
#   [SUCCESS] CallRecordSerializer - Registro completo con métricas
#   [SUCCESS] CallRecordListSerializer - Listado simplificado
#   [SUCCESS] CallRecordStatsSerializer - Estadísticas agregadas
#
# Notas de llamadas (1):
#   [SUCCESS] CallNoteSerializer - Nota completa con info de usuario
#
# Características:
#   [SUCCESS] SRP aplicado (4 archivos con responsabilidades únicas)
#   [SUCCESS] Serializers list/detail separados para performance
#   [SUCCESS] Validaciones robustas (código único, centro activo, etc.)
#   [SUCCESS] Campos enriched (center_name, agent_username, etc.)
#   [SUCCESS] Métricas calculadas (answer_rate, abandonment_rate, etc.)
#   [SUCCESS] Import circular resuelto con imports locales
#   [SUCCESS] Compatibilidad mantenida
#
# ====================================================================================
