# apps/alerts/services/alert_service.py

from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.alerts.models import AlertConfiguration, AlertSubscription, InternalMessage, MessageRecipient
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


class AlertService:
    """
    Servicio para gestión de alertas automáticas
    
    Cumple CNST-013: Usa APScheduler, NO Celery
    """
    
    @staticmethod
    def evaluate_all_active_configs():
        """
        Evalúa todas las configuraciones activas
        
        Ejecutado por APScheduler cada 5 minutos (CNST-013 compliant)
        """
        logger.info("Iniciando evaluación de alertas automáticas")
        
        active_configs = AlertConfiguration.objects.filter(
            is_active=True,
            deleted_at__isnull=True
        )
        
        triggered_count = 0
        
        for config in active_configs:
            try:
                # Actualizar timestamp de evaluación
                config.last_evaluated_at = timezone.now()
                config.save(update_fields=['last_evaluated_at'])
                
                # Evaluar condición
                if AlertService._evaluate_condition(config.condition):
                    # Condición cumplida, disparar alerta
                    AlertService._trigger_alert(config)
                    triggered_count += 1
                    
            except Exception as e:
                logger.error(f"Error evaluando config {config.id} '{config.name}': {e}")
        
        logger.info(f"Evaluación completada: {triggered_count} alertas disparadas de {active_configs.count()} configuraciones")
        
        return triggered_count
    
    
    @staticmethod
    def _evaluate_condition(condition: dict) -> bool:
        """
        Evalúa si una condición se cumple
        
        Args:
            condition: Dict con estructura:
                {
                    "metric": "call_volume | avg_wait_time | sla_percentage",
                    "operator": "> | < | >= | <= | ==",
                    "value": 100,
                    "period": "1h | 30m | 1d"
                }
        
        Returns:
            True si la condición se cumple, False otherwise
        """
        metric = condition.get('metric')
        operator = condition.get('operator')
        threshold = condition.get('value')
        period = condition.get('period')
        
        if not all([metric, operator, threshold is not None, period]):
            logger.warning(f"Condición incompleta: {condition}")
            return False
        
        # Calcular timestamp de inicio según período
        now = timezone.now()
        start_time = AlertService._get_start_time(now, period)
        
        if start_time is None:
            return False
        
        # Obtener métrica actual
        current_value = AlertService._get_metric_value(metric, start_time, now)
        
        if current_value is None:
            return False
        
        # Evaluar operador
        return AlertService._evaluate_operator(current_value, operator, threshold)
    
    
    @staticmethod
    def _get_start_time(now, period):
        """Calcula timestamp de inicio según período"""
        if period == '1h':
            return now - timedelta(hours=1)
        elif period == '30m':
            return now - timedelta(minutes=30)
        elif period == '1d':
            return now - timedelta(days=1)
        elif period == '6h':
            return now - timedelta(hours=6)
        elif period == '12h':
            return now - timedelta(hours=12)
        else:
            logger.warning(f"Período desconocido: {period}")
            return None
    
    
    @staticmethod
    def _get_metric_value(metric, start_time, end_time):
        """
        Obtiene valor actual de una métrica.

        Las métricas call_volume, avg_wait_time y sla_percentage dependían de
        CallRecord (PostgreSQL ORM), eliminado en FASE 3. Esas métricas deben
        reimplementarse usando MariaDB via ivr_services.py cuando corresponda.
        """
        logger.warning(
            f"_get_metric_value: métrica '{metric}' no disponible — "
            f"CallRecord eliminado en FASE 3 (UC_OPR/UC_SUP/UC_CLI fuera de scope)"
        )
        return None

    
    @staticmethod
    def _evaluate_operator(current_value, operator, threshold):
        """Evalúa operador de comparación"""
        if operator == '>':
            return current_value > threshold
        elif operator == '<':
            return current_value < threshold
        elif operator == '>=':
            return current_value >= threshold
        elif operator == '<=':
            return current_value <= threshold
        elif operator == '==':
            return current_value == threshold
        else:
            logger.warning(f"Operador desconocido: {operator}")
            return False
    
    
    @staticmethod
    @transaction.atomic
    def _trigger_alert(config):
        """
        Dispara una alerta: crea mensaje y envía a suscritos
        
        Args:
            config (AlertConfiguration): Configuración que se disparó
        """
        # Obtener usuarios suscritos activos
        subscriptions = AlertSubscription.objects.filter(
            alert_configuration=config,
            is_active=True,
            deleted_at__isnull=True
        ).select_related('user')
        
        if not subscriptions.exists():
            logger.info(f"Config {config.id} '{config.name}': Sin usuarios suscritos")
            return
        
        # Usuario del sistema para enviar (primer admin o staff)
        system_user = User.objects.filter(is_staff=True).first()
        
        if not system_user:
            logger.error("No hay usuario staff para enviar alertas automáticas")
            return
        
        # Crear mensaje automático
        message = InternalMessage.objects.create(
            sender=system_user,
            subject=f"ALERTA: {config.name}",
            body=(
                f"Se ha disparado la alerta automática '{config.name}'.\n\n"
                f"Descripción: {config.description}\n"
                f"Condición: {config.condition}\n"
                f"Fecha/hora: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"Esta es una alerta automática generada por el sistema."
            ),
            priority=config.priority
        )
        
        # Crear MessageRecipient para cada suscrito
        recipients = []
        for subscription in subscriptions:
            recipients.append(
                MessageRecipient(
                    message=message,
                    user=subscription.user
                )
            )
        
        MessageRecipient.objects.bulk_create(recipients)
        
        # Actualizar timestamp de disparo
        config.last_triggered_at = timezone.now()
        config.save(update_fields=['last_triggered_at'])
        
        logger.info(
            f"Alerta '{config.name}' disparada a {len(recipients)} usuarios"
        )
