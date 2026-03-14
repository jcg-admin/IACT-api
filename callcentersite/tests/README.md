# Estructura de Tests - IACT Call Center System

## 📁 Organización Híbrida

Este proyecto usa una **organización híbrida** de tests, siguiendo las mejores prácticas de Django/DRF:

```
callcentersite/
├── tests/                          # ← TESTS CENTRALIZADOS
│   ├── conftest.py                # Fixtures compartidos globales
│   ├── unit/                      # Tests unitarios cross-app
│   ├── integration/               # Tests de integración
│   ├── api/                       # Tests API REST (endpoints)
│   └── fixtures/                  # Fixtures y factories
│
└── apps/
    ├── authentication/tests/      # ← Tests específicos de auth
    ├── users/tests/               # ← Tests específicos de users
    ├── access/tests/              # ← Tests específicos de access
    ├── audit/tests/               # ← Tests específicos de audit
    └── core/tests/                # ← Tests específicos de core
```

---

## 🎯 ¿Dónde poner cada test?

### Tests en `apps/*/tests/` (Tests Unitarios App-específicos)

Coloca aquí tests que:
-  Son específicos de UNA sola app
-  Prueban modelos, serializers, services de esa app
-  No requieren múltiples apps funcionando juntas
-  Son rápidos y aislados

**Ejemplos:**
```python
# apps/authentication/tests/test_models.py
def test_user_creation():
    user = User.objects.create_user(...)
    assert user.is_active

# apps/access/tests/test_services.py
def test_module_access_service():
    service = ModuleAccessService()
    assert service.get_user_modules(user)
```

### Tests en `tests/` (Tests Centralizados)

Coloca aquí tests que:
-  Cruzan múltiples apps
-  Tests de integración
-  Tests API/endpoints completos
-  Tests E2E (flujos completos)

**Ejemplos:**
```python
# tests/api/test_access_api.py
def test_my_modules_endpoint(authenticated_client):
    """Test que combina auth + access + módulos"""
    response = authenticated_client.get('/api/v1/access/my-modules/')
    assert response.status_code == 200

# tests/integration/test_auth_flow.py
def test_complete_login_flow():
    """Test login → obtener módulos → acceder recurso"""
    ...
```

---

## 🧪 Fixtures Compartidos

### Global: `tests/conftest.py`

Fixtures disponibles en **todos los tests**:

| Fixture | Descripción |
|---------|-------------|
| `api_client` | REST API client sin autenticar |
| `authenticated_client` | API client autenticado (usuario normal) |
| `admin_client` | API client autenticado (superusuario) |
| `sample_user` | Usuario de prueba |
| `sample_admin` | Superusuario de prueba |
| `sample_center` | Centro de prueba |
| `sample_service` | Servicio 800 de prueba |
| `sample_date` | Fecha fija para reproducibilidad |

**Uso:**
```python
def test_endpoint(authenticated_client):
    response = authenticated_client.get('/api/v1/modules/')
    assert response.status_code == 200

def test_service_access(sample_user, sample_service):
    access = UserServiceAccess.objects.create(
        user=sample_user,
        service=sample_service
    )
    assert access.is_active
```

### App-específicos: `apps/*/tests/conftest.py`

Fixtures específicos de cada app.

---

## 🏷️ Markers Pytest

Usa markers para organizar y filtrar tests:

```python
import pytest

@pytest.mark.unit
def test_model():
    """Test unitario rápido"""
    ...

@pytest.mark.integration
@pytest.mark.slow
def test_full_flow():
    """Test de integración lento"""
    ...

@pytest.mark.api
def test_endpoint():
    """Test de endpoint API"""
    ...
```

### Markers disponibles:

- `@pytest.mark.unit` - Tests unitarios (rápidos, aislados)
- `@pytest.mark.integration` - Tests de integración
- `@pytest.mark.api` - Tests de API/endpoints
- `@pytest.mark.e2e` - Tests end-to-end
- `@pytest.mark.slow` - Tests lentos (>1s)
- `@pytest.mark.fast` - Tests rápidos (<1s)
- `@pytest.mark.access` - Tests de sistema access
- `@pytest.mark.audit` - Tests de auditoría
- `@pytest.mark.core` - Tests de core

---

## 🚀 Ejecutar Tests

### Todos los tests:
```bash
pytest
```

### Por ubicación:
```bash
# Tests centralizados
pytest tests/

# Tests de una app
pytest apps/authentication/tests/

# Tests API
pytest tests/api/

# Tests unitarios
pytest tests/unit/
```

### Por marker:
```bash
# Solo tests unitarios
pytest -m unit

# Solo tests API
pytest -m api

# Solo tests rápidos
pytest -m fast

# Excluir tests lentos
pytest -m "not slow"

# Combinar markers
pytest -m "unit and access"
```

### Con coverage:
```bash
pytest --cov=apps --cov-report=html
```

### Modo verbose:
```bash
pytest -v
pytest -vv  # Extra verbose
```

---

##  Checklist: ¿Dónde va mi test?

**Si tu test...**

- [ ] Prueba UN modelo/serializer/service → `apps/X/tests/`
- [ ] Prueba UN endpoint → `tests/api/`
- [ ] Cruza múltiples apps → `tests/integration/`
- [ ] Es flujo completo E2E → `tests/e2e/`
- [ ] Necesita fixtures complejos → considera crear fixture en `tests/conftest.py`

---

## 📝 Convenciones

1. **Nombres de archivos:** `test_*.py`
2. **Nombres de clases:** `TestNombreDescriptivo`
3. **Nombres de funciones:** `test_accion_esperada`
4. **Docstrings:** Siempre incluir qué se está probando
5. **Assertions:** Claras y específicas
6. **Fixtures:** Usar fixtures compartidos cuando sea posible

---

## 🔧 Configuración

- **pytest.ini:** Configuración pytest
- **config/settings/testing.py:** Settings para tests
- **tests/conftest.py:** Fixtures globales
- **apps/*/tests/conftest.py:** Fixtures app-específicos

---

## 📊 Estadísticas Actuales

- **Total tests:** ~62
- **Apps con tests:** authentication, users, access, audit, core
- **Coverage objetivo:** >80%

---

## 🎯 Mejores Prácticas

1.  Tests deben ser **independientes** (no depender de orden)
2.  Usar `@pytest.mark.django_db` para tests con DB
3.  Fixtures sobre setup/teardown manual
4.  Nombres descriptivos (`test_user_cannot_delete_other_users`)
5.  Un concepto por test (no múltiples asserts no relacionados)
6.  Usar markers para organizar
7.  Tests rápidos (unitarios) vs lentos (integración)

---

Última actualización: 2024 - Issue #5: Centralización de Tests
