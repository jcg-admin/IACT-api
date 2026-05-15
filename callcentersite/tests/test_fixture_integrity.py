"""Test fixtures funcionan correctamente."""
import pytest


@pytest.mark.unit
def test_user_data_fixture(user_data):
    """Fixture user_data funciona."""
    assert user_data['username'] == 'newuser'
    assert 'password' in user_data


@pytest.mark.unit
@pytest.mark.django_db
def test_basic_user_fixture(basic_user):
    """Fixture basic_user crea usuario."""
    assert basic_user.username == 'basicuser'
    assert not basic_user.is_superuser


@pytest.mark.unit
@pytest.mark.django_db
def test_admin_user_fixture(admin_user):
    """Fixture admin_user crea superuser."""
    assert admin_user.username == 'admin'
    assert admin_user.is_superuser


@pytest.mark.unit
@pytest.mark.django_db
def test_function_create_user_fixture(function_create_user):
    """Fixture function_create_user funciona."""
    assert function_create_user.code == 'create_user'
    assert function_create_user.name == 'Crear Usuario'
