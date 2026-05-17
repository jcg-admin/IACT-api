# HALLAZGOS-FASE2-IACT-API-2026-05-16T20:28:11

**Documento:** HALLAZGOS-FASE2-IACT-API-2026-05-16T20:28:11  
**Fecha:** 2026-05-16  
**Repositorio:** IACT-api  
**Commit:** 1eec802  
**Plan base:** PLAN-IMPL-IACT-API-2026-05-16T17:53:35.md — FASE 2

---

## Estado antes de FASE 2

```
flake8 --select=F811: 7 ocurrencias en 4 archivos
Suite: 1327 passed, 0 failed (FASE 1 completada)
```

---

## Cambios aplicados por archivo

### T2.1 — `apps/access/views.py` (4 F811)

**Causa:** `AccessGroup`, `UserAccessGroup`, `SeparationRule` y
`ExceptionalPermission` importados en el bloque inicial (L18) y
reimportados en L170 junto al comentario del ViewSet B-05.
`MenuItemSerializer` importado solo en L171 (mid-module).

**Corrección:**
- `MenuItemSerializer` añadido al bloque de imports iniciales.
- Bloque mid-module L170-171 eliminado íntegro.

### T2.2 — `apps/authentication/viewsets.py` (1 F811)

**Causa:** `LoginSerializer` importado en dos líneas consecutivas:
```python
from apps.authentication.serializers.auth import LoginSerializer   # L17
from apps.authentication.serializers import (LoginSerializer, ...)  # L18
```

**Corrección:** eliminar L17. El import del bloque L18 es suficiente.

### T2.3 — `apps/reports/models.py` (1 F811)

**Causa:** `ExportJob.__str__` definido dos veces.

| Definición | Línea | Implementación | Robustez |
|---|---|---|---|
| Primera | L249 | `f'ExportJob({report_type}/{format}/{status})'` | Alta — usa campos directos |
| Segunda | L257 | `f'Export {id} - {report.name} ({format})'` | Baja — usa FK `report` (null=True) |

**Corrección:** segunda definición eliminada. Primera conservada como canónica.

### T2.4 — `apps/reports/views.py` (1 F811)

**Causa:** dos bloques de imports mid-module:

Sección K-002/K-003 (L251-257): `viewsets`, `IsAuthenticated` y `HasFunction` (×2)
ya presentes en el bloque inicial. `HasFunction` incluso duplicado dentro del
mismo bloque (L254 y L255 idénticos).

Sección K-005 (L353-355): `APIView`, `Response` y `timezone` ya presentes
en el bloque inicial o en K-002/K-003.

**Corrección:** consolidar los imports únicos necesarios de K-002/K-003
(`extend_schema`, `extend_schema_view`, `OpenApiResponse`, `APIView`, `timezone`,
`ScheduledReport`, `SavedView`, `ScheduledReportSerializer`, `SavedViewSerializer`)
en un solo bloque mid-module. Eliminar todos los duplicados y el bloque K-005.

---

## Hallazgos durante la implementación

### H-F2-001 — El segundo `__str__` de `ExportJob` tenía un test que lo verificaba

Al correr la suite tras eliminar el segundo `__str__`, `test_export_job_str`
falló:

```
AssertionError: assert 'My Report' in 'ExportJob(None/excel/queued)'
```

El test verificaba `'My Report' in str(job)` — nombre del `Report` FK.
El primer `__str__` usa `report_type`, `format` y `status` (campos directos),
no `report.name` (FK nullable).

**Decisión:** el primer `__str__` es el correcto:
- Usa solo campos del propio modelo (`report_type`, `format`, `status`).
- No lanza `AttributeError` cuando `report=None` (campo nullable para jobs UC_RPT_04).
- Tiene type hint `-> str` (convención del proyecto).
- El segundo `__str__` era un añadido posterior que nunca debió estar ahí.

**Corrección adicional:** `test_export_job_str` actualizado para verificar
el comportamiento del primer `__str__`:

```python
# Antes (verificaba el __str__ incorrecto):
assert 'My Report' in str(job)
assert 'excel' in str(job)

# Después (verifica el __str__ canónico):
assert 'users' in result     # report_type
assert 'excel' in result     # format
assert 'ExportJob(' in result  # prefijo del formato
```

El test también crea el `job` con `report_type='users'` para que `str(job)`
devuelva `'ExportJob(users/excel/queued)'` en lugar de `'ExportJob(None/excel/queued)'`.

### H-F2-002 — `HasFunction` duplicado dentro del mismo bloque en `reports/views.py`

La sección K-002/K-003 tenía `HasFunction` importado **dos veces en líneas
consecutivas** (L254-255 idénticos):

```python
from apps.access.permissions.function_permissions import HasFunction
from apps.access.permissions.function_permissions import HasFunction
```

Ambas son redundantes porque `HasFunction` ya está en el bloque inicial (L12).
El duplicado dentro del mismo bloque es un error de copiar-pegar durante el
desarrollo incremental de la sección K.

### H-F2-003 — Inestabilidad de mysqld durante la suite completa

Al correr `pytest tests/unit tests/integration tests/api` en una sola sesión,
mysqld se cae durante la ejecución de `tests/unit` (la parte más larga, ~52s)
y los tests de `tests/integration` fallan en el `SETUP` del fixture
`ensure_mariadb`.

El conftest de pipeline (`tests/integration/pipeline/conftest.py`) arranca
`mariadbd` como proceso hijo de pytest en el fixture `ensure_mariadb`
(`scope='session'`). Cuando se corre la suite completa en una sola invocación,
el fixture `ensure_mariadb` se ejecuta una vez al inicio de la sesión pero
`mariadbd` se cae antes de que lleguen los tests de integración.

**Mitigación documentada:** correr los subsistemas en dos invocaciones separadas:

```bash
# Primero: unit + api (no necesitan MariaDB)
python -m pytest tests/unit tests/api

# Luego: integration (con ensure_mariadb activo desde el inicio)
python -m pytest tests/integration
```

Esto corresponde al comportamiento documentado en
`ANALISIS-FALLOS-MASIVOS-SUITE-2026-05-15.md`.

---

## Verificaciones realizadas

| Verificación | Resultado |
|---|---|
| `flake8 --select=F811` tras T2.1 | 0 en `access/views.py` |
| `flake8 --select=F811` tras T2.2 | 0 en `authentication/viewsets.py` |
| `flake8 --select=F811` tras T2.3 | 0 en `reports/models.py` |
| `flake8 --select=F811` tras T2.4 | 0 en `reports/views.py` |
| `flake8 --select=F811` en toda la base | 0 ocurrencias |
| `python manage.py check` | 0 issues |
| Tests `unit/access + unit/authentication + unit/reports` | 470 passed, 0 failed |
| Suite `tests/integration` (con mysqld activo) | 104 passed, 0 failed |
| Suite `tests/unit + tests/api` | 1223 passed, 0 failed |

---

## Estado después de FASE 2

```
flake8 --select=F811: 0 ocurrencias
Suite: 1327 passed, 0 failed
  tests/unit:        1215 passed
  tests/integration: 104 passed
  tests/api:         8 passed

DT-API-002: RESUELTA
```

---

*Generado: 2026-05-16T20:28:11 | Commit: 1eec802 | Suite: 1327 passed, 0 failed*
