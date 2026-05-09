"""
apps/access/services/menu_lifecycle_service.py

State machine para el lifecycle de MenuItem (UC_ADM_05).

Transiciones válidas:
    DRAFT → ACTIVE → DEPRECATED → ARCHIVED
    ARCHIVED → ACTIVE está prohibida.

Referencia: domain-model/menu-lifecycle-service.rst, ADR-BACK-008
"""
import logging
from datetime import timedelta
from typing import Optional

from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


class InvalidTransitionError(Exception):
    """La transición de estado solicitada no está permitida."""
    pass


class MenuLifecycleService:
    """
    Controla el ciclo de vida de MenuItem.

    Uso:
        MenuLifecycleService.transition(item, 'ACTIVE')
        MenuLifecycleService.auto_archive_menu_items()
    """

    # Transiciones permitidas: {estado_origen: [estados_destino]}
    VALID_TRANSITIONS = {
        'DRAFT':      ['ACTIVE'],
        'ACTIVE':     ['DEPRECATED'],
        'DEPRECATED': ['ARCHIVED'],
        'ARCHIVED':   [],          # estado terminal
    }

    # Días en DEPRECATED antes del auto-archivo (UC_ADM_05 FA-04)
    AUTO_ARCHIVE_DAYS = 90

    # -----------------------------------------------------------------------
    # Transición de estado
    # -----------------------------------------------------------------------

    @classmethod
    def transition(cls, item, new_status: str, *, block_reason: Optional[str] = None) -> None:
        """
        Aplica una transición de estado al MenuItem dado.

        Args:
            item: instancia de MenuItem.
            new_status: uno de DRAFT / ACTIVE / DEPRECATED / ARCHIVED.
            block_reason: si se provee junto con new_status='DEPRECATED',
                          marca el item como bloqueado para auto-archivo.

        Raises:
            InvalidTransitionError: si la transición no está permitida.
            ValueError: si new_status no es un valor válido.
        """
        from apps.access.models import MenuItem

        valid_statuses = [c[0] for c in MenuItem.STATUS_CHOICES]
        if new_status not in valid_statuses:
            raise ValueError(f"Estado inválido: '{new_status}'. Válidos: {valid_statuses}")

        current = item.status
        allowed = cls.VALID_TRANSITIONS.get(current, [])

        if new_status not in allowed:
            raise InvalidTransitionError(
                f"Transición no permitida: {current} → {new_status}. "
                f"Desde {current} solo se puede ir a: {allowed or ['ninguno (estado terminal)']}"
            )

        now = timezone.now()

        with transaction.atomic():
            item.status = new_status

            if new_status == 'DEPRECATED':
                item.deprecated_at = now
                if block_reason:
                    item.block_auto_archive = True
                    item.block_reason = block_reason

            elif new_status == 'ARCHIVED':
                item.archived_at = now

            item.save(update_fields=cls._fields_to_update(new_status))
            logger.info(
                "MenuItem %d: %s → %s",
                item.pk, current, new_status,
            )

    @staticmethod
    def _fields_to_update(new_status: str) -> list:
        fields = ['status', 'updated_at']
        if new_status == 'DEPRECATED':
            fields.append('deprecated_at')
        elif new_status == 'ARCHIVED':
            fields.append('archived_at')
        return fields

    # -----------------------------------------------------------------------
    # Auto-archivo (UC_ADM_05 FA-04)
    # -----------------------------------------------------------------------

    @classmethod
    def auto_archive_menu_items(cls) -> int:
        """
        Archiva todos los MenuItem en estado DEPRECATED con más de
        AUTO_ARCHIVE_DAYS días en ese estado, excepto los marcados con
        block_auto_archive=True.

        Returns:
            Número de items archivados.
        """
        from apps.access.models import MenuItem

        cutoff = timezone.now() - timedelta(days=cls.AUTO_ARCHIVE_DAYS)

        candidates = MenuItem.objects.filter(
            status='DEPRECATED',
            deprecated_at__lte=cutoff,
        )

        archived = 0
        for item in candidates:
            if getattr(item, 'block_auto_archive', False):
                logger.info("MenuItem %d omitido: block_auto_archive=True", item.pk)
                continue
            try:
                cls.transition(item, 'ARCHIVED')
                archived += 1
            except InvalidTransitionError as e:
                logger.error("MenuItem %d: error en auto-archivo: %s", item.pk, e)

        logger.info("auto_archive_menu_items: %d items archivados", archived)
        return archived

    # -----------------------------------------------------------------------
    # Consultas de conveniencia
    # -----------------------------------------------------------------------

    @staticmethod
    def can_transition(item, new_status: str) -> bool:
        """Retorna True si la transición es válida sin aplicarla."""
        allowed = MenuLifecycleService.VALID_TRANSITIONS.get(item.status, [])
        return new_status in allowed

    @staticmethod
    def get_allowed_transitions(item) -> list:
        """Retorna la lista de estados a los que puede transicionar el item."""
        return MenuLifecycleService.VALID_TRANSITIONS.get(item.status, [])
