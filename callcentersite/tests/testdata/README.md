# Factories

Factories para crear objetos de prueba con FactoryBoy.

## Ejemplo
```python
from tests.factories import UserFactory

def test_example():
    user = UserFactory(username='test')
    assert user.username == 'test'
```

## TODO
Implementar factories en Sprint 4 usando FactoryBoy.
