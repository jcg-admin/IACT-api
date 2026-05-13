"""
WidgetService - Servicio para generación de datos de widgets.

Proporciona métodos para:
- Obtener datos de widgets según su tipo
- Calcular datos para 8 tipos de widgets
- Refrescar cache de widgets

Tipos de widgets soportados:
- CALLS_CHART: Gráfico de llamadas
- TRANSFERS_CHART: Gráfico de transferencias
- ABANDONMENTS_CHART: Gráfico de abandonos
- TOP_CLIENTS: Top clientes
- METRICS_SUMMARY: Resumen de métricas
- HOURLY_STATS: Estadísticas por hora
- AGENT_PERFORMANCE: Rendimiento de agentes
- SLA_MONITOR: Monitor de SLA

FASE 2: Implementación de services.
"""

from datetime import datetime, timedelta
from django.core.cache import cache

from apps.dashboard.models import WidgetConfig
from apps.dashboard.services.filter_service import FilterService

# CallRecord eliminado en FASE 3 (UC_OPR/UC_SUP/UC_CLI fuera de scope analítico).
# Los widgets de llamadas deben reimplementarse usando MariaDB via ivr_services.py.


class WidgetService:
    """
    Servicio para generación de datos de widgets.
    
    Métodos principales:
    - get_widget_data: Obtener datos del widget
    - calculate_*_data: Calcular datos específicos por tipo
    - refresh_widget_cache: Refrescar cache
    """
    
    # Mapeo de tipos de widget a métodos de cálculo
    WIDGET_CALCULATORS = {
        'CALLS_CHART': 'calculate_calls_chart_data',
        'TRANSFERS_CHART': 'calculate_transfers_chart_data',
        'ABANDONMENTS_CHART': 'calculate_abandonments_chart_data',
        'TOP_CLIENTS': 'calculate_top_clients_data',
        'METRICS_SUMMARY': 'calculate_metrics_summary_data',
        'HOURLY_STATS': 'calculate_hourly_stats_data',
        'AGENT_PERFORMANCE': 'calculate_agent_performance_data',
        'SLA_MONITOR': 'calculate_sla_monitor_data',
    }
    
    @staticmethod
    def get_widget_data(widget_id, date_range=None, use_cache=True):
        """
        Obtener datos del widget según su tipo.
        
        Args:
            widget_id: ID del widget
            date_range: Tupla (date_from, date_to) opcional
            use_cache: Si usar cache (default: True)
        
        Returns:
            Dict con datos del widget
        
        Raises:
            WidgetConfig.DoesNotExist: Si widget no existe
            ValueError: Si widget_type no es reconocido
        """
        widget = WidgetConfig.objects.select_related('dashboard').get(id=widget_id)
        
        # Generar cache key
        cache_key = f'widget_data_{widget_id}'
        if date_range:
            cache_key += f'_{date_range[0]}_{date_range[1]}'
        
        # Intentar obtener de cache
        if use_cache:
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                return cached_data
        
        # Determinar método de cálculo
        calculator_method_name = WidgetService.WIDGET_CALCULATORS.get(
            widget.widget_type
        )
        
        if not calculator_method_name:
            raise ValueError(
                f"Tipo de widget no reconocido: {widget.widget_type}"
            )
        
        # Obtener método de cálculo
        calculator_method = getattr(WidgetService, calculator_method_name)
        
        # Parsear date_range si viene de config_data
        if not date_range and 'time_range' in widget.config_data:
            try:
                date_range = FilterService.parse_date_range(
                    widget.config_data['time_range']
                )
            except ValueError:
                # Si time_range no es reconocido, usar last_7_days
                date_range = FilterService.parse_date_range('last_7_days')
        
        # Calcular datos
        data = calculator_method(widget.config_data, date_range)
        
        # Guardar en cache
        cache_timeout = widget.refresh_interval_seconds
        cache.set(cache_key, data, timeout=cache_timeout)
        
        return data
    
    @staticmethod
    def calculate_calls_chart_data(config_data, date_range=None):
        """
        Calcular datos para gráfico de llamadas.
        
        Args:
            config_data: Configuración del widget
            date_range: Tupla (date_from, date_to)
        
        Returns:
            Dict con datos del gráfico:
                {
                    'labels': ['2025-01-01', '2025-01-02', ...],
                    'datasets': [
                        {'label': 'Total', 'data': [100, 120, ...]},
                        {'label': 'Contestadas', 'data': [90, 110, ...]},
                        {'label': 'Abandonadas', 'data': [10, 10, ...]}
                    ]
                }
        """
        # CallRecord eliminado en FASE 3 — reimplementar con MariaDB (ivr_services.py)
        return {}

    @staticmethod
    def calculate_transfers_chart_data(config_data, date_range=None):
        """
        Calcular datos para gráfico de transferencias.
        
        Args:
            config_data: Configuración del widget
            date_range: Tupla (date_from, date_to)
        
        Returns:
            Dict con datos del gráfico
        """
        # CallRecord eliminado en FASE 3 — reimplementar con MariaDB (ivr_services.py)
        return {}

    @staticmethod
    def calculate_abandonments_chart_data(config_data, date_range=None):
        """
        Calcular datos para gráfico de abandonos.
        
        Args:
            config_data: Configuración del widget
            date_range: Tupla (date_from, date_to)
        
        Returns:
            Dict con datos del gráfico y tasa de abandono
        """
        # CallRecord eliminado en FASE 3 — reimplementar con MariaDB (ivr_services.py)
        return {}

    @staticmethod
    def calculate_top_clients_data(config_data, date_range=None):
        """
        Calcular datos para top clientes.
        
        Args:
            config_data: Configuración del widget
            date_range: Tupla (date_from, date_to)
        
        Returns:
            Dict con top clientes ordenados por total de llamadas
        """
        # CallRecord eliminado en FASE 3 — reimplementar con MariaDB (ivr_services.py)
        return {}

    @staticmethod
    def calculate_metrics_summary_data(config_data, date_range=None):
        """
        Calcular datos para resumen de métricas (KPIs).
        
        Args:
            config_data: Configuración del widget
            date_range: Tupla (date_from, date_to)
        
        Returns:
            Dict con métricas resumen
        """
        # CallRecord eliminado en FASE 3 — reimplementar con MariaDB (ivr_services.py)
        return {}

    @staticmethod
    def calculate_hourly_stats_data(config_data, date_range=None):
        """
        Calcular datos para estadísticas por hora.
        
        Args:
            config_data: Configuración del widget
            date_range: Tupla (date_from, date_to)
        
        Returns:
            Dict con estadísticas por hora del día (0-23)
        """
        # CallRecord eliminado en FASE 3 — reimplementar con MariaDB (ivr_services.py)
        return {}

    @staticmethod
    def calculate_agent_performance_data(config_data, date_range=None):
        """
        Calcular datos para rendimiento de agentes.
        
        Args:
            config_data: Configuración del widget
            date_range: Tupla (date_from, date_to)
        
        Returns:
            Dict con rendimiento de agentes ordenado
        """
        # CallRecord eliminado en FASE 3 — reimplementar con MariaDB (ivr_services.py)
        return {}

    @staticmethod
    def calculate_sla_monitor_data(config_data, date_range=None):
        """
        Calcular datos para monitor de SLA.
        
        Args:
            config_data: Configuración del widget
            date_range: Tupla (date_from, date_to)
        
        Returns:
            Dict con métricas de SLA
        """
        # CallRecord eliminado en FASE 3 — reimplementar con MariaDB (ivr_services.py)
        return {}

    @staticmethod
    def refresh_widget_cache(widget_id):
        """
        Refrescar cache de widget.
        
        Elimina todas las entradas de cache del widget
        para forzar recálculo en próxima consulta.
        
        Args:
            widget_id: ID del widget
        """
        # Eliminar todas las variantes de cache del widget
        # Nota: En producción, podría usarse un patrón más sofisticado
        cache_pattern = f'widget_data_{widget_id}*'
        
        # Django cache no soporta delete_pattern nativamente
        # Por simplicidad, eliminamos la entrada base
        cache.delete(f'widget_data_{widget_id}')
        
        # También podríamos eliminar todas las variantes conocidas
        # Esto requeriría tracking de todas las date_range usadas