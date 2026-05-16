# apps/alerts/services/subscription_service.py

from django.db import IntegrityError
from apps.alerts.models import AlertSubscription
import logging

logger = logging.getLogger(__name__)


class SubscriptionService:
    """
    Servicio para gestión de suscripciones a alertas
    """

    @staticmethod
    def subscribe(user, alert_configuration):
        """
        Suscribe un usuario a una configuración de alerta

        Args:
            user (User): Usuario
            alert_configuration (AlertConfiguration): Configuración

        Returns:
            AlertSubscription: Suscripción creada o existente
        """
        try:
            subscription, created = AlertSubscription.objects.get_or_create(
                user=user,
                alert_configuration=alert_configuration,
                defaults={'is_active': True}
            )

            if not created and not subscription.is_active:
                # Reactivar suscripción existente
                subscription.is_active = True
                subscription.save(update_fields=['is_active'])
                logger.info(f"Suscripción reactivada: {user.username} -> {alert_configuration.name}")
            elif created:
                logger.info(f"Nueva suscripción: {user.username} -> {alert_configuration.name}")

            return subscription

        except IntegrityError as e:
            logger.error(f"Error creando suscripción: {e}")
            raise


    @staticmethod
    def unsubscribe(user, alert_configuration):
        """
        Desuscribe un usuario de una configuración de alerta

        Args:
            user (User): Usuario
            alert_configuration (AlertConfiguration): Configuración

        Returns:
            bool: True si se desuscribió, False si no estaba suscrito
        """
        try:
            subscription = AlertSubscription.objects.get(
                user=user,
                alert_configuration=alert_configuration
            )

            subscription.is_active = False
            subscription.save(update_fields=['is_active'])
            logger.info(f"Desuscripción: {user.username} -> {alert_configuration.name}")
            return True

        except AlertSubscription.DoesNotExist:
            logger.warning(f"Usuario {user.username} no estaba suscrito a {alert_configuration.name}")
            return False


    @staticmethod
    def get_user_subscriptions(user, active_only=True):
        """
        Obtiene las suscripciones de un usuario

        Args:
            user (User): Usuario
            active_only (bool): Solo suscripciones activas

        Returns:
            QuerySet[AlertSubscription]: Suscripciones del usuario
        """
        queryset = AlertSubscription.objects.filter(
            user=user,
            deleted_at__isnull=True
        ).select_related('alert_configuration')

        if active_only:
            queryset = queryset.filter(is_active=True)

        return queryset


    @staticmethod
    def get_configuration_subscribers(alert_configuration, active_only=True):
        """
        Obtiene los usuarios suscritos a una configuración

        Args:
            alert_configuration (AlertConfiguration): Configuración
            active_only (bool): Solo suscripciones activas

        Returns:
            QuerySet[AlertSubscription]: Suscripciones a la configuración
        """
        queryset = AlertSubscription.objects.filter(
            alert_configuration=alert_configuration,
            deleted_at__isnull=True
        ).select_related('user')

        if active_only:
            queryset = queryset.filter(is_active=True)

        return queryset
