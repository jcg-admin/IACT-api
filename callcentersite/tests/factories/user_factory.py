"""
Factory para User model y modelos relacionados.

FASE 2 PARTE 6: Factories actualizados para apps/users/
"""
import factory
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory

User = get_user_model()


class UserFactory(DjangoModelFactory):
    """Factory User básico."""
    
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    phone = '+52 55 1234 5678'
    position = 'ANALYST'
    is_active = True
    is_staff = False
    is_superuser = False
    
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override para usar create_user (hashea password)."""
        password = kwargs.pop('password', 'TestPass123!')
        user = model_class.objects.create_user(
            username=kwargs.get('username'),
            email=kwargs.get('email'),
            password=password,
            first_name=kwargs.get('first_name', ''),
            last_name=kwargs.get('last_name', ''),
            phone=kwargs.get('phone'),
            position=kwargs.get('position', 'ANALYST'),
        )
        
        # Aplicar otros campos si existen
        for key, value in kwargs.items():
            if key not in ['username', 'email', 'first_name', 'last_name', 'phone', 'position']:
                setattr(user, key, value)
        
        user.save()
        return user


class AdminUserFactory(UserFactory):
    """Factory User admin."""
    
    username = factory.Sequence(lambda n: f'admin{n}')
    is_staff = True
    is_superuser = True
    position = 'DIRECTOR'
    
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


class UserProfileFactory(DjangoModelFactory):
    """Factory para UserProfile."""
    
    class Meta:
        model = 'users.UserProfile'
    
    user = factory.SubFactory(UserFactory)
    bio = factory.Faker('text', max_nb_chars=200)
    department = 'IT'


class UserSettingsFactory(DjangoModelFactory):
    """Factory para UserSettings."""
    
    class Meta:
        model = 'users.UserSettings'
    
    user = factory.SubFactory(UserFactory)
    language = 'es'
    notifications_enabled = True


class SessionHistoryFactory(DjangoModelFactory):
    """Factory para SessionHistory."""
    
    class Meta:
        model = 'users.SessionHistory'
    
    user = factory.SubFactory(UserFactory)
    login_at = factory.Faker('date_time_this_month')
    logout_at = None  # Sesión activa por defecto
    ip_address = factory.Faker('ipv4')
    user_agent = factory.Faker('user_agent')
    is_active = True


# ============================================================================
# RESUMEN USER FACTORIES
# 
# Total: 5 factories
# 
# UserFactory:
#   [SUCCESS] User estándar con password hasheado
#   [SUCCESS] Default: is_active=True, is_staff=False
#   [SUCCESS] Phone y position incluidos
# 
# AdminUserFactory:
#   [SUCCESS] Superuser (is_staff=True, is_superuser=True)
#   [SUCCESS] Default position: DIRECTOR
# 
# UserProfileFactory:
#   [SUCCESS] Profile con bio y department
#   [SUCCESS] SubFactory(UserFactory)
# 
# UserSettingsFactory:
#   [SUCCESS] Settings (language, notifications_enabled)
#   [SUCCESS] SubFactory(UserFactory)
# 
# SessionHistoryFactory:
#   [SUCCESS] Sesión con login_at, IP, user_agent
#   [SUCCESS] is_active=True por defecto
# 
# FASE 2 PARTE 6: Actualizado para apps/users/ [SUCCESS]
# ============================================================================
