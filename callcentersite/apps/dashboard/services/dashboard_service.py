"""
DashboardService - Servicio para gestión de dashboards.

Proporciona métodos para:
- Crear dashboard por defecto para nuevos usuarios
- Clonar dashboards existentes
- Marcar dashboard como default
- Exportar/importar configuraciones
- Eliminar dashboards (soft delete)

FASE 2: Implementación de services.
"""

import json
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction

from apps.dashboard.models import (
    DashboardConfig,
    WidgetConfig,
    UserDashboardPreference
)


class DashboardService:
    """
    Servicio para gestión de dashboards.
    
    Métodos principales:
    - create_default_dashboard: Crear dashboard por defecto
    - clone_dashboard: Clonar dashboard existente
    - set_as_default: Marcar dashboard como default
    - export_config: Exportar configuración a JSON
    - import_config: Importar configuración desde JSON
    - delete_dashboard: Eliminar dashboard (soft delete)
    """
    
    @staticmethod
    @transaction.atomic
    def create_default_dashboard(user):
        """
        Crear dashboard por defecto para un usuario.
        
        Crea:
        - DashboardConfig con is_default=True
        - 3 widgets por defecto (METRICS_SUMMARY, CALLS_CHART, TRANSFERS_CHART)
        - UserDashboardPreference vinculada
        
        Args:
            user: Usuario para quien crear el dashboard
        
        Returns:
            DashboardConfig creado
        """
        # Crear dashboard
        dashboard = DashboardConfig.objects.create(
            user=user,
            config_name='Mi Dashboard',
            description='Dashboard por defecto',
            layout_config={
                'columns': 12,
                'rowHeight': 100
            },
            is_default=True,
            is_public=False
        )
        
        # Crear 3 widgets por defecto
        
        # 1. Resumen de métricas (ancho completo)
        WidgetConfig.objects.create(
            dashboard=dashboard,
            widget_type='METRICS_SUMMARY',
            widget_name='Resumen de Métricas',
            position_x=0,
            position_y=0,
            width=12,
            height=2,
            config_data={
                'metrics': ['total_calls', 'abandonment_rate', 'avg_duration']
            },
            is_visible=True,
            refresh_interval_seconds=300
        )
        
        # 2. Gráfico de llamadas (mitad izquierda)
        WidgetConfig.objects.create(
            dashboard=dashboard,
            widget_type='CALLS_CHART',
            widget_name='Gráfico de Llamadas',
            position_x=0,
            position_y=2,
            width=6,
            height=4,
            config_data={
                'chart_type': 'line',
                'metrics': ['total', 'answered', 'abandoned'],
                'time_range': 'last_7_days'
            },
            is_visible=True,
            refresh_interval_seconds=300
        )
        
        # 3. Gráfico de transferencias (mitad derecha)
        WidgetConfig.objects.create(
            dashboard=dashboard,
            widget_type='TRANSFERS_CHART',
            widget_name='Gráfico de Transferencias',
            position_x=6,
            position_y=2,
            width=6,
            height=4,
            config_data={
                'chart_type': 'bar',
                'time_range': 'last_7_days'
            },
            is_visible=True,
            refresh_interval_seconds=300
        )
        
        # Crear preferencias si no existen
        UserDashboardPreference.objects.get_or_create(
            user=user,
            defaults={
                'default_dashboard': dashboard,
                'theme': 'light',
                'refresh_enabled': True,
                'refresh_interval_seconds': 300,
                'show_notifications': True,
                'preferences': {
                    'language': 'es',
                    'timezone': 'America/Santiago',
                    'date_format': 'DD/MM/YYYY'
                }
            }
        )
        
        return dashboard
    
    @staticmethod
    @transaction.atomic
    def clone_dashboard(dashboard_id, new_user):
        """
        Clonar dashboard existente para un nuevo usuario.
        
        Copia:
        - DashboardConfig (sin is_default, sin is_public)
        - Todos los WidgetConfig asociados
        
        Args:
            dashboard_id: ID del dashboard a clonar
            new_user: Usuario que recibirá el clon
        
        Returns:
            DashboardConfig clonado
        
        Raises:
            DashboardConfig.DoesNotExist: Si dashboard no existe
        """
        original = DashboardConfig.objects.get(
            id=dashboard_id,
            deleted_at__isnull=True
        )
        
        # Crear copia del dashboard
        new_dashboard = DashboardConfig.objects.create(
            user=new_user,
            config_name=f"{original.config_name} (copia)",
            description=original.description,
            layout_config=original.layout_config.copy(),
            is_default=False,  # El clon nunca es default
            is_public=False    # El clon nunca es público
        )
        
        # Copiar todos los widgets
        for widget in original.widgets.all():
            WidgetConfig.objects.create(
                dashboard=new_dashboard,
                widget_type=widget.widget_type,
                widget_name=widget.widget_name,
                position_x=widget.position_x,
                position_y=widget.position_y,
                width=widget.width,
                height=widget.height,
                config_data=widget.config_data.copy(),
                is_visible=widget.is_visible,
                refresh_interval_seconds=widget.refresh_interval_seconds
            )
        
        return new_dashboard
    
    @staticmethod
    @transaction.atomic
    def set_as_default(dashboard_id, user):
        """
        Marcar dashboard como default para el usuario.
        
        Solo un dashboard puede ser default por usuario.
        Desmarca otros dashboards como default.
        
        Args:
            dashboard_id: ID del dashboard a marcar como default
            user: Usuario propietario
        
        Raises:
            DashboardConfig.DoesNotExist: Si dashboard no existe
            PermissionDenied: Si usuario no es propietario
        """
        dashboard = DashboardConfig.objects.get(
            id=dashboard_id,
            deleted_at__isnull=True
        )
        
        # Verificar ownership
        if dashboard.user != user:
            raise PermissionDenied(
                "No puedes marcar como default un dashboard que no te pertenece"
            )
        
        # Desmarcar otros dashboards como default
        DashboardConfig.objects.filter(
            user=user,
            is_default=True
        ).exclude(id=dashboard_id).update(is_default=False)
        
        # Marcar este como default
        dashboard.is_default = True
        dashboard.save()
        
        # Actualizar preferencias
        preference, _ = UserDashboardPreference.objects.get_or_create(
            user=user
        )
        preference.default_dashboard = dashboard
        preference.save()
    
    @staticmethod
    def export_config(dashboard_id):
        """
        Exportar configuración de dashboard a JSON.
        
        Exporta:
        - Configuración del dashboard
        - Configuración de todos los widgets
        
        Args:
            dashboard_id: ID del dashboard a exportar
        
        Returns:
            Dict con configuración completa
        
        Raises:
            DashboardConfig.DoesNotExist: Si dashboard no existe
        """
        dashboard = DashboardConfig.objects.get(
            id=dashboard_id,
            deleted_at__isnull=True
        )
        
        # Exportar dashboard
        export_data = {
            'version': '1.0',
            'dashboard': {
                'config_name': dashboard.config_name,
                'description': dashboard.description,
                'layout_config': dashboard.layout_config,
            },
            'widgets': []
        }
        
        # Exportar widgets
        for widget in dashboard.widgets.all().order_by('position_y', 'position_x'):
            export_data['widgets'].append({
                'widget_type': widget.widget_type,
                'widget_name': widget.widget_name,
                'position_x': widget.position_x,
                'position_y': widget.position_y,
                'width': widget.width,
                'height': widget.height,
                'config_data': widget.config_data,
                'is_visible': widget.is_visible,
                'refresh_interval_seconds': widget.refresh_interval_seconds
            })
        
        return export_data
    
    @staticmethod
    @transaction.atomic
    def import_config(config_json, user):
        """
        Importar configuración de dashboard desde JSON.
        
        Crea:
        - DashboardConfig nuevo
        - WidgetConfig asociados
        
        Args:
            config_json: Dict o str JSON con configuración
            user: Usuario que recibirá el dashboard importado
        
        Returns:
            DashboardConfig creado
        
        Raises:
            ValidationError: Si JSON es inválido
        """
        # Parsear JSON si es string
        if isinstance(config_json, str):
            try:
                config_data = json.loads(config_json)
            except json.JSONDecodeError as e:
                raise ValidationError(f"JSON inválido: {str(e)}")
        else:
            config_data = config_json
        
        # Validar estructura
        if 'dashboard' not in config_data or 'widgets' not in config_data:
            raise ValidationError(
                "JSON debe contener 'dashboard' y 'widgets'"
            )
        
        dashboard_data = config_data['dashboard']
        widgets_data = config_data['widgets']
        
        # Crear dashboard
        dashboard = DashboardConfig.objects.create(
            user=user,
            config_name=dashboard_data.get('config_name', 'Dashboard Importado'),
            description=dashboard_data.get('description', ''),
            layout_config=dashboard_data.get('layout_config', {}),
            is_default=False,
            is_public=False
        )
        
        # Crear widgets
        for widget_data in widgets_data:
            WidgetConfig.objects.create(
                dashboard=dashboard,
                widget_type=widget_data['widget_type'],
                widget_name=widget_data['widget_name'],
                position_x=widget_data.get('position_x', 0),
                position_y=widget_data.get('position_y', 0),
                width=widget_data.get('width', 6),
                height=widget_data.get('height', 4),
                config_data=widget_data.get('config_data', {}),
                is_visible=widget_data.get('is_visible', True),
                refresh_interval_seconds=widget_data.get('refresh_interval_seconds', 300)
            )
        
        return dashboard
    
    @staticmethod
    def delete_dashboard(dashboard_id, user):
        """
        Eliminar dashboard (soft delete).
        
        Si el dashboard es default, desmarca is_default.
        No elimina físicamente, solo marca deleted_at.
        
        Args:
            dashboard_id: ID del dashboard a eliminar
            user: Usuario propietario
        
        Raises:
            DashboardConfig.DoesNotExist: Si dashboard no existe
            PermissionDenied: Si usuario no es propietario
        """
        dashboard = DashboardConfig.objects.get(
            id=dashboard_id,
            deleted_at__isnull=True
        )
        
        # Verificar ownership
        if dashboard.user != user:
            raise PermissionDenied(
                "No puedes eliminar un dashboard que no te pertenece"
            )
        
        # Si es default, desmarcar
        if dashboard.is_default:
            dashboard.is_default = False
        
        # Soft delete
        dashboard.delete()  # SoftDeleteMixin maneja el soft delete
