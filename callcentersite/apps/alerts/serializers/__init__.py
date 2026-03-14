"""
Alerts Serializers - Organización con SRP.

Este paquete organiza los serializers de alerts aplicando el principio
de Responsabilidad Única (Single Responsibility Principle).

Estructura:
- message_serializers.py: Serialización de mensajes internos
- alert_serializers.py: Serialización de configuraciones y suscripciones

Importaciones centralizadas para mantener compatibilidad:
    from apps.alerts.serializers import InternalMessageCreateSerializer
    from apps.alerts.serializers import AlertConfigurationSerializer
    # etc.

Principios aplicados:
- SRP: Cada archivo tiene una responsabilidad única
- DRY: Evitar duplicación de código
- Clean Code: Nombres descriptivos y organización clara
- Service Layer: Uso de services para lógica de negocio
"""

# ====================================================================================
# MESSAGE SERIALIZERS
# ====================================================================================

from .message_serializers import (
    UserBasicSerializer,
    MessageRecipientSerializer,
    InternalMessageListSerializer,
    InternalMessageDetailSerializer,
    InternalMessageCreateSerializer,
    InboxMessageSerializer,
)

# ====================================================================================
# ALERT SERIALIZERS
# ====================================================================================

from .alert_serializers import (
    AlertConfigurationSerializer,
    AlertSubscriptionSerializer,
    AlertSubscriptionCreateSerializer,
)

# ====================================================================================
# __all__ - Exportaciones públicas
# ====================================================================================

__all__ = [
    # Message serializers
    'UserBasicSerializer',
    'MessageRecipientSerializer',
    'InternalMessageListSerializer',
    'InternalMessageDetailSerializer',
    'InternalMessageCreateSerializer',
    'InboxMessageSerializer',
    
    # Alert serializers
    'AlertConfigurationSerializer',
    'AlertSubscriptionSerializer',
    'AlertSubscriptionCreateSerializer',
]

# ====================================================================================
# RESUMEN
# ====================================================================================
#
# Total Serializers: 9
#
# Mensajes Internos (6):
#   [SUCCESS] UserBasicSerializer - Usuario básico para nested
#   [SUCCESS] MessageRecipientSerializer - Destinatario de mensaje
#   [SUCCESS] InternalMessageListSerializer - Listado de mensajes
#   [SUCCESS] InternalMessageDetailSerializer - Detalle de mensaje
#   [SUCCESS] InternalMessageCreateSerializer - Creación de mensaje
#   [SUCCESS] InboxMessageSerializer - Mensaje en bandeja
#
# Alertas (3):
#   [SUCCESS] AlertConfigurationSerializer - Configuración de alerta
#   [SUCCESS] AlertSubscriptionSerializer - Suscripción a alerta
#   [SUCCESS] AlertSubscriptionCreateSerializer - Creación de suscripción
#
# Características:
#   [SUCCESS] SRP aplicado (2 archivos con responsabilidades únicas)
#   [SUCCESS] Validaciones robustas (recipients, conditions)
#   [SUCCESS] Service Layer (MessageService, SubscriptionService)
#   [SUCCESS] Campos enriched (sender, user, etc.)
#   [SUCCESS] Constraint CNST-024 (máx 50 destinatarios)
#   [SUCCESS] Import circular resuelto con imports locales
#   [SUCCESS] Compatibilidad mantenida
#
# ====================================================================================
