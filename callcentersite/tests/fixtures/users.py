"""
Fixtures de usuarios para el modelo CustomUser.
Optimizado para: Modelos, APIs de Perfil/Avatar, Serializadores y Vistas.
Ubicación: tests/fixtures/users.py
"""
import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

# Referencia dinámica al CustomUser (users.CustomUser)
User = get_user_model()

@pytest.fixture
def user_data():
    """
    Diccionario de datos planos.
    Ideal para: Validar UserCreateSerializer sin guardar en DB.
    Es util para los test de serializers
    """
    return {
        'username': 'newuser',
        'email': 'new@example.com',
        'password': 'testpass123',
        'first_name': 'Test',
        'last_name': 'User',
        'phone': '+56912345678',
        'position': 'Developer',
        'employee_id': 'IACT-001'
    }

@pytest.fixture
def user_factory(db):
    """
    Factory para crear instancias reales de CustomUser en la DB.
    Permite evitar colisiones de username en tests que requieren múltiples usuarios.
    """
    def _make_user(username='testuser', **kwargs):
        if 'email' not in kwargs:
            kwargs['email'] = f'{username}@example.com'

        password = kwargs.pop('password', 'testpass123')

        # Filtrar campos que no existen en el modelo User actual
        valid_fields = {f.name for f in User._meta.fields}
        valid_fields.update({'state', 'first_login', 'phone'})
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_fields}

        user = User.objects.create_user(username=username, **filtered_kwargs)
        user.set_password(password)
        user.save()
        return user
    return _make_user

@pytest.fixture
def basic_user(user_factory):
    """Usuario estándar (instancia de base de datos)."""
    return user_factory(username='basicuser')

@pytest.fixture
def admin_user(db):
    """
    Superusuario administrador.
    Nota: Mantiene la compatibilidad con tu lógica original.
    """
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='admin123'
    )

@pytest.fixture
def user_with_profile(user_factory):
    """
    Usuario con perfil completo.
    Ideal para: tests de GET/PUT en la API de perfil.
    """
    return user_factory(
        username='juan_perez',
        first_name='Juan',
        last_name='Perez',
        phone='+56912345678',
        # position y employee_id no existen en el modelo User
    )

@pytest.fixture
def valid_avatar_file():
    """
    Archivo de imagen real mínimo en memoria.
    Evita repetir la creación de SimpleUploadedFile en test_avatar_api.py.
    """
    return SimpleUploadedFile(
        name='avatar.jpg',
        content=(
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x05\x04\x04'
            b'\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44'
            b'\x01\x00\x3b'
        ),
        content_type='image/jpeg'
    )

@pytest.fixture
def user_with_avatar(user_factory, valid_avatar_file):
    """Usuario que ya tiene un avatar asignado y guardado en disco."""
    return user_factory(username='avataruser', avatar=valid_avatar_file)

@pytest.fixture
def deleted_user(user_factory):
    """
    Usuario con Soft Delete aplicado.
    Ideal para: Probar que el Mixin de borrado lógico funciona.
    """
    user = user_factory(username='deleteduser')
    user.delete() # Llama al soft delete de SoftDeleteMixin
    return user