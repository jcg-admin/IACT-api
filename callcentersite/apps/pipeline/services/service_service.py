"""
Service Layer para Service (Servicio 800).

Contiene lógica de negocio para servicios 800.

Service Layer Pattern: Lógica de negocio separada de models.
CLEAN_CODE v3.0.1: Nombres auto-documentados.
"""

from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from typing import Dict, List, Optional, Tuple

from apps.pipeline.models import Service, Center


class ServiceService:
    """
    Service para operaciones de Service (servicios 800).
    
    Métodos:
        - create_service(data)
        - update_service(service, data)
        - deactivate_service(service)
        - activate_service(service)
        - transfer_service_to_center(service, new_center)
    
    LIMPIEZA DEUDA TÉCNICA (2026-01-22):
    Métodos ELIMINADOS (UserServiceAccess deprecated):
        [ERROR] grant_access
        [ERROR] revoke_access
        [ERROR] bulk_grant_access
        [ERROR] get_service_users
        [ERROR] get_user_services
        [ERROR] _invalidate_user_caches
    
    Control de acceso ahora: RBAC puro (Function/UserFunctionAssignment)
    Usuario con permiso -> ve TODOS los servicios
    """
    
    @staticmethod
    @transaction.atomic
    def create_service(data: Dict) -> Service:
        """
        Crear servicio 800.
        
        Args:
            data (dict): Datos del servicio
                - numero_800 (str): Número 800
                - nombre (str): Nombre del servicio
                - center_id (int): ID del centro
                - descripcion (str, opcional)
                - activo (bool, opcional, default=True)
        
        Returns:
            Service: Servicio creado
        
        Raises:
            ValidationError: Si datos inválidos
        
        Examples:
            >>> data = {
            ...     'numero_800': '800-123-4567',
            ...     'nombre': 'Soporte Técnico',
            ...     'center_id': 1,
            ...     'activo': True
            ... }
            >>> service = ServiceService.create_service(data)
        """
        # Validar número único
        numero_800 = data.get('numero_800')
        if Service.objects.filter(numero_800=numero_800).exists():
            raise ValidationError(f"Ya existe un servicio con número '{numero_800}'")
        
        # Validar centro activo
        center_id = data.pop('center_id', None)
        if not center_id:
            raise ValidationError("Centro es requerido")
        
        try:
            center = Center.objects.get(id=center_id)
        except Center.DoesNotExist:
            raise ValidationError(f"Centro con ID {center_id} no existe")
        
        if not center.activo:
            raise ValidationError(f"Centro '{center.nombre}' está inactivo")
        
        # Crear servicio
        service = Service.objects.create(center=center, **data)
        
        return service
    
    @staticmethod
    @transaction.atomic
    def update_service(service: Service, data: Dict) -> Service:
        """
        Actualizar servicio 800.
        
        Args:
            service (Service): Servicio a actualizar
            data (dict): Datos a actualizar
        
        Returns:
            Service: Servicio actualizado
        
        Raises:
            ValidationError: Si datos inválidos
        
        Examples:
            >>> data = {'nombre': 'Soporte Técnico 24/7'}
            >>> service = ServiceService.update_service(service, data)
        """
        # Validar número único si se cambia
        new_numero = data.get('numero_800')
        if new_numero and new_numero != service.numero_800:
            if Service.objects.filter(numero_800=new_numero).exists():
                raise ValidationError(f"Ya existe servicio con número '{new_numero}'")
        
        # Validar centro si se cambia
        new_center_id = data.get('center_id')
        if new_center_id:
            try:
                new_center = Center.objects.get(id=new_center_id)
                if not new_center.activo:
                    raise ValidationError(f"Centro '{new_center.nombre}' está inactivo")
                data['center'] = new_center
                del data['center_id']
            except Center.DoesNotExist:
                raise ValidationError(f"Centro con ID {new_center_id} no existe")
        
        # Actualizar campos
        for field, value in data.items():
            if hasattr(service, field):
                setattr(service, field, value)
        
        service.full_clean()
        service.save()
        
        return service
    
    @staticmethod
    @transaction.atomic
    def deactivate_service(service: Service) -> Service:
        """
        Desactivar servicio.
        
        Args:
            service (Service): Servicio a desactivar
        
        Returns:
            Service: Servicio desactivado
        
        Examples:
            >>> service = ServiceService.deactivate_service(service)
            >>> service.activo
            False
        """
        service.activo = False
        service.save()
        
        return service
    
    @staticmethod
    @transaction.atomic
    def activate_service(service: Service) -> Service:
        """
        Activar servicio.
        
        Valida que el centro esté activo.
        
        Args:
            service (Service): Servicio a activar
        
        Returns:
            Service: Servicio activado
        
        Raises:
            ValidationError: Si centro inactivo
        
        Examples:
            >>> service = ServiceService.activate_service(service)
            >>> service.activo
            True
        """
        if not service.center.activo:
            raise ValidationError(
                f"No se puede activar servicio: centro '{service.center.nombre}' está inactivo"
            )
        
        service.activo = True
        service.save()
        
        return service
    
    @staticmethod
    @transaction.atomic
    def transfer_service_to_center(service: Service, new_center: Center) -> Service:
        """
        Transferir servicio a otro centro.
        
        Args:
            service (Service): Servicio a transferir
            new_center (Center): Centro destino
        
        Returns:
            Service: Servicio transferido
        
        Raises:
            ValidationError: Si centro inactivo
        
        Examples:
            >>> service = ServiceService.transfer_service_to_center(service, new_center)
            >>> service.center == new_center
            True
        """
        if not new_center.activo:
            raise ValidationError(
                f"No se puede transferir a centro inactivo: '{new_center.nombre}'"
            )
        
        old_center = service.center
        service.center = new_center
        service.save()
        
        return service


# ============================================================================
# TOTAL METHODS: 5 (LIMPIEZA DEUDA TÉCNICA 2026-01-22)
# 
# CRUD:
#   - create_service(data)
#   - update_service(service, data)
# 
# Activation:
#   - deactivate_service(service)
#   - activate_service(service)
# 
# Transfer:
#   - transfer_service_to_center(service, new_center)
# 
# ELIMINADO (UserServiceAccess deprecated):
#   [ERROR] grant_access - Control ahora por RBAC
#   [ERROR] revoke_access - Control ahora por RBAC
#   [ERROR] bulk_grant_access - Control ahora por RBAC
#   [ERROR] get_service_users - Sin segmentación por servicio
#   [ERROR] get_user_services - Sin segmentación por servicio
#   [ERROR] _invalidate_user_caches - Sin cache de accesos
# 
# Características:
#   [SUCCESS] @transaction.atomic donde corresponde
#   [SUCCESS] Validaciones de negocio complejas
#   [SUCCESS] Type hints
#   [SUCCESS] Docstrings completos
#   [SUCCESS] CLEAN_CODE v3.0.1
#   [SUCCESS] Sin dependencias deprecated
# ============================================================================
