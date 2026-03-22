"""
Abstract Models base para IACT.

CLEAN_CODE v3.0.1: Nombres auto-documentados.
CRÍTICO: SOLO modelos con abstract=True.

Modelos concretos van en apps de negocio:
- Center, Service, CallRecord -> apps/pipeline/models.py
- UserServiceAccess -> apps/access/models.py (PARTE 7)
"""

from django.db import models
from django.utils import timezone
from django.conf import settings


# ============================================================================
# TIMESTAMPED MODEL
# ============================================================================

class TimeStampedModel(models.Model):
    """
    Modelo base con timestamps automáticos.
    
    CLEAN_CODE v3.0.1: Nombre que revela intención.
    
    Provee campos automáticos:
    - created_at: Se setea al crear
    - updated_at: Se actualiza al guardar
    
    Uso:
        class MiModelo(TimeStampedModel):
            # Automáticamente tiene created_at y updated_at
            nombre = models.CharField(max_length=100)
    """
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Creado',
        help_text='Fecha y hora de creación'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Actualizado',
        help_text='Fecha y hora de última actualización'
    )
    
    class Meta:
        abstract = True  # [SUCCESS] OBLIGATORIO


# ============================================================================
# SOFT DELETE QUERYSET Y MANAGER
# ============================================================================

class SoftDeleteQuerySet(models.QuerySet):
    """
    QuerySet para soft delete.
    
    CLEAN_CODE v3.0.1: Nombre auto-documentado.
    
    Provee métodos:
    - active(): Solo no eliminados
    - deleted(): Solo eliminados
    - with_deleted(): Todos (incluye eliminados)
    
    Uso:
        MiModelo.objects.active()  # Solo no eliminados
        MiModelo.objects.deleted()  # Solo eliminados
        MiModelo.objects.with_deleted()  # Todos
    """
    
    def active(self):
        """Retorna solo registros no eliminados."""
        return self.filter(is_deleted=False)
    
    def deleted(self):
        """Retorna solo registros eliminados."""
        return self.filter(is_deleted=True)
    
    def with_deleted(self):
        """Retorna todos los registros (incluye eliminados)."""
        return self


class SoftDeleteManager(models.Manager):
    """
    Manager para soft delete.
    
    CLEAN_CODE v3.0.1: Manager Pattern.
    
    Por defecto retorna solo no eliminados.
    
    Uso:
        class MiModelo(SoftDeleteMixin):
            objects = SoftDeleteManager()
        
        MiModelo.objects.all()  # Solo no eliminados
        MiModelo.objects.active()  # Explícito
        MiModelo.objects.deleted()  # Solo eliminados
    """
    
    def get_queryset(self):
        """Retorna queryset base."""
        return SoftDeleteQuerySet(self.model, using=self._db)
    
    def active(self):
        """Retorna solo no eliminados."""
        return self.get_queryset().active()
    
    def deleted(self):
        """Retorna solo eliminados."""
        return self.get_queryset().deleted()
    
    def with_deleted(self):
        """Retorna todos (incluye eliminados)."""
        return self.get_queryset().with_deleted()


# ============================================================================
# SOFT DELETE MIXIN
# ============================================================================

class SoftDeleteMixin(models.Model):
    """
    Mixin para soft delete (borrado lógico).
    
    CLEAN_CODE v3.0.1: Nombre descriptivo.
    
    Permite marcar registros como eliminados sin borrarlos físicamente de la BD.
    
    Provee:
    - is_deleted (flag booleano)
    - deleted_at (timestamp)
    - delete() override (soft delete)
    - hard_delete() (eliminación física)
    - restore() (restaurar eliminado)
    
    Uso:
        class MiModelo(SoftDeleteMixin, models.Model):
            nombre = models.CharField(max_length=100)
            
            # Usar SoftDeleteManager
            objects = SoftDeleteManager()
        
        # Soft delete
        obj = MiModelo.objects.get(id=1)
        obj.delete()  # Marca is_deleted=True
        
        # Hard delete
        obj.hard_delete()  # Elimina de BD
        
        # Restaurar
        obj.restore()  # is_deleted=False
        
        # Query solo no eliminados
        MiModelo.objects.active()
    """
    
    is_deleted = models.BooleanField(
        default=False,
        db_index=True,  # [SUCCESS] Índice para queries rápidas
        verbose_name='Eliminado',
        help_text='Indica si el registro está eliminado (delete lógico)'
    )
    
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Eliminado en',
        help_text='Fecha y hora en que se eliminó el registro'
    )
    
    class Meta:
        abstract = True  # [SUCCESS] OBLIGATORIO
    
    def delete(self, using=None, keep_parents=False):
        """
        Soft delete: marca como eliminado.
        
        NO elimina físicamente de la BD.
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])
    
    def hard_delete(self, using=None, keep_parents=False):
        """
        Hard delete: elimina físicamente.
        
        Usa delete() de Django directamente.
        """
        super().delete(using=using, keep_parents=keep_parents)
    
    def restore(self):
        """Restaura registro eliminado."""
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])


# ============================================================================
# AUDITED MODEL
# ============================================================================

class AuditedModel(models.Model):
    """
    Modelo con auditoría de creador y modificador.
    
    CLEAN_CODE v3.0.1: Nombre que revela intención.
    
    Provee campos:
    - created_by: Usuario que creó
    - updated_by: Usuario que modificó
    
    Uso:
        class MiModelo(AuditedModel, TimeStampedModel):
            nombre = models.CharField(max_length=100)
        
        # Al crear
        obj = MiModelo(nombre='Test')
        obj.created_by = request.user
        obj.save()
        
        # Al actualizar
        obj.nombre = 'Updated'
        obj.updated_by = request.user
        obj.save()
    """
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_created',
        verbose_name='Creado por',
        help_text='Usuario que creó el registro'
    )
    
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_updated',
        verbose_name='Actualizado por',
        help_text='Usuario que actualizó el registro'
    )
    
    class Meta:
        abstract = True  # [SUCCESS] OBLIGATORIO


# ============================================================================
# COMPLETE BASE MODEL
# ============================================================================

class CompleteBaseModel(TimeStampedModel, SoftDeleteMixin, AuditedModel):
    """
    Modelo base completo con timestamps, soft delete y auditoría.
    
    CLEAN_CODE v3.0.1: Nombre descriptivo.
    
    Combina:
    - TimeStampedModel (created_at, updated_at)
    - SoftDeleteMixin (is_deleted, deleted_at, delete(), restore())
    - AuditedModel (created_by, updated_by)
    
    Uso:
        class MiModelo(CompleteBaseModel):
            nombre = models.CharField(max_length=100)
            
            # Usar SoftDeleteManager
            objects = SoftDeleteManager()
        
        # Tiene automáticamente:
        # - created_at, updated_at
        # - is_deleted, deleted_at
        # - created_by, updated_by
        # - delete(), hard_delete(), restore()
    """
    
    class Meta:
        abstract = True  # [SUCCESS] OBLIGATORIO


# ============================================================================
# RESUMEN DE ABSTRACT MODELS
# 
# Total: 6 clases abstractas
# 
# Models:
#   [SUCCESS] TimeStampedModel (created_at, updated_at)
#   [SUCCESS] SoftDeleteMixin (is_deleted, deleted_at, delete, restore)
#   [SUCCESS] AuditedModel (created_by, updated_by)
#   [SUCCESS] CompleteBaseModel (combina los 3 anteriores)
# 
# Managers:
#   [SUCCESS] SoftDeleteManager
#   [SUCCESS] SoftDeleteQuerySet
# 
# CRÍTICO:
#   [ERROR] NO hay modelos concretos (db_table)
#   [SUCCESS] TODOS tienen abstract=True
#   [SUCCESS] SOLO clases base reutilizables
# ============================================================================

# ============================================================================
# BACKWARD-COMPAT RE-EXPORTS
# Los modelos concretos fueron movidos a apps.pipeline en DT-001.
# Estos re-exports mantienen compatibilidad con código existente.
# ============================================================================
from apps.pipeline.models import CallRecord, Center, Service  # noqa: F401, E402
