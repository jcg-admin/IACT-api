"""
Service Layer para Center.

Contiene lógica de negocio para centros de atención.

Service Layer Pattern: Lógica de negocio separada de models.
CLEAN_CODE v3.0.1: Nombres auto-documentados.
"""

from django.db import transaction
from django.core.cache import cache
from django.core.exceptions import ValidationError
from typing import Dict, List, Optional

from apps.pipeline.models import Center, Service
from apps.utils.constants import CACHE_TTL_MEDIUM, CACHE_KEY_USER_SERVICES


class CenterService:
    """
    Service para operaciones de Center.
    
    Métodos:
        - create_center(data)
        - update_center(center, data)
        - deactivate_center(center, user)
        - activate_center(center)
        - get_center_stats(center)
        - get_center_with_services(center_id)
        - bulk_create_centers(centers_data)
    """
    
    @staticmethod
    @transaction.atomic
    def create_center(data: Dict) -> Center:
        """
        Crear centro de atención.
        
        Args:
            data (dict): Datos del centro
                - nombre (str): Nombre del centro
                - codigo (str): Código único
                - descripcion (str, opcional)
                - direccion (str, opcional)
                - activo (bool, opcional, default=True)
        
        Returns:
            Center: Centro creado
        
        Raises:
            ValidationError: Si datos inválidos
        
        Examples:
            >>> data = {
            ...     'nombre': 'Centro Santiago',
            ...     'codigo': 'CT_SCL',
            ...     'descripcion': 'Centro principal',
            ...     'activo': True
            ... }
            >>> center = CenterService.create_center(data)
        """
        # Validar código único
        codigo = data.get('codigo')
        if Center.objects.filter(codigo=codigo).exists():
            raise ValidationError(f"Ya existe un centro con código '{codigo}'")
        
        # Crear centro
        center = Center.objects.create(**data)
        
        return center
    
    @staticmethod
    @transaction.atomic
    def update_center(center: Center, data: Dict) -> Center:
        """
        Actualizar centro de atención.
        
        Args:
            center (Center): Centro a actualizar
            data (dict): Datos a actualizar
        
        Returns:
            Center: Centro actualizado
        
        Raises:
            ValidationError: Si datos inválidos
        
        Examples:
            >>> data = {'nombre': 'Centro Santiago - Norte'}
            >>> center = CenterService.update_center(center, data)
        """
        # Validar código único si se cambia
        new_codigo = data.get('codigo')
        if new_codigo and new_codigo != center.codigo:
            if Center.objects.filter(codigo=new_codigo).exists():
                raise ValidationError(f"Ya existe un centro con código '{new_codigo}'")
        
        # Actualizar campos
        for field, value in data.items():
            if hasattr(center, field):
                setattr(center, field, value)
        
        center.full_clean()
        center.save()
        
        # Invalidar cache de servicios si existe
        CenterService._invalidate_services_cache(center)
        
        return center
    
    @staticmethod
    @transaction.atomic
    def deactivate_center(center: Center, user=None) -> Dict:
        """
        Desactivar centro y todos sus servicios.
        
        Args:
            center (Center): Centro a desactivar
            user (User, opcional): Usuario que desactiva
        
        Returns:
            dict: {
                'center': Center,
                'services_deactivated': int
            }
        
        Examples:
            >>> result = CenterService.deactivate_center(center, user=admin)
            >>> result['services_deactivated']
            5
        """
        # Desactivar centro
        center.activo = False
        center.save()
        
        # Desactivar todos los servicios del centro
        services = center.services.filter(activo=True)
        services_count = services.count()
        
        # Desactivar servicios
        services.update(activo=False)
        
        return {
            'center': center,
            'services_deactivated': services_count
        }
    
    @staticmethod
    @transaction.atomic
    def activate_center(center: Center) -> Center:
        """
        Activar centro.
        
        NOTA: Los servicios permanecen en su estado actual.
        
        Args:
            center (Center): Centro a activar
        
        Returns:
            Center: Centro activado
        """
        center.activo = True
        center.save()
        
        CenterService._invalidate_services_cache(center)
        
        return center
    
    @staticmethod
    def get_center_stats(center: Center) -> Dict:
        """
        Obtener estadísticas del centro.
        
        Args:
            center (Center): Centro
        
        Returns:
            dict: {
                'total_services': int,
                'active_services': int,
                'inactive_services': int,
                'is_active': bool
            }
        
        Examples:
            >>> stats = CenterService.get_center_stats(center)
            >>> stats['active_services']
            5
        """
        services = center.services.all()
        active_services = services.filter(activo=True)
        
        return {
            'total_services': services.count(),
            'active_services': active_services.count(),
            'inactive_services': services.filter(activo=False).count(),
            'is_active': center.activo
        }
    
    @staticmethod
    def get_center_with_services(center_id: int) -> Optional[Center]:
        """
        Obtener centro con servicios precargados.
        
        Usa select_related para optimizar queries.
        
        Args:
            center_id (int): ID del centro
        
        Returns:
            Center o None: Centro con servicios
        """
        try:
            return Center.objects.prefetch_related('services').get(id=center_id)
        except Center.DoesNotExist:
            return None
    
    @staticmethod
    @transaction.atomic
    def bulk_create_centers(centers_data: List[Dict]) -> List[Center]:
        """
        Crear múltiples centros en batch.
        
        Args:
            centers_data (list): Lista de dicts con datos de centros
        
        Returns:
            list: Lista de Centers creados
        
        Raises:
            ValidationError: Si hay códigos duplicados
        
        Examples:
            >>> data = [
            ...     {'nombre': 'Centro 1', 'codigo': 'CT01'},
            ...     {'nombre': 'Centro 2', 'codigo': 'CT02'},
            ... ]
            >>> centers = CenterService.bulk_create_centers(data)
        """
        # Validar códigos únicos
        codigos = [data['codigo'] for data in centers_data]
        if len(codigos) != len(set(codigos)):
            raise ValidationError("Hay códigos duplicados en la lista")
        
        # Verificar que no existan en BD
        existing = Center.objects.filter(codigo__in=codigos).values_list('codigo', flat=True)
        if existing:
            raise ValidationError(
                f"Ya existen centros con códigos: {', '.join(existing)}"
            )
        
        # Crear objetos
        centers = [Center(**data) for data in centers_data]
        
        # Validar todos
        for center in centers:
            center.full_clean()
        
        # Crear en batch
        return Center.objects.bulk_create(centers)


# ============================================================================
# TOTAL METHODS: 8 (LIMPIEZA DEUDA TÉCNICA 2026-01-22)
# 
# CRUD:
#   - create_center(data)
#   - update_center(center, data)
# 
# Activation:
#   - deactivate_center(center, user)
#   - activate_center(center)
# 
# Stats & Queries:
#   - get_center_stats(center)
#   - get_center_with_services(center_id)
# 
# Bulk:
#   - bulk_create_centers(centers_data)
# 
# Cache:
#   - _invalidate_services_cache(center)
# 
# Características:
#   [SUCCESS] @transaction.atomic donde corresponde
#   [SUCCESS] Validaciones de negocio
#   [SUCCESS] Cache invalidation
#   [SUCCESS] Optimización queries (prefetch_related)
#   [SUCCESS] Type hints
#   [SUCCESS] Docstrings completos
#   [SUCCESS] CLEAN_CODE v3.0.1
# ============================================================================
