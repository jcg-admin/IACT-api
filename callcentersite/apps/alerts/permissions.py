# apps/alerts/permissions.py

from apps.core.permissions import RequiresFunctionPermission


class MessagePermissions(RequiresFunctionPermission):
    """
    Permisos para mensajes internos

    MOD_Alerts functions:
    - alerts.send (ALRT_SEND)
    - alerts.view.inbox (ALRT_VIEW_INB)
    - alerts.view.all (ALRT_VIEW_ALL)
    - alerts.delete.messages (ALRT_DEL_MSG)
    """

    function_mapping = {
        'list': 'alerts.view.all',          # GET /messages/
        'retrieve': None,                    # Verificar ownership
        'create': 'alerts.send',            # POST /messages/
        'update': None,                      # No permitido
        'partial_update': None,              # No permitido
        'destroy': 'alerts.delete.messages', # DELETE /messages/{id}/

        # Custom actions
        'inbox': 'alerts.view.inbox',       # GET /messages/inbox/
        'mark_read': None,                   # Verificar ownership
        'archive': None,                     # Verificar ownership
        'unarchive': None,                   # Verificar ownership
    }

    def has_object_permission(self, request, view, obj):
        """
        Verificar ownership para acciones específicas

        Args:
            request: Request
            view: ViewSet
            obj: InternalMessage o MessageRecipient

        Returns:
            bool: True si tiene permiso
        """
        from apps.alerts.models import MessageRecipient

        # Determinar objeto real
        if isinstance(obj, MessageRecipient):
            message = obj.message
            recipient = obj
        else:
            message = obj
            recipient = None

        # Para retrieve, mark_read, archive, unarchive: debe ser destinatario
        if view.action in ['retrieve', 'mark_read', 'archive', 'unarchive']:
            # Verificar si es destinatario
            if recipient:
                return recipient.user == request.user
            else:
                return message.recipients.filter(id=request.user.id).exists()

        # Para destroy: debe ser sender o tener permiso especial
        if view.action == 'destroy':
            if message.sender == request.user:
                return True
            # Verificar si tiene permiso de eliminar cualquier mensaje
            return request.user.has_function('alerts.delete.messages')

        return False


class AlertConfigurationPermissions(RequiresFunctionPermission):
    """
    Permisos para configuraciones de alertas

    MOD_Alerts function:
    - alerts.configure.rules (ALRT_CFG_RUL)
    """

    function_mapping = {
        'list': 'alerts.configure.rules',
        'retrieve': 'alerts.configure.rules',
        'create': 'alerts.configure.rules',
        'update': 'alerts.configure.rules',
        'partial_update': 'alerts.configure.rules',
        'destroy': 'alerts.configure.rules',
    }


class AlertSubscriptionPermissions(RequiresFunctionPermission):
    """
    Permisos para suscripciones

    MOD_Alerts function:
    - alerts.manage.subscriptions (ALRT_MNG_SUB)
    """

    function_mapping = {
        'list': 'alerts.manage.subscriptions',
        'retrieve': 'alerts.manage.subscriptions',
        'create': 'alerts.manage.subscriptions',
        'destroy': 'alerts.manage.subscriptions',
    }

    def has_object_permission(self, request, view, obj):
        """
        Solo puede gestionar sus propias suscripciones

        Args:
            request: Request
            view: ViewSet
            obj: AlertSubscription

        Returns:
            bool: True si es su propia suscripción
        """
        return obj.user == request.user
