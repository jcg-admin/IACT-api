"""
Test simple para verificar factories y base de datos.

OBJETIVO: Verificar que factories, fixtures y DB funcionan correctamente.
"""

import pytest
import factory
from django.contrib.auth import get_user_model

User = get_user_model()


# Factory simple inline
class SimpleUserTestData(factory.django.DjangoModelFactory):
    """Factory simple para User."""
    
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f'testuser{n}')
    email = factory.Faker('email')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')


@pytest.mark.unit
@pytest.mark.django_db
class TestFactoriesAndDatabase:
    """Tests para verificar factories y base de datos."""
    
    def test_create_user_with_factory(self):
        """Factory crea usuario en DB."""
        user = SimpleUserTestData(username='alice')
        
        assert user.id is not None
        assert user.username == 'alice'
        
        # Verificar que está en DB
        retrieved = User.objects.get(id=user.id)
        assert retrieved.username == 'alice'
    
    def test_create_multiple_users(self):
        """Batch creation funciona."""
        users = SimpleUserTestData.create_batch(3)
        
        assert len(users) == 3
        assert User.objects.count() >= 3
    
    def test_query_users(self):
        """Queries a DB funcionan."""
        SimpleUserTestData(username='bob', email='bob@test.com')
        SimpleUserTestData(username='charlie', email='charlie@test.com')
        
        # Count
        assert User.objects.count() >= 2
        
        # Filter
        test_users = User.objects.filter(email__contains='test.com')
        assert test_users.count() >= 2
        
        # Get
        bob = User.objects.get(username='bob')
        assert bob.email == 'bob@test.com'
    
    def test_update_user(self):
        """Update funciona."""
        user = SimpleUserTestData(username='john', email='old@test.com')
        
        user.email = 'new@test.com'
        user.save()
        
        updated = User.objects.get(username='john')
        assert updated.email == 'new@test.com'
    
    def test_delete_user(self):
        """Delete funciona (soft delete)."""
        user = SimpleUserTestData(username='temp')
        user_id = user.id
        
        assert User.objects.filter(id=user_id).exists()
        
        # Soft delete
        user.delete()
        
        # Usuario sigue existiendo pero marcado como deleted
        user_deleted = User.objects.get(id=user_id)
        assert user_deleted.is_deleted == True
        
        # Para hard delete:
        # user.hard_delete()
        # assert not User.objects.filter(id=user_id).exists()


@pytest.mark.unit
@pytest.mark.django_db
class TestDatabaseTransactions:
    """Tests para verificar transacciones."""
    
    def test_transaction_isolation(self):
        """Cada test está aislado."""
        SimpleUserTestData(username='isolated_test')
        
        # Este usuario existe en este test
        assert User.objects.filter(username='isolated_test').exists()
        
        # Pero será rollback al terminar
    
    def test_no_data_from_previous_test(self):
        """No hay datos del test anterior."""
        # isolated_test del test anterior no existe aquí
        assert not User.objects.filter(username='isolated_test').exists()


# ============================================================================
# RESUMEN
# 
# Tests: 7
# Objetivo: Verificar factories, queries y transacciones [SUCCESS]
# ============================================================================
