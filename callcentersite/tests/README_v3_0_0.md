# Estructura de Tests - IACT Call Center System v3.0.0

## 📁 Organización Centralizada

Este proyecto usa **organización centralizada** de tests. **TODOS los tests están en `/tests/`**.

```
callcentersite/
├── tests/                          # ← TODOS LOS TESTS AQUÍ
│   ├── conftest.py                # Fixtures globales (60+ fixtures)
│   ├── pytest.ini                 # Configuración pytest
│   │
│   ├── unit/                      # Tests unitarios por app
│   │   ├── access/               # Tests de apps/access/
│   │   ├── alerts/               # Tests de apps/alerts/
│   │   ├── audit/                # Tests de apps/audit/
│   │   ├── authentication/       # Tests de apps/authentication/
│   │   ├── core/                 # Tests de apps/core/
│   │   ├── dashboard/            # Tests de apps/dashboard/
│   │   ├── ivr/                  # Tests de apps/ivr/
│   │   ├── pipeline/             # Tests de apps/pipeline/
│   │   ├── reports/              # Tests de apps/reports/
│   │   ├── users/                # Tests de apps/users/
│   │   └── utils/                # Tests de apps/utils/
│   │
│   ├── integration/               # Tests de integración multi-app
│   │   ├── test_auth_flow.py    # Login → access → recursos
│   │   ├── test_rbac_flow.py    # Usuario → rol → función → módulo
│   │   └── test_etl_flow.py     # Pipeline → IVR → Reports
│   │
│   ├── api/                       # Tests de endpoints REST
│   │   ├── test_access_api.py   # /api/v1/access/*
│   │   ├── test_reports_api.py  # /api/v1/reports/*
│   │   └── test_audit_api.py    # /api/v1/audit/*
│   │
│   ├── e2e/                       # Tests end-to-end
│   │   └── test_user_journey.py # Flujos completos usuario
│   │
│   ├── fixtures/                  # Fixtures compartidos
│   │   ├── users.py              # Fixtures de usuarios
│   │   └── rbac.py               # Fixtures RBAC
│   │
│   └── factories/                 # Factories (factory_boy)
│       ├── user_factory.py
│       └── access_factory.py
│
└── apps/                          # ❌ NO tests aquí
    ├── access/                    # ✅ Solo código producción
    ├── users/                     # ✅ Solo código producción
    └── ...
```

---

## 🎯 Principios de Organización

### ✅ TODOS los tests en `/tests/`

**NO hay tests en `apps/*/tests/`**. Toda la suite de tests está centralizada.

**Ventajas:**
- Fácil encontrar todos los tests
- Fixtures compartidos naturalmente
- Evita duplicación de conftest.py
- Mejor para CI/CD
- Estructura clara y predecible

---

## 📂 Estructura Detallada

### `tests/unit/` - Tests Unitarios

Tests aislados de una sola unidad (función, clase, método):

```
tests/unit/
├── access/
│   ├── test_models.py          # Module, Role, Function models
│   ├── test_services.py        # AccessService, ModuleService
│   ├── test_serializers.py     # ModuleSerializer, etc
│   └── test_permissions.py     # RequiresFunctionPermission
│
├── reports/
│   ├── test_models.py          # Report, ReportExecution
│   ├── test_generators.py      # QuarterlySummaryReport, etc
│   ├── test_exporters.py       # ExcelExporter, CSVExporter
│   └── test_services.py        # ReportGeneratorService
│
├── ivr/
│   ├── test_models.py          # QuarterlyReport, TransferReport
│   ├── test_router.py          # IVRRouter
│   └── test_readonly.py        # Verificar solo SELECT
│
└── ...
```

**Características:**
- Un test = una unidad
- Rápidos (<1s)
- Sin dependencias externas
- Mock de servicios externos

---

### `tests/integration/` - Tests de Integración

Tests que cruzan múltiples apps:

```
tests/integration/
├── test_auth_flow.py           # Login → Obtener módulos → Acceder recurso
├── test_rbac_flow.py           # Usuario → Rol → Función → Verificar permiso
├── test_etl_pipeline.py        # ETL → IVR → Generar reporte
└── test_alert_pipeline.py      # Verificar métrica → Disparar alerta → Notificar
```

**Características:**
- Cruzan 2+ apps
- Más lentos (1-5s)
- Usan BD de test
- Validan flujos completos

---

### `tests/api/` - Tests de API REST

Tests de endpoints REST completos:

```
tests/api/
├── test_access_api.py          # GET /api/v1/access/modules/
│                               # GET /api/v1/access/my-modules/
│                               # POST /api/v1/access/functions/
│
├── test_reports_api.py         # POST /api/v1/reports/generate/
│                               # GET /api/v1/reports/{id}/
│                               # GET /api/v1/reports/stats/
│
├── test_audit_api.py           # GET /api/v1/audit/logs/
│                               # GET /api/v1/audit/sessions/
│
└── test_users_api.py           # CRUD /api/v1/users/
```

**Características:**
- Test HTTP request → response
- Validar status codes
- Validar JSON structure
- Validar autenticación/permisos

---

### `tests/e2e/` - Tests End-to-End

Flujos completos de usuario:

```
tests/e2e/
└── test_user_journey.py
    - test_manager_generates_quarterly_report()
      1. Login
      2. Obtener módulos asignados
      3. Verificar permiso reports.create
      4. Generar reporte Q1 2025
      5. Descargar Excel
      6. Verificar auditoría
```

**Características:**
- Simulan usuario real
- Más lentos (5-30s)
- Tocan múltiples endpoints
- Validación completa

---

## 🧪 Fixtures Disponibles (60+)

Todas las fixtures están en `tests/conftest.py` (disponibles globalmente):

### API Clients (3)

| Fixture | Descripción |
|---------|-------------|
| `api_client` | Cliente REST sin autenticación |
| `authenticated_client` | Cliente autenticado (usuario normal) |
| `admin_client` | Cliente autenticado (superusuario) |

**Uso:**
```python
def test_endpoint(authenticated_client):
    response = authenticated_client.get('/api/v1/modules/')
    assert response.status_code == 200
```

---

### Users / Auth (6)

| Fixture | Descripción |
|---------|-------------|
| `sample_user` | Usuario estándar (test@example.com) |
| `sample_admin` | Superusuario (admin@example.com) |
| `sample_inactive_user` | Usuario inactivo |
| `valid_login_credentials` | Credenciales válidas |
| `invalid_login_credentials` | Credenciales inválidas |
| `jwt_tokens` | Tokens JWT (access + refresh) |

---

### Access / RBAC (8)

| Fixture | Descripción |
|---------|-------------|
| `sample_module` | Módulo raíz |
| `sample_child_module` | Módulo hijo |
| `sample_function` | Función RBAC |
| `sample_role` | Rol |
| `user_with_module_access` | Usuario con acceso a módulo |
| `user_with_function` | Usuario con función asignada |
| `user_with_role` | Usuario con rol asignado |

**Uso:**
```python
def test_access(user_with_function, sample_function):
    assert AccessService.user_has_function(user, sample_function.function_id)
```

---

### Audit (2)

| Fixture | Descripción |
|---------|-------------|
| `sample_audit_log` | Log de auditoría |
| `sample_session_log` | Log de sesión |

---

### IVR / ETL (5)

| Fixture | Descripción |
|---------|-------------|
| `sample_quarterly_report` | Reporte trimestral Q1 2025 |
| `sample_transfer_report` | Reporte de transferencias |
| `sample_abandoned_report` | Reporte de abandonos |
| `sample_client_report` | Reporte de clientes |
| `sample_call_record_q1` | Registro de llamada Q1 |

---

### Pipeline (3)

| Fixture | Descripción |
|---------|-------------|
| `sample_etl_job` | Job ETL exitoso |
| `sample_etl_error` | Error ETL |
| `sample_scheduler_config` | Config scheduler |

---

### Reports (3)

| Fixture | Descripción |
|---------|-------------|
| `sample_report` | Reporte generado (.xlsx) |
| `sample_report_execution` | Ejecución de reporte |
| `sample_report_template` | Template de reporte |

---

### Dashboard (2)

| Fixture | Descripción |
|---------|-------------|
| `sample_dashboard_config` | Config de dashboard |
| `sample_widget_config` | Config de widget |

---

### Alerts (3)

| Fixture | Descripción |
|---------|-------------|
| `sample_alert_rule` | Regla de alerta (abandonment > 15%) |
| `sample_alert` | Alerta disparada |
| `sample_alert_notification` | Notificación enviada |

---

### Utils (4)

| Fixture | Descripción |
|---------|-------------|
| `sample_date` | Fecha fija (2025-01-15) |
| `sample_datetime` | Datetime fijo |
| `sample_quarter` | Trimestre (Q1 2025) |
| `mock_request` | Mock request con usuario |

---

### Mocks (5)

| Fixture | Descripción |
|---------|-------------|
| `mock_etl_service` | Mock ETLService |
| `mock_email_service` | Mock EmailService (CNST-001) |
| `mock_cache` | Mock cache (CNST-010) |
| `mock_apscheduler` | Mock APScheduler (CNST-013) |

**Uso:**
```python
def test_etl(mock_etl_service):
    mock_etl_service.extract_data.return_value = [...]
    result = ETLService.extract_data()
    assert len(result) > 0
```

---

### Files (3)

| Fixture | Descripción |
|---------|-------------|
| `sample_excel_file` | Archivo .xlsx temporal |
| `sample_csv_file` | Archivo .csv temporal |
| `sample_pdf_file` | Archivo .pdf temporal |

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

---

## 🚀 Ejecutar Tests

### Todos los tests:
```bash
pytest
```

### Por directorio:
```bash
# Tests unitarios
pytest tests/unit/

# Tests de una app específica
pytest tests/unit/access/

# Tests API
pytest tests/api/

# Tests de integración
pytest tests/integration/

# Tests E2E
pytest tests/e2e/
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
pytest -m "unit and not slow"
```

### Con coverage:
```bash
# Coverage básico
pytest --cov=apps

# Coverage con reporte HTML
pytest --cov=apps --cov-report=html

# Ver en navegador
open htmlcov/index.html
```

### Modo verbose:
```bash
pytest -v                # Verbose
pytest -vv               # Extra verbose
pytest -vvs              # Extra verbose + sin captura output
```

### Tests específicos:
```bash
# Un archivo
pytest tests/unit/access/test_models.py

# Una clase
pytest tests/unit/access/test_models.py::TestModuleModel

# Una función
pytest tests/unit/access/test_models.py::TestModuleModel::test_create_root_module
```

---

## 📝 Convenciones

### Nombres de archivos:
- `test_*.py` (prefix test_)
- Ejemplo: `test_models.py`, `test_services.py`

### Nombres de clases:
- `TestNombreDescriptivo`
- Ejemplo: `TestModuleModel`, `TestAccessService`

### Nombres de funciones:
- `test_accion_esperada`
- Ejemplo: `test_create_user`, `test_user_cannot_delete_other_users`

### Docstrings:
Siempre incluir qué se está probando:

```python
def test_user_with_function_has_access(user_with_function, sample_function):
    """
    Test: Usuario con función asignada tiene acceso.
    
    Given: Usuario con función reports.create
    When: Verificamos si tiene la función
    Then: Retorna True
    """
    assert AccessService.user_has_function(
        user_with_function,
        sample_function.function_id
    )
```

### Assertions:
- Claras y específicas
- Un concepto por test
- Mensajes de error útiles

```python
# ❌ INCORRECTO
def test_user():
    user = create_user()
    assert user  # ¿Qué estamos validando?

# ✅ CORRECTO
def test_user_creation_sets_is_active_true():
    user = create_user()
    assert user.is_active is True, "Usuario debe ser activo por defecto"
```

---

## 🔧 Configuración

### Archivos de configuración:

- **pytest.ini:** Configuración pytest (markers, paths)
- **config/settings/testing.py:** Settings Django para tests
- **tests/conftest.py:** Fixtures globales (60+)

---

## 📊 Estadísticas

```yaml
Apps con tests (11/11):
  ✅ access
  ✅ alerts
  ✅ audit
  ✅ authentication
  ✅ core
  ✅ dashboard
  ✅ ivr
  ✅ pipeline
  ✅ reports
  ✅ users
  ✅ utils

Total tests: 294 colectados
Fixtures: 60+ fixtures globales
Coverage objetivo: >85%
```

---

## 🎯 Mejores Prácticas

1. **Tests independientes** - No dependen de orden de ejecución
2. **@pytest.mark.django_db** - Para tests con BD
3. **Fixtures sobre setup/teardown** - Más legible y reutilizable
4. **Nombres descriptivos** - `test_user_cannot_delete_other_users`
5. **Un concepto por test** - No múltiples asserts no relacionados
6. **Usar markers** - Organizar por tipo/velocidad
7. **Mock servicios externos** - ETL, email, cache, scheduler

---

## 🔍 Debugging Tests

### Ver output de print:
```bash
pytest -s
```

### Detener en primer error:
```bash
pytest -x
```

### Modo pdb (debugger):
```bash
pytest --pdb
```

### Ver traceback completo:
```bash
pytest --tb=long
```

### Mostrar tests más lentos:
```bash
pytest --durations=10
```

---

## 📚 Referencias

- [Pytest Documentation](https://docs.pytest.org/)
- [Django Testing](https://docs.djangoproject.com/en/5.0/topics/testing/)
- [DRF Testing](https://www.django-rest-framework.org/api-guide/testing/)
- [Factory Boy](https://factoryboy.readthedocs.io/)

---

**Última actualización:** 2026-01-20 - v3.0.0  
**Cambio principal:** Organización 100% centralizada (todos los tests en `/tests/`)  
**Fixtures:** 60+ fixtures globales disponibles  
**Apps cubiertas:** 11/11 (100%)
