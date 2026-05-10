# CLEAN_CODE_NAMING_PRINCIPLES

```yml
version: 1.0.0
status: Vigente
created_at: 2026-05-07
scope: Todo el proyecto — codigo de produccion y codigo de tests
```

---

## Proposito

Este documento establece las convenciones de nomenclatura obligatorias para el proyecto.
El objetivo es que cualquier desarrollador pueda leer el nombre de una clase, metodo,
variable o archivo y entender su rol sin necesidad de leer su implementacion.

**Principio rector:** el nombre describe el rol o el proposito. Nunca el patron de diseno
que implementa internamente, ni el tipo de dato, ni el mecanismo tecnico.

---

## 1. Clases

### 1.1 Regla general

Los nombres de clase usan `PascalCase` y describen el rol de la clase en el dominio.

### 1.2 Prohibicion de sufijos de patrones de diseno

Los patrones de diseno son detalles de implementacion. Exponerlos en el nombre
de la clase acopla el nombre a la solucion tecnica, no al problema del dominio.

| Prohibido | Razon | Correcto |
|---|---|---|
| `UserFactory` | Expone el patron Factory | `UserTestData` (tests) |
| `ReportFactory` | Expone el patron Factory | `ReportTestData` (tests) |
| `UserBuilder` | Implica interfaz fluent que no existe | `UserTestData` |
| `ConnectionManager` | Manager es vago — no describe el rol real | nombre de dominio |
| `UserSingleton` | Expone el patron Singleton | `CurrentUser` |
| `AuthHelper` | Helper no describe nada | nombre de dominio |

**Esta regla no tiene excepciones** para los patrones listados arriba.

### 1.3 Excepciones pragmaticas del ecosistema Django/DRF

Los sufijos `Serializer` y `ViewSet` son excepciones explicitas y deliberadas.

**No se argumenta que describan el rol del dominio — no lo hacen.**
Son mecanismos tecnicos de Django REST Framework.

La excepcion se justifica por dos razones pragmaticas:

1. **Friccion de incorporacion:** cualquier desarrollador Django reconoce
   instantaneamente que `UserSerializer` transforma datos de User y
   `UserViewSet` agrupa operaciones CRUD sobre User. Renombrarlos
   a `UserRepresentation` o `UserEndpoint` obligaria a cada nuevo
   desarrollador a aprender una convencion local antes de ser productivo.

2. **Sin confusion dentro del ecosistema:** a diferencia de `Manager`,
   `Helper` o `Factory`, que son vagos o ambiguos incluso entre
   desarrolladores Django, `Serializer` y `ViewSet` tienen significado
   preciso y acotado dentro del ecosistema. No generan la confusion
   que la regla general busca evitar.

| Sufijo | Estado | Razon |
|---|---|---|
| `Serializer` | **Permitido** | Convencion del ecosistema DRF — significado preciso y universal |
| `ViewSet` | **Permitido** | Convencion del ecosistema DRF — significado preciso y universal |
| `Backend` | **Prohibido** | Vago fuera de Django auth — no describe el rol real |
| `Manager` | **Prohibido** | Mecanismo del ORM — el nombre debe describir el rol de consulta |
| `Helper` | **Prohibido** | No describe nada — siempre existe un nombre mas preciso |
| `Factory` | **Prohibido** | Patron de diseno expuesto — usar `TestData` en tests |
| `Middleware` | **Permitido con criterio** | Usar nombre de dominio cuando el rol es claro (`SecurityHeadersPolicy`) |

### 1.4 Clases de tests — sufijo TestData

Las clases que definen datos de prueba usando `factory_boy` usan el sufijo `TestData`.
El sufijo describe el proposito sin implicar una interfaz de construccion progresiva.

```python
# Correcto
class UserTestData(factory.django.DjangoModelFactory):
    class Meta:
        model = User
    username = factory.Sequence(lambda n: f"user_{n}")

class AccessGroupTestData(factory.django.DjangoModelFactory):
    class Meta:
        model = AccessGroup
    code = factory.Sequence(lambda n: f"GRP_{n:04d}")

# Prohibido
class UserFactory(...)       # prohibido — expone patron
class UserBuilder(...)       # prohibido — implica interfaz fluent inexistente
```

Uso identico a cualquier clase de factory_boy:

```python
user = UserTestData()
user = UserTestData.build()
users = UserTestData.create_batch(5)
```

### 1.5 Clases de produccion con patrones de diseno

Cuando se implementa un patron de diseno en codigo de produccion, el nombre
describe el rol en el dominio, no el patron.

```python
# Incorrecto
class LocalizerFactory: ...

# Correcto
class LanguageResolver: ...   # describe el rol
```

---

## 2. Metodos y funciones

Los metodos usan `snake_case` y tienen nombres de verbo que describen la accion.

```python
# Correcto
def resolve_effective_permissions(user) -> set[str]: ...
def expire_exceptional_permissions() -> int: ...
def get_available_quarters() -> set[str]: ...

# Prohibido
def get_data(): ...       # no dice que datos ni de donde
def process(): ...        # no dice que procesa
def handle(): ...         # no dice que maneja (excepcion: BaseCommand.handle es contrato del framework)
def do_stuff(): ...       # no describe nada
```

---

## 3. Variables

Las variables usan `snake_case` y nombres que revelan intencion.

```python
# Correcto
active_user_count = 105
elapsed_days = 12
function_codes = set()
available_quarters = get_available_quarters()

# Prohibido
au = 105          # abreviacion sin contexto
d = 12            # letra sola
data = []         # no dice que contiene
result = query()  # no dice que tipo de resultado
```

Las colecciones usan nombres en plural que describen el contenido.

```python
# Correcto
users = User.objects.all()
active_function_codes = set()

# Prohibido
user_list = []    # sufijo _list es redundante
data = []         # no describe el contenido
```

---

## 4. Constantes

Las constantes usan `UPPER_SNAKE_CASE` y nombres que describen el valor conceptual.

```python
# Correcto
CACHE_TTL_SECONDS = 300
MAX_EXPORT_ROWS = 100_000
IVR_QUERY_TIMEOUT_SEC = 30

# Prohibido
TTL = 300         # sin contexto
NINETY = 90       # el nombre es el valor
```

---

## 5. Modulos y archivos

Los archivos Python usan `snake_case`. El nombre describe el contenido.

### 5.1 Codigo de produccion

```
apps/access/
    models.py
    services.py
    views.py
    serializers/
    urls.py
    admin.py
    scheduler.py
```

### 5.2 Codigo de tests

El directorio de datos de prueba se llama `test_data/`.
Los archivos usan el sufijo `_test_data.py`.

```
tests/
    test_data/
        __init__.py
        user_test_data.py
        access_test_data.py
        separation_rule_test_data.py
    fixtures/
        ivr.py
        users.py
    unit/
    integration/
```

---

## 6. Idioma

### 6.1 Codigo Python

Todos los identificadores Python son en ingles sin excepcion:
clases, metodos, atributos de modelos Django, variables locales,
parametros de funcion, constantes y nombres de archivo.

### 6.2 Base de datos

Los nombres de tablas, columnas, procedimientos almacenados y funciones
en MariaDB pueden estar en espanol porque los administradores de base de
datos trabajan directamente con SQL en el idioma del negocio.

Los strings que referencian objetos de MariaDB desde Python son valores
del contrato de DB — no son identificadores Python y no estan sujetos
a la regla de ingles.

```python
# Correcto — el identificador Python esta en ingles
# El string del SP es el contrato de la BD (valor opaco)
def get_clients(quarter: str) -> list[dict]:
    return _call_sp('sp_rpt_clientes', [quarter])

# Correcto — el nombre de columna en SQL es el contrato de la BD
cursor.execute("SELECT trimestre FROM base_ivr_detalle")
```

### 6.3 Comentarios y docstrings

Los comentarios y docstrings pueden estar en espanol o ingles.
No son identificadores y no estan sujetos a la regla de ingles.

---

## 7. Acronimos en identificadores

Los acronimos no se usan como identificadores en codigo Python.
El identificador usa el nombre completo del concepto.

| Prohibido | Correcto |
|---|---|
| `SodRule` | `SeparationRule` |
| `SodValidator` | `SeparationRuleValidator` |
| `RBAC_check` | `permission_check` |
| `ETL_run` | `pipeline_run` |

**Excepcion:** identificadores opacos con dependencias externas persistidas.
Los tokens de funcion como `access:view_sod` son contratos de integracion
con sistemas externos — no se modifican desde Python.

---

## 8. Resumen — referencia rapida

| Contexto | Convencion | Ejemplo |
|---|---|---|
| Clase de produccion | PascalCase, nombre de rol | `SeparationRuleViewSet` |
| Serializer DRF | PascalCase + Serializer (excepcion pragmatica) | `UserSerializer` |
| ViewSet DRF | PascalCase + ViewSet (excepcion pragmatica) | `UserViewSet` |
| Clase de test data | PascalCase + TestData | `UserTestData` |
| Metodo / funcion | snake_case, verbo descriptivo | `expire_exceptional_permissions` |
| Variable | snake_case, nombre descriptivo | `active_function_codes` |
| Constante | UPPER_SNAKE_CASE, nombre conceptual | `IVR_QUERY_TIMEOUT_SEC` |
| Archivo de produccion | snake_case | `services.py` |
| Archivo de test data | snake_case + _test_data | `user_test_data.py` |
| Directorio de test data | snake_case | `tests/test_data/` |

### Prohibiciones absolutas — sin excepciones

- Sufijo `Factory` en cualquier clase del proyecto.
- Sufijo `Builder` para clases de datos de prueba.
- Sufijo `Manager` como nombre principal de clase.
- Sufijo `Backend` en clases de produccion.
- Sufijo `Helper` o `Utils` como nombre principal de clase.
- Nombres de una sola letra fuera de iteradores.
- Acronimos en identificadores de codigo Python.

---

## 9. Historial de decisiones

| Version | Cambio | Razon |
|---|---|---|
| 1.0.0 | Version inicial | Consolidacion de decisiones del proyecto |
| 1.0.0 | `Serializer` y `ViewSet` como excepciones pragmaticas | No describen el dominio pero son universales en el ecosistema Django/DRF. La excepcion se justifica por friccion de incorporacion reducida, no por precision semantica. `Backend`, `Manager`, `Helper`, `Factory` siguen prohibidos porque son vagos o ambiguos incluso dentro del ecosistema. |
| 1.0.0 | Prohibicion de `Factory` sin excepciones | La excepcion para `tests/factories/` era incorrecta — delegaba la convencion a la libreria. `TestData` describe el proposito sin implicar una interfaz. |
| 1.0.0 | `TestData` como sufijo para datos de prueba | `Builder` implica interfaz fluent que factory_boy no expone en las subclases del proyecto. |
| 1.0.0 | Ingles en Python, espanol en DB | Cada capa es internamente consistente. Los strings que referencian objetos de MariaDB son contratos de integracion, no identificadores Python. |
| 1.0.0 | Prohibicion de acronimos en identificadores | SoD/SOD/sod en el mismo proyecto genera ambiguedad. El nombre completo es siempre preferible. |
