# Fixtures

Datos de prueba reutilizables.

## Uso
```python
from tests.fixtures.users import user_data

def test_example(user_data):
    assert user_data['username'] == 'testuser'
```
