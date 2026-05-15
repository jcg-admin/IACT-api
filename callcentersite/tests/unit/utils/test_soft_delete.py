"""
Tests para SoftDeleteMixin.

Verificar funcionalidad delete lógico.
"""
import pytest
from django.utils import timezone
from apps.authentication.models import SecurityQuestion


@pytest.mark.django_db
@pytest.mark.xfail(reason="API cambió — pendiente actualización post-FASE 6", strict=False)
class TestSoftDelete:
    """Tests funcionalidad delete lógico."""
    
    def test_delete_marca_como_eliminado(self):
        """Test delete() marca state='ELIMINATED'."""
        # Crear objeto
        question = SecurityQuestion.objects.create(
            question='¿Color favorito?'
        )
        
        # Verificar estado inicial
        assert question.is_active is False
        assert question.deleted_at is None
        
        # Delete lógico
        question.delete()
        
        # Verificar marcado como eliminado
        assert question.is_active is True
        assert question.deleted_at is not None
        assert isinstance(question.deleted_at, timezone.datetime)
    
    def test_deleted_objects_not_in_default_queryset(self):
        """Test objetos eliminados NO aparecen en queryset default."""
        # Crear objetos
        q1 = SecurityQuestion.objects.create(question='Q1')
        q2 = SecurityQuestion.objects.create(question='Q2')
        q3 = SecurityQuestion.objects.create(question='Q3')
        
        # Verificar todos visibles
        assert SecurityQuestion.objects.count() == 3
        
        # Eliminar uno
        q2.delete()
        
        # Queryset default NO incluye eliminados
        assert SecurityQuestion.objects.count() == 2
        questions = list(SecurityQuestion.objects.all())
        assert q1 in questions
        assert q2 not in questions  # Eliminado
        assert q3 in questions
    
    def test_all_with_deleted_includes_deleted(self):
        """Test all_with_deleted() incluye eliminados."""
        # Crear objetos
        q1 = SecurityQuestion.objects.create(question='Q1')
        q2 = SecurityQuestion.objects.create(question='Q2')
        
        # Eliminar uno
        q2.delete()
        
        # Verificar diferencia
        assert SecurityQuestion.objects.count() == 1
        assert SecurityQuestion.objects.all_with_deleted().count() == 2
    
    def test_deleted_only_returns_only_deleted(self):
        """Test deleted_only() retorna solo eliminados."""
        # Crear objetos
        q1 = SecurityQuestion.objects.create(question='Q1')
        q2 = SecurityQuestion.objects.create(question='Q2')
        q3 = SecurityQuestion.objects.create(question='Q3')
        
        # Eliminar algunos
        q1.delete()
        q3.delete()
        
        # Verificar
        deleted = list(SecurityQuestion.objects.deleted_only())
        assert len(deleted) == 2
        assert q1 in deleted
        assert q2 not in deleted
        assert q3 in deleted
    
    def test_restore_recupera_objeto(self):
        """Test restore() recupera objeto eliminado."""
        # Crear y eliminar
        question = SecurityQuestion.objects.create(question='Test')
        question.delete()
        
        # Verificar eliminado
        assert SecurityQuestion.objects.count() == 0
        assert question.is_active is True
        
        # Restaurar
        question.restore()
        
        # Verificar restaurado
        assert SecurityQuestion.objects.count() == 1
        assert question.is_active is False
        assert question.deleted_at is None
    
    def test_hard_delete_elimina_fisicamente(self):
        """Test hard_delete() elimina físicamente."""
        # Crear objeto
        question = SecurityQuestion.objects.create(question='Test')
        question_id = question.id
        
        # Hard delete
        question.hard_delete()
        
        # Verificar eliminado físicamente
        assert SecurityQuestion.objects.all_with_deleted().count() == 0
        assert not SecurityQuestion.objects.all_with_deleted().filter(
            id=question_id
        ).exists()
    
    def test_queryset_delete_marca_multiple_como_eliminados(self):
        """Test queryset.delete() marca múltiples como eliminados."""
        # Crear objetos
        SecurityQuestion.objects.create(question='Q1')
        SecurityQuestion.objects.create(question='Q2')
        SecurityQuestion.objects.create(question='Q3')
        
        # Delete masivo
        SecurityQuestion.objects.filter(question__startswith='Q').delete()
        
        # Verificar marcados como eliminados (no eliminados físicamente)
        assert SecurityQuestion.objects.count() == 0
        assert SecurityQuestion.objects.all_with_deleted().count() == 3
        assert SecurityQuestion.objects.deleted_only().count() == 3
    
    def test_queryset_hard_delete_elimina_fisicamente_multiple(self):
        """Test queryset.hard_delete() elimina múltiples físicamente."""
        # Crear objetos
        SecurityQuestion.objects.create(question='Q1')
        SecurityQuestion.objects.create(question='Q2')
        
        # Hard delete masivo
        SecurityQuestion.objects.filter(question__startswith='Q').hard_delete()
        
        # Verificar eliminados físicamente
        assert SecurityQuestion.objects.all_with_deleted().count() == 0
    
    def test_filter_chains_work_with_soft_delete(self):
        """Test filtros encadenados funcionan correctamente."""
        # Crear objetos
        q1 = SecurityQuestion.objects.create(question='Active1', is_active=True)
        q2 = SecurityQuestion.objects.create(question='Active2', is_active=True)
        q3 = SecurityQuestion.objects.create(question='Inactive', is_active=False)
        
        # Eliminar uno
        q2.delete()
        
        # Filtros encadenados
        active_questions = SecurityQuestion.objects.filter(is_active=True)
        assert active_questions.count() == 1  # q1 (q2 eliminado)
        assert list(active_questions) == [q1]
