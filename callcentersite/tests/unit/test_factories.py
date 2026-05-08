"""Test factories funcionan."""
import pytest
from tests.test_data.user_test_data import UserTestData, AdminUserTestData


@pytest.mark.unit
@pytest.mark.django_db
class TestUserTestData:
    """Test UserTestData."""
    
    def test_create_user(self):
        """Crear usuario con factory."""
        user = UserTestData()
        
        assert user.id is not None
        assert user.username.startswith('user')
        assert '@example.com' in user.email
        assert user.first_name  # Faker genera nombre
    
    def test_create_multiple_users(self):
        """Crear múltiples usuarios."""
        users = UserTestData.create_batch(5)
        
        assert len(users) == 5
        # Usernames únicos
        usernames = [u.username for u in users]
        assert len(set(usernames)) == 5
    
    def test_create_with_custom_values(self):
        """Crear usuario con valores custom."""
        user = UserTestData(
            username='customuser',
            email='custom@test.com',
            first_name='Custom'
        )
        
        assert user.username == 'customuser'
        assert user.email == 'custom@test.com'
        assert user.first_name == 'Custom'
    
    def test_create_admin(self):
        """Crear admin con factory."""
        admin = AdminUserTestData()
        
        assert admin.is_superuser
        assert admin.is_staff
        assert admin.username.startswith('admin')
