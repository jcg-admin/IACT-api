"""
Utilidades reutilizables para modelos Django.

Incluye:
- SoftDeleteQuerySet: QuerySet con soporte para delete lógico
- SoftDeleteManager: Manager para modelos con delete lógico
- SoftDeleteMixin: Mixin para agregar funcionalidad de delete lógico
"""
from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    """
    QuerySet personalizado con soporte para delete lógico.
    
    Filtra automáticamente registros eliminados (is_deleted=True)
    a menos que se use all_with_deleted() explícitamente.
    """
    
    def delete(self):
        """
        Delete lógico masivo.
        
        Marca todos los objetos del queryset como eliminados
        en lugar de eliminarlos físicamente.
        
        Returns:
            tuple: (count, dict) número de objetos actualizados
        """
        count = self.update(
            is_deleted=True,
            deleted_at=timezone.now()
        )
        return (count, {'updated': count})
    
    def hard_delete(self):
        """
        Delete físico masivo.
        
        Elimina permanentemente todos los objetos del queryset.
        
        Returns:
            tuple: (count, dict) número de objetos eliminados
        """
        return super().delete()
    
    def alive(self):
        """
        Filtrar solo registros no eliminados.
        
        Returns:
            QuerySet: Registros con is_deleted=False
        """
        return self.filter(is_deleted=False)
    
    def deleted(self):
        """
        Filtrar solo registros eliminados.
        
        Returns:
            QuerySet: Registros con is_deleted=True
        """
        return self.filter(is_deleted=True)
    
    def all_with_deleted(self):
        """
        Obtener todos los registros incluyendo eliminados.
        
        Returns:
            QuerySet: Todos los registros sin filtrar
        """
        return self.all()


class SoftDeleteManager(models.Manager):
    """
    Manager personalizado para modelos con delete lógico.
    
    Automáticamente excluye registros eliminados del queryset
    por defecto. Provee métodos para acceder a todos los registros
    si es necesario.
    """
    
    def get_queryset(self):
        """
        Queryset por defecto (sin eliminados).
        
        Returns:
            SoftDeleteQuerySet: Registros no eliminados
        """
        return SoftDeleteQuerySet(self.model, using=self._db).filter(
            is_deleted=False
        )
    
    def all_with_deleted(self):
        """
        Obtener todos los registros incluyendo eliminados.
        
        Returns:
            SoftDeleteQuerySet: Todos los registros
        """
        return SoftDeleteQuerySet(self.model, using=self._db)
    
    def deleted_only(self):
        """
        Obtener solo registros eliminados.
        
        Returns:
            SoftDeleteQuerySet: Solo registros eliminados
        """
        return SoftDeleteQuerySet(self.model, using=self._db).filter(
            is_deleted=True
        )


class SoftDeleteMixin(models.Model):
    """
    Mixin para agregar funcionalidad de delete lógico a modelos.
    
    Agrega campos:
    - is_deleted: bool indicando si está eliminado
    - deleted_at: timestamp de cuándo se eliminó
    
    Agrega métodos:
    - delete(): Delete lógico (marca como eliminado)
    - hard_delete(): Delete físico (elimina de DB)
    - restore(): Restaurar registro eliminado
    
    Uso:
        class MyModel(SoftDeleteMixin):
            # tus campos
            pass
        
        obj = MyModel.objects.create(name='test')
        obj.delete()  # Delete lógico
        obj.restore()  # Restaurar
        obj.hard_delete()  # Delete físico
    """
    
    is_deleted = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Indica si el registro está eliminado (delete lógico)"
    )
    
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora en que se eliminó el registro"
    )
    
    objects = SoftDeleteManager()
    
    class Meta:
        abstract = True
    
    def delete(self, using=None, keep_parents=False):
        """
        Delete lógico.
        
        Marca el registro como eliminado en lugar de eliminarlo
        físicamente de la base de datos.
        
        Args:
            using: Base de datos a usar (opcional)
            keep_parents: Mantener registros padre (opcional)
        
        Returns:
            tuple: (1, {'updated': 1})
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(using=using)
        return (1, {'updated': 1})
    
    def hard_delete(self, using=None, keep_parents=False):
        """
        Delete físico.
        
        Elimina permanentemente el registro de la base de datos.
        
        Args:
            using: Base de datos a usar (opcional)
            keep_parents: Mantener registros padre (opcional)
        
        Returns:
            tuple: (count, dict) número de objetos eliminados
        """
        return super().delete(using=using, keep_parents=keep_parents)
    
    def restore(self):
        """
        Restaurar registro eliminado.
        
        Marca el registro como no eliminado, permitiendo que
        vuelva a aparecer en las consultas normales.
        
        Returns:
            None
        """
        self.is_deleted = False
        self.deleted_at = None
        self.save()
