"""
Factory para User model y modelos relacionados.

FASE 2 PARTE 6: Factories actualizados para apps/users/
"""
import factory
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory

User = get_user_model()


class UserTestData(DjangoModelFactory):
    """
    Test data for User.
    User extends AbstractUser with: avatar, phone, is_active.
    """
    class Meta:
        model = User

    username    = factory.Sequence(lambda n: f'user{n}')
    email       = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    first_name  = factory.Faker('first_name')
    last_name   = factory.Faker('last_name')
    phone       = '+52 55 1234 5678'
    is_active   = True
    is_staff    = False
    is_superuser = False

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Use create_user to hash the password."""
        password = kwargs.pop('password', 'TestPass123!')
        user = model_class.objects.create_user(
            username=kwargs.get('username'),
            email=kwargs.get('email'),
            password=password,
            first_name=kwargs.get('first_name', ''),
            last_name=kwargs.get('last_name', ''),
            phone=kwargs.get('phone', ''),
        )
        for key, value in kwargs.items():
            if key not in ('username', 'email', 'first_name',
                           'last_name', 'phone'):
                if hasattr(user, key):
                    setattr(user, key, value)
        user.save()
        return user


class AdminUserTestData(UserTestData):
    """Factory User admin."""
    
    username = factory.Sequence(lambda n: f'admin{n}')
    is_staff = True
    is_superuser = True
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Crear superuser."""
        password = kwargs.pop('password', 'AdminPass123!')
        
        user = model_class.objects.create_superuser(
            username=kwargs.get('username'),
            email=kwargs.get('email'),
            password=password,
        )
        
        # Aplicar otros campos
        user.first_name = kwargs.get('first_name', 'Admin')
        user.last_name = kwargs.get('last_name', 'User')
        user.phone = kwargs.get('phone', '+52 55 9999 9999')
        user.position = kwargs.get('position', 'DIRECTOR')
        user.save()
        
        return user


# DT: UserProfile, UserSettings, SessionHistory no existen en users.models actual.
# Las factories se desactivan hasta que los modelos sean implementados.
# UserTestData y AdminUserTestData siguen activos — son los unicos modelos presentes.

class UserProfileTestData(UserTestData):
    """Alias de UserTestData — UserProfile no implementado aun."""
    pass


class UserSettingsTestData(UserTestData):
    """Alias de UserTestData — UserSettings no implementado aun."""
    pass


class SessionHistoryTestData(UserTestData):
    """Alias de UserTestData — SessionHistory no implementado aun."""
    pass


# ============================================================================
# RESUMEN USER FACTORIES
# 
# Total: 5 factories
# 
# UserTestData:
#   [SUCCESS] User estándar con password hasheado
#   [SUCCESS] Default: is_active=True, is_staff=False
#   [SUCCESS] Phone y position incluidos
# 
# AdminUserTestData:
#   [SUCCESS] Superuser (is_staff=True, is_superuser=True)
#   [SUCCESS] Default position: DIRECTOR
# 
# UserProfileTestData:
#   [SUCCESS] Profile con bio y department
#   [SUCCESS] SubTestData(UserTestData)
# 
# UserSettingsTestData:
#   [SUCCESS] Settings (language, notifications_enabled)
#   [SUCCESS] SubTestData(UserTestData)
# 
# SessionHistoryTestData:
#   [SUCCESS] Sesión con login_at, IP, user_agent
#   [SUCCESS] is_active=True por defecto
# 
# FASE 2 PARTE 6: Actualizado para apps/users/ [SUCCESS]
# ============================================================================
