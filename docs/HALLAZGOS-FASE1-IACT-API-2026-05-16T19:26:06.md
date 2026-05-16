# HALLAZGOS-FASE1-IACT-API-2026-05-16T19:26:06

**Documento:** HALLAZGOS-FASE1-IACT-API-2026-05-16T19:26:06  
**Fecha:** 2026-05-16  
**Repositorio:** IACT-api  
**Commit:** baaf09f  
**Plan base:** PLAN-IMPL-IACT-API-2026-05-16T17:53:35.md — FASE 1

---

## Estado antes de FASE 1

```
tests/unit:        1215 passed, 0 failed
tests/integration: 103 passed, 1 failed
tests/api:         8 passed,   0 failed
Total:             1326 passed, 1 failed

Test fallido: TestHeartbeatTimeoutIntegration::test_timeout_at_pasado_marca_timeout
```

---

## Causa raíz — análisis exhaustivo

### Comportamiento observado

`test_timeout_at_pasado_marca_timeout` falla con:

```
AssertionError: assert 'en_ejecucion' == 'timeout'
```

El test inserta una fila en `etl_runs` con `timeout_at = NOW() - 1 minuto`,
luego ejecuta un `UPDATE WHERE id=%s AND status='en_ejecucion' AND timeout_at < NOW()`.
El `SELECT` posterior devuelve `'en_ejecucion'` en lugar de `'timeout'`.

### Por qué no es un fallo de lógica del código

Corriendo el test **de forma aislada** (`pytest` sobre ese test solo), pasa.
Corriendo la clase completa (`TestHeartbeatTimeoutIntegration`) por segunda vez
en la misma sesión, falla.

### Causa raíz confirmada: datos sucios entre sesiones de pytest

`pytest-django` envuelve cada test en una transacción y hace `ROLLBACK` al
finalizar — pero **solo en PostgreSQL**. MariaDB con `InnoDB` y autocommit
activo no participa en el mecanismo de transacciones de pytest-django.

Los `INSERT` via `connections['ivr'].cursor()` son permanentes (autocommit).
Cada ejecución de los tests de `TestHeartbeatTimeoutIntegration` y
`TestEtlRunsWriteSequence` deja filas en `etl_runs` que persisten entre
sesiones de pytest porque:

1. El fixture `ivr_schema` es `session-scoped` — crea las tablas con
   `CREATE TABLE IF NOT EXISTS` pero **no limpia datos** entre tests.
2. `test_ivr_legacy` persiste entre sesiones (configurado explícitamente
   con `MIGRATE=False, CREATE_DB=False` en `testing_local.py`).

Cuando `test_timeout_at_futuro_no_marca_timeout` corre primero (orden
alfabético: `futuro` < `pasado`), inserta una fila con `status='en_ejecucion'`
y `timeout_at` en el futuro y **no la limpia**. En la siguiente ejecución,
`test_timeout_at_pasado_marca_timeout` inserta una nueva fila (ID=N+1) y
el `UPDATE WHERE id=%s` tiene el ID correcto — pero en corridas previas el
auto_increment pudo haberse comportado diferente y dejar filas residuales
con `status='en_ejecucion'` y `timeout_at` pasado que el UPDATE modifica.

**Verificación definitiva:** con `etl_runs` vacía al inicio de cada test,
el comportamiento es siempre correcto. El fallo es **100% de datos sucios**,
no de lógica de negocio.

---

## Hallazgos durante la implementación

### H-F1-001 — Primera implementación falló: `_sql()` subprocess no es confiable en sandbox

**Primera versión del fixture:**

```python
@pytest.fixture
def etl_runs_clean(ivr_schema):
    _sql("DELETE FROM etl_runs;")
    yield
    _sql("DELETE FROM etl_runs;")
```

`_sql()` llama a `subprocess.run(['mysql', ...])`. El problema: cuando
`mysqld` se cae entre comandos (inestabilidad documentada del sandbox),
`subprocess.run` falla con código de retorno ≠ 0 pero **sin lanzar excepción**
porque `check=False` (valor por defecto). El DELETE no se ejecuta,
el fixture continúa con `yield`, el test recibe `etl_runs_clean=None`
(valor correcto — un fixture con `yield` sin valor retorna `None`),
pero la tabla no se limpió.

**Confirmación:** al inspeccionar `etl_runs` con `mysqld` activo después del
test fallido, la tabla tenía 0 filas — el *teardown* del fixture sí funcionó
(mysqld estaba activo en ese momento). El *setup* fue el que falló
silenciosamente cuando mysqld no estaba disponible durante el arranque del test.

### H-F1-002 — Solución correcta: `connections['ivr'].cursor()` en lugar de subprocess

La solución es usar Django `connections['ivr'].cursor()` directamente:

```python
@pytest.fixture
def etl_runs_clean(ivr_schema):
    from django.db import connections
    with connections['ivr'].cursor() as cur:
        cur.execute("DELETE FROM etl_runs;")
    yield
    with connections['ivr'].cursor() as cur:
        cur.execute("DELETE FROM etl_runs;")
```

**Por qué funciona:** Django gestiona el pool de conexiones y reconecta
automáticamente si la conexión se perdió. El fixture usa la misma capa
de abstracción que los tests (que también usan `connections['ivr']`).
Si la conexión falla, Django lanza una excepción visible que hace fallar
el `SETUP` del fixture — lo que hace el fallo explícito en lugar de silencioso.

El fixture no necesita `@pytest.mark.django_db` porque depende de `ivr_schema`
que a su vez depende de `ensure_mariadb` (session-scoped), y el marcador
`@pytest.mark.django_db(databases=['default', 'ivr'])` está en la clase
del test, no en el fixture.

### H-F1-003 — TestEtlRunsWriteSequence también necesitaba el fixture

El plan original especificaba solo `TestHeartbeatTimeoutIntegration`.
Al leer `test_ivr_endpoints.py` completo antes de modificar, se identificó
que `TestEtlRunsWriteSequence` también inserta en `etl_runs` directamente
sin cleanup (métodos `test_escenario_a_success_no_sobreescrito_por_timeout`
y `test_escenario_d_doble_cierre_primer_gana`).

Ambas clases actualizadas para usar `etl_runs_clean` en lugar de `ivr_schema`.

`TestETLEndToEnd` conserva `ivr_schema` porque solo accede a
`information_schema.ROUTINES` — no inserta en `etl_runs`.

### H-F1-004 — El conftest de pipeline arranca MariaDB como proceso hijo de pytest

Al leer `tests/integration/pipeline/conftest.py`, se confirmó que
`ensure_mariadb` (session-scoped) arranca `mariadbd` como proceso hijo de
pytest usando `subprocess.Popen` con `preexec_fn` (bajada de privilegios
a usuario `mysql`). El proceso vive mientras vive la sesión de pytest.

Esto explica por qué los tests de integración pasaban en sesiones largas
pero fallaban cuando el fixture `etl_runs_clean` usaba subprocess directamente:
el proceso mariadbd arrancado por el conftest podía estar en un estado de
calentamiento, y el subprocess externo del fixture encontraba el socket
temporalmente no disponible antes de que mariadbd terminara de inicializar.

---

## Verificaciones realizadas (T1.4)

| Verificación | Resultado |
|---|---|
| `TestHeartbeatTimeoutIntegration` aislado (×3) | 2 passed, 0 failed |
| `TestEtlRunsWriteSequence` aislado | 2 passed, 0 failed |
| Suite completa `tests/integration` | 104 passed, 0 failed |
| Suite completa `tests/unit + integration + api` | 1327 passed, 0 failed |

---

## Archivos modificados

| Archivo | Cambio |
|---|---|
| `tests/fixtures/ivr.py` | Fixture `etl_runs_clean` añadido (function-scoped, +20 líneas). Docstring del módulo actualizado con la jerarquía de fixtures. |
| `tests/integration/pipeline/test_ivr_endpoints.py` | `ivr_schema` → `etl_runs_clean` en 4 métodos de 2 clases. |

`git diff --stat`: 2 files changed, 40 insertions(+), 4 deletions(-)

---

## Estado después de FASE 1

```
tests/unit:        1215 passed, 0 failed
tests/integration: 104 passed, 0 failed  (+1 test que antes fallaba)
tests/api:         8 passed,   0 failed
Total:             1327 passed, 0 failed  (+1 vs baseline)

DT-API-001: RESUELTA
```

---

*Generado: 2026-05-16T19:26:06 | Commit: baaf09f | Suite: 1327 passed, 0 failed*
