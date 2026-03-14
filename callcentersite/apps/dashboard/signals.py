"""
Signals para la app Dashboard.

Signals implementados:
- create_default_dashboard: Crear dashboard por defecto para nuevos usuarios
- ensure_only_one_default: Asegurar solo un dashboard default por usuario
- invalidate_widget_cache: Limpiar cache al actualizar widget

FASE 3: Implementación de signals.
"""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from apps.dashboard.models import DashboardConfig, WidgetConfig
from apps.dashboard.services import DashboardService, WidgetService

User = get_user_model()
logger = logging.getLogger(__name__)


# ==============================================================================
# SIGNAL: Crear dashboard por defecto para nuevos usuarios
# ==============================================================================

@receiver(post_save, sender=User)
def create_default_dashboard_for_new_user(sender, instance, created, **kwargs):
    """
    Crear dashboard por defecto cuando se crea un nuevo usuario.
    
    Ejecuta:
    - DashboardService.create_default_dashboard()
    - Crea dashboard con 3 widgets por defecto
    - Crea UserDashboardPreference vinculada
    
    Args:
        sender: Modelo User
        instance: Instancia de User creada
        created: Boolean, True si es nuevo usuario
        **kwargs: Argumentos adicionales
    """
    if created:
        try:
            # Crear dashboard por defecto usando el service
            dashboard = DashboardService.create_default_dashboard(instance)
            
            logger.info(
                f"Dashboard por defecto creado para usuario {instance.username} "
                f"(ID: {instance.id}) - Dashboard ID: {dashboard.id}"
            )
            
        except Exception as e:
            # Log error pero no fallar creación de usuario
            logger.error(
                f"Error al crear dashboard por defecto para usuario {instance.username}: {str(e)}",
                exc_info=True
            )


# ==============================================================================
# SIGNAL: Asegurar solo un dashboard default por usuario
# ==============================================================================

@receiver(post_save, sender=DashboardConfig)
def ensure_only_one_default_dashboard(sender, instance, created, **kwargs):
    """
    Asegurar que solo un dashboard sea default por usuario.
    
    Si un dashboard se marca como is_default=True:
    - Desmarca todos los otros dashboards del mismo usuario
    
    Args:
        sender: Modelo DashboardConfig
        instance: Instancia de DashboardConfig guardada
        created: Boolean, True si es nuevo dashboard
        **kwargs: Argumentos adicionales
    """
    # Solo actuar si el dashboard es default
    if instance.is_default:
        try:
            # Desmarcar otros dashboards del mismo usuario
            # Excluir el dashboard actual
            updated_count = DashboardConfig.objects.filter(
                user=instance.user,
                is_default=True,
                deleted_at__isnull=True
            ).exclude(id=instance.id).update(is_default=False)
            
            if updated_count > 0:
                logger.info(
                    f"Desmarcados {updated_count} dashboards como default para "
                    f"usuario {instance.user.username}. Nuevo default: '{instance.config_name}'"
                )
            
        except Exception as e:
            logger.error(
                f"Error al desmarcar dashboards default para usuario {instance.user.username}: {str(e)}",
                exc_info=True
            )


# ==============================================================================
# SIGNAL: Invalidar cache de widget al actualizar
# ==============================================================================

@receiver(post_save, sender=WidgetConfig)
def invalidate_widget_cache_on_update(sender, instance, created, **kwargs):
    """
    Invalidar cache del widget cuando se actualiza.
    
    Ejecuta:
    - WidgetService.refresh_widget_cache()
    - Limpia cache para forzar recálculo en próxima consulta
    
    Args:
        sender: Modelo WidgetConfig
        instance: Instancia de WidgetConfig guardada
        created: Boolean, True si es nuevo widget
        **kwargs: Argumentos adicionales
    """
    # Invalidar cache solo si es actualización (no creación)
    # En creación no hay cache previo
    if not created:
        try:
            # Refrescar cache del widget
            WidgetService.refresh_widget_cache(instance.id)
            
            logger.debug(
                f"Cache invalidado para widget '{instance.widget_name}' "
                f"(ID: {instance.id}) del dashboard '{instance.dashboard.config_name}'"
            )
            
        except Exception as e:
            # Log error pero no fallar actualización
            logger.error(
                f"Error al invalidar cache de widget {instance.id}: {str(e)}",
                exc_info=True
            )

