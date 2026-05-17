# Plan de Actualización — Nomenclatura IACT-api

**Versión:** 1.0.0
**Fecha:** 2026-05-13
**Referencia:** `docs/conventions/CLEAN_CODE_NAMING_PRINCIPLES_v1_0_0.md`
**Regla rectora (RA-011):** todo identificador Python en inglés sin excepción.
Comentarios y docstrings pueden estar en español.
Strings que referencian objetos de MariaDB son contratos de BD — no son
identificadores Python y no están sujetos a la regla de inglés.

---

## Inventario de violaciones encontradas

| ID | Tipo | Cantidad | Archivos | Riesgo |
|---|---|---|---|---|
| V1 | Clases de vistas en español | 6 | `apps/reports/ivr_views.py` | Bajo |
| V2 | Función helper en español | 1 | `apps/pipeline/views.py` | Trivial |
| V3 | Campos de modelo en español | 13 | `apps/pipeline/models.py` | Alto (migración) |
| V4 | Serializers con campos en español (derivado de V3) | 4 archivos | `pipeline/serializers/`, `core/serializers.py` | Medio |
| V5 | Sufijo `Builder` prohibido | 1 clase | `apps/core/navigation/builders.py` | Bajo |
| V6 | Sufijo `Factory` prohibido | ~90 clases | `tests/factories/` (8 archivos) | Medio |
| V7 | Directorio `tests/testdata/` duplicado de `tests/test_data/` | 11 archivos | `tests/testdata/` | Bajo |
| V8 | `apps/ivr/` — código muerto con deuda técnica pendiente desde 2026-03-21 | Toda la app | `apps/ivr/`, `tests/unit/ivr_legacy/` | Bajo (solo borrar) |

---

## Análisis especial: archivos y clases `ivr_*`

### Archivos `ivr_views.py` e `ivr_services.py` — **ACEPTABLES**

El prefijo `ivr_` es inglés: IVR = Interactive Voice Response (acrónimo en inglés).
Los archivos existen dentro de `apps/reports/` junto a `views.py` y `services.py`
que ya existen para los reportes Django-ORM. El prefijo diferencia las dos capas
del mismo módulo. No es una violación del RA-011.

Hay dos clases dentro de `ivr_views.py` con tags ausentes en `@extend_schema`
(`MenuRedirigidosView`, `MenuCentroView`) — eso es un gap de documentación OpenAPI,
no una violación de nomenclatura.

### `MenusIVRView` — **RENOMBRAR**

El nombre mezcla inglés y un acrónimo posicionado en el medio (`Menus` + `IVR` +
`View`). El acrónimo en PascalCase debe seguir el patrón `Ivr` (primera letra
mayúscula, resto minúsculas), no `IVR` (todo mayúsculas). La clase describe
una vista de menús IVR. El nombre correcto es `IvrMenusView`.

### Clases en `apps/ivr/` — **RENOMBRAR (V8)**

`TblTempPruebaIvr` expone el nombre físico de la tabla de BD como nombre de clase
Python. Viola la separación entre capa Python y capa de datos. La clase representa
un registro de prueba del sistema IVR. Nombre correcto: `IvrProbeRecord`.

`IvrConfig` en `apps.py` — excepción: es el `AppConfig` generado por Django para la
app llamada `ivr`. Convención del framework. Se mantiene.

---

## Plan de implementación — 7 FASEs

Las FASEs están ordenadas de menor a mayor riesgo y dependencias.
Cada FASE es un commit independiente y el proyecto debe pasar `verify.sh`
(tests) al completar cada una.

---

### FASE 1 — Función helper en español (trivial, sin dependencias)

**Archivo:** `apps/pipeline/views.py`
**Commits esperados:** 1

#### T1.1 — Renombrar `_build_resumen_salud`

```python
# ANTES:
def _build_resumen_salud(runs: list[dict]) -> dict:

# DESPUÉS:
def _build_pipeline_health_summary(runs: list[dict]) -> dict:
```

Actualizar la única llamada interna en la misma función `etl_status`:
```python
# ANTES:
resumen = _build_resumen_salud(runs)

# DESPUÉS:
resumen = _build_pipeline_health_summary(runs)
```

**Impacto:** 1 función, 1 llamada. Sin tests directos sobre la función privada.
Sin migración. Sin cambios en URLs ni serializers.

---

### FASE 2 — Clases de vistas en español en `ivr_views.py`

**Archivo principal:** `apps/reports/ivr_views.py`
**Archivos secundarios:** `apps/reports/urls.py`, tests que referencien estas clases
**Commits esperados:** 1

#### Tabla de renombres

| Clase actual | Clase nueva | Criterio |
|---|---|---|
| `ClientesReportView` | `ClientsReportView` | clientes → clients |
| `CentrosTransferenciaView` | `TransferCentersView` | centros transferencia → transfer centers |
| `LlamadasAbandonadasView` | `AbandonedCallsView` | llamadas abandonadas → abandoned calls |
| `CMENUErrorView` | `CMENUErrorView` | **sin cambio** — CMENU es término del dominio |
| `CentrosXSegmentoView` | `CentersBySegmentView` | centros × segmento → centers by segment |
| `MenusIVRView` | `IvrMenusView` | reordenar + normalizar acrónimo |
| `MenuRedirigidosView` | `RedirectedMenusView` | menus redirigidos → redirected menus |
| `MenuCentroView` | `CenterMenuView` | menu centro → center menu |

#### T2.1 — Renombrar las 7 clases en `ivr_views.py`

```python
# ANTES → DESPUÉS
class ClientesReportView(APIView):      → class ClientsReportView(APIView):
class CentrosTransferenciaView(APIView):→ class TransferCentersView(APIView):
class LlamadasAbandonadasView(APIView): → class AbandonedCallsView(APIView):
class CentrosXSegmentoView(APIView):    → class CentersBySegmentView(APIView):
class MenusIVRView(APIView):            → class IvrMenusView(APIView):
class MenuRedirigidosView(APIView):     → class RedirectedMenusView(APIView):
class MenuCentroView(APIView):          → class CenterMenuView(APIView):
```

Aprovechar para agregar `tags=["Reportes de Llamadas"]` en `MenuRedirigidosView`
y `MenuCentroView` (GAP-SPEC-01 del análisis de integración).

#### T2.2 — Actualizar `apps/reports/urls.py`

```python
# ANTES:
from .ivr_views import (
    MenuRedirigidosView, MenuCentroView,
    ClientesReportView, CentrosTransferenciaView,
    LlamadasAbandonadasView, CMENUErrorView,
    CentrosXSegmentoView, MenusIVRView,
)

# DESPUÉS:
from .ivr_views import (
    RedirectedMenusView, CenterMenuView,
    ClientsReportView, TransferCentersView,
    AbandonedCallsView, CMENUErrorView,
    CentersBySegmentView, IvrMenusView,
)
```

Actualizar `path(...)` en `urlpatterns` con los nuevos nombres de vista.

#### T2.3 — Actualizar imports en tests

```bash
grep -r "ClientesReportView\|CentrosTransferenciaView\|LlamadasAbandonadasView\
\|CentrosXSegmentoView\|MenusIVRView\|MenuRedirigidosView\|MenuCentroView" \
    callcentersite/tests/ --include="*.py" -l
```

Reemplazar en todos los archivos de tests encontrados.

---

### FASE 3 — `MenuBuilder` en `core/navigation/builders.py`

**Archivo:** `apps/core/navigation/builders.py`
**Commits esperados:** 1

#### Problema

`MenuBuilder` tiene el sufijo `Builder`, explícitamente prohibido por el
documento de convenciones. El sufijo implica una interfaz fluent que no existe.

#### Análisis del rol real

La clase construye la estructura de navegación a partir de los módulos del
usuario. Su rol en el dominio es: "ensamblar el árbol de menú de navegación".

#### T3.1 — Renombrar `MenuBuilder` → `NavigationMenuAssembler`

```python
# apps/core/navigation/builders.py

# ANTES:
class MenuBuilder:
    """Construye la estructura de navegacion a partir de los modulos."""

# DESPUÉS:
class NavigationMenuAssembler:
    """Construye la estructura de navegacion a partir de los modulos."""
```

`MenuValidator` en el mismo archivo no tiene sufijo prohibido — se mantiene.

#### T3.2 — Actualizar imports

```bash
grep -r "MenuBuilder" callcentersite/ --include="*.py" -l
```
Reemplazar `MenuBuilder` → `NavigationMenuAssembler` en todos los archivos.

---

### FASE 4 — Eliminar `apps/ivr/` (código muerto)

**Archivos a eliminar:**
- `apps/ivr/` completo (models, viewsets, serializers, urls, adapters, tests, migrations, apps.py, schema.py)
- `tests/unit/ivr_legacy/` completo (tests de TblTempPruebaIvr)
- `tests/factories/ivr_factories.py` (vacío — solo contiene comentario de deuda técnica)

**Commits esperados:** 1

#### Contexto

La eliminación estaba programada para el 2026-03-21. Razones para eliminar:

1. `CallLog`, `IVRAdapter`, `CallLogViewSet` — comentados con fecha de baja vencida
2. `TblTempPruebaIvr` — tabla de seed con 3000 números aleatorios, sin valor de negocio
3. Los endpoints de `apps/ivr/urls.py` **no están registrados** en `config/urls.py` — inaccesibles
4. `ivr_health` en `pipeline/views.py` ya verifica la conectividad con MariaDB
5. `managed=False` — Django nunca gestionó la tabla real, eliminar la app no borra datos

#### T4.1 — Quitar `apps.ivr` de `INSTALLED_APPS`

```python
# config/settings/base.py
INSTALLED_APPS = [
    ...
    # 'apps.ivr',    ← eliminar esta línea
    ...
]
```

#### T4.2 — Eliminar directorios

```bash
rm -rf callcentersite/apps/ivr/
rm -rf callcentersite/tests/unit/ivr_legacy/
rm -f  callcentersite/tests/factories/ivr_factories.py
```

#### T4.3 — Verificar que no quedan referencias

```bash
grep -r "apps.ivr\|from apps.ivr\|TblTempPruebaIvr\|temp.prueba"     callcentersite/ --include="*.py"
# Resultado esperado: 0 líneas
```

#### T4.4 — Squash o eliminación de la migración

La migración `apps/ivr/migrations/0001_initial.py` crea un modelo con
`managed=False` — Django nunca ejecutó DDL con ella. Al eliminar la app,
la migración desaparece con el directorio. No quedan operaciones pendientes
en la base de datos.

Si Django ya ejecutó `migrate` con esta migración registrada en
`django_migrations`, ejecutar:
```bash
python manage.py migrate ivr zero   # revertir
# luego eliminar el directorio
```

#### T4.5 — `tbl_temp_prueba_ivr` en MariaDB

La tabla en MariaDB **no se elimina**. Es responsabilidad de `IACT-db`,
no de `IACT-api`. Si el equipo de IACT-db decide eliminarla, lo hará
desde sus propios scripts de provisión.

---

### FASE 5 — Campos de modelo en español en `apps/pipeline/models.py`

**Esta es la FASE de mayor riesgo.** Requiere migración Django (PostgreSQL).
Afecta modelos, serializers, filtros, tests y cualquier código que referencie
los campos por nombre.

**Commits esperados:** 3 (migración + modelos + serializers + tests)

#### Tabla completa de renombres por modelo

**`Center`:**
| Campo actual | Campo nuevo |
|---|---|
| `nombre` | `name` |
| `codigo` | `code` |
| `descripcion` | `description` |
| `direccion` | `address` |
| `activo` | `is_active` |

**`Service`:**
| Campo actual | Campo nuevo |
|---|---|
| `numero_800` | `number_800` |
| `nombre` | `name` |
| `descripcion` | `description` |
| `activo` | `is_active` |

**`CallRecord`:**
| Campo actual | Campo nuevo |
|---|---|
| `fecha` | `date` |
| `telefono` | `phone` |
| `servicio_800` | `service_number` |
| `total_llamadas` | `total_calls` |
| `llamadas_contestadas` | `answered_calls` |
| `llamadas_abandonadas` | `abandoned_calls` |
| `duracion_total_segundos` | `total_duration_seconds` |

#### T5.1 — Actualizar `apps/pipeline/models.py`

Cambiar los nombres de campo en las tres clases.
Verificar que `answer_rate` y `abandonment_rate` en los métodos del
modelo referencian los campos nuevos (`answered_calls`, `abandoned_calls`).

#### T5.2 — Generar y revisar la migración

```bash
python manage.py makemigrations pipeline \
    --name rename_spanish_fields_to_english
```

La migración generará `RenameField` automáticamente para cada campo.
Revisar el archivo generado antes de aplicar — asegurar que son
`RenameField` y no `RemoveField`/`AddField` (que borrarían datos).

```python
# migrations/XXXX_rename_spanish_fields_to_english.py
operations = [
    migrations.RenameField('Center', 'nombre', 'name'),
    migrations.RenameField('Center', 'codigo', 'code'),
    migrations.RenameField('Center', 'descripcion', 'description'),
    migrations.RenameField('Center', 'direccion', 'address'),
    migrations.RenameField('Center', 'activo', 'is_active'),
    migrations.RenameField('Service', 'numero_800', 'number_800'),
    migrations.RenameField('Service', 'nombre', 'name'),
    migrations.RenameField('Service', 'descripcion', 'description'),
    migrations.RenameField('Service', 'activo', 'is_active'),
    migrations.RenameField('CallRecord', 'fecha', 'date'),
    migrations.RenameField('CallRecord', 'telefono', 'phone'),
    migrations.RenameField('CallRecord', 'servicio_800', 'service_number'),
    migrations.RenameField('CallRecord', 'total_llamadas', 'total_calls'),
    migrations.RenameField('CallRecord', 'llamadas_contestadas', 'answered_calls'),
    migrations.RenameField('CallRecord', 'llamadas_abandonadas', 'abandoned_calls'),
    migrations.RenameField('CallRecord', 'duracion_total_segundos', 'total_duration_seconds'),
]
```

#### T5.3 — Actualizar serializers (derivados de los modelos)

Archivos afectados:
```
apps/pipeline/serializers/callrecord_serializers.py
apps/pipeline/serializers/center_serializers.py
apps/pipeline/serializers/service_serializers.py
apps/core/serializers.py
apps/ivr/serializers/calllog_serializers.py
```

En cada serializer, actualizar la lista `fields` en `Meta`:
```python
# ANTES:
fields = ['id', 'fecha', 'telefono', 'servicio_800', 'total_llamadas', ...]

# DESPUÉS:
fields = ['id', 'date', 'phone', 'service_number', 'total_calls', ...]
```

#### T5.4 — Actualizar filtros

```bash
grep -r "total_llamadas\|nombre\|codigo\|activo\|fecha\|telefono" \
    callcentersite/apps/ --include="*.py" -l
```

`apps/pipeline/filters.py` tiene `total_llamadas__gte`, `total_llamadas__lte` →
`total_calls__gte`, `total_calls__lte`.

#### T5.5 — Actualizar tests

```bash
grep -r "total_llamadas\|nombre\|codigo\|activo\|fecha\|telefono\|servicio_800\
\|llamadas_contestadas\|llamadas_abandonadas\|duracion_total_segundos" \
    callcentersite/tests/ callcentersite/apps/ --include="*.py" -l
```

Actualizar todos los archivos encontrados: test_data, factories, unit tests,
integration tests, fixtures.

**Precaución:** `tests/fixtures/ivr.py` tiene queries SQL que referencian
columnas de MariaDB (`total_llamadas`, `fecha`). Estas son strings de contrato
de BD y NO deben cambiarse — son nombres de columnas reales de `base_ivr_detalle`.
Solo cambiar referencias a los campos Django del modelo PostgreSQL.

---

### FASE 6 — `tests/factories/` — sufijo `Factory` prohibido

**Archivos afectados:** 8 archivos en `tests/factories/`, `tests/testdata/` (eliminar),
y todos los imports en tests que referencien las factories.
**Commits esperados:** 2

#### Contexto

El documento de convenciones establece explícitamente:
- Sufijo `Factory` → **prohibido sin excepción**
- Sufijo `TestData` → **obligatorio** para clases de datos de prueba
- Directorio → `tests/test_data/` (ya existe correctamente)
- `tests/testdata/` → duplicado idéntico de `tests/test_data/` → **eliminar**

#### Inventario completo de clases a renombrar (~90 clases)

| Archivo | Clase actual | Clase nueva |
|---|---|---|
| `access_factories.py` | `ModuleFactory` | `ModuleTestData` |
| `access_factories.py` | `ModuleWithParentFactory` | `ModuleWithParentTestData` |
| `access_factories.py` | `FunctionFactory` | `FunctionTestData` |
| `access_factories.py` | `FunctionCreateFactory` | `FunctionCreateTestData` |
| `access_factories.py` | `FunctionViewFactory` | `FunctionViewTestData` |
| `access_factories.py` | `FunctionEditFactory` | `FunctionEditTestData` |
| `access_factories.py` | `FunctionDeleteFactory` | `FunctionDeleteTestData` |
| `access_factories.py` | `UserPermissionFactory` | `UserPermissionTestData` |
| `access_factories.py` | `UserWithModuleAccessFactory` | `UserWithModuleAccessTestData` |
| `access_factories.py` | `UserWithFunctionFactory` | `UserWithFunctionTestData` |
| `access_factories.py` | `CompleteUserFactory` | `CompleteUserTestData` |
| `alert_factories.py` | `AlertRuleFactory` | `AlertRuleTestData` |
| `alert_factories.py` | `AlertFactory` | `AlertTestData` |
| `alert_factories.py` | `TriggeredAlertFactory` | `TriggeredAlertTestData` |
| `alert_factories.py` | `ResolvedAlertFactory` | `ResolvedAlertTestData` |
| *(…y todos los demás en alert_factories.py)* | `*Factory` | `*TestData` |
| `audit_factories.py` | `AuditLogFactory` | `AuditLogTestData` |
| *(…y todos en audit_factories.py)* | `*Factory` | `*TestData` |
| `authentication_factories.py` | `LoginAttemptFactory` | `LoginAttemptTestData` |
| *(…y todos en authentication_factories.py)* | `*Factory` | `*TestData` |
| `core.py` | `CenterFactory` | `CenterTestData` |
| `core.py` | `ServiceFactory` | `ServiceTestData` |
| `core.py` | `CallRecordFactory` | `CallRecordTestData` |
| `dashboard_factories.py` | `DashboardConfigFactory` | `DashboardConfigTestData` |
| *(…y todos en dashboard_factories.py)* | `*Factory` | `*TestData` |
| `pipeline_factories.py` | `ETLJobFactory` | `ETLJobTestData` |
| *(…y todos en pipeline_factories.py)* | `*Factory` | `*TestData` |
| `report_factories.py` | `ReportFactory` | `ReportTestData` |
| *(…y todos en report_factories.py)* | `*Factory` | `*TestData` |
| `user_factory.py` | `UserFactory` | `UserTestData` |
| *(…y todos en user_factory.py)* | `*Factory` | `*TestData` |

#### T6.1 — Renombrar clases en `tests/factories/`

Regla mecánica: `s/Factory/TestData/g` sobre los nombres de clase.
No cambiar la herencia (`factory.django.DjangoModelFactory` se mantiene).

```python
# ANTES:
class UserFactory(factory.django.DjangoModelFactory):

# DESPUÉS:
class UserTestData(factory.django.DjangoModelFactory):
```

#### T6.2 — Mover archivos a `tests/test_data/` y limpiar duplicados

El contenido de `tests/factories/*.py` debe fusionarse con los archivos
equivalentes en `tests/test_data/` (o moverse si no existe equivalente).

Verificar conflictos antes de mover:
```bash
# Los archivos de test_data/ ya existen — verificar si tienen contenido propio
diff tests/factories/access_factories.py tests/test_data/access_test_data.py
```

Después de verificar, eliminar `tests/factories/` completo.
Eliminar también `tests/testdata/` (duplicado idéntico de `tests/test_data/`).

#### T6.3 — Actualizar todos los imports

```bash
# Encontrar todos los archivos que importan desde factories/
grep -r "from tests.factories\|from .factories\|import factories" \
    callcentersite/tests/ --include="*.py" -l

# Reemplazar el patrón de import:
# from tests.factories.user_factory import UserFactory
# → from tests.test_data.user_test_data import UserTestData
```

---

## Orden de ejecución y dependencias

```
FASE 1 (trivial)    → sin dependencias
FASE 2 (vistas)     → sin dependencias externas
FASE 3 (Builder)    → sin dependencias
FASE 4 (TblTemp)    → sin dependencias
FASE 5 (modelos)    → depende de: ninguna FASE previa
                       bloquea: FASE 6 (tests referencian campos)
FASE 6 (factories)  → puede ir antes o después de FASE 5
                       si va después: actualizar campos en T6.1 también
```

Orden recomendado: 1 → 2 → 3 → 4 → 6 → 5

Ejecutar FASE 5 al final porque es la de mayor riesgo y requiere
que los tests (FASE 6) ya estén actualizados para validar la migración.

---

## Verificación por FASE

Después de cada FASE:
```bash
# 1. Tests pasan
python manage.py test --settings=config.settings.testing_local

# 2. Imports no rotos
python -c "import callcentersite"  # o el módulo raíz

# 3. Sin referencias al nombre anterior
grep -r "<NOMBRE_ANTERIOR>" callcentersite/ --include="*.py"
```

Después de FASE 5 adicionalmente:
```bash
# Migración aplicada correctamente
python manage.py migrate pipeline
python manage.py showmigrations pipeline

# Datos no perdidos
python manage.py shell -c "
from apps.pipeline.models import CallRecord, Center, Service
print(CallRecord.objects.count(), Center.objects.count(), Service.objects.count())
"
```

---

## Lo que NO cambia

| Elemento | Razón |
|---|---|
| Strings de SPs: `'sp_rpt_clientes'`, `'sp_etl_maestro'` | Contratos de BD |
| Columnas SQL: `'trimestre'`, `'total_llamadas'` en queries raw | Contratos de BD |
| `db_table = 'tbl_temp_prueba_ivr'` | Contrato de BD |
| Archivos `ivr_views.py`, `ivr_services.py` | IVR es acrónimo inglés, nombres aceptables |
| `CMENUErrorView` | cMENU es término del dominio, no una palabra en español |
| `tbl_temp_prueba_ivr` en MariaDB | La tabla pertenece a IACT-db, no a IACT-api |
| Comentarios y docstrings en español | Permitidos por RA-011 |
| Nombres de columnas en `tests/fixtures/ivr.py` | Son strings SQL, contratos de BD |

---

## Commits esperados

| FASE | Commit message |
|---|---|
| 1 | `refactor(pipeline): renombrar _build_resumen_salud a _build_pipeline_health_summary` |
| 2 | `refactor(reports): renombrar vistas IVR de español a inglés (RA-011)` |
| 3 | `refactor(core): MenuBuilder → NavigationMenuAssembler (sufico Builder prohibido)` |
| 4 | `chore(ivr): eliminar apps/ivr/ — código muerto desde 2026-03-21` |
| 5a | `refactor(pipeline): renombrar campos de modelo de español a inglés (RA-011)` |
| 5b | `feat(pipeline): migración rename_spanish_fields_to_english` |
| 5c | `refactor(pipeline): actualizar serializers y filtros por renombres de FASE 5` |
| 5d | `test(pipeline): actualizar test_data y tests por renombres de FASE 5` |
| 6a | `refactor(tests): Factory → TestData en tests/factories/ (sufijo prohibido)` |
| 6b | `refactor(tests): eliminar tests/factories/ y tests/testdata/ (consolidar en test_data/)` |
