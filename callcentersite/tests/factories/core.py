"""
Factories para modelos core.

FactoryBoy para generación de datos test.
"""
import factory
from datetime import date
from apps.pipeline.models import CallRecord, Center, Service


class CenterFactory(factory.django.DjangoModelFactory):
    """Factory para Center."""
    
    class Meta:
        model = Center
        django_get_or_create = ('codigo',)
    
    nombre = factory.Faker('company')
    codigo = factory.Sequence(lambda n: f'CTR{n:03d}')
    activo = True


class ServiceFactory(factory.django.DjangoModelFactory):
    """Factory para Service."""
    
    class Meta:
        model = Service
        django_get_or_create = ('numero_800',)
    
    numero_800 = factory.Sequence(lambda n: f'800{n:07d}')
    nombre = factory.Faker('catch_phrase')
    center = factory.SubFactory(CenterFactory)
    activo = True


class CallRecordFactory(factory.django.DjangoModelFactory):
    """Factory para CallRecord."""
    
    class Meta:
        model = CallRecord
    
    fecha = factory.LazyFunction(lambda: date(2024, 1, 15))
    telefono = factory.Sequence(lambda n: f'555{n:07d}')
    servicio_800 = factory.Sequence(lambda n: f'800{n:07d}')
    total_llamadas = factory.Faker('random_int', min=10, max=1000)
    
    @factory.lazy_attribute
    def llamadas_contestadas(self):
        """Contestadas <= total."""
        import random
        return random.randint(0, self.total_llamadas)
    
    @factory.lazy_attribute
    def llamadas_abandonadas(self):
        """Abandonadas = total - contestadas."""
        return self.total_llamadas - self.llamadas_contestadas
