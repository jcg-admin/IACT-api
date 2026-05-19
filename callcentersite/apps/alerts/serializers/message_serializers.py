"""
Serializers para Sistema de Mensajería Interna.

Responsabilidad: Serialización de mensajes internos y bandeja de entrada.

Serializers:
- UserBasicSerializer: Usuario básico para nested fields
- MessageRecipientSerializer: Destinatario de mensaje
- InternalMessageListSerializer: Listado de mensajes
- InternalMessageDetailSerializer: Detalle de mensaje
- InternalMessageCreateSerializer: Creación de mensaje
- InboxMessageSerializer: Mensaje en bandeja de entrada

Principios aplicados:
- SRP: Responsabilidad única (mensajería interna)
- Clean Code: Validaciones claras
- Service Layer: Uso de MessageService para lógica de negocio
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

from apps.alerts.models import InternalMessage, MessageRecipient
from drf_spectacular.utils import extend_schema_field, OpenApiTypes

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    """
    Serializer básico de usuario para nested fields.

    Usado en mensajes y alertas para mostrar información básica del usuario.
    """

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = fields


class MessageRecipientSerializer(serializers.ModelSerializer):
    """
    Serializer para destinatario de mensaje.

    Incluye información del usuario y estado de lectura/archivo.
    """

    user = UserBasicSerializer(read_only=True)

    is_read     = serializers.BooleanField(read_only=True)
    is_archived = serializers.BooleanField(read_only=True)

    class Meta:
        model = MessageRecipient
        fields = [
            'id',
            'user',
            'read_at',
            'archived_at',
            'created_at',
            'is_read',
            'is_archived'
        ]
        read_only_fields = fields


class InternalMessageListSerializer(serializers.ModelSerializer):
    """
    Serializer para listar mensajes.

    Versión simplificada con información esencial.
    """

    sender = UserBasicSerializer(read_only=True)
    recipient_count = serializers.SerializerMethodField()

    class Meta:
        model = InternalMessage
        fields = [
            'id',
            'sender',
            'subject',
            'priority',
            'created_at',
            'recipient_count'
        ]
        read_only_fields = fields

    @extend_schema_field(OpenApiTypes.INT)
    def get_recipient_count(self, obj):
        """Contar destinatarios del mensaje."""
        return obj.recipients.count()


class InternalMessageDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detallado para mensaje.

    Incluye cuerpo del mensaje y lista completa de destinatarios.
    """

    sender = UserBasicSerializer(read_only=True)
    message_recipients = MessageRecipientSerializer(many=True, read_only=True)

    class Meta:
        model = InternalMessage
        fields = [
            'id',
            'sender',
            'subject',
            'body',
            'priority',
            'created_at',
            'message_recipients'
        ]
        read_only_fields = fields


class InternalMessageCreateSerializer(serializers.Serializer):
    """
    Serializer para crear mensaje.

    Valida destinatarios y crea mensaje usando MessageService.

    Constraints:
    - CNST-024: Máximo 50 destinatarios por mensaje
    """

    recipient_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        max_length=50,  # CNST-024
        write_only=True,
        help_text='Lista de IDs de usuarios destinatarios (máximo 50)'
    )
    subject = serializers.CharField(
        max_length=200
    )
    body = serializers.CharField()
    priority = serializers.ChoiceField(
        choices=['info', 'warning', 'error', 'critical'],
        default='info'
    )

    def validate_recipient_ids(self, value):
        """Validar que los usuarios existen."""
        users = User.objects.filter(id__in=value)
        if users.count() != len(value):
            raise serializers.ValidationError(
                'Algunos IDs de usuarios no son válidos'
            )
        return value

    def create(self, validated_data):
        """
        Crear mensaje usando MessageService.

        El remitente se obtiene automáticamente del request.user.
        """
        from apps.alerts.services import MessageService

        recipient_ids = validated_data.pop('recipient_ids')
        recipients = User.objects.filter(id__in=recipient_ids)
        sender = self.context['request'].user

        message = MessageService.send_message(
            sender=sender,
            recipients=list(recipients),
            subject=validated_data['subject'],
            body=validated_data['body'],
            priority=validated_data.get('priority', 'info')
        )

        return message


class InboxMessageSerializer(serializers.ModelSerializer):
    """
    Serializer para mensajes en bandeja de entrada.

    Basado en MessageRecipient pero muestra información del mensaje.
    """

    message_id = serializers.IntegerField(source='message.id', read_only=True)
    subject = serializers.CharField(source='message.subject', read_only=True)
    body = serializers.CharField(source='message.body', read_only=True)
    priority = serializers.CharField(source='message.priority', read_only=True)
    sender = UserBasicSerializer(source='message.sender', read_only=True)
    created_at = serializers.DateTimeField(source='message.created_at', read_only=True)

    is_read     = serializers.BooleanField(read_only=True)
    is_archived = serializers.BooleanField(read_only=True)

    class Meta:
        model = MessageRecipient
        fields = [
            'id',
            'message_id',
            'sender',
            'subject',
            'body',
            'priority',
            'read_at',
            'archived_at',
            'created_at',
            'is_read',
            'is_archived'
        ]
        read_only_fields = fields
