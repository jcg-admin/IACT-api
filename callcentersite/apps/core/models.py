"""
Abstract base models for the IACT API.

REPARACION v1.0.1 — 2026-04-30:
  Se restauran los modelos abstractos que el resto de las apps esperan importar.
  La implementacion real de SoftDeleteMixin/SoftDeleteManager vive en utils/models.py
  y se re-exporta aqui para mantener compatibilidad de imports.

Modelos disponibles:
  - TimestampedModel    (created_at, updated_at)
  - TimeStampedModel    (alias de TimestampedModel para compatibilidad)
  - SoftDeleteMixin     (is_deleted, deleted_at, delete(), restore())
  - SoftDeleteManager   (filtra is_deleted=False por defecto)
  - AuditedModel        (created_by, updated_by + timestamps)
  - CompleteBaseModel   (timestamps + audit + soft-delete)
"""
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Re-exportar desde utils para compatibilidad de imports
from apps.utils.models import SoftDeleteMixin, SoftDeleteManager, SoftDeleteQuerySet


# ==============================================================================
# TIMESTAMPS
# ==============================================================================

class TimestampedModel(models.Model):
    """Abstract model with created_at and updated_at timestamps."""
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Creado')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Actualizado')
    )

    class Meta:
        abstract = True


# Alias para compatibilidad (authentication/models.py importa TimeStampedModel)
TimeStampedModel = TimestampedModel


# ==============================================================================
# SOFT DELETE (compatibilidad con SoftDeleteModel nombrado)
# ==============================================================================

class SoftDeleteModel(TimestampedModel):
    """Abstract model with timestamps + soft-delete via is_active."""
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Activo')
    )

    class Meta:
        abstract = True

    def soft_delete(self):
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])

    def restore(self):
        self.is_active = True
        self.save(update_fields=['is_active', 'updated_at'])


# ==============================================================================
# AUDITED MODEL (quien creo / quien modifico)
# ==============================================================================

class AuditedModel(TimestampedModel):
    """
    Abstract model with audit fields: created_by, updated_by.

    Hereda de TimestampedModel (created_at, updated_at).
    Agrega: created_by, updated_by (FK al usuario del sistema).
    """
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name=_('Creado por')
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name=_('Actualizado por')
    )

    class Meta:
        abstract = True


# ==============================================================================
# COMPLETE BASE MODEL (timestamps + audit + soft-delete)
# ==============================================================================

class CompleteBaseModel(AuditedModel, SoftDeleteMixin):
    """
    Modelo completo con:
      - TimestampedModel: created_at, updated_at
      - AuditedModel: created_by, updated_by
      - SoftDeleteMixin: is_deleted, deleted_at, delete(), restore()

    Usado por: authentication.UserSecurityAnswer, authentication.SessionLog
    """
    class Meta:
        abstract = True
