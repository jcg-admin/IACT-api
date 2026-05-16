# apps/alerts/services/message_service.py

from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.alerts.models import InternalMessage, MessageRecipient
import logging

logger = logging.getLogger(__name__)


class MessageService:
    """
    Servicio para gestión de mensajes internos

    Cumple CNST-001: Solo mensajería interna (NO email)
    Cumple CNST-024: Máximo 50 destinatarios
    """

    @staticmethod
    @transaction.atomic
    def send_message(sender, recipients, subject, body, priority='info'):
        """
        Envía un mensaje interno a múltiples destinatarios

        Args:
            sender (User): Usuario que envía
            recipients (list[User]): Lista de usuarios destinatarios
            subject (str): Asunto del mensaje
            body (str): Contenido del mensaje
            priority (str): Prioridad (info, warning, error, critical)

        Returns:
            InternalMessage: Mensaje creado

        Raises:
            ValidationError: Si más de 50 destinatarios (CNST-024)
        """
        # Validar CNST-024: máximo 50 destinatarios
        if len(recipients) > 50:
            raise ValidationError(
                f'Máximo 50 destinatarios permitidos. Recibidos: {len(recipients)} (CNST-024)'
            )

        # Validar que hay al menos 1 destinatario
        if len(recipients) == 0:
            raise ValidationError('Debe especificar al menos 1 destinatario')

        # Crear mensaje
        message = InternalMessage.objects.create(
            sender=sender,
            subject=subject,
            body=body,
            priority=priority
        )

        # Crear MessageRecipient para cada destinatario
        recipients_objs = [
            MessageRecipient(message=message, user=recipient)
            for recipient in recipients
        ]
        MessageRecipient.objects.bulk_create(recipients_objs)

        logger.info(
            f"Mensaje '{subject}' enviado de {sender.username} a {len(recipients)} destinatarios"
        )

        return message


    @staticmethod
    def get_inbox(user, unread_only=False, archived=False):
        """
        Obtiene la bandeja de entrada de un usuario

        Args:
            user (User): Usuario
            unread_only (bool): Solo mensajes no leídos
            archived (bool): Incluir archivados

        Returns:
            QuerySet[MessageRecipient]: Mensajes en bandeja
        """
        queryset = MessageRecipient.objects.filter(
            user=user
        ).select_related(
            'message',
            'message__sender'
        ).order_by('-message__created_at')

        # Filtrar no leídos
        if unread_only:
            queryset = queryset.filter(read_at__isnull=True)

        # Filtrar archivados
        if not archived:
            queryset = queryset.filter(archived_at__isnull=True)

        return queryset


    @staticmethod
    def mark_as_read(message, user):
        """
        Marca un mensaje como leído para un usuario

        Args:
            message (InternalMessage): Mensaje
            user (User): Usuario destinatario

        Returns:
            MessageRecipient: Registro actualizado

        Raises:
            MessageRecipient.DoesNotExist: Si usuario no es destinatario
        """
        recipient = MessageRecipient.objects.get(
            message=message,
            user=user
        )

        if recipient.read_at is None:
            recipient.read_at = timezone.now()
            recipient.save(update_fields=['read_at'])
            logger.debug(f"Mensaje {message.id} marcado como leído por {user.username}")

        return recipient


    @staticmethod
    def archive_message(message, user):
        """
        Archiva un mensaje para un usuario

        Args:
            message (InternalMessage): Mensaje
            user (User): Usuario destinatario

        Returns:
            MessageRecipient: Registro actualizado
        """
        recipient = MessageRecipient.objects.get(
            message=message,
            user=user
        )

        if recipient.archived_at is None:
            recipient.archived_at = timezone.now()
            recipient.save(update_fields=['archived_at'])
            logger.debug(f"Mensaje {message.id} archivado por {user.username}")

        return recipient


    @staticmethod
    def unarchive_message(message, user):
        """
        Desarchivar un mensaje para un usuario

        Args:
            message (InternalMessage): Mensaje
            user (User): Usuario destinatario

        Returns:
            MessageRecipient: Registro actualizado
        """
        recipient = MessageRecipient.objects.get(
            message=message,
            user=user
        )

        if recipient.archived_at is not None:
            recipient.archived_at = None
            recipient.save(update_fields=['archived_at'])
            logger.debug(f"Mensaje {message.id} desarchivado por {user.username}")

        return recipient
