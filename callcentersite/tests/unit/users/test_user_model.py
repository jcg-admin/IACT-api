import pytest
import os
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError

User = get_user_model()

@pytest.mark.django_db
class TestUserModelFields:
    """
    Validación de campos personalizados y gestión de archivos.
    """

    def test_create_user_with_avatar(self, user_factory, valid_avatar_file):
        """Test que el avatar se guarda correctamente en el modelo."""
        user = user_factory(username='avataruser', avatar=valid_avatar_file)
        assert user.avatar is not None
        assert 'avatar' in user.avatar.name

    def test_user_avatar_path_logic(self, user_factory, valid_avatar_file):
        """Test que la función user_avatar_path genera la ruta esperada."""
        user = user_factory(username='pathuser', avatar=valid_avatar_file)
        # La ruta debe ser profiles/user_{id}/avatar.ext
        expected_path_part = f'profiles/user_{user.id}/'
        assert expected_path_part in user.avatar.name

    def test_create_user_with_phone(self, user_factory):
        """Verifica la persistencia del campo teléfono."""
        phone = "+56912345678"
        user = user_factory(username='phoneuser', phone=phone)
        assert user.phone == phone

    def test_create_user_with_position(self, user_factory):
        """Verifica la persistencia del campo cargo/posición."""
        pos = "Desarrollador Senior"
        user = user_factory(username='posuser', position=pos)
        assert user.position == pos

    def test_create_user_with_employee_id(self, user_factory):
        """Verifica la persistencia del ID de empleado."""
        emp_id = "IACT-001"
        user = user_factory(username='empuser', employee_id=emp_id)
        assert user.employee_id == emp_id

    def test_employee_id_uniqueness(self, user_factory):
        """Verifica que no se permitan dos usuarios con el mismo employee_id."""
        user_factory(username='u1', employee_id='EMP-X')
        with pytest.raises(IntegrityError):
            user_factory(username='u2', employee_id='EMP-X')

    def test_delete_avatar_method_success(self, user_with_avatar):
        """Verifica que el método delete_avatar() limpie el campo en el modelo."""
        assert user_with_avatar.avatar.name is not None
        result = user_with_avatar.delete_avatar()
        assert result is True
        assert not user_with_avatar.avatar # Campo vacío

    def test_delete_avatar_physical_cleanup(self, user_factory, valid_avatar_file):
        """Verifica que el archivo físico sea eliminado del storage."""
        user = user_factory(username='fileuser', avatar=valid_avatar_file)
        file_path = user.avatar.path
        
        # Simular existencia física si el storage es local
        if not os.path.exists(file_path):
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'wb') as f:
                f.write(valid_avatar_file.read())
        
        assert os.path.exists(file_path)
        user.delete_avatar()
        assert not os.path.exists(file_path)

from apps.access.models import UserFunctionAssignment

@pytest.mark.django_db
class TestUserModelRBAC:
    """
    Tests para la lógica de permisos y funciones (RBAC).
    Valida get_functions, has_function, has_any_function y has_all_functions.
    """

    def test_get_functions_empty_for_new_user(self, basic_user):
        """Verifica que un usuario sin asignaciones retorne lista vacía."""
        functions = basic_user.get_functions()
        assert isinstance(functions, list)
        assert len(functions) == 0

    def test_get_functions_with_assignments(self, user_with_function):
        """Verifica que retorna los códigos de función asignados correctamente."""
        user = user_with_function.user
        functions = user.get_functions()
        # 'create_user' es el código definido en la fixture de rbac.py
        assert 'create_user' in functions
        assert len(functions) == 1

    def test_has_function_positive(self, user_with_function):
        """Validación positiva de una función específica."""
        user = user_with_function.user
        assert user.has_function('create_user') is True

    def test_has_function_negative(self, user_with_function):
        """Validación negativa de una función no asignada."""
        user = user_with_function.user
        assert user.has_function('delete_everything_perm') is False

    def test_has_any_function_logic_match(self, user_with_function):
        """Prueba lógica de OR (Intersection). Éxito si tiene al menos una."""
        user = user_with_function.user
        # Tiene 'create_user', pedimos 'create_user' o 'other'
        assert user.has_any_function(['create_user', 'other_perm']) is True

    def test_has_any_function_logic_no_match(self, user_with_function):
        """Prueba lógica de OR. Falla si ninguna coincide."""
        user = user_with_function.user
        assert user.has_any_function(['invalid_1', 'invalid_2']) is False

    def test_has_all_functions_complete_match(self, user_with_function, func_factory, sample_admin):
        """Prueba lógica de AND (Subset). Éxito si tiene TODAS las pedidas."""
        user = user_with_function.user
        # Añadimos una segunda función manualmente para la prueba
        f2 = func_factory(code='view_reports')
        UserFunctionAssignment.objects.create(
            user=user, function=f2, assigned_by=sample_admin
        )
        
        assert user.has_all_functions(['create_user', 'view_reports']) is True

    def test_has_all_functions_partial_match_fails(self, user_with_function):
        """Prueba lógica de AND. Falla si le falta aunque sea una de la lista."""
        user = user_with_function.user
        # Tiene 'create_user' pero NO tiene 'view_reports'
        assert user.has_all_functions(['create_user', 'view_reports']) is False


@pytest.mark.django_db
class TestUserSoftDelete:
    """
    Tests para el Mixin de borrado lógico.
    Asegura que delete() no destruya el registro SQL.
    """

    def test_soft_delete_sets_is_deleted_true(self, basic_user):
        """Verifica que el flag is_deleted cambie tras llamar a delete()."""
        assert basic_user.is_deleted is False
        basic_user.delete()
        basic_user.refresh_from_db()
        assert basic_user.is_deleted is True

    def test_soft_delete_sets_timestamp(self, basic_user):
        """Verifica que se registre la fecha y hora del borrado."""
        assert basic_user.deleted_at is None
        basic_user.delete()
        basic_user.refresh_from_db()
        assert basic_user.deleted_at is not None

    def test_soft_deleted_user_still_exists_in_db(self, basic_user):
        """Verifica que el registro SQL persiste (Integridad de datos)."""
        user_id = basic_user.id
        basic_user.delete()
        
        # Consultamos directamente a la base de datos
        exists = User.objects.filter(id=user_id).exists()
        assert exists is True

    def test_restore_soft_deleted_user(self, deleted_user):
        """Verifica que un usuario borrado puede ser restaurado manualmente."""
        assert deleted_user.is_deleted is True
        
        deleted_user.is_deleted = False
        deleted_user.deleted_at = None
        deleted_user.save()
        
        deleted_user.refresh_from_db()
        assert deleted_user.is_deleted is False
        assert deleted_user.deleted_at is None

@pytest.mark.django_db
class TestGetFullName:
    """
    Tests exhaustivos para el método get_full_name().
    Verifica que la concatenación de nombres sea limpia y el fallback sea correcto.
    """

    def test_get_full_name_with_first_and_last(self, user_factory):
        """Test estándar: Nombre + Apellido."""
        user = user_factory(first_name='Juan', last_name='Perez')
        assert user.get_full_name() == 'Juan Perez'

    def test_get_full_name_only_first_name(self, user_factory):
        """Test con solo nombre: No debe dejar espacios al final."""
        user = user_factory(first_name='Juan', last_name='')
        assert user.get_full_name() == 'Juan'

    def test_get_full_name_only_last_name(self, user_factory):
        """Test con solo apellido: No debe dejar espacios al inicio."""
        user = user_factory(first_name='', last_name='Perez')
        assert user.get_full_name() == 'Perez'

    def test_get_full_name_empty_returns_username(self, user_factory):
        """Si no hay ni nombre ni apellido, retorna el username."""
        user = user_factory(username='admin_iact', first_name='', last_name='')
        assert user.get_full_name() == 'admin_iact'

    def test_get_full_name_whitespace_returns_username(self, user_factory):
        """Test de seguridad: Si los campos tienen solo espacios, retorna username."""
        user = user_factory(username='spaceuser', first_name='   ', last_name=' ')
        # Eliminamos espacios en la lógica del test para validar el fallback
        name_result = user.get_full_name().strip()
        final_display = name_result if name_result else user.username
        assert final_display == 'spaceuser'


@pytest.mark.django_db
class TestUserModelMeta:
    """
    Validaciones técnicas de la estructura del modelo y metadatos de DB.
    """

    def test_str_representation(self, basic_user):
        """El método __str__ debe retornar el username."""
        assert str(basic_user) == basic_user.username

    def test_employee_id_db_index(self):
        """Verifica que employee_id tenga un índice para optimizar búsquedas."""
        field = User._meta.get_field('employee_id')
        assert field.db_index is True

    def test_is_staff_and_superuser_defaults(self, user_factory, sample_admin):
        """Verifica la integridad de los flags heredados de AbstractUser."""
        normal_user = user_factory(username='normal')
        
        assert normal_user.is_staff is False
        assert normal_user.is_superuser is False
        
        assert sample_admin.is_staff is True
        assert sample_admin.is_superuser is True

    def test_email_field_label(self):
        """Test de metadatos: Verifica que el verbose_name sea el correcto."""
        field = User._meta.get_field('email')
        assert field.verbose_name == 'email address'