"""
FilterService - Servicio para aplicación de filtros.

Proporciona métodos para:
- Aplicar filtros a querysets (CallRecord eliminado en FASE 3)
- Validar configuraciones de filtros
- Parsear rangos de fechas

FASE 2: Implementación de services.
"""

from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django.db.models import Q


class FilterService:
    """
    Servicio para aplicar filtros a datos.
    
    Métodos principales:
    - apply_filter_to_queryset: Aplicar filter_config a queryset
    - validate_filter_config: Validar estructura de filter_config
    - parse_date_range: Parsear strings de rango de fecha
    """
    
    @staticmethod
    def apply_filter_to_queryset(queryset, filter_config):
        """
        Aplicar filter_config a queryset.
        
        Args:
            queryset: QuerySet
            filter_config: Dict con configuración de filtros
                {
                    "date_from": "2025-01-01",
                    "date_to": "2025-01-31",
                    "did": ["800123456"],
                    "call_type": "inbound",
                    "agent_id": [1, 2, 3],
                    "client_phone": "123456789"
                }
        
        Returns:
            QuerySet filtrado
        
        Raises:
            ValidationError: Si filter_config es inválido
        """
        if not filter_config:
            return queryset
        
        # Validar filter_config
        FilterService.validate_filter_config(filter_config)
        
        # Aplicar filtros de fecha
        if 'date_from' in filter_config and filter_config['date_from']:
            queryset = queryset.filter(fecha__gte=filter_config['date_from'])
        
        if 'date_to' in filter_config and filter_config['date_to']:
            queryset = queryset.filter(fecha__lte=filter_config['date_to'])
        
        # Aplicar filtro de DID (servicio_800)
        if 'did' in filter_config and filter_config['did']:
            did_list = filter_config['did']
            if isinstance(did_list, str):
                did_list = [did_list]
            queryset = queryset.filter(servicio_800__in=did_list)
        
        # Aplicar filtro de tipo de llamada
        if 'call_type' in filter_config and filter_config['call_type']:
            queryset = queryset.filter(call_type=filter_config['call_type'])
        
        # Aplicar filtro de agente
        if 'agent_id' in filter_config and filter_config['agent_id']:
            agent_ids = filter_config['agent_id']
            if isinstance(agent_ids, int):
                agent_ids = [agent_ids]
            queryset = queryset.filter(agent_id__in=agent_ids)
        
        # Aplicar filtro de cliente (teléfono)
        if 'client_phone' in filter_config and filter_config['client_phone']:
            queryset = queryset.filter(telefono=filter_config['client_phone'])
        
        # Aplicar filtro de duración mínima
        if 'min_duration' in filter_config and filter_config['min_duration']:
            queryset = queryset.filter(
                duracion_total_segundos__gte=filter_config['min_duration']
            )
        
        # Aplicar filtro de duración máxima
        if 'max_duration' in filter_config and filter_config['max_duration']:
            queryset = queryset.filter(
                duracion_total_segundos__lte=filter_config['max_duration']
            )
        
        return queryset
    
    @staticmethod
    def validate_filter_config(filter_config):
        """
        Validar estructura de filter_config.
        
        Args:
            filter_config: Dict con configuración de filtros
        
        Raises:
            ValidationError: Si filter_config es inválido
        """
        if not isinstance(filter_config, dict):
            raise ValidationError("filter_config debe ser un diccionario")
        
        # Validar date_from
        if 'date_from' in filter_config and filter_config['date_from']:
            try:
                if isinstance(filter_config['date_from'], str):
                    datetime.strptime(filter_config['date_from'], '%Y-%m-%d')
            except ValueError:
                raise ValidationError(
                    "date_from debe estar en formato YYYY-MM-DD"
                )
        
        # Validar date_to
        if 'date_to' in filter_config and filter_config['date_to']:
            try:
                if isinstance(filter_config['date_to'], str):
                    datetime.strptime(filter_config['date_to'], '%Y-%m-%d')
            except ValueError:
                raise ValidationError(
                    "date_to debe estar en formato YYYY-MM-DD"
                )
        
        # Validar que date_from <= date_to
        if ('date_from' in filter_config and filter_config['date_from'] and
            'date_to' in filter_config and filter_config['date_to']):
            
            date_from = filter_config['date_from']
            date_to = filter_config['date_to']
            
            if isinstance(date_from, str):
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            if isinstance(date_to, str):
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            
            if date_from > date_to:
                raise ValidationError("date_from debe ser menor o igual a date_to")
        
        # Validar duraciones
        if 'min_duration' in filter_config and filter_config['min_duration']:
            if not isinstance(filter_config['min_duration'], (int, float)):
                raise ValidationError("min_duration debe ser un número")
            if filter_config['min_duration'] < 0:
                raise ValidationError("min_duration debe ser mayor o igual a 0")
        
        if 'max_duration' in filter_config and filter_config['max_duration']:
            if not isinstance(filter_config['max_duration'], (int, float)):
                raise ValidationError("max_duration debe ser un número")
            if filter_config['max_duration'] < 0:
                raise ValidationError("max_duration debe ser mayor o igual a 0")
    
    @staticmethod
    def parse_date_range(range_string):
        """
        Parsear string de rango de fecha a tupla (date_from, date_to).
        
        Args:
            range_string: String con rango de fecha
                Opciones:
                - "today": Hoy
                - "yesterday": Ayer
                - "last_7_days": Últimos 7 días
                - "last_30_days": Últimos 30 días
                - "this_week": Esta semana
                - "this_month": Este mes
                - "this_quarter": Este trimestre
                - "this_year": Este año
        
        Returns:
            Tuple (date_from, date_to)
        
        Raises:
            ValueError: Si range_string no es reconocido
        """
        today = datetime.now().date()
        
        if range_string == 'today':
            return (today, today)
        
        elif range_string == 'yesterday':
            yesterday = today - timedelta(days=1)
            return (yesterday, yesterday)
        
        elif range_string == 'last_7_days':
            date_from = today - timedelta(days=7)
            return (date_from, today)
        
        elif range_string == 'last_30_days':
            date_from = today - timedelta(days=30)
            return (date_from, today)
        
        elif range_string == 'this_week':
            # Lunes de esta semana
            days_since_monday = today.weekday()
            date_from = today - timedelta(days=days_since_monday)
            return (date_from, today)
        
        elif range_string == 'this_month':
            date_from = today.replace(day=1)
            return (date_from, today)
        
        elif range_string == 'this_quarter':
            # Determinar primer mes del trimestre
            current_month = today.month
            first_month_of_quarter = ((current_month - 1) // 3) * 3 + 1
            date_from = today.replace(month=first_month_of_quarter, day=1)
            return (date_from, today)
        
        elif range_string == 'this_year':
            date_from = today.replace(month=1, day=1)
            return (date_from, today)
        
        else:
            raise ValueError(
                f"Rango de fecha no reconocido: {range_string}. "
                "Opciones: today, yesterday, last_7_days, last_30_days, "
                "this_week, this_month, this_quarter, this_year"
            )
