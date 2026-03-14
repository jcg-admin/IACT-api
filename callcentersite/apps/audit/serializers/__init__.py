"""
Audit Serializers - Organización con SRP.

Este paquete organiza los serializers de audit aplicando el principio
de Responsabilidad Única (Single Responsibility Principle).

Estructura:
- auditlog_serializers.py: Serialización de logs de auditoría

Importaciones centralizadas para mantener compatibilidad:
    from apps.audit.serializers import AuditLogSerializer
    from apps.audit.serializers import AuditLogSummarySerializer

Características:
- READ-ONLY: Los logs de auditoría son inmutables
- Campos enriched: username, full_name
- Performance optimizado: versión summary sin campos pesados

Principios aplicados:
- SRP: Responsabilidad única (logs de auditoría)
- Immutability: Todos los campos son read-only
- Clean Code: Información de usuario enriquecida
"""

# ====================================================================================
# AUDITLOG SERIALIZERS
# ====================================================================================

from .auditlog_serializers import (
    AuditLogSerializer,
    AuditLogSummarySerializer,
)

# ====================================================================================
# __all__ - Exportaciones públicas
# ====================================================================================

__all__ = [
    # AuditLog serializers
    'AuditLogSerializer',
    'AuditLogSummarySerializer',
]

# ====================================================================================
# RESUMEN
# ====================================================================================
#
# Total Serializers: 2
#
# AuditLog (2):
#   [SUCCESS] AuditLogSerializer - Log completo con detalles
#   [SUCCESS] AuditLogSummarySerializer - Resumen para listados
#
# Características:
#   [SUCCESS] SRP aplicado (1 archivo con responsabilidad única)
#   [SUCCESS] READ-ONLY (logs inmutables)
#   [SUCCESS] Campos enriched (username, full_name)
#   [SUCCESS] Performance optimizado (summary vs detail)
#   [SUCCESS] Auditoría completa (action, resource, result, timestamp)
#   [SUCCESS] IP tracking (ip_address, user_agent)
#   [SUCCESS] Compatibilidad mantenida
#
# ====================================================================================
