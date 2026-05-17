# ANALISIS-FALLOS-MASIVOS-SUITE-2026-05-15

**Documento:** ANALISIS-FALLOS-MASIVOS-SUITE-2026-05-15
**Fecha:** 2026-05-15
**Rama:** develop
**Propósito:** Explicar por qué la suite de 1335 tests a veces muestra 500+ errores

---

## Síntoma

En determinadas circunstancias la suite pasa de:
```
1335 passed in 53s
```
a:
```
530 failed, 784 passed, 21 errors
```
o
```
472 passed, 863 errors
```

## Causa raíz 1 — PostgreSQL no está corriendo (el caso más frecuente)

El entorno de CI de esta sesión requiere **dos bases de datos**:

| BD | Motor | Uso |
|---|---|---|
| `test_iact_analytics` | PostgreSQL 16 | BD principal (usuarios, permisos, sesiones, etc.) |
| `test_ivr_legacy` | MariaDB | BD legacy IVR (logs ETL, pipeline, reportes) |

PostgreSQL es un servicio del sistema que **se detiene al reiniciar el contenedor**
o cuando `pg_ctlcluster` falla silenciosamente. Cuando PostgreSQL está caído,
`pytest-django` intenta conectarse al crear la BD de test y falla con:

```
psycopg2.OperationalError: connection to server on socket
"/var/run/postgresql/.s.PGSQL.5432" failed: Connection refused
```

Este error ocurre en el **setup del primer test que necesita DB** (`@pytest.mark.django_db`).
Los tests sin `django_db` pasan (los 472 que se ven en el segundo escenario).
Los 863 errores son todos `ERROR` de setup, no `FAILED`.

**Diagnóstico inmediato:**
```bash
pg_ctlcluster 16 main status
# Si dice "down": pg_ctlcluster 16 main start && sleep 2
```

## Causa raíz 2 — ImportError en un módulo central

Cuando se modifica un archivo que es importado transitivamente por muchos módulos
(ej: `apps/core/models.py`, `apps/utils/models.py`, `apps/access/models.py`),
un error de import provoca que **Django no pueda iniciar** y pytest falla en la
fase de **colección** de todos los tests que tocan esa rama de imports.

La diferencia con los errores de BD: aquí aparece
`ImportError while importing test module` en la fase de colección, **antes de
que se ejecute cualquier test**.

Ejemplo observado durante FASE 7E:
- Se eliminó `extend_schema_view` de `reports/views.py` al limpiar imports.
- Ese símbolo era usado por un `@extend_schema_view(...)` en el mismo archivo.
- Al importar cualquier módulo que dependía de `reports`, Django fallaba.
- Resultado: 530 failed con el mensaje `NameError: name 'extend_schema_view' is not defined`.

**Diagnóstico inmediato:**
```bash
python3 -c "import django; django.setup()" 2>&1 | head -5
# Si sale ImportError o NameError → problema de código, no de infraestructura
```

## Causa raíz 3 — autoflake rompe bloques multilinea

Durante FASE 7E se probó `autoflake --remove-all-unused-imports` sobre `apps/`.
`autoflake` eliminó correctamente imports de líneas simples, pero en bloques
`from X import (\n  A,\n  B,\n)` eliminó el símbolo dejando la línea en blanco,
lo que corrompe la sintaxis Python (`SyntaxError: unexpected indent`).

Ejemplo:
```python
# Antes:
from apps.access.serializers import (
    AccessGroupSerializer,
    MenuItemSerializer,   # ← autoflake eliminó esta línea
)

# Resultado:
from apps.access.serializers import (
    AccessGroupSerializer,
                          # ← línea vacía — SyntaxError en la siguiente línea
)
```

**Resultado:** `SyntaxError` en el archivo afectado → todos los tests que importan
de esa ruta fallan en colección.

## Causa raíz 4 — Lógica de swagger_fake_view rota

Los ViewSets `AlertSubscriptionViewSet`, `ScheduledReportViewSet` y
`SavedViewViewSet` tenían:

```python
def get_queryset(self):
    if getattr(self, "swagger_fake_view", False):
        return self.queryset.none()  # ← self.queryset era None → AttributeError
    ...
```

Cuando `drf-spectacular` generaba el schema de la API (activado por cualquier
test que importara el router de URLs), la excepción en `get_queryset` se
propagaba y podía romper la configuración de URL.

Aunque este problema no generaba 500 fallos, sí causaba warnings `W001/W002`
en `django check` y podía causar 500 en algunos entornos de test que generan
el schema automáticamente.

## Procedimiento de arranque correcto

```bash
# 1. Arrancar ambas BDs
pg_ctlcluster 16 main start && service mariadb start && sleep 2

# 2. Verificar que Django puede iniciar
cd callcentersite
DJANGO_SETTINGS_MODULE=config.settings.testing_local \
python3 -c "import django; django.setup(); print('OK')"

# 3. Ejecutar la suite
DJANGO_SETTINGS_MODULE=config.settings.testing_local \
python3 -m pytest tests/ --no-header -q --tb=no
```

## Medidas preventivas implementadas

### En conftest.py (tests/unit/conftest.py)

Ya existe `ensure_mariadb_unit` (scope=session, autouse=True) que verifica
y arranca MariaDB automáticamente. No existe el equivalente para PostgreSQL.

### Propuesta: fixture de arranque automático de PostgreSQL

```python
# tests/conftest.py — añadir al final
import subprocess

@pytest.fixture(scope='session', autouse=True)
def ensure_postgresql():
    """Garantiza que PostgreSQL esté corriendo antes de la sesión de tests."""
    result = subprocess.run(
        ['pg_ctlcluster', '16', 'main', 'status'],
        capture_output=True, text=True
    )
    if 'online' not in result.stdout:
        subprocess.run(['pg_ctlcluster', '16', 'main', 'start'], check=True)
        import time; time.sleep(2)
    yield
```

Esta fixture garantizaría que la suite nunca falla por PostgreSQL caído,
independientemente de cómo se invoque pytest.

---

*Generado: 2026-05-15*
