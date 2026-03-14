# apps/utils/

**Versión:** 1.0.0  
**Última actualización:** FASE 3  
**Tipo:** Utilidades Puras (Sin DB)  

---

## 📋 DESCRIPCIÓN

`apps/utils/` contiene **funciones puras reutilizables** sin dependencias de base de datos.

**Principio:** Funciones simples, testeables, sin efectos secundarios.

---

## 🎯 RESPONSABILIDADES

```yaml
✅ SÍ (Utilidades Puras):
  - Validators (email, phone, RUT)
  - Formatters (phone, currency, dates)
  - Helpers (UUID, hashing, IP)
  - Date/String/Number utils
  - Decorators

❌ NO (Dependencias DB):
  - Queries a DB
  - Models
  - Managers
  - Servicios de negocio
```

---

## 📂 ESTRUCTURA

```
apps/utils/
├── __init__.py               # Exports
├── validators.py             # Funciones de validación
├── formatters.py             # Formateadores
├── helpers.py                # Helpers generales
├── date_utils.py             # Utilidades de fechas
├── string_utils.py           # Utilidades de strings
├── number_utils.py           # Utilidades de números
├── decorators.py             # Decorators reutilizables
├── constants.py              # Constantes del sistema
└── file_utils.py             # Utilidades de archivos
```

---

## ✅ VALIDATORS

### validate_email()

**Propósito:** Valida formato de email.

**Uso:**

```python
from apps.utils.validators import validate_email

assert validate_email('user@example.com') is True
assert validate_email('invalid.email') is False
```

**Regex:** `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`

---

### validate_phone_number() (CRÍTICO)

**Propósito:** Valida teléfonos chilenos.

**Usado en:** `User.phone` (apps/users/models.py)

**Formatos aceptados:**

```python
from apps.utils.validators import validate_phone_number

# Móvil (9 dígitos, empieza con 9)
assert validate_phone_number('912345678') is True
assert validate_phone_number('+56912345678') is True
assert validate_phone_number('9 1234 5678') is True

# Fijo (8 dígitos, empieza con 2-9)
assert validate_phone_number('223456789') is True
assert validate_phone_number('32345678') is True

# Inválidos
assert validate_phone_number('12345') is False
assert validate_phone_number('abc') is False
```

**Características:**
- Limpia espacios, guiones, +56
- Valida longitud (8 o 9 dígitos)
- Valida primer dígito

---

### validate_rut()

**Estado:** ⚠️ DEPRECADO (ver DT-004 en DEUDA_TECNICA.md)

---

### validate_service_800()

**Propósito:** Valida servicios 800.

**Uso:**

```python
from apps.utils.validators import validate_service_800

assert validate_service_800('8001234567') is True
assert validate_service_800('800-123-456') is True
assert validate_service_800('9001234567') is False  # No empieza con 800
```

---

### validate_codigo_center()

**Propósito:** Valida códigos de centro.

**Uso:**

```python
from apps.utils.validators import validate_codigo_center

assert validate_codigo_center('CTR001') is True
assert validate_codigo_center('CENTER_123') is True
```

---

### validate_date_range()

**Propósito:** Valida que start_date <= end_date.

**Uso:**

```python
from apps.utils.validators import validate_date_range
from datetime import date

start = date(2024, 1, 1)
end = date(2024, 1, 31)

validate_date_range(start, end)  # OK

# Si start > end → ValidationError
```

---

### validate_export_row_limit()

**Propósito:** Valida límite de filas en exports.

**Uso:**

```python
from apps.utils.validators import validate_export_row_limit

validate_export_row_limit(1000, max_limit=10000)  # OK
validate_export_row_limit(150000, max_limit=100000)  # ValidationError
```

---

## 🎨 FORMATTERS

### format_phone()

**Propósito:** Formatea teléfonos chilenos.

**Uso:**

```python
from apps.utils.formatters import format_phone

# Móvil
format_phone('912345678')
# → '+56 9 1234 5678' o '9 1234 5678'

# Fijo
format_phone('223456789')
# → '2 2345 6789'
```

---

### format_currency()

**Propósito:** Formatea moneda.

**Uso:**

```python
from apps.utils.formatters import format_currency

# CLP
format_currency(1000000, currency='CLP')
# → '$1.000.000' o '$1,000,000'

# USD
format_currency(1234.56, currency='USD')
# → '$1,234.56'

# Negativos
format_currency(-500, currency='CLP')
# → '-$500'
```

---

### format_percentage()

**Propósito:** Formatea porcentajes.

**Uso:**

```python
from apps.utils.formatters import format_percentage

format_percentage(0.75)
# → '75%' o '75.0%'

format_percentage(0.12345, decimals=2)
# → '12.35%'
```

---

### format_number()

**Propósito:** Formatea números con separador de miles.

**Uso:**

```python
from apps.utils.formatters import format_number

format_number(1000000)
# → '1.000.000' o '1,000,000'

format_number(1234.56, decimals=2)
# → '1,234.56'
```

---

### truncate_text()

**Propósito:** Trunca texto largo.

**Uso:**

```python
from apps.utils.formatters import truncate_text

truncate_text('This is a very long text...', max_length=10)
# → 'This is a...'
```

---

## 🔧 HELPERS

### get_client_ip() (CRÍTICO)

**Propósito:** Obtiene IP del cliente.

**Usado en:** `apps/users/signals.py` (log_user_login)

**Uso:**

```python
from apps.utils.helpers import get_client_ip

def my_view(request):
    ip = get_client_ip(request)
    print(f"IP: {ip}")
```

**Priority:**
1. `HTTP_X_FORWARDED_FOR` (primera IP)
2. `REMOTE_ADDR`
3. `HTTP_X_REAL_IP`

**Soporte IPv6:** ✅

---

### generate_uuid()

**Propósito:** Genera UUID4.

**Uso:**

```python
from apps.utils.helpers import generate_uuid

uuid = generate_uuid()
# → '550e8400-e29b-41d4-a716-446655440000'
```

---

### generate_short_uuid()

**Propósito:** Genera UUID corto.

**Uso:**

```python
from apps.utils.helpers import generate_short_uuid

short_uuid = generate_short_uuid(length=8)
# → 'a3f9b2c1'
```

---

### hash_string()

**Propósito:** Hash de string.

**Uso:**

```python
from apps.utils.helpers import hash_string

# SHA256 (default)
hashed = hash_string('password123')
# → '64 chars hex'

# MD5
hashed = hash_string('text', algorithm='md5')
# → '32 chars hex'
```

---

### generate_random_token()

**Propósito:** Token aleatorio.

**Uso:**

```python
from apps.utils.helpers import generate_random_token

token = generate_random_token(length=32)
# → 'a3f9b2c1d4e5f6g7...' (32 chars)
```

---

### safe_get()

**Propósito:** Acceso seguro a dicts anidados.

**Uso:**

```python
from apps.utils.helpers import safe_get

data = {'user': {'profile': {'name': 'John'}}}

name = safe_get(data, 'user', 'profile', 'name')
# → 'John'

email = safe_get(data, 'user', 'email', default='N/A')
# → 'N/A'
```

---

### merge_dicts()

**Propósito:** Merge múltiples dicts.

**Uso:**

```python
from apps.utils.helpers import merge_dicts

dict1 = {'a': 1, 'b': 2}
dict2 = {'c': 3}
dict3 = {'d': 4}

merged = merge_dicts(dict1, dict2, dict3)
# → {'a': 1, 'b': 2, 'c': 3, 'd': 4}
```

---

### chunk_list()

**Propósito:** Divide lista en chunks.

**Uso:**

```python
from apps.utils.helpers import chunk_list

items = [1, 2, 3, 4, 5, 6]
chunks = chunk_list(items, chunk_size=2)
# → [[1, 2], [3, 4], [5, 6]]
```

---

### flatten_list()

**Propósito:** Aplana lista anidada.

**Uso:**

```python
from apps.utils.helpers import flatten_list

nested = [[1, 2], [3, 4], [5]]
flat = flatten_list(nested)
# → [1, 2, 3, 4, 5]
```

---

### str_to_bool()

**Propósito:** Convierte string a bool.

**Uso:**

```python
from apps.utils.helpers import str_to_bool

assert str_to_bool('true') is True
assert str_to_bool('1') is True
assert str_to_bool('yes') is True
assert str_to_bool('false') is False
assert str_to_bool('0') is False
```

---

## 📅 DATE UTILS

### parse_date()

```python
from apps.utils import date_utils

date = date_utils.parse_date('2024-01-15')
# → date(2024, 1, 15)
```

### format_date()

```python
date = date(2024, 1, 15)
formatted = date_utils.format_date(date)
# → '2024-01-15' o '15/01/2024'
```

### is_weekend()

```python
saturday = date(2024, 1, 6)
assert date_utils.is_weekend(saturday) is True
```

### add_business_days()

```python
monday = date(2024, 1, 1)
next_week = date_utils.add_business_days(monday, 5)
# → Monday siguiente (skip weekends)
```

---

## 🔤 STRING UTILS

### slugify()

```python
from apps.utils import string_utils

slug = string_utils.slugify('Hello World!')
# → 'hello-world'
```

### sanitize_string()

```python
clean = string_utils.sanitize_string('<script>alert("XSS")</script>')
# → 'alert("XSS")' (remove tags)
```

### remove_accents()

```python
clean = string_utils.remove_accents('café résumé')
# → 'cafe resume'
```

---

## 🔢 NUMBER UTILS

### parse_number()

```python
from apps.utils import number_utils

num = number_utils.parse_number('123.45')
# → 123.45 (float)
```

### clamp_number()

```python
clamped = number_utils.clamp_number(150, min_val=0, max_val=100)
# → 100
```

### percentage_change()

```python
change = number_utils.percentage_change(old_value=100, new_value=150)
# → 50.0 (50% increase)
```

---

## 📊 TESTING

### Tests Disponibles

```bash
# Tests completos (117 tests)
pytest tests/unit/utils/ -v

# Tests por archivo
pytest tests/unit/utils/test_validators.py -v     # 38 tests
pytest tests/unit/utils/test_helpers.py -v        # 40 tests
pytest tests/unit/utils/test_formatters.py -v     # 17 tests
pytest tests/unit/utils/test_utils_misc.py -v     # 22 tests

# Coverage
pytest tests/unit/utils/ --cov=apps/utils --cov-report=html
```

### Coverage

```yaml
Objetivo: 95%+
  - Validators: 95%+
  - Helpers: 95%+
  - Formatters: 95%+
  - Utils: 95%+
```

---

## 💡 BEST PRACTICES

### DO (✅)

```python
# Funciones puras
def validate_email(email: str) -> bool:
    # Sin DB, sin side effects
    return bool(re.match(pattern, email))

# Tipado claro
def format_currency(amount: float, currency: str = 'CLP') -> str:
    pass

# Defaults razonables
def truncate_text(text: str, max_length: int = 100) -> str:
    pass
```

### DON'T (❌)

```python
# NO usar DB
def validate_user(user_id):
    user = User.objects.get(id=user_id)  # ❌
    
# NO side effects
def log_and_validate(email):
    logger.info(email)  # ❌ Side effect
    return validate_email(email)

# NO lógica compleja
def complex_business_logic():
    # Esto va en services ❌
    pass
```

---

## 🔄 DEPENDENCIAS

### apps/utils/ DEPENDE DE:

```yaml
✅ Python stdlib (re, datetime, etc)
✅ NADA MÁS (sin Django, sin DB)
```

### DEPENDIENTES DE apps/utils/:

```yaml
✅ apps/core/
✅ apps/users/
✅ apps/authentication/
✅ apps/pipeline/
✅ apps/reports/
✅ TODOS los apps
```

**Importante:** apps/utils/ es **nivel 1** (fundación pura, sin dependencias).

---

## 📚 VER TAMBIÉN

- [apps/core/README.md](../core/README.md) - Infraestructura base
- [INTEGRATION_GUIDE_CORE.md](../../docs/INTEGRATION_GUIDE_CORE.md) - Guía de integración
- [DEUDA_TECNICA.md](../../docs/DEUDA_TECNICA.md) - Deuda técnica

---

## 📋 CHANGELOG

### v1.0.0 (FASE 3)
- ✅ Tests: 117 tests creados (95%+ coverage)
- ✅ Docs: README completo
- ⚠️ Deprecado: validate_rut (DT-004)

---

**Mantenido por:** IACT Development Team  
**Última actualización:** 2026-01-21 (FASE 3 PARTE 4)
