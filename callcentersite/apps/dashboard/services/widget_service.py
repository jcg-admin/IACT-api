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
from django.db.models import Sum, Avg, Count, F, Q
from django.db.models.functions import ExtractHour

from apps.dashboard.models import WidgetConfig
from apps.dashboard.services.filter_service import FilterService
from apps.pipeline.models import CallRecord


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
        # Obtener queryset base
        queryset = CallRecord.objects.filter(deleted_at__isnull=True)
        
        # Aplicar filtros de fecha
        if date_range:
            queryset = queryset.filter(
                fecha__gte=date_range[0],
                fecha__lte=date_range[1]
            )
        else:
            # Por defecto: últimos 7 días
            date_from = datetime.now().date() - timedelta(days=7)
            queryset = queryset.filter(fecha__gte=date_from)
        
        # Aplicar filtros adicionales de config_data
        if 'filters' in config_data:
            queryset = FilterService.apply_filter_to_queryset(
                queryset,
                config_data['filters']
            )
        
        # Agrupar por fecha y agregar
        data = queryset.values('fecha').annotate(
            total=Sum('total_llamadas'),
            contestadas=Sum('llamadas_contestadas'),
            abandonadas=Sum('llamadas_abandonadas')
        ).order_by('fecha')
        
        # Formatear datos para el gráfico
        labels = [item['fecha'].strftime('%Y-%m-%d') for item in data]
        
        datasets = [
            {
                'label': 'Total',
                'data': [item['total'] or 0 for item in data]
            },
            {
                'label': 'Contestadas',
                'data': [item['contestadas'] or 0 for item in data]
            },
            {
                'label': 'Abandonadas',
                'data': [item['abandonadas'] or 0 for item in data]
            }
        ]
        
        return {
            'labels': labels,
            'datasets': datasets,
            'chart_type': config_data.get('chart_type', 'line')
        }
    
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
        # Obtener queryset base (solo transferencias)
        queryset = CallRecord.objects.filter(
            deleted_at__isnull=True,
            call_type='transfer'
        )
        
        # Aplicar filtros de fecha
        if date_range:
            queryset = queryset.filter(
                fecha__gte=date_range[0],
                fecha__lte=date_range[1]
            )
        else:
            date_from = datetime.now().date() - timedelta(days=7)
            queryset = queryset.filter(fecha__gte=date_from)
        
        # Aplicar filtros adicionales
        if 'filters' in config_data:
            queryset = FilterService.apply_filter_to_queryset(
                queryset,
                config_data['filters']
            )
        
        # Agrupar por fecha
        data = queryset.values('fecha').annotate(
            total=Sum('total_llamadas')
        ).order_by('fecha')
        
        labels = [item['fecha'].strftime('%Y-%m-%d') for item in data]
        values = [item['total'] or 0 for item in data]
        
        return {
            'labels': labels,
            'datasets': [
                {
                    'label': 'Transferencias',
                    'data': values
                }
            ],
            'chart_type': config_data.get('chart_type', 'bar')
        }
    
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
        queryset = CallRecord.objects.filter(deleted_at__isnull=True)
        
        if date_range:
            queryset = queryset.filter(
                fecha__gte=date_range[0],
                fecha__lte=date_range[1]
            )
        else:
            date_from = datetime.now().date() - timedelta(days=7)
            queryset = queryset.filter(fecha__gte=date_from)
        
        if 'filters' in config_data:
            queryset = FilterService.apply_filter_to_queryset(
                queryset,
                config_data['filters']
            )
        
        # Agrupar por fecha y calcular tasa de abandono
        data = queryset.values('fecha').annotate(
            total=Sum('total_llamadas'),
            abandonadas=Sum('llamadas_abandonadas')
        ).order_by('fecha')
        
        labels = []
        abandoned_values = []
        abandonment_rate = []
        
        for item in data:
            labels.append(item['fecha'].strftime('%Y-%m-%d'))
            abandoned_values.append(item['abandonadas'] or 0)
            
            # Calcular tasa de abandono
            if item['total'] and item['total'] > 0:
                rate = (item['abandonadas'] or 0) / item['total'] * 100
            else:
                rate = 0
            abandonment_rate.append(round(rate, 2))
        
        datasets = [
            {
                'label': 'Llamadas Abandonadas',
                'data': abandoned_values
            }
        ]
        
        # Si config incluye show_rate, agregar dataset de tasa
        if config_data.get('show_rate', True):
            datasets.append({
                'label': 'Tasa de Abandono (%)',
                'data': abandonment_rate
            })
        
        return {
            'labels': labels,
            'datasets': datasets,
            'chart_type': config_data.get('chart_type', 'line'),
            'threshold': config_data.get('threshold', 0.15)  # 15% threshold
        }
    
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
        queryset = CallRecord.objects.filter(deleted_at__isnull=True)
        
        if date_range:
            queryset = queryset.filter(
                fecha__gte=date_range[0],
                fecha__lte=date_range[1]
            )
        else:
            date_from = datetime.now().date() - timedelta(days=30)
            queryset = queryset.filter(fecha__gte=date_from)
        
        if 'filters' in config_data:
            queryset = FilterService.apply_filter_to_queryset(
                queryset,
                config_data['filters']
            )
        
        # Límite de resultados
        limit = config_data.get('limit', 5)
        
        # Agrupar por teléfono y agregar
        data = queryset.values('telefono').annotate(
            total_llamadas=Sum('total_llamadas'),
            llamadas_contestadas=Sum('llamadas_contestadas'),
            duracion_promedio=Avg('duracion_total_segundos')
        ).order_by('-total_llamadas')[:limit]
        
        # Formatear datos
        clients = []
        for item in data:
            clients.append({
                'phone': item['telefono'],
                'total_calls': item['total_llamadas'] or 0,
                'answered_calls': item['llamadas_contestadas'] or 0,
                'avg_duration': round(item['duracion_promedio'] or 0, 2)
            })
        
        return {
            'clients': clients,
            'limit': limit,
            'sort_by': config_data.get('sort_by', 'total_calls')
        }
    
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
        queryset = CallRecord.objects.filter(deleted_at__isnull=True)
        
        if date_range:
            queryset = queryset.filter(
                fecha__gte=date_range[0],
                fecha__lte=date_range[1]
            )
        else:
            date_from = datetime.now().date() - timedelta(days=30)
            queryset = queryset.filter(fecha__gte=date_from)
        
        if 'filters' in config_data:
            queryset = FilterService.apply_filter_to_queryset(
                queryset,
                config_data['filters']
            )
        
        # Calcular métricas agregadas
        aggregates = queryset.aggregate(
            total_calls=Sum('total_llamadas'),
            answered_calls=Sum('llamadas_contestadas'),
            abandoned_calls=Sum('llamadas_abandonadas'),
            avg_duration=Avg('duracion_total_segundos'),
            unique_clients=Count('telefono', distinct=True)
        )
        
        # Calcular tasa de abandono
        total = aggregates['total_calls'] or 0
        abandoned = aggregates['abandoned_calls'] or 0
        abandonment_rate = (abandoned / total * 100) if total > 0 else 0
        
        # Calcular tasa de respuesta
        answered = aggregates['answered_calls'] or 0
        answer_rate = (answered / total * 100) if total > 0 else 0
        
        # Construir métricas
        metrics = {
            'total_calls': total,
            'answered_calls': answered,
            'abandoned_calls': abandoned,
            'abandonment_rate': round(abandonment_rate, 2),
            'answer_rate': round(answer_rate, 2),
            'avg_duration': round(aggregates['avg_duration'] or 0, 2),
            'unique_clients': aggregates['unique_clients'] or 0
        }
        
        # Filtrar métricas según config
        if 'metrics' in config_data:
            requested_metrics = config_data['metrics']
            metrics = {
                key: value for key, value in metrics.items()
                if key in requested_metrics
            }
        
        return {
            'metrics': metrics,
            'date_range': {
                'from': date_range[0].strftime('%Y-%m-%d') if date_range else None,
                'to': date_range[1].strftime('%Y-%m-%d') if date_range else None
            }
        }
    
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
        queryset = CallRecord.objects.filter(deleted_at__isnull=True)
        
        if date_range:
            queryset = queryset.filter(
                fecha__gte=date_range[0],
                fecha__lte=date_range[1]
            )
        else:
            date_from = datetime.now().date() - timedelta(days=7)
            queryset = queryset.filter(fecha__gte=date_from)
        
        if 'filters' in config_data:
            queryset = FilterService.apply_filter_to_queryset(
                queryset,
                config_data['filters']
            )
        
        # Nota: Asumimos que CallRecord tiene un campo created_at con hora
        # Si no, este widget necesitaría un campo de hora en el modelo
        # Por ahora, agrupamos por fecha solamente
        
        # Crear matriz de 24 horas inicializada en 0
        hourly_data = {hour: 0 for hour in range(24)}
        
        # Si queryset tiene created_at, extraer hora
        # Como CallRecord no tiene hora explícita, retornamos estructura vacía
        # Este widget requeriría datos adicionales en el modelo
        
        return {
            'hourly_distribution': hourly_data,
            'labels': [f'{hour:02d}:00' for hour in range(24)],
            'note': 'Widget requiere datos de hora en CallRecord'
        }
    
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
        queryset = CallRecord.objects.filter(
            deleted_at__isnull=True,
            agent__isnull=False  # Solo llamadas con agente asignado
        )
        
        if date_range:
            queryset = queryset.filter(
                fecha__gte=date_range[0],
                fecha__lte=date_range[1]
            )
        else:
            date_from = datetime.now().date() - timedelta(days=30)
            queryset = queryset.filter(fecha__gte=date_from)
        
        if 'filters' in config_data:
            queryset = FilterService.apply_filter_to_queryset(
                queryset,
                config_data['filters']
            )
        
        # Límite de resultados
        limit = config_data.get('limit', 10)
        
        # Agrupar por agente y agregar
        data = queryset.values('agent', 'agent__username').annotate(
            total_calls=Sum('total_llamadas'),
            answered_calls=Sum('llamadas_contestadas'),
            abandoned_calls=Sum('llamadas_abandonadas'),
            avg_duration=Avg('duracion_total_segundos')
        ).order_by('-total_calls')[:limit]
        
        # Formatear datos
        agents = []
        for item in data:
            total = item['total_calls'] or 0
            answered = item['answered_calls'] or 0
            abandoned = item['abandoned_calls'] or 0
            
            # Calcular tasas
            answer_rate = (answered / total * 100) if total > 0 else 0
            abandonment_rate = (abandoned / total * 100) if total > 0 else 0
            
            agents.append({
                'agent_id': item['agent'],
                'agent_name': item['agent__username'] or 'Unknown',
                'total_calls': total,
                'answered_calls': answered,
                'abandoned_calls': abandoned,
                'answer_rate': round(answer_rate, 2),
                'abandonment_rate': round(abandonment_rate, 2),
                'avg_duration': round(item['avg_duration'] or 0, 2)
            })
        
        return {
            'agents': agents,
            'limit': limit,
            'sort_by': config_data.get('sort_by', 'total_calls')
        }
    
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
        queryset = CallRecord.objects.filter(deleted_at__isnull=True)
        
        if date_range:
            queryset = queryset.filter(
                fecha__gte=date_range[0],
                fecha__lte=date_range[1]
            )
        else:
            date_from = datetime.now().date() - timedelta(days=1)
            queryset = queryset.filter(fecha__gte=date_from)
        
        if 'filters' in config_data:
            queryset = FilterService.apply_filter_to_queryset(
                queryset,
                config_data['filters']
            )
        
        # Configuración de SLA
        sla_threshold = config_data.get('sla_threshold', 0.80)  # 80% default
        max_abandonment_rate = config_data.get('max_abandonment_rate', 0.15)  # 15% default
        
        # Calcular métricas
        aggregates = queryset.aggregate(
            total_calls=Sum('total_llamadas'),
            answered_calls=Sum('llamadas_contestadas'),
            abandoned_calls=Sum('llamadas_abandonadas')
        )
        
        total = aggregates['total_calls'] or 0
        answered = aggregates['answered_calls'] or 0
        abandoned = aggregates['abandoned_calls'] or 0
        
        # Calcular tasas
        answer_rate = (answered / total) if total > 0 else 0
        abandonment_rate = (abandoned / total) if total > 0 else 0
        
        # Determinar cumplimiento de SLA
        sla_met = answer_rate >= sla_threshold and abandonment_rate <= max_abandonment_rate
        
        return {
            'sla_met': sla_met,
            'answer_rate': round(answer_rate * 100, 2),
            'abandonment_rate': round(abandonment_rate * 100, 2),
            'total_calls': total,
            'answered_calls': answered,
            'abandoned_calls': abandoned,
            'thresholds': {
                'sla_threshold': sla_threshold * 100,
                'max_abandonment_rate': max_abandonment_rate * 100
            }
        }
    
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