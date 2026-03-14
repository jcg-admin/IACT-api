"""
Services Layer para apps/core/.

CLEAN_CODE v3.0.1: Solo infraestructura base.
SOLID SRP: apps/core/ NO tiene lógica de negocio.

Services de negocio están en apps apropiadas:
- CenterService, ServiceService, CallRecordService, ETLService -> apps/pipeline/services/
"""

from .base_service import BaseService

__all__ = [
    'BaseService',
]
